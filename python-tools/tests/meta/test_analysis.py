#!/usr/bin/env python3
# pyright: reportArgumentType=false
"""Tests for grammar analysis functions."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    LitTerminal, NamedTerminal, Nonterminal,
    Star, Option, Sequence,
    Rule, Grammar,
)
from meta.grammar_analysis import (
    check_reachability,
    compute_nullable,
    compute_first,
    compute_first_k,
    compute_follow,
    compute_follow_k,
    _is_rhs_elem_nullable,
    _compute_rhs_elem_first,
    _compute_rhs_elem_first_k,
    _compute_rhs_elem_follow,
    _compute_rhs_elem_follow_k,
    _concat_first_k_sets,
)
from meta.target import BaseType, MessageType, Lambda, Var


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
    action_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, Sequence((a, b)), action_s))

    # A -> "a"
    action_a = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, lit_a, action_a))

    # B -> "b"
    action_b = Lambda([], MessageType("proto", "B"), Var("y", MessageType("proto", "B")))
    grammar.add_rule(Rule(b, lit_b, action_b))

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
    action_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, Sequence((a, b)), action_s))

    # A -> "a"
    action_a1 = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, lit_a, action_a1))

    # A -> epsilon
    action_a2 = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, Sequence(()), action_a2))

    # B -> "b"
    action_b = Lambda([], MessageType("proto", "B"), Var("y", MessageType("proto", "B")))
    grammar.add_rule(Rule(b, lit_b, action_b))

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
    action_s1 = Lambda([param_s, param_t1], MessageType("proto", "S"), param_s)
    grammar.add_rule(Rule(s, Sequence((s, plus, t)), action_s1))

    # S -> T
    param_t2 = Var("z", MessageType("proto", "T"))
    action_s2 = Lambda([param_t2], MessageType("proto", "S"), param_t2)
    grammar.add_rule(Rule(s, t, action_s2))

    # T -> NUM
    param_num = Var("n", BaseType("Int64"))
    action_t = Lambda([param_num], MessageType("proto", "T"), param_num)
    grammar.add_rule(Rule(t, num, action_t))

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
    action_s = Lambda([param_a], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, a, action_s))

    # A -> "a"
    action_a = Lambda([], MessageType("proto", "A"), Var("y", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, lit_a, action_a))

    # B -> "b" (unreachable)
    action_b = Lambda([], MessageType("proto", "B"), Var("z", MessageType("proto", "B")))
    grammar.add_rule(Rule(b, lit_b, action_b))

    return grammar, s, a, b


class TestCheckReachability:
    """Tests for check_reachability."""

    def test_simple_grammar_all_reachable(self):
        """Test reachability in simple grammar where all nonterminals are reachable."""
        grammar, s, a, b, _, _ = make_simple_grammar()
        reachable = check_reachability(grammar)
        assert s in reachable
        assert a in reachable
        assert b in reachable
        assert len(reachable) == 3

    def test_unreachable_nonterminal(self):
        """Test reachability with unreachable nonterminal."""
        grammar, s, a, b = make_unreachable_grammar()
        reachable = check_reachability(grammar)
        assert s in reachable
        assert a in reachable
        assert b not in reachable
        assert len(reachable) == 2

    def test_empty_grammar(self):
        """Test reachability with grammar that has no rules for start."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        reachable = check_reachability(grammar)
        # Start is always added to rules dict by Grammar constructor
        assert len(reachable) == 1
        assert s in reachable

    def test_single_rule(self):
        """Test reachability with single rule."""
        s = Nonterminal("S", MessageType("proto", "S"))
        lit = LitTerminal("a")
        grammar = Grammar(s)
        action = Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))
        grammar.add_rule(Rule(s, lit, action))
        reachable = check_reachability(grammar)
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
        action_s = Lambda([param_a], MessageType("proto", "S"), param_a)
        action_a = Lambda([param_b], MessageType("proto", "A"), param_b)
        action_b = Lambda([param_c], MessageType("proto", "B"), param_c)
        action_c = Lambda([param_c], MessageType("proto", "C"), param_c)

        grammar.add_rule(Rule(s, a, action_s))
        grammar.add_rule(Rule(a, b, action_a))
        grammar.add_rule(Rule(b, c, action_b))
        grammar.add_rule(Rule(c, c, action_c))

        reachable = check_reachability(grammar)
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
        nullable = compute_nullable(grammar)
        assert not nullable[s]
        assert not nullable[a]
        assert not nullable[b]

    def test_nullable_grammar(self):
        """Test nullable computation with nullable nonterminal."""
        grammar, s, a, b = make_nullable_grammar()
        nullable = compute_nullable(grammar)
        assert nullable[a]
        assert not nullable[b]
        assert not nullable[s]

    def test_star_makes_nullable(self):
        """Test that star makes sequence nullable."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        star_a = Star(a)

        grammar = Grammar(s)
        param = Var("x", MessageType("proto", "S"))
        action = Lambda([param], MessageType("proto", "S"), param)
        grammar.add_rule(Rule(s, star_a, action))

        nullable = compute_nullable(grammar)
        assert nullable[s]

    def test_option_makes_nullable(self):
        """Test that option makes nonterminal nullable."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        opt_a = Option(a)

        grammar = Grammar(s)
        param = Var("x", MessageType("proto", "S"))
        action = Lambda([param], MessageType("proto", "S"), param)
        grammar.add_rule(Rule(s, opt_a, action))

        nullable = compute_nullable(grammar)
        assert nullable[s]

    def test_empty_sequence_makes_nullable(self):
        """Test that empty sequence makes nonterminal nullable."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        action = Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))
        grammar.add_rule(Rule(s, Sequence(()), action))

        nullable = compute_nullable(grammar)
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
        action_s = Lambda([param_a], MessageType("proto", "S"), param_a)
        action_a = Lambda([param_b], MessageType("proto", "A"), param_b)
        action_b = Lambda([], MessageType("proto", "B"), Var("z", MessageType("proto", "B")))

        grammar.add_rule(Rule(s, a, action_s))
        grammar.add_rule(Rule(a, b, action_a))
        grammar.add_rule(Rule(b, Sequence(()), action_b))

        nullable = compute_nullable(grammar)
        assert nullable[s]
        assert nullable[a]
        assert nullable[b]


class TestIsRhsElemNullable:
    """Tests for _is_rhs_elem_nullable."""

    def test_literal_not_nullable(self):
        """Test that literal is not nullable."""
        lit = LitTerminal("a")
        nullable = {}
        assert not _is_rhs_elem_nullable(lit, nullable)

    def test_terminal_not_nullable(self):
        """Test that terminal is not nullable."""
        term = NamedTerminal("TOK", BaseType("String"))
        nullable = {}
        assert not _is_rhs_elem_nullable(term, nullable)

    def test_nonterminal_nullable(self):
        """Test nonterminal nullable when in nullable set."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        nullable = {nt: True}
        assert _is_rhs_elem_nullable(nt, nullable)

    def test_nonterminal_not_nullable(self):
        """Test nonterminal not nullable when not in set."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        nullable = {nt: False}
        assert not _is_rhs_elem_nullable(nt, nullable)

    def test_star_nullable(self):
        """Test that star is always nullable."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        star = Star(nt)
        nullable = {nt: False}
        assert _is_rhs_elem_nullable(star, nullable)

    def test_option_nullable(self):
        """Test that option is always nullable."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        opt = Option(nt)
        nullable = {nt: False}
        assert _is_rhs_elem_nullable(opt, nullable)

    def test_empty_sequence_nullable(self):
        """Test that empty sequence is nullable."""
        seq = Sequence(())
        nullable = {}
        assert _is_rhs_elem_nullable(seq, nullable)

    def test_sequence_all_nullable(self):
        """Test sequence is nullable when all elements are nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((a, b))
        nullable = {a: True, b: True}
        assert _is_rhs_elem_nullable(seq, nullable)

    def test_sequence_one_not_nullable(self):
        """Test sequence is not nullable when one element is not nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((a, b))
        nullable = {a: True, b: False}
        assert not _is_rhs_elem_nullable(seq, nullable)


class TestComputeFirst:
    """Tests for compute_first."""

    def test_simple_grammar(self):
        """Test FIRST computation for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        first = compute_first(grammar)

        assert lit_a in first[a]
        assert lit_b in first[b]
        assert lit_a in first[s]

    def test_nullable_grammar(self):
        """Test FIRST with nullable nonterminal."""
        grammar, s, a, b = make_nullable_grammar()
        first = compute_first(grammar)

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
        first = compute_first(grammar)

        # Both S and T start with NUM
        assert num in first[s]
        assert num in first[t]


class TestComputeRhsElemFirst:
    """Tests for _compute_rhs_elem_first."""

    def test_literal(self):
        """Test FIRST of literal."""
        lit = LitTerminal("a")
        first = {}
        nullable = {}
        result = _compute_rhs_elem_first(lit, first, nullable)
        assert lit in result

    def test_terminal(self):
        """Test FIRST of terminal."""
        term = NamedTerminal("NUM", BaseType("Int64"))
        first = {}
        nullable = {}
        result = _compute_rhs_elem_first(term, first, nullable)
        assert term in result

    def test_nonterminal(self):
        """Test FIRST of nonterminal."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        first = {nt: {lit}}
        nullable = {nt: False}
        result = _compute_rhs_elem_first(nt, first, nullable)
        assert lit in result

    def test_sequence_all_first(self):
        """Test FIRST of sequence where first element is not nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        seq = Sequence((a, b))

        first = {a: {lit_a}, b: {lit_b}}
        nullable = {a: False, b: False}
        result = _compute_rhs_elem_first(seq, first, nullable)
        assert lit_a in result
        assert lit_b not in result

    def test_sequence_nullable_first(self):
        """Test FIRST of sequence where first element is nullable."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        seq = Sequence((a, b))

        first = {a: {lit_a}, b: {lit_b}}
        nullable = {a: True, b: False}
        result = _compute_rhs_elem_first(seq, first, nullable)
        assert lit_a in result
        assert lit_b in result


class TestComputeFirstK:
    """Tests for compute_first_k."""

    def test_simple_grammar_k2(self):
        """Test FIRST_2 for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        first_k = compute_first_k(grammar, k=2)

        # S -> A B, so FIRST_2(S) = {("a", "b")}
        assert (lit_a, lit_b) in first_k[s]

    def test_k1_matches_first(self):
        """Test that FIRST_1 matches regular FIRST."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        first = compute_first(grammar)
        first_k = compute_first_k(grammar, k=1)

        for nt in [s, a, b]:
            first_set = {(t,) for t in first[nt]}
            assert first_set == first_k[nt]

    def test_empty_sequence_gives_empty_tuple(self):
        """Test that empty production gives empty tuple."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        action = Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))
        grammar.add_rule(Rule(s, Sequence(()), action))

        first_k = compute_first_k(grammar, k=2)
        assert () in first_k[s]


class TestComputeRhsElemFirstK:
    """Tests for _compute_rhs_elem_first_k."""

    def test_literal_k2(self):
        """Test FIRST_k of literal."""
        lit = LitTerminal("a")
        first_k = {}
        nullable = {}
        result = _compute_rhs_elem_first_k(lit, first_k, nullable, k=2)
        assert (lit,) in result

    def test_terminal_k2(self):
        """Test FIRST_k of terminal."""
        term = NamedTerminal("NUM", BaseType("Int64"))
        first_k = {}
        nullable = {}
        result = _compute_rhs_elem_first_k(term, first_k, nullable, k=2)
        assert (term,) in result

    def test_nonterminal_k2(self):
        """Test FIRST_k of nonterminal."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        first_k = {nt: {(lit,)}}
        nullable = {nt: False}
        result = _compute_rhs_elem_first_k(nt, first_k, nullable, k=2)
        assert (lit,) in result

    def test_sequence_concatenation_k2(self):
        """Test FIRST_k of sequence concatenates."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        seq = Sequence((a, b))

        first_k = {a: {(lit_a,)}, b: {(lit_b,)}}
        nullable = {a: False, b: False}
        result = _compute_rhs_elem_first_k(seq, first_k, nullable, k=2)
        assert (lit_a, lit_b) in result

    def test_sequence_truncates_to_k(self):
        """Test FIRST_k truncates sequences to k."""
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        c = Nonterminal("C", MessageType("proto", "C"))
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        seq = Sequence((a, b, c))

        first_k = {a: {(lit_a,)}, b: {(lit_b,)}, c: {(lit_c,)}}
        nullable = {a: False, b: False, c: False}
        result = _compute_rhs_elem_first_k(seq, first_k, nullable, k=2)
        assert (lit_a, lit_b) in result
        assert (lit_a, lit_b, lit_c) not in result

    def test_empty_sequence_gives_empty_tuple(self):
        """Test empty sequence gives empty tuple."""
        seq = Sequence(())
        first_k = {}
        nullable = {}
        result = _compute_rhs_elem_first_k(seq, first_k, nullable, k=2)
        assert () in result

    def test_star_includes_empty(self):
        """Test that star includes empty tuple."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        star = Star(nt)

        first_k = {nt: {(lit,)}}
        nullable = {nt: False}
        result = _compute_rhs_elem_first_k(star, first_k, nullable, k=2)
        assert (lit,) in result
        assert () in result

    def test_option_includes_empty(self):
        """Test that option includes empty tuple."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        opt = Option(nt)

        first_k = {nt: {(lit,)}}
        nullable = {nt: False}
        result = _compute_rhs_elem_first_k(opt, first_k, nullable, k=2)
        assert (lit,) in result
        assert () in result


class TestComputeFollow:
    """Tests for compute_follow."""

    def test_simple_grammar(self):
        """Test FOLLOW for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        follow = compute_follow(grammar)

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
        action_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
        grammar.add_rule(Rule(s, Sequence((a, b)), action_s))

        # A -> epsilon
        action_a = Lambda([], MessageType("proto", "A"), Var("z", MessageType("proto", "A")))
        grammar.add_rule(Rule(a, Sequence(()), action_a))

        # B -> "b"
        action_b = Lambda([], MessageType("proto", "B"), Var("w", MessageType("proto", "B")))
        grammar.add_rule(Rule(b, lit_b, action_b))

        follow = compute_follow(grammar)

        # FOLLOW(A) includes FIRST(B) = {"b"}
        assert lit_b in follow[a]
        # FOLLOW(A) also includes FOLLOW(S) because B might be nullable
        # But in this case B is not nullable, so just {"b"}


class TestComputeRhsElemFollow:
    """Tests for _compute_rhs_elem_follow."""

    def test_nonterminal_at_end(self):
        """Test FOLLOW for nonterminal at end of production."""
        lhs = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        lit_a = LitTerminal("a")

        first = {a: {lit_a}}
        nullable = {a: False}
        follow = {lhs: {lit_a}}

        result = _compute_rhs_elem_follow(a, lhs, first, nullable, follow)
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

        result = _compute_rhs_elem_follow(seq, lhs, first, nullable, follow)
        assert a in result
        assert lit_b in result[a]


class TestComputeFollowK:
    """Tests for compute_follow_k."""

    def test_simple_grammar_k2(self):
        """Test FOLLOW_2 for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        follow_k = compute_follow_k(grammar, k=2)

        # FOLLOW_2(A) includes FIRST_2(B) = {("b",)}
        assert (lit_b,) in follow_k[a]

        # FOLLOW_2(S) includes {("$",)}
        eof = NamedTerminal('$', BaseType('EOF'))
        assert (eof,) in follow_k[s]

    def test_k1_matches_follow(self):
        """Test that FOLLOW_1 matches regular FOLLOW."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        follow = compute_follow(grammar)
        follow_k = compute_follow_k(grammar, k=1)

        for nt in [s, a, b]:
            follow_set = {(t,) for t in follow[nt]}
            assert follow_set == follow_k[nt]


class TestConcatFirstKSets:
    """Tests for _concat_first_k_sets."""

    def test_concatenate_two_single_element_sets(self):
        """Test concatenating two single-element sets."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        set1 = {(lit_a,)}
        set2 = {(lit_b,)}

        result = _concat_first_k_sets(set1, set2, k=2)
        assert (lit_a, lit_b) in result

    def test_truncate_to_k(self):
        """Test that concatenation truncates to k."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        set1 = {(lit_a,)}
        set2 = {(lit_b, lit_c)}

        result = _concat_first_k_sets(set1, set2, k=2)
        assert (lit_a, lit_b) in result
        assert (lit_a, lit_b, lit_c) not in result

    def test_already_at_k_length(self):
        """Test sequences already at k length."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        set1 = {(lit_a, lit_b)}
        set2 = {(lit_c,)}

        result = _concat_first_k_sets(set1, set2, k=2)
        assert (lit_a, lit_b) in result

    def test_empty_tuple_concatenation(self):
        """Test concatenation with empty tuple."""
        lit_a = LitTerminal("a")
        set1 = {()}
        set2 = {(lit_a,)}

        result = _concat_first_k_sets(set1, set2, k=2)
        assert (lit_a,) in result

    def test_multiple_sequences(self):
        """Test concatenation with multiple sequences."""
        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")
        set1 = {(lit_a,), (lit_b,)}
        set2 = {(lit_c,)}

        result = _concat_first_k_sets(set1, set2, k=2)
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
        reachable = check_reachability(grammar)
        assert len(reachable) == 3

        # Compute nullable
        nullable = compute_nullable(grammar)
        assert not any(nullable.values())

        # Compute FIRST
        first = compute_first(grammar, nullable)
        assert lit_a in first[s]

        # Compute FOLLOW
        follow = compute_follow(grammar, nullable, first)
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
        action1 = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
        grammar.add_rule(Rule(s, Sequence((a, b)), action1))

        param_b2 = Var("z", MessageType("proto", "B"))
        action2 = Lambda([param_b2], MessageType("proto", "S"), param_b2)
        grammar.add_rule(Rule(s, b, action2))

        # A -> "a"
        action3 = Lambda([], MessageType("proto", "A"), Var("w", MessageType("proto", "A")))
        grammar.add_rule(Rule(a, lit_a, action3))

        # B -> "b"
        action4 = Lambda([], MessageType("proto", "B"), Var("v", MessageType("proto", "B")))
        grammar.add_rule(Rule(b, lit_b, action4))

        # Check everything works together
        reachable = check_reachability(grammar)
        nullable = compute_nullable(grammar)
        first = compute_first(grammar, nullable)
        follow = compute_follow(grammar, nullable, first)

        assert len(reachable) == 3
        assert lit_a in first[s]
        assert lit_b in first[s]
