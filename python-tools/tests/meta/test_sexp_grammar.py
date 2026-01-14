"""Tests for s-expression to grammar conversions."""

import pytest

from meta.sexp import SAtom, SList
from meta.sexp_parser import parse_sexp
from meta.sexp_grammar import (
    sexp_to_rhs, sexp_to_rule, rhs_to_sexp, rule_to_sexp,
    load_grammar_config, GrammarConversionError
)
from meta.grammar import (
    LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence, Rule
)
from meta.target import BaseType, MessageType, ListType, Lambda, Var, Lit, Call, Builtin


class TestSexpToRhs:
    """Tests for converting s-expressions to Rhs."""

    def test_lit_terminal(self):
        result = sexp_to_rhs(parse_sexp('"missing"'))
        assert result == LitTerminal("missing")

    def test_lit_terminal_operator(self):
        result = sexp_to_rhs(parse_sexp('"="'))
        assert result == LitTerminal("=")

    def test_lit_terminal_paren(self):
        result = sexp_to_rhs(parse_sexp('"("'))
        assert result == LitTerminal("(")

    def test_nonterminal(self):
        result = sexp_to_rhs(parse_sexp("(nonterm value (Message logic Value))"))
        assert result == Nonterminal("value", MessageType("logic", "Value"))

    def test_nonterminal_base_type(self):
        result = sexp_to_rhs(parse_sexp("(nonterm name String)"))
        assert result == Nonterminal("name", BaseType("String"))

    def test_named_terminal(self):
        result = sexp_to_rhs(parse_sexp("(term STRING String)"))
        assert result == NamedTerminal("STRING", BaseType("String"))

    def test_named_terminal_int(self):
        result = sexp_to_rhs(parse_sexp("(term INT Int64)"))
        assert result == NamedTerminal("INT", BaseType("Int64"))

    def test_star_nonterminal(self):
        result = sexp_to_rhs(parse_sexp("(star (nonterm binding (Message logic Binding)))"))
        assert result == Star(Nonterminal("binding", MessageType("logic", "Binding")))

    def test_star_terminal(self):
        result = sexp_to_rhs(parse_sexp("(star (term INT Int64))"))
        assert result == Star(NamedTerminal("INT", BaseType("Int64")))

    def test_option_nonterminal(self):
        result = sexp_to_rhs(parse_sexp("(option (nonterm sync (Message transactions Sync)))"))
        assert result == Option(Nonterminal("sync", MessageType("transactions", "Sync")))

    def test_option_terminal(self):
        result = sexp_to_rhs(parse_sexp("(option (term INT Int64))"))
        assert result == Option(NamedTerminal("INT", BaseType("Int64")))

    def test_sequence_simple(self):
        result = sexp_to_rhs(parse_sexp('(seq "(" ")" )'))
        assert result == Sequence((LitTerminal("("), LitTerminal(")")))

    def test_sequence_mixed(self):
        result = sexp_to_rhs(parse_sexp('(seq "(" "date" (term INT Int64) (term INT Int64) (term INT Int64) ")")'))
        expected = Sequence((
            LitTerminal("("),
            LitTerminal("date"),
            NamedTerminal("INT", BaseType("Int64")),
            NamedTerminal("INT", BaseType("Int64")),
            NamedTerminal("INT", BaseType("Int64")),
            LitTerminal(")")
        ))
        assert result == expected

    def test_sequence_with_nonterminals(self):
        result = sexp_to_rhs(parse_sexp('(seq "(" "rule" (nonterm name String) (nonterm value (Message logic Value)) ")")'))
        expected = Sequence((
            LitTerminal("("),
            LitTerminal("rule"),
            Nonterminal("name", BaseType("String")),
            Nonterminal("value", MessageType("logic", "Value")),
            LitTerminal(")")
        ))
        assert result == expected

    def test_sequence_with_star_and_option(self):
        result = sexp_to_rhs(parse_sexp('(seq "[" (star (nonterm binding (Message logic Binding))) (option (nonterm values (List (Message logic Binding)))) "]")'))
        expected = Sequence((
            LitTerminal("["),
            Star(Nonterminal("binding", MessageType("logic", "Binding"))),
            Option(Nonterminal("values", ListType(MessageType("logic", "Binding")))),
            LitTerminal("]")
        ))
        assert result == expected

    def test_invalid_rhs_unquoted_atom(self):
        with pytest.raises(GrammarConversionError):
            sexp_to_rhs(SAtom("foo"))

    def test_invalid_rhs_unknown_form(self):
        with pytest.raises(GrammarConversionError):
            sexp_to_rhs(parse_sexp("(unknown foo bar)"))

    def test_star_invalid_inner(self):
        with pytest.raises(GrammarConversionError):
            sexp_to_rhs(parse_sexp('(star "literal")'))


class TestSexpToRule:
    """Tests for converting s-expressions to Rule."""

    def test_simple_rule_lit_terminal(self):
        sexp = parse_sexp('''
            (rule (lhs boolean_value Boolean)
                (rhs "true")
                (lambda () Boolean (lit true)))
        ''')
        result = sexp_to_rule(sexp)
        assert result.lhs == Nonterminal("boolean_value", BaseType("Boolean"))
        assert result.rhs == LitTerminal("true")
        assert isinstance(result.constructor, Lambda)
        assert result.constructor.params == ()
        assert result.constructor.body == Lit(True)

    def test_rule_with_nonterminal(self):
        sexp = parse_sexp('''
            (rule (lhs value (Message logic Value))
                (rhs (nonterm date (Message logic DateValue)))
                (lambda ((value (Message logic DateValue))) (Message logic Value)
                    (call (message logic Value)
                        (call (oneof date_value) (var value (Message logic DateValue))))))
        ''')
        result = sexp_to_rule(sexp)
        assert result.lhs == Nonterminal("value", MessageType("logic", "Value"))
        assert result.rhs == Nonterminal("date", MessageType("logic", "DateValue"))
        assert len(result.constructor.params) == 1
        assert result.constructor.params[0].name == "value"

    def test_rule_with_sequence(self):
        sexp = parse_sexp('''
            (rule (lhs date (Message logic DateValue))
                (rhs "(" "date" (term INT Int64) (term INT Int64) (term INT Int64) ")")
                (lambda ((year Int64) (month Int64) (day Int64)) (Message logic DateValue)
                    (call (message logic DateValue)
                        (var year Int64) (var month Int64) (var day Int64))))
        ''')
        result = sexp_to_rule(sexp)
        assert result.lhs == Nonterminal("date", MessageType("logic", "DateValue"))
        assert isinstance(result.rhs, Sequence)
        assert len(result.rhs.elements) == 6
        assert len(result.constructor.params) == 3

    def test_rule_with_star(self):
        sexp = parse_sexp('''
            (rule (lhs config_dict (List (Tuple String (Message logic Value))))
                (rhs "{" (star (nonterm config_key_value (Tuple String (Message logic Value)))) "}")
                (lambda ((x (List (Tuple String (Message logic Value))))) (List (Tuple String (Message logic Value)))
                    (var x (List (Tuple String (Message logic Value))))))
        ''')
        result = sexp_to_rule(sexp)
        assert result.lhs.name == "config_dict"
        assert isinstance(result.rhs, Sequence)
        assert isinstance(result.rhs.elements[1], Star)

    def test_invalid_rule_wrong_element_count(self):
        with pytest.raises(GrammarConversionError):
            sexp_to_rule(parse_sexp("(rule foo)"))

    def test_invalid_rule_non_lambda_constructor(self):
        with pytest.raises(GrammarConversionError):
            sexp_to_rule(parse_sexp('(rule (lhs foo String) (rhs "bar") (lit 42))'))


class TestRhsToSexp:
    """Tests for converting Rhs to s-expressions."""

    def test_lit_terminal(self):
        result = rhs_to_sexp(LitTerminal("missing"))
        assert result == SAtom("missing", quoted=True)

    def test_named_terminal(self):
        result = rhs_to_sexp(NamedTerminal("STRING", BaseType("String")))
        assert result == SList((SAtom("term"), SAtom("STRING"), SAtom("String")))

    def test_nonterminal(self):
        result = rhs_to_sexp(Nonterminal("value", MessageType("logic", "Value")))
        expected = SList((
            SAtom("nonterm"),
            SAtom("value"),
            SList((SAtom("Message"), SAtom("logic"), SAtom("Value")))
        ))
        assert result == expected

    def test_star(self):
        result = rhs_to_sexp(Star(Nonterminal("binding", MessageType("logic", "Binding"))))
        expected = SList((
            SAtom("star"),
            SList((
                SAtom("nonterm"),
                SAtom("binding"),
                SList((SAtom("Message"), SAtom("logic"), SAtom("Binding")))
            ))
        ))
        assert result == expected

    def test_option(self):
        result = rhs_to_sexp(Option(NamedTerminal("INT", BaseType("Int64"))))
        expected = SList((
            SAtom("option"),
            SList((SAtom("term"), SAtom("INT"), SAtom("Int64")))
        ))
        assert result == expected

    def test_sequence(self):
        result = rhs_to_sexp(Sequence((LitTerminal("("), LitTerminal(")"))))
        expected = SList((SAtom("seq"), SAtom("(", quoted=True), SAtom(")", quoted=True)))
        assert result == expected


class TestRuleToSexp:
    """Tests for converting Rule to s-expressions."""

    def test_simple_rule(self):
        rule = Rule(
            lhs=Nonterminal("boolean_value", BaseType("Boolean")),
            rhs=LitTerminal("true"),
            constructor=Lambda([], BaseType("Boolean"), Lit(True))
        )
        result = rule_to_sexp(rule)
        assert isinstance(result, SList)
        assert result[0] == SAtom("rule")
        # result[1] is (lhs boolean_value Boolean)
        assert isinstance(result[1], SList)
        assert result[1][0] == SAtom("lhs")
        assert result[1][1] == SAtom("boolean_value")
        # result[2] is (rhs "true")
        assert isinstance(result[2], SList)
        assert result[2][0] == SAtom("rhs")

    def test_rule_with_params(self):
        rule = Rule(
            lhs=Nonterminal("name", BaseType("String")),
            rhs=NamedTerminal("COLON_SYMBOL", BaseType("String")),
            constructor=Lambda(
                [Var("x", BaseType("String"))],
                BaseType("String"),
                Var("x", BaseType("String"))
            )
        )
        result = rule_to_sexp(rule)
        assert isinstance(result, SList)
        assert result[0] == SAtom("rule")
        assert isinstance(result[1], SList)
        assert result[1][0] == SAtom("lhs")


class TestRhsRoundTrip:
    """Tests for Rhs conversion round-tripping."""

    def test_roundtrip_lit_terminal(self):
        original = LitTerminal("missing")
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp)
        assert recovered == original

    def test_roundtrip_named_terminal(self):
        original = NamedTerminal("STRING", BaseType("String"))
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp)
        assert recovered == original

    def test_roundtrip_nonterminal(self):
        original = Nonterminal("value", MessageType("logic", "Value"))
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp)
        assert recovered == original

    def test_roundtrip_star(self):
        original = Star(Nonterminal("binding", MessageType("logic", "Binding")))
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp)
        assert recovered == original

    def test_roundtrip_option(self):
        original = Option(NamedTerminal("INT", BaseType("Int64")))
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp)
        assert recovered == original

    def test_roundtrip_sequence(self):
        original = Sequence((
            LitTerminal("("),
            LitTerminal("date"),
            NamedTerminal("INT", BaseType("Int64")),
            NamedTerminal("INT", BaseType("Int64")),
            NamedTerminal("INT", BaseType("Int64")),
            LitTerminal(")")
        ))
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp)
        assert recovered == original

    def test_roundtrip_complex_sequence(self):
        original = Sequence((
            LitTerminal("["),
            Star(Nonterminal("binding", MessageType("logic", "Binding"))),
            Option(Nonterminal("values", ListType(MessageType("logic", "Binding")))),
            LitTerminal("]")
        ))
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp)
        assert recovered == original


class TestRuleRoundTrip:
    """Tests for Rule conversion round-tripping."""

    def test_roundtrip_simple_rule(self):
        original = Rule(
            lhs=Nonterminal("boolean_value", BaseType("Boolean")),
            rhs=LitTerminal("true"),
            constructor=Lambda([], BaseType("Boolean"), Lit(True))
        )
        sexp = rule_to_sexp(original)
        recovered = sexp_to_rule(sexp)
        assert recovered.lhs == original.lhs
        assert recovered.rhs == original.rhs
        assert recovered.constructor == original.constructor

    def test_roundtrip_rule_with_terminal(self):
        original = Rule(
            lhs=Nonterminal("name", BaseType("String")),
            rhs=NamedTerminal("COLON_SYMBOL", BaseType("String")),
            constructor=Lambda(
                [Var("x", BaseType("String"))],
                BaseType("String"),
                Var("x", BaseType("String"))
            )
        )
        sexp = rule_to_sexp(original)
        recovered = sexp_to_rule(sexp)
        assert recovered.lhs == original.lhs
        assert recovered.rhs == original.rhs
        assert recovered.constructor == original.constructor

    def test_roundtrip_rule_with_sequence(self):
        original = Rule(
            lhs=Nonterminal("date", MessageType("logic", "DateValue")),
            rhs=Sequence((
                LitTerminal("("),
                LitTerminal("date"),
                NamedTerminal("INT", BaseType("Int64")),
                NamedTerminal("INT", BaseType("Int64")),
                NamedTerminal("INT", BaseType("Int64")),
                LitTerminal(")")
            )),
            constructor=Lambda(
                [Var("year", BaseType("Int64")), Var("month", BaseType("Int64")), Var("day", BaseType("Int64"))],
                MessageType("logic", "DateValue"),
                Call(
                    Builtin("make_date"),
                    [Var("year", BaseType("Int64")), Var("month", BaseType("Int64")), Var("day", BaseType("Int64"))]
                )
            )
        )
        sexp = rule_to_sexp(original)
        recovered = sexp_to_rule(sexp)
        assert recovered.lhs == original.lhs
        assert recovered.rhs == original.rhs
        assert recovered.constructor == original.constructor


class TestLoadGrammarConfig:
    """Tests for loading grammar configuration."""

    def test_load_single_rule(self):
        config = '''
            (rule (lhs boolean_value Boolean)
                (rhs "true")
                (lambda () Boolean (lit true)))
        '''
        result = load_grammar_config(config)
        assert len(result) == 1
        nt = Nonterminal("boolean_value", BaseType("Boolean"))
        assert nt in result
        rules, is_final = result[nt]
        assert len(rules) == 1
        assert is_final is True

    def test_load_multiple_rules_same_lhs(self):
        config = '''
            (rule (lhs boolean_value Boolean)
                (rhs "true")
                (lambda () Boolean (lit true)))
            (rule (lhs boolean_value Boolean)
                (rhs "false")
                (lambda () Boolean (lit false)))
        '''
        result = load_grammar_config(config)
        nt = Nonterminal("boolean_value", BaseType("Boolean"))
        rules, is_final = result[nt]
        assert len(rules) == 2
        assert is_final is True

    def test_load_multiple_rules_different_lhs(self):
        config = '''
            (rule (lhs boolean_value Boolean)
                (rhs "true")
                (lambda () Boolean (lit true)))
            (rule (lhs name String)
                (rhs (term COLON_SYMBOL String))
                (lambda ((x String)) String (var x String)))
        '''
        result = load_grammar_config(config)
        assert len(result) == 2

    def test_load_with_mark_nonfinal(self):
        config = '''
            (rule (lhs formula (Message logic Formula))
                (rhs (nonterm conjunction (Message logic Conjunction)))
                (lambda ((value (Message logic Conjunction))) (Message logic Formula)
                    (call (message logic Formula)
                        (call (oneof conjunction) (var value (Message logic Conjunction))))))
            (mark-nonfinal formula)
        '''
        result = load_grammar_config(config)
        nt = Nonterminal("formula", MessageType("logic", "Formula"))
        rules, is_final = result[nt]
        assert len(rules) == 1
        assert is_final is False

    def test_load_with_comments(self):
        config = '''
            ; This is a comment
            (rule (lhs boolean_value Boolean)
                (rhs "true")
                (lambda () Boolean (lit true)))
            ; Another comment
        '''
        result = load_grammar_config(config)
        assert len(result) == 1

    def test_load_empty_config(self):
        result = load_grammar_config("")
        assert len(result) == 0

    def test_load_comments_only(self):
        config = '''
            ; Just comments
            ; No rules
        '''
        result = load_grammar_config(config)
        assert len(result) == 0

    def test_load_invalid_directive(self):
        config = '''
            (unknown_directive foo bar)
        '''
        with pytest.raises(GrammarConversionError):
            load_grammar_config(config)
