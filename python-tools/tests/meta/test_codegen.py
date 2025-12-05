#!/usr/bin/env python3
"""Tests for code generation from action AST."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.target import Var, Symbol, Call, Lambda, Let, BaseType
from meta.codegen_python import generate_python, escape_identifier as escape_python
from meta.codegen_julia import generate_julia, escape_identifier as escape_julia
from meta.codegen_go import generate_go, escape_identifier as escape_go

_any_type = BaseType("Any")


def test_python_keyword_escaping():
    """Test that Python keywords are properly escaped."""
    # Test keyword variables
    assert escape_python("class") == "class_"
    assert escape_python("return") == "return_"
    assert escape_python("lambda") == "lambda_"

    # Test non-keywords
    assert escape_python("foo") == "foo"
    assert escape_python("my_var") == "my_var"

    # Test in expressions
    var = Var("class", _any_type)
    code = generate_python(var)
    assert code == "class_"

    print("✓ Python keyword escaping works")


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

    print("✓ Julia keyword escaping works")


def test_go_keyword_escaping():
    """Test that Go keywords are properly escaped."""
    # Test keyword variables
    assert escape_go("func") == "func_"
    assert escape_go("type") == "type_"
    assert escape_go("var") == "var_"

    # Test predeclared identifiers
    assert escape_go("string") == "string_"
    assert escape_go("int") == "int_"

    # Test non-keywords
    assert escape_go("foo") == "foo"
    assert escape_go("myVar") == "myVar"

    # Test in expressions
    var = Var("type", _any_type)
    code = generate_go(var)
    assert code == "type_"

    print("✓ Go keyword escaping works")


def test_python_call_generation():
    """Test Python function call generation."""
    # Simple call
    call = Call(Var("foo", _any_type), [Var("x", _any_type), Var("y", _any_type)])
    code = generate_python(call)
    assert code == "foo(x, y)"

    # Call with keyword argument
    call_kw = Call(Var("class", _any_type), [Var("arg", _any_type)])  # 'class' is a keyword
    code_kw = generate_python(call_kw)
    assert code_kw == "class_(arg)"

    # Nested call
    nested = Call(Var("outer", _any_type), [Call(Var("inner", _any_type), [Var("z", _any_type)])])
    code_nested = generate_python(nested)
    assert code_nested == "outer(inner(z))"

    print("✓ Python call generation works")


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

    print("✓ Julia call generation works")


def test_go_call_generation():
    """Test Go function call generation."""
    # Simple call
    call = Call(Var("foo", _any_type), [Var("x", _any_type), Var("y", _any_type)])
    code = generate_go(call)
    assert code == "foo(x, y)"

    # Call with keyword function name
    call_kw = Call(Var("func", _any_type), [Var("arg", _any_type)])
    code_kw = generate_go(call_kw)
    assert code_kw == "func_(arg)"

    print("✓ Go call generation works")


def test_python_let_generation():
    """Test Python Let-binding generation."""
    # Simple let
    let_expr = Let(Var("x", _any_type), Call(Var("parse_foo", _any_type), []), Var("x", _any_type))
    code = generate_python(let_expr)
    assert "x = parse_foo()" in code
    assert "return x" in code

    # Nested let
    nested_let = Let(Var("x", _any_type), Call(Var("parse_a", _any_type), []),
                     Let(Var("y", _any_type), Call(Var("parse_b", _any_type), []),
                         Call(Var("make", _any_type), [Var("x", _any_type), Var("y", _any_type)])))
    code_nested = generate_python(nested_let)
    assert "x = parse_a()" in code_nested
    assert "y = parse_b()" in code_nested
    assert "return make(x, y)" in code_nested

    # Let with keyword variable
    let_kw = Let(Var("class", _any_type), Call(Var("parse", _any_type), []), Var("class", _any_type))
    code_kw = generate_python(let_kw)
    assert "class_ = parse()" in code_kw
    assert "return class_" in code_kw

    print("✓ Python Let generation works")


def test_julia_let_generation():
    """Test Julia Let-binding generation."""
    # Simple let
    let_expr = Let(Var("x", _any_type), Call(Var("parse_foo", _any_type), []), Var("x", _any_type))
    code = generate_julia(let_expr)
    assert "let x = parse_foo(); x end" in code

    # Nested let
    nested_let = Let(Var("x", _any_type), Call(Var("parse_a", _any_type), []),
                     Let(Var("y", _any_type), Call(Var("parse_b", _any_type), []),
                         Call(Var("make", _any_type), [Var("x", _any_type), Var("y", _any_type)])))
    code_nested = generate_julia(nested_let)
    assert "let x = parse_a(), y = parse_b(); make(x, y) end" in code_nested

    # Let with keyword variable
    let_kw = Let(Var("end", _any_type), Call(Var("parse", _any_type), []), Var("end", _any_type))
    code_kw = generate_julia(let_kw)
    assert 'var"end"' in code_kw

    print("✓ Julia Let generation works")


def test_go_let_generation():
    """Test Go Let-binding generation (as IIFE)."""
    # Simple let
    let_expr = Let(Var("x", _any_type), Call(Var("parse_foo", _any_type), []), Var("x", _any_type))
    code = generate_go(let_expr)
    assert "func() interface{}" in code
    assert "x := parse_foo()" in code
    assert "return x" in code

    # Let with keyword variable
    let_kw = Let(Var("type", _any_type), Call(Var("parse", _any_type), []), Var("type", _any_type))
    code_kw = generate_go(let_kw)
    assert "type_ := parse()" in code_kw
    assert "return type_" in code_kw

    print("✓ Go Let generation works")


def test_python_lambda_generation():
    """Test Python lambda generation."""
    # Simple lambda
    lam = Lambda([Var("x", _any_type), Var("y", _any_type)], _any_type, Call(Var("Add", _any_type), [Var("x", _any_type), Var("y", _any_type)]))
    code = generate_python(lam)
    assert code == "lambda x, y: Add(x, y)"

    # Lambda with keyword parameter
    lam_kw = Lambda([Var("class", _any_type), Var("value", _any_type)], _any_type, Var("value", _any_type))
    code_kw = generate_python(lam_kw)
    assert code_kw == "lambda class_, value: value"

    print("✓ Python lambda generation works")


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

    print("✓ Julia lambda generation works")


def test_go_lambda_generation():
    """Test Go anonymous function generation."""
    # Simple lambda
    lam = Lambda([Var("x", _any_type), Var("y", _any_type)], _any_type, Call(Var("Add", _any_type), [Var("x", _any_type), Var("y", _any_type)]))
    code = generate_go(lam)
    assert "func(x interface{}, y interface{}) interface{}" in code
    assert "return Add(x, y)" in code

    print("✓ Go lambda generation works")


if __name__ == "__main__":
    test_python_keyword_escaping()
    test_julia_keyword_escaping()
    test_go_keyword_escaping()
    test_python_call_generation()
    test_julia_call_generation()
    test_go_call_generation()
    test_python_let_generation()
    test_julia_let_generation()
    test_go_let_generation()
    test_python_lambda_generation()
    test_julia_lambda_generation()
    test_go_lambda_generation()
    print("\n✓ All code generation tests passed")
