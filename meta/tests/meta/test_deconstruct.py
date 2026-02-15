#!/usr/bin/env python3
"""Tests for parse_deconstruct_action validation."""

import pytest

from meta.target import (
    BaseType, MessageType, TupleType, SequenceType, ListType, OptionType,
    Var, Call, Lambda, GetField, IfElse, Seq,
)
from meta.grammar import (
    Nonterminal, LitTerminal, NamedTerminal, Star, Option, Sequence,
)
from meta.yacc_action_parser import (
    parse_deconstruct_action, TypeContext, YaccGrammarError,
)


@pytest.fixture
def ctx():
    """Minimal TypeContext for testing."""
    return TypeContext()


# -- Helpers for building RHS patterns --

def _msg_type(name: str) -> MessageType:
    return MessageType("proto", name)


def _nonterminal(name: str, t=None) -> Nonterminal:
    return Nonterminal(name, t or BaseType("String"))


def _seq(*elems) -> Sequence:
    return Sequence(tuple(elems))


# ============================================================================
# Identity deconstruct
# ============================================================================

class TestIdentityDeconstruct:

    def test_identity_returns_param(self, ctx):
        """'$$' with no guard returns the input unchanged."""
        lhs_type = _msg_type("Foo")
        rhs = _nonterminal("foo", lhs_type)
        result = parse_deconstruct_action("$$", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)
        assert len(result.params) == 1
        assert result.params[0].type == lhs_type
        # Body is the parameter itself
        assert isinstance(result.body, Var)
        assert result.body.name == "_dollar_dollar"

    def test_identity_with_guard_is_not_identity(self, ctx):
        """'$$' with a guard is NOT treated as identity shortcut."""
        lhs_type = _msg_type("Foo")
        # All-literal RHS so no $N assignments are needed
        rhs = _seq(LitTerminal("("), LitTerminal("foo"), LitTerminal(")"))
        result = parse_deconstruct_action("$$", lhs_type, rhs, ctx, guard="True")
        # With a guard, the body wraps in IfElse, not a plain identity Var
        assert isinstance(result.body, IfElse)


# ============================================================================
# Simple field extraction
# ============================================================================

class TestSimpleFieldExtraction:

    def test_single_assignment(self, ctx):
        """Single $1 assignment extracts one field."""
        lhs_type = _msg_type("Wrapper")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String") if fn == "name" else None
        result = parse_deconstruct_action("$2 = $$.name", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)
        assert len(result.params) == 1
        assert isinstance(result.body, GetField)

    def test_two_assignments(self, ctx):
        """Two $N assignments produce a tuple body."""
        lhs_type = _msg_type("Pair")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("first", BaseType("String")),
            _nonterminal("second", BaseType("Int64")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: {
            "a": BaseType("String"),
            "b": BaseType("Int64"),
        }.get(fn)
        result = parse_deconstruct_action("$2 = $$.a; $3 = $$.b", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)
        # Two assignments -> tuple via builtin
        assert isinstance(result.body, Call)

    def test_assignments_out_of_order(self, ctx):
        """Assignments can appear in any order."""
        lhs_type = _msg_type("Pair")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("first", BaseType("String")),
            _nonterminal("second", BaseType("Int64")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: {
            "a": BaseType("String"),
            "b": BaseType("Int64"),
        }.get(fn)
        # $3 before $2
        result = parse_deconstruct_action("$3 = $$.b; $2 = $$.a", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)


# ============================================================================
# Validation: missing / extra assignments
# ============================================================================

class TestAssignmentValidation:

    def test_missing_assignment_errors(self, ctx):
        """Omitting a required $N assignment raises YaccGrammarError."""
        lhs_type = _msg_type("Pair")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("first", BaseType("String")),
            _nonterminal("second", BaseType("Int64")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        with pytest.raises(YaccGrammarError, match=r"missing assignments"):
            parse_deconstruct_action("$2 = $$.a", lhs_type, rhs, ctx)

    def test_extra_assignment_errors(self, ctx):
        """Assigning to a $N that doesn't correspond to a non-literal RHS element errors."""
        lhs_type = _msg_type("Single")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        with pytest.raises(YaccGrammarError, match=r"non-existent RHS elements"):
            parse_deconstruct_action("$2 = $$.a; $4 = $$.b", lhs_type, rhs, ctx)

    def test_literal_position_not_assignable(self, ctx):
        """Assigning to a literal position (e.g., $1 when position 1 is '(') errors."""
        lhs_type = _msg_type("Wrapper")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        # $1 is LitTerminal("("), so it's not a non-literal element
        with pytest.raises(YaccGrammarError, match=r"non-existent RHS elements"):
            parse_deconstruct_action("$1 = $$.a; $2 = $$.b", lhs_type, rhs, ctx)


# ============================================================================
# Type annotations
# ============================================================================

class TestTypeAnnotations:

    def test_compatible_annotation_accepted(self, ctx):
        """Type annotation that is a subtype of the RHS element type is accepted."""
        lhs_type = _msg_type("Wrapper")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        # Annotate $2 as String (matches Nonterminal type)
        result = parse_deconstruct_action("$2: String = $$.name", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)

    def test_incompatible_annotation_errors(self, ctx):
        """Type annotation incompatible with RHS element type raises error."""
        lhs_type = _msg_type("Wrapper")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("Int64")
        with pytest.raises(YaccGrammarError, match=r"Type annotation"):
            parse_deconstruct_action("$2: Int64 = $$.name", lhs_type, rhs, ctx)

    def test_list_annotation(self, ctx):
        """List[T] annotation on a List-typed RHS element is accepted."""
        lhs_type = _msg_type("Container")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("items", ListType(BaseType("String"))),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: ListType(BaseType("String"))
        result = parse_deconstruct_action(
            "$2: List[String] = $$.items", lhs_type, rhs, ctx
        )
        assert isinstance(result, Lambda)

    def test_sequence_annotation_on_sequence_rhs(self, ctx):
        """Sequence[T] annotation on a Sequence-typed RHS element is accepted."""
        lhs_type = _msg_type("Container")
        inner_nt = _nonterminal("item", BaseType("String"))
        rhs = _seq(
            LitTerminal("("),
            Star(inner_nt),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: SequenceType(BaseType("String"))
        result = parse_deconstruct_action(
            "$2: Sequence[String] = $$.items", lhs_type, rhs, ctx
        )
        assert isinstance(result, Lambda)


# ============================================================================
# Guard expressions
# ============================================================================

class TestGuardExpressions:

    def test_guard_wraps_in_option(self, ctx):
        """A guard expression wraps the result in Option (IfElse with None fallback)."""
        lhs_type = _msg_type("Wrapper")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        result = parse_deconstruct_action(
            "$2 = $$.name", lhs_type, rhs, ctx, guard="True"
        )
        assert isinstance(result, Lambda)
        assert isinstance(result.return_type, OptionType)
        assert isinstance(result.body, IfElse)

    def test_guard_references_dollar_dollar(self, ctx):
        """Guard can reference $$ (the input message)."""
        lhs_type = _msg_type("Wrapper")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        result = parse_deconstruct_action(
            "$2 = $$.name", lhs_type, rhs, ctx, guard="$$.name == 'foo'"
        )
        assert isinstance(result, Lambda)
        assert isinstance(result.return_type, OptionType)

    def test_guard_syntax_error(self, ctx):
        """Invalid guard syntax raises YaccGrammarError."""
        lhs_type = _msg_type("Wrapper")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        with pytest.raises(YaccGrammarError, match=r"Syntax error in deconstruct guard"):
            parse_deconstruct_action(
                "$2 = $$.name", lhs_type, rhs, ctx, guard="if =="
            )

    def test_guard_with_multiple_assignments(self, ctx):
        """Guard with multiple assignments wraps a tuple in Option."""
        lhs_type = _msg_type("Pair")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("a", BaseType("String")),
            _nonterminal("b", BaseType("Int64")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: {
            "x": BaseType("String"),
            "y": BaseType("Int64"),
        }.get(fn)
        result = parse_deconstruct_action(
            "$2 = $$.x; $3 = $$.y", lhs_type, rhs, ctx, guard="True"
        )
        assert isinstance(result.return_type, OptionType)
        inner = result.return_type.element_type
        assert isinstance(inner, TupleType)
        assert len(inner.elements) == 2


# ============================================================================
# Side-effect expressions
# ============================================================================

class TestSideEffects:

    def test_side_effect_with_assignment(self, ctx):
        """Side-effect expressions are allowed alongside $N assignments."""
        lhs_type = _msg_type("Wrapper")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        # some_builtin($$.name) is a side effect, $2 = $$.name is the assignment
        result = parse_deconstruct_action(
            "length($$.name)\n$2 = $$.name", lhs_type, rhs, ctx
        )
        assert isinstance(result, Lambda)
        # Body should be Seq wrapping side-effect + result
        assert isinstance(result.body, Seq)


# ============================================================================
# Error cases
# ============================================================================

class TestErrorCases:

    def test_syntax_error(self, ctx):
        """Invalid Python syntax raises YaccGrammarError."""
        lhs_type = _msg_type("Foo")
        rhs = _nonterminal("foo", BaseType("String"))
        with pytest.raises(YaccGrammarError, match=r"Syntax error"):
            parse_deconstruct_action("$1 = =bad", lhs_type, rhs, ctx)

    def test_assert_no_longer_supported(self, ctx):
        """assert in deconstruct action raises error."""
        lhs_type = _msg_type("Foo")
        rhs = _nonterminal("foo", BaseType("String"))
        with pytest.raises(YaccGrammarError, match=r"assert.*no longer supported"):
            parse_deconstruct_action("assert True\n$1 = $$.name", lhs_type, rhs, ctx)

    def test_unsupported_statement(self, ctx):
        """Unsupported statement types (e.g., for loop) raise error."""
        lhs_type = _msg_type("Foo")
        rhs = _nonterminal("foo", BaseType("String"))
        with pytest.raises(YaccGrammarError, match=r"must be"):
            parse_deconstruct_action(
                "for x in []: pass\n$1 = $$.name", lhs_type, rhs, ctx
            )

    def test_pass_is_ignored(self, ctx):
        """'pass' statements are silently ignored."""
        lhs_type = _msg_type("Wrapper")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        result = parse_deconstruct_action("pass\n$2 = $$.name", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)

    def test_unknown_field(self, ctx):
        """Accessing a field that doesn't exist on the message type raises error."""
        lhs_type = _msg_type("Foo")
        rhs = _seq(
            LitTerminal("("),
            _nonterminal("inner", BaseType("String")),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: None
        with pytest.raises(YaccGrammarError, match=r"Unknown field"):
            parse_deconstruct_action("$2 = $$.nonexistent", lhs_type, rhs, ctx)


# ============================================================================
# RHS patterns: Star, Option
# ============================================================================

class TestRhsPatterns:

    def test_star_rhs_element(self, ctx):
        """Deconstruct with Star RHS element validates correctly."""
        lhs_type = _msg_type("ListHolder")
        inner_nt = _nonterminal("item", BaseType("String"))
        rhs = _seq(
            LitTerminal("("),
            Star(inner_nt),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: SequenceType(BaseType("String"))
        result = parse_deconstruct_action("$2 = $$.items", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)

    def test_option_rhs_element(self, ctx):
        """Deconstruct with Option RHS element validates correctly."""
        lhs_type = _msg_type("OptHolder")
        inner_nt = _nonterminal("maybe", BaseType("String"))
        rhs = _seq(
            LitTerminal("("),
            Option(inner_nt),
            LitTerminal(")"),
        )
        ctx.field_type_lookup = lambda mt, fn: OptionType(BaseType("String"))
        result = parse_deconstruct_action("$2 = $$.maybe", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)

    def test_bare_nonterminal_rhs(self, ctx):
        """Deconstruct on a rule with a single non-sequence RHS nonterminal."""
        lhs_type = _msg_type("Alias")
        rhs = _nonterminal("target", BaseType("String"))
        ctx.field_type_lookup = lambda mt, fn: BaseType("String")
        result = parse_deconstruct_action("$1 = $$.value", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)
        assert isinstance(result.body, GetField)

    def test_bare_terminal_rhs(self, ctx):
        """Deconstruct on a rule with a single NamedTerminal RHS."""
        lhs_type = BaseType("String")
        rhs = NamedTerminal("SYMBOL", BaseType("String"))
        result = parse_deconstruct_action("$1 = $$", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)

    def test_all_literals_no_assignments_needed(self, ctx):
        """When RHS is all literals, no assignments needed."""
        lhs_type = _msg_type("Keyword")
        rhs = _seq(LitTerminal("("), LitTerminal("keyword"), LitTerminal(")"))
        # Empty action text would be identity, but let's test with 'pass'
        result = parse_deconstruct_action("pass", lhs_type, rhs, ctx)
        assert isinstance(result, Lambda)
