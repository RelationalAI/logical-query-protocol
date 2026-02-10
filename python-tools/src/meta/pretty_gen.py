"""Pretty printer generator.

Generates pretty-printer visitor methods from grammar rules. Each nonterminal
gets a pretty_X method that deconstructs a protobuf message according to the
rule's deconstruct action, then prints the RHS elements.

For nonterminals with multiple rules, rules are tried in specificity order
(most specific first), using the deconstructor to determine which rule matches.
"""

from typing import Dict, List, Optional, Union
from .grammar import Grammar, GrammarConfig, Rule, Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .grammar_utils import is_epsilon, rhs_elements
from .target import (
    Lambda, Call, VisitNonterminalDef, Var, Lit, Builtin, Let, IfElse,
    BaseType, ListType, TupleType, TargetExpr, Seq, VisitNonterminal, gensym,
    OptionType, ForeachEnumerated, GetElement
)
from .target_builtins import make_builtin

# Type alias for grammar parameter (both Grammar and GrammarConfig have .rules)
GrammarLike = Union[Grammar, GrammarConfig]


def _get_rules_dict(grammar: GrammarLike) -> Dict[Nonterminal, List[Rule]]:
    """Get the rules dictionary from either Grammar or GrammarConfig."""
    return grammar.rules


def generate_pretty_functions(grammar: GrammarLike,
                              proto_messages: Optional[Dict] = None) -> List[VisitNonterminalDef]:
    """Generate pretty printer functions for all nonterminals."""
    pretty_methods = []

    if isinstance(grammar, GrammarConfig):
        nonterminals = sorted(grammar.rules.keys(), key=lambda nt: nt.name)
    else:
        rule_order, _ = grammar.analysis.partition_nonterminals_by_reachability()
        reachable = grammar.analysis.reachability
        nonterminals = [nt for nt in rule_order if reachable is None or nt in reachable]

    rules_dict = _get_rules_dict(grammar)
    for nt in nonterminals:
        rules = rules_dict[nt]
        method_code = _generate_pretty_method(nt, rules, grammar, proto_messages)
        pretty_methods.append(method_code)
    return pretty_methods


def _generate_pretty_method(lhs: Nonterminal, rules: List[Rule],
                            grammar: GrammarLike,
                            proto_messages: Optional[Dict]) -> VisitNonterminalDef:
    """Generate a pretty-print visitor method for a nonterminal."""
    nt = rules[0].lhs
    msg_param = Var("msg", nt.type)

    if len(rules) == 1:
        body = _generate_pretty_with_deconstruct(rules[0], msg_param, grammar, proto_messages)
    else:
        body = _generate_pretty_alternatives(rules, msg_param, grammar, proto_messages)

    return VisitNonterminalDef(
        visitor_name='pretty',
        nonterminal=nt,
        params=[msg_param],
        return_type=OptionType(BaseType("Never")),
        body=body
    )


def _generate_pretty_alternatives(rules: List[Rule], msg_param: Var,
                                  grammar: GrammarLike,
                                  proto_messages: Optional[Dict]) -> TargetExpr:
    """Generate if-else chain trying rules in declaration order.

    Rules are tried in the order they appear in the grammar. For each rule,
    the deconstructor is called; if it returns non-None, that rule is used.
    The last rule with a trivial (always-matching) deconstructor serves as
    the fallback.
    """
    # Find the last rule with a trivial deconstructor to use as fallback.
    # All other rules are tried in declaration order before it.
    fallback_idx: Optional[int] = None
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
            rules[fallback_idx], msg_param, grammar, proto_messages)
    else:
        result = Call(make_builtin('error'), [Lit(f"No matching rule for {rules[0].lhs.name}")])

    # Build if-else chain in reverse declaration order (so first-declared ends up outermost)
    guarded_indices = [i for i in range(len(rules)) if i != fallback_idx]
    for i in reversed(guarded_indices):
        rule = rules[i]
        if _is_nonterminal_ref(rule) and _has_guarded_deconstruct(rule.rhs, grammar):
            result = _generate_nonterminal_ref_dispatch(rule, msg_param, grammar, proto_messages, result)
        elif rule.deconstructor is not None and isinstance(rule.deconstructor.return_type, OptionType):
            deconstruct_result_var = Var(gensym('deconstruct_result'), rule.deconstructor.return_type)
            deconstruct_call = Call(rule.deconstructor, [msg_param])
            pretty_body = _generate_pretty_from_fields(
                rule.rhs, deconstruct_result_var, grammar, proto_messages)
            result = Let(
                deconstruct_result_var,
                deconstruct_call,
                IfElse(
                    Call(make_builtin('is_some'), [deconstruct_result_var]),
                    pretty_body,
                    result
                )
            )
        else:
            # Unguarded non-fallback rule — treat as always matching at this position
            result = _generate_pretty_with_deconstruct(rule, msg_param, grammar, proto_messages)

    return result


def _is_guarded_rule(rule: Rule, grammar: GrammarLike) -> bool:
    """Check if a rule has a guard (Optional deconstructor or guarded nonterminal ref)."""
    if _is_nonterminal_ref(rule) and _has_guarded_deconstruct(rule.rhs, grammar):
        return True
    if rule.deconstructor is not None and isinstance(rule.deconstructor.return_type, OptionType):
        return True
    return False


def _is_nonterminal_ref(rule: Rule) -> bool:
    """Check if a rule's RHS is a single nonterminal reference."""
    return isinstance(rule.rhs, Nonterminal)


def _has_guarded_deconstruct(nt_ref: Rhs, grammar: GrammarLike) -> bool:
    """Check if a referenced nonterminal has a guarded (Optional) deconstructor."""
    if not isinstance(nt_ref, Nonterminal):
        return False
    rules_dict = _get_rules_dict(grammar)
    for nt, rules in rules_dict.items():
        if nt.name == nt_ref.name:
            return any(
                r.deconstructor is not None
                and isinstance(r.deconstructor.return_type, OptionType)
                for r in rules
            )
    return False


def _generate_nonterminal_ref_dispatch(rule: Rule, msg_param: Var,
                                       grammar: GrammarLike,
                                       proto_messages: Optional[Dict],
                                       fallback: TargetExpr) -> TargetExpr:
    """Generate dispatch for a nonterminal-reference alternative.

    Uses the referenced nonterminal's deconstructor as the guard condition,
    then calls the referenced nonterminal's pretty printer if matched.
    """
    nt_ref = rule.rhs
    assert isinstance(nt_ref, Nonterminal)

    rules_dict = _get_rules_dict(grammar)
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
        if r.deconstructor is not None and isinstance(r.deconstructor.return_type, OptionType):
            guard_deconstructor = r.deconstructor
            break

    if guard_deconstructor is None:
        return Call(VisitNonterminal('pretty', nt_ref), [msg_param])

    deconstruct_result_var = Var(gensym('guard_result'), guard_deconstructor.return_type)
    deconstruct_call = Call(guard_deconstructor, [msg_param])
    pretty_call = Call(VisitNonterminal('pretty', nt_ref), [msg_param])

    return Let(
        deconstruct_result_var,
        deconstruct_call,
        IfElse(
            Call(make_builtin('is_some'), [deconstruct_result_var]),
            pretty_call,
            fallback
        )
    )


def _generate_pretty_with_deconstruct(rule: Rule, msg_param: Var,
                                      grammar: GrammarLike,
                                      proto_messages: Optional[Dict]) -> TargetExpr:
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

        fields_var = Var(gensym('fields'), unwrapped_type)
        pretty_body = _generate_pretty_from_fields(rule.rhs, fields_var, grammar, proto_messages)
        return Let(fields_var, fields_expr, pretty_body)

    # Non-trivial deconstruct — call the lambda
    deconstructor = rule.deconstructor
    deconstruct_result_var = Var(gensym('fields'), deconstructor.return_type)
    deconstruct_call = Call(deconstructor, [msg_param])

    if isinstance(deconstructor.return_type, OptionType):
        unwrapped_type = deconstructor.return_type.element_type
    else:
        unwrapped_type = deconstructor.return_type

    unwrapped_var = Var(gensym('unwrapped_fields'), unwrapped_type)
    unwrap_expr = Call(make_builtin('unwrap_option'), [deconstruct_result_var])

    pretty_body = _generate_pretty_from_fields(rule.rhs, unwrapped_var, grammar, proto_messages)

    return Let(deconstruct_result_var, deconstruct_call,
               Let(unwrapped_var, unwrap_expr, pretty_body))


def _generate_pretty_from_fields(rhs: Rhs, fields_var: Var,
                                 grammar: GrammarLike,
                                 proto_messages: Optional[Dict]) -> TargetExpr:
    """Generate pretty printing code given extracted field values."""
    if isinstance(rhs, Sequence):
        return _generate_pretty_sequence_from_fields(rhs, fields_var, grammar, proto_messages)
    elif isinstance(rhs, LitTerminal):
        return _format_literal(rhs)
    elif isinstance(rhs, NamedTerminal):
        formatted = _format_terminal(rhs, fields_var)
        return Call(make_builtin('write_io'), [formatted])
    elif isinstance(rhs, Nonterminal):
        return Call(VisitNonterminal('pretty', rhs), [fields_var])
    elif isinstance(rhs, Option):
        return _generate_pretty_option_from_field(rhs, fields_var, grammar, proto_messages)
    elif isinstance(rhs, Star):
        return _generate_pretty_star_from_field(rhs, fields_var, grammar, proto_messages)
    else:
        assert False, f'Unsupported Rhs type: {type(rhs)}'


def _generate_pretty_sequence_from_fields(rhs: Sequence, fields_var: Var,
                                          grammar: GrammarLike,
                                          proto_messages: Optional[Dict]) -> TargetExpr:
    """Generate pretty printing for a sequence using extracted field values."""
    if is_epsilon(rhs):
        return Lit(None)

    elems = list(rhs_elements(rhs))
    stmts: List[TargetExpr] = []
    field_idx = 0

    # Detect S-expression pattern: first element is "(", second is a keyword literal
    is_sexp = (len(elems) >= 2
               and isinstance(elems[0], LitTerminal) and elems[0].name == '('
               and isinstance(elems[1], LitTerminal) and elems[1].name != '(')

    # Count non-literal elements to determine if fields_var is a tuple or single value
    non_lit_count = sum(1 for e in elems if not isinstance(e, LitTerminal))

    for i, elem in enumerate(elems):
        if isinstance(elem, LitTerminal):
            is_keyword = is_sexp and i == 1
            stmts.append(_format_literal(elem, is_sexp_keyword=is_keyword))
        else:
            # Insert newline between consecutive non-literal elements
            if stmts and field_idx > 0 and is_sexp:
                stmts.append(Call(make_builtin('newline_io'), []))

            # Extract field from tuple or use directly
            if non_lit_count > 1 and isinstance(fields_var.type, TupleType):
                elem_type = fields_var.type.elements[field_idx]
                elem_var = Var(gensym('field'), elem_type)
                elem_expr = GetElement(fields_var, field_idx)
                pretty_elem = _pretty_print_element(elem, elem_var, grammar, proto_messages)
                stmts.append(Let(elem_var, elem_expr, pretty_elem))
            else:
                stmts.append(_pretty_print_element(elem, fields_var, grammar, proto_messages))
            field_idx += 1

    if not stmts:
        return Lit(None)
    elif len(stmts) == 1:
        return stmts[0]
    else:
        return Seq(stmts)


def _pretty_print_element(elem: Rhs, var: Var, grammar: GrammarLike,
                           proto_messages: Optional[Dict]) -> TargetExpr:
    """Pretty print a single RHS element given its value."""
    if isinstance(elem, NamedTerminal):
        formatted = _format_terminal(elem, var)
        return Call(make_builtin('write_io'), [formatted])
    elif isinstance(elem, Nonterminal):
        return Call(VisitNonterminal('pretty', elem), [var])
    elif isinstance(elem, Option):
        return _generate_pretty_option_from_field(elem, var, grammar, proto_messages)
    elif isinstance(elem, Star):
        return _generate_pretty_star_from_field(elem, var, grammar, proto_messages)
    else:
        return Call(make_builtin('write_io'), [Lit(f'<{type(elem).__name__}>')])


def _generate_pretty_option_from_field(rhs: Option, field_var: Var,
                                       grammar: GrammarLike,
                                       proto_messages: Optional[Dict]) -> TargetExpr:
    """Generate pretty printing for an optional field."""
    has_value = Call(make_builtin('is_some'), [field_var])

    inner_type = field_var.type
    if isinstance(inner_type, OptionType):
        inner_type = inner_type.element_type

    value_var = Var(gensym('opt_val'), inner_type)
    value_expr = Call(make_builtin('unwrap_option'), [field_var])

    if isinstance(rhs.rhs, NamedTerminal):
        formatted = _format_terminal(rhs.rhs, value_var)
        pretty_inner = Call(make_builtin('write_io'), [formatted])
    elif isinstance(rhs.rhs, Nonterminal):
        pretty_inner = Call(VisitNonterminal('pretty', rhs.rhs), [value_var])
    elif isinstance(rhs.rhs, Sequence):
        pretty_inner = _generate_pretty_from_fields(rhs.rhs, value_var, grammar, proto_messages)
    else:
        pretty_inner = Call(make_builtin('write_io'), [Call(make_builtin('to_string'), [value_var])])

    return IfElse(
        has_value,
        Let(value_var, value_expr, pretty_inner),
        Lit(None)
    )


def _generate_pretty_star_from_field(rhs: Star, field_var: Var,
                                     grammar: GrammarLike,
                                     proto_messages: Optional[Dict]) -> TargetExpr:
    """Generate pretty printing for a repeated field."""
    list_type = field_var.type
    if isinstance(list_type, ListType):
        elem_type = list_type.element_type
    else:
        elem_type = BaseType('Any')

    elem_var = Var(gensym('elem'), elem_type)
    index_var = Var(gensym('i'), BaseType('Int64'))

    if isinstance(rhs.rhs, NamedTerminal):
        formatted = _format_terminal(rhs.rhs, elem_var)
        pretty_elem = Call(make_builtin('write_io'), [formatted])
    elif isinstance(rhs.rhs, Nonterminal):
        pretty_elem = Call(VisitNonterminal('pretty', rhs.rhs), [elem_var])
    elif isinstance(rhs.rhs, Sequence):
        pretty_elem = _generate_pretty_from_fields(rhs.rhs, elem_var, grammar, proto_messages)
    else:
        pretty_elem = Call(make_builtin('write_io'), [Call(make_builtin('to_string'), [elem_var])])

    # Add newline between elements (except before first)
    pretty_with_spacing = IfElse(
        Call(make_builtin('greater'), [index_var, Lit(0)]),
        Seq([Call(make_builtin('newline_io'), []), pretty_elem]),
        pretty_elem
    )

    pretty_with_spacing = _optimize_if_else_with_common_tail(pretty_with_spacing)

    return ForeachEnumerated(index_var, elem_var, field_var, pretty_with_spacing)


def _format_literal(lit: LitTerminal, is_sexp_keyword: bool = False) -> TargetExpr:
    """Format a literal terminal for output.

    is_sexp_keyword: True if this literal is the keyword in an S-expression
    (i.e., appears at position 1 in a "(keyword ...)" sequence).
    """
    if lit.name == '(':
        return Call(make_builtin('write_io'), [Lit('(')])
    elif lit.name == ')':
        return Seq([
            Call(make_builtin('dedent_io'), []),
            Call(make_builtin('write_io'), [Lit(')')]),
            Call(make_builtin('newline_io'), []),
        ])
    elif is_sexp_keyword:
        return Seq([
            Call(make_builtin('write_io'), [Lit(lit.name)]),
            Call(make_builtin('newline_io'), []),
            Call(make_builtin('indent_io'), []),
        ])
    else:
        return Call(make_builtin('write_io'), [Lit(lit.name)])


def _format_terminal(terminal: NamedTerminal, value_var: Var) -> TargetExpr:
    """Format a terminal value for pretty printing."""
    if terminal.name in ['SYMBOL', 'IDENTIFIER']:
        return Call(make_builtin('format_symbol'), [value_var])
    elif terminal.name == 'STRING':
        return Call(make_builtin('format_string'), [value_var])
    elif terminal.name in ['INT', 'NUMBER']:
        return Call(make_builtin('format_int64'), [value_var])
    elif terminal.name == 'FLOAT':
        return Call(make_builtin('format_float64'), [value_var])
    elif terminal.name == 'BOOL':
        return Call(make_builtin('format_bool'), [value_var])
    elif terminal.name == 'HEX_UINT128':
        return Call(make_builtin('format_uint128'), [value_var])
    else:
        return Call(make_builtin('to_string'), [value_var])


# --- Utility functions ---

def _is_trivial_deconstruct(deconstructor: Lambda) -> bool:
    """Check if a deconstructor is trivial (just returns msg or msg.field)."""
    body = deconstructor.body
    if isinstance(body, Var) and body.name == 'msg':
        return True
    if (isinstance(body, Call) and isinstance(body.func, Builtin) and
            body.func.name == 'some' and len(body.args) == 1 and
            isinstance(body.args[0], Var) and body.args[0].name == 'msg'):
        return True
    return False


def _extract_trivial_deconstruct_result(deconstructor: Lambda, msg_param: Var) -> TargetExpr:
    """Extract the result expression from a trivial deconstructor."""
    body = deconstructor.body
    if isinstance(body, Var) and body.name == 'msg':
        return msg_param
    if (isinstance(body, Call) and isinstance(body.func, Builtin) and
            body.func.name == 'some' and len(body.args) == 1):
        return msg_param
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
            new_then = Seq(then_branch.exprs[:-1]) if len(then_branch.exprs) > 2 else then_branch.exprs[0]
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

    new_then = Seq(then_prefix) if len(then_prefix) > 1 else (then_prefix[0] if then_prefix else Lit(None))
    new_else = Seq(else_prefix) if len(else_prefix) > 1 else (else_prefix[0] if else_prefix else Lit(None))

    result_parts = [IfElse(expr.condition, new_then, new_else)] + common_suffix
    return Seq(result_parts) if len(result_parts) > 1 else result_parts[0]
