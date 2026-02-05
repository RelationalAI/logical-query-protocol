#!/usr/bin/env python3
"""Tests for Julia code generation from action AST."""

from meta.target import (
    Var, Lit, Symbol, Builtin, NamedFun, NewMessage, ListExpr, Call, Lambda, Let,
    IfElse, Seq, Assign, Return, FunDef, VisitNonterminalDef,
    BaseType, MessageType, ListType, OptionType, GetElement,
)
from meta.grammar import Nonterminal
from meta.codegen_julia import (
    generate_julia,
    escape_identifier as escape_julia,
    JuliaCodeGenerator,
)
from meta.codegen_base import ALREADY_RETURNED
from meta.gensym import reset as reset_gensym

_any_type = BaseType("Any")
_int_type = BaseType("Int64")
_str_type = BaseType("String")
_bool_type = BaseType("Boolean")


def test_julia_keyword_escaping():
    """Test that Julia keywords are properly escaped."""
    # Test keyword variables
    assert escape_julia("function") == 'var"function"'
    assert escape_julia("end") == 'var"end"'
    assert escape_julia("let") == 'var"let"'

    # Test non-keywords
    assert escape_julia("foo") == "foo"
    assert escape_julia("my_var") == "my_var"

    # Test in expressions
    var = Var("function", _any_type)
    code = generate_julia(var)
    assert code == 'var"function"'


def test_julia_call_generation():
    """Test Julia function call generation."""
    # Simple call
    call = Call(Var("foo", _any_type), [Var("x", _any_type), Var("y", _any_type)])
    code = generate_julia(call)
    assert code == "foo(x, y)"

    # Call with keyword function name
    call_kw = Call(Var("function", _any_type), [Var("arg", _any_type)])
    code_kw = generate_julia(call_kw)
    assert code_kw == 'var"function"(arg)'


def test_julia_let_generation():
    """Test Julia Let-binding generation."""
    # Simple let
    let_expr = Let(Var("x", _any_type), Call(Var("parse_foo", _any_type), []), Var("x", _any_type))
    code = generate_julia(let_expr)
    assert "parse_foo()" in code and "x = " in code

    # Nested let
    nested_let = Let(Var("x", _any_type), Call(Var("parse_a", _any_type), []),
                     Let(Var("y", _any_type), Call(Var("parse_b", _any_type), []),
                         Call(Var("make", _any_type), [Var("x", _any_type), Var("y", _any_type)])))
    code_nested = generate_julia(nested_let)
    assert "parse_a()" in code_nested and "x = " in code_nested
    assert "parse_b()" in code_nested and "y = " in code_nested
    assert "make(x, y)" in code_nested

    # Let with keyword variable
    let_kw = Let(Var("end", _any_type), Call(Var("parse", _any_type), []), Var("end", _any_type))
    code_kw = generate_julia(let_kw)
    assert 'var"end"' in code_kw


def test_julia_lambda_generation():
    """Test Julia anonymous function generation."""
    # Simple lambda
    lam = Lambda([Var("x", _any_type), Var("y", _any_type)], _any_type, Call(Var("Add", _any_type), [Var("x", _any_type), Var("y", _any_type)]))
    code = generate_julia(lam)
    assert code == "(x, y) -> Add(x, y)"

    # Lambda with keyword parameter
    lam_kw = Lambda([Var("struct", _any_type), Var("value", _any_type)], _any_type, Var("value", _any_type))
    code_kw = generate_julia(lam_kw)
    assert 'var"struct"' in code_kw


def test_julia_builtin_generation():
    """Test Julia builtin function code generation."""
    gen = JuliaCodeGenerator()

    # Test 'not' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("not"), [Var("x", _bool_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "!x"
    assert len(lines) == 0

    # Test 'equal' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("equal"), [Var("a", _any_type), Var("b", _any_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "a == b"

    # Test 'list_concat' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("list_concat"), [Var("lst", ListType(_int_type)), Var("other", ListType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "vcat(lst, other)"

    # Test 'is_none' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("is_none"), [Var("x", OptionType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "isnothing(x)"

    # Test 'is_some' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("is_some"), [Var("x", OptionType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "!isnothing(x)"

    # Test 'and' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("and"), [Var("a", _bool_type), Var("b", _bool_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "(a && b)"

    # Test 'or' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("or"), [Var("a", _bool_type), Var("b", _bool_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "(a || b)"

    # Test 'add' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("add"), [Var("x", _int_type), Var("y", _int_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "(x + y)"

    # Test 'length' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("length"), [Var("lst", ListType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "length(lst)"

    # Test 'tuple' builtin (variadic)
    reset_gensym()
    lines = []
    expr = Call(Builtin("tuple"), [Var("a", _int_type), Var("b", _str_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "(a, b,)"


def test_julia_get_element_generation():
    """Test Julia GetElement with 1-based indexing."""
    gen = JuliaCodeGenerator()

    # GetElement uses 1-based indexing in Julia
    reset_gensym()
    lines = []
    expr = GetElement(Var("pair", _any_type), 0)
    result = gen.generate_lines(expr, lines, "")
    assert result == "pair[1]"  # 0-based -> 1-based

    reset_gensym()
    lines = []
    expr = GetElement(Var("pair", _any_type), 1)
    result = gen.generate_lines(expr, lines, "")
    assert result == "pair[2]"  # 0-based -> 1-based


def test_julia_if_else_generation():
    """Test Julia if-else code generation."""
    gen = JuliaCodeGenerator()

    # Basic if-else
    reset_gensym()
    lines = []
    expr = IfElse(Var("cond", _bool_type), Lit("yes"), Lit("no"))
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)
    assert "if cond" in code
    assert "else" in code
    assert "end" in code
    # Result should be a temp variable
    assert result.startswith("_t")

    # Short-circuit optimization: cond or else_value
    reset_gensym()
    lines = []
    expr = IfElse(Var("cond", _bool_type), Lit(True), Var("default", _bool_type))
    result = gen.generate_lines(expr, lines, "")
    assert "||" in result or "cond" in result

    # Short-circuit optimization: cond and then_value
    reset_gensym()
    lines = []
    expr = IfElse(Var("cond", _bool_type), Var("value", _bool_type), Lit(False))
    result = gen.generate_lines(expr, lines, "")
    assert "&&" in result or "cond" in result


def test_julia_symbol_generation():
    """Test Julia symbol code generation."""
    gen = JuliaCodeGenerator()

    reset_gensym()
    lines = []
    expr = Symbol("add")
    result = gen.generate_lines(expr, lines, "")
    assert result == ":add"


def test_julia_list_expr_generation():
    """Test Julia list expression code generation."""
    gen = JuliaCodeGenerator()

    # Empty list
    reset_gensym()
    lines = []
    expr = ListExpr([], _int_type)
    result = gen.generate_lines(expr, lines, "")
    assert "Int64[]" in result

    # List with elements
    reset_gensym()
    lines = []
    expr = ListExpr([Lit(1), Lit(2), Lit(3)], _int_type)
    result = gen.generate_lines(expr, lines, "")
    assert "Int64[1, 2, 3]" in result


def test_julia_type_generation():
    """Test Julia type hint generation."""
    gen = JuliaCodeGenerator()

    # Base types
    assert gen.gen_type(BaseType("Int32")) == "Int32"
    assert gen.gen_type(BaseType("Int64")) == "Int64"
    assert gen.gen_type(BaseType("Float64")) == "Float64"
    assert gen.gen_type(BaseType("String")) == "String"
    assert gen.gen_type(BaseType("Boolean")) == "Bool"
    assert gen.gen_type(BaseType("Bytes")) == "Vector{UInt8}"

    # Message type
    assert gen.gen_type(MessageType("logic", "Expr")) == "Proto.Expr"

    # List type
    assert gen.gen_type(ListType(BaseType("Int64"))) == "Vector{Int64}"

    # Option type
    assert gen.gen_type(OptionType(BaseType("String"))) == "Union{Nothing, String}"


def test_julia_fun_def_generation():
    """Test Julia function definition code generation."""
    gen = JuliaCodeGenerator()

    # Simple function
    reset_gensym()
    func = FunDef(
        name="add",
        params=[Var("x", _int_type), Var("y", _int_type)],
        return_type=_int_type,
        body=Call(Builtin("add"), [Var("x", _int_type), Var("y", _int_type)]),
    )
    code = gen.generate_def(func)
    assert "function add(x::Int64, y::Int64)::Int64" in code
    assert "return" in code
    assert "end" in code

    # Function with keyword parameter
    reset_gensym()
    func = FunDef(
        name="process",
        params=[Var("struct", _str_type)],
        return_type=_str_type,
        body=Var("struct", _str_type),
    )
    code = gen.generate_def(func)
    assert 'var"struct"' in code
    assert "return" in code


def test_julia_visit_nonterminal_def_generation():
    """Test Julia VisitNonterminalDef code generation."""
    gen = JuliaCodeGenerator()

    # Create a nonterminal
    nt = Nonterminal("expr", MessageType("logic", "Expr"))

    # Simple parse method
    reset_gensym()
    parse_def = VisitNonterminalDef(
        visitor_name="parse",
        nonterminal=nt,
        params=[],
        return_type=MessageType("logic", "Expr"),
        body=NewMessage("logic", "Expr", ()),
    )
    code = gen.generate_def(parse_def)
    assert "function parse_expr(parser::Parser)::Proto.Expr" in code
    assert "return" in code
    assert "end" in code


def test_julia_return_generation():
    """Test Julia return statement code generation."""
    gen = JuliaCodeGenerator()

    reset_gensym()
    lines = []
    expr = Return(Var("result", _any_type))
    result = gen.generate_lines(expr, lines, "")
    # Return generates a return statement and returns ALREADY_RETURNED sentinel
    assert result == ALREADY_RETURNED
    assert "return result" in lines[0]


def test_julia_assign_generation():
    """Test Julia assignment code generation."""
    gen = JuliaCodeGenerator()

    reset_gensym()
    lines = []
    expr = Assign(Var("x", _int_type), Lit(42))
    result = gen.generate_lines(expr, lines, "")
    assert result == "nothing"
    assert "x = 42" in lines[0]


def test_julia_seq_generation():
    """Test Julia sequence expression code generation."""
    gen = JuliaCodeGenerator()

    # Sequence of expressions
    reset_gensym()
    lines = []
    expr = Seq([
        Call(Var("setup", _any_type), []),
        Call(Var("process", _any_type), []),
        Var("result", _any_type),
    ])
    result = gen.generate_lines(expr, lines, "")
    assert result == "result"
    code = "\n".join(lines)
    assert "setup()" in code
    assert "process()" in code


def test_julia_helper_function_calling_another():
    """Test Julia code generation for helper function calling another function."""
    gen = JuliaCodeGenerator()
    reset_gensym()

    # Equivalent to:
    # function wrapper(x::Int64)::Int64
    #     return Parser.helper(x)
    # end
    func = FunDef(
        name="wrapper",
        params=[Var("x", _int_type)],
        return_type=_int_type,
        body=Call(NamedFun("helper"), [Var("x", _int_type)]),
    )
    code = gen.generate_def(func)
    assert "function wrapper(x::Int64)::Int64" in code
    assert "Parser.helper(x)" in code


if __name__ == "__main__":
    test_julia_keyword_escaping()
    test_julia_call_generation()
    test_julia_let_generation()
    test_julia_lambda_generation()
    test_julia_builtin_generation()
    test_julia_get_element_generation()
    test_julia_if_else_generation()
    test_julia_symbol_generation()
    test_julia_list_expr_generation()
    test_julia_type_generation()
    test_julia_fun_def_generation()
    test_julia_visit_nonterminal_def_generation()
    test_julia_return_generation()
    test_julia_assign_generation()
    test_julia_seq_generation()
    test_julia_helper_function_calling_another()
