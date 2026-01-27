"""Tests for s-expression to grammar conversions."""

import pytest

from meta.sexp import SAtom, SList
from meta.sexp_parser import parse_sexp
from meta.sexp_grammar import (
    sexp_to_rhs, sexp_to_rule, rhs_to_sexp, rule_to_sexp,
    load_grammar_config, GrammarConversionError, TypeContext
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


class TestSexpToRhsWithContext:
    """Tests for converting s-expressions to Rhs with TypeContext.

    With context, bare symbols are looked up as terminals or nonterminals.
    """

    @pytest.fixture
    def ctx(self):
        return TypeContext(
            terminals={
                "STRING": BaseType("String"),
                "INT": BaseType("Int64"),
                "FLOAT": BaseType("Float64"),
            },
            nonterminals={
                "value": MessageType("logic", "Value"),
                "binding": MessageType("logic", "Binding"),
                "sync": MessageType("transactions", "Sync"),
            }
        )

    def test_lit_terminal(self, ctx):
        result = sexp_to_rhs(parse_sexp('"missing"'), ctx)
        assert result == LitTerminal("missing")

    def test_nonterminal_bare_symbol(self, ctx):
        """Bare symbol is looked up as nonterminal."""
        result = sexp_to_rhs(parse_sexp("value"), ctx)
        assert result == Nonterminal("value", MessageType("logic", "Value"))

    def test_terminal_bare_symbol(self, ctx):
        """Bare symbol is looked up as terminal."""
        result = sexp_to_rhs(parse_sexp("STRING"), ctx)
        assert result == NamedTerminal("STRING", BaseType("String"))

    def test_star_with_bare_symbol(self, ctx):
        result = sexp_to_rhs(parse_sexp("(star binding)"), ctx)
        assert result == Star(Nonterminal("binding", MessageType("logic", "Binding")))

    def test_option_with_bare_symbol(self, ctx):
        result = sexp_to_rhs(parse_sexp("(option INT)"), ctx)
        assert result == Option(NamedTerminal("INT", BaseType("Int64")))

    def test_sequence_with_bare_symbols(self, ctx):
        result = sexp_to_rhs(parse_sexp('(seq "(" INT value ")")'), ctx)
        expected = Sequence((
            LitTerminal("("),
            NamedTerminal("INT", BaseType("Int64")),
            Nonterminal("value", MessageType("logic", "Value")),
            LitTerminal(")")
        ))
        assert result == expected

    def test_unknown_symbol_error(self, ctx):
        """Unknown bare symbol raises error."""
        with pytest.raises(GrammarConversionError, match="unknown symbol"):
            sexp_to_rhs(parse_sexp("unknown_name"), ctx)


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
                    (new-message logic Value
                        (value (call (oneof date_value) (var value (Message logic DateValue)))))))
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
                    (new-message logic DateValue
                        (year (var year Int64)) (month (var month Int64)) (day (var day Int64)))))
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
    """Tests for converting Rhs to s-expressions.

    Terminals and nonterminals are output as bare symbols.
    Types are declared separately via terminal declarations and rule LHS.
    """

    def test_lit_terminal(self):
        result = rhs_to_sexp(LitTerminal("missing"))
        assert result == SAtom("missing", quoted=True)

    def test_named_terminal(self):
        result = rhs_to_sexp(NamedTerminal("STRING", BaseType("String")))
        # Bare symbol for terminals
        assert result == SAtom("STRING")

    def test_nonterminal(self):
        result = rhs_to_sexp(Nonterminal("value", MessageType("logic", "Value")))
        # Bare symbol for nonterminals
        assert result == SAtom("value")

    def test_star(self):
        result = rhs_to_sexp(Star(Nonterminal("binding", MessageType("logic", "Binding"))))
        expected = SList((SAtom("star"), SAtom("binding")))
        assert result == expected

    def test_option(self):
        result = rhs_to_sexp(Option(NamedTerminal("INT", BaseType("Int64"))))
        expected = SList((SAtom("option"), SAtom("INT")))
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
    """Tests for Rhs conversion round-tripping.

    Round-tripping requires a TypeContext because rhs_to_sexp does not
    include types, so sexp_to_rhs needs to look them up from context.
    """

    def test_roundtrip_lit_terminal(self):
        # Lit terminals don't need context
        original = LitTerminal("missing")
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp)
        assert recovered == original

    def test_roundtrip_named_terminal(self):
        original = NamedTerminal("STRING", BaseType("String"))
        ctx = TypeContext(
            terminals={"STRING": BaseType("String")},
            nonterminals={}
        )
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp, ctx)
        assert recovered == original

    def test_roundtrip_nonterminal(self):
        original = Nonterminal("value", MessageType("logic", "Value"))
        ctx = TypeContext(
            terminals={},
            nonterminals={"value": MessageType("logic", "Value")}
        )
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp, ctx)
        assert recovered == original

    def test_roundtrip_star(self):
        original = Star(Nonterminal("binding", MessageType("logic", "Binding")))
        ctx = TypeContext(
            terminals={},
            nonterminals={"binding": MessageType("logic", "Binding")}
        )
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp, ctx)
        assert recovered == original

    def test_roundtrip_option(self):
        original = Option(NamedTerminal("INT", BaseType("Int64")))
        ctx = TypeContext(
            terminals={"INT": BaseType("Int64")},
            nonterminals={}
        )
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp, ctx)
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
        ctx = TypeContext(
            terminals={"INT": BaseType("Int64")},
            nonterminals={}
        )
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp, ctx)
        assert recovered == original

    def test_roundtrip_complex_sequence(self):
        original = Sequence((
            LitTerminal("["),
            Star(Nonterminal("binding", MessageType("logic", "Binding"))),
            Option(Nonterminal("values", ListType(MessageType("logic", "Binding")))),
            LitTerminal("]")
        ))
        ctx = TypeContext(
            terminals={},
            nonterminals={
                "binding": MessageType("logic", "Binding"),
                "values": ListType(MessageType("logic", "Binding"))
            }
        )
        sexp = rhs_to_sexp(original)
        recovered = sexp_to_rhs(sexp, ctx)
        assert recovered == original


class TestRuleRoundTrip:
    """Tests for Rule conversion round-tripping.

    Round-tripping requires a TypeContext because rhs_to_sexp does not
    include types, so sexp_to_rule needs context to look them up.
    """

    def test_roundtrip_simple_rule(self):
        # Lit terminals don't need context
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
        ctx = TypeContext(
            terminals={"COLON_SYMBOL": BaseType("String")},
            nonterminals={"name": BaseType("String")}
        )
        sexp = rule_to_sexp(original)
        recovered = sexp_to_rule(sexp, ctx)
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
        ctx = TypeContext(
            terminals={"INT": BaseType("Int64")},
            nonterminals={"date": MessageType("logic", "DateValue")}
        )
        sexp = rule_to_sexp(original)
        recovered = sexp_to_rule(sexp, ctx)
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
        assert len(result.rules) == 1
        nt = Nonterminal("boolean_value", BaseType("Boolean"))
        assert nt in result.rules
        rules = result.rules[nt]
        assert len(rules) == 1

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
        rules = result.rules[nt]
        assert len(rules) == 2

    def test_load_multiple_rules_different_lhs(self):
        config = '''
            (terminal COLON_SYMBOL String)
            (rule (lhs boolean_value Boolean)
                (rhs "true")
                (lambda () Boolean (lit true)))
            (rule (lhs name String)
                (rhs COLON_SYMBOL)
                (lambda ((x String)) String (var x String)))
        '''
        result = load_grammar_config(config)
        assert len(result.rules) == 2

    def test_load_with_comments(self):
        config = '''
            ; This is a comment
            (rule (lhs boolean_value Boolean)
                (rhs "true")
                (lambda () Boolean (lit true)))
            ; Another comment
        '''
        result = load_grammar_config(config)
        assert len(result.rules) == 1

    def test_load_empty_config(self):
        result = load_grammar_config("")
        assert len(result.rules) == 0
        assert len(result.terminals) == 0

    def test_load_comments_only(self):
        config = '''
            ; Just comments
            ; No rules
        '''
        result = load_grammar_config(config)
        assert len(result.rules) == 0

    def test_load_invalid_directive(self):
        config = '''
            (unknown_directive foo bar)
        '''
        with pytest.raises(GrammarConversionError):
            load_grammar_config(config)

    def test_load_with_terminal_declarations(self):
        """Test loading config with terminal declarations."""
        config = '''
            (terminal STRING String)
            (terminal INT Int64)
            (rule (lhs name String)
                (rhs STRING)
                (lambda ((x String)) String (var x String)))
        '''
        result = load_grammar_config(config)
        assert len(result.terminals) == 2
        assert "STRING" in result.terminals
        assert "INT" in result.terminals
        assert result.terminals["STRING"] == BaseType("String")
        assert result.terminals["INT"] == BaseType("Int64")
        assert len(result.rules) == 1

    def test_load_with_nonterminal_in_rhs(self):
        """Test that nonterminal types are looked up from rule LHS."""
        config = '''
            (rule (lhs outer String)
                (rhs inner)
                (lambda ((x String)) String (var x String)))
            (rule (lhs inner String)
                (rhs "foo")
                (lambda () String (lit "foo")))
        '''
        result = load_grammar_config(config)
        assert len(result.rules) == 2

    def test_load_duplicate_terminal_error(self):
        """Duplicate terminal declarations are an error."""
        config = '''
            (terminal STRING String)
            (terminal STRING Int64)
        '''
        with pytest.raises(GrammarConversionError, match="duplicate terminal"):
            load_grammar_config(config)

    def test_load_unknown_symbol_error(self):
        """Using undeclared symbol is an error."""
        config = '''
            (rule (lhs name String)
                (rhs UNKNOWN)
                (lambda ((x String)) String (var x String)))
        '''
        with pytest.raises(GrammarConversionError, match="unknown symbol"):
            load_grammar_config(config)


class TestSexpToRhsErrors:
    """Tests for error handling in sexp_to_rhs."""

    def test_empty_list_error(self):
        """Empty list is not a valid RHS."""
        with pytest.raises(GrammarConversionError, match="Invalid RHS expression"):
            sexp_to_rhs(SList(()))

    def test_list_with_quoted_head_error(self):
        """List with quoted head is not valid."""
        with pytest.raises(GrammarConversionError, match="RHS expression must start with a symbol"):
            sexp_to_rhs(SList((SAtom("nonterm", quoted=True), SAtom("foo"))))

    def test_nonterm_wrong_arity_without_context(self):
        """Without context, nonterm requires name and type."""
        with pytest.raises(GrammarConversionError, match="nonterm requires name and type"):
            sexp_to_rhs(parse_sexp("(nonterm foo)"))

    def test_nonterm_inline_type_with_context(self):
        """With context, inline type is allowed as an override."""
        ctx = TypeContext(terminals={}, nonterminals={"foo": BaseType("String")})
        # Inline type overrides context
        result = sexp_to_rhs(parse_sexp("(nonterm foo Int64)"), ctx)
        assert result == Nonterminal("foo", BaseType("Int64"))

    def test_term_wrong_arity_without_context(self):
        """Without context, term requires name and type."""
        with pytest.raises(GrammarConversionError, match="term requires name and type"):
            sexp_to_rhs(parse_sexp("(term INT)"))

    def test_term_inline_type_with_context(self):
        """With context, inline type is allowed as an override."""
        ctx = TypeContext(terminals={"INT": BaseType("Int64")}, nonterminals={})
        # Inline type overrides context
        result = sexp_to_rhs(parse_sexp("(term INT Int32)"), ctx)
        assert result == NamedTerminal("INT", BaseType("Int32"))

    def test_star_wrong_arity(self):
        """star requires exactly 1 argument."""
        with pytest.raises(GrammarConversionError, match="star requires one RHS element"):
            sexp_to_rhs(parse_sexp("(star)"))

    def test_option_wrong_arity(self):
        """option requires exactly 1 argument."""
        with pytest.raises(GrammarConversionError, match="option requires one RHS element"):
            sexp_to_rhs(parse_sexp("(option)"))

    def test_option_invalid_inner(self):
        """option inner must be nonterm or term."""
        with pytest.raises(GrammarConversionError, match="option inner must be nonterm or term"):
            sexp_to_rhs(parse_sexp('(option "literal")'))

    def test_seq_empty(self):
        """seq requires at least one element."""
        with pytest.raises(GrammarConversionError, match="seq requires at least one element"):
            sexp_to_rhs(parse_sexp("(seq)"))


class TestSexpToRuleErrors:
    """Tests for error handling in sexp_to_rule."""

    def test_rule_not_list(self):
        """Rule must be a list."""
        with pytest.raises(GrammarConversionError, match="rule requires"):
            sexp_to_rule(SAtom("foo"))

    def test_rule_wrong_element_count_too_few(self):
        """Rule requires exactly 4 elements."""
        with pytest.raises(GrammarConversionError, match="rule requires"):
            sexp_to_rule(parse_sexp("(rule (lhs foo String) (rhs \"x\"))"))

    def test_rule_head_not_rule(self):
        """Rule head must be 'rule'."""
        with pytest.raises(GrammarConversionError, match="Expected rule"):
            sexp_to_rule(parse_sexp('(notarule (lhs foo String) (rhs "x") (lambda ((x String)) String x))'))

    def test_rule_lhs_not_list(self):
        """Rule lhs must be a list."""
        with pytest.raises(GrammarConversionError, match="lhs requires name and type"):
            sexp_to_rule(parse_sexp('(rule foo (rhs "x") (lambda ((x String)) String x))'))

    def test_rule_lhs_wrong_element_count(self):
        """Rule lhs must have exactly 3 elements."""
        with pytest.raises(GrammarConversionError, match="lhs requires name and type"):
            sexp_to_rule(parse_sexp('(rule (lhs foo) (rhs "x") (lambda ((x String)) String x))'))

    def test_rule_lhs_head_not_lhs(self):
        """Rule lhs head must be 'lhs'."""
        with pytest.raises(GrammarConversionError, match="Expected \\(lhs ...\\)"):
            sexp_to_rule(parse_sexp('(rule (notlhs foo String) (rhs "x") (lambda ((x String)) String x))'))

    def test_rule_rhs_not_list(self):
        """Rule rhs must be a list."""
        with pytest.raises(GrammarConversionError, match="rhs must be a list"):
            sexp_to_rule(parse_sexp('(rule (lhs foo String) notalist (lambda ((x String)) String x))'))

    def test_rule_rhs_empty_list(self):
        """Rule rhs must be a non-empty list."""
        with pytest.raises(GrammarConversionError, match="rhs must be a list"):
            sexp_to_rule(parse_sexp('(rule (lhs foo String) () (lambda ((x String)) String x))'))

    def test_rule_rhs_head_not_rhs(self):
        """Rule rhs head must be 'rhs'."""
        with pytest.raises(GrammarConversionError, match="Expected \\(rhs ...\\)"):
            sexp_to_rule(parse_sexp('(rule (lhs foo String) (notrhs "x") (lambda ((x String)) String x))'))


class TestExpectSymbolErrors:
    """Tests for _expect_symbol error handling."""

    def test_expect_symbol_non_atom(self):
        """_expect_symbol requires an atom."""
        from meta.sexp_grammar import _expect_symbol
        with pytest.raises(GrammarConversionError, match="must be a symbol"):
            _expect_symbol(SList((SAtom("foo"),)), "test")

    def test_expect_symbol_quoted(self):
        """_expect_symbol requires unquoted symbol."""
        from meta.sexp_grammar import _expect_symbol
        with pytest.raises(GrammarConversionError, match="must be unquoted symbol"):
            _expect_symbol(SAtom("foo", quoted=True), "test")

    def test_expect_symbol_non_string(self):
        """_expect_symbol requires string value."""
        from meta.sexp_grammar import _expect_symbol
        with pytest.raises(GrammarConversionError, match="must be a symbol"):
            _expect_symbol(SAtom(123), "test")


class TestLoadGrammarConfigErrors:
    """Tests for load_grammar_config error handling."""

    def test_load_invalid_top_level_atom(self):
        """Top-level atoms are invalid."""
        with pytest.raises(GrammarConversionError, match="Invalid config directive"):
            load_grammar_config("foo")

    def test_load_invalid_top_level_list_no_head(self):
        """Top-level lists must have a symbol head."""
        with pytest.raises(GrammarConversionError, match="Config directive must start with symbol"):
            load_grammar_config('(("nested") foo)')


class TestRhsToSexpErrors:
    """Tests for rhs_to_sexp error handling."""

    def test_unknown_rhs_type(self):
        """Unknown RHS type raises error."""
        # Create a custom RHS type that doesn't match any known types
        class FakeRhs:
            pass
        with pytest.raises(GrammarConversionError, match="Unknown RHS type"):
            rhs_to_sexp(FakeRhs())


class TestLoadGrammarConfigFile:
    """Tests for load_grammar_config_file function."""

    def test_load_grammar_from_file(self):
        """Load grammar from file path."""
        import tempfile
        from pathlib import Path
        from meta.sexp_grammar import load_grammar_config_file

        config_text = '''
        (terminal STRING String)
        (rule
          (lhs test String)
          (rhs STRING)
          (lambda ((x String)) String (var x String)))
        '''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sexp', delete=False) as f:
            f.write(config_text)
            f.flush()
            path = Path(f.name)

        try:
            result = load_grammar_config_file(path)
            assert len(result.rules) == 1
            assert len(result.terminals) == 1
        finally:
            path.unlink()
