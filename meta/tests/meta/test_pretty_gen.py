#!/usr/bin/env python3
"""Tests for pretty_gen: generating pretty-printer IR from grammar rules."""

from textwrap import dedent

from meta.grammar import Grammar
from meta.pretty_gen import generate_pretty_functions
from meta.target import (
    Builtin,
    Call,
    GetElement,
    IfElse,
    Let,
    PrintNonterminalDef,
    Return,
    Seq,
)
from meta.yacc_parser import load_yacc_grammar


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


def _is_try_flat_let(expr):
    """Check if a Let is the try_flat wrapper (init calls try_flat_io)."""
    return (
        isinstance(expr, Let)
        and isinstance(expr.init, Call)
        and isinstance(expr.init.func, Builtin)
        and expr.init.func.name == "try_flat_io"
        and isinstance(expr.body, IfElse)
    )


def _is_try_flat_if(if_else):
    """Check if an IfElse is a try_flat wrapper (then-branch contains Return)."""
    then = if_else.then_branch
    if isinstance(then, Return):
        return True
    if isinstance(then, Seq):
        return any(isinstance(e, Return) for e in then.exprs)
    return False


def _find_if_else(expr):
    """Find the first guarded IfElse node, skipping try_flat wrappers."""
    if isinstance(expr, IfElse):
        if not _is_try_flat_if(expr):
            return expr
        result = _find_if_else(expr.else_branch)
        if result is not None:
            return result
        return _find_if_else(expr.then_branch)
    if isinstance(expr, Let):
        if _is_try_flat_let(expr):
            assert isinstance(expr.body, IfElse)
            return _find_if_else(expr.body.else_branch)
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


def _build_grammar(text):
    """Parse a grammar string and build a Grammar object."""
    config = load_yacc_grammar(dedent(text).lstrip())
    start = None
    for nt in config.rules:
        if nt.name == config.start_symbol:
            start = nt
            break
    assert start is not None
    grammar = Grammar(start=start, function_defs=config.function_defs)
    for rules in config.rules.values():
        for rule in rules:
            grammar.add_rule(rule)
    return grammar


def _get_pretty_def(grammar, name):
    """Generate pretty functions and return the one for the given nonterminal."""
    defs = generate_pretty_functions(grammar)
    matches = [d for d in defs if d.nonterminal.name == name]
    assert len(matches) == 1, f"Expected 1 def for {name}, got {len(matches)}"
    return matches[0]


class TestPrettyGenOptionTupleUnwrap:
    """Test that guarded alternatives with OptionType(TupleType(...)) properly
    extract tuple fields via GetElement."""

    GRAMMAR_TWO_FIELDS = """\
        %token STRING String r'"[^"]*"'
        %token SYMBOL String r'[a-z]+'
        %nonterm config test.Config
        %nonterm path String
        %nonterm source String
        %start config
        %%
        config
            : "(" "config_v2" path source ")"
              construct: $$ = test.Config(path=$3, source=$4)
              deconstruct if True:
                $3: String = $$.path
                $4: String = $$.source
            | "(" "config" path ")"
              construct: $$ = test.Config(path=$3)
              deconstruct:
                $3: String = $$.path

        path
            : STRING

        source
            : SYMBOL
        %%
    """

    def test_guarded_alternative_extracts_tuple_fields(self):
        """When a guarded deconstructor returns Option[Tuple[...]],
        the then-branch should extract individual fields via GetElement."""
        grammar = _build_grammar(self.GRAMMAR_TWO_FIELDS)
        defn = _get_pretty_def(grammar, "config")
        assert isinstance(defn, PrintNonterminalDef)

        if_else = _find_if_else(defn.body)
        assert if_else is not None, "Expected IfElse for guarded alternative"

        get_elems = _collect_nodes(if_else.then_branch, GetElement)
        assert len(get_elems) == 2, (
            f"Expected 2 GetElement nodes for 2 tuple fields, got {len(get_elems)}"
        )
        indices = sorted(ge.index for ge in get_elems)
        assert indices == [0, 1]

    def test_guarded_fallback_has_no_get_element(self):
        """The fallback (None/else) branch with a single field should not
        use GetElement."""
        grammar = _build_grammar(self.GRAMMAR_TWO_FIELDS)
        defn = _get_pretty_def(grammar, "config")

        if_else = _find_if_else(defn.body)
        assert if_else is not None

        get_elems = _collect_nodes(if_else.else_branch, GetElement)
        assert len(get_elems) == 0, (
            f"Expected no GetElement in fallback branch, got {len(get_elems)}"
        )

    def test_guarded_three_fields(self):
        """Guarded alternative with 3 tuple fields extracts all via GetElement."""
        grammar = _build_grammar("""\
            %token STRING String r'"[^"]*"'
            %token SYMBOL String r'[a-z]+'
            %nonterm export test.Export
            %nonterm path String
            %nonterm source String
            %nonterm cfg String
            %start export
            %%
            export
                : "(" "export_v2" path source cfg ")"
                  construct: $$ = test.Export(path=$3, source=$4, cfg=$5)
                  deconstruct if True:
                    $3: String = $$.path
                    $4: String = $$.source
                    $5: String = $$.cfg
                | "(" "export" path ")"

            path
                : STRING

            source
                : SYMBOL

            cfg
                : SYMBOL
            %%
        """)
        defn = _get_pretty_def(grammar, "export")

        if_else = _find_if_else(defn.body)
        assert if_else is not None

        get_elems = _collect_nodes(if_else.then_branch, GetElement)
        assert len(get_elems) == 3, f"Expected 3 GetElement nodes, got {len(get_elems)}"
        indices = sorted(ge.index for ge in get_elems)
        assert indices == [0, 1, 2]


class TestPrettyGenPlainTuple:
    """Test that non-guarded rules with plain TupleType still extract fields."""

    def test_single_rule_tuple_extracts_fields(self):
        """A single rule with multiple non-literal elements should extract
        fields via GetElement."""
        grammar = _build_grammar("""\
            %token STRING String r'"[^"]*"'
            %token INT Int64 r'[0-9]+'
            %nonterm pair test.Pair
            %start pair
            %%
            pair
                : "(" "pair" STRING INT ")"
                  construct: $$ = test.Pair(first=$3, second=$4)
                  deconstruct:
                    $3: String = $$.first
                    $4: Int64 = $$.second
            %%
        """)
        defn = _get_pretty_def(grammar, "pair")

        get_elems = _collect_nodes(defn.body, GetElement)
        assert len(get_elems) == 2, f"Expected 2 GetElement nodes, got {len(get_elems)}"
        indices = sorted(ge.index for ge in get_elems)
        assert indices == [0, 1]
