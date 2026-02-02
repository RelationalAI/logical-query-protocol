#!/usr/bin/env python3
"""Tests for Python code generation from action AST."""

from meta.target import (
    Var, Lit, Symbol, Builtin, NewMessage, OneOf, ListExpr, Call, Lambda, Let,
    IfElse, Seq, While, Assign, Return, FunDef, VisitNonterminalDef,
    BaseType, MessageType, ListType, OptionType,
)
from meta.grammar import Nonterminal
from meta.codegen_python import (
    generate_python,
    escape_identifier as escape_python,
    PythonCodeGenerator,
)
from meta.gensym import reset as reset_gensym

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
    nested = Call(Var("outer", _any_type), [Call(Var("inner", _any_type), [Var("z", _any_type)])])
    code_nested = generate_python(nested)
    assert code_nested == "outer(inner(z))"


def test_python_let_generation():
    """Test Python Let-binding generation."""
    reset_gensym()

    # Simple let
    let_expr = Let(Var("x", _any_type), Call(Var("parse_foo", _any_type), []), Var("x", _any_type))
    code = generate_python(let_expr)
    assert "_t" in code and "parse_foo()" in code
    assert any(s in code for s in ("x = _t", "x = parse_foo()"))
    assert code.strip().endswith("x")

    # Nested let
    reset_gensym()
    nested_let = Let(Var("x", _any_type), Call(Var("parse_a", _any_type), []),
                     Let(Var("y", _any_type), Call(Var("parse_b", _any_type), []),
                         Call(Var("make", _any_type), [Var("x", _any_type), Var("y", _any_type)])))
    code_nested = generate_python(nested_let)
    assert "parse_a()" in code_nested and "x = " in code_nested
    assert "parse_b()" in code_nested and "y = " in code_nested
    assert "make(x, y)" in code_nested

    # Let with keyword variable
    reset_gensym()
    let_kw = Let(Var("class", _any_type), Call(Var("parse", _any_type), []), Var("class", _any_type))
    code_kw = generate_python(let_kw)
    assert "parse()" in code_kw and "class_ = " in code_kw
    assert code_kw.strip().endswith("class_")


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


def test_python_builtin_generation():
    """Test Python builtin function code generation."""
    gen = PythonCodeGenerator()

    # Test 'not' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("not"), [Var("x", _bool_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "not x"
    assert len(lines) == 0

    # Test 'equal' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("equal"), [Var("a", _any_type), Var("b", _any_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "a == b"

    # Test 'list_append' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("list_append"), [Var("lst", ListType(_int_type)), Var("item", _int_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "lst + [item]"

    # Test 'is_none' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("is_none"), [Var("x", OptionType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "x is None"

    # Test GetElement (replaces fst and snd builtins)
    reset_gensym()
    lines = []
    from meta.target import GetElement
    expr = GetElement(Var("pair", _any_type), 0)
    result = gen.generate_lines(expr, lines, "")
    assert result == "pair[0]"

    reset_gensym()
    lines = []
    expr = GetElement(Var("pair", _any_type), 1)
    result = gen.generate_lines(expr, lines, "")
    assert result == "pair[1]"

    # Test 'length' builtin
    reset_gensym()
    lines = []
    expr = Call(Builtin("length"), [Var("lst", ListType(_int_type))])
    result = gen.generate_lines(expr, lines, "")
    assert result == "len(lst)"

    # Test 'make_tuple' builtin (variadic)
    reset_gensym()
    lines = []
    expr = Call(Builtin("make_tuple"), [Var("a", _int_type), Var("b", _str_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "(a, b,)"

    # Test builtin with side effects ('list_push!')
    reset_gensym()
    lines = []
    expr = Call(Builtin("list_push!"), [Var("lst", ListType(_int_type)), Var("item", _int_type)])
    result = gen.generate_lines(expr, lines, "")
    assert result == "None"
    assert len(lines) == 1
    assert "lst.append(item)" in lines[0]


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
    assert result.startswith("_t")

    # Short-circuit optimization: cond or else_value
    reset_gensym()
    lines = []
    expr = IfElse(Var("cond", _bool_type), Lit(True), Var("default", _bool_type))
    result = gen.generate_lines(expr, lines, "")
    assert "cond or default" in result
    assert len(lines) == 0

    # Short-circuit optimization: cond and then_value
    reset_gensym()
    lines = []
    expr = IfElse(Var("cond", _bool_type), Var("value", _bool_type), Lit(False))
    result = gen.generate_lines(expr, lines, "")
    assert "cond and value" in result
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
    assert "class_ = 'MyClass'" in lines[0]


def test_python_return_generation():
    """Test Python return statement code generation."""
    gen = PythonCodeGenerator()

    reset_gensym()
    lines = []
    expr = Return(Var("result", _any_type))
    result = gen.generate_lines(expr, lines, "")
    assert result == "None"
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

    # Simple message reference (no fields) - returns constructor reference
    reset_gensym()
    lines = []
    expr = NewMessage("logic", "Expr", ())
    result = gen.generate_lines(expr, lines, "")
    assert result == "logic_pb2.Expr"

    # NewMessage call without field mapping
    reset_gensym()
    lines = []
    expr = Call(NewMessage("logic", "Expr", ()), [Var("value", _any_type)])
    result = gen.generate_lines(expr, lines, "")
    assert "logic_pb2.Expr" in "\n".join(lines)


def test_python_oneof_generation():
    """Test Python OneOf field code generation."""
    gen = PythonCodeGenerator()

    # OneOf in NewMessage constructor call
    reset_gensym()
    lines = []
    oneof_call = Call(OneOf("literal"), [Lit("hello")])
    expr = Call(NewMessage("logic", "Value", ()), [oneof_call])
    result = gen.generate_lines(expr, lines, "")
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
        body=Call(Builtin("add"), [Var("x", _int_type), Var("y", _int_type)]),
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
    """Test Python VisitNonterminalDef code generation."""
    gen = PythonCodeGenerator()

    # Create a nonterminal
    nt = Nonterminal("expr", MessageType("logic", "Expr"))

    # Simple parse method
    reset_gensym()
    parse_def = VisitNonterminalDef(
        visitor_name="parse",
        nonterminal=nt,
        params=[],
        return_type=MessageType("logic", "Expr"),
        body=Call(NewMessage("logic", "Expr", ()), []),
    )
    code = gen.generate_def(parse_def)
    assert "def parse_expr(self) -> logic_pb2.Expr:" in code
    assert "return" in code

    # Parse method with parameters
    reset_gensym()
    parse_def = VisitNonterminalDef(
        visitor_name="parse",
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


def test_generator_instance_isolation():
    """Test that generator instances don't share state."""
    gen1 = PythonCodeGenerator()
    gen2 = PythonCodeGenerator()

    # Register a custom builtin on gen1
    from meta.codegen_base import BuiltinResult
    gen1.register_builtin("custom_op", 1,
        lambda args, lines, indent: BuiltinResult(f"custom({args[0]})", []))

    # gen1 should have the custom builtin
    assert "custom_op" in gen1.builtin_registry

    # gen2 should NOT have the custom builtin
    assert "custom_op" not in gen2.builtin_registry
