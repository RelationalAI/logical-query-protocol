"""Language-independent parser generation.

This module contains language-independent logic for generating LL(k)
recursive-descent parsers from grammars, including:
- IR generation for parsing logic
- Decision tree construction
- Grammar analysis and transformation
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Sequence as PySequence
from .grammar import Grammar, Rule, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Terminal, is_epsilon, rhs_elements, Sequence
from .target import Lambda, Call, ParseNonterminalDef, Var, Lit, Symbol, Builtin, Let, IfElse, FunDef, BaseType, ListType, TargetExpr, Seq, While, Assign, Type, ParseNonterminal, ParseNonterminalDef, Return, Constructor, gensym
_any_type = BaseType('Any')

MAX_LOOKAHEAD = 3

class TerminalSequenceSet:
    """Abstract base class for lazily computing sets of terminal sequences."""

    def get(self, k: int) -> Set[Tuple[Terminal, ...]]:
        """Get sequences of length up to k, computing and caching if needed."""
        raise NotImplementedError

@dataclass
class FollowSet(TerminalSequenceSet):
    """Lazily computes and caches FOLLOW_k sets for a nonterminal."""

    grammar: Grammar
    lhs: Nonterminal
    _cache: Dict[int, Set[Tuple[Terminal, ...]]] = field(default_factory=dict)

    def get(self, k: int) -> Set[Tuple[Terminal, ...]]:
        """Get FOLLOW_k set for the nonterminal, computing and caching if needed."""
        if k not in self._cache:
            self._cache[k] = self.grammar.follow_k(k, self.lhs)
        return self._cache[k]

@dataclass
class FirstSet(TerminalSequenceSet):
    """Lazily computes and caches FIRST_k sets for an RHS."""

    grammar: Grammar
    rhs: Rhs
    _cache: Dict[int, Set[Tuple[Terminal, ...]]] = field(default_factory=dict)

    def get(self, k: int) -> Set[Tuple[Terminal, ...]]:
        """Get FIRST_k set for the RHS, computing and caching if needed."""
        if k not in self._cache:
            self._cache[k] = self.grammar.first_k(k, self.rhs)
        return self._cache[k]

@dataclass
class ConcatSet(TerminalSequenceSet):
    """Lazily concatenates two TerminalSequenceSets."""

    first: TerminalSequenceSet
    second: TerminalSequenceSet
    _cache: Dict[int, Set[Tuple[Terminal, ...]]] = field(default_factory=dict)

    def get(self, k: int) -> Set[Tuple[Terminal, ...]]:
        """Get concatenation of first and second sets, truncated to length k."""
        if k in self._cache:
            return self._cache[k]

        # Get first set
        first_set = self.first.get(k)

        # Determine how much of second set we need based on shortest sequence in first
        if first_set:
            min_len = min(len(seq) for seq in first_set)
            needed_second_k = k - min_len
            if needed_second_k <= 0:
                # All sequences are max length, don't need second at all
                result = first_set
            else:
                # Need second_k where k = needed_second_k
                from .analysis import _concat_first_k_sets
                second_set = self.second.get(needed_second_k)
                result = _concat_first_k_sets(first_set, second_set, k)
        else:
            result = self.second.get(k)

        self._cache[k] = result
        return result

def generate_parse_functions(grammar: Grammar) -> List[ParseNonterminalDef]:
    parser_methods = []
    rule_order = grammar.traverse_rules_preorder(reachable_only=True)
    reachable = grammar.check_reachability()
    for nt in rule_order:
        if reachable is not None and nt not in reachable:
            continue
        rules = grammar.rules[nt]
        method_code = _generate_parse_method(nt, rules, grammar)
        parser_methods.append(method_code)
    return parser_methods

def _generate_parse_method(lhs: Nonterminal, rules: List[Rule], grammar: Grammar) -> ParseNonterminalDef:
    """Generate parse method code as string (preserving existing logic)."""
    return_type = None
    rhs = None
    follow_set = FollowSet(grammar, lhs)
    if len(rules) == 1:
        rule = rules[0]
        rhs = _generate_parse_rhs_ir(rule.rhs, grammar, follow_set, True, rule.action)
        return_type = rule.action.return_type
    else:
        predictor = _build_predictor(grammar, lhs, rules)
        prediction = gensym('prediction')
        has_epsilon = any((is_epsilon(rule.rhs) for rule in rules))
        if has_epsilon:
            tail = Lit(None)
        else:
            tail = Call(Builtin('error'), [Lit(f'Unexpected token in {lhs}'), Call(Builtin('current_token'), [])])
        for i, rule in enumerate(rules):
            # Ensure the return type is the same for all actions for this nonterminal.
            assert return_type is None or return_type == rule.action.return_type, f'Return type mismatch at rule {i}: {return_type} != {rule.action.return_type}'
            return_type = rule.action.return_type
            if is_epsilon(rule.rhs):
                continue
            tail = IfElse(Call(Builtin('equal'), [Var(prediction, BaseType('Int64')), Lit(i)]), _generate_parse_rhs_ir(rule.rhs, grammar, follow_set, True, rule.action), tail)
        rhs = Let(Var(prediction, BaseType('Int64')), predictor, tail)
    assert return_type is not None
    return ParseNonterminalDef(lhs, [], return_type, rhs)

def _build_predictor(grammar: Grammar, lhs: Nonterminal, rules: List[Rule]) -> TargetExpr:
    """Build a predictor expression that returns the index of the matching rule.

    Uses FIRST_k lookahead to distinguish between alternatives. Builds a
    decision tree lazily, computing FIRST_k only as needed for rules that
    require more lookahead.
    """
    assert len(rules) > 1
    nullable = grammar.compute_nullable()
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
        assert False, f'Grammar conflict at lookahead depth {depth}:\n  {conflict_rules}'
    groups: Dict[Terminal, List[int]] = {}
    exhausted: Set[int] = set()
    for rule_idx in active_indices:
        rule = rules[rule_idx]
        rule_first = grammar.first_k(depth + 1, rule.rhs)
        tokens_at_depth: Set[Terminal] = set()
        for seq in rule_first:
            if len(seq) > depth:
                tokens_at_depth.add(seq[depth])
            else:
                exhausted.add(rule_idx)
        for token in tokens_at_depth:
            if token not in groups:
                groups[token] = []
            groups[token].append(rule_idx)
    if len(exhausted) > 1:
        subtree_default = _build_predictor_tree(grammar, rules, list(exhausted), nullable, default, depth + 1)
    elif len(exhausted) == 1:
        subtree_default = Lit(exhausted.pop())
    else:
        subtree_default = default
    if not groups:
        return subtree_default
    result = subtree_default
    for token, indices in groups.items():
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

def findfirst(predicate, iterable):
    return next((i for i, x in enumerate(iterable) if predicate(x)), None)

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

    for seq in token_sequences:
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
    for token, subsequences in groups.items():
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
        element_first = grammar.first_k(k, element)
        follow_k = follow_set.get(k)
        if not (element_first & follow_k):
            return _build_lookahead_check(element_first, depth=0)

    # Still conflicts at MAX_LOOKAHEAD
    element_first = grammar.first_k(MAX_LOOKAHEAD, element)
    conflict_msg = f'Ambiguous Option/Star: FIRST_{MAX_LOOKAHEAD}({element}) and follow set overlap'
    assert False, conflict_msg

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
        return Call(Builtin('consume_terminal'), [Lit(rhs.name)])
    elif isinstance(rhs, Nonterminal):
        return Call(ParseNonterminal(rhs), [])
    elif isinstance(rhs, Option):
        assert grammar is not None
        predictor = _build_option_predictor(grammar, rhs.rhs, follow_set)
        return IfElse(predictor, _generate_parse_rhs_ir(rhs.rhs, grammar, follow_set, False, None), Lit(None))
    elif isinstance(rhs, Star):
        assert grammar is not None
        xs = gensym('xs')
        cond = gensym('cond')
        cond_var = Var(cond, BaseType('Boolean'))
        predictor = _build_option_predictor(grammar, rhs.rhs, follow_set)
        return Let(Var(xs, _any_type), Call(Builtin('make_list'), []), Let(cond_var, predictor, Seq([While(cond_var, Seq([Call(Builtin('list_push!'), [Var(xs, _any_type), _generate_parse_rhs_ir(rhs.rhs, grammar, follow_set, False, None)]), Assign(cond_var, predictor)])), Var(xs, _any_type)])))
    else:
        assert False, f'Unsupported Rhs type: {type(rhs)}'

def _generate_parse_rhs_ir_sequence(rhs: Sequence, grammar: Grammar, follow_set: TerminalSequenceSet, apply_action: bool=False, action: Optional[Lambda]=None) -> TargetExpr:
    if is_epsilon(rhs):
        return Lit(None)

    exprs = []
    arg_vars = []
    param_names = []
    elems = list(rhs_elements(rhs))
    non_literal_count = 0
    for i, elem in enumerate(elems):
        if i + 1 < len(elems):
            following = Sequence(elems[i+1:])
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
                var_name = gensym('arg')
            param_names.append(var_name)
            exprs.append(Assign(Var(var_name, _any_type), elem_ir))
            arg_vars.append(Var(var_name, _any_type))
            non_literal_count += 1
    if apply_action and action:
        lambda_call = _apply(action, arg_vars)
        exprs.append(lambda_call)
    elif len(arg_vars) > 1:
        # Multiple values - wrap in tuple
        exprs.append(Call(Builtin('Tuple'), arg_vars))
    elif len(arg_vars) == 1:
        # Single value - just use it
        pass  # Value already assigned
    # else: no non-literal elements, return None

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
    elif isinstance(expr, Return):
        return Return(_subst(expr.expr, var, val))
    return expr
