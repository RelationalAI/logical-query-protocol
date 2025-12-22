#!/usr/bin/env python3
"""Tests for grammar analysis functions."""

import sys
from pathlib import Path
from typing import cast

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    LitTerminal, NamedTerminal, Nonterminal, Terminal,
    Star, Option, Sequence,
    Rule, Grammar,
)
from meta.grammar_analysis import GrammarAnalysis
from meta.target import BaseType, MessageType, Lambda, Var, OptionType, TupleType, Lit, Call, Builtin


def make_simple_grammar():
    """Create a simple test grammar.

    S -> A B
    A -> "a"
    B -> "b"
    """
    s = Nonterminal("S", MessageType("proto", "S"))
    a = Nonterminal("A", MessageType("proto", "A"))
    b = Nonterminal("B", MessageType("proto", "B"))
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")

    grammar = Grammar(s)

    # S -> A B
    param_a = Var("x", MessageType("proto", "A"))
    param_b = Var("y", MessageType("proto", "B"))
    construct_action_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    deconstruct_action_s = Lambda(
        [Var('msg', MessageType("proto", "S"))],
        OptionType(TupleType([MessageType("proto", "A"), MessageType("proto", "B")])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
            Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('a')]),
            Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('b')])
        ])])
    )
    grammar.add_rule(Rule(s, Sequence((a, b)), construct_action_s, deconstruct_action_s))

    # A -> "a"
    construct_action_a = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    deconstruct_action_a = Lambda(
        [Var('msg', MessageType("proto", "A"))],
        OptionType(TupleType([])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
    )
    grammar.add_rule(Rule(a, lit_a, construct_action_a, deconstruct_action_a))

    # B -> "b"
    construct_action_b = Lambda([], MessageType("proto", "B"), Var("y", MessageType("proto", "B")))
    deconstruct_action_b = Lambda(
        [Var('msg', MessageType("proto", "B"))],
        OptionType(TupleType([])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
    )
    grammar.add_rule(Rule(b, lit_b, construct_action_b, deconstruct_action_b))

    return grammar, s, a, b, lit_a, lit_b


def make_nullable_grammar():
    """Create a grammar with nullable productions.

    S -> A B
    A -> "a" | epsilon
    B -> "b"
    """
    s = Nonterminal("S", MessageType("proto", "S"))
    a = Nonterminal("A", MessageType("proto", "A"))
    b = Nonterminal("B", MessageType("proto", "B"))
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")

    grammar = Grammar(s)

    # S -> A B
    param_a = Var("x", MessageType("proto", "A"))
    param_b = Var("y", MessageType("proto", "B"))
    construct_action_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    deconstruct_action_s = Lambda(
        [Var('msg', MessageType("proto", "S"))],
        OptionType(TupleType([MessageType("proto", "A"), MessageType("proto", "B")])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
            Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('a')]),
            Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('b')])
        ])])
    )
    grammar.add_rule(Rule(s, Sequence((a, b)), construct_action_s, deconstruct_action_s))

    # A -> "a"
    construct_action_a1 = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    deconstruct_action_a1 = Lambda(
        [Var('msg', MessageType("proto", "A"))],
        OptionType(TupleType([])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
    )
    grammar.add_rule(Rule(a, lit_a, construct_action_a1, deconstruct_action_a1))

    # A -> epsilon
    construct_action_a2 = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    deconstruct_action_a2 = Lambda(
        [Var('msg', MessageType("proto", "A"))],
        OptionType(TupleType([])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
    )
    grammar.add_rule(Rule(a, Sequence(()), construct_action_a2, deconstruct_action_a2))

    # B -> "b"
    construct_action_b = Lambda([], MessageType("proto", "B"), Var("y", MessageType("proto", "B")))
    deconstruct_action_b = Lambda(
        [Var('msg', MessageType("proto", "B"))],
        OptionType(TupleType([])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
    )
    grammar.add_rule(Rule(b, lit_b, construct_action_b, deconstruct_action_b))

    return grammar, s, a, b


def make_left_recursive_grammar():
    """Create a left-recursive grammar.

    S -> S "+" T | T
    T -> "num"
    """
    s = Nonterminal("S", MessageType("proto", "S"))
    t = Nonterminal("T", MessageType("proto", "T"))
    plus = LitTerminal("+")
    num = NamedTerminal("NUM", BaseType("Int64"))

    grammar = Grammar(s)

    # S -> S "+" T
    param_s = Var("x", MessageType("proto", "S"))
    param_t1 = Var("y", MessageType("proto", "T"))
    construct_action_s1 = Lambda([param_s, param_t1], MessageType("proto", "S"), param_s)
    deconstruct_action_s1 = Lambda(
        [Var('msg', MessageType("proto", "S"))],
        OptionType(TupleType([MessageType("proto", "S"), MessageType("proto", "T")])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
            Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('s')]),
            Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('t')])
        ])])
    )
    grammar.add_rule(Rule(s, Sequence((s, plus, t)), construct_action_s1, deconstruct_action_s1))

    # S -> T
    param_t2 = Var("z", MessageType("proto", "T"))
    construct_action_s2 = Lambda([param_t2], MessageType("proto", "S"), param_t2)
    deconstruct_action_s2 = Lambda(
        [Var('msg', MessageType("proto", "S"))],
        OptionType(MessageType("proto", "T")),
        Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('t')])])
    )
    grammar.add_rule(Rule(s, t, construct_action_s2, deconstruct_action_s2))

    # T -> NUM
    param_num = Var("n", BaseType("Int64"))
    construct_action_t = Lambda([param_num], MessageType("proto", "T"), param_num)
    deconstruct_action_t = Lambda(
        [Var('msg', MessageType("proto", "T"))],
        OptionType(BaseType("Int64")),
        Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "T")), Lit('n')])])
    )
    grammar.add_rule(Rule(t, num, construct_action_t, deconstruct_action_t))

    return grammar, s, t, num


def make_unreachable_grammar():
    """Create a grammar with unreachable nonterminals.

    S -> A
    A -> "a"
    B -> "b"  (unreachable)
    """
    s = Nonterminal("S", MessageType("proto", "S"))
    a = Nonterminal("A", MessageType("proto", "A"))
    b = Nonterminal("B", MessageType("proto", "B"))
    lit_a = LitTerminal("a")
    lit_b = LitTerminal("b")

    grammar = Grammar(s)

    # S -> A
    param_a = Var("x", MessageType("proto", "A"))
    construct_action_s = Lambda([param_a], MessageType("proto", "S"), param_a)
    deconstruct_action_s = Lambda(
        [Var('msg', MessageType("proto", "S"))],
        OptionType(MessageType("proto", "A")),
        Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('a')])])
    )
    grammar.add_rule(Rule(s, a, construct_action_s, deconstruct_action_s))

    # A -> "a"
    construct_action_a = Lambda([], MessageType("proto", "A"), Var("y", MessageType("proto", "A")))
    deconstruct_action_a = Lambda(
        [Var('msg', MessageType("proto", "A"))],
        OptionType(TupleType([])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
    )
    grammar.add_rule(Rule(a, lit_a, construct_action_a, deconstruct_action_a))

    # B -> "b" (unreachable)
    construct_action_b = Lambda([], MessageType("proto", "B"), Var("z", MessageType("proto", "B")))
    deconstruct_action_b = Lambda(
        [Var('msg', MessageType("proto", "B"))],
        OptionType(TupleType([])),
        Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
    )
    grammar.add_rule(Rule(b, lit_b, construct_action_b, deconstruct_action_b))

    return grammar, s, a, b


class TestComputeReachability:
    """Tests for compute_reachability."""

    def test_simple_grammar_all_reachable(self):
        """Test reachability in simple grammar where all nonterminals are reachable."""
        grammar, s, a, b, _, _ = make_simple_grammar()
        reachable = GrammarAnalysis.compute_reachability_static(grammar)
        assert s in reachable
        assert a in reachable
        assert b in reachable
        assert len(reachable) == 3

    def test_unreachable_nonterminal(self):
        """Test reachability with unreachable nonterminal."""
        grammar, s, a, b = make_unreachable_grammar()
        reachable = GrammarAnalysis.compute_reachability_static(grammar)
        assert s in reachable
        assert a in reachable
        assert b not in reachable
        assert len(reachable) == 2

    def test_empty_grammar(self):
        """Test reachability with grammar that has no rules for start."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        reachable = GrammarAnalysis.compute_reachability_static(grammar)
        # Start is always added to rules dict by Grammar constructor
        assert len(reachable) == 1
        assert s in reachable

    def test_single_rule(self):
        """Test reachability with single rule."""
        s = Nonterminal("S", MessageType("proto", "S"))
        lit = LitTerminal("a")
        grammar = Grammar(s)
        construct_action = Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))
        deconstruct_action = Lambda(
            [Var('msg', MessageType("proto", "S"))],
            OptionType(TupleType([])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
        )
        grammar.add_rule(Rule(s, lit, construct_action, deconstruct_action))
        reachable = GrammarAnalysis.compute_reachability_static(grammar)
        assert s in reachable
        assert len(reachable) == 1

    def test_indirect_reachability(self):
        """Test indirect reachability through multiple nonterminals."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        c = Nonterminal("C", MessageType("proto", "C"))

        grammar = Grammar(s)

        # S -> A, A -> B, B -> C
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        param_c = Var("z", MessageType("proto", "C"))
        construct_action_s = Lambda([param_a], MessageType("proto", "S"), param_a)
        construct_action_a = Lambda([param_b], MessageType("proto", "A"), param_b)
        construct_action_b = Lambda([param_c], MessageType("proto", "B"), param_c)
        construct_action_c = Lambda([param_c], MessageType("proto", "C"), param_c)

        deconstruct_action_s = Lambda([Var('msg', MessageType("proto", "S"))], OptionType(MessageType("proto", "A")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('a')])]))
        deconstruct_action_a = Lambda([Var('msg', MessageType("proto", "A"))], OptionType(MessageType("proto", "B")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')])]))
        deconstruct_action_b = Lambda([Var('msg', MessageType("proto", "B"))], OptionType(MessageType("proto", "C")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "B")), Lit('c')])]))
        deconstruct_action_c = Lambda([Var('msg', MessageType("proto", "C"))], OptionType(MessageType("proto", "C")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "C")), Lit('c')])]))

        grammar.add_rule(Rule(s, a, construct_action_s, deconstruct_action_s))
        grammar.add_rule(Rule(a, b, construct_action_a, deconstruct_action_a))
        grammar.add_rule(Rule(b, c, construct_action_b, deconstruct_action_b))
        grammar.add_rule(Rule(c, c, construct_action_c, deconstruct_action_c))

        reachable = GrammarAnalysis.compute_reachability_static(grammar)
        assert len(reachable) == 4
        assert s in reachable
        assert a in reachable
        assert b in reachable
        assert c in reachable


class TestComputeNullable:
    """Tests for compute_nullable."""

    def test_simple_grammar_no_nullable(self):
        """Test nullable computation with no nullable nonterminals."""
        grammar, s, a, b, _, _ = make_simple_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert not nullable[s]
        assert not nullable[a]
        assert not nullable[b]

    def test_nullable_grammar(self):
        """Test nullable computation with nullable nonterminal."""
        grammar, s, a, b = make_nullable_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[a]
        assert not nullable[b]
        assert not nullable[s]

    def test_star_makes_nullable(self):
        """Test that star makes sequence nullable."""
        from meta.target import ListType
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        star_a = Star(a)

        grammar = Grammar(s)
        param = Var("x", ListType(MessageType("proto", "A")))
        construct_action = Lambda([param], MessageType("proto", "S"), param)
        deconstruct_action = Lambda(
            [Var('msg', MessageType("proto", "S"))],
            OptionType(ListType(MessageType("proto", "A"))),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('list')])])
        )
        grammar.add_rule(Rule(s, star_a, construct_action, deconstruct_action))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[s]

    def test_option_makes_nullable(self):
        """Test that option makes nonterminal nullable."""
        from meta.target import OptionType
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        opt_a = Option(a)

        grammar = Grammar(s)
        param = Var("x", OptionType(MessageType("proto", "A")))
        construct_action = Lambda([param], MessageType("proto", "S"), param)
        deconstruct_action = Lambda(
            [Var('msg', MessageType("proto", "S"))],
            OptionType(OptionType(MessageType("proto", "A"))),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('opt')])])
        )
        grammar.add_rule(Rule(s, opt_a, construct_action, deconstruct_action))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[s]

    def test_empty_sequence_makes_nullable(self):
        """Test that empty sequence makes nonterminal nullable."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        construct_action = Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))
        deconstruct_action = Lambda(
            [Var('msg', MessageType("proto", "S"))],
            OptionType(TupleType([])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
        )
        grammar.add_rule(Rule(s, Sequence(()), construct_action, deconstruct_action))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[s]

    def test_transitive_nullable(self):
        """Test transitive nullable through multiple nonterminals."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))

        grammar = Grammar(s)

        # S -> A, A -> B, B -> epsilon
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        construct_action_s = Lambda([param_a], MessageType("proto", "S"), param_a)
        construct_action_a = Lambda([param_b], MessageType("proto", "A"), param_b)
        construct_action_b = Lambda([], MessageType("proto", "B"), Var("z", MessageType("proto", "B")))

        deconstruct_action_s = Lambda([Var('msg', MessageType("proto", "S"))], OptionType(MessageType("proto", "A")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('a')])]))
        deconstruct_action_a = Lambda([Var('msg', MessageType("proto", "A"))], OptionType(MessageType("proto", "B")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')])]))
        deconstruct_action_b = Lambda([Var('msg', MessageType("proto", "B"))], OptionType(TupleType([])), Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])]))

        grammar.add_rule(Rule(s, a, construct_action_s, deconstruct_action_s))
        grammar.add_rule(Rule(a, b, construct_action_a, deconstruct_action_a))
        grammar.add_rule(Rule(b, Sequence(()), construct_action_b, deconstruct_action_b))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[s]
        assert nullable[a]
        assert nullable[b]


class TestIsRhsNullable:
    """Tests for is_rhs_nullable."""

    def test_literal_not_nullable(self):
        """Test that literal is not nullable."""
        lit = LitTerminal("a")
        nullable = {}
        assert not GrammarAnalysis.is_rhs_nullable(lit, nullable)

    def test_terminal_not_nullable(self):
        """Test that terminal is not nullable."""
        term = NamedTerminal("TOK", BaseType("String"))
        nullable = {}
        assert not GrammarAnalysis.is_rhs_nullable(term, nullable)

    def test_nonterminal_nullable(self):
        """Test nonterminal nullable when in nullable set."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        nullable = {nt: True}
        assert GrammarAnalysis.is_rhs_nullable(nt, nullable)

    def test_nonterminal_not_nullable(self):
        """Test nonterminal not nullable when not in set."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        nullable = {nt: False}
        assert not GrammarAnalysis.is_rhs_nullable(nt, nullable)

    def test_star_nullable(self):
        """Test that star is always nullable."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        star = Star(nt)
        nullable = {nt: False}
        assert GrammarAnalysis.is_rhs_nullable(star, nullable)

    def test_option_nullable(self):
        """Test that option is always nullable."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        opt = Option(nt)
        nullable = {nt: False}
        assert GrammarAnalysis.is_rhs_nullable(opt, nullable)

    def test_empty_sequence_nullable(self):
        """Test that empty sequence is nullable."""
        seq = Sequence(())
        nullable = {}
        assert GrammarAnalysis.is_rhs_nullable(seq, nullable)

    def test_sequence_all_nullable(self):
        """Test sequence is nullable when all elements are nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((a, b))
        nullable = {a: True, b: True}
        assert GrammarAnalysis.is_rhs_nullable(seq, nullable)

    def test_sequence_one_not_nullable(self):
        """Test sequence is not nullable when one element is not nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((a, b))
        nullable = {a: True, b: False}
        assert not GrammarAnalysis.is_rhs_nullable(seq, nullable)


class TestComputeFirst:
    """Tests for compute_first."""

    def test_simple_grammar(self):
        """Test FIRST computation for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)

        assert lit_a in first[a]
        assert lit_b in first[b]
        assert lit_a in first[s]

    def test_nullable_grammar(self):
        """Test FIRST with nullable nonterminal."""
        grammar, s, a, b = make_nullable_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)

        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")

        # A can start with "a"
        assert lit_a in first[a]
        # B starts with "b"
        assert lit_b in first[b]
        # S can start with "a" or "b" (because A is nullable)
        assert lit_a in first[s]
        assert lit_b in first[s]

    def test_left_recursive_grammar(self):
        """Test FIRST with left recursion."""
        grammar, s, t, num = make_left_recursive_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)

        # Both S and T start with NUM
        assert num in first[s]
        assert num in first[t]


class TestRhsFirst:
    """Tests for rhs_first."""

    def test_literal(self):
        """Test FIRST of literal."""
        lit = LitTerminal("a")
        first = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first(lit, first, nullable)
        assert lit in result

    def test_terminal(self):
        """Test FIRST of terminal."""
        term = NamedTerminal("NUM", BaseType("Int64"))
        first = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first(term, first, nullable)
        assert term in result

    def test_nonterminal(self):
        """Test FIRST of nonterminal."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        first = {nt: cast(set[Terminal], {lit})}
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first(nt, first, nullable)
        assert lit in result

    def test_sequence_all_first(self):
        """Test FIRST of sequence where first element is not nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        seq = Sequence((a, b))

        first = {a: cast(set[Terminal], {lit_a}), b: cast(set[Terminal], {lit_b})}
        nullable = {a: False, b: False}
        result = GrammarAnalysis.rhs_first(seq, first, nullable)
        assert lit_a in result
        assert lit_b not in result

    def test_sequence_nullable_first(self):
        """Test FIRST of sequence where first element is nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        seq = Sequence((a, b))

        first = {a: cast(set[Terminal], {lit_a}), b: cast(set[Terminal], {lit_b})}
        nullable = {a: True, b: False}
        result = GrammarAnalysis.rhs_first(seq, first, nullable)
        assert lit_a in result
        assert lit_b in result


class TestComputeFirstK:
    """Tests for compute_first_k."""

    def test_simple_grammar_k2(self):
        """Test FIRST_2 for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first_k = GrammarAnalysis.compute_first_k_static(grammar, k=2, nullable=nullable)

        # S -> A B, so FIRST_2(S) = {("a", "b")}
        assert (lit_a, lit_b) in first_k[s]

    def test_k1_matches_first(self):
        """Test that FIRST_1 matches regular FIRST."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        first_k = GrammarAnalysis.compute_first_k_static(grammar, k=1, nullable=nullable)

        for nt in [s, a, b]:
            first_set = {(t,) for t in first[nt]}
            assert first_set == first_k[nt]

    def test_empty_sequence_gives_empty_tuple(self):
        """Test that empty production gives empty tuple."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        construct_action = Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))
        deconstruct_action = Lambda(
            [Var('msg', MessageType("proto", "S"))],
            OptionType(TupleType([])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
        )
        grammar.add_rule(Rule(s, Sequence(()), construct_action, deconstruct_action))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first_k = GrammarAnalysis.compute_first_k_static(grammar, k=2, nullable=nullable)
        assert () in first_k[s]


class TestRhsFirstK:
    """Tests for rhs_first_k."""

    def test_literal_k2(self):
        """Test FIRST_k of literal."""
        lit = LitTerminal("a")
        first_k = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first_k(lit, first_k, nullable, k=2)
        assert (lit,) in result

    def test_terminal_k2(self):
        """Test FIRST_k of terminal."""
        term = NamedTerminal("NUM", BaseType("Int64"))
        first_k = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first_k(term, first_k, nullable, k=2)
        assert (term,) in result

    def test_nonterminal_k2(self):
        """Test FIRST_k of nonterminal."""
        from meta.grammar_analysis import TerminalSeq  # type: ignore[import-untyped]
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        first_k = {nt: cast(set[TerminalSeq], {(lit,)})}
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first_k(nt, first_k, nullable, k=2)
        assert (lit,) in result

    def test_sequence_concatenation_k2(self):
        """Test FIRST_k of sequence concatenates."""
        from meta.grammar_analysis import TerminalSeq  # type: ignore[import-untyped]
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        seq = Sequence((a, b))

        first_k = {a: cast(set[TerminalSeq], {(lit_a,)}), b: cast(set[TerminalSeq], {(lit_b,)})}
        nullable = {a: False, b: False}
        result = GrammarAnalysis.rhs_first_k(seq, first_k, nullable, k=2)
        assert (lit_a, lit_b) in result

    def test_sequence_truncates_to_k(self):
        """Test FIRST_k truncates sequences to k."""
        from meta.grammar_analysis import TerminalSeq  # type: ignore[import-untyped]
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        c = Nonterminal("C", MessageType("proto", "C"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        seq = Sequence((a, b, c))

        first_k = {a: cast(set[TerminalSeq], {(lit_a,)}), b: cast(set[TerminalSeq], {(lit_b,)}), c: cast(set[TerminalSeq], {(lit_c,)})}
        nullable = {a: False, b: False, c: False}
        result = GrammarAnalysis.rhs_first_k(seq, first_k, nullable, k=2)
        assert (lit_a, lit_b) in result
        assert (lit_a, lit_b, lit_c) not in result

    def test_empty_sequence_gives_empty_tuple(self):
        """Test empty sequence gives empty tuple."""
        seq = Sequence(())
        first_k = {}
        nullable = {}
        result = GrammarAnalysis.rhs_first_k(seq, first_k, nullable, k=2)
        assert () in result

    def test_star_includes_empty(self):
        """Test that star includes empty tuple."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        star = Star(nt)

        first_k = {nt: {(lit,)}}  # type: ignore
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first_k(star, first_k, nullable, k=2)
        assert (lit,) in result
        assert () in result

    def test_option_includes_empty(self):
        """Test that option includes empty tuple."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        opt = Option(nt)

        first_k = {nt: {(lit,)}}  # type: ignore
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first_k(opt, first_k, nullable, k=2)
        assert (lit,) in result
        assert () in result


class TestComputeFollow:
    """Tests for compute_follow."""

    def test_simple_grammar(self):
        """Test FOLLOW for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)

        # FOLLOW(A) includes FIRST(B) = {"b"}
        assert lit_b in follow[a]
        # FOLLOW(S) includes EOF
        eof = NamedTerminal('$', BaseType('EOF'))
        assert eof in follow[s]

    def test_nullable_propagates_follow(self):
        """Test that nullable nonterminal propagates FOLLOW."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_b = LitTerminal("b")

        grammar = Grammar(s)

        # S -> A B
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        construct_action_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
        deconstruct_action_s = Lambda(
            [Var('msg', MessageType("proto", "S"))],
            OptionType(TupleType([MessageType("proto", "A"), MessageType("proto", "B")])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('a')]),
                Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('b')])
            ])])
        )
        grammar.add_rule(Rule(s, Sequence((a, b)), construct_action_s, deconstruct_action_s))

        # A -> epsilon
        construct_action_a = Lambda([], MessageType("proto", "A"), Var("z", MessageType("proto", "A")))
        deconstruct_action_a = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(TupleType([])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
        )
        grammar.add_rule(Rule(a, Sequence(()), construct_action_a, deconstruct_action_a))

        # B -> "b"
        construct_action_b = Lambda([], MessageType("proto", "B"), Var("w", MessageType("proto", "B")))
        deconstruct_action_b = Lambda(
            [Var('msg', MessageType("proto", "B"))],
            OptionType(TupleType([])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
        )
        grammar.add_rule(Rule(b, lit_b, construct_action_b, deconstruct_action_b))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)

        # FOLLOW(A) includes FIRST(B) = {"b"}
        assert lit_b in follow[a]
        # FOLLOW(A) also includes FOLLOW(S) because B might be nullable
        # But in this case B is not nullable, so just {"b"}


class TestRhsFollow:
    """Tests for rhs_follow."""

    def test_nonterminal_at_end(self):
        """Test FOLLOW for nonterminal at end of production."""
        lhs = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        lit_a = LitTerminal("a")

        first = {a: {lit_a}}  # type: ignore
        nullable = {a: False}
        follow = {lhs: {lit_a}}  # type: ignore

        result = GrammarAnalysis.rhs_follow(a, lhs, first, nullable, follow)
        assert a in result
        assert lit_a in result[a]

    def test_nonterminal_followed_by_terminal(self):
        """Test FOLLOW for nonterminal followed by terminal."""
        lhs = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_b = LitTerminal("b")

        seq = Sequence((a, lit_b))
        first = {a: set(), b: set()}
        nullable = {a: False, b: False}
        follow = {lhs: set()}

        result = GrammarAnalysis.rhs_follow(seq, lhs, first, nullable, follow)
        assert a in result
        assert lit_b in result[a]


class TestComputeFollowK:
    """Tests for compute_follow_k."""

    def test_simple_grammar_k2(self):
        """Test FOLLOW_2 for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first_k = GrammarAnalysis.compute_first_k_static(grammar, k=2, nullable=nullable)
        follow_k = GrammarAnalysis.compute_follow_k_static(grammar, k=2, nullable=nullable, first_k=first_k)

        # FOLLOW_2(A) includes FIRST_2(B) = {("b",)}
        assert (lit_b,) in follow_k[a]

        # FOLLOW_2(S) includes {("$",)}
        eof = NamedTerminal('$', BaseType('EOF'))
        assert (eof,) in follow_k[s]

    def test_k1_matches_follow(self):
        """Test that FOLLOW_1 matches regular FOLLOW."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        first_k = GrammarAnalysis.compute_first_k_static(grammar, k=1, nullable=nullable)
        follow_k = GrammarAnalysis.compute_follow_k_static(grammar, k=1, nullable=nullable, first_k=first_k)

        for nt in [s, a, b]:
            follow_set = {(t,) for t in follow[nt]}
            assert follow_set == follow_k[nt]


class TestConcatK:
    """Tests for concat_k."""

    def test_concatenate_two_single_element_sets(self):
        """Test concatenating two single-element sets."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        set1 = {(lit_a,)}
        set2 = {(lit_b,)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a, lit_b) in result

    def test_truncate_to_k(self):
        """Test that concatenation truncates to k."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        set1 = {(lit_a,)}
        set2 = {(lit_b, lit_c)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a, lit_b) in result
        assert (lit_a, lit_b, lit_c) not in result

    def test_already_at_k_length(self):
        """Test sequences already at k length."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        set1 = {(lit_a, lit_b)}
        set2 = {(lit_c,)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a, lit_b) in result

    def test_empty_tuple_concatenation(self):
        """Test concatenation with empty tuple."""
        lit_a = LitTerminal("a")
        set1 = {()}
        set2 = {(lit_a,)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a,) in result

    def test_multiple_sequences(self):
        """Test concatenation with multiple sequences."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        set1 = {(lit_a,), (lit_b,)}
        set2 = {(lit_c,)}

        result = GrammarAnalysis.concat_k(set1, set2, k=2)
        assert (lit_a, lit_c) in result
        assert (lit_b, lit_c) in result


class TestIntegration:
    """Integration tests combining multiple analysis functions."""

    def test_grammar_methods_cache_results(self):
        """Test that Grammar methods properly cache results."""
        grammar, s, a, b, _, _ = make_simple_grammar()

        # First call should compute
        nullable1 = grammar.compute_nullable()
        # Second call should return cached value
        nullable2 = grammar.compute_nullable()
        assert nullable1 is nullable2

        # Same for FIRST
        first1 = grammar.compute_first()
        first2 = grammar.compute_first()
        assert first1 is first2

        # Same for FOLLOW
        follow1 = grammar.compute_follow()
        follow2 = grammar.compute_follow()
        assert follow1 is follow2

    def test_complete_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        # Check reachability
        reachable = GrammarAnalysis.compute_reachability_static(grammar)
        assert len(reachable) == 3

        # Compute nullable
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert not any(nullable.values())

        # Compute FIRST
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert lit_a in first[s]

        # Compute FOLLOW
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        assert lit_b in follow[a]

    def test_complex_grammar_analysis(self):
        """Test analysis on more complex grammar."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")

        grammar = Grammar(s)

        # S -> A B | B
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        construct_action1 = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
        deconstruct_action1 = Lambda(
            [Var('msg', MessageType("proto", "S"))],
            OptionType(TupleType([MessageType("proto", "A"), MessageType("proto", "B")])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('a')]),
                Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('b')])
            ])])
        )
        grammar.add_rule(Rule(s, Sequence((a, b)), construct_action1, deconstruct_action1))

        param_b2 = Var("z", MessageType("proto", "B"))
        construct_action2 = Lambda([param_b2], MessageType("proto", "S"), param_b2)
        deconstruct_action2 = Lambda(
            [Var('msg', MessageType("proto", "S"))],
            OptionType(MessageType("proto", "B")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "S")), Lit('b')])])
        )
        grammar.add_rule(Rule(s, b, construct_action2, deconstruct_action2))

        # A -> "a"
        construct_action3 = Lambda([], MessageType("proto", "A"), Var("w", MessageType("proto", "A")))
        deconstruct_action3 = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(TupleType([])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
        )
        grammar.add_rule(Rule(a, lit_a, construct_action3, deconstruct_action3))

        # B -> "b"
        construct_action4 = Lambda([], MessageType("proto", "B"), Var("v", MessageType("proto", "B")))
        deconstruct_action4 = Lambda(
            [Var('msg', MessageType("proto", "B"))],
            OptionType(TupleType([])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [])])
        )
        grammar.add_rule(Rule(b, lit_b, construct_action4, deconstruct_action4))

        # Check everything works together
        reachable = GrammarAnalysis.compute_reachability_static(grammar)
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)

        assert len(reachable) == 3
        assert lit_a in first[s]
        assert lit_b in first[s]
