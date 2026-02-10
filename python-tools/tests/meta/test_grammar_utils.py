"""Tests for grammar_utils module."""

from meta.grammar import (
    Nonterminal, LitTerminal, NamedTerminal, Sequence, Star, Option, Rule, make_rule,
)
from meta.grammar_utils import collect, get_nonterminals, get_literals, rewrite_rule
from meta.target import MessageType, BaseType, Lambda, Var, OptionType, ListType


class TestCollect:
    """Test collect function."""

    def test_collect_nonterminal_direct(self):
        """Collect nonterminal from direct reference."""
        nt = Nonterminal('Foo', MessageType('test', 'Foo'))
        result = collect(nt, Nonterminal)
        assert result == [nt]

    def test_collect_nonterminal_in_sequence(self):
        """Collect nonterminals from sequence."""
        nt1 = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt2 = Nonterminal('Bar', MessageType('test', 'Bar'))
        seq = Sequence((nt1, nt2))
        result = collect(seq, Nonterminal)
        assert result == [nt1, nt2]

    def test_collect_nonterminal_in_star(self):
        """Collect nonterminal from star."""
        nt = Nonterminal('Foo', MessageType('test', 'Foo'))
        star = Star(nt)
        result = collect(star, Nonterminal)
        assert result == [nt]

    def test_collect_nonterminal_in_option(self):
        """Collect nonterminal from option."""
        nt = Nonterminal('Foo', MessageType('test', 'Foo'))
        opt = Option(nt)
        result = collect(opt, Nonterminal)
        assert result == [nt]

    def test_collect_deduplicates(self):
        """Collect deduplicates repeated elements."""
        nt = Nonterminal('Foo', MessageType('test', 'Foo'))
        seq = Sequence((nt, nt))
        result = collect(seq, Nonterminal)
        assert result == [nt]
        assert len(result) == 1

    def test_collect_preserves_order(self):
        """Collect preserves first-occurrence order."""
        nt1 = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt2 = Nonterminal('Bar', MessageType('test', 'Bar'))
        # nt1 appears twice but should only be in result once at first position
        seq = Sequence((nt1, nt2, nt1))
        result = collect(seq, Nonterminal)
        assert result == [nt1, nt2]

    def test_collect_complex_nesting(self):
        """Collect from complex nested structures."""
        nt1 = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt2 = Nonterminal('Bar', MessageType('test', 'Bar'))
        # Star and Option can contain sequences, but sequences can't contain sequences
        star = Star(nt1)
        seq = Sequence((star, nt2))
        result = collect(seq, Nonterminal)
        assert result == [nt1, nt2]

    def test_collect_terminal_type(self):
        """Collect can target terminal types."""
        lit = LitTerminal('foo')
        term = NamedTerminal('INT', BaseType('Int64'))
        seq = Sequence((lit, term))
        result = collect(seq, LitTerminal)
        assert result == [lit]

    def test_collect_empty_result(self):
        """Collect returns empty list when no matches."""
        lit = LitTerminal('foo')
        result = collect(lit, Nonterminal)
        assert result == []


class TestGetNonterminals:
    """Test get_nonterminals convenience function."""

    def test_get_nonterminals_simple(self):
        """Get nonterminals from simple rhs."""
        nt = Nonterminal('Foo', MessageType('test', 'Foo'))
        result = get_nonterminals(nt)
        assert result == [nt]

    def test_get_nonterminals_sequence(self):
        """Get nonterminals from sequence."""
        nt1 = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt2 = Nonterminal('Bar', MessageType('test', 'Bar'))
        lit = LitTerminal('baz')
        seq = Sequence((nt1, lit, nt2))
        result = get_nonterminals(seq)
        assert result == [nt1, nt2]

    def test_get_nonterminals_from_terminal(self):
        """Get nonterminals from terminal returns empty."""
        lit = LitTerminal('foo')
        result = get_nonterminals(lit)
        assert result == []


class TestGetLiterals:
    """Test get_literals convenience function."""

    def test_get_literals_simple(self):
        """Get literals from simple rhs."""
        lit = LitTerminal('foo')
        result = get_literals(lit)
        assert result == [lit]

    def test_get_literals_sequence(self):
        """Get literals from sequence."""
        lit1 = LitTerminal('foo')
        lit2 = LitTerminal('bar')
        nt = Nonterminal('Baz', MessageType('test', 'Baz'))
        seq = Sequence((lit1, nt, lit2))
        result = get_literals(seq)
        assert result == [lit1, lit2]

    def test_get_literals_from_nonterminal(self):
        """Get literals from nonterminal returns empty."""
        nt = Nonterminal('Foo', MessageType('test', 'Foo'))
        result = get_literals(nt)
        assert result == []


class TestRewriteRhs:
    """Test _rewrite_rhs function (indirectly through rewrite_rule)."""

    def test_rewrite_nonterminal(self):
        """Rewrite replaces nonterminal."""
        nt_old = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt_new = Nonterminal('Bar', MessageType('test', 'Foo'))
        param = Var('x', MessageType('test', 'Foo'))
        rule = make_rule(
            lhs=nt_old,
            rhs=nt_old,
            constructor=Lambda([param], MessageType('test', 'Foo'), param),
            source_type='test.Foo'
        )
        result = rewrite_rule(rule, {nt_old: nt_new})
        assert result.rhs == nt_new

    def test_rewrite_in_sequence(self):
        """Rewrite replaces nonterminal in sequence."""
        nt_old = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt_new = Nonterminal('Bar', MessageType('test', 'Foo'))
        nt_keep = Nonterminal('Keep', MessageType('test', 'Keep'))
        seq = Sequence((nt_old, nt_keep))
        # Constructor needs 2 params since RHS has 2 non-literals
        param1 = Var('x', MessageType('test', 'Foo'))
        param2 = Var('y', MessageType('test', 'Keep'))
        rule = make_rule(
            lhs=Nonterminal('Result', MessageType('test', 'Result')),
            rhs=seq,
            constructor=Lambda([param1, param2], MessageType('test', 'Result'), param1),
            source_type='test.Result'
        )
        result = rewrite_rule(rule, {nt_old: nt_new})
        assert isinstance(result.rhs, Sequence)
        assert result.rhs.elements[0] == nt_new
        assert result.rhs.elements[1] == nt_keep

    def test_rewrite_in_star(self):
        """Rewrite replaces nonterminal in star."""
        nt_old = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt_new = Nonterminal('Bar', MessageType('test', 'Foo'))
        star = Star(nt_old)
        param = Var('x', MessageType('test', 'Foo'))
        rule = make_rule(
            lhs=Nonterminal('Result', MessageType('test', 'Result')),
            rhs=star,
            constructor=Lambda([param], MessageType('test', 'Result'), param),
            source_type='test.Result'
        )
        result = rewrite_rule(rule, {nt_old: nt_new})
        assert isinstance(result.rhs, Star)
        assert result.rhs.rhs == nt_new

    def test_rewrite_in_option(self):
        """Rewrite replaces nonterminal in option."""
        nt_old = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt_new = Nonterminal('Bar', MessageType('test', 'Foo'))
        opt = Option(nt_old)
        param = Var('x', MessageType('test', 'Foo'))
        rule = make_rule(
            lhs=Nonterminal('Result', MessageType('test', 'Result')),
            rhs=opt,
            constructor=Lambda([param], MessageType('test', 'Result'), param),
            source_type='test.Result'
        )
        result = rewrite_rule(rule, {nt_old: nt_new})
        assert isinstance(result.rhs, Option)
        assert result.rhs.rhs == nt_new

    def test_rewrite_no_match_returns_original(self):
        """Rewrite with no matches returns original rule."""
        nt = Nonterminal('Foo', MessageType('test', 'Foo'))
        param = Var('x', MessageType('test', 'Foo'))
        rule = make_rule(
            lhs=nt,
            rhs=nt,
            constructor=Lambda([param], MessageType('test', 'Foo'), param),
            source_type='test.Foo'
        )
        other_nt = Nonterminal('Other', MessageType('test', 'Other'))
        result = rewrite_rule(rule, {other_nt: nt})
        assert result is rule  # Same object

    def test_rewrite_nested_structure(self):
        """Rewrite in deeply nested structure."""
        nt_old = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt_new = Nonterminal('Bar', MessageType('test', 'Foo'))
        nt_keep = Nonterminal('Keep', MessageType('test', 'Keep'))
        # Sequence containing Option containing Star containing target
        inner = Star(nt_old)
        middle = Option(inner)
        outer = Sequence((nt_keep, middle))
        # Constructor needs 2 params - one for Keep, one for Option containing Star
        param1 = Var('x', MessageType('test', 'Keep'))
        param2 = Var('y', OptionType(ListType(MessageType('test', 'Foo'))))
        rule = make_rule(
            lhs=Nonterminal('Result', MessageType('test', 'Result')),
            rhs=outer,
            constructor=Lambda([param1, param2], MessageType('test', 'Result'), param1),
            source_type='test.Result'
        )
        result = rewrite_rule(rule, {nt_old: nt_new})
        # Navigate down to check the replacement
        assert isinstance(result.rhs, Sequence)
        assert isinstance(result.rhs.elements[1], Option)
        assert isinstance(result.rhs.elements[1].rhs, Star)
        assert result.rhs.elements[1].rhs.rhs == nt_new

    def test_rewrite_multiple_replacements(self):
        """Rewrite with multiple replacements in mapping."""
        nt1_old = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt1_new = Nonterminal('NewFoo', MessageType('test', 'Foo'))
        nt2_old = Nonterminal('Bar', MessageType('test', 'Bar'))
        nt2_new = Nonterminal('NewBar', MessageType('test', 'Bar'))
        seq = Sequence((nt1_old, nt2_old))
        # Constructor needs 2 params since RHS has 2 non-literals
        param1 = Var('x', MessageType('test', 'Foo'))
        param2 = Var('y', MessageType('test', 'Bar'))
        rule = make_rule(
            lhs=Nonterminal('Result', MessageType('test', 'Result')),
            rhs=seq,
            constructor=Lambda([param1, param2], MessageType('test', 'Result'), param1),
            source_type='test.Result'
        )
        result = rewrite_rule(rule, {nt1_old: nt1_new, nt2_old: nt2_new})
        assert isinstance(result.rhs, Sequence)
        assert result.rhs.elements[0] == nt1_new
        assert result.rhs.elements[1] == nt2_new

    def test_rewrite_preserves_lhs_and_constructor(self):
        """Rewrite only changes rhs, preserves other rule fields."""
        nt_old = Nonterminal('Foo', MessageType('test', 'Foo'))
        nt_new = Nonterminal('Bar', MessageType('test', 'Foo'))
        lhs = Nonterminal('Result', MessageType('test', 'Result'))
        param = Var('x', MessageType('test', 'Foo'))
        constructor = Lambda([param], MessageType('test', 'Result'), param)
        rule = make_rule(
            lhs=lhs,
            rhs=nt_old,
            constructor=constructor,
            source_type='test.Result'
        )
        result = rewrite_rule(rule, {nt_old: nt_new})
        assert result.lhs == lhs
        assert result.constructor == constructor
        assert result.source_type == 'test.Result'
