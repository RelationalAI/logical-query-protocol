"""Tests for target_utils module."""

import pytest
from meta.target import (
    BaseType, MessageType, ListType, OptionType, TupleType, DictType, FunctionType,
    Var, Lit, Call, Builtin, Lambda, Let, IfElse, Seq, While,
    Return, Assign, GetField, GetElement,
    TargetType,
)
from meta.target_builtins import make_builtin
from meta.target_utils import (
    STRING_TYPE, INT64_TYPE, FLOAT64_TYPE, BOOLEAN_TYPE,
    create_identity_function, subst, type_join,
    make_equal, make_which_oneof, make_get_field, make_some,
    make_tuple, make_get_element, make_is_empty, make_concat,
    make_length, make_unwrap_option_or, apply_lambda
)

# Dummy type for test builtins
_ANY = BaseType("Any")
_DUMMY_FN_TYPE = FunctionType([], _ANY)


def _test_builtin(name: str, return_type: TargetType = _ANY) -> Builtin:
    """Create a test builtin with specified return type (default Any)."""
    return Builtin(name, FunctionType([], return_type))


class TestCommonTypes:
    """Test common type constants."""

    def test_string_type(self):
        assert STRING_TYPE == BaseType('String')

    def test_int64_type(self):
        assert INT64_TYPE == BaseType('Int64')

    def test_float64_type(self):
        assert FLOAT64_TYPE == BaseType('Float64')

    def test_boolean_type(self):
        assert BOOLEAN_TYPE == BaseType('Boolean')


class TestCreateIdentityFunction:
    """Test identity function creation."""

    def test_identity_string(self):
        func = create_identity_function(STRING_TYPE)
        assert isinstance(func, Lambda)
        assert len(func.params) == 1
        assert func.params[0].name == 'x'
        assert func.params[0].type == STRING_TYPE
        assert func.return_type == STRING_TYPE
        assert func.body == Var('x', STRING_TYPE)

    def test_identity_int64(self):
        func = create_identity_function(INT64_TYPE)
        assert isinstance(func, Lambda)
        assert func.params[0].type == INT64_TYPE
        assert func.return_type == INT64_TYPE

    def test_identity_message_type(self):
        msg_type = MessageType('test', 'Foo')
        func = create_identity_function(msg_type)
        assert func.params[0].type == msg_type
        assert func.return_type == msg_type


class TestSubstitution:
    """Test variable substitution."""

    def test_subst_empty_mapping(self):
        """Substitution with empty mapping returns original expression."""
        expr = Var('x', STRING_TYPE)
        result = subst(expr, {})
        assert result == expr

    def test_subst_simple_var(self):
        """Substitute a variable with a literal."""
        expr = Var('x', STRING_TYPE)
        result = subst(expr, {'x': Lit("hello")})
        assert result == Lit("hello")

    def test_subst_var_not_in_mapping(self):
        """Variable not in mapping is unchanged."""
        expr = Var('y', STRING_TYPE)
        result = subst(expr, {'x': Lit("hello")})
        assert result == expr

    def test_subst_in_call(self):
        """Substitute variable in call arguments."""
        expr = Call(_test_builtin('print'), [Var('x', STRING_TYPE)])
        result = subst(expr, {'x': Lit("hello")})
        assert isinstance(result, Call)
        assert result.args[0] == Lit("hello")

    def test_subst_single_occurrence_side_effect(self):
        """Single occurrence with side effect substitutes directly."""
        expr = Var('x', STRING_TYPE)
        # Call has potential side effects
        replacement = Call(_test_builtin('get_value', STRING_TYPE), [])
        result = subst(expr, {'x': replacement})
        assert result == replacement

    def test_subst_multiple_occurrences_simple(self):
        """Multiple occurrences of simple value substitutes directly."""
        expr = Call(_test_builtin('concat'), [Var('x', STRING_TYPE), Var('x', STRING_TYPE)])
        result = subst(expr, {'x': Lit("hello")})
        assert isinstance(result, Call)
        assert result.args[0] == Lit("hello")
        assert result.args[1] == Lit("hello")

    def test_subst_multiple_occurrences_side_effect(self):
        """Multiple occurrences with side effect introduces Let binding."""
        expr = Call(_test_builtin('concat'), [Var('x', STRING_TYPE), Var('x', STRING_TYPE)])
        replacement = Call(_test_builtin('get_value', STRING_TYPE), [])
        result = subst(expr, {'x': replacement})
        # Should wrap in Let to avoid duplicating side effect
        assert isinstance(result, Let)
        assert result.init == replacement
        # Body should have the substituted vars
        assert isinstance(result.body, Call)

    def test_subst_in_lambda_no_shadow(self):
        """Substitute in lambda body when parameter doesn't shadow."""
        x_var = Var('x', STRING_TYPE)
        y_var = Var('y', INT64_TYPE)
        expr = Lambda([x_var], STRING_TYPE, Call(_test_builtin('f'), [x_var, y_var]))
        result = subst(expr, {'y': Lit(42)})
        assert isinstance(result, Lambda)
        assert isinstance(result.body, Call)
        assert result.body.args[1] == Lit(42)

    def test_subst_in_lambda_with_shadow(self):
        """Parameter shadows variable in mapping."""
        x_var = Var('x', STRING_TYPE)
        expr = Lambda([x_var], STRING_TYPE, x_var)
        result = subst(expr, {'x': Lit("hello")})
        # Lambda parameter shadows, so body should still reference x
        assert isinstance(result, Lambda)
        assert result.body == x_var

    def test_subst_in_let(self):
        """Substitute in Let expression."""
        x_var = Var('x', STRING_TYPE)
        y_var = Var('y', STRING_TYPE)
        expr = Let(x_var, Lit("foo"), y_var)
        result = subst(expr, {'y': Lit("bar")})
        assert isinstance(result, Let)
        assert result.body == Lit("bar")

    def test_subst_in_let_shadowing(self):
        """Let variable shadows mapping."""
        x_var = Var('x', STRING_TYPE)
        expr = Let(x_var, Var('y', STRING_TYPE), x_var)
        result = subst(expr, {'x': Lit("shadowed"), 'y': Lit("init")})
        assert isinstance(result, Let)
        assert result.init == Lit("init")
        assert result.body == x_var  # Shadowed

    def test_subst_in_ifelse(self):
        """Substitute in IfElse branches."""
        x_var = Var('x', INT64_TYPE)
        expr = IfElse(
            Var('cond', BOOLEAN_TYPE),
            x_var,
            Lit(0)
        )
        result = subst(expr, {'x': Lit(42), 'cond': Lit(True)})
        assert isinstance(result, IfElse)
        assert result.condition == Lit(True)
        assert result.then_branch == Lit(42)
        assert result.else_branch == Lit(0)

    def test_subst_in_seq(self):
        """Substitute in sequence."""
        x_var = Var('x', INT64_TYPE)
        expr = Seq([x_var, x_var])
        result = subst(expr, {'x': Lit(42)})
        assert isinstance(result, Seq)
        assert result.exprs[0] == Lit(42)
        assert result.exprs[1] == Lit(42)

    def test_subst_in_while(self):
        """Substitute in while loop."""
        x_var = Var('x', BOOLEAN_TYPE)
        y_var = Var('y', INT64_TYPE)
        expr = While(x_var, y_var)
        result = subst(expr, {'x': Lit(True), 'y': Lit(42)})
        assert isinstance(result, While)
        assert result.condition == Lit(True)
        assert result.body == Lit(42)

    def test_subst_in_return(self):
        """Substitute in return statement."""
        x_var = Var('x', INT64_TYPE)
        expr = Return(x_var)
        result = subst(expr, {'x': Lit(42)})
        assert isinstance(result, Return)
        assert result.expr == Lit(42)

    def test_subst_in_assign(self):
        """Substitute in assignment."""
        x_var = Var('x', INT64_TYPE)
        y_var = Var('y', INT64_TYPE)
        expr = Assign(x_var, y_var)
        result = subst(expr, {'y': Lit(42)})
        assert isinstance(result, Assign)
        assert result.expr == Lit(42)

    def test_subst_preserves_other_exprs(self):
        """Literals and other expressions without variables are preserved."""
        expr = Lit(42)
        result = subst(expr, {'x': Lit(100)})
        assert result == expr


class TestBuiltinHelpers:
    """Test builtin helper functions."""

    def test_make_equal(self):
        left = Var('x', INT64_TYPE)
        right = Lit(42)
        result = make_equal(left, right)
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin)
        assert result.func.name == 'equal'
        assert result.args == (left, right)

    def test_make_which_oneof(self):
        msg = Var('msg', MessageType('test', 'Foo'))
        oneof_name = 'field'
        result = make_which_oneof(msg, oneof_name)
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin)
        assert result.func.name == 'which_one_of'
        assert result.args == (msg, oneof_name)

    def test_make_get_field_with_string(self):
        msg_type = MessageType('test', 'Foo')
        field_type = BaseType('String')
        obj = Var('obj', msg_type)
        result = make_get_field(obj, 'field_name', msg_type, field_type)
        assert isinstance(result, GetField)
        assert result.object == obj
        assert result.field_name == 'field_name'
        assert result.message_type == msg_type
        assert result.field_type == field_type

    def test_make_get_field_with_lit(self):
        """GetField unwraps Lit field names."""
        msg_type = MessageType('test', 'Foo')
        field_type = BaseType('Int64')
        obj = Var('obj', msg_type)
        result = make_get_field(obj, Lit('field_name'), msg_type, field_type)
        assert isinstance(result, GetField)
        assert result.field_name == 'field_name'
        assert result.message_type == msg_type
        assert result.field_type == field_type

    def test_make_some(self):
        value = Lit(42)
        result = make_some(value)
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin)
        assert result.func.name == 'some'
        assert result.args == (value,)

    def test_make_tuple(self):
        result = make_tuple(Lit(1), Lit(2), Lit(3))
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin)
        assert result.func.name == 'tuple'
        assert len(result.args) == 3

    def test_make_get_element(self):
        tuple_expr = Var('t', TupleType([INT64_TYPE, STRING_TYPE]))
        result = make_get_element(tuple_expr, 0)
        assert isinstance(result, GetElement)
        assert result.tuple_expr == tuple_expr
        assert result.index == 0

    def test_make_is_empty(self):
        collection = Var('items', ListType(STRING_TYPE))
        result = make_is_empty(collection)
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin)
        assert result.func.name == 'is_empty'
        assert result.args == (collection,)

    def test_make_concat(self):
        left = Var('list1', ListType(INT64_TYPE))
        right = Var('list2', ListType(INT64_TYPE))
        result = make_concat(left, right)
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin)
        assert result.func.name == 'list_concat'
        assert result.args == (left, right)

    def test_make_length(self):
        collection = Var('items', ListType(STRING_TYPE))
        result = make_length(collection)
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin)
        assert result.func.name == 'length'
        assert result.args == (collection,)

    def test_make_unwrap_option_or(self):
        option = Var('opt', OptionType(INT64_TYPE))
        default = Lit(0)
        result = make_unwrap_option_or(option, default)
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin)
        assert result.func.name == 'unwrap_option_or'
        assert result.args == (option, default)


class TestApplyLambda:
    """Test lambda application."""

    def test_apply_lambda_no_params_no_args(self):
        """Lambda with no parameters returns body directly."""
        body = Lit(42)
        func = Lambda([], INT64_TYPE, body)
        result = apply_lambda(func, [])
        assert result == body

    def test_apply_lambda_single_param_var(self):
        """Lambda with single Var argument substitutes directly."""
        param = Var('x', INT64_TYPE)
        func = Lambda([param], INT64_TYPE, param)
        arg = Var('y', INT64_TYPE)
        result = apply_lambda(func, [arg])
        assert result == arg

    def test_apply_lambda_single_param_lit(self):
        """Lambda with single Lit argument substitutes directly."""
        param = Var('x', INT64_TYPE)
        func = Lambda([param], INT64_TYPE, param)
        arg = Lit(42)
        result = apply_lambda(func, [arg])
        assert result == arg

    def test_apply_lambda_single_param_call(self):
        """Lambda with Call argument introduces Let binding."""
        param = Var('x', INT64_TYPE)
        func = Lambda([param], INT64_TYPE, param)
        arg = Call(_test_builtin('f'), [])
        result = apply_lambda(func, [arg])
        assert isinstance(result, Let)
        assert result.var == param
        assert result.init == arg

    def test_apply_lambda_multiple_params_all_simple(self):
        """Multiple parameters with simple arguments."""
        x = Var('x', INT64_TYPE)
        y = Var('y', INT64_TYPE)
        func = Lambda([x, y], INT64_TYPE, Call(_test_builtin('add'), [x, y]))
        result = apply_lambda(func, [Lit(1), Lit(2)])
        # Should substitute both
        assert isinstance(result, Call)
        assert result.args[0] == Lit(1)
        assert result.args[1] == Lit(2)

    def test_apply_lambda_multiple_params_with_call(self):
        """Multiple parameters with non-simple arguments."""
        x = Var('x', INT64_TYPE)
        y = Var('y', INT64_TYPE)
        func = Lambda([x, y], INT64_TYPE, Call(_test_builtin('add'), [x, y]))
        call_arg = Call(_test_builtin('f'), [])
        result = apply_lambda(func, [call_arg, Lit(2)])
        # Should introduce Let for first arg
        assert isinstance(result, Let)
        assert result.init == call_arg

    def test_apply_lambda_partial_application(self):
        """Lambda with fewer arguments returns Call."""
        x = Var('x', INT64_TYPE)
        y = Var('y', INT64_TYPE)
        func = Lambda([x, y], INT64_TYPE, Call(_test_builtin('add'), [x, y]))
        result = apply_lambda(func, [])
        assert isinstance(result, Call)
        assert result.func == func
        assert result.args == ()

    def test_apply_lambda_body_uses_param_multiple_times(self):
        """Lambda body uses parameter multiple times."""
        x = Var('x', INT64_TYPE)
        func = Lambda([x], INT64_TYPE, Call(_test_builtin('add'), [x, x]))
        result = apply_lambda(func, [Lit(5)])
        # Should substitute literal directly even with multiple uses
        assert isinstance(result, Call)
        assert result.args == (Lit(5), Lit(5))


class TestIsSimpleExpr:
    """Test _is_simple_expr helper (indirectly through subst)."""

    def test_var_is_simple(self):
        """Var is simple - no Let needed for multiple uses."""
        expr = Call(_test_builtin('f'), [Var('x', INT64_TYPE), Var('x', INT64_TYPE)])
        result = subst(expr, {'x': Var('y', INT64_TYPE)})
        # Should substitute directly without Let
        assert isinstance(result, Call)
        assert not isinstance(result, Let)

    def test_lit_is_simple(self):
        """Lit is simple - no Let needed for multiple uses."""
        expr = Call(_test_builtin('f'), [Var('x', INT64_TYPE), Var('x', INT64_TYPE)])
        result = subst(expr, {'x': Lit(42)})
        assert isinstance(result, Call)
        assert not isinstance(result, Let)

    def test_call_builtin_equal_is_simple(self):
        """Builtin 'equal' is considered simple."""
        expr = Call(_test_builtin('f'), [Var('x', BOOLEAN_TYPE), Var('x', BOOLEAN_TYPE)])
        replacement = Call(_test_builtin('equal', BOOLEAN_TYPE), [Lit(1), Lit(2)])
        result = subst(expr, {'x': replacement})
        # equal builtin is simple, so no Let needed
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin) and result.func.name == 'f'

    def test_call_non_builtin_is_not_simple(self):
        """Non-simple builtin needs Let for multiple uses."""
        expr = Call(_test_builtin('f'), [Var('x', INT64_TYPE), Var('x', INT64_TYPE)])
        replacement = Call(_test_builtin('compute', INT64_TYPE), [])
        result = subst(expr, {'x': replacement})
        # Should introduce Let
        assert isinstance(result, Let)

    def test_ifelse_with_simple_parts_is_simple(self):
        """IfElse with all simple parts is simple."""
        expr = Call(_test_builtin('f'), [Var('x', INT64_TYPE), Var('x', INT64_TYPE)])
        replacement = IfElse(Lit(True), Lit(1), Lit(2))
        result = subst(expr, {'x': replacement})
        # IfElse with all literals is simple
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin) and result.func.name == 'f'

    def test_let_with_simple_parts_is_simple(self):
        """Let with simple parts is simple."""
        expr = Call(_test_builtin('f'), [Var('x', INT64_TYPE), Var('x', INT64_TYPE)])
        y_var = Var('y', INT64_TYPE)
        replacement = Let(y_var, Lit(5), y_var)
        result = subst(expr, {'x': replacement})
        # Let with literal init is simple
        assert isinstance(result, Call)
        assert isinstance(result.func, Builtin) and result.func.name == 'f'


class TestCountVarOccurrences:
    """Test _count_var_occurrences helper (indirectly through subst)."""

    def test_zero_occurrences(self):
        """Variable with zero occurrences not substituted."""
        expr = Lit(42)
        result = subst(expr, {'x': Call(_test_builtin('expensive'), [])})
        # Since x doesn't appear, expensive call is not used
        assert result == expr

    def test_occurrence_in_nested_call(self):
        """Count variable in nested call structures."""
        expr = Call(_test_builtin('f'), [Call(_test_builtin('g'), [Var('x', INT64_TYPE)])])
        replacement = Call(_test_builtin('expensive', INT64_TYPE), [])
        result = subst(expr, {'x': replacement})
        # Single occurrence, so substitutes directly
        assert isinstance(result, Call)
        inner_call = result.args[0]
        assert isinstance(inner_call, Call)
        assert inner_call.args[0] == replacement


_NEVER = BaseType("Never")


class TestTypeJoin:
    """Tests for type_join."""

    def test_same_type(self):
        assert type_join(INT64_TYPE, INT64_TYPE) == INT64_TYPE

    def test_never_left(self):
        assert type_join(_NEVER, INT64_TYPE) == INT64_TYPE

    def test_never_right(self):
        assert type_join(INT64_TYPE, _NEVER) == INT64_TYPE

    def test_never_never(self):
        assert type_join(_NEVER, _NEVER) == _NEVER

    def test_any_absorbs(self):
        assert type_join(_ANY, INT64_TYPE) == _ANY
        assert type_join(INT64_TYPE, _ANY) == _ANY

    def test_option_covariant(self):
        assert type_join(OptionType(_NEVER), OptionType(INT64_TYPE)) == OptionType(INT64_TYPE)

    def test_list_covariant(self):
        assert type_join(ListType(_NEVER), ListType(INT64_TYPE)) == ListType(INT64_TYPE)

    def test_dict_covariant_value(self):
        assert type_join(
            DictType(STRING_TYPE, _NEVER),
            DictType(STRING_TYPE, INT64_TYPE)
        ) == DictType(STRING_TYPE, INT64_TYPE)

    def test_dict_key_mismatch(self):
        with pytest.raises(TypeError, match="key types"):
            type_join(DictType(STRING_TYPE, INT64_TYPE), DictType(INT64_TYPE, INT64_TYPE))

    def test_incompatible_base_types(self):
        with pytest.raises(TypeError, match="Cannot join"):
            type_join(INT64_TYPE, STRING_TYPE)

    def test_incompatible_type_kinds(self):
        with pytest.raises(TypeError, match="Cannot join"):
            type_join(INT64_TYPE, OptionType(INT64_TYPE))
