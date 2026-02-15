#!/usr/bin/env python3
"""Tests for terminal_sequence_set module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    LitTerminal, NamedTerminal, Nonterminal, Sequence, Rule, Grammar,
)
from meta.target import BaseType, MessageType, Lambda, Var
from meta.terminal_sequence_set import (
    TerminalSequenceSet, FollowSet, FirstSet, ConcatSet,
)


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

    param_a = Var("x", MessageType("proto", "A"))
    param_b = Var("y", MessageType("proto", "B"))
    construct_action_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, Sequence((a, b)), construct_action_s))

    construct_action_a = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, lit_a, construct_action_a))

    construct_action_b = Lambda([], MessageType("proto", "B"), Var("y", MessageType("proto", "B")))
    grammar.add_rule(Rule(b, lit_b, construct_action_b))

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

    param_a = Var("x", MessageType("proto", "A"))
    param_b = Var("y", MessageType("proto", "B"))
    construct_action_s = Lambda([param_a, param_b], MessageType("proto", "S"), param_a)
    grammar.add_rule(Rule(s, Sequence((a, b)), construct_action_s))

    construct_action_a1 = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, lit_a, construct_action_a1))

    construct_action_a2 = Lambda([], MessageType("proto", "A"), Var("x", MessageType("proto", "A")))
    grammar.add_rule(Rule(a, Sequence(()), construct_action_a2))

    construct_action_b = Lambda([], MessageType("proto", "B"), Var("y", MessageType("proto", "B")))
    grammar.add_rule(Rule(b, lit_b, construct_action_b))

    return grammar, s, a, b, lit_a, lit_b


class LiteralTerminalSequenceSet(TerminalSequenceSet):
    """A TerminalSequenceSet backed by a literal set of sequences."""

    def __init__(self, sequences):
        self.sequences = sequences
        self.call_counts = {}

    def get(self, k):
        self.call_counts[k] = self.call_counts.get(k, 0) + 1
        return {seq[:k] for seq in self.sequences}


class TestFollowSet:
    """Tests for FollowSet."""

    def test_follow_set_computes_follow_k(self):
        """Test that FollowSet delegates to grammar.analysis.follow_k_of."""
        grammar, _, a, _, _, lit_b = make_simple_grammar()

        follow_a = FollowSet(grammar, a)
        result = follow_a.get(1)

        assert result == {(lit_b,)}

    def test_follow_set_caches_results(self):
        """Test that FollowSet caches computed results."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        follow_a = FollowSet(grammar, a)

        result1 = follow_a.get(1)
        result2 = follow_a.get(1)

        assert result1 is result2
        assert 1 in follow_a._cache

    def test_follow_set_different_k_values(self):
        """Test FollowSet with different k values."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        follow_a = FollowSet(grammar, a)

        result_k1 = follow_a.get(1)
        result_k2 = follow_a.get(2)

        assert 1 in follow_a._cache
        assert 2 in follow_a._cache
        assert result_k1 == {(lit_b,)}
        assert result_k2 == {(lit_b,)}

    def test_follow_set_start_symbol(self):
        """Test FollowSet for start symbol returns EOF marker."""
        grammar, s, _, _, _, _ = make_simple_grammar()

        follow_s = FollowSet(grammar, s)
        result = follow_s.get(1)

        eof = NamedTerminal('$', BaseType('EOF'))
        assert result == {(eof,)}


class TestFirstSet:
    """Tests for FirstSet."""

    def test_first_set_computes_first_k(self):
        """Test that FirstSet delegates to grammar.analysis.first_k_of."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first_a = FirstSet(grammar, lit_a)
        result = first_a.get(1)

        assert result == {(lit_a,)}

    def test_first_set_caches_results(self):
        """Test that FirstSet caches computed results."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first_a = FirstSet(grammar, a)

        result1 = first_a.get(1)
        result2 = first_a.get(1)

        assert result1 is result2
        assert 1 in first_a._cache

    def test_first_set_sequence(self):
        """Test FirstSet for a sequence."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        seq = Sequence((a, b))
        first_seq = FirstSet(grammar, seq)
        result = first_seq.get(2)

        assert result == {(lit_a, lit_b)}

    def test_first_set_nullable(self):
        """Test FirstSet for nullable nonterminal."""
        grammar, s, a, b, lit_a, lit_b = make_nullable_grammar()

        first_a = FirstSet(grammar, a)
        result = first_a.get(1)

        assert (lit_a,) in result
        assert () in result


class TestConcatSet:
    """Tests for ConcatSet."""

    def test_concat_basic(self):
        """Test basic concatenation of two sets."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first = LiteralTerminalSequenceSet({(lit_a,)})
        second = LiteralTerminalSequenceSet({(lit_b,)})
        concat = ConcatSet(first, second)

        result = concat.get(2)

        assert result == {(lit_a, lit_b)}

    def test_concat_caches_results(self):
        """Test that ConcatSet caches computed results."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first = LiteralTerminalSequenceSet({(lit_a,)})
        second = LiteralTerminalSequenceSet({(lit_b,)})
        concat = ConcatSet(first, second)

        result1 = concat.get(2)
        result2 = concat.get(2)

        assert result1 is result2
        assert 2 in concat._cache

    def test_concat_optimization_full_length(self):
        """Test optimization: second set not fetched when first is full length."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first = LiteralTerminalSequenceSet({(lit_a, lit_b)})
        second = LiteralTerminalSequenceSet({(lit_a,)})
        concat = ConcatSet(first, second)

        result = concat.get(2)

        assert result == {(lit_a, lit_b)}
        assert 2 in first.call_counts
        assert second.call_counts == {}

    def test_concat_empty_first(self):
        """Test concatenation when first set is empty."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first = LiteralTerminalSequenceSet(set())
        second = LiteralTerminalSequenceSet({(lit_b,)})
        concat = ConcatSet(first, second)

        result = concat.get(1)

        assert result == {(lit_b,)}

    def test_concat_with_short_sequences(self):
        """Test concatenation handles short sequences from nullable elements."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first = LiteralTerminalSequenceSet({(), (lit_a,)})
        second = LiteralTerminalSequenceSet({(lit_b,)})
        concat = ConcatSet(first, second)

        result = concat.get(2)

        assert (lit_a, lit_b) in result
        assert (lit_b,) in result

    def test_concat_truncates_to_k(self):
        """Test that concatenation truncates results to k."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first = LiteralTerminalSequenceSet({(lit_a, lit_a)})
        second = LiteralTerminalSequenceSet({(lit_b, lit_b)})
        concat = ConcatSet(first, second)

        result = concat.get(3)

        assert all(len(seq) <= 3 for seq in result)
        assert (lit_a, lit_a, lit_b) in result

    def test_concat_different_k_values(self):
        """Test ConcatSet with different k values."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first = LiteralTerminalSequenceSet({(lit_a,)})
        second = LiteralTerminalSequenceSet({(lit_b,)})
        concat = ConcatSet(first, second)

        result_k1 = concat.get(1)
        result_k2 = concat.get(2)

        assert 1 in concat._cache
        assert 2 in concat._cache
        assert result_k1 == {(lit_a,)}
        assert result_k2 == {(lit_a, lit_b)}


class TestIntegration:
    """Integration tests using real grammar analysis."""

    def test_follow_first_concat(self):
        """Test combining FollowSet, FirstSet, and ConcatSet."""
        grammar, s, a, b, lit_a, lit_b = make_simple_grammar()

        first_b = FirstSet(grammar, b)
        follow_s = FollowSet(grammar, s)
        concat = ConcatSet(first_b, follow_s)

        result = concat.get(1)

        assert result == {(lit_b,)}

    def test_nullable_first_concat_follow(self):
        """Test with nullable grammar."""
        grammar, s, a, b, lit_a, lit_b = make_nullable_grammar()

        first_a = FirstSet(grammar, a)
        first_b = FirstSet(grammar, b)
        concat = ConcatSet(first_a, first_b)

        result = concat.get(2)

        assert (lit_a, lit_b) in result
        assert (lit_b,) in result
