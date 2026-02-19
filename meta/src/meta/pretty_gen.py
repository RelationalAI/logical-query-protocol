"""Pretty printer generator.

Generates pretty-printer visitor methods from grammar rules. Each nonterminal
gets a pretty_X method that deconstructs a protobuf message according to the
rule's deconstruct action, then prints the RHS elements.

For nonterminals with multiple rules, rules are tried in specificity order
(most specific first), using the deconstructor to determine which rule matches.
"""

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
)
from .grammar_utils import is_epsilon, rhs_elements
from .target import (
    BaseType,
    Builtin,
    Call,
    ForeachEnumerated,
    GetElement,
    IfElse,
    Lambda,
    Let,
    ListType,
    Lit,
    OptionType,
    PrintNonterminal,
    PrintNonterminalDef,
    Return,
    Seq,
    SequenceType,
    TargetExpr,
    TupleType,
    Var,
    gensym,
)
from .target_builtins import STRING, VOID, make_builtin


def generate_pretty_functions(
    grammar: Grammar, proto_messages: dict | None = None
) -> list[PrintNonterminalDef]:
    """Generate pretty printer functions for all nonterminals."""
    pretty_methods = []

    rule_order, _ = grammar.analysis.partition_nonterminals_by_reachability()
    reachable = grammar.analysis.reachability
    nonterminals = [nt for nt in rule_order if reachable is None or nt in reachable]

    for nt in nonterminals:
        rules = grammar.rules[nt]
        method_code = _generate_pretty_method(nt, rules, grammar, proto_messages)
        pretty_methods.append(method_code)
    return pretty_methods


def _generate_pretty_method(
    lhs: Nonterminal,
    rules: list[Rule],
    grammar: Grammar,
    proto_messages: dict | None,
) -> PrintNonterminalDef:
    """Generate a pretty-print visitor method for a nonterminal."""
    nt = rules[0].lhs
    msg_param = Var("msg", nt.type)

    if len(rules) == 1:
        body = _generate_pretty_with_deconstruct(
            rules[0], msg_param, grammar, proto_messages
        )
    else:
        body = _generate_pretty_alternatives(rules, msg_param, grammar, proto_messages)

    if not _is_all_literals(rules):
        body = _wrap_with_try_flat(nt, msg_param, body)

    return PrintNonterminalDef(
        nonterminal=nt,
        params=[msg_param],
        return_type=VOID,
        body=body,
    )


def _wrap_with_try_flat(
    nt: Nonterminal, msg_param: Var, body: TargetExpr
) -> TargetExpr:
    """Wrap a pretty function body with a try_flat preamble.

    Generates the equivalent of:
        _flat = try_flat(pp, msg, pretty_<nt>)
        if _flat is not nothing
            write(pp, _flat)
            return nothing
        else
            <body>
        end
    """
    flat_var = Var(gensym("flat"), OptionType(STRING))
    try_flat_call = Call(make_builtin("try_flat_io"), [msg_param, PrintNonterminal(nt)])
    flat_write = Seq(
        [
            Call(
                make_builtin("write_io"),
                [Call(make_builtin("unwrap_option"), [flat_var])],
            ),
            Return(Lit(None)),
        ]
    )
    return Let(
        flat_var,
        try_flat_call,
        IfElse(Call(make_builtin("is_some"), [flat_var]), flat_write, body),
    )


def _generate_pretty_alternatives(
    rules: list[Rule], msg_param: Var, grammar: Grammar, proto_messages: dict | None
) -> TargetExpr:
    """Generate if-else chain trying rules in declaration order.

    Rules are tried in the order they appear in the grammar. For each rule,
    the deconstructor is called; if it returns non-None, that rule is used.
    The last rule with a trivial (always-matching) deconstructor serves as
    the fallback.
    """
    # Find the last rule with a trivial deconstructor to use as fallback.
    # All other rules are tried in declaration order before it.
    fallback_idx: int | None = None
    for i in range(len(rules) - 1, -1, -1):
        rule = rules[i]
        if is_epsilon(rule.rhs):
            fallback_idx = i
            break
        if rule.deconstructor is None or _is_trivial_deconstruct(rule.deconstructor):
            fallback_idx = i
            break
        if not (_is_guarded_rule(rule, grammar)):
            fallback_idx = i
            break

    if fallback_idx is not None:
        result: TargetExpr = _generate_pretty_with_deconstruct(
            rules[fallback_idx], msg_param, grammar, proto_messages
        )
    else:
        result = Call(
            make_builtin("error"), [Lit(f"No matching rule for {rules[0].lhs.name}")]
        )

    # Build if-else chain in reverse declaration order (so first-declared ends up outermost)
    guarded_indices = [i for i in range(len(rules)) if i != fallback_idx]
    for i in reversed(guarded_indices):
        rule = rules[i]
        if rule.deconstructor is not None and isinstance(
            rule.deconstructor.return_type, OptionType
        ):
            deconstruct_result_var = Var(
                gensym("deconstruct_result"), rule.deconstructor.return_type
            )
            deconstruct_call = Call(rule.deconstructor, [msg_param])
            # Unwrap the option inside the is_some guard
            inner_type = rule.deconstructor.return_type.element_type
            unwrapped_var = Var(gensym("unwrapped"), inner_type)
            pretty_body = _generate_pretty_from_fields(
                rule.rhs, unwrapped_var, grammar, proto_messages
            )
            result = Let(
                deconstruct_result_var,
                deconstruct_call,
                IfElse(
                    Call(make_builtin("is_some"), [deconstruct_result_var]),
                    Let(
                        unwrapped_var,
                        Call(make_builtin("unwrap_option"), [deconstruct_result_var]),
                        pretty_body,
                    ),
                    result,
                ),
            )
        elif _is_nonterminal_ref(rule) and _has_guarded_deconstruct(rule.rhs, grammar):
            result = _generate_nonterminal_ref_dispatch(
                rule, msg_param, grammar, proto_messages, result
            )
        else:
            # Unguarded non-fallback rule — treat as always matching at this position
            result = _generate_pretty_with_deconstruct(
                rule, msg_param, grammar, proto_messages
            )

    return result


def _is_guarded_rule(rule: Rule, grammar: Grammar) -> bool:
    """Check if a rule has a guard (Optional deconstructor or guarded nonterminal ref)."""
    if _is_nonterminal_ref(rule) and _has_guarded_deconstruct(rule.rhs, grammar):
        return True
    if rule.deconstructor is not None and isinstance(
        rule.deconstructor.return_type, OptionType
    ):
        return True
    return False


def _is_nonterminal_ref(rule: Rule) -> bool:
    """Check if a rule's RHS is a single nonterminal reference."""
    return isinstance(rule.rhs, Nonterminal)


def _has_guarded_deconstruct(nt_ref: Rhs, grammar: Grammar) -> bool:
    """Check if a referenced nonterminal has a guarded (Optional) deconstructor."""
    if not isinstance(nt_ref, Nonterminal):
        return False
    rules_dict = grammar.rules
    for nt, rules in rules_dict.items():
        if nt.name == nt_ref.name:
            return any(
                r.deconstructor is not None
                and isinstance(r.deconstructor.return_type, OptionType)
                for r in rules
            )
    return False


def _generate_nonterminal_ref_dispatch(
    rule: Rule,
    msg_param: Var,
    grammar: Grammar,
    proto_messages: dict | None,
    fallback: TargetExpr,
) -> TargetExpr:
    """Generate dispatch for a nonterminal-reference alternative.

    Uses the referenced nonterminal's deconstructor as the guard condition,
    then calls the referenced nonterminal's pretty printer if matched.
    """
    nt_ref = rule.rhs
    assert isinstance(nt_ref, Nonterminal)

    rules_dict = grammar.rules
    subrule_rules = None
    for nt, rules in rules_dict.items():
        if nt.name == nt_ref.name:
            subrule_rules = rules
            break

    if subrule_rules is None:
        return fallback

    # Find the first rule with an Optional deconstructor (guard)
    guard_deconstructor = None
    for r in subrule_rules:
        if r.deconstructor is not None and isinstance(
            r.deconstructor.return_type, OptionType
        ):
            guard_deconstructor = r.deconstructor
            break

    if guard_deconstructor is None:
        return Call(PrintNonterminal(nt_ref), [msg_param])

    deconstruct_result_var = Var(
        gensym("guard_result"), guard_deconstructor.return_type
    )
    deconstruct_call = Call(guard_deconstructor, [msg_param])
    pretty_call = Call(PrintNonterminal(nt_ref), [msg_param])

    return Let(
        deconstruct_result_var,
        deconstruct_call,
        IfElse(
            Call(make_builtin("is_some"), [deconstruct_result_var]),
            pretty_call,
            fallback,
        ),
    )


def _generate_pretty_with_deconstruct(
    rule: Rule, msg_param: Var, grammar: Grammar, proto_messages: dict | None
) -> TargetExpr:
    """Generate pretty printing using the deconstructor to extract fields."""
    if rule.deconstructor is None or _is_trivial_deconstruct(rule.deconstructor):
        deconstructor = rule.deconstructor
        if deconstructor is not None:
            fields_expr = _extract_trivial_deconstruct_result(deconstructor, msg_param)
            if isinstance(deconstructor.return_type, OptionType):
                unwrapped_type = deconstructor.return_type.element_type
            else:
                unwrapped_type = deconstructor.return_type
        else:
            fields_expr = msg_param
            unwrapped_type = msg_param.type

        fields_var = Var(gensym("fields"), unwrapped_type)
        pretty_body = _generate_pretty_from_fields(
            rule.rhs, fields_var, grammar, proto_messages
        )
        return Let(fields_var, fields_expr, pretty_body)

    # Non-trivial deconstruct — call the lambda
    deconstructor = rule.deconstructor
    deconstruct_result_var = Var(gensym("fields"), deconstructor.return_type)
    deconstruct_call = Call(deconstructor, [msg_param])

    if isinstance(deconstructor.return_type, OptionType):
        unwrapped_type = deconstructor.return_type.element_type
    else:
        unwrapped_type = deconstructor.return_type

    unwrapped_var = Var(gensym("unwrapped_fields"), unwrapped_type)
    unwrap_expr = Call(make_builtin("unwrap_option"), [deconstruct_result_var])

    pretty_body = _generate_pretty_from_fields(
        rule.rhs, unwrapped_var, grammar, proto_messages
    )

    return Let(
        deconstruct_result_var,
        deconstruct_call,
        Let(unwrapped_var, unwrap_expr, pretty_body),
    )


def _generate_pretty_from_fields(
    rhs: Rhs, fields_var: Var, grammar: Grammar, proto_messages: dict | None
) -> TargetExpr:
    """Generate pretty printing code given extracted field values."""
    if isinstance(rhs, Sequence):
        return _generate_pretty_sequence_from_fields(
            rhs, fields_var, grammar, proto_messages
        )
    elif isinstance(rhs, LitTerminal):
        return _format_literal(rhs)
    elif isinstance(rhs, NamedTerminal):
        formatted = _format_terminal(rhs, fields_var)
        return Call(make_builtin("write_io"), [formatted])
    elif isinstance(rhs, Nonterminal):
        return Call(PrintNonterminal(rhs), [fields_var])
    elif isinstance(rhs, Option):
        return _generate_pretty_option_from_field(
            rhs, fields_var, grammar, proto_messages
        )
    elif isinstance(rhs, Star):
        return _generate_pretty_star_from_field(
            rhs, fields_var, grammar, proto_messages
        )
    else:
        assert False, f"Unsupported Rhs type: {type(rhs)}"


def _get_tuple_type(t) -> TupleType | None:
    """Unwrap OptionType if present and return TupleType, or None."""
    if isinstance(t, TupleType):
        return t
    if isinstance(t, OptionType) and isinstance(t.element_type, TupleType):
        return t.element_type
    return None


def _generate_pretty_sequence_from_fields(
    rhs: Sequence, fields_var: Var, grammar: Grammar, proto_messages: dict | None
) -> TargetExpr:
    """Generate pretty printing for a sequence using extracted field values."""
    if is_epsilon(rhs):
        return Lit(None)

    elems = list(rhs_elements(rhs))
    stmts: list[TargetExpr] = []
    field_idx = 0

    NO_TRAILING_SPACE = {"(", "[", ":", "#", "::"}
    NO_LEADING_SPACE = {")", "]", "}", "::"}

    # Detect S-expression pattern: first element is "(", second is a keyword literal
    is_sexp = (
        len(elems) >= 2
        and isinstance(elems[0], LitTerminal)
        and elems[0].name == "("
        and isinstance(elems[1], LitTerminal)
        and elems[1].name != "("
    )

    # Detect brace-delimited block: "{" ... "}"
    last_elem = elems[-1] if elems else None
    is_brace = (
        len(elems) >= 2
        and isinstance(elems[0], LitTerminal)
        and elems[0].name == "{"
        and isinstance(last_elem, LitTerminal)
        and last_elem.name == "}"
    )

    # Count non-literal elements to determine if fields_var is a tuple or single value
    non_lit_count = sum(1 for e in elems if not isinstance(e, LitTerminal))

    first_elem = elems[0] if elems else None
    last_elem = elems[-1] if elems else None

    def _is_delimited(open_delim: str, close_delim: str) -> bool:
        return (
            non_lit_count > 0
            and len(elems) >= 2
            and isinstance(first_elem, LitTerminal)
            and first_elem.name == open_delim
            and isinstance(last_elem, LitTerminal)
            and last_elem.name == close_delim
        )

    is_bracket_group = _is_delimited("[", "]")
    is_paren_group = not is_sexp and _is_delimited("(", ")")
    is_brace_group = _is_delimited("{", "}")

    # Whether this is a structured group that uses newlines between children
    is_group = is_sexp or is_bracket_group or is_paren_group or is_brace_group

    # Track the previous element's literal name for spacing decisions
    prev_lit_name: str | None = None

    for i, elem in enumerate(elems):
        is_optional_or_star = isinstance(elem, (Option, Star))

        # Compute leading whitespace for this element
        leading_ws: list[TargetExpr] = []
        if isinstance(elem, LitTerminal):
            if is_group and i >= 2 and elem.name not in NO_LEADING_SPACE:
                # Group spacing: newline before non-bracket-closing literals
                stmts.append(Call(make_builtin("newline_io"), []))
            elif is_brace and i >= 1 and elem.name not in NO_LEADING_SPACE:
                # Brace spacing: newline before non-bracket-closing literals
                stmts.append(Call(make_builtin("newline_io"), []))
            elif not is_group and not is_brace and stmts:
                cur_lit_name = elem.name
                suppress = False
                if prev_lit_name in NO_TRAILING_SPACE:
                    suppress = True
                if cur_lit_name in NO_LEADING_SPACE:
                    suppress = True
                if not suppress:
                    stmts.append(Call(make_builtin("write_io"), [Lit(" ")]))
        else:
            if is_group:
                if prev_lit_name in NO_TRAILING_SPACE:
                    # After opening brackets, no whitespace
                    pass
                else:
                    # Group spacing: newline before each non-literal
                    leading_ws = [Call(make_builtin("newline_io"), [])]
            elif is_brace:
                if prev_lit_name == "{":
                    # First element after {: space, not newline
                    leading_ws = [Call(make_builtin("write_io"), [Lit(" ")])]
                elif prev_lit_name in NO_TRAILING_SPACE:
                    pass
                else:
                    leading_ws = [Call(make_builtin("newline_io"), [])]
            elif stmts:
                # Non-group spacing between elements
                cur_lit_name = None
                suppress = False
                if prev_lit_name in NO_TRAILING_SPACE:
                    suppress = True
                if not suppress:
                    leading_ws = [Call(make_builtin("write_io"), [Lit(" ")])]

        if isinstance(elem, LitTerminal):
            is_keyword = is_sexp and i == 1

            # Closing delimiter: emit dedent before
            is_closing = (
                (is_sexp and elem.name == ")" and non_lit_count > 0)
                or (is_bracket_group and elem.name == "]")
                or (is_paren_group and elem.name == ")")
            )
            if is_closing:
                stmts.append(Call(make_builtin("dedent_io"), []))
            # For brace closing, emit dedent if we indented
            if is_brace and elem.name == "}" and non_lit_count > 0:
                stmts.append(Call(make_builtin("dedent_io"), []))
            stmts.append(_format_literal(elem))

            # Opening delimiter/keyword: emit indent after
            if is_keyword and non_lit_count > 0:
                stmts.append(Call(make_builtin("indent_sexp_io"), []))
            elif (is_bracket_group and elem.name == "[") or (
                is_paren_group and elem.name == "("
            ):
                stmts.append(Call(make_builtin("indent_io"), []))
            # After opening brace, emit indent
            if is_brace and elem.name == "{" and non_lit_count > 0:
                stmts.append(Call(make_builtin("indent_io"), []))
            prev_lit_name = elem.name
        else:
            # For non-optional, non-star elements, emit spacing unconditionally
            if not is_optional_or_star:
                stmts.extend(leading_ws)
            prev_lit_name = None

            # Extract field from tuple or use directly
            tuple_type = _get_tuple_type(fields_var.type)
            if tuple_type is not None:
                elem_type = tuple_type.elements[field_idx]
                elem_var = Var(gensym("field"), elem_type)
                elem_expr = GetElement(fields_var, field_idx)
                pretty_elem = _pretty_print_element(
                    elem,
                    elem_var,
                    grammar,
                    proto_messages,
                    leading_ws=leading_ws if is_optional_or_star else [],
                )
                stmts.append(Let(elem_var, elem_expr, pretty_elem))
            else:
                stmts.append(
                    _pretty_print_element(
                        elem,
                        fields_var,
                        grammar,
                        proto_messages,
                        leading_ws=leading_ws if is_optional_or_star else [],
                    )
                )
            field_idx += 1

    if not stmts:
        return Lit(None)
    elif len(stmts) == 1:
        return stmts[0]
    else:
        return Seq(stmts)


def _pretty_print_element(
    elem: Rhs,
    var: Var,
    grammar: Grammar,
    proto_messages: dict | None,
    leading_ws: list[TargetExpr] | None = None,
) -> TargetExpr:
    """Pretty print a single RHS element given its value.

    Args:
        leading_ws: Whitespace expressions to emit before the element,
            but only if the element produces output (used for Option/Star).
    """
    if isinstance(elem, NamedTerminal):
        formatted = _format_terminal(elem, var)
        return Call(make_builtin("write_io"), [formatted])
    elif isinstance(elem, Nonterminal):
        return Call(PrintNonterminal(elem), [var])
    elif isinstance(elem, Option):
        return _generate_pretty_option_from_field(
            elem, var, grammar, proto_messages, leading_ws=leading_ws or []
        )
    elif isinstance(elem, Star):
        return _generate_pretty_star_from_field(
            elem, var, grammar, proto_messages, leading_ws=leading_ws or []
        )
    else:
        return Call(make_builtin("write_io"), [Lit(f"<{type(elem).__name__}>")])


def _generate_pretty_option_from_field(
    rhs: Option,
    field_var: Var,
    grammar: Grammar,
    proto_messages: dict | None,
    leading_ws: list[TargetExpr] | None = None,
) -> TargetExpr:
    """Generate pretty printing for an optional field."""
    has_value = Call(make_builtin("is_some"), [field_var])

    inner_type = field_var.type
    if isinstance(inner_type, OptionType):
        inner_type = inner_type.element_type

    value_var = Var(gensym("opt_val"), inner_type)
    value_expr = Call(make_builtin("unwrap_option"), [field_var])

    if isinstance(rhs.rhs, NamedTerminal):
        formatted = _format_terminal(rhs.rhs, value_var)
        pretty_inner = Call(make_builtin("write_io"), [formatted])
    elif isinstance(rhs.rhs, Nonterminal):
        pretty_inner = Call(PrintNonterminal(rhs.rhs), [value_var])
    elif isinstance(rhs.rhs, Sequence):
        pretty_inner = _generate_pretty_from_fields(
            rhs.rhs, value_var, grammar, proto_messages
        )
    else:
        pretty_inner = Call(
            make_builtin("write_io"), [Call(make_builtin("to_string"), [value_var])]
        )

    then_body: TargetExpr = Let(value_var, value_expr, pretty_inner)
    # Include leading whitespace inside the conditional
    if leading_ws:
        then_body = Seq(list(leading_ws) + [then_body])

    return IfElse(has_value, then_body, Lit(None))


def _generate_pretty_star_from_field(
    rhs: Star,
    field_var: Var,
    grammar: Grammar,
    proto_messages: dict | None,
    leading_ws: list[TargetExpr] | None = None,
) -> TargetExpr:
    """Generate pretty printing for a repeated field."""
    list_type = field_var.type
    if isinstance(list_type, (SequenceType, ListType)):
        elem_type = list_type.element_type
    else:
        elem_type = BaseType("Any")

    elem_var = Var(gensym("elem"), elem_type)
    index_var = Var(gensym("i"), BaseType("Int64"))

    if isinstance(rhs.rhs, NamedTerminal):
        formatted = _format_terminal(rhs.rhs, elem_var)
        pretty_elem = Call(make_builtin("write_io"), [formatted])
    elif isinstance(rhs.rhs, Nonterminal):
        pretty_elem = Call(PrintNonterminal(rhs.rhs), [elem_var])
    elif isinstance(rhs.rhs, Sequence):
        pretty_elem = _generate_pretty_from_fields(
            rhs.rhs, elem_var, grammar, proto_messages
        )
    else:
        pretty_elem = Call(
            make_builtin("write_io"), [Call(make_builtin("to_string"), [elem_var])]
        )

    # Add newline between elements (except before first)
    pretty_with_spacing = IfElse(
        Call(make_builtin("greater"), [index_var, Lit(0)]),
        Seq([Call(make_builtin("newline_io"), []), pretty_elem]),
        pretty_elem,
    )

    pretty_with_spacing = _optimize_if_else_with_common_tail(pretty_with_spacing)

    loop_body: TargetExpr = ForeachEnumerated(
        index_var, elem_var, field_var, pretty_with_spacing
    )

    # Include leading whitespace inside an is_empty guard
    if leading_ws:
        loop_body = IfElse(
            Call(make_builtin("not"), [Call(make_builtin("is_empty"), [field_var])]),
            Seq(list(leading_ws) + [loop_body]),
            Lit(None),
        )

    return loop_body


def _format_literal(lit: LitTerminal) -> TargetExpr:
    """Format a literal terminal for output."""
    return Call(make_builtin("write_io"), [Lit(lit.name)])


def _format_terminal(terminal: NamedTerminal, value_var: Var) -> TargetExpr:
    """Format a terminal value for pretty printing."""
    if terminal.name in ["SYMBOL", "IDENTIFIER"]:
        return Call(make_builtin("format_symbol"), [value_var])
    elif terminal.name == "STRING":
        return Call(make_builtin("format_string"), [value_var])
    elif terminal.name in ["INT", "NUMBER"]:
        return Call(make_builtin("format_int64"), [value_var])
    elif terminal.name == "INT128":
        return Call(make_builtin("format_int128"), [value_var])
    elif terminal.name == "FLOAT":
        return Call(make_builtin("format_float64"), [value_var])
    elif terminal.name == "DECIMAL":
        return Call(make_builtin("format_decimal"), [value_var])
    elif terminal.name == "BOOL":
        return Call(make_builtin("format_bool"), [value_var])
    elif terminal.name == "UINT128":
        return Call(make_builtin("format_uint128"), [value_var])
    else:
        return Call(make_builtin("to_string"), [value_var])


# --- Utility functions ---


def _is_all_literals(rules: list[Rule]) -> bool:
    """Check if all rules produce only literal output (no fields to format)."""
    for rule in rules:
        for elem in rhs_elements(rule.rhs):
            if not isinstance(elem, LitTerminal):
                return False
    return True


def _is_identity_deconstruct(deconstructor: Lambda) -> bool:
    """Check if a deconstructor is an identity function (lambda x: x)."""
    if len(deconstructor.params) != 1:
        return False
    return deconstructor.body == deconstructor.params[0]


def _is_some_identity_deconstruct(deconstructor: Lambda) -> bool:
    """Check if a deconstructor is lambda x: some(x)."""
    if len(deconstructor.params) != 1:
        return False
    body = deconstructor.body
    return (
        isinstance(body, Call)
        and isinstance(body.func, Builtin)
        and body.func.name == "some"
        and len(body.args) == 1
        and body.args[0] == deconstructor.params[0]
    )


def _is_trivial_deconstruct(deconstructor: Lambda) -> bool:
    """Check if a deconstructor is trivial (identity or some(identity))."""
    return _is_identity_deconstruct(deconstructor) or _is_some_identity_deconstruct(
        deconstructor
    )


def _extract_trivial_deconstruct_result(
    deconstructor: Lambda, msg_param: Var
) -> TargetExpr:
    """Extract the result expression from a trivial deconstructor.

    For identity (lambda x: x), returns msg_param directly.
    For some-identity (lambda x: some(x)), also returns msg_param since
    the caller handles unwrapping the OptionType.
    """
    return msg_param


def _optimize_if_else_with_common_tail(expr: IfElse) -> TargetExpr:
    """Optimize IfElse where both branches end with the same expression.

    Transforms: IfElse(cond, Seq([a, b, c]), Seq([x, c]))
    Into: Seq([IfElse(cond, Seq([a, b]), x), c])
    """
    then_branch = expr.then_branch
    else_branch = expr.else_branch

    if not isinstance(then_branch, Seq):
        return expr

    if not isinstance(else_branch, Seq):
        if len(then_branch.exprs) > 1 and then_branch.exprs[-1] == else_branch:
            new_then = (
                Seq(then_branch.exprs[:-1])
                if len(then_branch.exprs) > 2
                else then_branch.exprs[0]
            )
            return Seq([IfElse(expr.condition, new_then, Lit(None)), else_branch])
        return expr

    then_exprs = list(then_branch.exprs)
    else_exprs = list(else_branch.exprs)

    common_len = 0
    min_len = min(len(then_exprs), len(else_exprs))
    for i in range(1, min_len + 1):
        if then_exprs[-i] == else_exprs[-i]:
            common_len = i
        else:
            break

    if common_len == 0:
        return expr

    then_prefix = then_exprs[:-common_len]
    else_prefix = else_exprs[:-common_len]
    common_suffix = then_exprs[-common_len:]

    if len(then_prefix) == 0 and len(else_prefix) == 0:
        return Seq(common_suffix) if len(common_suffix) > 1 else common_suffix[0]

    new_then = (
        Seq(then_prefix)
        if len(then_prefix) > 1
        else (then_prefix[0] if then_prefix else Lit(None))
    )
    new_else = (
        Seq(else_prefix)
        if len(else_prefix) > 1
        else (else_prefix[0] if else_prefix else Lit(None))
    )

    result_parts = [IfElse(expr.condition, new_then, new_else)] + common_suffix
    return Seq(result_parts) if len(result_parts) > 1 else result_parts[0]
