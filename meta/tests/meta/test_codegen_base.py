#!/usr/bin/env python3
"""Tests for base code generation infrastructure."""

from meta.codegen_base import PARSER_CONFIG
from meta.codegen_go import GoCodeGenerator
from meta.codegen_julia import JuliaCodeGenerator
from meta.codegen_python import PythonCodeGenerator
from meta.codegen_templates import BuiltinTemplate
from meta.gensym import reset as reset_gensym
from meta.target import BaseType, Call, Lit, Var

_any_type = BaseType("Any")


def test_register_builtin_from_template():
    """Register a template-based builtin, call it, verify output."""
    gen = PythonCodeGenerator()
    gen.register_builtin_from_template("double", BuiltinTemplate("({0} * 2)"))
    lines = []
    result = gen.gen_builtin_call("double", ["x"], lines, "")
    assert result is not None
    assert result.value == "(x * 2)"
    assert result.statements == []


def test_register_builtin_from_template_with_statements():
    """Template with both value and statements generates both."""
    gen = PythonCodeGenerator()
    gen.register_builtin_from_template(
        "log_and_return",
        BuiltinTemplate("{0}", ["print({0})"]),
    )
    lines = []
    result = gen.gen_builtin_call("log_and_return", ["val"], lines, "")
    assert result is not None
    assert result.value == "val"
    assert result.statements == ["print(val)"]


def test_builtin_arity_validation():
    """Registered builtin with wrong arity returns None (falls through)."""
    gen = PythonCodeGenerator()
    # "not" is in BUILTIN_REGISTRY with arity 1.
    # Calling with 2 args should fail the arity check and return None.
    result = gen.gen_builtin_call("not", ["a", "b"], [], "")
    assert result is None


def test_generate_lit_values():
    """Literal generation across types for all three languages."""
    py = PythonCodeGenerator()
    jl = JuliaCodeGenerator(config=PARSER_CONFIG)
    go = GoCodeGenerator()

    cases = [
        (Lit(42), "42", "42", "42"),
        (Lit(True), "True", "true", "true"),
        (Lit(False), "False", "false", "false"),
        (Lit("hello"), '"hello"', '"hello"', '"hello"'),
        (Lit(""), '""', '""', '""'),
        (Lit(None), "None", "nothing", "nil"),
    ]
    for expr, py_exp, jl_exp, go_exp in cases:
        reset_gensym()
        assert py.generate_lines(expr, [], "") == py_exp, f"Python failed on {expr}"
        assert jl.generate_lines(expr, [], "") == jl_exp, f"Julia failed on {expr}"
        assert go.generate_lines(expr, [], "") == go_exp, f"Go failed on {expr}"


def test_generate_deeply_nested_expr():
    """4-level nested Call produces valid output in all three generators."""
    py = PythonCodeGenerator()
    jl = JuliaCodeGenerator(config=PARSER_CONFIG)
    go = GoCodeGenerator()

    inner = Call(Var("d", _any_type), [Var("x", _any_type)])
    level3 = Call(Var("c", _any_type), [inner])
    level2 = Call(Var("b", _any_type), [level3])
    expr = Call(Var("a", _any_type), [level2])

    for gen in [py, jl, go]:
        reset_gensym()
        lines = []
        result = gen.generate_lines(expr, lines, "")
        assert result is not None
        code = "\n".join(lines) + "\n" + result
        assert "d(x)" in code
        assert "c(" in code
        assert "b(" in code
        assert "a(" in code


if __name__ == "__main__":
    test_register_builtin_from_template()
    test_register_builtin_from_template_with_statements()
    test_builtin_arity_validation()
    test_generate_lit_values()
    test_generate_deeply_nested_expr()
