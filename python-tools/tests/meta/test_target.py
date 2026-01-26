#!/usr/bin/env python3
"""Tests for target IR (intermediate representation)."""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.target import (
    # Types
    BaseType, MessageType, TupleType, ListType, OptionType, FunctionType,
    # Expressions
    Var, Lit, Symbol, Builtin, Message, Call, Lambda, Let, IfElse,
    Seq, While, Assign, Return,
    # Definitions
    FunDef,
    # Utilities
    gensym,
)
from meta.gensym import reset as reset_gensym


# ============================================================================
# Type Tests
# ============================================================================

class TestBaseType:
    """Tests for BaseType."""

    def test_construction(self):
        """Test BaseType construction."""
        t = BaseType("Int64")
        assert t.name == "Int64"

    def test_str(self):
        """Test BaseType string representation."""
        t = BaseType("String")
        assert str(t) == "String"

    def test_equality(self):
        """Test BaseType equality."""
        t1 = BaseType("Int64")
        t2 = BaseType("Int64")
        t3 = BaseType("String")
        assert t1 == t2
        assert t1 != t3


class TestMessageType:
    """Tests for MessageType."""

    def test_construction(self):
        """Test MessageType construction."""
        t = MessageType("proto", "Transaction")
        assert t.name == "Transaction"
        assert t.module == "proto"

    def test_str(self):
        """Test MessageType string representation."""
        t = MessageType("proto", "Formula")
        assert str(t) == "proto.Formula"

    def test_equality(self):
        """Test MessageType equality."""
        t1 = MessageType("proto", "Term")
        t2 = MessageType("proto", "Term")
        t3 = MessageType("proto", "Value")
        assert t1 == t2
        assert t1 != t3


class TestTupleType:
    """Tests for TupleType."""

    def test_construction_with_list(self):
        """Test TupleType construction with list."""
        t = TupleType([BaseType("Int64"), BaseType("String")])
        assert len(t.elements) == 2
        assert isinstance(t.elements, tuple)

    def test_construction_with_tuple(self):
        """Test TupleType construction with tuple."""
        t = TupleType((BaseType("Int64"), BaseType("String")))
        assert len(t.elements) == 2
        assert isinstance(t.elements, tuple)

    def test_str(self):
        """Test TupleType string representation."""
        t = TupleType([BaseType("Int64"), BaseType("String")])
        assert str(t) == "(Int64, String)"

    def test_nested_tuple(self):
        """Test nested TupleType."""
        inner = TupleType([BaseType("Int64"), BaseType("String")])
        outer = TupleType([inner, BaseType("Boolean")])
        assert str(outer) == "((Int64, String), Boolean)"

    def test_empty_tuple(self):
        """Test empty TupleType."""
        t = TupleType([])
        assert str(t) == "()"


class TestListType:
    """Tests for ListType."""

    def test_construction(self):
        """Test ListType construction."""
        t = ListType(BaseType("Int64"))
        assert t.element_type == BaseType("Int64")

    def test_str(self):
        """Test ListType string representation."""
        t = ListType(BaseType("String"))
        assert str(t) == "List[String]"

    def test_nested_list(self):
        """Test nested ListType."""
        inner = ListType(BaseType("Int64"))
        outer = ListType(inner)
        assert str(outer) == "List[List[Int64]]"

    def test_list_of_messages(self):
        """Test ListType with MessageType."""
        t = ListType(MessageType("proto", "Term"))
        assert str(t) == "List[proto.Term]"


class TestOptionType:
    """Tests for OptionType."""

    def test_construction(self):
        """Test OptionType construction."""
        t = OptionType(BaseType("Int64"))
        assert t.element_type == BaseType("Int64")

    def test_str(self):
        """Test OptionType string representation."""
        t = OptionType(BaseType("String"))
        assert str(t) == "Option[String]"

    def test_option_of_list(self):
        """Test OptionType with ListType."""
        inner = ListType(BaseType("Int64"))
        t = OptionType(inner)
        assert str(t) == "Option[List[Int64]]"

    def test_option_of_message(self):
        """Test OptionType with MessageType."""
        t = OptionType(MessageType("proto", "Formula"))
        assert str(t) == "Option[proto.Formula]"


class TestFunctionType:
    """Tests for FunctionType."""

    def test_construction_with_list(self):
        """Test FunctionType construction with list."""
        t = FunctionType([BaseType("Int64"), BaseType("String")], BaseType("Boolean"))
        assert len(t.param_types) == 2
        assert isinstance(t.param_types, tuple)

    def test_construction_with_tuple(self):
        """Test FunctionType construction with tuple."""
        t = FunctionType((BaseType("Int64"),), BaseType("String"))
        assert len(t.param_types) == 1
        assert isinstance(t.param_types, tuple)

    def test_str(self):
        """Test FunctionType string representation."""
        t = FunctionType([BaseType("Int64"), BaseType("String")], BaseType("Boolean"))
        assert str(t) == "(Int64, String) -> Boolean"

    def test_no_params(self):
        """Test FunctionType with no parameters."""
        t = FunctionType([], BaseType("Int64"))
        assert str(t) == "() -> Int64"

    def test_nested_function(self):
        """Test nested FunctionType."""
        inner = FunctionType([BaseType("Int64")], BaseType("String"))
        outer = FunctionType([inner], BaseType("Boolean"))
        assert str(outer) == "((Int64) -> String) -> Boolean"


# ============================================================================
# Expression Tests
# ============================================================================

class TestVar:
    """Tests for Var."""

    def test_construction(self):
        """Test Var construction."""
        v = Var("x", BaseType("Int64"))
        assert v.name == "x"
        assert v.type == BaseType("Int64")

    def test_str(self):
        """Test Var string representation."""
        v = Var("result", MessageType("proto", "Formula"))
        assert str(v) == "result::proto.Formula"

    def test_invalid_name(self):
        """Test Var with invalid name."""
        with pytest.raises(ValueError, match="Invalid variable name"):
            Var("123invalid", BaseType("Int64"))

        with pytest.raises(ValueError, match="Invalid variable name"):
            Var("with-dash", BaseType("String"))



class TestLit:
    """Tests for Lit."""

    def test_int_literal(self):
        """Test integer literal."""
        lit = Lit(42)
        assert lit.value == 42
        assert str(lit) == "42"

    def test_string_literal(self):
        """Test string literal."""
        lit = Lit("hello")
        assert lit.value == "hello"
        assert str(lit) == "'hello'"

    def test_bool_literal(self):
        """Test boolean literal."""
        lit_true = Lit(True)
        lit_false = Lit(False)
        assert str(lit_true) == "True"
        assert str(lit_false) == "False"

    def test_none_literal(self):
        """Test None literal."""
        lit = Lit(None)
        assert lit.value is None
        assert str(lit) == "None"

    def test_float_literal(self):
        """Test float literal."""
        lit = Lit(3.14)
        assert lit.value == 3.14
        assert str(lit) == "3.14"


class TestSymbol:
    """Tests for Symbol."""

    def test_construction(self):
        """Test Symbol construction."""
        sym = Symbol("cast")
        assert sym.name == "cast"

    def test_str(self):
        """Test Symbol string representation."""
        sym = Symbol("field_name")
        assert str(sym) == ":field_name"

    def test_invalid_name(self):
        """Test Symbol with invalid name."""
        with pytest.raises(ValueError, match="Invalid variable name"):
            Symbol("123invalid")

        with pytest.raises(ValueError, match="Invalid variable name"):
            Symbol("with-dash")


class TestBuiltin:
    """Tests for Builtin."""

    def test_construction(self):
        """Test Builtin construction."""
        b = Builtin("consume")
        assert b.name == "consume"

    def test_str(self):
        """Test Builtin string representation."""
        b = Builtin("is_none")
        assert str(b) == "%is_none"

    def test_any_string_allowed(self):
        """Test that Builtin accepts any string."""
        b = Builtin("some-builtin-123")
        assert b.name == "some-builtin-123"


class TestMessage:
    """Tests for Message."""

    def test_construction(self):
        """Test Message construction."""
        c = Message("proto", "Transaction")
        assert c.name == "Transaction"
        assert c.module == "proto"

    def test_str(self):
        """Test Message string representation."""
        c = Message("proto", "Formula")
        assert str(c) == "@proto.Formula"

    def test_invalid_name(self):
        """Test Message with invalid name."""
        with pytest.raises(ValueError, match="Invalid message name"):
            Message("proto", "123Invalid")

        with pytest.raises(ValueError, match="Invalid message name"):
            Message("proto", "with-dash")


class TestCall:
    """Tests for Call."""

    def test_construction_no_args(self):
        """Test Call with no arguments."""
        func = Builtin("get_value")
        call = Call(func, [])
        assert call.func == func
        assert len(call.args) == 0
        assert isinstance(call.args, tuple)

    def test_construction_with_args(self):
        """Test Call with arguments."""
        func = Message("proto", "Transaction")
        arg1 = Var("x", BaseType("Int64"))
        arg2 = Var("y", BaseType("String"))
        call = Call(func, [arg1, arg2])
        assert len(call.args) == 2
        assert isinstance(call.args, tuple)

    def test_str(self):
        """Test Call string representation."""
        func = Builtin("add")
        arg1 = Lit(1)
        arg2 = Lit(2)
        call = Call(func, [arg1, arg2])
        assert str(call) == "%add(1, 2)"

    def test_nested_call(self):
        """Test nested Call."""
        inner = Call(Builtin("get_x"), [])
        outer = Call(Builtin("process"), [inner, Lit(42)])
        assert str(outer) == "%process(%get_x(), 42)"



class TestLambda:
    """Tests for Lambda."""

    def test_construction_no_params(self):
        """Test Lambda with no parameters."""
        body = Lit(42)
        lam = Lambda([], BaseType("Int64"), body)
        assert len(lam.params) == 0
        assert isinstance(lam.params, tuple)

    def test_construction_with_params(self):
        """Test Lambda with parameters."""
        param1 = Var("x", BaseType("Int64"))
        param2 = Var("y", BaseType("String"))
        body = Var("x", BaseType("Int64"))
        lam = Lambda([param1, param2], BaseType("Int64"), body)
        assert len(lam.params) == 2
        assert isinstance(lam.params, tuple)

    def test_str(self):
        """Test Lambda string representation."""
        param = Var("x", BaseType("Int64"))
        body = Var("x", BaseType("Int64"))
        lam = Lambda([param], BaseType("Int64"), body)
        assert str(lam) == "lambda x::Int64 -> Int64: x::Int64"



class TestLet:
    """Tests for Let."""

    def test_construction(self):
        """Test Let construction."""
        var = Var("x", BaseType("Int64"))
        init = Lit(42)
        body = Var("x", BaseType("Int64"))
        let = Let(var, init, body)
        assert let.var == var
        assert let.init == init
        assert let.body == body

    def test_str(self):
        """Test Let string representation."""
        var = Var("result", BaseType("String"))
        init = Lit("hello")
        body = Var("result", BaseType("String"))
        let = Let(var, init, body)
        assert str(let) == "let result: String = 'hello' in result::String"

    def test_nested_let(self):
        """Test nested Let."""
        var1 = Var("x", BaseType("Int64"))
        init1 = Lit(1)
        var2 = Var("y", BaseType("Int64"))
        init2 = Lit(2)
        body = Var("x", BaseType("Int64"))
        inner = Let(var2, init2, body)
        outer = Let(var1, init1, inner)
        assert "let x" in str(outer)
        assert "let y" in str(outer)



class TestIfElse:
    """Tests for IfElse."""

    def test_construction(self):
        """Test IfElse construction."""
        cond = Var("flag", BaseType("Boolean"))
        then_br = Lit(1)
        else_br = Lit(2)
        ifelse = IfElse(cond, then_br, else_br)
        assert ifelse.condition == cond
        assert ifelse.then_branch == then_br
        assert ifelse.else_branch == else_br

    def test_str(self):
        """Test IfElse string representation."""
        cond = Var("x", BaseType("Boolean"))
        then_br = Lit("yes")
        else_br = Lit("no")
        ifelse = IfElse(cond, then_br, else_br)
        assert str(ifelse) == "if (x::Boolean) then 'yes' else 'no'"

    def test_nested_ifelse(self):
        """Test nested IfElse."""
        cond1 = Var("a", BaseType("Boolean"))
        cond2 = Var("b", BaseType("Boolean"))
        inner = IfElse(cond2, Lit(2), Lit(3))
        outer = IfElse(cond1, Lit("x"), inner)
        assert "if (a" in str(outer)
        assert "if (b" in str(outer)



class TestSeq:
    """Tests for Seq."""

    def test_construction(self):
        """Test Seq construction with list."""
        expr1 = Lit(1)
        expr2 = Lit(2)
        expr3 = Lit(3)
        seq = Seq([expr1, expr2, expr3])
        assert len(seq.exprs) == 3
        assert isinstance(seq.exprs, tuple)

    def test_str(self):
        """Test Seq string representation."""
        expr1 = Lit(1)
        expr2 = Lit(2)
        seq = Seq([expr1, expr2])
        assert str(seq) == "1; 2"

    def test_single_expr_fails(self):
        """Test that Seq requires at least two expressions."""
        with pytest.raises(AssertionError, match="at least two expressions"):
            Seq([Lit(1)])

    def test_empty_seq_fails(self):
        """Test that empty Seq fails."""
        with pytest.raises(AssertionError, match="at least two expressions"):
            Seq([])



class TestWhile:
    """Tests for While."""

    def test_construction(self):
        """Test While construction."""
        cond = Var("running", BaseType("Boolean"))
        body = Lit(42)
        loop = While(cond, body)
        assert loop.condition == cond
        assert loop.body == body

    def test_str(self):
        """Test While string representation."""
        cond = Var("flag", BaseType("Boolean"))
        body = Lit(1)
        loop = While(cond, body)
        assert str(loop) == "while (flag::Boolean) 1"



class TestAssign:
    """Tests for Assign."""

    def test_construction(self):
        """Test Assign construction."""
        var = Var("x", BaseType("Int64"))
        expr = Lit(42)
        assign = Assign(var, expr)
        assert assign.var == var
        assert assign.expr == expr

    def test_str(self):
        """Test Assign string representation."""
        var = Var("result", BaseType("String"))
        expr = Lit("hello")
        assign = Assign(var, expr)
        assert str(assign) == "result = 'hello'"



class TestReturn:
    """Tests for Return."""

    def test_construction(self):
        """Test Return construction."""
        expr = Lit(42)
        ret = Return(expr)
        assert ret.expr == expr

    def test_str(self):
        """Test Return string representation."""
        expr = Var("result", BaseType("Int64"))
        ret = Return(expr)
        assert str(ret) == "return result::Int64"

    def test_return_validates_expr_type(self):
        """Test Return validates that expr is a TargetExpr."""
        with pytest.raises(AssertionError):
            Return("not an expr")  # type: ignore

    def test_nested_return_fails(self):
        """Test that Return cannot contain another Return."""
        inner = Return(Lit(42))
        with pytest.raises(AssertionError):
            Return(inner)


# ============================================================================
# Definition Tests
# ============================================================================

class TestFunDef:
    """Tests for FunDef."""

    def test_construction_no_params(self):
        """Test FunDef with no parameters."""
        body = Lit(42)
        fundef = FunDef("get_answer", [], BaseType("Int64"), body)
        assert fundef.name == "get_answer"
        assert len(fundef.params) == 0
        assert isinstance(fundef.params, tuple)

    def test_construction_with_params(self):
        """Test FunDef with parameters."""
        param1 = Var("x", BaseType("Int64"))
        param2 = Var("y", BaseType("String"))
        body = Var("x", BaseType("Int64"))
        fundef = FunDef("process", [param1, param2], BaseType("Int64"), body)
        assert len(fundef.params) == 2
        assert isinstance(fundef.params, tuple)

    def test_str(self):
        """Test FunDef string representation."""
        param = Var("n", BaseType("Int64"))
        body = Var("n", BaseType("Int64"))
        fundef = FunDef("identity", [param], BaseType("Int64"), body)
        assert str(fundef) == "def identity(n: Int64) -> Int64: n::Int64"


# ============================================================================
# Utility Tests
# ============================================================================

class TestGensym:
    """Tests for gensym utility."""

    def test_default_prefix(self):
        """Test gensym with default prefix."""
        reset_gensym(0)
        sym1 = gensym()
        sym2 = gensym()
        assert sym1 == "_t0"
        assert sym2 == "_t1"

    def test_custom_prefix(self):
        """Test gensym with custom prefix."""
        reset_gensym(0)
        sym1 = gensym("temp")
        sym2 = gensym("temp")
        assert sym1 == "temp0"
        assert sym2 == "temp1"

    def test_unique_symbols(self):
        """Test that gensym generates unique symbols."""
        reset_gensym(0)
        symbols = [gensym() for _ in range(100)]
        assert len(set(symbols)) == 100


class TestComplexExpressions:
    """Tests for complex nested expressions."""

    def test_complex_lambda(self):
        """Test complex lambda expression."""
        # lambda x, y: if x then y else 0
        param_x = Var("x", BaseType("Boolean"))
        param_y = Var("y", BaseType("Int64"))
        then_br = Var("y", BaseType("Int64"))
        else_br = Lit(0)
        body = IfElse(Var("x", BaseType("Boolean")), then_br, else_br)
        lam = Lambda([param_x, param_y], BaseType("Int64"), body)

        assert len(lam.params) == 2
        assert isinstance(lam.body, IfElse)

    def test_let_with_call(self):
        """Test let expression with function call."""
        # let x = f(42) in x
        var = Var("x", BaseType("Int64"))
        init = Call(Builtin("f"), [Lit(42)])
        body = Var("x", BaseType("Int64"))
        let = Let(var, init, body)

        assert isinstance(let.init, Call)
        assert str(let).startswith("let x")

    def test_nested_calls(self):
        """Test deeply nested function calls."""
        # f(g(h(42)))
        innermost = Call(Builtin("h"), [Lit(42)])
        middle = Call(Builtin("g"), [innermost])
        outermost = Call(Builtin("f"), [middle])

        assert isinstance(outermost.args[0], Call)
        assert str(outermost) == "%f(%g(%h(42)))"

    def test_constructor_with_complex_args(self):
        """Test constructor call with complex arguments."""
        # Transaction(epochs, configure, sync)
        ctor = Message("proto", "Transaction")
        arg1 = Var("epochs", ListType(MessageType("proto", "Epoch")))
        arg2 = Var("configure", OptionType(MessageType("proto", "Configure")))
        arg3 = Var("sync", OptionType(MessageType("proto", "Sync")))
        call = Call(ctor, [arg1, arg2, arg3])

        assert len(call.args) == 3
        assert isinstance(call.func, Message)
        assert "@proto.Transaction" in str(call)

    def test_function_returning_function(self):
        """Test function type that returns a function."""
        # (Int64) -> (String) -> Boolean
        inner_func = FunctionType([BaseType("String")], BaseType("Boolean"))
        outer_func = FunctionType([BaseType("Int64")], inner_func)

        assert str(outer_func) == "(Int64) -> (String) -> Boolean"

    def test_complex_tuple_type(self):
        """Test complex tuple with various types."""
        # (Int64, List[String], Option[MessageType], (Boolean, Float64))
        inner_tuple = TupleType([BaseType("Boolean"), BaseType("Float64")])
        t = TupleType([
            BaseType("Int64"),
            ListType(BaseType("String")),
            OptionType(MessageType("proto", "Value")),
            inner_tuple
        ])

        assert len(t.elements) == 4
        assert "List[String]" in str(t)
        assert "Option[proto.Value]" in str(t)
