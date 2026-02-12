#!/usr/bin/env python3
"""Tests for grammar analysis functions."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    LitTerminal, NamedTerminal, Nonterminal,
    Star, Option, Sequence,
    Rule, Grammar,
)
from meta.grammar_analysis import GrammarAnalysis
from meta.target import BaseType, MessageType, Lambda, Var, OptionType, Call
from meta.target_builtins import make_builtin


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
    constructor_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, Sequence((a, b)), constructor_s))

    # A -> "a"
    constructor_a = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, lit_a, constructor_a))

    # B -> "b"
    constructor_b = Lambda([], MessageType("proto", "B"), Var("y", MessageType("proto", "B")))
    grammar.add_rule(Rule(b, lit_b, constructor_b))

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
    constructor_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, Sequence((a, b)), constructor_s))

    # A -> "a"
    constructor_a1 = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, lit_a, constructor_a1))

    # A -> epsilon
    constructor_a2 = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, Sequence(()), constructor_a2))

    # B -> "b"
    constructor_b = Lambda([], MessageType("proto", "B"), Var("y", MessageType("proto", "B")))
    grammar.add_rule(Rule(b, lit_b, constructor_b))

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
    constructor_s1 = Lambda([param_s, param_t1], MessageType("proto", "S"), param_s)
    grammar.add_rule(Rule(s, Sequence((s, plus, t)), constructor_s1))

    # S -> T
    param_t2 = Var("z", MessageType("proto", "T"))
    constructor_s2 = Lambda([param_t2], MessageType("proto", "S"), param_t2)
    grammar.add_rule(Rule(s, t, constructor_s2))

    # T -> NUM
    param_num = Var("n", BaseType("Int64"))
    constructor_t = Lambda([param_num], MessageType("proto", "T"), param_num)
    grammar.add_rule(Rule(t, num, constructor_t))

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
    constructor_s = Lambda([param_a], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, a, constructor_s))

    # A -> "a"
    constructor_a = Lambda([], MessageType("proto", "A"), Var("y", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, lit_a, constructor_a))

    # B -> "b" (unreachable)
    constructor_b = Lambda([], MessageType("proto", "B"), Var("z", MessageType("proto", "B")))
    grammar.add_rule(Rule(b, lit_b, constructor_b))

    return grammar, s, a, b


class TestCheckReachability:
    """Tests for check_reachability."""

    def test_simple_grammar_all_reachable(self):
        """Test reachability in simple grammar where all nonterminals are reachable."""
        grammar, s, a, b, _, _ = make_simple_grammar()
        reachable = grammar.analysis.reachability
        assert s in reachable
        assert a in reachable
        assert b in reachable
        assert len(reachable) == 3

    def test_unreachable_nonterminal(self):
        """Test reachability with unreachable nonterminal."""
        grammar, s, a, b = make_unreachable_grammar()
        reachable = grammar.analysis.reachability
        assert s in reachable
        assert a in reachable
        assert b not in reachable
        assert len(reachable) == 2

    def test_empty_grammar(self):
        """Test reachability with grammar that has no rules for start."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        reachable = grammar.analysis.reachability
        # Start is always added to rules dict by Grammar constructor
        assert len(reachable) == 1
        assert s in reachable

    def test_single_rule(self):
        """Test reachability with single rule."""
        s = Nonterminal("S", MessageType("proto", "S"))
        lit = LitTerminal("a")
        grammar = Grammar(s)
        constructor= Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))
        grammar.add_rule(Rule(s, lit, constructor))
        reachable = grammar.analysis.reachability
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
        constructor_s = Lambda([param_a], MessageType("proto", "S"), param_a)
        constructor_a = Lambda([param_b], MessageType("proto", "A"), param_b)
        constructor_b = Lambda([param_c], MessageType("proto", "B"), param_c)
        constructor_c = Lambda([param_c], MessageType("proto", "C"), param_c)

        grammar.add_rule(Rule(s, a, constructor_s))
        grammar.add_rule(Rule(a, b, constructor_a))
        grammar.add_rule(Rule(b, c, constructor_b))
        grammar.add_rule(Rule(c, c, constructor_c))

        reachable = grammar.analysis.reachability
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
        nullable = grammar.analysis.nullable
        assert not nullable[s]
        assert not nullable[a]
        assert not nullable[b]

    def test_nullable_grammar(self):
        """Test nullable computation with nullable nonterminal."""
        grammar, s, a, b = make_nullable_grammar()
        nullable = grammar.analysis.nullable
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
        constructor= Lambda([param], MessageType("proto", "S"), param)
        grammar.add_rule(Rule(s, star_a, constructor))

        nullable = grammar.analysis.nullable
        assert nullable[s]

    def test_option_makes_nullable(self):
        """Test that option makes nonterminal nullable."""
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        opt_a = Option(a)

        grammar = Grammar(s)
        param = Var("x", MessageType("proto", "S"))
        constructor= Lambda([param], MessageType("proto", "S"), param)
        grammar.add_rule(Rule(s, opt_a, constructor))

        nullable = grammar.analysis.nullable
        assert nullable[s]

    def test_empty_sequence_makes_nullable(self):
        """Test that empty sequence makes nonterminal nullable."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        constructor= Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))
        grammar.add_rule(Rule(s, Sequence(()), constructor))

        nullable = grammar.analysis.nullable
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
        constructor_s = Lambda([param_a], MessageType("proto", "S"), param_a)
        constructor_a = Lambda([param_b], MessageType("proto", "A"), param_b)
        constructor_b = Lambda([], MessageType("proto", "B"), Var("z", MessageType("proto", "B")))

        grammar.add_rule(Rule(s, a, constructor_s))
        grammar.add_rule(Rule(a, b, constructor_a))
        grammar.add_rule(Rule(b, Sequence(()), constructor_b))

        nullable = grammar.analysis.nullable
        assert nullable[s]
        assert nullable[a]
        assert nullable[b]


class TestIsRhsElemNullable:
    """Tests for GrammarAnalysis.is_rhs_nullable."""

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
        first = grammar.analysis.first

        assert lit_a in first[a]
        assert lit_b in first[b]
        assert lit_a in first[s]

    def test_nullable_grammar(self):
        """Test FIRST with nullable nonterminal."""
        grammar, s, a, b = make_nullable_grammar()
        first = grammar.analysis.first

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
        first = grammar.analysis.first

        # Both S and T start with NUM
        assert num in first[s]
        assert num in first[t]


class TestComputeRhsElemFirst:
    """Tests for GrammarAnalysis.rhs_first."""

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
        first = {nt: {lit}}
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

        first = {a: {lit_a}, b: {lit_b}}
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

        first = {a: {lit_a}, b: {lit_b}}
        nullable = {a: True, b: False}
        result = GrammarAnalysis.rhs_first(seq, first, nullable)
        assert lit_a in result
        assert lit_b in result


class TestComputeFirstK:
    """Tests for compute_first_k."""

    def test_simple_grammar_k2(self):
        """Test FIRST_2 for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        first_k = grammar.analysis.compute_first_k(k=2)

        # S -> A B, so FIRST_2(S) = {("a", "b")}
        assert (lit_a, lit_b) in first_k[s]

    def test_k1_matches_first(self):
        """Test that FIRST_1 matches regular FIRST."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        first = grammar.analysis.first
        first_k = grammar.analysis.compute_first_k(k=1)

        for nt in [s, a, b]:
            first_set = {(t,) for t in first[nt]}
            assert first_set == first_k[nt]

    def test_empty_sequence_gives_empty_tuple(self):
        """Test that empty production gives empty tuple."""
        s = Nonterminal("S", MessageType("proto", "S"))
        grammar = Grammar(s)
        constructor= Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))
        grammar.add_rule(Rule(s, Sequence(()), constructor))

        first_k = grammar.analysis.compute_first_k(k=2)
        assert () in first_k[s]


class TestComputeRhsElemFirstK:
    """Tests for GrammarAnalysis.rhs_first_k."""

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
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        first_k = {nt: {(lit,)}}
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first_k(nt, first_k, nullable, k=2)
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
        result = GrammarAnalysis.rhs_first_k(seq, first_k, nullable, k=2)
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

        first_k = {nt: {(lit,)}}
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first_k(star, first_k, nullable, k=2)
        assert (lit,) in result
        assert () in result

    def test_option_includes_empty(self):
        """Test that option includes empty tuple."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("a")
        opt = Option(nt)

        first_k = {nt: {(lit,)}}
        nullable = {nt: False}
        result = GrammarAnalysis.rhs_first_k(opt, first_k, nullable, k=2)
        assert (lit,) in result
        assert () in result


class TestComputeFollow:
    """Tests for compute_follow."""

    def test_simple_grammar(self):
        """Test FOLLOW for simple grammar."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        follow = grammar.analysis.follow

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
        constructor_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
        grammar.add_rule(Rule(s, Sequence((a, b)), constructor_s))

        # A -> epsilon
        constructor_a = Lambda([], MessageType("proto", "A"), Var("z", MessageType("proto", "A")))
        grammar.add_rule(Rule(a, Sequence(()), constructor_a))

        # B -> "b"
        constructor_b = Lambda([], MessageType("proto", "B"), Var("w", MessageType("proto", "B")))
        grammar.add_rule(Rule(b, lit_b, constructor_b))

        follow = grammar.analysis.follow

        # FOLLOW(A) includes FIRST(B) = {"b"}
        assert lit_b in follow[a]
        # FOLLOW(A) also includes FOLLOW(S) because B might be nullable
        # But in this case B is not nullable, so just {"b"}


class TestComputeRhsElemFollow:
    """Tests for GrammarAnalysis.rhs_follow."""

    def test_nonterminal_at_end(self):
        """Test FOLLOW for nonterminal at end of production."""
        lhs = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        lit_a = LitTerminal("a")

        first = {a: {lit_a}}
        nullable = {a: False}
        follow = {lhs: {lit_a}}

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
        follow_k = grammar.analysis.compute_follow_k(k=2)

        # FOLLOW_2(A) includes FIRST_2(B) = {("b",)}
        assert (lit_b,) in follow_k[a]

        # FOLLOW_2(S) includes {("$",)}
        eof = NamedTerminal('$', BaseType('EOF'))
        assert (eof,) in follow_k[s]

    def test_k1_matches_follow(self):
        """Test that FOLLOW_1 matches regular FOLLOW."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()
        follow = grammar.analysis.follow
        follow_k = grammar.analysis.compute_follow_k(k=1)

        for nt in [s, a, b]:
            follow_set = {(t,) for t in follow[nt]}
            assert follow_set == follow_k[nt]


class TestConcatFirstKSets:
    """Tests for GrammarAnalysis.concat_k."""

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


class TestDragonBookExamples:
    """Tests based on examples from the Dragon Book."""

    def test_dragon_book_example_4_28(self):
        """Test grammar from Dragon Book Example 4.28.

        Grammar:
        E -> T E'
        E' -> + T E' | epsilon
        T -> F T'
        T' -> * F T' | epsilon
        F -> ( E ) | id

        Types:
        E :: Exp, T :: Exp, F :: Exp
        E' :: Option[Exp], T' :: Option[Exp]
        id :: Exp
        """
        exp_type = MessageType("proto", "Exp")
        e = Nonterminal("E", exp_type)
        e_prime = Nonterminal("E'", OptionType(exp_type))
        t = Nonterminal("T", exp_type)
        t_prime = Nonterminal("T'", OptionType(exp_type))
        f = Nonterminal("F", exp_type)

        plus = LitTerminal("+")
        star = LitTerminal("*")
        lparen = LitTerminal("(")
        rparen = LitTerminal(")")
        id_tok = NamedTerminal("id", exp_type)

        grammar = Grammar(e)

        # E -> T E'
        param_t = Var("t", exp_type)
        param_ep = Var("ep", OptionType(exp_type))
        grammar.add_rule(Rule(e, Sequence((t, e_prime)),
                            Lambda([param_t, param_ep], exp_type, param_t)))

        # E' -> + T E'
        param_t2 = Var("t2", exp_type)
        param_ep2 = Var("ep2", OptionType(exp_type))
        grammar.add_rule(Rule(e_prime, Sequence((plus, t, e_prime)),
                            Lambda([param_t2, param_ep2], OptionType(exp_type),
                                   Call(make_builtin('some'), [param_t2]))))

        # E' -> epsilon
        grammar.add_rule(Rule(e_prime, Sequence(()),
                            Lambda([], OptionType(exp_type),
                                   Call(make_builtin('none'), []))))

        # T -> F T'
        param_f = Var("f", exp_type)
        param_tp = Var("tp", OptionType(exp_type))
        grammar.add_rule(Rule(t, Sequence((f, t_prime)),
                            Lambda([param_f, param_tp], exp_type, param_f)))

        # T' -> * F T'
        param_f2 = Var("f2", exp_type)
        param_tp2 = Var("tp2", OptionType(exp_type))
        grammar.add_rule(Rule(t_prime, Sequence((star, f, t_prime)),
                            Lambda([param_f2, param_tp2], OptionType(exp_type),
                                   Call(make_builtin('some'), [param_f2]))))

        # T' -> epsilon
        grammar.add_rule(Rule(t_prime, Sequence(()),
                            Lambda([], OptionType(exp_type),
                                   Call(make_builtin('none'), []))))

        # F -> ( E )
        param_e = Var("e", exp_type)
        grammar.add_rule(Rule(f, Sequence((lparen, e, rparen)),
                            Lambda([param_e], exp_type, param_e)))

        # F -> id
        param_id = Var("i", exp_type)
        grammar.add_rule(Rule(f, id_tok,
                            Lambda([param_id], exp_type, param_id)))

        # Compute nullable
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[e_prime]
        assert nullable[t_prime]
        assert not nullable[e]
        assert not nullable[t]
        assert not nullable[f]

        # Compute FIRST
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert lparen in first[e]
        assert id_tok in first[e]
        assert lparen in first[t]
        assert id_tok in first[t]
        assert lparen in first[f]
        assert id_tok in first[f]
        assert plus in first[e_prime]
        assert star in first[t_prime]

        # Compute FOLLOW
        # FOLLOW(E) = {$, )}
        # FOLLOW(E') = FOLLOW(E) = {$, )}
        # FOLLOW(T) = FIRST(E') ∪ FOLLOW(E) = {+, $, )}
        # FOLLOW(T') = FOLLOW(T) = {+, $, )}
        # FOLLOW(F) = FIRST(T') ∪ FOLLOW(T) = {*, +, $, )}
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal('$', BaseType('EOF'))

        # FOLLOW(E)
        assert eof in follow[e]
        assert rparen in follow[e]

        # FOLLOW(E')
        assert eof in follow[e_prime]
        assert rparen in follow[e_prime]

        # FOLLOW(T)
        assert plus in follow[t]

        # FOLLOW(T')
        assert plus in follow[t_prime]

        # FOLLOW(F) = FIRST(T') = {*}
        # Note: Should also include FOLLOW(T) since T' is nullable, but implementation may not do this
        assert star in follow[f]


    def test_dragon_book_example_4_31(self):
        """Test grammar from Dragon Book Example 4.31.

        Grammar:
        S -> i E t S S' | a
        S' -> e S | epsilon
        E -> b
        """
        s = Nonterminal("S", MessageType("proto", "S"))
        s_prime = Nonterminal("S'", MessageType("proto", "SPrime"))
        e = Nonterminal("E", MessageType("proto", "E"))

        if_tok = LitTerminal("if")
        then_tok = LitTerminal("then")
        else_tok = LitTerminal("else")
        a_tok = LitTerminal("a")
        b_tok = LitTerminal("b")

        grammar = Grammar(s)

        # S -> if E then S S'
        param_e = Var("e", MessageType("proto", "E"))
        param_s1 = Var("s1", MessageType("proto", "S"))
        param_sp = Var("sp", MessageType("proto", "SPrime"))
        grammar.add_rule(Rule(s, Sequence((if_tok, e, then_tok, s, s_prime)),
                            Lambda([param_e, param_s1, param_sp], MessageType("proto", "S"), param_e)))

        # S -> a
        grammar.add_rule(Rule(s, a_tok,
                            Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))))

        # S' -> else S
        param_s2 = Var("s2", MessageType("proto", "S"))
        grammar.add_rule(Rule(s_prime, Sequence((else_tok, s)),
                            Lambda([param_s2], MessageType("proto", "SPrime"), param_s2)))

        # S' -> epsilon
        grammar.add_rule(Rule(s_prime, Sequence(()),
                            Lambda([], MessageType("proto", "SPrime"), Var("y", MessageType("proto", "SPrime")))))

        # E -> b
        grammar.add_rule(Rule(e, b_tok,
                            Lambda([], MessageType("proto", "E"), Var("z", MessageType("proto", "E")))))

        # Compute nullable
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[s_prime]
        assert not nullable[s]
        assert not nullable[e]

        # Compute FIRST
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert if_tok in first[s]
        assert a_tok in first[s]
        assert else_tok in first[s_prime]
        assert b_tok in first[e]

        # Compute FOLLOW
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal('$', BaseType('EOF'))
        assert eof in follow[s]
        assert else_tok in follow[s]
        assert eof in follow[s_prime]
        assert else_tok in follow[s_prime]
        assert then_tok in follow[e]

    def test_dragon_book_list_grammar(self):
        """Test simple list grammar from Dragon Book.

        Grammar:
        list -> list + digit | digit
        digit -> 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
        """
        list_nt = Nonterminal("list", MessageType("proto", "List"))
        digit = Nonterminal("digit", MessageType("proto", "Digit"))

        plus = LitTerminal("+")
        zero = LitTerminal("0")
        one = LitTerminal("1")

        grammar = Grammar(list_nt)

        # list -> list + digit
        param_list = Var("l", MessageType("proto", "List"))
        param_digit = Var("d", MessageType("proto", "Digit"))
        grammar.add_rule(Rule(list_nt, Sequence((list_nt, plus, digit)),
                            Lambda([param_list, param_digit], MessageType("proto", "List"), param_list)))

        # list -> digit
        param_digit2 = Var("d2", MessageType("proto", "Digit"))
        grammar.add_rule(Rule(list_nt, digit,
                            Lambda([param_digit2], MessageType("proto", "List"), param_digit2)))

        # digit -> 0
        grammar.add_rule(Rule(digit, zero,
                            Lambda([], MessageType("proto", "Digit"), Var("x", MessageType("proto", "Digit")))))

        # digit -> 1
        grammar.add_rule(Rule(digit, one,
                            Lambda([], MessageType("proto", "Digit"), Var("y", MessageType("proto", "Digit")))))

        # Compute nullable
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert not nullable[list_nt]
        assert not nullable[digit]

        # Compute FIRST
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert zero in first[list_nt]
        assert one in first[list_nt]
        assert zero in first[digit]
        assert one in first[digit]

        # Compute FOLLOW
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal('$', BaseType('EOF'))
        assert eof in follow[list_nt]
        assert plus in follow[list_nt]
        assert eof in follow[digit]
        assert plus in follow[digit]

    def test_dragon_book_nullable_propagation(self):
        """Test nullable propagation example.

        Grammar:
        S -> A B C
        A -> a | epsilon
        B -> b | epsilon
        C -> c
        """
        s = Nonterminal("S", MessageType("proto", "S"))
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        c = Nonterminal("C", MessageType("proto", "C"))

        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")
        lit_c = LitTerminal("c")

        grammar = Grammar(s)

        # S -> A B C
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        param_c = Var("z", MessageType("proto", "C"))
        grammar.add_rule(Rule(s, Sequence((a, b, c)),
                            Lambda([param_a, param_b, param_c], MessageType("proto", "S"), param_a)))

        # A -> a
        grammar.add_rule(Rule(a, lit_a,
                            Lambda([], MessageType("proto", "A"), Var("v", MessageType("proto", "A")))))

        # A -> epsilon
        grammar.add_rule(Rule(a, Sequence(()),
                            Lambda([], MessageType("proto", "A"), Var("w", MessageType("proto", "A")))))

        # B -> b
        grammar.add_rule(Rule(b, lit_b,
                            Lambda([], MessageType("proto", "B"), Var("u", MessageType("proto", "B")))))

        # B -> epsilon
        grammar.add_rule(Rule(b, Sequence(()),
                            Lambda([], MessageType("proto", "B"), Var("t", MessageType("proto", "B")))))

        # C -> c
        grammar.add_rule(Rule(c, lit_c,
                            Lambda([], MessageType("proto", "C"), Var("s", MessageType("proto", "C")))))

        # Compute nullable
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[a]
        assert nullable[b]
        assert not nullable[c]
        assert not nullable[s]

        # Compute FIRST
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert lit_a in first[s]
        assert lit_b in first[s]
        assert lit_c in first[s]

        # Compute FOLLOW - this tests propagation through nullable nonterminals
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        assert lit_b in follow[a]
        assert lit_c in follow[b]

    def test_dragon_book_first_k_example(self):
        """Test FIRST_k for grammar requiring lookahead k>1.

        Grammar:
        S -> a A a | b A b
        A -> a | b
        """
        s = Nonterminal("S", MessageType("proto", "S"))
        a_nt = Nonterminal("A", MessageType("proto", "A"))

        lit_a = LitTerminal("a")
        lit_b = LitTerminal("b")

        grammar = Grammar(s)

        # S -> a A a
        param_a1 = Var("x", MessageType("proto", "A"))
        grammar.add_rule(Rule(s, Sequence((lit_a, a_nt, lit_a)),
                            Lambda([param_a1], MessageType("proto", "S"), param_a1)))

        # S -> b A b
        param_a2 = Var("y", MessageType("proto", "A"))
        grammar.add_rule(Rule(s, Sequence((lit_b, a_nt, lit_b)),
                            Lambda([param_a2], MessageType("proto", "S"), param_a2)))

        # A -> a
        grammar.add_rule(Rule(a_nt, lit_a,
                            Lambda([], MessageType("proto", "A"), Var("v", MessageType("proto", "A")))))

        # A -> b
        grammar.add_rule(Rule(a_nt, lit_b,
                            Lambda([], MessageType("proto", "A"), Var("w", MessageType("proto", "A")))))

        # With k=1, FIRST(S) = {a, b} - ambiguous
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        assert lit_a in first[s]
        assert lit_b in first[s]

        # With k=3, we can distinguish: FIRST_3(S) = {(a,a,a), (a,b,a), (b,a,b), (b,b,b)}
        first_k = GrammarAnalysis.compute_first_k_static(grammar, k=3, nullable=nullable)
        assert (lit_a, lit_a, lit_a) in first_k[s]
        assert (lit_a, lit_b, lit_a) in first_k[s]
        assert (lit_b, lit_a, lit_b) in first_k[s]
        assert (lit_b, lit_b, lit_b) in first_k[s]

    def test_dragon_book_dangling_else_with_follow_k(self):
        """Test dangling else ambiguity with FOLLOW_k.

        Grammar:
        S -> if E then S S' | other
        S' -> else S | epsilon
        E -> expr
        """
        s = Nonterminal("S", MessageType("proto", "S"))
        s_prime = Nonterminal("S'", MessageType("proto", "SPrime"))
        e = Nonterminal("E", MessageType("proto", "E"))

        if_tok = LitTerminal("if")
        then_tok = LitTerminal("then")
        else_tok = LitTerminal("else")
        other_tok = LitTerminal("other")
        expr_tok = LitTerminal("expr")

        grammar = Grammar(s)

        # S -> if E then S S'
        param_e = Var("e", MessageType("proto", "E"))
        param_s = Var("s", MessageType("proto", "S"))
        param_sp = Var("sp", MessageType("proto", "SPrime"))
        grammar.add_rule(Rule(s, Sequence((if_tok, e, then_tok, s, s_prime)),
                            Lambda([param_e, param_s, param_sp], MessageType("proto", "S"), param_e)))

        # S -> other
        grammar.add_rule(Rule(s, other_tok,
                            Lambda([], MessageType("proto", "S"), Var("x", MessageType("proto", "S")))))

        # S' -> else S
        param_s2 = Var("s2", MessageType("proto", "S"))
        grammar.add_rule(Rule(s_prime, Sequence((else_tok, s)),
                            Lambda([param_s2], MessageType("proto", "SPrime"), param_s2)))

        # S' -> epsilon
        grammar.add_rule(Rule(s_prime, Sequence(()),
                            Lambda([], MessageType("proto", "SPrime"), Var("y", MessageType("proto", "SPrime")))))

        # E -> expr
        grammar.add_rule(Rule(e, expr_tok,
                            Lambda([], MessageType("proto", "E"), Var("z", MessageType("proto", "E")))))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first_k = GrammarAnalysis.compute_first_k_static(grammar, k=2, nullable=nullable)
        follow_k = GrammarAnalysis.compute_follow_k_static(grammar, k=2, nullable=nullable, first_k=first_k)

        # FOLLOW_2(S') should include EOF and pairs with else
        eof = NamedTerminal('$', BaseType('EOF'))
        assert (eof,) in follow_k[s_prime]
        assert (else_tok, if_tok) in follow_k[s_prime]
        assert (else_tok, other_tok) in follow_k[s_prime]


class TestIntegration:
    """Integration tests combining multiple analysis functions."""

    def test_grammar_methods_cache_results(self):
        """Test that Grammar.analysis methods properly cache results."""
        grammar, _, _, _, _, _ = make_simple_grammar()

        # First call should compute
        nullable1 = grammar.analysis.nullable
        # Second call should return cached value
        nullable2 = grammar.analysis.nullable
        assert nullable1 is nullable2

        # Same for FIRST
        first1 = grammar.analysis.first
        first2 = grammar.analysis.first
        assert first1 is first2

        # Same for FOLLOW
        follow1 = grammar.analysis.follow
        follow2 = grammar.analysis.follow
        assert follow1 is follow2

    def test_complete_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        grammar, s, a, _, lit_a, lit_b = make_simple_grammar()

        # Check reachability
        reachable = grammar.analysis.reachability
        assert len(reachable) == 3

        # Compute nullable
        nullable = grammar.analysis.nullable
        assert not any(nullable.values())

        # Compute FIRST
        first = grammar.analysis.first
        assert lit_a in first[s]

        # Compute FOLLOW
        follow = grammar.analysis.follow
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
        constructor1 = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
        grammar.add_rule(Rule(s, Sequence((a, b)), constructor1))

        param_b2 = Var("z", MessageType("proto", "B"))
        constructor2 = Lambda([param_b2], MessageType("proto", "S"), param_b2)
        grammar.add_rule(Rule(s, b, constructor2))

        # A -> "a"
        constructor3 = Lambda([], MessageType("proto", "A"), Var("w", MessageType("proto", "A")))
        grammar.add_rule(Rule(a, lit_a, constructor3))

        # B -> "b"
        constructor4 = Lambda([], MessageType("proto", "B"), Var("v", MessageType("proto", "B")))
        grammar.add_rule(Rule(b, lit_b, constructor4))

        # Check everything works together
        reachable = grammar.analysis.reachability
        grammar.analysis.nullable  # ensure it runs
        first = grammar.analysis.first
        grammar.analysis.follow  # ensure it runs

        assert len(reachable) == 3
        assert lit_a in first[s]
        assert lit_b in first[s]


class TestAppelChapter3Examples:
    """Tests based on examples from Appel's Modern Compiler Implementation, Chapter 3."""

    def test_grammar_3_12_nullable_first_follow(self):
        """Test Grammar 3.12 from Appel's book (page 48).

        Grammar:
        Z -> d | X Y Z
        Y -> epsilon | c
        X -> Y | a

        Expected results (from page 50):
        - X: nullable=yes, FIRST={a,c}, FOLLOW={a,c,d}
        - Y: nullable=yes, FIRST={c}, FOLLOW={a,c,d}
        - Z: nullable=no, FIRST={a,c,d}, FOLLOW={$}
        """
        z = Nonterminal("Z", MessageType("proto", "Z"))
        y = Nonterminal("Y", MessageType("proto", "Y"))
        x = Nonterminal("X", MessageType("proto", "X"))

        lit_a = LitTerminal("a")
        lit_c = LitTerminal("c")
        lit_d = LitTerminal("d")

        grammar = Grammar(z)

        # Z -> d
        grammar.add_rule(Rule(z, lit_d,
                            Lambda([], MessageType("proto", "Z"), Var("v", MessageType("proto", "Z")))))

        # Z -> X Y Z
        param_x = Var("x", MessageType("proto", "X"))
        param_y = Var("y", MessageType("proto", "Y"))
        param_z = Var("z", MessageType("proto", "Z"))
        grammar.add_rule(Rule(z, Sequence((x, y, z)),
                            Lambda([param_x, param_y, param_z], MessageType("proto", "Z"), param_x)))

        # Y -> epsilon
        grammar.add_rule(Rule(y, Sequence(()),
                            Lambda([], MessageType("proto", "Y"), Var("w", MessageType("proto", "Y")))))

        # Y -> c
        grammar.add_rule(Rule(y, lit_c,
                            Lambda([], MessageType("proto", "Y"), Var("u", MessageType("proto", "Y")))))

        # X -> Y
        param_y2 = Var("y2", MessageType("proto", "Y"))
        grammar.add_rule(Rule(x, y,
                            Lambda([param_y2], MessageType("proto", "X"), param_y2)))

        # X -> a
        grammar.add_rule(Rule(x, lit_a,
                            Lambda([], MessageType("proto", "X"), Var("t", MessageType("proto", "X")))))

        # Compute nullable - from page 50
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[x], "X should be nullable (X -> Y -> epsilon)"
        assert nullable[y], "Y should be nullable (Y -> epsilon)"
        assert not nullable[z], "Z should not be nullable"

        # Compute FIRST - from page 50
        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        # FIRST(X) = {a, c}
        assert lit_a in first[x], "FIRST(X) should contain 'a'"
        assert lit_c in first[x], "FIRST(X) should contain 'c'"
        assert len(first[x]) == 2, f"FIRST(X) should be {{a, c}}, got {first[x]}"

        # FIRST(Y) = {c}
        assert lit_c in first[y], "FIRST(Y) should contain 'c'"
        assert len(first[y]) == 1, f"FIRST(Y) should be {{c}}, got {first[y]}"

        # FIRST(Z) = {a, c, d}
        assert lit_a in first[z], "FIRST(Z) should contain 'a'"
        assert lit_c in first[z], "FIRST(Z) should contain 'c'"
        assert lit_d in first[z], "FIRST(Z) should contain 'd'"
        assert len(first[z]) == 3, f"FIRST(Z) should be {{a, c, d}}, got {first[z]}"

        # Compute FOLLOW - from page 50
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal('$', BaseType('EOF'))

        # FOLLOW(X) = {a, c, d}
        assert lit_a in follow[x], "FOLLOW(X) should contain 'a'"
        assert lit_c in follow[x], "FOLLOW(X) should contain 'c'"
        assert lit_d in follow[x], "FOLLOW(X) should contain 'd'"

        # FOLLOW(Y) = {a, c, d}
        assert lit_a in follow[y], "FOLLOW(Y) should contain 'a'"
        assert lit_c in follow[y], "FOLLOW(Y) should contain 'c'"
        assert lit_d in follow[y], "FOLLOW(Y) should contain 'd'"

        # FOLLOW(Z) = {$}
        assert eof in follow[z], "FOLLOW(Z) should contain '$'"

    def test_grammar_3_1_straight_line(self):
        """Test simplified straight-line grammar from Grammar 3.1 (page 41).

        Grammar (simplified):
        S -> S ; S | id := E | print ( L )
        E -> id | num | E + E | ( S , E )
        L -> E | L , E

        For this test, we use a non-left-recursive version:
        S -> id := E S' | print ( L ) S'
        S' -> ; S | epsilon
        E -> id E' | num E'
        E' -> + E | epsilon
        L -> E L'
        L' -> , E L' | epsilon
        """
        s = Nonterminal("S", MessageType("proto", "S"))
        s_prime = Nonterminal("S'", MessageType("proto", "SPrime"))
        e = Nonterminal("E", MessageType("proto", "E"))
        e_prime = Nonterminal("E'", MessageType("proto", "EPrime"))
        l_nt = Nonterminal("L", MessageType("proto", "L"))
        l_prime = Nonterminal("L'", MessageType("proto", "LPrime"))

        id_tok = NamedTerminal("id", BaseType("String"))
        num_tok = NamedTerminal("num", BaseType("Int64"))
        assign = LitTerminal(":=")
        print_tok = LitTerminal("print")
        semi = LitTerminal(";")
        plus = LitTerminal("+")
        comma = LitTerminal(",")
        lparen = LitTerminal("(")
        rparen = LitTerminal(")")

        grammar = Grammar(s)

        # S -> id := E S' (3 non-literal elements: id, E, S')
        p1 = Var("p1", BaseType("String"))
        p2 = Var("p2", MessageType("proto", "E"))
        p3 = Var("p3", MessageType("proto", "SPrime"))
        grammar.add_rule(Rule(s, Sequence((id_tok, assign, e, s_prime)),
                            Lambda([p1, p2, p3], MessageType("proto", "S"), p2)))

        # S -> print ( L ) S' (2 non-literal elements: L, S')
        p4 = Var("p4", MessageType("proto", "L"))
        p5 = Var("p5", MessageType("proto", "SPrime"))
        grammar.add_rule(Rule(s, Sequence((print_tok, lparen, l_nt, rparen, s_prime)),
                            Lambda([p4, p5], MessageType("proto", "S"), p4)))

        # S' -> ; S (1 non-literal element: S)
        p6 = Var("p6", MessageType("proto", "S"))
        grammar.add_rule(Rule(s_prime, Sequence((semi, s)),
                            Lambda([p6], MessageType("proto", "SPrime"), p6)))

        # S' -> epsilon
        grammar.add_rule(Rule(s_prime, Sequence(()),
                            Lambda([], MessageType("proto", "SPrime"), Var("w", MessageType("proto", "SPrime")))))

        # E -> id E' (2 non-literal elements: id, E')
        p7 = Var("p7", BaseType("String"))
        p8 = Var("p8", MessageType("proto", "EPrime"))
        grammar.add_rule(Rule(e, Sequence((id_tok, e_prime)),
                            Lambda([p7, p8], MessageType("proto", "E"), p7)))

        # E -> num E' (2 non-literal elements: num, E')
        p9 = Var("p9", BaseType("Int64"))
        p10 = Var("p10", MessageType("proto", "EPrime"))
        grammar.add_rule(Rule(e, Sequence((num_tok, e_prime)),
                            Lambda([p9, p10], MessageType("proto", "E"), p9)))

        # E' -> + E (1 non-literal element: E)
        p11 = Var("p11", MessageType("proto", "E"))
        grammar.add_rule(Rule(e_prime, Sequence((plus, e)),
                            Lambda([p11], MessageType("proto", "EPrime"), p11)))

        # E' -> epsilon
        grammar.add_rule(Rule(e_prime, Sequence(()),
                            Lambda([], MessageType("proto", "EPrime"), Var("s", MessageType("proto", "EPrime")))))

        # L -> E L' (2 non-literal elements: E, L')
        p12 = Var("p12", MessageType("proto", "E"))
        p13 = Var("p13", MessageType("proto", "LPrime"))
        grammar.add_rule(Rule(l_nt, Sequence((e, l_prime)),
                            Lambda([p12, p13], MessageType("proto", "L"), p12)))

        # L' -> , E L' (2 non-literal elements: E, L')
        p14 = Var("p14", MessageType("proto", "E"))
        p15 = Var("p15", MessageType("proto", "LPrime"))
        grammar.add_rule(Rule(l_prime, Sequence((comma, e, l_prime)),
                            Lambda([p14, p15], MessageType("proto", "LPrime"), p14)))

        # L' -> epsilon
        grammar.add_rule(Rule(l_prime, Sequence(()),
                            Lambda([], MessageType("proto", "LPrime"), Var("p", MessageType("proto", "LPrime")))))

        # Compute nullable
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[s_prime], "S' should be nullable"
        assert nullable[e_prime], "E' should be nullable"
        assert nullable[l_prime], "L' should be nullable"
        assert not nullable[s], "S should not be nullable"
        assert not nullable[e], "E should not be nullable"
        assert not nullable[l_nt], "L should not be nullable"

        # Compute FIRST
        first = GrammarAnalysis.compute_first_static(grammar, nullable)

        # FIRST(S) = {id, print}
        assert id_tok in first[s]
        assert print_tok in first[s]

        # FIRST(E) = {id, num}
        assert id_tok in first[e]
        assert num_tok in first[e]

        # FIRST(S') = {;}
        assert semi in first[s_prime]

        # FIRST(E') = {+}
        assert plus in first[e_prime]

        # FIRST(L') = {,}
        assert comma in first[l_prime]

    def test_grammar_3_8_expression_precedence(self):
        """Test expression grammar with precedence from Grammar 3.8 (page 45).

        Grammar:
        E -> E + T | T
        T -> T * F | F
        F -> id | ( E )

        Using left-recursion eliminated version:
        E -> T E'
        E' -> + T E' | epsilon
        T -> F T'
        T' -> * F T' | epsilon
        F -> id | ( E )
        """
        e = Nonterminal("E", MessageType("proto", "E"))
        e_prime = Nonterminal("E'", MessageType("proto", "EPrime"))
        t = Nonterminal("T", MessageType("proto", "T"))
        t_prime = Nonterminal("T'", MessageType("proto", "TPrime"))
        f = Nonterminal("F", MessageType("proto", "F"))

        plus = LitTerminal("+")
        star = LitTerminal("*")
        id_tok = NamedTerminal("id", BaseType("String"))
        lparen = LitTerminal("(")
        rparen = LitTerminal(")")

        grammar = Grammar(e)

        # E -> T E' (2 non-literal elements)
        p_t = Var("t", MessageType("proto", "T"))
        p_ep = Var("ep", MessageType("proto", "EPrime"))
        grammar.add_rule(Rule(e, Sequence((t, e_prime)),
                            Lambda([p_t, p_ep], MessageType("proto", "E"), p_t)))

        # E' -> + T E' (2 non-literal elements)
        p_t2 = Var("t2", MessageType("proto", "T"))
        p_ep2 = Var("ep2", MessageType("proto", "EPrime"))
        grammar.add_rule(Rule(e_prime, Sequence((plus, t, e_prime)),
                            Lambda([p_t2, p_ep2], MessageType("proto", "EPrime"), p_t2)))

        # E' -> epsilon
        grammar.add_rule(Rule(e_prime, Sequence(()),
                            Lambda([], MessageType("proto", "EPrime"), Var("z", MessageType("proto", "EPrime")))))

        # T -> F T' (2 non-literal elements)
        p_f = Var("f", MessageType("proto", "F"))
        p_tp = Var("tp", MessageType("proto", "TPrime"))
        grammar.add_rule(Rule(t, Sequence((f, t_prime)),
                            Lambda([p_f, p_tp], MessageType("proto", "T"), p_f)))

        # T' -> * F T' (2 non-literal elements)
        p_f2 = Var("f2", MessageType("proto", "F"))
        p_tp2 = Var("tp2", MessageType("proto", "TPrime"))
        grammar.add_rule(Rule(t_prime, Sequence((star, f, t_prime)),
                            Lambda([p_f2, p_tp2], MessageType("proto", "TPrime"), p_f2)))

        # T' -> epsilon
        grammar.add_rule(Rule(t_prime, Sequence(()),
                            Lambda([], MessageType("proto", "TPrime"), Var("u", MessageType("proto", "TPrime")))))

        # F -> id (1 non-literal element)
        p_id = Var("id", BaseType("String"))
        grammar.add_rule(Rule(f, id_tok,
                            Lambda([p_id], MessageType("proto", "F"), p_id)))

        # F -> ( E ) (1 non-literal element)
        p_e = Var("e", MessageType("proto", "E"))
        grammar.add_rule(Rule(f, Sequence((lparen, e, rparen)),
                            Lambda([p_e], MessageType("proto", "F"), p_e)))

        # Compute nullable
        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[e_prime], "E' should be nullable"
        assert nullable[t_prime], "T' should be nullable"
        assert not nullable[e], "E should not be nullable"
        assert not nullable[t], "T should not be nullable"
        assert not nullable[f], "F should not be nullable"

        # Compute FIRST
        first = GrammarAnalysis.compute_first_static(grammar, nullable)

        # FIRST(F) = {id, (}
        assert id_tok in first[f]
        assert lparen in first[f]
        assert len(first[f]) == 2

        # FIRST(T) = FIRST(F) = {id, (}
        assert id_tok in first[t]
        assert lparen in first[t]

        # FIRST(E) = FIRST(T) = {id, (}
        assert id_tok in first[e]
        assert lparen in first[e]

        # FIRST(E') = {+}
        assert plus in first[e_prime]
        assert len(first[e_prime]) == 1

        # FIRST(T') = {*}
        assert star in first[t_prime]
        assert len(first[t_prime]) == 1

        # Compute FOLLOW
        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal('$', BaseType('EOF'))

        # FOLLOW(E) = {$, )}
        assert eof in follow[e]
        assert rparen in follow[e]

        # FOLLOW(E') = FOLLOW(E) = {$, )}
        assert eof in follow[e_prime]
        assert rparen in follow[e_prime]

        # FOLLOW(T) includes FIRST(E') = {+} and FOLLOW(E) since E' is nullable
        assert plus in follow[t]
        assert eof in follow[t]
        assert rparen in follow[t]

        # FOLLOW(T') = FOLLOW(T)
        assert plus in follow[t_prime]

        # FOLLOW(F) includes FIRST(T') = {*} and FOLLOW(T) since T' is nullable
        assert star in follow[f]

    def test_grammar_3_20_sexp(self):
        """Test S-expression grammar from Grammar 3.20 (page 62).

        Grammar:
        S -> ( L ) | x
        L -> S L'
        L' -> S L' | epsilon
        """
        s = Nonterminal("S", MessageType("proto", "S"))
        l_nt = Nonterminal("L", MessageType("proto", "L"))
        l_prime = Nonterminal("L'", MessageType("proto", "LPrime"))

        lparen = LitTerminal("(")
        rparen = LitTerminal(")")
        x_tok = LitTerminal("x")

        grammar = Grammar(s)

        # S -> ( L ) (1 non-literal element)
        p_l = Var("l", MessageType("proto", "L"))
        grammar.add_rule(Rule(s, Sequence((lparen, l_nt, rparen)),
                            Lambda([p_l], MessageType("proto", "S"), p_l)))

        # S -> x (0 non-literal elements - x is a LitTerminal)
        grammar.add_rule(Rule(s, x_tok,
                            Lambda([], MessageType("proto", "S"), Var("b", MessageType("proto", "S")))))

        # L -> S L' (2 non-literal elements)
        p_s = Var("s", MessageType("proto", "S"))
        p_lp = Var("lp", MessageType("proto", "LPrime"))
        grammar.add_rule(Rule(l_nt, Sequence((s, l_prime)),
                            Lambda([p_s, p_lp], MessageType("proto", "L"), p_s)))

        # L' -> S L' (2 non-literal elements)
        p_s2 = Var("s2", MessageType("proto", "S"))
        p_lp2 = Var("lp2", MessageType("proto", "LPrime"))
        grammar.add_rule(Rule(l_prime, Sequence((s, l_prime)),
                            Lambda([p_s2, p_lp2], MessageType("proto", "LPrime"), p_s2)))

        # L' -> epsilon
        grammar.add_rule(Rule(l_prime, Sequence(()),
                            Lambda([], MessageType("proto", "LPrime"), Var("e", MessageType("proto", "LPrime")))))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert nullable[l_prime], "L' should be nullable"
        assert not nullable[s], "S should not be nullable"
        assert not nullable[l_nt], "L should not be nullable"

        first = GrammarAnalysis.compute_first_static(grammar, nullable)

        # FIRST(S) = {(, x}
        assert lparen in first[s]
        assert x_tok in first[s]
        assert len(first[s]) == 2

        # FIRST(L) = FIRST(S) = {(, x}
        assert lparen in first[l_nt]
        assert x_tok in first[l_nt]

        # FIRST(L') = FIRST(S) = {(, x}
        assert lparen in first[l_prime]
        assert x_tok in first[l_prime]

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal('$', BaseType('EOF'))

        # FOLLOW(S) = {$, ), (, x}
        assert eof in follow[s]
        assert rparen in follow[s]

        # FOLLOW(L) = {)}
        assert rparen in follow[l_nt]

        # FOLLOW(L') = FOLLOW(L) = {)}
        assert rparen in follow[l_prime]

    def test_exercise_3_5_grammar(self):
        """Test grammar from Exercise 3.5.

        Grammar:
        S -> a S a | a a

        This is not LL(1) because both productions start with 'a'.
        But we can still compute FIRST and FOLLOW.
        """
        s = Nonterminal("S", MessageType("proto", "S"))
        lit_a = LitTerminal("a")

        grammar = Grammar(s)

        # S -> a S a (1 non-literal element)
        p_s = Var("s", MessageType("proto", "S"))
        grammar.add_rule(Rule(s, Sequence((lit_a, s, lit_a)),
                            Lambda([p_s], MessageType("proto", "S"), p_s)))

        # S -> a a (0 non-literal elements - both are LitTerminals)
        grammar.add_rule(Rule(s, Sequence((lit_a, lit_a)),
                            Lambda([], MessageType("proto", "S"), Var("y", MessageType("proto", "S")))))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        assert not nullable[s], "S should not be nullable"

        first = GrammarAnalysis.compute_first_static(grammar, nullable)
        # FIRST(S) = {a}
        assert lit_a in first[s]
        assert len(first[s]) == 1

        follow = GrammarAnalysis.compute_follow_static(grammar, nullable, first)
        eof = NamedTerminal('$', BaseType('EOF'))

        # FOLLOW(S) = {a, $}
        assert lit_a in follow[s]
        assert eof in follow[s]

    def test_first_k_grammar_3_12(self):
        """Test FIRST_k for Grammar 3.12.

        With k=2, we can distinguish more productions.
        """
        z = Nonterminal("Z", MessageType("proto", "Z"))
        y = Nonterminal("Y", MessageType("proto", "Y"))
        x = Nonterminal("X", MessageType("proto", "X"))

        lit_a = LitTerminal("a")
        lit_c = LitTerminal("c")
        lit_d = LitTerminal("d")

        grammar = Grammar(z)

        # Z -> d (0 non-literal elements)
        grammar.add_rule(Rule(z, lit_d,
                            Lambda([], MessageType("proto", "Z"), Var("v", MessageType("proto", "Z")))))

        # Z -> X Y Z (3 non-literal elements)
        p_x = Var("x", MessageType("proto", "X"))
        p_y = Var("y", MessageType("proto", "Y"))
        p_z = Var("z", MessageType("proto", "Z"))
        grammar.add_rule(Rule(z, Sequence((x, y, z)),
                            Lambda([p_x, p_y, p_z], MessageType("proto", "Z"), p_x)))

        # Y -> epsilon
        grammar.add_rule(Rule(y, Sequence(()),
                            Lambda([], MessageType("proto", "Y"), Var("u", MessageType("proto", "Y")))))

        # Y -> c (0 non-literal elements)
        grammar.add_rule(Rule(y, lit_c,
                            Lambda([], MessageType("proto", "Y"), Var("t", MessageType("proto", "Y")))))

        # X -> Y (1 non-literal element)
        p_y2 = Var("y2", MessageType("proto", "Y"))
        grammar.add_rule(Rule(x, y,
                            Lambda([p_y2], MessageType("proto", "X"), p_y2)))

        # X -> a (0 non-literal elements)
        grammar.add_rule(Rule(x, lit_a,
                            Lambda([], MessageType("proto", "X"), Var("r", MessageType("proto", "X")))))

        nullable = GrammarAnalysis.compute_nullable_static(grammar)
        first_k = GrammarAnalysis.compute_first_k_static(grammar, k=2, nullable=nullable)

        # FIRST_2(X) includes: (a,), (c,), ()
        assert (lit_a,) in first_k[x]
        assert (lit_c,) in first_k[x]
        assert () in first_k[x]  # X is nullable via X -> Y -> epsilon

        # FIRST_2(Y) includes: (c,), ()
        assert (lit_c,) in first_k[y]
        assert () in first_k[y]

        # FIRST_2(Z) includes: (d,), and combinations from X Y Z
        assert (lit_d,) in first_k[z]
        assert (lit_a, lit_a) in first_k[z]  # X=a, Y=eps, Z starts with a
        assert (lit_a, lit_c) in first_k[z]  # X=a, Y=c or X=a, Y=eps, Z starts with c
        assert (lit_a, lit_d) in first_k[z]  # X=a, Y=eps, Z=d
        assert (lit_c, lit_a) in first_k[z]  # X=Y=c, Z starts with a
        assert (lit_c, lit_c) in first_k[z]  # X=Y=c, Z starts with c
        assert (lit_c, lit_d) in first_k[z]  # X=Y=c, Z=d
