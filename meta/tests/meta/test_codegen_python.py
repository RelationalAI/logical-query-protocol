#!/usr/bin/env python3
"""Tests for Python code generation from action AST."""

from meta.codegen_python import (
    PythonCodeGenerator,
    generate_python,
)
from meta.codegen_python import (
    escape_identifier as escape_python,
)
from meta.gensym import reset as reset_gensym
from meta.grammar import Nonterminal
from meta.target import (
    Assign,
    BaseType,
    Call,
    FunctionType,
    FunDef,
    GetElement,
    IfElse,
    Lambda,
    Let,
    ListExpr,
    ListType,
    Lit,
    MessageType,
    NamedFun,
    NewMessage,
    OptionType,
    ParseNonterminalDef,
    Return,
    Seq,
    Symbol,
    Var,
    While,
)
from meta.target_builtins import make_builtin

_any_type = BaseType("Any")
_int_type = BaseType("Int64")
_str_type = BaseType("String")
_bool_type = BaseType("Boolean")


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


def test_python_call_generation():
    """Test Python function call generation."""
    # Simple call
    call = Call(Var("foo", _any_type), [Var("x", _any_type), Var("y", _any_type)])
    code = generate_python(call)
    assert code == "foo(x, y)"

    # Call with keyword argument
    call_kw = Call(Var("class", _any_type), [Var("arg", _any_type)])
    code_kw = generate_python(call_kw)
    assert code_kw == "class_(arg)"

    # Nested call
    nested = Call(
        Var("outer", _any_type), [Call(Var("inner", _any_type), [Var("z", _any_type)])]
    )
    code_nested = generate_python(nested)
    assert code_nested == "outer(inner(z))"


def test_python_let_generation():
    """Test Python Let-binding generation."""
    reset_gensym()

    # Simple let
    let_expr = Let(
        Var("x", _any_type), Call(Var("parse_foo", _any_type), []), Var("x", _any_type)
    )
    code = generate_python(let_expr)
    assert "_t" in code and "parse_foo()" in code
    assert any(s in code for s in ("x = _t", "x = parse_foo()"))
    assert code.strip().endswith("x")

    # Nested let
    reset_gensym()
    nested_let = Let(
        Var("x", _any_type),
        Call(Var("parse_a", _any_type), []),
        Let(
            Var("y", _any_type),
            Call(Var("parse_b", _any_type), []),
            Call(Var("make", _any_type), [Var("x", _any_type), Var("y", _any_type)]),
        ),
    )
    code_nested = generate_python(nested_let)
    assert "parse_a()" in code_nested and "x = " in code_nested
    assert "parse_b()" in code_nested and "y = " in code_nested
    assert "make(x, y)" in code_nested

    # Let with keyword variable
    reset_gensym()
    let_kw = Let(
        Var("class", _any_type),
        Call(Var("parse", _any_type), []),
        Var("class", _any_type),
    )
    code_kw = generate_python(let_kw)
    assert "parse()" in code_kw and "class_ = " in code_kw
    assert code_kw.strip().endswith("class_")


def test_python_lambda_generation():
    """Test Python lambda generation."""
    # Simple lambda
    lam = Lambda(
        [Var("x", _any_type), Var("y", _any_type)],
        _any_type,
        Call(Var("Add", _any_type), [Var("x", _any_type), Var("y", _any_type)]),
    )
    code = generate_python(lam)
    assert code == "lambda x, y: Add(x, y)"

    # Lambda with keyword parameter
    lam_kw = Lambda(
        [Var("class", _any_type), Var("value", _any_type)],
        _any_type,
        Var("value", _any_type),
    )
    code_kw = generate_python(lam_kw)
    assert code_kw == "lambda class_, value: value"


def test_python_builtin_generation():
    """Test Python builtin function code generation."""
    gen = PythonCodeGenerator()

    # Test 'not' builtin
    reset_gensym()
    lines = []
    expr = Call(make_builtin("not"), [Var("x", _bool_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "not x"
    assert len(lines) == 0

    # Test 'equal' builtin
    reset_gensym()
    lines = []
    expr = Call(make_builtin("equal"), [Var("a", _any_type), Var("b", _any_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "a == b"

    # Test 'list_concat' builtin
    reset_gensym()
    lines = []
    expr = Call(
        make_builtin("list_concat"),
        [Var("lst", ListType(_int_type)), Var("other", ListType(_int_type))],
    )
    result = gen.generate_lines(expr, lines, "")
    assert result == "(list(lst) + list(other if other is not None else []))"

    # Test 'list_push' builtin (mutating push with statement)
    reset_gensym()
    lines = []
    expr = Call(
        make_builtin("list_push"),
        [Var("lst", ListType(_int_type)), Var("item", _int_type)],
    )
    result = gen.generate_lines(expr, lines, "")
    assert result == "None"
    assert lines == ["lst.append(item)"]

    # Test 'is_none' builtin
    reset_gensym()
    lines = []
    expr = Call(make_builtin("is_none"), [Var("x", OptionType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "x is None"

    # Test 'length' builtin
    reset_gensym()
    lines = []
    expr = Call(make_builtin("length"), [Var("lst", ListType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "len(lst)"

    # Test 'tuple' builtin (variadic)
    reset_gensym()
    lines = []
    expr = Call(make_builtin("tuple"), [Var("a", _int_type), Var("b", _str_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "(a, b,)"


def test_python_get_element_generation():
    """Test Python GetElement with 0-based indexing."""
    gen = PythonCodeGenerator()

    # GetElement uses 0-based indexing in Python
    reset_gensym()
    lines = []
    expr = GetElement(Var("pair", _any_type), 0)
    result = gen.generate_lines(expr, lines, "")
    assert result == "pair[0]"

    reset_gensym()
    lines = []
    expr = GetElement(Var("pair", _any_type), 1)
    result = gen.generate_lines(expr, lines, "")
    assert result == "pair[1]"


def test_python_if_else_generation():
    """Test Python if-else code generation."""
    gen = PythonCodeGenerator()

    # Basic if-else (use strings to avoid Lit(1)==Lit(True) issue in Python)
    reset_gensym()
    lines = []
    expr = IfElse(Var("cond", _bool_type), Lit("yes"), Lit("no"))
    result = gen.generate_lines(expr, lines, "")
    assert "if cond:" in "\n".join(lines)
    assert "else:" in "\n".join(lines)
    # Result should be a temp variable
    assert result is not None and result.startswith("_t")

    # Short-circuit optimization: cond or else_value
    reset_gensym()
    lines = []
    expr = IfElse(Var("cond", _bool_type), Lit(True), Var("default", _bool_type))
    result = gen.generate_lines(expr, lines, "")
    assert result is not None and "cond or default" in result
    assert len(lines) == 0

    # Short-circuit optimization: cond and then_value
    reset_gensym()
    lines = []
    expr = IfElse(Var("cond", _bool_type), Var("value", _bool_type), Lit(False))
    result = gen.generate_lines(expr, lines, "")
    assert result is not None and "cond and value" in result
    assert len(lines) == 0


def test_python_while_generation():
    """Test Python while loop code generation."""
    gen = PythonCodeGenerator()

    # Simple while loop
    reset_gensym()
    lines = []
    expr = While(Var("running", _bool_type), Call(Var("do_work", _any_type), []))
    result = gen.generate_lines(expr, lines, "")
    assert result == "None"
    code = "\n".join(lines)
    assert "while running:" in code
    assert "do_work()" in code


def test_python_seq_generation():
    """Test Python sequence expression code generation."""
    gen = PythonCodeGenerator()

    # Sequence of expressions
    reset_gensym()
    lines = []
    expr = Seq(
        [
            Call(Var("setup", _any_type), []),
            Call(Var("process", _any_type), []),
            Var("result", _any_type),
        ]
    )
    result = gen.generate_lines(expr, lines, "")
    assert result == "result"
    code = "\n".join(lines)
    assert "setup()" in code
    assert "process()" in code


def test_python_assign_generation():
    """Test Python assignment code generation."""
    gen = PythonCodeGenerator()

    reset_gensym()
    lines = []
    expr = Assign(Var("x", _int_type), Lit(42))
    result = gen.generate_lines(expr, lines, "")
    assert result == "None"
    assert "x = 42" in lines[0]

    # Assign with keyword variable
    reset_gensym()
    lines = []
    expr = Assign(Var("class", _str_type), Lit("MyClass"))
    result = gen.generate_lines(expr, lines, "")
    assert 'class_ = "MyClass"' in lines[0]


def test_python_return_generation():
    """Test Python return statement code generation."""
    gen = PythonCodeGenerator()

    reset_gensym()
    lines = []
    expr = Return(Var("result", _any_type))
    result = gen.generate_lines(expr, lines, "")
    # Return generates a return statement and returns None
    # to indicate that the caller should not add another return
    assert result is None
    assert "return result" in lines[0]


def test_python_list_expr_generation():
    """Test Python list expression code generation."""
    gen = PythonCodeGenerator()

    # Empty list
    reset_gensym()
    lines = []
    expr = ListExpr([], _int_type)
    result = gen.generate_lines(expr, lines, "")
    assert result == "[]"

    # List with elements
    reset_gensym()
    lines = []
    expr = ListExpr([Lit(1), Lit(2), Lit(3)], _int_type)
    result = gen.generate_lines(expr, lines, "")
    assert result == "[1, 2, 3]"


def test_python_symbol_generation():
    """Test Python symbol code generation."""
    gen = PythonCodeGenerator()

    reset_gensym()
    lines = []
    expr = Symbol("add")
    result = gen.generate_lines(expr, lines, "")
    assert result == '"add"'


def test_python_message_generation():
    """Test Python NewMessage constructor code generation."""
    gen = PythonCodeGenerator()

    # Simple message with no fields
    reset_gensym()
    lines = []
    expr = NewMessage("logic", "Expr", ())
    result = gen.generate_lines(expr, lines, "")
    assert result == "_t0"
    assert "logic_pb2.Expr()" in "\n".join(lines)

    # NewMessage with field
    reset_gensym()
    lines = []
    expr = NewMessage("logic", "Expr", (("value", Var("value", _any_type)),))
    result = gen.generate_lines(expr, lines, "")
    assert "logic_pb2.Expr" in "\n".join(lines)


def test_python_oneof_generation():
    """Test Python OneOf field code generation."""
    gen = PythonCodeGenerator()

    # OneOf in NewMessage constructor
    reset_gensym()
    lines = []
    expr = NewMessage("logic", "Value", (("literal", Lit("hello")),))
    gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)
    assert "literal='hello'" in code or "literal=" in code


def test_python_fun_def_generation():
    """Test Python function definition code generation."""
    gen = PythonCodeGenerator()

    # Simple function
    reset_gensym()
    func = FunDef(
        name="add",
        params=[Var("x", _int_type), Var("y", _int_type)],
        return_type=_int_type,
        body=Call(make_builtin("add"), [Var("x", _int_type), Var("y", _int_type)]),
    )
    code = gen.generate_def(func)
    assert "def add(x: int, y: int) -> int:" in code
    assert "return" in code

    # Function with keyword parameter
    reset_gensym()
    func = FunDef(
        name="process",
        params=[Var("class", _str_type)],
        return_type=_str_type,
        body=Var("class", _str_type),
    )
    code = gen.generate_def(func)
    assert "def process(class_: str) -> str:" in code
    assert "return class_" in code


def test_python_visit_nonterminal_def_generation():
    """Test Python ParseNonterminalDef code generation."""
    gen = PythonCodeGenerator()

    # Create a nonterminal
    nt = Nonterminal("expr", MessageType("logic", "Expr"))

    # Simple parse method
    reset_gensym()
    parse_def = ParseNonterminalDef(
        nonterminal=nt,
        params=[],
        return_type=MessageType("logic", "Expr"),
        body=NewMessage("logic", "Expr", ()),
    )
    code = gen.generate_def(parse_def)
    assert "def parse_expr(self) -> logic_pb2.Expr:" in code
    assert "return" in code

    # Parse method with parameters
    reset_gensym()
    parse_def = ParseNonterminalDef(
        nonterminal=nt,
        params=[Var("context", _str_type)],
        return_type=MessageType("logic", "Expr"),
        body=Var("result", MessageType("logic", "Expr")),
    )
    code = gen.generate_def(parse_def)
    assert "def parse_expr(self, context: str) -> logic_pb2.Expr:" in code


def test_python_type_generation():
    """Test Python type hint generation."""
    gen = PythonCodeGenerator()

    # Base types
    assert gen.gen_type(BaseType("Int32")) == "int"
    assert gen.gen_type(BaseType("Int64")) == "int"
    assert gen.gen_type(BaseType("Float64")) == "float"
    assert gen.gen_type(BaseType("String")) == "str"
    assert gen.gen_type(BaseType("Boolean")) == "bool"

    # Message type
    assert gen.gen_type(MessageType("logic", "Expr")) == "logic_pb2.Expr"

    # List type
    assert gen.gen_type(ListType(BaseType("Int64"))) == "list[int]"

    # Option type
    assert gen.gen_type(OptionType(BaseType("String"))) == "Optional[str]"


# Tests for helper function codegen (FunDef from yacc grammar)


def test_python_helper_function_simple():
    """Test Python code generation for a simple helper function."""
    gen = PythonCodeGenerator()
    reset_gensym()

    # Equivalent to: def add_one(x: int) -> int: return x + 1
    # Using builtin add
    func = FunDef(
        name="add_one",
        params=[Var("x", _int_type)],
        return_type=_int_type,
        body=Call(make_builtin("add"), [Var("x", _int_type), Lit(1)]),
    )
    code = gen.generate_def(func)
    assert "def add_one(x: int) -> int:" in code
    assert "return (x + 1)" in code


def test_python_helper_function_with_if():
    """Test Python code generation for helper function with if-else."""
    gen = PythonCodeGenerator()
    reset_gensym()

    # Equivalent to:
    # def check_value(v: Optional[int], default: int) -> int:
    #     if v is None:
    #         return default
    #     return v
    func = FunDef(
        name="check_value",
        params=[Var("v", OptionType(_int_type)), Var("default", _int_type)],
        return_type=_int_type,
        body=IfElse(
            Call(make_builtin("is_none"), [Var("v", OptionType(_int_type))]),
            Return(Var("default", _int_type)),
            Return(Var("v", OptionType(_int_type))),
        ),
    )
    code = gen.generate_def(func)
    assert "def check_value(v: Optional[int], default: int) -> int:" in code
    assert "if v is None:" in code
    assert "return default" in code
    assert "return v" in code


def test_python_helper_function_with_assignment():
    """Test Python code generation for helper function with variable assignment."""
    gen = PythonCodeGenerator()
    reset_gensym()

    # Equivalent to:
    # def transform(x: int) -> int:
    #     result = x
    #     return result
    func = FunDef(
        name="transform",
        params=[Var("x", _int_type)],
        return_type=_int_type,
        body=Seq(
            [
                Assign(Var("result", _int_type), Var("x", _int_type)),
                Return(Var("result", _int_type)),
            ]
        ),
    )
    code = gen.generate_def(func)
    assert "def transform(x: int) -> int:" in code
    assert "result = x" in code
    assert "return result" in code


def test_python_helper_function_message_constructor():
    """Test Python code generation for helper function constructing a message."""
    gen = PythonCodeGenerator()
    reset_gensym()

    # Equivalent to:
    # def make_value(x: int) -> logic.Value:
    #     return logic.Value(int_value=x)
    func = FunDef(
        name="make_value",
        params=[Var("x", _int_type)],
        return_type=MessageType("logic", "Value"),
        body=NewMessage("logic", "Value", (("int_value", Var("x", _int_type)),)),
    )
    code = gen.generate_def(func)
    assert "def make_value(x: int) -> logic_pb2.Value:" in code
    assert "logic_pb2.Value" in code
    assert "int_value=" in code


def test_python_helper_function_calling_another():
    """Test Python code generation for helper function calling another function."""
    gen = PythonCodeGenerator()
    reset_gensym()

    # Equivalent to:
    # def wrapper(x: int) -> int:
    #     return helper(x)
    func = FunDef(
        name="wrapper",
        params=[Var("x", _int_type)],
        return_type=_int_type,
        body=Call(
            NamedFun("helper", FunctionType([_int_type], _int_type)),
            [Var("x", _int_type)],
        ),
    )
    code = gen.generate_def(func)
    assert "def wrapper(x: int) -> int:" in code
    assert "self.helper(x)" in code


def test_python_and_short_circuit_with_side_effects():
    """Test that 'and' preserves short-circuit semantics when RHS has side-effects.

    When the RHS of 'and' contains a function call (which generates a temp-var
    assignment), those side-effects must not be hoisted above the short-circuit
    check — they should only execute when the LHS is truthy.
    """
    gen = PythonCodeGenerator()
    reset_gensym()
    lines = []

    # and(a, f(x) == 42)
    # The call f(x) generates a temp-var assignment line.
    # That assignment must be guarded by the 'and' LHS.
    expr = Call(
        make_builtin("and"),
        [
            Var("a", _bool_type),
            Call(
                make_builtin("equal"),
                [
                    Call(Var("f", _any_type), [Var("x", _any_type)]),
                    Lit(42),
                ],
            ),
        ],
    )
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)

    assert result is not None
    # f(x) call must be inside the if body, not before it
    assert "f(x)" not in code.split("if ")[0], (
        f"f(x) was hoisted above the if guard:\n{code}"
    )
    assert "if " in code, f"Expected if-else for short-circuit, got:\n{code}"


def test_python_or_short_circuit_with_side_effects():
    """Test that 'or' preserves short-circuit semantics when RHS has side-effects."""
    gen = PythonCodeGenerator()
    reset_gensym()
    lines = []

    # or(a, f(x) == 42)
    # f(x) side-effects must only execute when a is falsy.
    expr = Call(
        make_builtin("or"),
        [
            Var("a", _bool_type),
            Call(
                make_builtin("equal"),
                [
                    Call(Var("f", _any_type), [Var("x", _any_type)]),
                    Lit(42),
                ],
            ),
        ],
    )
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)

    assert result is not None
    assert "f(x)" not in code.split("if ")[0], (
        f"f(x) was hoisted above the if guard:\n{code}"
    )
    assert "if " in code, f"Expected if-else for short-circuit, got:\n{code}"


def test_python_and_without_side_effects_uses_template():
    """Test that 'and' without side-effects uses the simple template."""
    gen = PythonCodeGenerator()
    reset_gensym()
    lines = []

    # and(a, b) with no side-effects should produce (a and b)
    expr = Call(
        make_builtin("and"),
        [
            Var("a", _bool_type),
            Var("b", _bool_type),
        ],
    )
    result = gen.generate_lines(expr, lines, "")
    assert result == "(a and b)"
    assert len(lines) == 0


def test_python_or_without_side_effects_uses_template():
    """Test that 'or' without side-effects uses the simple template."""
    gen = PythonCodeGenerator()
    reset_gensym()
    lines = []

    expr = Call(
        make_builtin("or"),
        [
            Var("a", _bool_type),
            Var("b", _bool_type),
        ],
    )
    result = gen.generate_lines(expr, lines, "")
    assert result == "(a or b)"
    assert len(lines) == 0


def test_python_and_short_circuit_with_unwrap_side_effects():
    """Test that 'and' preserves short-circuit semantics when RHS has side-effects.

    When the RHS of 'and' contains a builtin like unwrap_option that emits
    side-effect statements (e.g., assert), those side-effects must not be
    hoisted above the 'and' — they should only execute when the LHS is truthy.
    """
    gen = PythonCodeGenerator()
    reset_gensym()
    lines = []

    # and(x is not None, unwrap_option(x) == 42)
    # unwrap_option emits `assert x is not None` as a side-effect.
    # That assert must NOT execute when x is None.
    expr = Call(
        make_builtin("and"),
        [
            Call(make_builtin("is_some"), [Var("x", OptionType(_int_type))]),
            Call(
                make_builtin("equal"),
                [
                    Call(
                        make_builtin("unwrap_option"), [Var("x", OptionType(_int_type))]
                    ),
                    Lit(42),
                ],
            ),
        ],
    )
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)

    # The assert from unwrap_option must be inside the if body, not at the top
    assert result is not None
    assert "assert" not in code.split("if ")[0], (
        f"assert was hoisted above the if guard:\n{code}"
    )
    assert "if " in code, f"Expected if-else for short-circuit, got:\n{code}"


def test_python_or_short_circuit_with_unwrap_side_effects():
    """Test that 'or' preserves short-circuit semantics when RHS has side-effects."""
    gen = PythonCodeGenerator()
    reset_gensym()
    lines = []

    # or(x is None, unwrap_option(x) == 42)
    # unwrap_option side-effects must only execute when x is NOT None.
    expr = Call(
        make_builtin("or"),
        [
            Call(make_builtin("is_none"), [Var("x", OptionType(_int_type))]),
            Call(
                make_builtin("equal"),
                [
                    Call(
                        make_builtin("unwrap_option"), [Var("x", OptionType(_int_type))]
                    ),
                    Lit(42),
                ],
            ),
        ],
    )
    result = gen.generate_lines(expr, lines, "")
    code = "\n".join(lines)

    assert result is not None
    assert "assert" not in code.split("if ")[0], (
        f"assert was hoisted above the if guard:\n{code}"
    )
    assert "if " in code, f"Expected if-else for short-circuit, got:\n{code}"


def test_python_empty_string_literal():
    """Empty string literal generates correctly."""
    gen = PythonCodeGenerator()
    lines = []
    result = gen.generate_lines(Lit(""), lines, "")
    assert result == '""'


def test_python_deeply_nested_calls():
    """4-level nested Call produces valid output."""
    gen = PythonCodeGenerator()
    reset_gensym()
    lines = []
    inner = Call(Var("d", _any_type), [Var("x", _any_type)])
    level3 = Call(Var("c", _any_type), [inner])
    level2 = Call(Var("b", _any_type), [level3])
    expr = Call(Var("a", _any_type), [level2])
    result = gen.generate_lines(expr, lines, "")
    assert result is not None
    code = "\n".join(lines) + "\n" + result
    assert "d(x)" in code
    assert "a(" in code


def test_python_long_variable_name():
    """Variable with 100-char name renders correctly."""
    gen = PythonCodeGenerator()
    long_name = "v" * 100
    lines = []
    result = gen.generate_lines(Var(long_name, _any_type), lines, "")
    assert result == long_name


def test_python_nested_if_else():
    """3-level nested IfElse produces valid output."""
    gen = PythonCodeGenerator()
    reset_gensym()
    lines = []
    inner = IfElse(Var("c", _bool_type), Lit("x"), Lit("y"))
    mid = IfElse(Var("b", _bool_type), inner, Lit("z"))
    expr = IfElse(Var("a", _bool_type), mid, Lit("w"))
    result = gen.generate_lines(expr, lines, "")
    assert result is not None
    code = "\n".join(lines)
    assert code.count("if ") >= 3


def test_python_two_element_seq():
    """Minimal Seq (2 elements) returns last element's value."""
    gen = PythonCodeGenerator()
    reset_gensym()
    lines = []
    result = gen.generate_lines(Seq([Lit(1), Lit(2)]), lines, "")
    assert result == "2"


def test_python_option_none_lit():
    """Lit(None) generates correctly."""
    gen = PythonCodeGenerator()
    lines = []
    result = gen.generate_lines(Lit(None), lines, "")
    assert result == "None"


if __name__ == "__main__":
    test_python_keyword_escaping()
    test_python_call_generation()
    test_python_let_generation()
    test_python_lambda_generation()
    test_python_builtin_generation()
    test_python_get_element_generation()
    test_python_if_else_generation()
    test_python_while_generation()
    test_python_seq_generation()
    test_python_assign_generation()
    test_python_return_generation()
    test_python_list_expr_generation()
    test_python_symbol_generation()
    test_python_message_generation()
    test_python_oneof_generation()
    test_python_fun_def_generation()
    test_python_visit_nonterminal_def_generation()
    test_python_type_generation()
    test_python_helper_function_simple()
    test_python_helper_function_with_if()
    test_python_helper_function_with_assignment()
    test_python_helper_function_message_constructor()
    test_python_helper_function_calling_another()
    test_python_and_short_circuit_with_side_effects()
    test_python_or_short_circuit_with_side_effects()
    test_python_and_without_side_effects_uses_template()
    test_python_or_without_side_effects_uses_template()
    test_python_empty_string_literal()
    test_python_deeply_nested_calls()
    test_python_long_variable_name()
    test_python_nested_if_else()
    test_python_two_element_seq()
    test_python_option_none_lit()
