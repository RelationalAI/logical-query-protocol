"""Tests that substitution preserves typing.

The result of substitution should have a type that is a subtype of the original
expression's type. This ensures type soundness of the substitution operation.
"""

from meta.target import (
    BaseType, ListType, OptionType, TupleType, FunctionType, MessageType,
    Var, Lit, Call, Builtin, Lambda, Let, IfElse, Seq,
    TargetType, TargetExpr,
)
from meta.target_builtins import make_builtin
from meta.target_utils import subst, is_subtype, STRING_TYPE, INT64_TYPE, BOOLEAN_TYPE


def _make_builtin(name: str, return_type: TargetType) -> Builtin:
    """Create a builtin with specified return type."""
    return Builtin(name, FunctionType([], return_type))


class TestSubstPreservesTyping:
    """Tests that subst(expr, mapping).target_type() <: expr.target_type()."""

    def test_var_substitution_same_type(self):
        """Substituting a var with same-typed value preserves type."""
        expr = Var('x', STRING_TYPE)
        result = subst(expr, {'x': Lit("hello")})
        assert is_subtype(result.target_type(), expr.target_type())

    def test_var_substitution_subtype(self):
        """Substituting with a subtype preserves typing."""
        any_type = BaseType("Any")
        expr = Var('x', any_type)
        result = subst(expr, {'x': Lit(42)})
        # Int64 <: Any, so result type (Int64) <: original type (Any)
        assert is_subtype(result.target_type(), expr.target_type())

    def test_call_preserves_type(self):
        """Substituting in Call arguments preserves call type."""
        builtin = _make_builtin('concat', STRING_TYPE)
        expr = Call(builtin, [Var('x', STRING_TYPE), Var('y', STRING_TYPE)])
        result = subst(expr, {'x': Lit("hello"), 'y': Lit("world")})
        assert is_subtype(result.target_type(), expr.target_type())

    def test_let_preserves_body_type(self):
        """Let expression type is determined by body, preserved after subst."""
        x = Var('x', INT64_TYPE)
        y = Var('y', STRING_TYPE)
        expr = Let(x, Lit(1), y)
        result = subst(expr, {'y': Lit("hello")})
        assert is_subtype(result.target_type(), expr.target_type())

    def test_ifelse_preserves_branch_type(self):
        """IfElse type comes from branches, preserved after subst."""
        expr = IfElse(
            Var('cond', BOOLEAN_TYPE),
            Var('x', INT64_TYPE),
            Lit(0)
        )
        result = subst(expr, {'cond': Lit(True), 'x': Lit(42)})
        assert is_subtype(result.target_type(), expr.target_type())

    def test_seq_preserves_last_expr_type(self):
        """Seq type comes from last expression, preserved after subst."""
        expr = Seq([Var('x', STRING_TYPE), Var('y', INT64_TYPE)])
        result = subst(expr, {'x': Lit("hello"), 'y': Lit(42)})
        assert is_subtype(result.target_type(), expr.target_type())

    def test_lambda_body_substitution_preserves_type(self):
        """Substituting free vars in lambda body preserves lambda type."""
        param = Var('x', INT64_TYPE)
        free_var = Var('y', STRING_TYPE)
        body = Call(_make_builtin('f', INT64_TYPE), [param, free_var])
        expr = Lambda([param], INT64_TYPE, body)
        result = subst(expr, {'y': Lit("hello")})
        assert is_subtype(result.target_type(), expr.target_type())

    def test_nested_substitution_preserves_type(self):
        """Nested expressions preserve typing after substitution."""
        inner = Call(_make_builtin('inner', INT64_TYPE), [Var('x', INT64_TYPE)])
        outer = Call(_make_builtin('outer', STRING_TYPE), [inner])
        result = subst(outer, {'x': Lit(42)})
        assert is_subtype(result.target_type(), outer.target_type())

    def test_list_type_preserved(self):
        """List expressions preserve element type after substitution."""
        from meta.target import ListExpr
        expr = ListExpr([Var('x', STRING_TYPE)], STRING_TYPE)
        result = subst(expr, {'x': Lit("hello")})
        assert is_subtype(result.target_type(), expr.target_type())

    def test_multiple_substitutions_preserve_type(self):
        """Multiple simultaneous substitutions preserve type."""
        builtin = _make_builtin('f', BOOLEAN_TYPE)
        expr = Call(builtin, [
            Var('a', INT64_TYPE),
            Var('b', STRING_TYPE),
            Var('c', BOOLEAN_TYPE)
        ])
        result = subst(expr, {
            'a': Lit(1),
            'b': Lit("hello"),
            'c': Lit(True)
        })
        assert is_subtype(result.target_type(), expr.target_type())

    def test_partial_substitution_preserves_type(self):
        """Partial substitution (some vars remain) preserves type."""
        builtin = _make_builtin('f', INT64_TYPE)
        expr = Call(builtin, [Var('x', INT64_TYPE), Var('y', INT64_TYPE)])
        result = subst(expr, {'x': Lit(42)})
        assert is_subtype(result.target_type(), expr.target_type())

    def test_no_substitution_preserves_type(self):
        """Empty substitution preserves type exactly."""
        expr = Call(_make_builtin('f', STRING_TYPE), [Var('x', INT64_TYPE)])
        result = subst(expr, {})
        assert result.target_type() == expr.target_type()

    def test_shadowed_var_not_substituted(self):
        """Shadowed variables are not substituted, type preserved."""
        x = Var('x', INT64_TYPE)
        expr = Let(x, Lit(1), x)
        # x in body is shadowed by let binding, should not be substituted
        result = subst(expr, {'x': Lit(999)})
        assert is_subtype(result.target_type(), expr.target_type())


class TestSubstTypeErrors:
    """Tests that subst raises when val type is not a subtype of var type."""

    def test_incompatible_base_types_raises(self):
        """Substituting Int64 var with String value raises."""
        expr = Var('x', INT64_TYPE)
        import pytest
        with pytest.raises(AssertionError, match="Type mismatch"):
            subst(expr, {'x': Lit("wrong type")})

    def test_supertype_not_allowed(self):
        """Substituting with supertype raises (Any is not subtype of Int64)."""
        expr = Var('x', INT64_TYPE)
        # Create a value with Any type - Any is supertype of Int64, not subtype
        any_type = BaseType("Any")
        any_val = Call(Builtin('get_any', FunctionType([], any_type)), [])
        import pytest
        with pytest.raises(AssertionError, match="Type mismatch"):
            subst(expr, {'x': any_val})

    def test_list_element_type_mismatch_raises(self):
        """Substituting list var with wrong element type raises."""
        list_type = ListType(INT64_TYPE)
        expr = Var('xs', list_type)
        from meta.target import ListExpr
        import pytest
        with pytest.raises(AssertionError, match="Type mismatch"):
            subst(expr, {'xs': ListExpr([], STRING_TYPE)})

    def test_option_element_type_mismatch_raises(self):
        """Substituting Option[Int64] var with Option[String] raises."""
        opt_int = OptionType(INT64_TYPE)
        opt_str = OptionType(STRING_TYPE)
        expr = Var('x', opt_int)
        # Create an Option[String] value
        some_builtin = Builtin('some', FunctionType([STRING_TYPE], opt_str))
        val = Call(some_builtin, [Lit("hello")])
        import pytest
        with pytest.raises(AssertionError, match="Type mismatch"):
            subst(expr, {'x': val})

    def test_nested_call_type_mismatch_raises(self):
        """Type mismatch in nested expression raises."""
        builtin = Builtin('f', FunctionType([], STRING_TYPE))
        expr = Call(builtin, [Var('x', INT64_TYPE), Var('y', INT64_TYPE)])
        import pytest
        with pytest.raises(AssertionError, match="Type mismatch"):
            # x expects Int64, giving String
            subst(expr, {'x': Lit("wrong")})
