#!/usr/bin/env python3
"""Tests for pretty_gen: generating pretty-printer IR from grammar rules."""

from meta.grammar import (
    Grammar,
    LitTerminal,
    Nonterminal,
    Rule,
    Sequence,
)
from meta.pretty_gen import generate_pretty_functions
from meta.target import (
    BaseType,
    Call,
    GetElement,
    IfElse,
    Lambda,
    Let,
    Lit,
    MessageType,
    OptionType,
    PrintNonterminalDef,
    Seq,
    TupleType,
    Var,
)


def _msg_type(name: str) -> MessageType:
    return MessageType("proto", name)


def _nonterminal(name: str, t=None) -> Nonterminal:
    return Nonterminal(name, t or BaseType("String"))


def _seq(*elems) -> Sequence:
    return Sequence(tuple(elems))


def _collect_nodes(expr, node_type):
    """Collect all nodes of a given type from an IR tree."""
    results = []
    if isinstance(expr, node_type):
        results.append(expr)
    if isinstance(expr, Let):
        results.extend(_collect_nodes(expr.init, node_type))
        results.extend(_collect_nodes(expr.body, node_type))
    elif isinstance(expr, IfElse):
        results.extend(_collect_nodes(expr.condition, node_type))
        results.extend(_collect_nodes(expr.then_branch, node_type))
        results.extend(_collect_nodes(expr.else_branch, node_type))
    elif isinstance(expr, Seq):
        for e in expr.exprs:
            results.extend(_collect_nodes(e, node_type))
    elif isinstance(expr, Call):
        for a in expr.args:
            results.extend(_collect_nodes(a, node_type))
    return results


def _make_grammar(start_nt, rules):
    """Build a Grammar and add rules."""
    grammar = Grammar(start=start_nt)
    for rule in rules:
        grammar.add_rule(rule)
    return grammar


def _find_if_else(expr):
    """Find the first IfElse node in the IR tree."""
    if isinstance(expr, IfElse):
        return expr
    if isinstance(expr, Let):
        result = _find_if_else(expr.body)
        if result is not None:
            return result
        return _find_if_else(expr.init)
    if isinstance(expr, Seq):
        for e in expr.exprs:
            result = _find_if_else(e)
            if result is not None:
                return result
    return None


def _make_guarded_deconstructor(lhs_type, tuple_type):
    """Build a non-trivial deconstructor returning OptionType(tuple_type).

    The body is a dummy IfElse — pretty_gen only cares about the return type.
    """
    dd = Var("_dollar_dollar", lhs_type)
    return Lambda(
        [dd],
        OptionType(tuple_type),
        # Non-trivial body so pretty_gen doesn't shortcut
        IfElse(Lit(True), Lit(None), Lit(None)),
    )


def _make_deconstructor(lhs_type, return_type):
    """Build a non-trivial deconstructor returning return_type."""
    dd = Var("_dollar_dollar", lhs_type)
    return Lambda(
        [dd],
        return_type,
        Lit(42),  # Non-trivial body
    )


class TestPrettyGenOptionTupleUnwrap:
    """Test that guarded alternatives with OptionType(TupleType(...)) properly
    extract tuple fields via GetElement."""

    def test_guarded_alternative_extracts_tuple_fields(self):
        """When a guarded deconstructor returns Option[Tuple[...]],
        the then-branch should extract individual fields via GetElement."""
        cfg_type = _msg_type("Config")
        nt = _nonterminal("config", cfg_type)

        guarded_rhs = _seq(
            LitTerminal("("),
            LitTerminal("config_v2"),
            _nonterminal("path", BaseType("String")),
            _nonterminal("source", BaseType("String")),
            LitTerminal(")"),
        )
        guarded_constructor = Lambda(
            [Var("p", BaseType("String")), Var("s", BaseType("String"))],
            cfg_type,
            Var("result", cfg_type),
        )
        tuple_type = TupleType([BaseType("String"), BaseType("String")])
        guarded_deconstructor = _make_guarded_deconstructor(cfg_type, tuple_type)

        fallback_rhs = _seq(
            LitTerminal("("),
            LitTerminal("config"),
            _nonterminal("path", BaseType("String")),
            LitTerminal(")"),
        )
        fallback_constructor = Lambda(
            [Var("p", BaseType("String"))],
            cfg_type,
            Var("result", cfg_type),
        )
        fallback_deconstructor = _make_deconstructor(cfg_type, BaseType("String"))

        grammar = _make_grammar(nt, [
            Rule(nt, guarded_rhs, guarded_constructor, guarded_deconstructor),
            Rule(nt, fallback_rhs, fallback_constructor, fallback_deconstructor),
        ])

        defs = generate_pretty_functions(grammar, proto_messages=None)
        assert len(defs) == 1
        assert isinstance(defs[0], PrintNonterminalDef)

        body = defs[0].body
        if_else = _find_if_else(body)
        assert if_else is not None, "Expected IfElse for guarded alternative"

        # The then-branch (Some case) should extract fields via GetElement
        get_elems = _collect_nodes(if_else.then_branch, GetElement)
        assert len(get_elems) == 2, (
            f"Expected 2 GetElement nodes for 2 tuple fields, got {len(get_elems)}"
        )
        indices = sorted(ge.index for ge in get_elems)
        assert indices == [0, 1]

    def test_guarded_fallback_has_no_get_element(self):
        """The fallback (None/else) branch with a single field should not
        use GetElement."""
        cfg_type = _msg_type("Config")
        nt = _nonterminal("config", cfg_type)

        guarded_rhs = _seq(
            LitTerminal("("),
            LitTerminal("config_v2"),
            _nonterminal("path", BaseType("String")),
            _nonterminal("source", BaseType("String")),
            LitTerminal(")"),
        )
        guarded_constructor = Lambda(
            [Var("p", BaseType("String")), Var("s", BaseType("String"))],
            cfg_type,
            Var("result", cfg_type),
        )
        tuple_type = TupleType([BaseType("String"), BaseType("String")])
        guarded_deconstructor = _make_guarded_deconstructor(cfg_type, tuple_type)

        fallback_rhs = _seq(
            LitTerminal("("),
            LitTerminal("config"),
            _nonterminal("path", BaseType("String")),
            LitTerminal(")"),
        )
        fallback_constructor = Lambda(
            [Var("p", BaseType("String"))],
            cfg_type,
            Var("result", cfg_type),
        )
        fallback_deconstructor = _make_deconstructor(cfg_type, BaseType("String"))

        grammar = _make_grammar(nt, [
            Rule(nt, guarded_rhs, guarded_constructor, guarded_deconstructor),
            Rule(nt, fallback_rhs, fallback_constructor, fallback_deconstructor),
        ])

        defs = generate_pretty_functions(grammar, proto_messages=None)
        body = defs[0].body

        if_else = _find_if_else(body)
        assert if_else is not None

        # Else-branch (fallback) has single field — no GetElement needed
        get_elems = _collect_nodes(if_else.else_branch, GetElement)
        assert len(get_elems) == 0, (
            f"Expected no GetElement in fallback branch, got {len(get_elems)}"
        )

    def test_guarded_three_fields(self):
        """Guarded alternative with 3 tuple fields extracts all via GetElement."""
        cfg_type = _msg_type("ExportConfig")
        nt = _nonterminal("export_config", cfg_type)

        guarded_rhs = _seq(
            LitTerminal("("),
            LitTerminal("export_v2"),
            _nonterminal("path", BaseType("String")),
            _nonterminal("source", BaseType("String")),
            _nonterminal("config", BaseType("String")),
            LitTerminal(")"),
        )
        guarded_constructor = Lambda(
            [
                Var("p", BaseType("String")),
                Var("s", BaseType("String")),
                Var("c", BaseType("String")),
            ],
            cfg_type,
            Var("result", cfg_type),
        )
        tuple_type = TupleType([
            BaseType("String"), BaseType("String"), BaseType("String"),
        ])
        guarded_deconstructor = _make_guarded_deconstructor(cfg_type, tuple_type)

        # Fallback: all literals
        fallback_rhs = _seq(
            LitTerminal("("),
            LitTerminal("export"),
            LitTerminal(")"),
        )
        fallback_constructor = Lambda([], cfg_type, Var("result", cfg_type))

        grammar = _make_grammar(nt, [
            Rule(nt, guarded_rhs, guarded_constructor, guarded_deconstructor),
            Rule(nt, fallback_rhs, fallback_constructor),
        ])

        defs = generate_pretty_functions(grammar, proto_messages=None)
        body = defs[0].body

        if_else = _find_if_else(body)
        assert if_else is not None

        get_elems = _collect_nodes(if_else.then_branch, GetElement)
        assert len(get_elems) == 3, (
            f"Expected 3 GetElement nodes, got {len(get_elems)}"
        )
        indices = sorted(ge.index for ge in get_elems)
        assert indices == [0, 1, 2]


class TestPrettyGenPlainTuple:
    """Test that non-guarded rules with plain TupleType still extract fields."""

    def test_single_rule_tuple_extracts_fields(self):
        """A single rule with a TupleType deconstructor should extract
        fields via GetElement."""
        cfg_type = _msg_type("Pair")
        nt = _nonterminal("pair", cfg_type)

        rhs = _seq(
            LitTerminal("("),
            LitTerminal("pair"),
            _nonterminal("first", BaseType("String")),
            _nonterminal("second", BaseType("Int64")),
            LitTerminal(")"),
        )
        constructor = Lambda(
            [Var("a", BaseType("String")), Var("b", BaseType("Int64"))],
            cfg_type,
            Var("result", cfg_type),
        )
        tuple_type = TupleType([BaseType("String"), BaseType("Int64")])
        deconstructor = _make_deconstructor(cfg_type, tuple_type)

        grammar = _make_grammar(nt, [
            Rule(nt, rhs, constructor, deconstructor),
        ])

        defs = generate_pretty_functions(grammar, proto_messages=None)
        assert len(defs) == 1
        body = defs[0].body

        get_elems = _collect_nodes(body, GetElement)
        assert len(get_elems) == 2, (
            f"Expected 2 GetElement nodes, got {len(get_elems)}"
        )
        indices = sorted(ge.index for ge in get_elems)
        assert indices == [0, 1]
