"""Code generation for Python from semantic action AST.

This module generates Python code from semantic action expressions,
with proper keyword escaping and idiomatic Python style.
"""

from typing import Set, Union
from .target import TargetExpr, Var, Lit, Symbol, Builtin, Constructor, Call, Lambda, Let, IfElse, Seq, While, TryCatch, Assign, Return, FunDef, ParseNonterminalDef, ParseNonterminal, Type, BaseType, TupleType, ListType, TargetNode


# Python keywords that need escaping
PYTHON_KEYWORDS: Set[str] = {
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
    'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
    'try', 'while', 'with', 'yield',
}


def escape_identifier(name: str) -> str:
    """Escape a Python identifier if it's a keyword.

    Args:
        name: Identifier to potentially escape

    Returns:
        Escaped identifier (adds trailing underscore if keyword)
    """
    if name in PYTHON_KEYWORDS:
        return f"{name}_"
    return name


def generate_python_type(typ: Type) -> str:
    """Generate Python type hint from a Type expression.

    Args:
        typ: Type expression to generate code for

    Returns:
        Python type hint as a string
    """
    if isinstance(typ, BaseType):
        # Map base types to Python types
        type_map = {
            'Int64': 'int',
            'Float64': 'float',
            'String': 'str',
            'Boolean': 'bool',
        }
        return type_map.get(typ.name, typ.name)

    elif isinstance(typ, TupleType):
        if not typ.elements:
            return 'tuple[()]'
        element_types = ', '.join(generate_python_type(e) for e in typ.elements)
        return f"tuple[{element_types}]"

    elif isinstance(typ, ListType):
        element_type = generate_python_type(typ.element_type)
        return f"list[{element_type}]"

    else:
        raise ValueError(f"Unknown type: {type(typ)}")

def generate_python(expr: TargetExpr, indent: str = "") -> str:
    """Generate Python code from an action expression.

    Args:
        expr: Action expression to generate code for
        indent: Current indentation level

    Returns:
        Python code as a string
    """
    if isinstance(expr, Var):
        return escape_identifier(expr.name)

    elif isinstance(expr, Lit):
        return repr(expr.value)

    elif isinstance(expr, Symbol):
        return f'"{expr.name}"'

    elif isinstance(expr, Constructor):
        return f"ir.{expr.name}"

    elif isinstance(expr, Call):
        # Special case: Handle special builtins inline
        if isinstance(expr.func, Builtin):
            if expr.func.name == "list_concat" and len(expr.args) == 2:
                arg1 = generate_python(expr.args[0], indent)
                arg2 = generate_python(expr.args[1], indent)
                return f"{arg1} + {arg2}"
            elif expr.func.name == "make_list" and len(expr.args) == 1:
                arg = generate_python(expr.args[0], indent)
                return f"[{arg}]"
            elif expr.func.name == "consume_terminal" and len(expr.args) == 1:
                arg = generate_python(expr.args[0], indent)
                return f"self.consume_terminal({arg})"
            elif expr.func.name == "consume_literal" and len(expr.args) == 1:
                arg = generate_python(expr.args[0], indent)
                return f"self.consume_literal({arg})"
            else:
                func_code = f"self.{expr.func.name}"
                if not expr.args:
                    return f"{func_code}()"
                else:
                    args_code = ', '.join(generate_python(arg, indent) for arg in expr.args)
                    return f"{func_code}({args_code})"

        # Regular call
        func_code = generate_python(expr.func, indent)

        if not expr.args:
            return f"{func_code}()"
        else:
            args_code = ', '.join(generate_python(arg, indent) for arg in expr.args)
            return f"{func_code}({args_code})"

    elif isinstance(expr, Lambda):
        params = [escape_identifier(p) for p in expr.params]
        params_str = ', '.join(params) if params else ''

        if expr.body is None:
            body_code = "None"
        else:
            body_code = generate_python(expr.body, indent)

        return f"lambda {params_str}: {body_code}"

    elif isinstance(expr, Let):
        var_name = escape_identifier(expr.var)
        init_code = generate_python(expr.init, indent)

        if isinstance(expr.body, Let):
            body_code = generate_python_let_sequence(expr.body, indent)
            return f"{var_name} = {init_code}\n{indent}{body_code}"
        else:
            body_code = generate_python(expr.body, indent)
            return f"{var_name} = {init_code}\n{indent}{body_code}"

    elif isinstance(expr, IfElse):
        cond_code = generate_python(expr.condition, indent)
        then_code = generate_python(expr.then_branch, indent)
        else_code = generate_python(expr.else_branch, indent)
        return f"if {cond_code}:\n{indent}    {then_code}\n{indent}else:\n{indent}    {else_code}"

    elif isinstance(expr, Seq):
        if not expr.exprs:
            return "pass"

        lines = []
        for e in expr.exprs:
            e_code = generate_python(e, indent)
            lines.append(e_code)

        return f"\n{indent}".join(lines)

    elif isinstance(expr, While):
        cond_code = generate_python(expr.condition, indent)
        body_code = generate_python(expr.body, indent + "    ")
        return f"while {cond_code}:\n{indent}    {body_code}"

    elif isinstance(expr, TryCatch):
        try_code = generate_python(expr.try_body, indent + "    ")

        if expr.catch_body:
            catch_code = generate_python(expr.catch_body, indent + "    ")
            exc_type = expr.exception_type or "Exception"
            return f"try:\n{indent}    {try_code}\n{indent}except {exc_type}:\n{indent}    {catch_code}"
        else:
            return f"try:\n{indent}    {try_code}\n{indent}except:\n{indent}    pass"

    elif isinstance(expr, Assign):
        var_name = escape_identifier(expr.var)
        expr_code = generate_python(expr.expr, indent)
        return f"{var_name} = {expr_code}"

    elif isinstance(expr, Return):
        expr_code = generate_python(expr.expr, indent)
        return f"return {expr_code}"

    elif isinstance(expr, ParseNonterminal):
        func_name = f"self.parse_{expr.nonterminal.name}"
        if not expr.args:
            return f"{func_name}()"
        else:
            args_code = ', '.join(generate_python(arg, indent) for arg in expr.args)
            return f"{func_name}({args_code})"

    else:
        raise ValueError(f"Unknown action expression type: {type(expr)}")


def generate_python_def(expr: Union[FunDef, ParseNonterminalDef], indent: str = "") -> str:
    if isinstance(expr, FunDef):
        func_name = escape_identifier(expr.name)

        params = []
        for param_name, param_type in expr.params:
            escaped_name = escape_identifier(param_name)
            type_hint = generate_python_type(param_type)
            params.append(f"{escaped_name}: {type_hint}")

        params_str = ', '.join(params)

        ret_hint = f" -> {generate_python_type(expr.return_type)}" if expr.return_type else ""

        if expr.body is None:
            body_code = f"{indent}    pass"
        else:
            body_inner = generate_python(expr.body, indent + "    ")
            body_code = f"{indent}    {body_inner}"

        return f"{indent}def {func_name}({params_str}){ret_hint}:\n{body_code}"

    elif isinstance(expr, ParseNonterminalDef):
        func_name = f"parse_{expr.nonterminal.name}"

        params = []
        for param_name, param_type in expr.params:
            escaped_name = escape_identifier(param_name)
            type_hint = generate_python_type(param_type)
            params.append(f"{escaped_name}: {type_hint}")

        params_str = ', '.join(params) if params else ''
        if params_str:
            params_str = ', ' + params_str

        ret_hint = f" -> {generate_python_type(expr.return_type)}" if expr.return_type else ""

        if expr.body is None:
            body_code = f"{indent}    pass"
        else:
            body_inner = generate_python(Return(expr.body), indent + "    ")
            body_code = f"{indent}    {body_inner}"

        return f"{indent}def {func_name}(self{params_str}){ret_hint}:\n{body_code}"


def generate_python_let_sequence(expr: Let, indent: str = "") -> str:
    """Generate Python code for a sequence of Let-bindings.

    Handles nested Let-bindings by flattening them into a sequence of assignments.

    Args:
        expr: Let expression (possibly nested)
        indent: Current indentation level

    Returns:
        Python code with assignments
    """
    assignments = []
    current = expr

    while isinstance(current, Let):
        var_name = escape_identifier(current.var)
        init_code = generate_python(current.init, indent)
        assignments.append(f"{var_name} = {init_code}")
        current = current.body

    final_code = generate_python(current, indent)
    lines = assignments + [final_code]
    return f"\n{indent}".join(lines)


def generate_python_function_body(expr: TargetExpr, indent: str = "    ") -> str:
    """Generate Python code for a function body with proper indentation.

    Args:
        expr: Action expression for the function body
        indent: Indentation string (default: 4 spaces)

    Returns:
        Python code with proper indentation
    """
    return generate_python(expr, indent)


__all__ = [
    'escape_identifier',
    'generate_python',
    'generate_python_let_sequence',
    'generate_python_function_body',
    'PYTHON_KEYWORDS',
]
