"""Tests for s-expression to target IR conversions."""

import pytest

from meta.sexp import SAtom, SList
from meta.sexp_parser import parse_sexp
from meta.sexp_target import (
    sexp_to_type, sexp_to_expr, type_to_sexp, expr_to_sexp,
    SExprConversionError
)
from meta.target import (
    BaseType, MessageType, ListType, OptionType, TupleType, FunctionType,
    Var, Lit, Symbol, Builtin, NewMessage, OneOf, ListExpr, Call, Lambda,
    Let, IfElse, Seq, While, Foreach, Assign, Return
)


class TestSexpToType:
    """Tests for converting s-expressions to TargetType."""

    def test_base_type_string(self):
        result = sexp_to_type(parse_sexp("String"))
        assert result == BaseType("String")

    def test_base_type_int64(self):
        result = sexp_to_type(parse_sexp("Int64"))
        assert result == BaseType("Int64")

    def test_base_type_float64(self):
        result = sexp_to_type(parse_sexp("Float64"))
        assert result == BaseType("Float64")

    def test_base_type_boolean(self):
        result = sexp_to_type(parse_sexp("Boolean"))
        assert result == BaseType("Boolean")

    def test_message_type(self):
        result = sexp_to_type(parse_sexp("(Message logic Value)"))
        assert result == MessageType("logic", "Value")

    def test_message_type_different_module(self):
        result = sexp_to_type(parse_sexp("(Message transactions Transaction)"))
        assert result == MessageType("transactions", "Transaction")

    def test_list_type_simple(self):
        result = sexp_to_type(parse_sexp("(List Int64)"))
        assert result == ListType(BaseType("Int64"))

    def test_list_type_nested(self):
        result = sexp_to_type(parse_sexp("(List (Message logic Binding))"))
        assert result == ListType(MessageType("logic", "Binding"))

    def test_option_type_simple(self):
        result = sexp_to_type(parse_sexp("(Option String)"))
        assert result == OptionType(BaseType("String"))

    def test_option_type_nested(self):
        result = sexp_to_type(parse_sexp("(Option (List Int64))"))
        assert result == OptionType(ListType(BaseType("Int64")))

    def test_tuple_type_two_elements(self):
        result = sexp_to_type(parse_sexp("(Tuple String Int64)"))
        assert result == TupleType([BaseType("String"), BaseType("Int64")])

    def test_tuple_type_three_elements(self):
        result = sexp_to_type(parse_sexp("(Tuple String Int64 Boolean)"))
        assert result == TupleType([BaseType("String"), BaseType("Int64"), BaseType("Boolean")])

    def test_tuple_type_nested(self):
        result = sexp_to_type(parse_sexp("(Tuple (List String) (Option Int64))"))
        assert result == TupleType([ListType(BaseType("String")), OptionType(BaseType("Int64"))])

    def test_function_type_no_params(self):
        result = sexp_to_type(parse_sexp("(Function () Int64)"))
        assert result == FunctionType([], BaseType("Int64"))

    def test_function_type_one_param(self):
        result = sexp_to_type(parse_sexp("(Function (String) Int64)"))
        assert result == FunctionType([BaseType("String")], BaseType("Int64"))

    def test_function_type_multiple_params(self):
        result = sexp_to_type(parse_sexp("(Function (String Int64) Boolean)"))
        assert result == FunctionType([BaseType("String"), BaseType("Int64")], BaseType("Boolean"))

    def test_invalid_type_quoted_string(self):
        with pytest.raises(SExprConversionError):
            sexp_to_type(parse_sexp('"String"'))

    def test_invalid_type_number(self):
        with pytest.raises(SExprConversionError):
            sexp_to_type(SAtom(42))

    def test_invalid_type_unknown_constructor(self):
        with pytest.raises(SExprConversionError):
            sexp_to_type(parse_sexp("(Unknown foo bar)"))


class TestSexpToExpr:
    """Tests for converting s-expressions to TargetExpr."""

    def test_var(self):
        result = sexp_to_expr(parse_sexp("(var x Int64)"))
        assert result == Var("x", BaseType("Int64"))

    def test_var_with_message_type(self):
        result = sexp_to_expr(parse_sexp("(var value (Message logic Value))"))
        assert result == Var("value", MessageType("logic", "Value"))

    def test_lit_integer(self):
        result = sexp_to_expr(parse_sexp("(lit 42)"))
        assert result == Lit(42)

    def test_lit_string(self):
        result = sexp_to_expr(parse_sexp('(lit "hello")'))
        assert result == Lit("hello")

    def test_lit_boolean_true(self):
        result = sexp_to_expr(parse_sexp("(lit true)"))
        assert result == Lit(True)

    def test_lit_boolean_false(self):
        result = sexp_to_expr(parse_sexp("(lit false)"))
        assert result == Lit(False)

    def test_symbol_literal(self):
        result = sexp_to_expr(parse_sexp(":foo"))
        assert result == Symbol("foo")

    def test_builtin(self):
        result = sexp_to_expr(parse_sexp("(builtin make_tuple)"))
        assert result == Builtin("make_tuple")

    def test_new_message_empty(self):
        result = sexp_to_expr(parse_sexp("(new-message logic Value)"))
        assert result == NewMessage("logic", "Value", ())

    def test_new_message_with_fields(self):
        result = sexp_to_expr(parse_sexp("(new-message logic Value (name (var x String)) (age (lit 42)))"))
        assert result == NewMessage("logic", "Value", (("name", Var("x", BaseType("String"))), ("age", Lit(42))))

    def test_oneof(self):
        result = sexp_to_expr(parse_sexp("(oneof string_value)"))
        assert result == OneOf("string_value")

    def test_list_empty(self):
        result = sexp_to_expr(parse_sexp("(list Int64)"))
        assert result == ListExpr([], BaseType("Int64"))

    def test_list_with_elements(self):
        result = sexp_to_expr(parse_sexp("(list Int64 (lit 1) (lit 2) (lit 3))"))
        assert result == ListExpr([Lit(1), Lit(2), Lit(3)], BaseType("Int64"))

    def test_call_no_args(self):
        result = sexp_to_expr(parse_sexp("(call (builtin foo))"))
        assert result == Call(Builtin("foo"), [])

    def test_call_with_args(self):
        result = sexp_to_expr(parse_sexp("(call (builtin add) (var x Int64) (var y Int64))"))
        assert result == Call(Builtin("add"), [Var("x", BaseType("Int64")), Var("y", BaseType("Int64"))])

    def test_call_new_message_constructor(self):
        result = sexp_to_expr(parse_sexp("(call (new-message logic Value) (var x String))"))
        assert result == Call(NewMessage("logic", "Value", ()), [Var("x", BaseType("String"))])

    def test_lambda_no_params(self):
        result = sexp_to_expr(parse_sexp("(lambda () Int64 (lit 42))"))
        assert result == Lambda([], BaseType("Int64"), Lit(42))

    def test_lambda_one_param(self):
        result = sexp_to_expr(parse_sexp("(lambda ((x Int64)) Int64 (var x Int64))"))
        assert result == Lambda([Var("x", BaseType("Int64"))], BaseType("Int64"), Var("x", BaseType("Int64")))

    def test_lambda_multiple_params(self):
        result = sexp_to_expr(parse_sexp("(lambda ((x Int64) (y Int64)) Int64 (call (builtin add) (var x Int64) (var y Int64)))"))
        expected = Lambda(
            [Var("x", BaseType("Int64")), Var("y", BaseType("Int64"))],
            BaseType("Int64"),
            Call(Builtin("add"), [Var("x", BaseType("Int64")), Var("y", BaseType("Int64"))])
        )
        assert result == expected

    def test_let(self):
        result = sexp_to_expr(parse_sexp("(let (x Int64) (lit 10) (var x Int64))"))
        assert result == Let(Var("x", BaseType("Int64")), Lit(10), Var("x", BaseType("Int64")))

    def test_if(self):
        result = sexp_to_expr(parse_sexp("(if (lit true) (lit 1) (lit 0))"))
        assert result == IfElse(Lit(True), Lit(1), Lit(0))

    def test_seq(self):
        result = sexp_to_expr(parse_sexp("(seq (lit 1) (lit 2))"))
        assert result == Seq([Lit(1), Lit(2)])

    def test_seq_three_exprs(self):
        result = sexp_to_expr(parse_sexp("(seq (lit 1) (lit 2) (lit 3))"))
        assert result == Seq([Lit(1), Lit(2), Lit(3)])

    def test_while(self):
        result = sexp_to_expr(parse_sexp("(while (lit true) (lit 0))"))
        assert result == While(Lit(True), Lit(0))

    def test_foreach(self):
        result = sexp_to_expr(parse_sexp("(foreach (x Int64) (var items (List Int64)) (lit 0))"))
        assert result == Foreach(Var("x", BaseType("Int64")), Var("items", ListType(BaseType("Int64"))), Lit(0))

    def test_assign(self):
        result = sexp_to_expr(parse_sexp("(assign (x Int64) (lit 42))"))
        assert result == Assign(Var("x", BaseType("Int64")), Lit(42))

    def test_return(self):
        result = sexp_to_expr(parse_sexp("(return (lit 42))"))
        assert result == Return(Lit(42))

    def test_invalid_expr_untyped_symbol(self):
        with pytest.raises(SExprConversionError):
            sexp_to_expr(SAtom("foo"))

    def test_invalid_expr_unknown_form(self):
        with pytest.raises(SExprConversionError):
            sexp_to_expr(parse_sexp("(unknown_form x y z)"))


class TestTypeToSexp:
    """Tests for converting TargetType to s-expressions."""

    def test_base_type_string(self):
        result = type_to_sexp(BaseType("String"))
        assert result == SAtom("String")

    def test_base_type_int64(self):
        result = type_to_sexp(BaseType("Int64"))
        assert result == SAtom("Int64")

    def test_message_type(self):
        result = type_to_sexp(MessageType("logic", "Value"))
        assert result == SList((SAtom("Message"), SAtom("logic"), SAtom("Value")))

    def test_list_type(self):
        result = type_to_sexp(ListType(BaseType("Int64")))
        assert result == SList((SAtom("List"), SAtom("Int64")))

    def test_option_type(self):
        result = type_to_sexp(OptionType(BaseType("String")))
        assert result == SList((SAtom("Option"), SAtom("String")))

    def test_tuple_type(self):
        result = type_to_sexp(TupleType([BaseType("String"), BaseType("Int64")]))
        assert result == SList((SAtom("Tuple"), SAtom("String"), SAtom("Int64")))

    def test_function_type(self):
        result = type_to_sexp(FunctionType([BaseType("String")], BaseType("Int64")))
        expected = SList((SAtom("Function"), SList((SAtom("String"),)), SAtom("Int64")))
        assert result == expected

    def test_nested_type(self):
        result = type_to_sexp(ListType(OptionType(MessageType("logic", "Value"))))
        expected = SList((
            SAtom("List"),
            SList((
                SAtom("Option"),
                SList((SAtom("Message"), SAtom("logic"), SAtom("Value")))
            ))
        ))
        assert result == expected


class TestExprToSexp:
    """Tests for converting TargetExpr to s-expressions."""

    def test_var(self):
        result = expr_to_sexp(Var("x", BaseType("Int64")))
        assert result == SList((SAtom("var"), SAtom("x"), SAtom("Int64")))

    def test_lit_integer(self):
        result = expr_to_sexp(Lit(42))
        assert result == SList((SAtom("lit"), SAtom(42)))

    def test_lit_string(self):
        result = expr_to_sexp(Lit("hello"))
        assert result == SList((SAtom("lit"), SAtom("hello", quoted=True)))

    def test_lit_boolean(self):
        result = expr_to_sexp(Lit(True))
        assert result == SList((SAtom("lit"), SAtom("true")))

    def test_symbol(self):
        result = expr_to_sexp(Symbol("foo"))
        assert result == SAtom(":foo")

    def test_builtin(self):
        result = expr_to_sexp(Builtin("make_tuple"))
        assert result == SList((SAtom("builtin"), SAtom("make_tuple")))

    def test_new_message_empty(self):
        result = expr_to_sexp(NewMessage("logic", "Value", ()))
        assert result == SList((SAtom("new-message"), SAtom("logic"), SAtom("Value")))

    def test_new_message_with_fields(self):
        result = expr_to_sexp(NewMessage("logic", "Person", (("name", Var("x", BaseType("String"))), ("age", Lit(42)))))
        expected = parse_sexp("(new-message logic Person (name (var x String)) (age (lit 42)))")
        assert result == expected

    def test_oneof(self):
        result = expr_to_sexp(OneOf("string_value"))
        assert result == SList((SAtom("oneof"), SAtom("string_value")))

    def test_list_expr_empty(self):
        result = expr_to_sexp(ListExpr([], BaseType("Int64")))
        assert result == SList((SAtom("list"), SAtom("Int64")))

    def test_list_expr_with_elements(self):
        result = expr_to_sexp(ListExpr([Lit(1), Lit(2)], BaseType("Int64")))
        expected = SList((
            SAtom("list"),
            SAtom("Int64"),
            SList((SAtom("lit"), SAtom(1))),
            SList((SAtom("lit"), SAtom(2)))
        ))
        assert result == expected

    def test_call(self):
        result = expr_to_sexp(Call(Builtin("foo"), [Lit(1), Lit(2)]))
        expected = SList((
            SAtom("call"),
            SList((SAtom("builtin"), SAtom("foo"))),
            SList((SAtom("lit"), SAtom(1))),
            SList((SAtom("lit"), SAtom(2)))
        ))
        assert result == expected

    def test_lambda(self):
        result = expr_to_sexp(Lambda([Var("x", BaseType("Int64"))], BaseType("Int64"), Var("x", BaseType("Int64"))))
        expected = SList((
            SAtom("lambda"),
            SList((SList((SAtom("x"), SAtom("Int64"))),)),
            SAtom("Int64"),
            SList((SAtom("var"), SAtom("x"), SAtom("Int64")))
        ))
        assert result == expected

    def test_let(self):
        result = expr_to_sexp(Let(Var("x", BaseType("Int64")), Lit(10), Var("x", BaseType("Int64"))))
        expected = SList((
            SAtom("let"),
            SList((SAtom("x"), SAtom("Int64"))),
            SList((SAtom("lit"), SAtom(10))),
            SList((SAtom("var"), SAtom("x"), SAtom("Int64")))
        ))
        assert result == expected

    def test_if_else(self):
        result = expr_to_sexp(IfElse(Lit(True), Lit(1), Lit(0)))
        expected = SList((
            SAtom("if"),
            SList((SAtom("lit"), SAtom("true"))),
            SList((SAtom("lit"), SAtom(1))),
            SList((SAtom("lit"), SAtom(0)))
        ))
        assert result == expected

    def test_seq(self):
        result = expr_to_sexp(Seq([Lit(1), Lit(2)]))
        expected = SList((
            SAtom("seq"),
            SList((SAtom("lit"), SAtom(1))),
            SList((SAtom("lit"), SAtom(2)))
        ))
        assert result == expected


class TestTypeRoundTrip:
    """Tests for type conversion round-tripping."""

    def test_roundtrip_base_type(self):
        original = BaseType("String")
        sexp = type_to_sexp(original)
        recovered = sexp_to_type(sexp)
        assert recovered == original

    def test_roundtrip_message_type(self):
        original = MessageType("logic", "Value")
        sexp = type_to_sexp(original)
        recovered = sexp_to_type(sexp)
        assert recovered == original

    def test_roundtrip_list_type(self):
        original = ListType(BaseType("Int64"))
        sexp = type_to_sexp(original)
        recovered = sexp_to_type(sexp)
        assert recovered == original

    def test_roundtrip_option_type(self):
        original = OptionType(MessageType("logic", "Binding"))
        sexp = type_to_sexp(original)
        recovered = sexp_to_type(sexp)
        assert recovered == original

    def test_roundtrip_tuple_type(self):
        original = TupleType([BaseType("String"), BaseType("Int64"), BaseType("Boolean")])
        sexp = type_to_sexp(original)
        recovered = sexp_to_type(sexp)
        assert recovered == original

    def test_roundtrip_function_type(self):
        original = FunctionType([BaseType("String"), BaseType("Int64")], BaseType("Boolean"))
        sexp = type_to_sexp(original)
        recovered = sexp_to_type(sexp)
        assert recovered == original

    def test_roundtrip_complex_nested_type(self):
        original = TupleType([
            ListType(MessageType("logic", "Binding")),
            OptionType(TupleType([BaseType("String"), BaseType("Int64")]))
        ])
        sexp = type_to_sexp(original)
        recovered = sexp_to_type(sexp)
        assert recovered == original


class TestExprRoundTrip:
    """Tests for expression conversion round-tripping."""

    def test_roundtrip_var(self):
        original = Var("x", BaseType("Int64"))
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_lit_int(self):
        original = Lit(42)
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_lit_string(self):
        original = Lit("hello")
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_lit_bool(self):
        original = Lit(True)
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_symbol(self):
        original = Symbol("foo")
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_builtin(self):
        original = Builtin("make_tuple")
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_message(self):
        original = NewMessage("logic", "Value", ())
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_oneof(self):
        original = OneOf("string_value")
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_list_expr(self):
        original = ListExpr([Lit(1), Lit(2)], BaseType("Int64"))
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_call(self):
        original = Call(Builtin("foo"), [Var("x", BaseType("Int64"))])
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_lambda(self):
        original = Lambda(
            [Var("x", BaseType("Int64"))],
            BaseType("Int64"),
            Var("x", BaseType("Int64"))
        )
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_let(self):
        original = Let(Var("x", BaseType("Int64")), Lit(10), Var("x", BaseType("Int64")))
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_if_else(self):
        original = IfElse(Lit(True), Lit(1), Lit(0))
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_seq(self):
        original = Seq([Lit(1), Lit(2), Lit(3)])
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original

    def test_roundtrip_complex_expression(self):
        original = Lambda(
            [Var("x", BaseType("Int64")), Var("y", BaseType("Int64"))],
            BaseType("Int64"),
            Let(
                Var("sum", BaseType("Int64")),
                Call(Builtin("add"), [Var("x", BaseType("Int64")), Var("y", BaseType("Int64"))]),
                IfElse(
                    Call(Builtin("greater"), [Var("sum", BaseType("Int64")), Lit(0)]),
                    Var("sum", BaseType("Int64")),
                    Lit(0)
                )
            )
        )
        sexp = expr_to_sexp(original)
        recovered = sexp_to_expr(sexp)
        assert recovered == original


class TestSexpToTypeErrors:
    """Tests for error handling in sexp_to_type."""

    def test_quoted_string_error(self):
        """Quoted string is not a valid type."""
        with pytest.raises(SExprConversionError, match="Unexpected string literal in type"):
            sexp_to_type(SAtom(value="foo", quoted=True))

    def test_invalid_type_atom(self):
        """Non-string atom is not a valid type."""
        with pytest.raises(SExprConversionError, match="Invalid type atom"):
            sexp_to_type(SAtom(value=42, quoted=False))

    def test_empty_list_error(self):
        """Empty list is not a valid type."""
        with pytest.raises(SExprConversionError, match="Invalid type expression"):
            sexp_to_type(SList([]))

    def test_type_with_quoted_head(self):
        """Type expression must start with symbol, not string."""
        with pytest.raises(SExprConversionError, match="Type expression must start with a symbol"):
            sexp_to_type(SList([SAtom(value="Message", quoted=True), SAtom(value="test", quoted=False)]))

    def test_typevar_wrong_arity(self):
        """TypeVar requires exactly one argument."""
        with pytest.raises(SExprConversionError, match="TypeVar requires name"):
            sexp_to_type(parse_sexp("(TypeVar)"))

    def test_message_wrong_arity(self):
        """Message type requires module and name."""
        with pytest.raises(SExprConversionError, match="Message type requires module and name"):
            sexp_to_type(parse_sexp("(Message test)"))

    def test_list_wrong_arity(self):
        """List type requires element type."""
        with pytest.raises(SExprConversionError, match="List type requires element type"):
            sexp_to_type(parse_sexp("(List)"))

    def test_option_wrong_arity(self):
        """Option type requires element type."""
        with pytest.raises(SExprConversionError, match="Option type requires element type"):
            sexp_to_type(parse_sexp("(Option)"))

    def test_function_wrong_arity(self):
        """Function type requires param types and return type."""
        with pytest.raises(SExprConversionError, match="Function type requires param types and return type"):
            sexp_to_type(parse_sexp("(Function ())"))

    def test_function_params_not_list(self):
        """Function param types must be a list."""
        with pytest.raises(SExprConversionError, match="Function param types must be a list"):
            sexp_to_type(parse_sexp("(Function Int64 String)"))

    def test_unknown_type_constructor(self):
        """Unknown type constructor raises error."""
        with pytest.raises(SExprConversionError, match="Unknown type constructor"):
            sexp_to_type(parse_sexp("(UnknownType foo)"))


class TestSexpToExprErrors:
    """Tests for error handling in sexp_to_expr."""

    def test_untyped_symbol_error(self):
        """Untyped symbol (not starting with :) is not allowed."""
        with pytest.raises(SExprConversionError, match="Untyped symbol in expression context"):
            sexp_to_expr(SAtom(value="foo", quoted=False))

    def test_empty_list_error(self):
        """Empty list is not a valid expression."""
        with pytest.raises(SExprConversionError, match="Invalid expression"):
            sexp_to_expr(SList([]))

    def test_expr_with_quoted_head(self):
        """Expression must start with symbol, not string."""
        with pytest.raises(SExprConversionError, match="Expression must start with a symbol"):
            sexp_to_expr(SList([SAtom(value="var", quoted=True)]))

    def test_var_wrong_arity(self):
        """var requires name and type."""
        with pytest.raises(SExprConversionError, match="var requires name and type"):
            sexp_to_expr(parse_sexp("(var x)"))

    def test_lit_wrong_arity(self):
        """lit requires a value."""
        with pytest.raises(SExprConversionError, match="lit requires a value"):
            sexp_to_expr(parse_sexp("(lit)"))

    def test_lit_non_atom_value(self):
        """lit value must be an atom."""
        with pytest.raises(SExprConversionError, match="lit value must be an atom"):
            sexp_to_expr(parse_sexp("(lit (foo))"))

    def test_call_missing_function(self):
        """call requires function."""
        with pytest.raises(SExprConversionError, match="call requires function"):
            sexp_to_expr(parse_sexp("(call)"))

    def test_lambda_wrong_arity(self):
        """lambda requires params, return type, and body."""
        with pytest.raises(SExprConversionError, match="lambda requires params, return type, and body"):
            sexp_to_expr(parse_sexp("(lambda () Int64)"))

    def test_lambda_params_not_list(self):
        """lambda params must be a list."""
        with pytest.raises(SExprConversionError, match="lambda params must be a list"):
            sexp_to_expr(parse_sexp("(lambda x Int64 42)"))

    def test_lambda_param_wrong_format(self):
        """lambda param must be (name type)."""
        with pytest.raises(SExprConversionError, match="lambda param must be \\(name type\\)"):
            sexp_to_expr(parse_sexp("(lambda (x) Int64 42)"))

    def test_let_wrong_arity(self):
        """let requires (name type), init, and body."""
        with pytest.raises(SExprConversionError, match="let requires \\(name type\\), init, and body"):
            sexp_to_expr(parse_sexp("(let (x Int64) 42)"))

    def test_let_binding_wrong_format(self):
        """let binding must be (name type)."""
        with pytest.raises(SExprConversionError, match="let binding must be \\(name type\\)"):
            sexp_to_expr(parse_sexp("(let x 42 x)"))

    def test_if_wrong_arity(self):
        """if requires condition, then, and else."""
        with pytest.raises(SExprConversionError, match="if requires condition, then, and else"):
            sexp_to_expr(parse_sexp("(if true 1)"))

    def test_builtin_wrong_arity(self):
        """builtin requires name."""
        with pytest.raises(SExprConversionError, match="builtin requires name"):
            sexp_to_expr(parse_sexp("(builtin)"))

    def test_new_message_wrong_arity(self):
        """new-message requires module, name, and fields."""
        with pytest.raises(SExprConversionError, match="new-message requires module, name, and fields"):
            sexp_to_expr(parse_sexp("(new-message test)"))

    def test_oneof_wrong_arity(self):
        """oneof requires field name."""
        with pytest.raises(SExprConversionError, match="oneof requires field name"):
            sexp_to_expr(parse_sexp("(oneof)"))

    def test_list_wrong_arity(self):
        """list requires element type."""
        with pytest.raises(SExprConversionError, match="list requires element type"):
            sexp_to_expr(parse_sexp("(list)"))

    def test_get_field_wrong_arity(self):
        """get-field requires object and field name."""
        with pytest.raises(SExprConversionError, match="get-field requires object and field name"):
            sexp_to_expr(parse_sexp("(get-field (var x String))"))

    def test_get_element_wrong_arity(self):
        """get-element requires tuple and index."""
        with pytest.raises(SExprConversionError, match="get-element requires tuple and index"):
            sexp_to_expr(parse_sexp("(get-element (var x (Tuple Int64 String)))"))

    def test_get_element_non_int_index(self):
        """get-element index must be an integer literal."""
        with pytest.raises(SExprConversionError, match="get-element index must be an integer literal"):
            sexp_to_expr(parse_sexp('(get-element (var x (Tuple Int64 String)) "not-an-int")'))

    def test_seq_too_few_args(self):
        """seq requires at least 2 expressions."""
        with pytest.raises(SExprConversionError, match="seq requires at least 2 expressions"):
            sexp_to_expr(parse_sexp("(seq 1)"))

    def test_while_wrong_arity(self):
        """while requires condition and body."""
        with pytest.raises(SExprConversionError, match="while requires condition and body"):
            sexp_to_expr(parse_sexp("(while true)"))

    def test_foreach_wrong_arity(self):
        """foreach requires (var type), collection, and body."""
        with pytest.raises(SExprConversionError, match="foreach requires \\(var type\\), collection, and body"):
            sexp_to_expr(parse_sexp("(foreach (x Int64) (list Int64))"))

    def test_foreach_binding_wrong_format(self):
        """foreach var must be (name type)."""
        with pytest.raises(SExprConversionError, match="foreach var must be \\(name type\\)"):
            sexp_to_expr(parse_sexp("(foreach x (list Int64) x)"))

    def test_foreach_enumerated_wrong_arity(self):
        """foreach-enumerated requires (idx type), (var type), collection, and body."""
        with pytest.raises(SExprConversionError, match="foreach-enumerated requires \\(idx type\\), \\(var type\\), collection, and body"):
            sexp_to_expr(parse_sexp("(foreach-enumerated (i Int64) (x String) (list String))"))

    def test_foreach_enumerated_binding_wrong_format(self):
        """foreach-enumerated index var must be (name type)."""
        with pytest.raises(SExprConversionError, match="foreach-enumerated index var must be \\(name type\\)"):
            sexp_to_expr(parse_sexp("(foreach-enumerated i (x String) (list String) x)"))

    def test_assign_wrong_arity(self):
        """assign requires (var type) and expr."""
        with pytest.raises(SExprConversionError, match="assign requires \\(var type\\) and expr"):
            sexp_to_expr(parse_sexp("(assign (x Int64))"))

    def test_assign_binding_wrong_format(self):
        """assign var must be (name type)."""
        with pytest.raises(SExprConversionError, match="assign var must be \\(name type\\)"):
            sexp_to_expr(parse_sexp("(assign x 42)"))

    def test_return_wrong_arity(self):
        """return requires expr."""
        with pytest.raises(SExprConversionError, match="return requires expr"):
            sexp_to_expr(parse_sexp("(return)"))

    def test_unknown_expr_form(self):
        """Unknown expression form raises error."""
        with pytest.raises(SExprConversionError, match="Unknown expression form"):
            sexp_to_expr(parse_sexp("(unknown-form 123)"))
