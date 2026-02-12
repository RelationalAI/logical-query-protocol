#!/usr/bin/env python3
"""Tests for Go code generation from action AST."""

from meta.target import (
    Var, Lit, Symbol, NewMessage, ListExpr, Call, Let,
    IfElse, Seq, While, Assign, Return, FunDef, ParseNonterminalDef,
    BaseType, MessageType, ListType, OptionType, GetElement,
)
from meta.target_builtins import make_builtin
from meta.grammar import Nonterminal
from meta.codegen_go import (
    GoCodeGenerator,
    escape_identifier as escape_go,
    generate_go_lines as generate_go,
    to_pascal_case,
)
from meta.gensym import reset as reset_gensym

_any_type = BaseType("Any")
_int_type = BaseType("Int64")
_str_type = BaseType("String")
_bool_type = BaseType("Boolean")


def test_go_keyword_escaping():
    """Test that Go keywords are properly escaped."""
    assert escape_go("type") == "type_"
    assert escape_go("range") == "range_"
    assert escape_go("map") == "map_"
    assert escape_go("return") == "return_"

    # Non-keywords unchanged
    assert escape_go("foo") == "foo"
    assert escape_go("my_var") == "my_var"

    # In expressions
    var = Var("type", _any_type)
    code = generate_go(var, [], "")
    assert code == "type_"


def test_go_pascal_case():
    """Test snake_case to PascalCase conversion."""
    assert to_pascal_case("foo_bar") == "FooBar"
    assert to_pascal_case("id_low") == "IdLow"
    assert to_pascal_case("simple") == "Simple"
    assert to_pascal_case("a_b_c") == "ABC"


def test_go_literal_generation():
    """Test Go literal code generation."""
    gen = GoCodeGenerator()

    reset_gensym()
    lines = []
    assert gen.generate_lines(Lit(42), lines, "") == "42"
    assert gen.generate_lines(Lit(True), lines, "") == "true"
    assert gen.generate_lines(Lit(False), lines, "") == "false"
    assert gen.generate_lines(Lit("hello"), lines, "") == '"hello"'
    assert gen.generate_lines(Lit(None), lines, "") == "nil"


def test_go_string_escaping():
    """Test Go string literal escaping."""
    gen = GoCodeGenerator()
    lines = []

    assert gen.generate_lines(Lit("line\nnext"), lines, "") == '"line\\nnext"'
    assert gen.generate_lines(Lit('say "hi"'), lines, "") == '"say \\"hi\\""'
    assert gen.generate_lines(Lit("tab\there"), lines, "") == '"tab\\there"'


def test_go_call_generation():
    """Test Go function call generation.

    Go codegen assigns call results to temp vars via :=, so the return
    value is a temp var name and the call appears in the lines list.
    """
    gen = GoCodeGenerator()
    gen.reset_declared_vars()
    reset_gensym()

    lines = []
    call = Call(Var("foo", _any_type), [Var("x", _any_type), Var("y", _any_type)])
    result = gen.generate_lines(call, lines, "")
    code = "\n".join(lines)
    assert "foo(x, y)" in code
    assert result is not None


def test_go_let_generation():
    """Test Go Let-binding generation."""
    gen = GoCodeGenerator()
    reset_gensym()

    lines = []
    let_expr = Let(Var("x", _any_type), Call(Var("parse_foo", _any_type), []), Var("x", _any_type))
    result = gen.generate_lines(let_expr, lines, "")
    code = "\n".join(lines)
    assert "parse_foo()" in code
    assert "x" in code
    assert result is not None
    assert result.strip().endswith("x") or result == "x"


def test_go_builtin_generation():
    """Test Go builtin function code generation."""
    gen = GoCodeGenerator()

    # Test 'not' builtin
    reset_gensym()
    lines = []
    expr = Call(make_builtin("not"), [Var("x", _bool_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "!x"

    # Test 'equal' builtin
    reset_gensym()
    lines = []
    expr = Call(make_builtin("equal"), [Var("a", _any_type), Var("b", _any_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "a == b"

    # Test 'is_none' builtin
    reset_gensym()
    lines = []
    expr = Call(make_builtin("is_none"), [Var("x", OptionType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "x == nil"

    # Test 'is_some' builtin
    reset_gensym()
    lines = []
    expr = Call(make_builtin("is_some"), [Var("x", OptionType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "x != nil"

    # Test 'length' builtin
    reset_gensym()
    lines = []
    expr = Call(make_builtin("length"), [Var("lst", ListType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "int64(len(lst))"


def test_go_list_expr_generation():
    """Test Go list expression code generation."""
    gen = GoCodeGenerator()

    # Empty list with known type
    reset_gensym()
    lines = []
    expr = ListExpr([], _int_type)
    result = gen.generate_lines(expr, lines, "")
    assert result == "[]int64{}"

    # List with elements
    reset_gensym()
    lines = []
    expr = ListExpr([Lit(1), Lit(2), Lit(3)], _int_type)
    result = gen.generate_lines(expr, lines, "")
    assert result == "[]int64{1, 2, 3}"


def test_go_symbol_generation():
    """Test Go symbol code generation."""
    gen = GoCodeGenerator()

    reset_gensym()
    lines = []
    expr = Symbol("add")
    result = gen.generate_lines(expr, lines, "")
    assert result == '"add"'


def test_go_type_generation():
    """Test Go type generation."""
    gen = GoCodeGenerator()

    # Base types
    assert gen.gen_type(BaseType("Int32")) == "int32"
    assert gen.gen_type(BaseType("Int64")) == "int64"
    assert gen.gen_type(BaseType("Float64")) == "float64"
    assert gen.gen_type(BaseType("String")) == "string"
    assert gen.gen_type(BaseType("Boolean")) == "bool"
    assert gen.gen_type(BaseType("Bytes")) == "[]byte"

    # Message type
    assert gen.gen_type(MessageType("logic", "Expr")) == "*pb.Expr"

    # List type
    assert gen.gen_type(ListType(BaseType("Int64"))) == "[]int64"

    # Option type — scalar inner types become pointer
    assert gen.gen_type(OptionType(BaseType("String"))) == "*string"

    # Nested types
    assert gen.gen_type(ListType(MessageType("logic", "Expr"))) == "[]*pb.Expr"
    # Option of already-nullable type collapses
    assert gen.gen_type(OptionType(MessageType("logic", "Expr"))) == "*pb.Expr"


def test_go_assignment_generation():
    """Test Go assignment code generation with := vs = tracking."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()

    # First assignment uses :=
    reset_gensym()
    lines = []
    expr = Assign(Var("x", _int_type), Lit(42))
    gen.generate_lines(expr, lines, "")
    assert "x := 42" in lines[0]

    # Second assignment uses =
    lines = []
    expr = Assign(Var("x", _int_type), Lit(100))
    gen.generate_lines(expr, lines, "")
    assert "x = 100" in lines[0]


def test_go_return_generation():
    """Test Go return statement code generation."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()

    reset_gensym()
    lines = []
    expr = Return(Var("result", _any_type))
    result = gen.generate_lines(expr, lines, "")
    assert result is None
    assert "return result" in lines[0]


def test_go_if_else_generation():
    """Test Go if-else code generation."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()

    reset_gensym()
    lines = []
    expr = IfElse(Var("cond", _bool_type), Lit("yes"), Lit("no"))
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)
    assert "if cond {" in code
    assert "} else {" in code
    # Result should be a temp variable
    assert result is not None and result.startswith("_t")


def test_go_while_generation():
    """Test Go while loop (for loop) code generation."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()

    reset_gensym()
    lines = []
    expr = While(Var("running", _bool_type), Call(Var("do_work", _any_type), []))
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)
    assert "for running {" in code
    assert "do_work()" in code


def test_go_seq_generation():
    """Test Go sequence expression code generation."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()

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


def test_go_message_generation():
    """Test Go NewMessage constructor code generation."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()

    # Simple message with no fields
    reset_gensym()
    lines = []
    expr = NewMessage("logic", "Expr", ())
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)
    assert "&pb.Expr{}" in code


def test_go_fun_def_generation():
    """Test Go function definition code generation."""
    gen = GoCodeGenerator()

    reset_gensym()
    func = FunDef(
        name="add",
        params=[Var("x", _int_type), Var("y", _int_type)],
        return_type=_int_type,
        body=Call(make_builtin("add"), [Var("x", _int_type), Var("y", _int_type)]),
    )
    code = gen.generate_def(func)
    # FunDef generates non-method functions
    assert "func add(x int64, y int64) int64 {" in code
    assert "return" in code


def test_go_visit_nonterminal_def_generation():
    """Test Go ParseNonterminalDef code generation."""
    gen = GoCodeGenerator()

    nt = Nonterminal("expr", MessageType("logic", "Expr"))

    reset_gensym()
    parse_def = ParseNonterminalDef(
        nonterminal=nt,
        params=[],
        return_type=MessageType("logic", "Expr"),
        body=NewMessage("logic", "Expr", ()),
    )
    code = gen.generate_def(parse_def)
    assert "func (p *Parser) parse_expr() *pb.Expr {" in code
    assert "return" in code


def test_go_declared_var_tracking():
    """Test that Go variable declaration tracking works correctly."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()

    assert not gen.is_declared("x")
    gen.mark_declared("x")
    assert gen.is_declared("x")

    # Reset clears all
    gen.reset_declared_vars()
    assert not gen.is_declared("x")


def test_go_get_element_generation():
    """Test Go GetElement with type assertion."""
    gen = GoCodeGenerator()

    reset_gensym()
    lines = []
    expr = GetElement(Var("pair", _any_type), 0)
    result = gen.generate_lines(expr, lines, "")
    assert result is not None
    assert "pair[0]" in result

    reset_gensym()
    lines = []
    expr = GetElement(Var("pair", _any_type), 1)
    result = gen.generate_lines(expr, lines, "")
    assert result is not None
    assert "pair[1]" in result


def test_go_and_short_circuit_with_side_effects():
    """Test that 'and' preserves short-circuit semantics when RHS has side-effects."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()
    reset_gensym()
    lines = []

    # and(a, f(x) == 42)
    # The call f(x) generates a temp-var assignment.
    # That assignment must be guarded by the if.
    expr = Call(make_builtin("and"), [
        Var("a", _bool_type),
        Call(make_builtin("equal"), [
            Call(Var("f", _any_type), [Var("x", _any_type)]),
            Lit(42),
        ]),
    ])
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)

    assert result is not None
    assert "f(x)" not in code.split("if ")[0], \
        f"f(x) was hoisted above the if guard:\n{code}"
    assert "if " in code, f"Expected if-else for short-circuit, got:\n{code}"
    assert "} else {" in code


def test_go_or_short_circuit_with_side_effects():
    """Test that 'or' preserves short-circuit semantics when RHS has side-effects."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()
    reset_gensym()
    lines = []

    # or(a, f(x) == 42)
    expr = Call(make_builtin("or"), [
        Var("a", _bool_type),
        Call(make_builtin("equal"), [
            Call(Var("f", _any_type), [Var("x", _any_type)]),
            Lit(42),
        ]),
    ])
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)

    assert result is not None
    assert "f(x)" not in code.split("if ")[0], \
        f"f(x) was hoisted above the if guard:\n{code}"
    assert "if " in code, f"Expected if-else for short-circuit, got:\n{code}"
    assert "} else {" in code


def test_go_and_without_side_effects_uses_template():
    """Test that 'and' without side-effects uses the simple template."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()
    reset_gensym()
    lines = []

    expr = Call(make_builtin("and"), [
        Var("a", _bool_type),
        Var("b", _bool_type),
    ])
    result = gen.generate_lines(expr, lines, "")
    assert result == "(a && b)"
    assert len(lines) == 0


def test_go_or_without_side_effects_uses_template():
    """Test that 'or' without side-effects uses the simple template."""
    gen = GoCodeGenerator()
    gen.reset_declared_vars()
    reset_gensym()
    lines = []

    expr = Call(make_builtin("or"), [
        Var("a", _bool_type),
        Var("b", _bool_type),
    ])
    result = gen.generate_lines(expr, lines, "")
    assert result == "(a || b)"
    assert len(lines) == 0


if __name__ == "__main__":
    test_go_keyword_escaping()
    test_go_pascal_case()
    test_go_literal_generation()
    test_go_string_escaping()
    test_go_call_generation()
    test_go_let_generation()
    test_go_builtin_generation()
    test_go_list_expr_generation()
    test_go_symbol_generation()
    test_go_type_generation()
    test_go_assignment_generation()
    test_go_return_generation()
    test_go_if_else_generation()
    test_go_while_generation()
    test_go_seq_generation()
    test_go_message_generation()
    test_go_fun_def_generation()
    test_go_visit_nonterminal_def_generation()
    test_go_declared_var_tracking()
    test_go_get_element_generation()
    test_go_and_short_circuit_with_side_effects()
    test_go_or_short_circuit_with_side_effects()
    test_go_and_without_side_effects_uses_template()
    test_go_or_without_side_effects_uses_template()
