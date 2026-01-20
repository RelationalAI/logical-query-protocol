#!/usr/bin/env python3
"""Tests for Python code generation from action AST."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.target import Var, Call, Lambda, Let, BaseType
from meta.codegen_python import generate_python, escape_identifier as escape_python

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


def test_python_let_generation():
    """Test Python Let-binding generation."""
    # Simple let
    let_expr = Let(Var("x", _any_type), Call(Var("parse_foo", _any_type), []), Var("x", _any_type))
    code = generate_python(let_expr)
    assert "_t" in code and "parse_foo()" in code
    assert "x = _t" in code or "x = parse_foo()" in code
    assert code.strip().endswith("x")

    # Nested let
    nested_let = Let(Var("x", _any_type), Call(Var("parse_a", _any_type), []),
                     Let(Var("y", _any_type), Call(Var("parse_b", _any_type), []),
                         Call(Var("make", _any_type), [Var("x", _any_type), Var("y", _any_type)])))
    code_nested = generate_python(nested_let)
    assert "parse_a()" in code_nested and "x = " in code_nested
    assert "parse_b()" in code_nested and "y = " in code_nested
    assert "make(x, y)" in code_nested

    # Let with keyword variable
    let_kw = Let(Var("class", _any_type), Call(Var("parse", _any_type), []), Var("class", _any_type))
    code_kw = generate_python(let_kw)
    assert "parse()" in code_kw and "class_ = " in code_kw
    assert code_kw.strip().endswith("class_")

    print("✓ Python Let generation works")


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


if __name__ == "__main__":
    test_python_keyword_escaping()
    test_python_call_generation()
    test_python_let_generation()
    test_python_lambda_generation()
    print("\n✓ All Python code generation tests passed")
