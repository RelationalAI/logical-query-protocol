#!/usr/bin/env python3
"""Roundtrip tests for target_print.

These tests verify that parsing a restricted Python expression and then
pretty-printing it back yields the same string.
"""

import pytest
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from meta.target import (
    TargetType, BaseType, MessageType, ListType, OptionType, TupleType,
    DictType, FunctionType, VarType,
    TargetExpr, Var, Lit, Builtin, NewMessage, Call, Lambda, Let, IfElse,
    Seq, ListExpr, GetElement,
)
from meta.target_print import expr_to_str, type_to_str
from meta.yacc_action_parser import TypeContext
from meta.target import Var
import ast


def make_ctx() -> TypeContext:
    """Create an empty TypeContext for parsing."""
    return TypeContext()


def parse_expr(text: str, ctx: TypeContext, extra_vars: Optional[dict] = None) -> 'TargetExpr':
    """Parse a simple expression for testing.

    This is a simplified wrapper that doesn't use $N parameter references,
    just extra_vars for variable bindings.
    """
    from meta.yacc_action_parser import _convert_node_with_vars
    if extra_vars is None:
        extra_vars = {}

    # Parse as Python expression
    tree = ast.parse(text, mode='eval')

    # Create empty param_info and params (no $N references in tests)
    param_info = []
    params = []

    return _convert_node_with_vars(tree.body, param_info, params, ctx, None, extra_vars)


class TestTypeRoundtrip:
    """Roundtrip tests for type_to_str."""

    @pytest.mark.parametrize("type_str", [
        "String",
        "Int64",
        "Float64",
        "Boolean",
        "Unknown",
    ])
    def test_base_types(self, type_str: str):
        """Test base type roundtrips."""
        typ = BaseType(type_str)
        assert type_to_str(typ) == type_str

    @pytest.mark.parametrize("module,name,expected", [
        ("logic", "Value", "logic.Value"),
        ("proto", "Formula", "proto.Formula"),
        ("lqp", "Term", "lqp.Term"),
    ])
    def test_message_types(self, module: str, name: str, expected: str):
        """Test message type roundtrips."""
        typ = MessageType(module, name)
        assert type_to_str(typ) == expected

    @pytest.mark.parametrize("elem,expected", [
        (BaseType("Int64"), "List[Int64]"),
        (BaseType("String"), "List[String]"),
        (MessageType("logic", "Value"), "List[logic.Value]"),
    ])
    def test_list_types(self, elem: TargetType, expected: str):
        """Test list type roundtrips."""
        typ = ListType(elem)
        assert type_to_str(typ) == expected

    def test_nested_list_type(self):
        """Test nested list type."""
        typ = ListType(ListType(BaseType("Int64")))
        assert type_to_str(typ) == "List[List[Int64]]"

    @pytest.mark.parametrize("elem,expected", [
        (BaseType("Int64"), "Optional[Int64]"),
        (BaseType("String"), "Optional[String]"),
        (MessageType("logic", "Value"), "Optional[logic.Value]"),
    ])
    def test_option_types(self, elem: TargetType, expected: str):
        """Test option type roundtrips."""
        typ = OptionType(elem)
        assert type_to_str(typ) == expected

    @pytest.mark.parametrize("elems,expected", [
        ([BaseType("Int64"), BaseType("String")], "Tuple[Int64, String]"),
        ([BaseType("Int64"), BaseType("String"), BaseType("Boolean")], "Tuple[Int64, String, Boolean]"),
    ])
    def test_tuple_types(self, elems: List[TargetType], expected: str):
        """Test tuple type roundtrips."""
        typ = TupleType(elems)
        assert type_to_str(typ) == expected

    def test_dict_type(self):
        """Test dict type roundtrip."""
        typ = DictType(BaseType("String"), BaseType("Int64"))
        assert type_to_str(typ) == "Dict[String, Int64]"

    def test_function_type(self):
        """Test function type roundtrip."""
        typ = FunctionType([BaseType("Int64"), BaseType("String")], BaseType("Boolean"))
        assert type_to_str(typ) == "Callable[[Int64, String], Boolean]"

    def test_function_type_no_params(self):
        """Test function type with no params."""
        typ = FunctionType([], BaseType("Int64"))
        assert type_to_str(typ) == "Callable[[], Int64]"


class TestExprRoundtrip:
    """Roundtrip tests for expr_to_str with parsing."""

    @pytest.mark.parametrize("expr_str", [
        "42",
        "0",
        "3.14",
        "'hello'",
        "\"world\"",
        "True",
        "False",
    ])
    def test_literals(self, expr_str: str):
        """Test literal roundtrips."""
        ctx = make_ctx()
        expr = parse_expr(expr_str, ctx)
        result = expr_to_str(expr)
        # Normalize: double quotes become single
        expected = expr_str.replace('"', "'")
        assert result == expected

    def test_variable(self):
        """Test variable roundtrip."""
        ctx = make_ctx()
        extra_vars = {"x": BaseType("Int64")}
        expr = parse_expr("x", ctx, extra_vars)
        assert expr_to_str(expr) == "x"

    def test_builtin_call(self):
        """Test builtin function call roundtrip."""
        ctx = make_ctx()
        extra_vars = {"x": ListType(BaseType("Int64")), "y": ListType(BaseType("Int64"))}
        expr = parse_expr("list_concat(x, y)", ctx, extra_vars)
        assert expr_to_str(expr) == "builtin.list_concat(x, y)"

    def test_builtin_call_no_args(self):
        """Test builtin function call with no args."""
        ctx = make_ctx()
        expr = parse_expr("none()", ctx)
        assert expr_to_str(expr) == "builtin.none()"

    def test_message_constructor_no_fields(self):
        """Test message constructor with no fields."""
        ctx = make_ctx()
        expr = parse_expr("logic.Value()", ctx)
        assert expr_to_str(expr) == "logic.Value()"

    def test_message_constructor_with_fields(self):
        """Test message constructor with fields."""
        ctx = make_ctx()
        extra_vars = {"x": BaseType("Int64")}
        expr = parse_expr("logic.Value(int_value=x)", ctx, extra_vars)
        assert expr_to_str(expr) == "logic.Value(int_value=x)"

    def test_message_constructor_multiple_fields(self):
        """Test message constructor with multiple fields."""
        ctx = make_ctx()
        extra_vars = {"x": BaseType("Int64"), "y": BaseType("String")}
        expr = parse_expr("proto.Pair(first=x, second=y)", ctx, extra_vars)
        assert expr_to_str(expr) == "proto.Pair(first=x, second=y)"

    def test_empty_list(self):
        """Test empty list roundtrip."""
        ctx = make_ctx()
        expr = parse_expr("[]", ctx)
        assert expr_to_str(expr) == "[]"

    def test_list_with_elements(self):
        """Test list with elements."""
        ctx = make_ctx()
        extra_vars = {"x": BaseType("Int64"), "y": BaseType("Int64")}
        expr = parse_expr("[x, y]", ctx, extra_vars)
        assert expr_to_str(expr) == "[x, y]"

    def test_list_with_literals(self):
        """Test list with literal elements."""
        ctx = make_ctx()
        expr = parse_expr("[1, 2, 3]", ctx)
        assert expr_to_str(expr) == "[1, 2, 3]"

    def test_conditional_expression(self):
        """Test conditional (ternary) expression."""
        ctx = make_ctx()
        extra_vars = {"cond": BaseType("Boolean"), "x": BaseType("Int64"), "y": BaseType("Int64")}
        expr = parse_expr("x if cond else y", ctx, extra_vars)
        assert expr_to_str(expr) == "(x if cond else y)"

    def test_nested_conditional(self):
        """Test nested conditional expression."""
        ctx = make_ctx()
        extra_vars = {
            "a": BaseType("Boolean"),
            "b": BaseType("Boolean"),
            "x": BaseType("Int64"),
            "y": BaseType("Int64"),
            "z": BaseType("Int64"),
        }
        expr = parse_expr("x if a else (y if b else z)", ctx, extra_vars)
        assert expr_to_str(expr) == "(x if a else (y if b else z))"

    def test_seq_expression(self):
        """Test seq expression roundtrip."""
        ctx = make_ctx()
        extra_vars = {"x": BaseType("Int64"), "y": BaseType("Int64")}
        expr = parse_expr("seq(x, y)", ctx, extra_vars)
        assert expr_to_str(expr) == "seq(x; y)"

    def test_seq_multiple_expressions(self):
        """Test seq with multiple expressions."""
        ctx = make_ctx()
        extra_vars = {"x": BaseType("Int64"), "y": BaseType("Int64"), "z": BaseType("Int64")}
        expr = parse_expr("seq(x, y, z)", ctx, extra_vars)
        assert expr_to_str(expr) == "seq(x; y; z)"

    def test_tuple_element_access(self):
        """Test tuple element access."""
        ctx = make_ctx()
        extra_vars = {"pair": TupleType([BaseType("Int64"), BaseType("String")])}
        expr = parse_expr("pair[0]", ctx, extra_vars)
        assert expr_to_str(expr) == "pair[0]"

    def test_tuple_second_element(self):
        """Test tuple second element access."""
        ctx = make_ctx()
        extra_vars = {"pair": TupleType([BaseType("Int64"), BaseType("String")])}
        expr = parse_expr("pair[1]", ctx, extra_vars)
        assert expr_to_str(expr) == "pair[1]"

    def test_nested_call(self):
        """Test nested function calls."""
        ctx = make_ctx()
        extra_vars = {"x": ListType(BaseType("Int64")), "y": ListType(BaseType("Int64")), "z": ListType(BaseType("Int64"))}
        expr = parse_expr("list_concat(list_concat(x, y), z)", ctx, extra_vars)
        assert expr_to_str(expr) == "builtin.list_concat(builtin.list_concat(x, y), z)"


class TestExprDirect:
    """Direct tests for expr_to_str without parsing (for constructs not easily parsed)."""

    def test_lambda_single_param(self):
        """Test lambda with single parameter."""
        param = Var("x", BaseType("Int64"))
        body = Var("x", BaseType("Int64"))
        lam = Lambda([param], BaseType("Int64"), body)
        assert expr_to_str(lam) == "lambda x: x"

    def test_lambda_multiple_params(self):
        """Test lambda with multiple parameters."""
        p1 = Var("x", BaseType("Int64"))
        p2 = Var("y", BaseType("String"))
        body = Var("x", BaseType("Int64"))
        lam = Lambda([p1, p2], BaseType("Int64"), body)
        assert expr_to_str(lam) == "lambda x, y: x"

    def test_lambda_with_call_body(self):
        """Test lambda with function call body."""
        param = Var("x", BaseType("Int64"))
        body = Call(Builtin("append"), [Var("x", BaseType("Int64")), Lit(1)])
        lam = Lambda([param], ListType(BaseType("Int64")), body)
        assert expr_to_str(lam) == "lambda x: builtin.append(x, 1)"

    def test_symbol(self):
        """Test symbol expression."""
        from meta.target import Symbol
        sym = Symbol("field_name")
        assert expr_to_str(sym) == ":field_name"

    def test_get_field(self):
        """Test field access expression."""
        from meta.target import GetField
        obj = Var("msg", MessageType("logic", "Value"))
        field = GetField(obj, "int_value")
        assert expr_to_str(field) == "msg.int_value"

    def test_nested_get_field(self):
        """Test nested field access."""
        from meta.target import GetField
        obj = Var("msg", MessageType("logic", "Outer"))
        inner = GetField(obj, "inner")
        outer = GetField(inner, "value")
        assert expr_to_str(outer) == "msg.inner.value"

    def test_has_proto_field(self):
        """Test has_proto_field builtin call."""
        from meta.target import Call, Builtin
        obj = Var("msg", MessageType("logic", "Value"))
        has = Call(Builtin("has_proto_field"), [obj, Lit("int_value")])
        assert expr_to_str(has) == "builtin.has_proto_field(msg, 'int_value')"

    def test_dict_from_list(self):
        """Test dict_from_list builtin call."""
        from meta.target import Call, Builtin
        pairs = Var("pairs", ListType(TupleType([BaseType("String"), BaseType("Int64")])))
        d = Call(Builtin("dict_from_list"), [pairs])
        assert expr_to_str(d) == "builtin.dict_from_list(pairs)"

    def test_dict_lookup(self):
        """Test dict_get builtin call."""
        from meta.target import Call, Builtin
        d = Var("d", DictType(BaseType("String"), BaseType("Int64")))
        key = Lit("key")
        lookup = Call(Builtin("dict_get"), [d, key])
        assert expr_to_str(lookup) == "builtin.dict_get(d, 'key')"

    def test_assign(self):
        """Test assignment expression."""
        from meta.target import Assign
        var = Var("x", BaseType("Int64"))
        expr = Lit(42)
        assign = Assign(var, expr)
        assert expr_to_str(assign) == "x = 42"

    def test_return(self):
        """Test return expression."""
        from meta.target import Return
        expr = Var("x", BaseType("Int64"))
        ret = Return(expr)
        assert expr_to_str(ret) == "return x"

    def test_while(self):
        """Test while expression."""
        from meta.target import While
        cond = Var("running", BaseType("Boolean"))
        body = Lit(42)
        loop = While(cond, body)
        assert expr_to_str(loop) == "while running: 42"

    def test_foreach(self):
        """Test foreach expression."""
        from meta.target import Foreach
        var = Var("x", BaseType("Int64"))
        coll = Var("xs", ListType(BaseType("Int64")))
        body = Var("x", BaseType("Int64"))
        loop = Foreach(var, coll, body)
        assert expr_to_str(loop) == "for x in xs: x"

    def test_foreach_enumerated(self):
        """Test foreach enumerated expression."""
        from meta.target import ForeachEnumerated
        idx = Var("i", BaseType("Int64"))
        elem = Var("x", BaseType("Int64"))
        coll = Var("xs", ListType(BaseType("Int64")))
        body = Var("x", BaseType("Int64"))
        loop = ForeachEnumerated(index_var=idx, var=elem, collection=coll, body=body)
        assert expr_to_str(loop) == "for i, x in enumerate(xs): x"

    def test_oneof(self):
        """Test oneof expression."""
        from meta.target import OneOf
        oneof = OneOf("value")
        assert expr_to_str(oneof) == "oneof(value)"

    def test_named_fun(self):
        """Test named function reference."""
        from meta.target import NamedFun
        fun = NamedFun("my_func")
        assert expr_to_str(fun) == "my_func"

    def test_builtin(self):
        """Test builtin function reference."""
        b = Builtin("append")
        assert expr_to_str(b) == "builtin.append"


class TestFunDefPrint:
    """Tests for fundef_to_str."""

    def test_simple_function(self):
        """Test simple function definition."""
        from meta.target_print import fundef_to_str
        from meta.target import FunDef
        param = Var("x", BaseType("Int64"))
        body = Var("x", BaseType("Int64"))
        fundef = FunDef("identity", [param], BaseType("Int64"), body)
        result = fundef_to_str(fundef)
        assert result == "def identity(x: Int64) -> Int64:\n    return x"

    def test_function_multiple_params(self):
        """Test function with multiple parameters."""
        from meta.target_print import fundef_to_str
        from meta.target import FunDef
        p1 = Var("x", BaseType("Int64"))
        p2 = Var("y", BaseType("String"))
        body = Var("x", BaseType("Int64"))
        fundef = FunDef("first", [p1, p2], BaseType("Int64"), body)
        result = fundef_to_str(fundef)
        assert result == "def first(x: Int64, y: String) -> Int64:\n    return x"

    def test_function_no_params(self):
        """Test function with no parameters."""
        from meta.target_print import fundef_to_str
        from meta.target import FunDef
        body = Lit(42)
        fundef = FunDef("get_answer", [], BaseType("Int64"), body)
        result = fundef_to_str(fundef)
        assert result == "def get_answer() -> Int64:\n    return 42"
