#!/usr/bin/env python3
"""Tests for grammar data structures."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.grammar import (
    LitTerminal, NamedTerminal, Nonterminal,
    Star, Option, Sequence,
    Rule, Token, Grammar,

    get_nonterminals, get_literals, is_epsilon, rhs_elements,
    _count_nonliteral_rhs_elements,
)
from meta.target import BaseType, MessageType, TupleType, ListType, OptionType, Lambda, Var, Lit, Call, Builtin


class TestLitTerminal:
    """Tests for LitTerminal."""

    def test_construction(self):
        """Test LitTerminal construction."""
        term = LitTerminal("if")
        assert term.name == "if"

    def test_str(self):
        """Test LitTerminal string representation."""
        term = LitTerminal("keyword")
        assert str(term) == '"keyword"'

    def test_target_type(self):
        """Test LitTerminal target type is empty tuple."""
        term = LitTerminal("foo")
        result = term.target_type()
        assert isinstance(result, TupleType)
        assert len(result.elements) == 0

    def test_hashable(self):
        """Test that LitTerminal is hashable."""
        term1 = LitTerminal("x")
        term2 = LitTerminal("x")
        term3 = LitTerminal("y")
        assert term1 == term2
        assert term1 != term3
        assert hash(term1) == hash(term2)
        assert hash(term1) != hash(term3)
        s = {term1, term2, term3}
        assert len(s) == 2


class TestNamedTerminal:
    """Tests for NamedTerminal."""

    def test_construction(self):
        """Test NamedTerminal construction."""
        term = NamedTerminal("SYMBOL", BaseType("String"))
        assert term.name == "SYMBOL"
        assert term.type == BaseType("String")

    def test_str(self):
        """Test NamedTerminal string representation."""
        term = NamedTerminal("NUMBER", BaseType("Int64"))
        assert str(term) == "NUMBER"

    def test_target_type(self):
        """Test NamedTerminal returns its type."""
        term = NamedTerminal("ID", BaseType("String"))
        assert term.target_type() == BaseType("String")

    def test_hashable(self):
        """Test that NamedTerminal is hashable."""
        term1 = NamedTerminal("TOK", BaseType("String"))
        term2 = NamedTerminal("TOK", BaseType("String"))
        term3 = NamedTerminal("TOK2", BaseType("String"))
        assert term1 == term2
        assert term1 != term3
        s = {term1, term2, term3}
        assert len(s) == 2


class TestNonterminal:
    """Tests for Nonterminal."""

    def test_construction(self):
        """Test Nonterminal construction."""
        nt = Nonterminal("Expr", MessageType("proto", "Expr"))
        assert nt.name == "Expr"
        assert nt.type == MessageType("proto", "Expr")

    def test_str(self):
        """Test Nonterminal string representation."""
        nt = Nonterminal("Statement", MessageType("proto", "Stmt"))
        assert str(nt) == "Statement"

    def test_target_type(self):
        """Test Nonterminal returns its type."""
        nt = Nonterminal("Value", MessageType("proto", "Value"))
        assert nt.target_type() == MessageType("proto", "Value")

    def test_hashable(self):
        """Test that Nonterminal is hashable."""
        nt1 = Nonterminal("A", MessageType("proto", "A"))
        nt2 = Nonterminal("A", MessageType("proto", "A"))
        nt3 = Nonterminal("B", MessageType("proto", "B"))
        assert nt1 == nt2
        assert nt1 != nt3
        s = {nt1, nt2, nt3}
        assert len(s) == 2


class TestStar:
    """Tests for Star."""

    def test_construction_with_nonterminal(self):
        """Test Star construction with Nonterminal."""
        nt = Nonterminal("Item", MessageType("proto", "Item"))
        star = Star(nt)
        assert star.rhs == nt

    def test_construction_with_terminal(self):
        """Test Star construction with NamedTerminal."""
        term = NamedTerminal("NUMBER", BaseType("Int64"))
        star = Star(term)
        assert star.rhs == term

    def test_str(self):
        """Test Star string representation."""
        nt = Nonterminal("Item", MessageType("proto", "Item"))
        star = Star(nt)
        assert str(star) == "Item*"

    def test_target_type(self):
        """Test Star returns list type."""
        nt = Nonterminal("Item", MessageType("proto", "Item"))
        star = Star(nt)
        result = star.target_type()
        assert isinstance(result, ListType)
        assert result.element_type == MessageType("proto", "Item")


class TestOption:
    """Tests for Option."""

    def test_construction_with_nonterminal(self):
        """Test Option construction with Nonterminal."""
        nt = Nonterminal("Value", MessageType("proto", "Value"))
        opt = Option(nt)
        assert opt.rhs == nt

    def test_construction_with_terminal(self):
        """Test Option construction with NamedTerminal."""
        term = NamedTerminal("ID", BaseType("String"))
        opt = Option(term)
        assert opt.rhs == term

    def test_str(self):
        """Test Option string representation."""
        nt = Nonterminal("Value", MessageType("proto", "Value"))
        opt = Option(nt)
        assert str(opt) == "Value?"

    def test_target_type(self):
        """Test Option returns option type."""
        nt = Nonterminal("Value", MessageType("proto", "Value"))
        opt = Option(nt)
        result = opt.target_type()
        assert isinstance(result, OptionType)
        assert result.element_type == MessageType("proto", "Value")


class TestSequence:
    """Tests for Sequence."""

    def test_construction_empty(self):
        """Test Sequence construction with empty tuple."""
        seq = Sequence(())
        assert len(seq.elements) == 0
        assert isinstance(seq.elements, tuple)

    def test_construction_single(self):
        """Test Sequence with single element."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        seq = Sequence((nt,))
        assert len(seq.elements) == 1
        assert seq.elements[0] == nt

    def test_construction_multiple(self):
        """Test Sequence with multiple elements."""
        nt1 = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("foo")
        nt2 = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((nt1, lit, nt2))
        assert len(seq.elements) == 3

    def test_construction_fails_with_nested_sequence(self):
        """Test Sequence fails with nested Sequence."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        inner = Sequence((nt,))
        with pytest.raises(AssertionError, match="Sequence elements cannot be Sequence"):
            Sequence((inner,))

    def test_str(self):
        """Test Sequence string representation."""
        nt1 = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("if")
        nt2 = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((nt1, lit, nt2))
        assert str(seq) == 'A "if" B'

    def test_target_type_empty(self):
        """Test Sequence with empty elements returns empty tuple type."""
        seq = Sequence(())
        result = seq.target_type()
        assert isinstance(result, TupleType)
        assert len(result.elements) == 0

    def test_target_type_single_nonliteral(self):
        """Test Sequence with single non-literal returns element type directly."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        seq = Sequence((nt,))
        result = seq.target_type()
        assert result == MessageType("proto", "A")

    def test_target_type_multiple_nonliterals(self):
        """Test Sequence with multiple non-literals returns tuple type."""
        nt1 = Nonterminal("A", MessageType("proto", "A"))
        nt2 = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((nt1, nt2))
        result = seq.target_type()
        assert isinstance(result, TupleType)
        assert len(result.elements) == 2
        assert result.elements[0] == MessageType("proto", "A")
        assert result.elements[1] == MessageType("proto", "B")

    def test_target_type_filters_literals(self):
        """Test Sequence filters out literals from target type."""
        nt1 = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("foo")
        nt2 = Nonterminal("B", MessageType("proto", "B"))
        seq = Sequence((nt1, lit, nt2))
        result = seq.target_type()
        assert isinstance(result, TupleType)
        assert len(result.elements) == 2
        assert result.elements[0] == MessageType("proto", "A")
        assert result.elements[1] == MessageType("proto", "B")


class TestRule:
    """Tests for Rule."""

    def test_construction_simple(self):
        """Test Rule construction with matching action parameters."""
        lhs = Nonterminal("A", MessageType("proto", "A"))
        nt = Nonterminal("B", MessageType("proto", "B"))
        rhs = nt
        param = Var("x", MessageType("proto", "B"))
        constructor = Lambda([param], MessageType("proto", "A"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "B")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')])])
        )
        rule = Rule(lhs, rhs, constructor, deconstructor)
        assert rule.lhs == lhs
        assert rule.rhs == rhs
        assert rule.constructor == constructor

    def test_construction_with_sequence(self):
        """Test Rule construction with sequence RHS."""
        lhs = Nonterminal("A", MessageType("proto", "A"))
        nt1 = Nonterminal("B", MessageType("proto", "B"))
        nt2 = Nonterminal("C", MessageType("proto", "C"))
        rhs = Sequence((nt1, nt2))
        param1 = Var("x", MessageType("proto", "B"))
        param2 = Var("y", MessageType("proto", "C"))
        constructor = Lambda([param1, param2], MessageType("proto", "A"), param1)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(TupleType([MessageType("proto", "B"), MessageType("proto", "C")])),
            Call(Builtin('Some'), [Call(Builtin('make_tuple'), [
                Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')]),
                Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('c')])
            ])])
        )
        rule = Rule(lhs, rhs, constructor, deconstructor)
        assert len(rule.constructor.params) == 2

    def test_construction_filters_literals(self):
        """Test Rule construction with literals in RHS."""
        lhs = Nonterminal("A", MessageType("proto", "A"))
        nt = Nonterminal("B", MessageType("proto", "B"))
        lit = LitTerminal("foo")
        rhs = Sequence((nt, lit))
        param = Var("x", MessageType("proto", "B"))
        constructor = Lambda([param], MessageType("proto", "A"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "B")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')])])
        )
        rule = Rule(lhs, rhs, constructor, deconstructor)
        assert len(rule.constructor.params) == 1

    def test_construction_fails_with_wrong_param_count(self):
        """Test Rule construction fails with mismatched parameter count."""
        lhs = Nonterminal("A", MessageType("proto", "A"))
        nt1 = Nonterminal("B", MessageType("proto", "B"))
        nt2 = Nonterminal("C", MessageType("proto", "C"))
        rhs = Sequence((nt1, nt2))
        param = Var("x", MessageType("proto", "B"))
        constructor = Lambda([param], MessageType("proto", "A"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "B")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')])])
        )
        with pytest.raises(AssertionError, match="Action for A has 1 parameter"):
            Rule(lhs, rhs, constructor, deconstructor)

    def test_str(self):
        """Test Rule string representation."""
        lhs = Nonterminal("A", MessageType("proto", "A"))
        nt = Nonterminal("B", MessageType("proto", "B"))
        param = Var("x", MessageType("proto", "B"))
        constructor = Lambda([param], MessageType("proto", "A"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "B")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')])])
        )
        rule = Rule(lhs, nt, constructor, deconstructor)
        result = str(rule)
        assert "A ->" in result
        assert "B" in result

    def test_source_type(self):
        """Test Rule with source_type."""
        lhs = Nonterminal("A", MessageType("proto", "A"))
        nt = Nonterminal("B", MessageType("proto", "B"))
        param = Var("x", MessageType("proto", "B"))
        constructor = Lambda([param], MessageType("proto", "A"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "B")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')])])
        )
        rule = Rule(lhs, nt, constructor, deconstructor, source_type="SomeProtoType")
        assert rule.source_type == "SomeProtoType"


class TestToken:
    """Tests for Token."""

    def test_construction(self):
        """Test Token construction."""
        token = Token("NUMBER", r"\d+", BaseType("Int64"))
        assert token.name == "NUMBER"
        assert token.pattern == r"\d+"
        assert token.type == BaseType("Int64")


class TestGrammar:
    """Tests for Grammar."""

    def test_construction(self):
        """Test Grammar construction."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        assert grammar.start == start
        assert len(grammar.rules) == 1

    def test_add_rule(self):
        """Test Grammar add_rule."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        nt = Nonterminal("A", MessageType("proto", "A"))
        param = Var("x", MessageType("proto", "A"))
        constructor = Lambda([param], MessageType("proto", "A"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "A")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('a')])])
        )
        rule = Rule(nt, nt, constructor, deconstructor)
        grammar.add_rule(rule)
        assert nt in grammar.rules
        assert len(grammar.rules[nt]) == 1

    def test_add_multiple_rules_same_lhs(self):
        """Test adding multiple rules with same LHS."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        nt = Nonterminal("A", MessageType("proto", "A"))
        nt_b = Nonterminal("B", MessageType("proto", "B"))
        nt_c = Nonterminal("C", MessageType("proto", "C"))
        param_b = Var("x", MessageType("proto", "B"))
        param_c = Var("y", MessageType("proto", "C"))
        constructor_b = Lambda([param_b], MessageType("proto", "A"), param_b)
        constructor_c = Lambda([param_c], MessageType("proto", "A"), param_c)
        deconstructor_b = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "B")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')])])
        )
        deconstructor_c = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "C")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('c')])])
        )
        rule1 = Rule(nt, nt_b, constructor_b, deconstructor_b)
        rule2 = Rule(nt, nt_c, constructor_c, deconstructor_c)
        grammar.add_rule(rule1)
        grammar.add_rule(rule2)
        assert len(grammar.rules[nt]) == 2

    def test_get_rules(self):
        """Test Grammar get_rules."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        nt = Nonterminal("A", MessageType("proto", "A"))
        param = Var("x", MessageType("proto", "A"))
        constructor = Lambda([param], MessageType("proto", "A"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "A")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('a')])])
        )
        rule = Rule(nt, nt, constructor, deconstructor)
        grammar.add_rule(rule)
        rules = grammar.get_rules(nt)
        assert len(rules) == 1
        assert rules[0] == rule

    def test_get_rules_nonexistent(self):
        """Test get_rules for non-existent nonterminal."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        nt = Nonterminal("A", MessageType("proto", "A"))
        rules = grammar.get_rules(nt)
        assert rules == []

    def test_has_rule(self):
        """Test Grammar has_rule."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        nt = Nonterminal("A", MessageType("proto", "A"))
        param = Var("x", MessageType("proto", "A"))
        constructor = Lambda([param], MessageType("proto", "A"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "A"))],
            OptionType(MessageType("proto", "A")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('a')])])
        )
        rule = Rule(nt, nt, constructor, deconstructor)
        grammar.add_rule(rule)
        assert grammar.has_rule(nt)
        other = Nonterminal("B", MessageType("proto", "B"))
        assert not grammar.has_rule(other)

    def test_traverse_rules_preorder(self):
        """Test Grammar traverse_rules_preorder."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        a = Nonterminal("A", MessageType("proto", "A"))
        b = Nonterminal("B", MessageType("proto", "B"))
        c = Nonterminal("C", MessageType("proto", "C"))

        # Start -> A, A -> B, B -> C
        param_a = Var("x", MessageType("proto", "A"))
        param_b = Var("y", MessageType("proto", "B"))
        param_c = Var("z", MessageType("proto", "C"))
        construct_action_start = Lambda([param_a], MessageType("proto", "Start"), param_a)
        construct_action_a = Lambda([param_b], MessageType("proto", "A"), param_b)
        construct_action_b = Lambda([param_c], MessageType("proto", "B"), param_c)
        construct_action_c = Lambda([param_c], MessageType("proto", "C"), param_c)

        deconstruct_action_start = Lambda([Var('msg', MessageType("proto", "Start"))], OptionType(MessageType("proto", "A")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "Start")), Lit('a')])]))
        deconstruct_action_a = Lambda([Var('msg', MessageType("proto", "A"))], OptionType(MessageType("proto", "B")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "A")), Lit('b')])]))
        deconstruct_action_b = Lambda([Var('msg', MessageType("proto", "B"))], OptionType(MessageType("proto", "C")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "B")), Lit('c')])]))
        deconstruct_action_c = Lambda([Var('msg', MessageType("proto", "C"))], OptionType(MessageType("proto", "C")), Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "C")), Lit('c')])]))

        grammar.add_rule(Rule(start, a, construct_action_start, deconstruct_action_start))
        grammar.add_rule(Rule(a, b, construct_action_a, deconstruct_action_a))
        grammar.add_rule(Rule(b, c, construct_action_b, deconstruct_action_b))
        grammar.add_rule(Rule(c, c, construct_action_c, deconstruct_action_c))

        order = grammar.traverse_rules_preorder()
        assert order[0] == start
        assert order[1] == a
        assert order[2] == b
        assert order[3] == c

    def test_nullable_literal(self):
        """Test Grammar nullable for literal."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        lit = LitTerminal("foo")
        assert not grammar.analysis.nullable(lit)

    def test_nullable_star(self):
        """Test Grammar nullable for star."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        nt = Nonterminal("A", MessageType("proto", "A"))
        star = Star(nt)
        assert grammar.analysis.nullable(star)

    def test_nullable_option(self):
        """Test Grammar nullable for option."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        nt = Nonterminal("A", MessageType("proto", "A"))
        opt = Option(nt)
        assert grammar.analysis.nullable(opt)

    def test_nullable_empty_sequence(self):
        """Test Grammar nullable for empty sequence."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        seq = Sequence(())
        assert grammar.analysis.nullable(seq)

    def test_print_grammar(self):
        """Test Grammar print_grammar."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        a = Nonterminal("A", MessageType("proto", "A"))
        param = Var("x", MessageType("proto", "A"))
        constructor = Lambda([param], MessageType("proto", "Start"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "Start"))],
            OptionType(MessageType("proto", "A")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "Start")), Lit('a')])])
        )
        grammar.add_rule(Rule(start, a, constructor, deconstructor))
        output = grammar.print_grammar()
        assert "Start:" in output
        assert "A" in output

    def test_cache_invalidation_on_add_rule(self):
        """Test that caches are not used after add_rule."""
        start = Nonterminal("Start", MessageType("proto", "Start"))
        grammar = Grammar(start)
        a = Nonterminal("A", MessageType("proto", "A"))
        param = Var("x", MessageType("proto", "A"))
        constructor = Lambda([param], MessageType("proto", "Start"), param)
        deconstructor = Lambda(
            [Var('msg', MessageType("proto", "Start"))],
            OptionType(MessageType("proto", "A")),
            Call(Builtin('Some'), [Call(Builtin('get_field'), [Var('msg', MessageType("proto", "Start")), Lit('a')])])
        )
        rule = Rule(start, a, constructor, deconstructor)

        # Trigger analysis (creates _analysis object)
        grammar.analysis.compute_nullable()
        assert grammar._analysis is not None

        # This should fail because analysis exists
        with pytest.raises(AssertionError, match="already analyzed"):
            grammar.add_rule(rule)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_nonterminals_single(self):
        """Test get_nonterminals with single nonterminal."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        result = get_nonterminals(nt)
        assert result == [nt]

    def test_get_nonterminals_terminal(self):
        """Test get_nonterminals with terminal returns empty."""
        term = NamedTerminal("TOK", BaseType("String"))
        result = get_nonterminals(term)
        assert result == []

    def test_get_nonterminals_sequence(self):
        """Test get_nonterminals with sequence."""
        nt1 = Nonterminal("A", MessageType("proto", "A"))
        nt2 = Nonterminal("B", MessageType("proto", "B"))
        lit = LitTerminal("foo")
        seq = Sequence((nt1, lit, nt2))
        result = get_nonterminals(seq)
        assert len(result) == 2
        assert nt1 in result
        assert nt2 in result

    def test_get_nonterminals_star(self):
        """Test get_nonterminals with star."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        star = Star(nt)
        result = get_nonterminals(star)
        assert result == [nt]

    def test_get_nonterminals_option(self):
        """Test get_nonterminals with option."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        opt = Option(nt)
        result = get_nonterminals(opt)
        assert result == [nt]

    def test_get_nonterminals_deduplicates(self):
        """Test get_nonterminals removes duplicates."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        seq = Sequence((nt, nt, nt))
        result = get_nonterminals(seq)
        assert len(result) == 1
        assert result[0] == nt

    def test_get_literals_single(self):
        """Test get_literals with single literal."""
        lit = LitTerminal("foo")
        result = get_literals(lit)
        assert result == [lit]

    def test_get_literals_nonterminal(self):
        """Test get_literals with nonterminal returns empty."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        result = get_literals(nt)
        assert result == []

    def test_get_literals_sequence(self):
        """Test get_literals with sequence."""
        lit1 = LitTerminal("foo")
        lit2 = LitTerminal("bar")
        nt = Nonterminal("A", MessageType("proto", "A"))
        seq = Sequence((lit1, nt, lit2))
        result = get_literals(seq)
        assert len(result) == 2
        assert lit1 in result
        assert lit2 in result

    def test_is_epsilon_empty_sequence(self):
        """Test is_epsilon with empty sequence."""
        seq = Sequence(())
        assert is_epsilon(seq)

    def test_is_epsilon_nonempty_sequence(self):
        """Test is_epsilon with non-empty sequence."""
        lit = LitTerminal("foo")
        seq = Sequence((lit,))
        assert not is_epsilon(seq)

    def test_is_epsilon_nonterminal(self):
        """Test is_epsilon with nonterminal."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        assert not is_epsilon(nt)

    def test_rhs_elements_sequence(self):
        """Test rhs_elements with sequence."""
        lit = LitTerminal("foo")
        nt = Nonterminal("A", MessageType("proto", "A"))
        seq = Sequence((lit, nt))
        result = rhs_elements(seq)
        assert result == (lit, nt)

    def test_rhs_elements_nonsequence(self):
        """Test rhs_elements with non-sequence."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        result = rhs_elements(nt)
        assert result == (nt,)

    def test_count_nonliteral_rhs_elements_single_nonterminal(self):
        """Test _count_nonliteral_rhs_elements with nonterminal."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        assert _count_nonliteral_rhs_elements(nt) == 1

    def test_count_nonliteral_rhs_elements_terminal(self):
        """Test _count_nonliteral_rhs_elements with terminal."""
        term = NamedTerminal("TOK", BaseType("String"))
        assert _count_nonliteral_rhs_elements(term) == 1

    def test_count_nonliteral_rhs_elements_literal(self):
        """Test _count_nonliteral_rhs_elements with literal."""
        lit = LitTerminal("foo")
        assert _count_nonliteral_rhs_elements(lit) == 0

    def test_count_nonliteral_rhs_elements_star(self):
        """Test _count_nonliteral_rhs_elements with star."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        star = Star(nt)
        assert _count_nonliteral_rhs_elements(star) == 1

    def test_count_nonliteral_rhs_elements_option(self):
        """Test _count_nonliteral_rhs_elements with option."""
        nt = Nonterminal("A", MessageType("proto", "A"))
        opt = Option(nt)
        assert _count_nonliteral_rhs_elements(opt) == 1

    def test_count_nonliteral_rhs_elements_sequence(self):
        """Test _count_nonliteral_rhs_elements with sequence."""
        nt1 = Nonterminal("A", MessageType("proto", "A"))
        lit = LitTerminal("foo")
        nt2 = Nonterminal("B", MessageType("proto", "B"))
        term = NamedTerminal("TOK", BaseType("String"))
        seq = Sequence((nt1, lit, nt2, term))
        assert _count_nonliteral_rhs_elements(seq) == 3
