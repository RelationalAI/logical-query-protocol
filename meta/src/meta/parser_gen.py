"""Language-independent LL(k) parser generation.

This module generates recursive-descent parsers from context-free grammars.
It produces a target-language-independent IR (intermediate representation)
that can then be translated to Python, Julia, or other languages.

Overview
--------
The parser generator takes a Grammar and produces a list of ParseNonterminalDef
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
- list_push(list, item): Mutating push to list (returns Void)
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

from .gensym import gensym
from .grammar import (
    Grammar,
    LitTerminal,
    NamedTerminal,
    Nonterminal,
    Option,
    Rhs,
    Rule,
    Sequence,
    Star,
    Terminal,
)
from .grammar_utils import is_epsilon, rhs_elements
from .proto_ast import ProtoField, ProtoMessage
from .target import (
    Assign,
    BaseType,
    Call,
    IfElse,
    Lambda,
    Let,
    ListExpr,
    ListType,
    Lit,
    NewMessage,
    OneOf,
    ParseNonterminal,
    ParseNonterminalDef,
    Seq,
    TargetExpr,
    Var,
    While,
)
from .target_builtins import make_builtin, make_builtin_with_type
from .target_utils import apply_lambda
from .terminal_sequence_set import ConcatSet, FirstSet, FollowSet, TerminalSequenceSet

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


def _proto_fields_by_name(
    proto_messages: dict[tuple[str, str], ProtoMessage] | None,
    module: str,
    name: str,
) -> dict[str, ProtoField]:
    """Return a name->ProtoField map for a proto message, or {} if not found."""
    if proto_messages is None:
        return {}
    proto_msg = proto_messages.get((module, name))
    if proto_msg is None:
        return {}
    result: dict[str, ProtoField] = {}
    for f in proto_msg.fields:
        result[f.name] = f
    for oneof in proto_msg.oneofs:
        for f in oneof.fields:
            result[f.name] = f
    return result


def _build_param_proto_fields(
    action: Lambda,
    proto_messages: dict[tuple[str, str], ProtoMessage] | None,
) -> dict[int, ProtoField]:
    """Map lambda parameter indices to protobuf ProtoField descriptors.

    Inspects the semantic action's body. When it is a NewMessage, cross-references
    field names with proto_messages to find proto fields.

    As a fallback, when the action's return type is a known proto message,
    matches parameter names to proto field names.

    Returns dict mapping parameter index to ProtoField.
    """
    if proto_messages is None:
        return {}
    body = action.body
    if isinstance(body, NewMessage):
        fields_by_name = _proto_fields_by_name(proto_messages, body.module, body.name)
        if not fields_by_name:
            return {}
        param_names = [p.name for p in action.params]
        result: dict[int, ProtoField] = {}
        for field_name, field_expr in body.fields:
            pf = fields_by_name.get(field_name)
            if pf is None:
                continue
            param_name = _extract_param_name(field_expr, param_names)
            if param_name is not None and param_name in param_names:
                param_idx = param_names.index(param_name)
                result.setdefault(param_idx, pf)
        return result
    # Fallback: match parameter names against the return type's proto fields.
    return _build_param_proto_fields_by_return_type(action, proto_messages)


def _build_param_proto_fields_by_return_type(
    action: Lambda,
    proto_messages: dict[tuple[str, str], ProtoMessage] | None,
) -> dict[int, ProtoField]:
    """Fallback: match parameter names to proto fields via the return type."""
    from .target import MessageType

    if proto_messages is None:
        return {}
    rt = action.return_type
    if not isinstance(rt, MessageType):
        return {}
    fields_by_name = _proto_fields_by_name(proto_messages, rt.module, rt.name)
    if not fields_by_name:
        return {}
    result: dict[int, ProtoField] = {}
    for i, param in enumerate(action.params):
        pf = fields_by_name.get(param.name)
        if pf is not None:
            result[i] = pf
    return result


def _extract_param_name(expr: TargetExpr, param_names: list[str]) -> str | None:
    """Extract the parameter name from a field expression.

    Handles:
    - Direct Var reference
    - Call(OneOf(...), [Var(...)]) wrapper
    - Call(Builtin(...), [Var(...), ...]) e.g. unwrap_option_or
    """
    from .target import Builtin

    if isinstance(expr, Var) and expr.name in param_names:
        return expr.name
    if isinstance(expr, Call):
        if isinstance(expr.func, OneOf) and expr.args:
            return _extract_param_name(expr.args[0], param_names)
        if isinstance(expr.func, Builtin) and expr.args:
            return _extract_param_name(expr.args[0], param_names)
    return None


def generate_parse_functions(
    grammar: Grammar,
    indent: str = "",
    proto_messages: dict[tuple[str, str], ProtoMessage] | None = None,
) -> list[ParseNonterminalDef]:
    parser_methods = []
    reachable, _ = grammar.analysis.partition_nonterminals_by_reachability()
    for nt in reachable:
        rules = grammar.rules[nt]
        method_code = _generate_parse_method(nt, rules, grammar, indent, proto_messages)
        parser_methods.append(method_code)
    return parser_methods


def _wrap_with_span(body: TargetExpr, return_type) -> TargetExpr:
    """Wrap a nonterminal body with span_start/record_span."""
    span_var = Var(gensym("span_start"), BaseType("Int64"))
    result_var = Var(gensym("result"), return_type)
    return Let(
        span_var,
        Call(make_builtin("span_start"), []),
        Let(
            result_var,
            body,
            Seq(
                [
                    Call(make_builtin("record_span"), [span_var]),
                    result_var,
                ]
            ),
        ),
    )


def _generate_parse_method(
    lhs: Nonterminal,
    rules: list[Rule],
    grammar: Grammar,
    indent: str = "",
    proto_messages: dict[tuple[str, str], ProtoMessage] | None = None,
) -> ParseNonterminalDef:
    """Generate parse method for a nonterminal with provenance tracking."""
    return_type = None
    rhs = None
    follow_set = FollowSet(grammar, lhs)
    if len(rules) == 1:
        rule = rules[0]
        rhs = _generate_parse_rhs_ir(
            rule.rhs, grammar, follow_set, True, rule.constructor, proto_messages
        )
        return_type = rule.constructor.return_type
    else:
        predictor = _build_predictor(grammar, rules)
        prediction = gensym("prediction")
        has_epsilon = any(is_epsilon(rule.rhs) for rule in rules)
        if has_epsilon:
            tail = Lit(None)
        else:
            tail = Call(
                make_builtin("error_with_token"),
                [
                    Lit(f"Unexpected token in {lhs}"),
                    Call(make_builtin("current_token"), []),
                ],
            )
        for i, rule in enumerate(rules):
            assert return_type is None or return_type == rule.constructor.return_type, (
                f"Return type mismatch at rule {i}: {return_type} != {rule.constructor.return_type}"
            )
            return_type = rule.constructor.return_type
            if is_epsilon(rule.rhs):
                continue
            tail = IfElse(
                Call(
                    make_builtin("equal"), [Var(prediction, BaseType("Int64")), Lit(i)]
                ),
                _generate_parse_rhs_ir(
                    rule.rhs,
                    grammar,
                    follow_set,
                    True,
                    rule.constructor,
                    proto_messages,
                ),
                tail,
            )
        rhs = Let(Var(prediction, BaseType("Int64")), predictor, tail)
    assert return_type is not None
    rhs = _wrap_with_span(rhs, return_type)
    return ParseNonterminalDef(lhs, [], return_type, rhs, indent)


def _build_predictor(grammar: Grammar, rules: list[Rule]) -> TargetExpr:
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
    return _build_predictor_tree(
        grammar, rules, active_indices, nullable, default, depth=0
    )


def _build_predictor_tree(
    grammar: Grammar,
    rules: list[Rule],
    active_indices: list[int],
    nullable: dict[Nonterminal, bool],
    default: TargetExpr,
    depth: int,
) -> TargetExpr:
    """Build a decision tree for predicting which rule matches.

    Lazily computes FIRST_k at each depth, only for rules that need more
    lookahead. Groups by token at current depth, then recurses.
    """
    if not active_indices:
        return default
    if depth >= MAX_LOOKAHEAD:
        conflict_rules = "\n  ".join(f"Rule {i}: {rules[i]}" for i in active_indices)
        raise GrammarConflictError(
            f"Grammar conflict at lookahead depth {depth}:\n  {conflict_rules}"
        )
    groups: dict[Terminal, list[int]] = {}
    exhausted: set[int] = set()
    for rule_idx in active_indices:
        rule = rules[rule_idx]
        rule_first = grammar.analysis.first_k_of(depth + 1, rule.rhs)
        tokens_at_depth: set[Terminal] = set()
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
        conflict_rules = "\n  ".join(f"Rule {i}: {rules[i]}" for i in sorted(exhausted))
        raise GrammarConflictError(
            f"Grammar conflict: multiple rules fully consumed at lookahead depth {depth}:\n  {conflict_rules}"
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
            then_branch = _build_predictor_tree(
                grammar, rules, indices, nullable, subtree_default, depth + 1
            )
        result = IfElse(check, then_branch, result)
    return result


def _build_token_check(term: Terminal, depth: int) -> TargetExpr:
    """Build a check for a single token at a given lookahead depth."""
    if isinstance(term, LitTerminal):
        return Call(
            make_builtin("match_lookahead_literal"), [Lit(term.name), Lit(depth)]
        )
    elif isinstance(term, NamedTerminal):
        return Call(
            make_builtin("match_lookahead_terminal"), [Lit(term.name), Lit(depth)]
        )
    else:
        return Lit(False)


def _build_lookahead_check(
    token_sequences: set[tuple[Terminal, ...]], depth: int
) -> TargetExpr:
    """Build a boolean expression that checks if lookahead matches any of the token sequences.

    Args:
        token_sequences: Set of token sequences to match
        depth: Current lookahead depth

    Returns a boolean expression.
    """
    if not token_sequences:
        return Lit(False)

    groups: dict[Terminal, set[tuple[Terminal, ...]]] = {}
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


def _build_option_predictor(
    grammar: Grammar, element: Rhs, follow_set: TerminalSequenceSet
) -> TargetExpr:
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
    conflict_msg = f"Ambiguous Option/Star: FIRST_{MAX_LOOKAHEAD}({element}) and follow set overlap"
    raise AmbiguousGrammarError(conflict_msg)


def _generate_parse_rhs_ir(
    rhs: Rhs,
    grammar: Grammar,
    follow_set: TerminalSequenceSet,
    apply_action: bool = False,
    action: Lambda | None = None,
    proto_messages: dict[tuple[str, str], ProtoMessage] | None = None,
) -> TargetExpr:
    """Generate IR for parsing an RHS with provenance tracking."""
    if isinstance(rhs, Sequence):
        return _generate_parse_rhs_ir_sequence(
            rhs, grammar, follow_set, apply_action, action, proto_messages
        )
    elif isinstance(rhs, LitTerminal):
        parse_expr = Call(make_builtin("consume_literal"), [Lit(rhs.name)])
        if apply_action and action:
            return Seq([parse_expr, apply_lambda(action, [])])
        return parse_expr
    elif isinstance(rhs, NamedTerminal):
        from .target import FunctionType

        terminal_type = rhs.target_type()
        consume_builtin = make_builtin_with_type(
            "consume_terminal", FunctionType([BaseType("String")], terminal_type)
        )
        parse_expr = Call(consume_builtin, [Lit(rhs.name)])
        if apply_action and action:
            if len(action.params) == 0:
                return Seq([parse_expr, apply_lambda(action, [])])
            var_name = gensym(action.params[0].name)
            var = Var(var_name, rhs.target_type())
            return Let(var, parse_expr, apply_lambda(action, [var]))
        return parse_expr
    elif isinstance(rhs, Nonterminal):
        parse_expr = Call(ParseNonterminal(rhs), [])
        if apply_action and action:
            if len(action.params) == 0:
                return Seq([parse_expr, apply_lambda(action, [])])
            var_name = gensym(action.params[0].name)
            var = Var(var_name, rhs.target_type())
            # Wrap with push_path when the action maps this param to a proto
            # field (e.g., oneof dispatch: formula -> atom pushes the atom
            # field number onto the provenance path).
            if proto_messages is not None:
                pf = _build_param_proto_fields(action, proto_messages).get(0)
                if pf is not None:
                    stmts = _wrap_with_path(pf.number, var, parse_expr)
                    stmts.append(apply_lambda(action, [var]))
                    return Seq(stmts)
            return Let(var, parse_expr, apply_lambda(action, [var]))
        return parse_expr
    elif isinstance(rhs, Option):
        assert grammar is not None
        predictor = _build_option_predictor(grammar, rhs.rhs, follow_set)
        parse_result = _generate_parse_rhs_ir(
            rhs.rhs, grammar, follow_set, False, None, proto_messages
        )
        return IfElse(predictor, Call(make_builtin("some"), [parse_result]), Lit(None))
    elif isinstance(rhs, Star):
        assert grammar is not None
        xs = Var(gensym("xs"), ListType(rhs.rhs.target_type()))
        cond = Var(gensym("cond"), BaseType("Boolean"))
        predictor = _build_option_predictor(grammar, rhs.rhs, follow_set)
        parse_item = _generate_parse_rhs_ir(
            rhs.rhs, grammar, follow_set, False, None, proto_messages
        )
        item = Var(gensym("item"), rhs.rhs.target_type())
        loop_body = Seq(
            [
                Assign(item, parse_item),
                Call(make_builtin("list_push"), [xs, item]),
                Assign(cond, predictor),
            ]
        )
        return Let(
            xs,
            ListExpr([], rhs.rhs.target_type()),
            Let(cond, predictor, Seq([While(cond, loop_body), xs])),
        )
    else:
        raise NotImplementedError(f"Unsupported Rhs type: {type(rhs)}")


def _wrap_with_path(field_num: int, var: Var, inner: TargetExpr) -> list[TargetExpr]:
    """Return statements that push path, assign inner to var, then pop path."""
    return [
        Call(make_builtin("push_path"), [Lit(field_num)]),
        Assign(var, inner),
        Call(make_builtin("pop_path"), []),
    ]


def _generate_parse_rhs_ir_sequence(
    rhs: Sequence,
    grammar: Grammar,
    follow_set: TerminalSequenceSet,
    apply_action: bool = False,
    action: Lambda | None = None,
    proto_messages: dict[tuple[str, str], ProtoMessage] | None = None,
) -> TargetExpr:
    if is_epsilon(rhs):
        return Lit(None)

    # Compute param->proto field mapping for provenance
    param_proto_fields: dict[int, ProtoField] = {}
    if action is not None and proto_messages is not None:
        param_proto_fields = _build_param_proto_fields(action, proto_messages)

    exprs = []
    arg_vars = []
    elems = list(rhs_elements(rhs))
    non_literal_count = 0
    for i, elem in enumerate(elems):
        if i + 1 < len(elems):
            following = Sequence(tuple(elems[i + 1 :]))
            first_following = FirstSet(grammar, following)
            follow_set_i = ConcatSet(first_following, follow_set)
        else:
            follow_set_i = follow_set
        elem_ir = _generate_parse_rhs_ir(
            elem, grammar, follow_set_i, False, None, proto_messages
        )
        if isinstance(elem, LitTerminal):
            exprs.append(elem_ir)
        else:
            if action and non_literal_count < len(action.params):
                var_name = gensym(action.params[non_literal_count].name)
            else:
                if action is not None and non_literal_count >= len(action.params):
                    raise ValueError(
                        f"Action parameter count mismatch: action has {len(action.params)} params "
                        f"but sequence has at least {non_literal_count + 1} non-literal elements"
                    )
                var_name = gensym("arg")
            var = Var(var_name, elem.target_type())
            pf = param_proto_fields.get(non_literal_count)
            if pf is not None and pf.is_repeated and isinstance(elem, Star):
                # Repeated proto field parsed as a Star: push field number
                # around the whole loop and push/pop an index per element.
                stmts = _wrap_star_with_index_path(
                    elem, var, grammar, follow_set_i, pf.number, proto_messages
                )
                exprs.extend(stmts)
            elif isinstance(elem, Star) and proto_messages is not None:
                # Star without a repeated proto field (helper rule): still
                # push/pop an index per element for provenance.
                stmts = _wrap_star_with_index_path(
                    elem, var, grammar, follow_set_i, None, proto_messages
                )
                exprs.extend(stmts)
            elif pf is not None:
                exprs.extend(_wrap_with_path(pf.number, var, elem_ir))
            else:
                exprs.append(Assign(var, elem_ir))
            arg_vars.append(var)
            non_literal_count += 1
    if apply_action and action:
        lambda_call = apply_lambda(action, arg_vars)
        exprs.append(lambda_call)
    elif len(arg_vars) > 1:
        exprs.append(Call(make_builtin("tuple"), arg_vars))
    elif len(arg_vars) == 1:
        exprs.append(arg_vars[0])
    else:
        return Lit(None)

    if len(exprs) == 1:
        return exprs[0]
    else:
        return Seq(exprs)


def _wrap_star_with_index_path(
    star: Star,
    result_var: Var,
    grammar: Grammar,
    follow_set: TerminalSequenceSet,
    field_num: int | None,
    proto_messages: dict[tuple[str, str], ProtoMessage] | None = None,
) -> list[TargetExpr]:
    """Return statements for a Star loop with push_path(index)/pop_path()
    around each element. When field_num is provided, the entire loop is
    also wrapped with push_path(field_num)/pop_path().
    Assigns the resulting list to result_var."""
    xs = Var(gensym("xs"), ListType(star.rhs.target_type()))
    cond = Var(gensym("cond"), BaseType("Boolean"))
    idx = Var(gensym("idx"), BaseType("Int64"))
    predictor = _build_option_predictor(grammar, star.rhs, follow_set)
    parse_item = _generate_parse_rhs_ir(
        star.rhs, grammar, follow_set, False, None, proto_messages
    )
    item = Var(gensym("item"), star.rhs.target_type())
    loop_body = Seq(
        [
            Call(make_builtin("push_path"), [idx]),
            Assign(item, parse_item),
            Call(make_builtin("pop_path"), []),
            Call(make_builtin("list_push"), [xs, item]),
            Assign(idx, Call(make_builtin("add"), [idx, Lit(1)])),
            Assign(cond, predictor),
        ]
    )
    inner = Let(
        xs,
        ListExpr([], star.rhs.target_type()),
        Let(
            cond,
            predictor,
            Let(
                idx,
                Lit(0),
                Seq([While(cond, loop_body), xs]),
            ),
        ),
    )
    if field_num is not None:
        return [
            Call(make_builtin("push_path"), [Lit(field_num)]),
            Assign(result_var, inner),
            Call(make_builtin("pop_path"), []),
        ]
    return [Assign(result_var, inner)]
