"""Language-independent parser generation.

This module contains language-independent logic for generating LL(k)
recursive-descent parsers from grammars, including:
- IR generation for parsing logic
- Decision tree construction
- Grammar analysis and transformation
"""

from typing import Dict, List, Optional, Set, Tuple

from .grammar import Grammar, Rule, Rhs, Literal, Terminal, Nonterminal, Star, Plus, Option
from .target import Lambda, Call, ParseNonterminalDef, Var, Lit, Symbol, Builtin, Let, IfElse, FunDef, BaseType, ListType, TargetExpr, Seq, While, TryCatch, Assign, Type, ParseNonterminal, ParseNonterminalDef


def is_epsilon(rhs):
    return isinstance(rhs, list) and len(rhs) == 0


def _make_call(func: TargetExpr, args: List[TargetExpr] = None) -> Call:
    """Create a function call.

    Args:
        func: Function expression (typically Var or Symbol)
        args: List of argument expressions
    """
    if args is None:
        args = []
    return Call(func, args)

def generate_rules(grammar: Grammar) -> List[ParseNonterminalDef]:
    reachable, is_ll2, conflicts, nullable, first, first_2, follow = prepare_grammar(grammar)

    # Generate parser methods as strings
    parser_methods = []
    rule_order = grammar.traverse_rules_preorder(reachable_only=(reachable is not None))
    for nt_name in rule_order:
        if reachable is not None and nt_name not in reachable:
            continue

        rules = grammar.rules[nt_name]

        method_code = _generate_parse_method(
            nt_name, rules,
            grammar, nullable, first_2, reachable
        )
        parser_methods.append(method_code)

    return parser_methods


def prepare_grammar(grammar: Grammar) -> Tuple[Set[str], bool, List[str], Dict[str, bool], Dict[str, Set[str]], Dict[str, Set[Tuple[str, ...]]], Dict[str, Set[str]]]:
    """Prepare grammar for parser generation.

    Returns:
        - reachable: Set of reachable nonterminals
        - is_ll2: Whether grammar is LL(2)
        - conflicts: List of conflict messages
        - nullable: Nullable set
        - first: FIRST sets
        - first_2: FIRST_2 sets
        - follow: FOLLOW sets
    """
    reachable = grammar.check_reachability()

    # Check LL(2)
    is_ll2, conflicts = grammar.check_ll_k(k=2)

    # Compute analysis sets
    nullable = grammar.compute_nullable()
    first = grammar.compute_first(nullable)
    first_2 = grammar.compute_first_k(k=2, nullable=nullable)
    follow = grammar.compute_follow(nullable, first)

    return reachable, is_ll2, conflicts, nullable, first, first_2, follow


def _generate_parse_method(
    lhs: str,
    rules: List[Rule],
    grammar: Grammar,
    nullable,
    first_2,
    reachable) -> ParseNonterminalDef:

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
            tail = IfElse(Call(predictor, i), _generate_parse_rhs_ir(rule.rhs, rule, grammar), tail)

        rhs = tail

    return ParseNonterminalDef(Nonterminal(lhs), [], BaseType('Any'), rhs)

def _build_predictor(grammar, lhs, rules):
    assert len(rules) > 1

    for i, rule in enumerate(rules):
        if is_epsilon(rule.rhs):
            continue

    predictor = Call(Builtin('predict'), [Lit(lhs), Lit(len(rules))])
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
                lines = TryCatch(try_parse, 'ParseError', Seq([
                    Call(Builtin('restore_position'), [Var('saved_pos')]),
                    lines
                ]))
            body = Let(Var('saved_pos'), Call(Builtin('save_position'), []), lines)
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

def _generate_parse_rhs_ir(rhs: List[Rhs], rule: Optional[Rule] = None, grammar: Optional[Grammar] = None) -> Optional[TargetExpr]:
    """Generate IR for parsing an RHS.

    Returns IR expression for leaf nodes (Literal, Terminal, Nonterminal).
    Returns None for complex cases that still use string generation.
    """
    if not rhs:
        # Empty sequence returns None
        return Lit(None)

    # Parse sequence
    # Parse each element
    literal_exprs = []  # Literals executed for side effects
    arg_exprs = []  # Non-literal arguments to pass to Lambda
    param_names = []  # Parameter names for Lambda

    for i, elem in enumerate(rhs):
        elem_ir = _generate_parse_rhs_ir1(elem, None, grammar)
        if elem_ir is None:
            # Element not yet supported in IR
            return None

        if isinstance(elem, Literal):
            # Literal: execute for side effect
            literal_exprs.append(elem_ir)
        else:
            # Non-literal: will be passed as argument
            arg_exprs.append(elem_ir)
            if rule and rule.action and i < len(rule.action.params):
                param_names.append(rule.action.params[i - len(literal_exprs)])
            else:
                param_names.append(f"_arg{len(param_names)}")

    # Build Lambda and Call
    if rule and rule.action:
        # Use the action's Lambda
        action_lambda = rule.action
    else:
        # Create default Lambda that returns list of arguments
        # Lambda([arg0, arg1, ...], MakeList([Var(arg0), Var(arg1), ...]))
        list_expr = Call(Builtin('Tuple'), [Var(p) for p in param_names])
        action_lambda = Lambda(param_names, list_expr)

    # Call the Lambda with parsed arguments
    lambda_call = Call(action_lambda, arg_exprs)

    # Wrap in Seq if there are literals
    if literal_exprs:
        literal_exprs.append(lambda_call)
        return Seq(literal_exprs)
    else:
        return lambda_call

def _generate_parse_rhs_ir1(rhs: Rhs, rule: Optional[Rule] = None, grammar: Optional[Grammar] = None) -> Optional[TargetExpr]:
    """Generate IR for parsing an RHS.

    Returns IR expression for leaf nodes (Literal, Terminal, Nonterminal).
    Returns None for complex cases that still use string generation.
    """
    if isinstance(rhs, Literal):
        # Build IR: Call(Builtin('consume_literal'), [Lit(literal)])
        return Call(Builtin('consume_literal'), [Lit(rhs.name)])
    elif isinstance(rhs, Terminal):
        # Build IR: Call(Builtin('consume_terminal'), [Lit(terminal.name)])
        return Call(Builtin('consume_terminal'), [Lit(rhs.name)])
    elif isinstance(rhs, Nonterminal):
        # Build IR: ParseNonterminal(nonterminal, [])
        return ParseNonterminal(rhs, [])
    elif isinstance(rhs, Option):
        if isinstance(rhs.rhs, Terminal):
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
                _generate_parse_rhs_ir([rhs.rhs], None, grammar),
                Lit(None)
            )
    elif isinstance(rhs, Star):
        if isinstance(rhs.rhs, Terminal):
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
                                _generate_parse_rhs_ir([rhs.rhs], None, grammar),
                                Call(Builtin('append'), [Var('xs'), Var('x')])
                            )
                        ),
                        Var('xs')
                    ])
            )
    else:
        assert False, f"Unsupported RHS type: {type(rhs)}"

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
    has_epsilon = any(len(rule.rhs) == 0 for rule in rules)

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
        try_body = _generate_parse_rhs_ir(Sequence(rule.rhs), rule, grammar)

        # Restore position in catch
        restore = Call(Builtin('restore_position'), [Var('saved_pos')])

        body = TryCatch(
            try_body=try_body,
            exception_type='ParseError',
            catch_body=Seq([restore, body])
        )

    # Save position at the start
    save = Assign(var='saved_pos', expr=Call(Builtin('save_position'), []))

    return Seq([save, body])


def generate_parse_method_ir(nt_name: str, rules: List[Rule],
                              is_continuation: bool, grammar: Grammar,
                              nullable: Dict[str, bool]) -> FunDef:
    """Generate parse method as FunDef IR.

    Returns a FunDef with:
    - name: parse_{nt_name}
    - params: [(prefix_results, Type)] if is_continuation else []
    - return_type: BaseType('Any')
    - body: Seq of parse logic
    """
    func_name = f"parse_{nt_name}"

    # Build parameters
    if is_continuation:
        params = [("prefix_results", ListType(BaseType('Any')))]
    else:
        params = []

    # Build body
    if len(rules) == 1:
        # Single rule - simpler body
        rule = rules[0]
        body = _generate_parse_rhs_ir(Sequence(rule.rhs), rule, grammar)
    else:
        # Multiple rules - need decision tree
        from .analysis import _compute_rhs_first_k

        # Use fixed k=2 lookahead
        min_k = 2
        first_k_final = grammar.compute_first_k(min_k, nullable)

        # Collect sequences and group by tokens progressively
        first_token_to_rules = {}

        for rule_idx, rule in enumerate(rules):
            sequences = _compute_rhs_first_k(Sequence(rule.rhs), first_k_final, nullable, min_k)

            for seq in sequences:
                if len(seq) == 0:
                    continue
                first_token = seq[0]

                if first_token not in first_token_to_rules:
                    first_token_to_rules[first_token] = []
                first_token_to_rules[first_token].append((seq, rule_idx))

        # Build decision tree as IR
        body = _build_decision_tree_ir(first_token_to_rules, rules, nt_name, 0, min_k, is_continuation, grammar)

    return FunDef(
        name=func_name,
        params=params,
        return_type=BaseType('Any'),
        body=body
    )
