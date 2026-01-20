#!/usr/bin/env python3
"""Tests for Julia code generation from action AST."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.target import Var, Call, Lambda, Let, BaseType
from meta.codegen_julia import generate_julia, escape_identifier as escape_julia

_any_type = BaseType("Any")


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

    print("✓ Julia Let generation works")


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


if __name__ == "__main__":
    test_julia_keyword_escaping()
    test_julia_call_generation()
    test_julia_let_generation()
    test_julia_lambda_generation()
    print("\n✓ All Julia code generation tests passed")
