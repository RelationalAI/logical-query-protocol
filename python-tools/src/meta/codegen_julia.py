"""Code generation for Julia from semantic action AST.

This module generates Julia code from semantic action expressions,
with proper keyword escaping and idiomatic Julia style.
"""

from typing import Set
from .target import TargetExpr, Wildcard, Var, Symbol, Call, Lambda, Let, FunDef, Type, BaseType, TupleType, ListType


# Julia keywords that need escaping
JULIA_KEYWORDS: Set[str] = {
    'abstract', 'baremodule', 'begin', 'break', 'catch', 'const', 'continue',
    'do', 'else', 'elseif', 'end', 'export', 'false', 'finally', 'for',
    'function', 'global', 'if', 'import', 'let', 'local', 'macro', 'module',
    'quote', 'return', 'struct', 'true', 'try', 'type', 'using', 'while',
    # Soft keywords (contextual)
    'as', 'in', 'isa', 'where', 'mutable', 'primitive', 'outer',
}


def escape_identifier(name: str) -> str:
    """Escape a Julia identifier if it's a keyword.

    In Julia, non-standard identifiers can be created using var"name" syntax.

    Args:
        name: Identifier to potentially escape

    Returns:
        Escaped identifier (uses var"name" syntax if keyword)
    """
    if name in JULIA_KEYWORDS:
        return f'var"{name}"'
    return name


def generate_julia_type(typ: Type) -> str:
    """Generate Julia type annotation from a Type expression.

    Args:
        typ: Type expression to generate code for

    Returns:
        Julia type annotation as a string
    """
    if isinstance(typ, BaseType):
        # Map base types to Julia types
        type_map = {
            'Int64': 'Int64',
            'Float64': 'Float64',
            'String': 'String',
            'Boolean': 'Bool',
        }
        return type_map.get(typ.name, typ.name)

    elif isinstance(typ, TupleType):
        if not typ.elements:
            return 'Tuple{}'
        element_types = ', '.join(generate_julia_type(e) for e in typ.elements)
        return f"Tuple{{{element_types}}}"

    elif isinstance(typ, ListType):
        element_type = generate_julia_type(typ.element_type)
        return f"Vector{{{element_type}}}"

    else:
        raise ValueError(f"Unknown type: {type(typ)}")


def generate_julia(expr: TargetExpr, indent: str = "") -> str:
    """Generate Julia code from an action expression.

    Args:
        expr: Action expression to generate code for
        indent: Current indentation level

    Returns:
        Julia code as a string
    """
    if isinstance(expr, Wildcard):
        return "_"

    elif isinstance(expr, Var):
        return escape_identifier(expr.name)

    elif isinstance(expr, Symbol):
        # Symbols in Julia use :name syntax
        return f":{expr.name}"

    elif isinstance(expr, Call):
        func_name = escape_identifier(expr.name)
        if not expr.args:
            return f"{func_name}()"

        args_code = ', '.join(generate_julia(arg, indent) for arg in expr.args)
        return f"{func_name}({args_code})"

    elif isinstance(expr, Lambda):
        # Generate anonymous function: (params...) -> body
        params = [escape_identifier(p) for p in expr.params]
        params_str = ', '.join(params) if params else ''

        if expr.body is None:
            body_code = "nothing"
        else:
            body_code = generate_julia(expr.body, indent)

        if params:
            return f"({params_str}) -> {body_code}"
        else:
            return f"() -> {body_code}"

    elif isinstance(expr, Let):
        # Generate Let-binding
        # Julia native: let x = e1; e2 end
        var_name = escape_identifier(expr.var)
        expr1_code = generate_julia(expr.init, indent)

        # Check if expr2 is another Let (for proper nesting)
        if isinstance(expr.body, Let):
            # Nested Let: can use Julia's let with multiple bindings
            bindings = []
            current = expr
            while isinstance(current, Let):
                v = escape_identifier(current.var)
                e = generate_julia(current.init, indent)
                bindings.append(f"{v} = {e}")
                current = current.body

            body_code = generate_julia(current, indent)
            bindings_str = ", ".join(bindings)
            return f"let {bindings_str}; {body_code} end"
        else:
            expr2_code = generate_julia(expr.body, indent)
            return f"let {var_name} = {expr1_code}; {expr2_code} end"

    elif isinstance(expr, FunDef):
        # Generate function definition
        func_name = escape_identifier(expr.name)

        # Generate parameters with type annotations
        params = []
        for param_name, param_type in expr.params:
            escaped_name = escape_identifier(param_name)
            type_annotation = generate_julia_type(param_type)
            params.append(f"{escaped_name}::{type_annotation}")

        params_str = ', '.join(params) if params else ''

        # Generate return type annotation
        ret_annotation = f"::{generate_julia_type(expr.return_type)}" if expr.return_type else ""

        # Generate body
        if expr.body is None:
            body_code = f"{indent}    nothing"
        else:
            body_code = f"{indent}    " + generate_julia_function_body(expr.body, indent + "    ")

        return f"function {func_name}({params_str}){ret_annotation}\n{body_code}\n{indent}end"

    else:
        raise ValueError(f"Unknown action expression type: {type(expr)}")


def generate_julia_function_body(expr: TargetExpr, indent: str = "    ") -> str:
    """Generate Julia code for a function body with proper indentation.

    Args:
        expr: Action expression for the function body
        indent: Indentation string (default: 4 spaces)

    Returns:
        Julia code with proper indentation
    """
    if isinstance(expr, Let):
        # Let-bindings can be expressed natively in Julia
        return generate_julia(expr, indent)
    else:
        # Single expression
        return generate_julia(expr, indent)


__all__ = [
    'escape_identifier',
    'generate_julia',
    'generate_julia_function_body',
    'JULIA_KEYWORDS',
]
