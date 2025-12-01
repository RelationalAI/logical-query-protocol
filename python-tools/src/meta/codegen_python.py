"""Code generation for Python from semantic action AST.

This module generates Python code from semantic action expressions,
with proper keyword escaping and idiomatic Python style.
"""

from typing import Set
from .target import TargetExpr, Wildcard, Var, Symbol, Call, Lambda, Let, FunDef, Type, BaseType, TupleType, ListType


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
    if isinstance(expr, Wildcard):
        return "_"

    elif isinstance(expr, Var):
        return escape_identifier(expr.name)

    elif isinstance(expr, Symbol):
        # Symbols are typically string literals
        return f'"{expr.name}"'

    elif isinstance(expr, Call):
        func_name = escape_identifier(expr.name)
        if not expr.args:
            return f"{func_name}()"

        args_code = ', '.join(generate_python(arg, indent) for arg in expr.args)
        return f"{func_name}({args_code})"

    elif isinstance(expr, Lambda):
        # Generate lambda function
        params = [escape_identifier(p) for p in expr.params]
        params_str = ', '.join(params) if params else ''

        if expr.body is None:
            body_code = "None"
        else:
            body_code = generate_python(expr.body, indent)

        return f"lambda {params_str}: {body_code}"

    elif isinstance(expr, Let):
        # Generate Let as sequential assignment and return
        # let x = e1 in e2  becomes:  x = e1; return e2
        var_name = escape_identifier(expr.var)
        expr1_code = generate_python(expr.init, indent)

        # Check if expr2 is another Let (for proper nesting)
        if isinstance(expr.body, Let):
            # Nested Let: generate as sequence of assignments
            expr2_code = generate_python_let_sequence(expr.body, indent)
            return f"{var_name} = {expr1_code}\n{indent}{expr2_code}"
        else:
            expr2_code = generate_python(expr.body, indent)
            return f"{var_name} = {expr1_code}\n{indent}return {expr2_code}"

    elif isinstance(expr, FunDef):
        # Generate function definition
        func_name = escape_identifier(expr.name)

        # Generate parameters with type hints
        params = []
        for param_name, param_type in expr.params:
            escaped_name = escape_identifier(param_name)
            type_hint = generate_python_type(param_type)
            params.append(f"{escaped_name}: {type_hint}")

        params_str = ', '.join(params) if params else ''

        # Generate return type hint
        ret_hint = f" -> {generate_python_type(expr.return_type)}" if expr.return_type else ""

        # Generate body
        if expr.body is None:
            body_code = f"{indent}    pass"
        else:
            body_code = f"{indent}    " + generate_python_function_body(expr.body, indent + "    ")

        return f"def {func_name}({params_str}){ret_hint}:\n{body_code}"

    else:
        raise ValueError(f"Unknown action expression type: {type(expr)}")


def generate_python_let_sequence(expr: Let, indent: str = "") -> str:
    """Generate Python code for a sequence of Let-bindings.

    Handles nested Let-bindings by flattening them into a sequence
    of assignments followed by a return.

    Args:
        expr: Let expression (possibly nested)
        indent: Current indentation level

    Returns:
        Python code with assignments and final return
    """
    assignments = []
    current = expr

    # Collect all Let-bindings in sequence
    while isinstance(current, Let):
        var_name = escape_identifier(current.var)
        expr1_code = generate_python(current.init, indent)
        assignments.append(f"{var_name} = {expr1_code}")
        current = current.body

    # Generate the final expression (not a Let)
    final_code = generate_python(current, indent)

    # Combine all assignments and return
    lines = assignments + [f"return {final_code}"]
    return f"\n{indent}".join(lines)


def generate_python_function_body(expr: TargetExpr, indent: str = "    ") -> str:
    """Generate Python code for a function body with proper indentation.

    This is useful for generating method bodies in classes.

    Args:
        expr: Action expression for the function body
        indent: Indentation string (default: 4 spaces)

    Returns:
        Python code with proper indentation
    """
    if isinstance(expr, Let):
        # Let-bindings become sequential statements
        return generate_python_let_sequence(expr, indent)
    else:
        # Single expression becomes return statement
        expr_code = generate_python(expr, indent)
        return f"return {expr_code}"


__all__ = [
    'escape_identifier',
    'generate_python',
    'generate_python_let_sequence',
    'generate_python_function_body',
    'PYTHON_KEYWORDS',
]
