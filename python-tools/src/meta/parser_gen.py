"""Language-independent parser generation.

This module contains language-independent logic for generating LL(k)
recursive-descent parsers from grammars, including:
- IR generation for parsing logic
- Decision tree construction
- Grammar analysis and transformation
"""

from re import L
from typing import Dict, List, Optional, Set, Tuple, Callable, Sequence as PySequence

from .grammar import Grammar, Rule, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Plus, Option, Terminal, is_epsilon, rhs_elements, Sequence
from .target import Lambda, Call, ParseNonterminalDef, Var, Lit, Symbol, Builtin, Let, IfElse, FunDef, BaseType, ListType, TargetExpr, Seq, While, TryCatch, Assign, Type, ParseNonterminal, ParseNonterminalDef, Return, Constructor


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

        has_epsilon = any(is_epsilon(rule.rhs) for rule in rules)

        if has_epsilon:
            tail = Lit(None)
        else:
            tail = Call(Builtin('error'), [Lit(f'Unexpected token in {lhs}'), Call(Builtin('current_token'), [])])

        for (i, rule) in enumerate(rules):
            if is_epsilon(rule.rhs):
                continue
            tail = IfElse(
                Call(Builtin('equal'), [predictor, Lit(i)]),
                _generate_parse_rhs_ir(rule.rhs, rule, grammar),
                tail)

        rhs = tail

    rhs = _normalize(rhs, lambda x: Return(x))

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

def _build_predictor(grammar, lhs, rules):
    assert len(rules) > 1
    # TODO PR Placeholder!
    predictor = Call(Builtin('predict'), [Lit(lhs.name)])
    return predictor

def _generate_decision_tree(tail: TargetExpr, token_map: Dict, rules: List, nt_name: str,
                            depth: int, max_depth: int, is_continuation: bool, grammar: Grammar, first_2) -> TargetExpr:
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
                body = _generate_decision_tree(tail, sub_map, rules, nt_name, depth + 1, max_depth, is_continuation, grammar, first_2)
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
        return ParseNonterminal(rhs, [])
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
            return IfElse(
                Call(Builtin('current'), [Lit(rhs.rhs.name)]),
                _generate_parse_rhs_ir(rhs.rhs, None, grammar),
                Lit(None)
            )
    elif isinstance(rhs, Star):
        if isinstance(rhs.rhs, NamedTerminal):
            term = rhs.rhs
            return While(
                Call(Builtin('match_terminal'), [Lit(term.name)]),
                Call(Builtin('consume_terminal'), [Lit(term.name)])
            )
        else:
            assert isinstance(rhs.rhs, Nonterminal)
            return Let(
                    'xs',
                    Call(Builtin('List'), []),
                    Seq([
                        While(
                            Call(Builtin('current'), [Lit(rhs.rhs.name)]),
                            Let('x',
                                _generate_parse_rhs_ir(rhs.rhs, None, grammar),
                                Call(Builtin('append'), [Var('xs'), Var('x')])
                            )
                        ),
                        Var('xs')
                    ])
            )
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
            if rule and rule.action and non_literal_count < len(rule.action.params):
                var_name = rule.action.params[non_literal_count]
            else:
                var_name = f"_arg{non_literal_count}"
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
        # TODO PR do substitution correctly
        if isinstance(args[0], Var) and func.params[0] == args[0].name:
            return body
        return Let(func.params[0], args[0], body)
    # TODO
    # assert False, f"Invalid application of {func} to {args}"
    return Call(func, args)

def _generate_parse_rhs_ir1(rhs: Rhs, rule: Optional[Rule] = None, grammar: Optional[Grammar] = None) -> Optional[TargetExpr]:
    """Generate IR for parsing an RHS.

    Returns IR expression for leaf nodes (LitTerminal, NamedTerminal, Nonterminal).
    Returns None for complex cases that still use string generation.
    """

def _build_decision_tree_ir(token_map: Dict, rules: List[Rule], nt_name: str,
                            depth: int, max_depth: int, is_continuation: bool = False, grammar: Optional[Grammar] = None) -> TargetExpr:
    """Build decision tree IR for k-token lookahead.

    Args:
        token_map: Map from tokens to (seq, rule_idx) pairs
        rules: List of rules for this nonterminal
        nt_name: Name of nonterminal being parsed
        depth: Current lookahead depth
        max_depth: Maximum lookahead depth
        is_continuation: Whether this is a continuation rule

    Returns:
        TargetExpr representing the decision tree (IfElse chain)
    """
    if depth >= max_depth:
        # Beyond max depth - use first available rule
        # This shouldn't happen in well-formed grammars
        first_item = next(iter(token_map.values()))
        if isinstance(first_item, list) and len(first_item) > 0:
            _, rule_idx = first_item[0]
            rule = rules[rule_idx]
            return _generate_parse_rhs_ir(Sequence(rule.rhs), rule, grammar)
        return Lit(None)

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

    # Build list of (check, then_expr) pairs
    checks_and_thens = []

    for token, items in next_level.items():
        # Build check for this token
        if token.startswith('"'):
            lit = token[1:-1]
            if depth == 0:
                check = Call(Builtin('match_literal'), [Lit(lit)])
            else:
                check = Call(Builtin('match_lookahead_literal'), [Lit(lit), Lit(depth)])
        else:
            if depth == 0:
                check = Call(Builtin('match_terminal'), [Lit(token)])
            else:
                check = Call(Builtin('match_lookahead_terminal'), [Lit(token), Lit(depth)])

        # Determine what to do when this check succeeds
        rule_indices = set()
        for seq, rule_idx in items:
            rule_indices.add(rule_idx)

        if len(rule_indices) == 1:
            # Single rule - parse it
            rule_idx = rule_indices.pop()
            rule = rules[rule_idx]
            then_expr = _generate_parse_rhs_ir(Sequence(rule.rhs), rule, grammar)
        elif depth >= 2:
            # Beyond 2 tokens - use backtracking
            # Build try-catch chain
            then_expr = _build_backtracking_ir(sorted(rule_indices), rules, grammar)
        elif depth + 1 < max_depth:
            # Recurse to next depth
            sub_map = {}
            for seq, rule_idx in items:
                if len(seq) > depth + 1:
                    next_token = seq[depth + 1]
                    if next_token not in sub_map:
                        sub_map[next_token] = []
                    sub_map[next_token].append((seq, rule_idx))

            if sub_map:
                then_expr = _build_decision_tree_ir(sub_map, rules, nt_name, depth + 1, max_depth, is_continuation, grammar)
            else:
                # No further tokens - use first rule
                rule_idx = items[0][1]
                rule = rules[rule_idx]
                then_expr = _generate_parse_rhs_ir(Sequence(rule.rhs), rule, grammar)
        else:
            # At max depth - use first rule
            rule_idx = items[0][1]
            rule = rules[rule_idx]
            then_expr = _generate_parse_rhs_ir(Sequence(rule.rhs), rule, grammar)

        checks_and_thens.append((check, then_expr))

    # Handle the final else case
    # Check if any rule is epsilon (empty list)
    has_epsilon = any(is_epsilon(rule.rhs) for rule in rules)

    if has_epsilon:
        final_else = Lit(None)
    else:
        # Raise parse error
        error_msg = f"Unexpected token in {nt_name}: {{self.current()}}"
        final_else = Call(Builtin('raise_parse_error'), [Lit(error_msg)])

    # Build if-elif-else chain from end to beginning
    if not checks_and_thens:
        return final_else

    # Start with the final else
    result = final_else

    # Build chain backwards
    for check, then_expr in reversed(checks_and_thens):
        result = IfElse(condition=check, then_branch=then_expr, else_branch=result)

    return result


def _build_backtracking_ir(rule_indices: List[int], rules: List[Rule], grammar: Optional[Grammar] = None) -> TargetExpr:
    """Build backtracking IR for multiple rules.

    Generates:
    saved_pos = save_position()
    try:
        parse_rule_0
    except ParseError:
        restore_position(saved_pos)
        try:
            parse_rule_1
        except ParseError:
            restore_position(saved_pos)
            parse_rule_n
    """
    if not rule_indices:
        return Lit(None)

    # Start with the last rule (no try-catch)
    last_idx = rule_indices[-1]
    last_rule = rules[last_idx]
    body = _generate_parse_rhs_ir(last_rule.rhs, last_rule, grammar)

    # Build try-catch chain in reverse
    for i in range(len(rule_indices) - 2, -1, -1):
        rule_idx = rule_indices[i]
        rule = rules[rule_idx]
        try_body = _generate_parse_rhs_ir(rule.rhs, rule, grammar)

        # Restore position in catch
        restore = Call(Builtin('restore_position'), [Var('saved_pos')])

        body = TryCatch(
            try_body=try_body,
            catch_body=Seq([restore, body]),
            exception_type='ParseError',
        )

    # Save position at the start
    save = Assign(var='saved_pos', expr=Call(Builtin('save_position'), []))

    return Seq([save, body])
