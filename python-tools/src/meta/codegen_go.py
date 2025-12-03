"""Code generation for Go from semantic action AST.

This module generates Go code from semantic action expressions,
with proper keyword escaping and idiomatic Go style.
"""

from typing import Set
from .target import TargetExpr, Var, Symbol, Constructor, Call, Lambda, Let, FunDef, Type, BaseType, TupleType, ListType


# Go keywords that need escaping
GO_KEYWORDS: Set[str] = {
    'break', 'case', 'chan', 'const', 'continue', 'default', 'defer',
    'else', 'fallthrough', 'for', 'func', 'go', 'goto', 'if', 'import',
    'interface', 'map', 'package', 'range', 'return', 'select', 'struct',
    'switch', 'type', 'var',
    # Predeclared identifiers (not keywords but often need escaping)
    'bool', 'byte', 'complex64', 'complex128', 'error', 'float32', 'float64',
    'int', 'int8', 'int16', 'int32', 'int64', 'rune', 'string',
    'uint', 'uint8', 'uint16', 'uint32', 'uint64', 'uintptr',
    'true', 'false', 'iota', 'nil',
    'append', 'cap', 'close', 'complex', 'copy', 'delete', 'imag', 'len',
    'make', 'new', 'panic', 'print', 'println', 'real', 'recover',
}


def escape_identifier(name: str) -> str:
    """Escape a Go identifier if it's a keyword or predeclared.

    Go doesn't have a special syntax for escaping keywords, so we append
    an underscore to make the identifier valid.

    Args:
        name: Identifier to potentially escape

    Returns:
        Escaped identifier (adds trailing underscore if keyword)
    """
    if name in GO_KEYWORDS:
        return f"{name}_"
    return name


def generate_go_type(typ: Type) -> str:
    """Generate Go type from a Type expression.

    Args:
        typ: Type expression to generate code for

    Returns:
        Go type as a string
    """
    if isinstance(typ, BaseType):
        # Map base types to Go types
        type_map = {
            'Int64': 'int64',
            'Float64': 'float64',
            'String': 'string',
            'Boolean': 'bool',
        }
        return type_map.get(typ.name, typ.name)

    elif isinstance(typ, TupleType):
        # Go doesn't have tuple types, use struct with numbered fields
        if not typ.elements:
            return 'struct{}'
        fields = []
        for i, element_type in enumerate(typ.elements):
            go_type = generate_go_type(element_type)
            fields.append(f"F{i} {go_type}")
        fields_str = '; '.join(fields)
        return f"struct{{ {fields_str} }}"

    elif isinstance(typ, ListType):
        element_type = generate_go_type(typ.element_type)
        return f"[]{element_type}"

    else:
        raise ValueError(f"Unknown type: {type(typ)}")


def generate_go(expr: TargetExpr, indent: str = "") -> str:
    """Generate Go code from an action expression.

    Args:
        expr: Action expression to generate code for
        indent: Current indentation level

    Returns:
        Go code as a string
    """
    if isinstance(expr, Var):
        return escape_identifier(expr.name)

    elif isinstance(expr, Symbol):
        # Symbols as string literals (Go doesn't have Ruby-style symbols)
        return f'"{expr.name}"'

    elif isinstance(expr, Constructor):
        # Constructor reference
        return f"{expr.name}"

    elif isinstance(expr, Call):
        # Generate function expression (can be Var, Symbol, or arbitrary expression)
        func_code = generate_go(expr.func, indent)
        if not expr.args:
            return f"{func_code}()"

        args_code = ', '.join(generate_go(arg, indent) for arg in expr.args)
        return f"{func_code}({args_code})"

    elif isinstance(expr, Lambda):
        # Generate anonymous function: func(params...) ReturnType { return body }
        params = [escape_identifier(p) for p in expr.params]

        if expr.body is None:
            body_code = "nil"
        else:
            body_code = generate_go(expr.body, indent + "\t")

        # Build parameter list with interface{} type (generic)
        param_list = ', '.join(f"{p} interface{{}}" for p in params)

        # Generate return type
        ret_type = generate_go_type(expr.return_type) if expr.return_type else "interface{}"

        return f"func({param_list}) {ret_type} {{\n{indent}\treturn {body_code}\n{indent}}}"

    elif isinstance(expr, Let):
        # Generate Let as variable declaration and evaluation
        # Go doesn't have let expressions, so we use a closure
        var_name = escape_identifier(expr.var)
        init_code = generate_go(expr.init, indent)

        # Check if body is another Let
        if isinstance(expr.body, Let):
            # Nested Let: use IIFE (Immediately Invoked Function Expression)
            inner_code = generate_go_let_sequence(expr, indent + "\t")
            return f"func() interface{{}} {{\n{indent}\t{inner_code}\n{indent}}}()"
        else:
            body_code = generate_go(expr.body, indent)
            # Simple let: wrap in IIFE
            return f"func() interface{{}} {{\n{indent}\t{var_name} := {init_code}\n{indent}\treturn {body_code}\n{indent}}}()"

    elif isinstance(expr, FunDef):
        # Generate function definition
        func_name = escape_identifier(expr.name)

        # Generate parameters with types
        params = []
        for param_name, param_type in expr.params:
            escaped_name = escape_identifier(param_name)
            go_type = generate_go_type(param_type)
            params.append(f"{escaped_name} {go_type}")

        params_str = ', '.join(params) if params else ''

        # Generate return type
        ret_type = generate_go_type(expr.return_type) if expr.return_type else "interface{}"

        # Generate body
        if expr.body is None:
            body_code = f"{indent}\t// no body"
        else:
            body_code = f"{indent}\t" + generate_go_function_body(expr.body, indent + "\t")

        return f"func {func_name}({params_str}) {ret_type} {{\n{body_code}\n{indent}}}"

    else:
        raise ValueError(f"Unknown action expression type: {type(expr)}")


def generate_go_let_sequence(expr: Let, indent: str = "\t") -> str:
    """Generate Go code for a sequence of Let-bindings.

    Handles nested Let-bindings by flattening them into a sequence
    of variable declarations followed by a return.

    Args:
        expr: Let expression (possibly nested)
        indent: Current indentation level

    Returns:
        Go code with declarations and final return
    """
    statements = []
    current = expr

    # Collect all Let-bindings in sequence
    while isinstance(current, Let):
        var_name = escape_identifier(current.var)
        init_code = generate_go(current.init, indent)
        statements.append(f"{var_name} := {init_code}")
        current = current.body

    # Generate the final expression (not a Let)
    final_code = generate_go(current, indent)
    statements.append(f"return {final_code}")

    # Combine all statements
    return f"\n{indent}".join(statements)


def generate_go_function_body(expr: TargetExpr, indent: str = "\t") -> str:
    """Generate Go code for a function body with proper indentation.

    Args:
        expr: Action expression for the function body
        indent: Indentation string (default: tab)

    Returns:
        Go code with proper indentation
    """
    if isinstance(expr, Let):
        # Let-bindings become sequential statements
        return generate_go_let_sequence(expr, indent)
    else:
        # Single expression becomes return statement
        expr_code = generate_go(expr, indent)
        return f"return {expr_code}"


__all__ = [
    'escape_identifier',
    'generate_go',
    'generate_go_let_sequence',
    'generate_go_function_body',
    'GO_KEYWORDS',
]
