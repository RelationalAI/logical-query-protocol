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

from .grammar import Grammar, Rule, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Terminal, is_epsilon, rhs_elements, Sequence
from .target import Lambda, Call, ParseNonterminalDef, Var, Lit, Symbol, Builtin, Let, IfElse, FunDef, BaseType, ListType, TargetExpr, Seq, While, Assign, Type, ParseNonterminal, ParseNonterminalDef, Return, Constructor, gensym

_any_type = BaseType("Any")


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
                Call(Builtin('equal'), [Var(prediction, _any_type), Lit(i)]),
                _generate_parse_rhs_ir(rule.rhs, rule, grammar),
                tail)

        rhs = Let(Var(prediction, _any_type), predictor, tail)

    return ParseNonterminalDef(lhs, [], BaseType('Any'), rhs)

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
        parse_expr = Call(Builtin('consume_literal'), [Lit(rhs.name)])
        if rule and rule.action:
            return Seq([parse_expr, _apply(rule.action, [])])
        return parse_expr
    elif isinstance(rhs, NamedTerminal):
        # Build IR: Call(Builtin('consume_terminal'), [Lit(terminal.name)])
        parse_expr = Call(Builtin('consume_terminal'), [Lit(rhs.name)])
        if rule and rule.action:
            var_name = gensym(rule.action.params[0].name if rule.action.params else "arg")
            return Seq([Assign(Var(var_name, _any_type), parse_expr), _apply(rule.action, [Var(var_name, _any_type)])])
        return parse_expr
    elif isinstance(rhs, Nonterminal):
        # Build IR: ParseNonterminal(nonterminal, [])
        parse_expr = Call(ParseNonterminal(rhs), [])
        if rule and rule.action:
            var_name = gensym(rule.action.params[0] if rule.action.params else "arg")
            return Seq([Assign(Var(var_name, _any_type), parse_expr), _apply(rule.action, [Var(var_name, _any_type)])])
        return parse_expr
    elif isinstance(rhs, Option):
        if isinstance(rhs.rhs, NamedTerminal):
            term = rhs.rhs
            parse_expr = IfElse(
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
                rules = rules + [Rule(lhs, Sequence([]), Lambda(params=[], return_type=_any_type, body=Lit(None)))]
            epsilon_index = findfirst(lambda rule: is_epsilon(rule.rhs), rules)
            if len(rules) > 1:
                predictor = _build_predictor(grammar, lhs, rules)
                parse_expr = IfElse(
                    Call(Builtin('not_equal'), [predictor, Lit(epsilon_index)]),
                    _generate_parse_rhs_ir(rhs.rhs, None, grammar),
                    Lit(None)
                )
            else:
                parse_expr = Lit(None)
        if rule and rule.action:
            var_name = gensym(rule.action.params[0] if rule.action.params else "arg")
            return Seq([Assign(Var(var_name, _any_type), parse_expr), _apply(rule.action, [Var(var_name, _any_type)])])
        return parse_expr


    elif isinstance(rhs, Star):
        if isinstance(rhs.rhs, NamedTerminal):
            term = rhs.rhs
            parse_expr = While(
                Call(Builtin('match_terminal'), [Lit(term.name)]),
                Call(Builtin('consume_terminal'), [Lit(term.name)])
            )
        else:
            assert isinstance(rhs.rhs, Nonterminal)
            lhs = rhs.rhs
            rules = grammar.get_rules(lhs)
            has_epsilon = any(is_epsilon(rule.rhs) for rule in rules)
            if not has_epsilon:
                rules = rules + [Rule(lhs, Sequence([]), Lambda(params=[], return_type=_any_type, body=Lit(None)))]
            epsilon_index = findfirst(lambda rule: is_epsilon(rule.rhs), rules)
            if len(rules) > 1:
                predictor = _build_predictor(grammar, lhs, rules)
                x = gensym('x')
                xs = gensym('xs')
                parse_expr = Let(
                        Var(xs, _any_type),
                        Call(Builtin('make_list'), []),
                        Seq([
                            While(
                                Call(Builtin('not_equal'), [predictor, Lit(epsilon_index)]),
                                Call(Builtin('list_push!'), [Var(xs, _any_type), _generate_parse_rhs_ir(rhs.rhs, None, grammar)])
                            ),
                            Var(xs, _any_type)
                        ])
                )
            else:
                parse_expr = Call(Builtin('make_list'), [])
        if rule and rule.action:
            var_name = gensym(rule.action.params[0] if rule.action.params else "arg")
            return Seq([Assign(Var(var_name, _any_type), parse_expr), _apply(rule.action, [Var(var_name, _any_type)])])
        return parse_expr
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
                var_name = gensym(rule.action.params[non_literal_count].name)
            else:
                var_name = gensym("arg")
            param_names.append(var_name)
            exprs.append(Assign(Var(var_name, _any_type), elem_ir))
            arg_vars.append(Var(var_name, _any_type))
            non_literal_count += 1

    # Build Lambda and Call
    if rule and rule.action:
        # Use the action's Lambda
        action_lambda = rule.action
    else:
        # Create default Lambda that returns list of arguments
        # Lambda([Var(arg0), Var(arg1), ...], Tuple([Var(arg0, _any_type), Var(arg1, _any_type), ...]))
        param_vars = [Var(name, _any_type) for name in param_names]
        list_expr = Call(Builtin('Tuple'), arg_vars)
        action_lambda = Lambda(param_vars, list_expr, return_type=_any_type)

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
            Lambda(params=func.params[1:], return_type=func.return_type, body=func.body),
            args[1:]
        )
        if isinstance(args[0], (Var, Lit)):
            return _subst(body, func.params[0].name, args[0])
        return Let(func.params[0], args[0], body)
    # TODO
    # assert False, f"Invalid application of {func} to {args}"
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
