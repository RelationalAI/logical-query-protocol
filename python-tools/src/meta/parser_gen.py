"""Language-independent parser generation.

This module contains language-independent logic for generating LL(k)
recursive-descent parsers from grammars, including:
- IR generation for parsing logic
- Decision tree construction
- Grammar analysis and transformation
"""

from dataclasses import is_dataclass
from re import L
from typing import Dict, List, Optional, Set, Tuple, Callable, Sequence as PySequence

from .grammar import Grammar, Rule, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Plus, Option, Terminal, is_epsilon, rhs_elements, Sequence
from .target import Lambda, Call, ParseNonterminalDef, Var, Lit, Symbol, Builtin, Let, IfElse, Try, Ok, Err, FunDef, BaseType, ListType, TargetExpr, Seq, While, TryCatch, Assign, Type, ParseNonterminal, ParseNonterminalDef, Return, Constructor, gensym


def generate_rules(grammar: Grammar) -> List[ParseNonterminalDef]:
    # Generate parser methods as strings
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

def _generate_parse_method(
    lhs: Nonterminal,
    rules: List[Rule],
    grammar: Grammar) -> ParseNonterminalDef:

    """Generate parse method code as string (preserving existing logic)."""

    rhs = None
    if len(rules) == 1:
        rule = rules[0]
        rhs = _generate_parse_rhs_ir(rule.rhs, rule, grammar)
    else:
        predictor = _build_predictor(grammar, lhs, rules)
        prediction = gensym("prediction")

        has_epsilon = any(is_epsilon(rule.rhs) for rule in rules)
        if has_epsilon:
            tail = Lit(None)
        else:
            tail = Call(Builtin('error'), [Lit(f'Unexpected token in {lhs}'), Call(Builtin('current_token'), [])])

        for (i, rule) in enumerate(rules):
            if is_epsilon(rule.rhs):
                continue
            tail = IfElse(
                Call(Builtin('equal'), [Var(prediction), Lit(i)]),
                _generate_parse_rhs_ir(rule.rhs, rule, grammar),
                tail)

        rhs = Let(prediction, predictor, tail)

    return ParseNonterminalDef(lhs, [], BaseType('Any'), rhs)

def _normalize(expr: TargetExpr, k: Callable[[TargetExpr], TargetExpr] = lambda x: x) -> TargetExpr:
    if isinstance(expr, Return):
        return Return(_normalize(expr))
    if isinstance(expr, Assign):
        return _normalize(expr.expr, lambda rhs: k(Assign(expr.var, rhs)))
    if isinstance(expr, Seq):
        return Seq([_normalize(e) for e in expr.exprs[:-1]] + [_normalize(expr.exprs[-1], k)])
    if isinstance(expr, IfElse):
        return IfElse(_normalize(expr.condition), _normalize(expr.then_branch, k), _normalize(expr.else_branch, k))
    if isinstance(expr, Let):
        return Let(expr.var, _normalize(expr.init), _normalize(expr.body, k))
    if isinstance(expr, TryCatch):
        return TryCatch(_normalize(expr.try_body, k), _normalize(expr.catch_body, k), expr.exception_type)
    if isinstance(expr, Call):
        return k(Call(_normalize(expr.func), [_normalize(arg) for arg in expr.args]))
    if isinstance(expr, Lambda):
        return k(Lambda(expr.params, _normalize(expr.body), expr.return_type))
    if isinstance(expr, While):
        return k(While(_normalize(expr.condition), _normalize(expr.body)))
    if isinstance(expr, (Var, Lit, Symbol, Constructor, Builtin)):
        return k(expr)
    return k(expr)

MAX_LOOKAHEAD = 3

def _build_predictor(grammar: Grammar, lhs: Nonterminal, rules: List[Rule]) -> TargetExpr:
    """Build a predictor expression that returns the index of the matching rule.

    Uses FIRST_k lookahead to distinguish between alternatives. Builds a
    decision tree lazily, computing FIRST_k only as needed for rules that
    require more lookahead.
    """
    assert len(rules) > 1

    nullable = grammar.compute_nullable()

    # Start with non-epsilon rule indices
    active_indices = [i for i, rule in enumerate(rules) if not is_epsilon(rule.rhs)]

    # Find epsilon rule index (if any)
    epsilon_index = None
    for i, rule in enumerate(rules):
        if is_epsilon(rule.rhs):
            epsilon_index = i
            break

    default = Lit(epsilon_index) if epsilon_index is not None else Lit(-1)

    return _build_predictor_tree(grammar, rules, active_indices, nullable, default, depth=0)


def _build_predictor_tree(
    grammar: Grammar,
    rules: List[Rule],
    active_indices: List[int],
    nullable: Dict[Nonterminal, bool],
    default: TargetExpr,
    depth: int
) -> TargetExpr:
    """Build a decision tree for predicting which rule matches.

    Lazily computes FIRST_k at each depth, only for rules that need more
    lookahead. Groups by token at current depth, then recurses.
    """
    if not active_indices:
        return default

    if len(active_indices) == 1:
        return Lit(active_indices[0])

    if depth >= MAX_LOOKAHEAD:
        conflict_rules = '\n  '.join(f"Rule {i}: {rules[i]}" for i in active_indices)
        assert False, f"Grammar conflict at lookahead depth {depth}:\n  {conflict_rules}"

    # Compute FIRST_{depth+1} to get tokens at position `depth`
    first_k = grammar.compute_first_k(depth + 1)

    # Group rules by token at current depth
    groups: Dict[Terminal, List[int]] = {}
    exhausted: Set[int] = set()

    for rule_idx in active_indices:
        rule = rules[rule_idx]
        from .analysis import _compute_rhs_elem_first_k
        rule_first = _compute_rhs_elem_first_k(rule.rhs, first_k, nullable, depth + 1)

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

    # Handle exhausted rules
    if len(exhausted) > 1:
        # Multiple rules exhausted - try deeper lookahead
        subtree_default = _build_predictor_tree(
            grammar, rules, list(exhausted), nullable, default, depth + 1
        )
    elif len(exhausted) == 1:
        subtree_default = Lit(exhausted.pop())
    else:
        subtree_default = default

    if not groups:
        return subtree_default

    # Build decision tree from groups
    result = subtree_default
    for token, indices in groups.items():
        check = _build_token_check(token, depth)

        if len(indices) == 1:
            then_branch = Lit(indices[0])
        else:
            then_branch = _build_predictor_tree(
                grammar, rules, indices, nullable, subtree_default, depth + 1
            )

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

def _generate_decision_tree(tail: TargetExpr, token_map: Dict, rules: List, nt_name: str,
                            depth: int, max_depth: int, is_continuation: bool, grammar: Grammar) -> TargetExpr:
    """Generate decision tree for k-token lookahead."""
    if depth >= max_depth:
        return tail

    # TODO: I think we should very naively just generate a sequence of try/catch blocks for each rule
    # using backtracking.

    # Group alternatives by token at current depth
    next_level = {}
    for seq_or_token, alternatives in token_map.items():
        if isinstance(alternatives, list) and len(alternatives) > 0 and isinstance(alternatives[0], tuple):
            for seq, rule_idx in alternatives:
                if len(seq) > depth:
                    token_at_depth = seq[depth]
                    if token_at_depth not in next_level:
                        next_level[token_at_depth] = []
                    next_level[token_at_depth].append((seq, rule_idx))
        else:
            next_level[seq_or_token] = alternatives

    for idx, (token, items) in enumerate(next_level.items()):
        # Generate check for this token
        if token.startswith('"'):
            lit = token[1:-1]
            check = Call(Builtin("match_lookahead_literal"), [Lit(lit), Lit(depth)])
        else:
            check = Call(Builtin("match_lookahead_terminal"), [Lit(token), Lit(depth)])

        # Check if all items lead to the same rule
        rule_indices = set()
        for seq, rule_idx in items:
            rule_indices.add(rule_idx)

        if len(rule_indices) == 1:
            rule_idx = rule_indices.pop()
            rule = rules[rule_idx]
            body = _generate_parse_rhs_ir(rule.rhs, rule, grammar)
        elif depth >= 2:
            # Beyond 2 tokens, use backtracking
            # TODO not sure the `tail` here is right!
            lines = tail
            for bt_idx, rule_idx in enumerate(sorted(rule_indices)):
                rule = rules[rule_idx]
                try_parse = _generate_parse_rhs_ir(rule.rhs, rule, grammar)
                lines = TryCatch(try_parse, Seq([
                    Call(Builtin('restore_position'), [Var('saved_pos')]),
                    lines,
                ]), 'ParseError')
            body = Let('saved_pos', Call(Builtin('save_position'), []), lines)
        elif depth + 1 < max_depth:
            sub_map = {}
            for seq, rule_idx in items:
                if len(seq) > depth + 1:
                    next_token = seq[depth + 1]
                    if next_token not in sub_map:
                        sub_map[next_token] = []
                    sub_map[next_token].append((seq, rule_idx))

            if sub_map:
                body = _generate_decision_tree(tail, sub_map, rules, nt_name, depth + 1, max_depth, is_continuation, grammar)
            else:
                rule_idx = items[0][1]
                rule = rules[rule_idx]
                body = _generate_parse_rhs_ir(rule.rhs, rule, grammar)
        else:
            rule_idx = items[0][1]
            rule = rules[rule_idx]
            body = _generate_parse_rhs_ir(rule.rhs, rule, grammar)

        tail = IfElse(check, body, tail)

    return tail

def findfirst(predicate, iterable):
    return next((i for i, x in enumerate(iterable) if predicate(x)), None)


def _generate_parse_rhs_ir(rhs: Rhs, rule: Optional[Rule] = None, grammar: Optional[Grammar] = None) -> TargetExpr:
    """Generate IR for parsing an RHS.

    Returns IR expression for leaf nodes (Literal, Terminal, Nonterminal).
    Returns None for complex cases that still use string generation.
    """
    if isinstance(rhs, Sequence):
        return _generate_parse_rhs_ir_sequence(rhs, rule, grammar)
    elif isinstance(rhs, LitTerminal):
        # Build IR: Call(Builtin('consume_literal'), [Lit(literal)])
        return Call(Builtin('consume_literal'), [Lit(rhs.name)])
    elif isinstance(rhs, NamedTerminal):
        # Build IR: Call(Builtin('consume_terminal'), [Lit(terminal.name)])
        return Call(Builtin('consume_terminal'), [Lit(rhs.name)])
    elif isinstance(rhs, Nonterminal):
        # Build IR: ParseNonterminal(nonterminal, [])
        return Call(ParseNonterminal(rhs), [])
    elif isinstance(rhs, Option):
        if isinstance(rhs.rhs, NamedTerminal):
            term = rhs.rhs
            return IfElse(
                Call(Builtin('match_terminal'), [Lit(term.name)]),
                Call(Builtin('consume_terminal'), [Lit(term.name)]),
                Lit(None)
            )
        else:
            assert isinstance(rhs.rhs, Nonterminal)
            lhs = rhs.rhs
            rules = grammar.get_rules(lhs)
            has_epsilon = any(is_epsilon(rule.rhs) for rule in rules)
            if not has_epsilon:
                rules = rules + [Rule(lhs, Sequence([]), Lambda(params=[], body=Lit(None)))]
            epsilon_index = findfirst(lambda rule: is_epsilon(rule.rhs), rules)
            predictor = _build_predictor(grammar, lhs, rules)
            body = IfElse(
                Call(Builtin('not_equal'), [predictor, Lit(epsilon_index)]),
                _generate_parse_rhs_ir(rhs.rhs, None, grammar),
                Lit(None)
            )
            return body


    elif isinstance(rhs, Plus):
        # A+ is equivalent to A A*
        return _generate_parse_rhs_ir(Sequence([rhs.rhs, Star(rhs.rhs)]), rule, grammar)
    elif isinstance(rhs, Star):
        if isinstance(rhs.rhs, NamedTerminal):
            term = rhs.rhs
            return While(
                Call(Builtin('match_terminal'), [Lit(term.name)]),
                Call(Builtin('consume_terminal'), [Lit(term.name)])
            )
        else:
            assert isinstance(rhs.rhs, Nonterminal)
            lhs = rhs.rhs
            rules = grammar.get_rules(lhs)
            has_epsilon = any(is_epsilon(rule.rhs) for rule in rules)
            if not has_epsilon:
                rules = rules + [Rule(lhs, Sequence([]), Lambda(params=[], body=Lit(None)))]
            epsilon_index = findfirst(lambda rule: is_epsilon(rule.rhs), rules)
            predictor = _build_predictor(grammar, lhs, rules)
            x = gensym('x')
            xs = gensym('xs')
            body = Let(
                    xs,
                    Call(Builtin('make_list'), []),
                    Seq([
                        While(
                            Call(Builtin('not_equal'), [predictor, Lit(epsilon_index)]),
                            Call(Builtin('list_push'), [Var(xs), _generate_parse_rhs_ir(rhs.rhs, None, grammar)])
                        ),
                        Var(xs)
                    ])
            )
            return body
    else:
        assert False, f"Unsupported Rhs type: {type(rhs)}"

def _generate_parse_rhs_ir_sequence(rhs: Sequence, rule: Optional[Rule] = None, grammar: Optional[Grammar] = None) -> TargetExpr:
    if is_epsilon(rhs):
        # Empty sequence returns None
        return Lit(None)

    # Parse sequence
    # Parse each element
    exprs = []  # All expressions in order
    arg_vars = []  # Variables holding non-literal results
    param_names = []  # Parameter names for Lambda

    non_literal_count = 0
    for i, elem in enumerate(rhs_elements(rhs)):
        elem_ir = _generate_parse_rhs_ir(elem, None, grammar)

        if isinstance(elem, LitTerminal):
            # LitTerminal: execute for side effect
            exprs.append(elem_ir)
        else:
            # Non-literal: bind to variable
            if rule and non_literal_count < len(rule.action.params):
                var_name = gensym(rule.action.params[non_literal_count])
            else:
                var_name = gensym("arg")
            param_names.append(var_name)
            exprs.append(Assign(var_name, elem_ir))
            arg_vars.append(Var(var_name))
            non_literal_count += 1

    # Build Lambda and Call
    if rule and rule.action:
        # Use the action's Lambda
        action_lambda = rule.action
    else:
        # Create default Lambda that returns list of arguments
        # Lambda([arg0, arg1, ...], Tuple([Var(arg0), Var(arg1), ...]))
        list_expr = Call(Builtin('Tuple'), arg_vars)
        action_lambda = Lambda(param_names, list_expr)

    # Call the Lambda with the variables
    lambda_call = _apply(action_lambda, arg_vars)

    # Add lambda call to expression list
    exprs.append(lambda_call)

    # Return as sequence
    if len(exprs) == 1:
        return exprs[0]
    else:
        return Seq(exprs)

def _apply(func: 'Lambda', args: PySequence['TargetExpr']) -> 'TargetExpr':
    if len(args) == 0 and len(func.params) == 0:
        return func.body
    if len(func.params) > 0 and len(args) > 0:
        body = _apply(
            Lambda(params=func.params[1:], body=func.body, return_type=func.return_type),
            args[1:]
        )
        if isinstance(args[0], (Var, Lit)):
            return _subst(body, func.params[0], args[0])
        return Let(func.params[0], args[0], body)
    # TODO
    # assert False, f"Invalid application of {func} to {args}"
    return Call(func, args)

def _subst(expr: 'TargetExpr', var: str, val: 'TargetExpr') -> 'TargetExpr':
    if isinstance(expr, Var) and expr.name == var:
        return val
    elif isinstance(expr, Lambda):
        if var in expr.params:
            return expr
        return Lambda(expr.params, _subst(expr.body, var, val), expr.return_type)
    elif isinstance(expr, Let):
        if expr.var == var:
            return expr
        return Let(expr.var, expr.init, _subst(expr.body, var, val))
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
    elif isinstance(expr, Try):
        return Try(_subst(expr.expr, var, val), _subst(expr.rollback, var, val))
    elif isinstance(expr, Ok):
        return Ok(_subst(expr.expr, var, val))
    elif isinstance(expr, Err):
        return Err(_subst(expr.expr, var, val))
    elif isinstance(expr, Return):
        return Return(_subst(expr.expr, var, val))
    return expr
