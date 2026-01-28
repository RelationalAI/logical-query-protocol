"""Language-independent LL(k) parser generation.

This module generates recursive-descent parsers from context-free grammars.
It produces a target-language-independent IR (intermediate representation)
that can then be translated to Python, Julia, Go, or other languages.

Overview
--------
The parser generator takes a Grammar and produces a list of VisitNonterminalDef
objects, one for each reachable nonterminal. Each definition contains:
- The nonterminal being parsed
- Parameters (for parameterized nonterminals)
- Return type
- Body: an IR expression tree representing the parsing logic

The generated parsers are LL(k) - they use up to k tokens of lookahead to
decide which production to use. The value of k is determined automatically
based on what's needed to distinguish alternatives.

Key Concepts
------------

**Prediction**: When a nonterminal has multiple productions, we need to decide
which one to use based on lookahead. The predictor builds a decision tree that
examines tokens at increasing depths until alternatives can be distinguished.

**FIRST and FOLLOW sets**: These classical grammar analysis sets determine what
tokens can appear at various positions. FIRST_k(α) is the set of k-length
terminal prefixes derivable from α. FOLLOW_k(A) is what can follow nonterminal A.

**Lazy lookahead**: We compute FIRST_k and FOLLOW_k lazily, starting with k=1
and only increasing if needed. This avoids expensive computation when simple
lookahead suffices. See terminal_sequence_set.py for details.

**Semantic actions**: Each production has a Lambda that constructs the result.
The parser captures values from non-literal RHS elements and applies the action.

IR Structure
------------
The generated IR uses these main constructs (from target.py):

- Let(var, init, body): Bind a variable
- IfElse(cond, then, else): Conditional
- Call(func, args): Function/builtin call
- Seq([exprs]): Sequence of expressions
- While(cond, body): Loop (for Star elements)
- Assign(var, expr): Assignment (for loop variables)

Builtins used:
- consume_literal(s): Consume a literal token, error if mismatch
- consume_terminal(name): Consume a terminal, return its value
- match_lookahead_literal(s, k): Check if lookahead[k] is literal s
- match_lookahead_terminal(name, k): Check if lookahead[k] is terminal type
- list_push!(list, elem): Append to list (mutating)
- equal(a, b): Equality check
- error(msg, context): Raise parse error

Example
-------
For grammar:
    expr → term '+' expr | term
    term → INT

The generated IR for expr (simplified) would be:
    let prediction = if match_lookahead_terminal("INT", 0) and
                        match_lookahead_literal("+", 1)
                     then 0  # first alternative
                     else 1  # second alternative
    if equal(prediction, 0) then
        let t = parse_term()
        consume_literal("+")
        let e = parse_expr()
        Expr(t, e)  # semantic action
    else
        let t = parse_term()
        t  # semantic action
"""

from typing import Dict, List, Optional, Set, Tuple, Sequence as PySequence
from .grammar import Grammar, Rule, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Terminal, Sequence
from .grammar_utils import is_epsilon, rhs_elements
from .target import Lambda, Call, VisitNonterminalDef, Var, Lit, Symbol, Builtin, NewMessage, OneOf, Let, IfElse, BaseType, ListType, ListExpr, TargetExpr, Seq, While, Foreach, ForeachEnumerated, Assign, VisitNonterminal, Return
from .gensym import gensym
from .terminal_sequence_set import TerminalSequenceSet, FollowSet, FirstSet, ConcatSet

# Maximum lookahead depth for LL(k) parsing.
# Set to 3 because this is sufficient for parsing S-expressions in LQP.
# S-expressions require k=3 to distinguish alternatives like:
#   (op arg1 arg2)  vs  (op arg1)  vs  (op)
# where we need to look at: "(" token[0], operator token[1], first-arg token[2]
MAX_LOOKAHEAD = 3


class GrammarConflictError(Exception):
    """Raised when grammar has LL(k) conflicts that cannot be resolved within MAX_LOOKAHEAD."""
    pass


class AmbiguousGrammarError(Exception):
    """Raised when Option or Star cannot be distinguished from follow set."""
    pass


def generate_parse_functions(grammar: Grammar, indent: str = "") -> List[VisitNonterminalDef]:
    parser_methods = []
    reachable, _ = grammar.analysis.partition_nonterminals_by_reachability()
    for nt in reachable:
        rules = grammar.rules[nt]
        method_code = _generate_parse_method(nt, rules, grammar, indent)
        parser_methods.append(method_code)
    return parser_methods

def _generate_parse_method(lhs: Nonterminal, rules: List[Rule], grammar: Grammar, indent: str = "") -> VisitNonterminalDef:
    """Generate parse method code as string (preserving existing logic)."""
    return_type = None
    rhs = None
    follow_set = FollowSet(grammar, lhs)
    if len(rules) == 1:
        rule = rules[0]
        rhs = _generate_parse_rhs_ir(rule.rhs, grammar, follow_set, True, rule.constructor)
        return_type = rule.constructor.return_type
    else:
        predictor = _build_predictor(grammar, rules)
        prediction = gensym('prediction')
        has_epsilon = any((is_epsilon(rule.rhs) for rule in rules))
        if has_epsilon:
            tail = Lit(None)
        else:
            tail = Call(Builtin('error'), [Lit(f'Unexpected token in {lhs}'), Call(Builtin('current_token'), [])])
        for i, rule in enumerate(rules):
            # Ensure the return type is the same for all actions for this nonterminal.
            assert return_type is None or return_type == rule.constructor.return_type, f'Return type mismatch at rule {i}: {return_type} != {rule.constructor.return_type}'
            return_type = rule.constructor.return_type
            if is_epsilon(rule.rhs):
                continue
            tail = IfElse(Call(Builtin('equal'), [Var(prediction, BaseType('Int64')), Lit(i)]), _generate_parse_rhs_ir(rule.rhs, grammar, follow_set, True, rule.constructor), tail)
        rhs = Let(Var(prediction, BaseType('Int64')), predictor, tail)
    assert return_type is not None
    return VisitNonterminalDef('parse', lhs, [], return_type, rhs, indent)

def _build_predictor(grammar: Grammar, rules: List[Rule]) -> TargetExpr:
    """Build a predictor expression that returns the index of the matching rule.

    Uses FIRST_k lookahead to distinguish between alternatives. Builds a
    decision tree lazily, computing FIRST_k only as needed for rules that
    require more lookahead.
    """
    assert len(rules) > 1
    nullable = grammar.analysis.nullable
    active_indices = [i for i, rule in enumerate(rules) if not is_epsilon(rule.rhs)]
    epsilon_index = None
    for i, rule in enumerate(rules):
        if is_epsilon(rule.rhs):
            epsilon_index = i
            break
    default = Lit(epsilon_index) if epsilon_index is not None else Lit(-1)
    return _build_predictor_tree(grammar, rules, active_indices, nullable, default, depth=0)

def _build_predictor_tree(grammar: Grammar, rules: List[Rule], active_indices: List[int], nullable: Dict[Nonterminal, bool], default: TargetExpr, depth: int) -> TargetExpr:
    """Build a decision tree for predicting which rule matches.

    Lazily computes FIRST_k at each depth, only for rules that need more
    lookahead. Groups by token at current depth, then recurses.
    """
    if not active_indices:
        return default
    if depth >= MAX_LOOKAHEAD:
        conflict_rules = '\n  '.join((f'Rule {i}: {rules[i]}' for i in active_indices))
        raise GrammarConflictError(f'Grammar conflict at lookahead depth {depth}:\n  {conflict_rules}')
    groups: Dict[Terminal, List[int]] = {}
    exhausted: Set[int] = set()
    for rule_idx in active_indices:
        rule = rules[rule_idx]
        rule_first = grammar.analysis.first_k_of(depth + 1, rule.rhs)
        tokens_at_depth: Set[Terminal] = set()
        for seq in sorted(rule_first, key=lambda s: tuple(str(t) for t in s)):
            if len(seq) > depth:
                tokens_at_depth.add(seq[depth])
            else:
                exhausted.add(rule_idx)
        for token in sorted(tokens_at_depth, key=str):
            if token not in groups:
                groups[token] = []
            groups[token].append(rule_idx)
    if len(exhausted) > 1:
        conflict_rules = '\n  '.join(
            (f'Rule {i}: {rules[i]}' for i in sorted(exhausted))
        )
        raise GrammarConflictError(
            f'Grammar conflict: multiple rules fully consumed at lookahead depth {depth}:\n  {conflict_rules}'
        )
    elif len(exhausted) == 1:
        exhausted_idx = next(iter(exhausted))
        subtree_default = Lit(exhausted_idx)
    else:
        subtree_default = default
    if not groups:
        return subtree_default
    result = subtree_default
    # Build IfElse chain with specific ordering for literal string matching.
    # We iterate through tokens and wrap each new condition around the previous result:
    #   result = IfElse(check_token_n, ..., result)
    # This means the LAST token processed becomes the FIRST condition checked.
    # We want LitTerminals (literal strings like "let", "if", "(") checked before
    # NamedTerminals (token types like SYMBOL, INT).
    # So we sort with LitTerminals AFTER NamedTerminals in iteration order.
    def token_sort_key(item):
        token = item[0]
        # Iteration order (lower processed first):
        #   0 = NamedTerminals (processed first, become inner conditions)
        #   1 = LitTerminals (processed last, become outer/first-checked conditions)
        iteration_order = 1 if isinstance(token, LitTerminal) else 0
        return (iteration_order, str(token))
    for token, indices in sorted(groups.items(), key=token_sort_key):
        check = _build_token_check(token, depth)
        if len(indices) == 1:
            then_branch = Lit(indices[0])
        else:
            then_branch = _build_predictor_tree(grammar, rules, indices, nullable, subtree_default, depth + 1)
        result = IfElse(check, then_branch, result)
    return result

def _build_token_check(term: Terminal, depth: int) -> TargetExpr:
    """Build a check for a single token at a given lookahead depth."""
    if isinstance(term, LitTerminal):
        return Call(Builtin('match_lookahead_literal'), [Lit(term.name), Lit(depth)])
    elif isinstance(term, NamedTerminal):
        return Call(Builtin('match_lookahead_terminal'), [Lit(term.name), Lit(depth)])
    else:
        return Lit(False)

def _build_lookahead_check(token_sequences: Set[Tuple[Terminal, ...]], depth: int) -> TargetExpr:
    """Build a boolean expression that checks if lookahead matches any of the token sequences.

    Args:
        token_sequences: Set of token sequences to match
        depth: Current lookahead depth

    Returns a boolean expression.
    """
    if not token_sequences:
        return Lit(False)

    groups: Dict[Terminal, Set[Tuple[Terminal, ...]]] = {}
    short_sequences = False

    for seq in sorted(token_sequences, key=lambda s: tuple(str(t) for t in s)):
        if len(seq) <= depth:
            short_sequences = True
        else:
            token = seq[depth]
            if token not in groups:
                groups[token] = set()
            groups[token].add(seq)

    if short_sequences:
        return Lit(True)

    if not groups:
        return Lit(False)

    conditions = []
    for token, subsequences in sorted(groups.items(), key=lambda item: str(item[0])):
        token_check = _build_token_check(token, depth)
        deeper_check = _build_lookahead_check(subsequences, depth + 1)
        if isinstance(deeper_check, Lit) and deeper_check.value is True:
            conditions.append(token_check)
        else:
            conditions.append(IfElse(token_check, deeper_check, Lit(False)))

    result = conditions[0]
    for cond in conditions[1:]:
        result = IfElse(result, Lit(True), cond)
    return result

def _build_option_predictor(grammar: Grammar, element: Rhs, follow_set: TerminalSequenceSet) -> TargetExpr:
    """Build a predicate that checks if we should enter an Option or continue a Star.

    Returns a boolean expression that's true if the lookahead matches the element,
    false if it matches what follows.
    """
    # Find minimal k needed to distinguish element from follow
    for k in range(1, MAX_LOOKAHEAD + 1):
        element_first = grammar.analysis.first_k_of(k, element)
        follow_k = follow_set.get(k)
        if not (element_first & follow_k):
            return _build_lookahead_check(element_first, depth=0)

    # Still conflicts at MAX_LOOKAHEAD
    element_first = grammar.analysis.first_k_of(MAX_LOOKAHEAD, element)
    conflict_msg = f'Ambiguous Option/Star: FIRST_{MAX_LOOKAHEAD}({element}) and follow set overlap'
    raise AmbiguousGrammarError(conflict_msg)

def _generate_parse_rhs_ir(rhs: Rhs, grammar: Grammar, follow_set: TerminalSequenceSet, apply_action: bool=False, action: Optional[Lambda]=None) -> TargetExpr:
    """Generate IR for parsing an RHS.

    Args:
        rhs: The RHS to parse
        grammar: The grammar
        follow_set: TerminalSequenceSet for computing follow lazily
        apply_action: Whether to apply the semantic action
        action: The semantic action to apply (required if apply_action is True)

    Returns IR expression for leaf nodes (Literal, Terminal, Nonterminal).
    Returns None for complex cases that still use string generation.
    """
    if isinstance(rhs, Sequence):
        return _generate_parse_rhs_ir_sequence(rhs, grammar, follow_set, apply_action, action)
    elif isinstance(rhs, LitTerminal):
        parse_expr = Call(Builtin('consume_literal'), [Lit(rhs.name)])
        if apply_action and action:
            return Seq([parse_expr, _apply(action, [])])
        return parse_expr
    elif isinstance(rhs, NamedTerminal):
        parse_expr = Call(Builtin('consume_terminal'), [Lit(rhs.name)])
        if apply_action and action:
            if len(action.params) == 0:
                return Seq([parse_expr, _apply(action, [])])
            var_name = gensym(action.params[0].name)
            var = Var(var_name, rhs.target_type())
            return Let(var, parse_expr, _apply(action, [var]))
        return parse_expr
    elif isinstance(rhs, Nonterminal):
        parse_expr = Call(VisitNonterminal('parse', rhs), [])
        if apply_action and action:
            if len(action.params) == 0:
                return Seq([parse_expr, _apply(action, [])])
            var_name = gensym(action.params[0].name)
            var = Var(var_name, rhs.target_type())
            return Let(var, parse_expr, _apply(action, [var]))
        return parse_expr
    elif isinstance(rhs, Option):
        assert grammar is not None
        predictor = _build_option_predictor(grammar, rhs.rhs, follow_set)
        return IfElse(predictor, _generate_parse_rhs_ir(rhs.rhs, grammar, follow_set, False, None), Lit(None))
    elif isinstance(rhs, Star):
        assert grammar is not None
        xs = Var(gensym('xs'), ListType(rhs.rhs.target_type()))
        cond = Var(gensym('cond'), BaseType('Boolean'))
        predictor = _build_option_predictor(grammar, rhs.rhs, follow_set)
        parse_item = _generate_parse_rhs_ir(rhs.rhs, grammar, follow_set, False, None)
        loop_body = Seq([Call(Builtin('list_push!'), [xs, parse_item]), Assign(cond, predictor)])
        return Let(xs, ListExpr([], rhs.rhs.target_type()),
                   Let(cond, predictor, Seq([While(cond, loop_body), xs])))
    else:
        raise NotImplementedError(f'Unsupported Rhs type: {type(rhs)}')

def _generate_parse_rhs_ir_sequence(rhs: Sequence, grammar: Grammar, follow_set: TerminalSequenceSet, apply_action: bool=False, action: Optional[Lambda]=None) -> TargetExpr:
    if is_epsilon(rhs):
        return Lit(None)

    exprs = []
    arg_vars = []
    elems = list(rhs_elements(rhs))
    non_literal_count = 0
    for i, elem in enumerate(elems):
        if i + 1 < len(elems):
            following = Sequence(tuple(elems[i+1:]))
            first_following = FirstSet(grammar, following)
            follow_set_i = ConcatSet(first_following, follow_set)
        else:
            follow_set_i = follow_set
        elem_ir = _generate_parse_rhs_ir(elem, grammar, follow_set_i, False, None)
        if isinstance(elem, LitTerminal):
            exprs.append(elem_ir)
        else:
            if action and non_literal_count < len(action.params):
                var_name = gensym(action.params[non_literal_count].name)
            else:
                if action is not None and non_literal_count >= len(action.params):
                    raise ValueError(
                        f'Action parameter count mismatch: action has {len(action.params)} params '
                        f'but sequence has at least {non_literal_count + 1} non-literal elements'
                    )
                var_name = gensym('arg')
            var = Var(var_name, elem.target_type())
            exprs.append(Assign(var, elem_ir))
            arg_vars.append(var)
            non_literal_count += 1
    if apply_action and action:
        lambda_call = _apply(action, arg_vars)
        exprs.append(lambda_call)
    elif len(arg_vars) > 1:
        # Multiple values - wrap in tuple
        exprs.append(Call(Builtin('make_tuple'), arg_vars))
    elif len(arg_vars) == 1:
        # Single value - return the variable
        exprs.append(arg_vars[0])
    else:
        # no non-literal elements, return None
        return Lit(None)

    if len(exprs) == 1:
        return exprs[0]
    else:
        return Seq(exprs)

def _apply(func: 'Lambda', args: PySequence['TargetExpr']) -> 'TargetExpr':
    if len(args) == 0 and len(func.params) == 0:
        return func.body
    if len(func.params) > 0 and len(args) > 0:
        body = _apply(Lambda(params=func.params[1:], return_type=func.return_type, body=func.body), args[1:])
        if isinstance(args[0], (Var, Lit)):
            return _subst(body, func.params[0].name, args[0])
        return Let(func.params[0], args[0], body)
    return Call(func, args)

def _subst(expr: 'TargetExpr', var: str, val: 'TargetExpr') -> 'TargetExpr':
    if isinstance(expr, Var) and expr.name == var:
        return val
    elif isinstance(expr, Lambda):
        if var in [p.name for p in expr.params]:
            return expr
        return Lambda(params=expr.params, return_type=expr.return_type, body=_subst(expr.body, var, val))
    elif isinstance(expr, Let):
        if expr.var.name == var:
            return expr
        return Let(expr.var, _subst(expr.init, var, val), _subst(expr.body, var, val))
    elif isinstance(expr, Assign):
        return Assign(expr.var, _subst(expr.expr, var, val))
    elif isinstance(expr, Call):
        return Call(_subst(expr.func, var, val), [_subst(arg, var, val) for arg in expr.args])
    elif isinstance(expr, Seq):
        return Seq([_subst(arg, var, val) for arg in expr.exprs])
    elif isinstance(expr, IfElse):
        return IfElse(_subst(expr.condition, var, val), _subst(expr.then_branch, var, val), _subst(expr.else_branch, var, val))
    elif isinstance(expr, While):
        return While(_subst(expr.condition, var, val), _subst(expr.body, var, val))
    elif isinstance(expr, Foreach):
        if expr.var.name == var:
            return expr
        return Foreach(expr.var, _subst(expr.collection, var, val), _subst(expr.body, var, val))
    elif isinstance(expr, ForeachEnumerated):
        if expr.index_var.name == var or expr.var.name == var:
            return expr
        return ForeachEnumerated(expr.index_var, expr.var, _subst(expr.collection, var, val), _subst(expr.body, var, val))
    elif isinstance(expr, ListExpr):
        return ListExpr([_subst(elem, var, val) for elem in expr.elements], expr.element_type)
    elif isinstance(expr, Return):
        return Return(_subst(expr.expr, var, val))
    elif isinstance(expr, (Lit, Symbol, Builtin, NewMessage, OneOf, VisitNonterminal)):
        # These don't contain variables, return unchanged
        return expr
    raise ValueError(f"Unknown expression type in _subst: {type(expr).__name__}")
