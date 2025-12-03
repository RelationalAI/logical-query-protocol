"""Code generation for Python from semantic action AST.

This module generates Python code from semantic action expressions,
with proper keyword escaping and idiomatic Python style.
"""

from typing import Set
from .target import TargetExpr, Var, Lit, Symbol, Builtin, Constructor, Call, Lambda, Let, IfElse, Seq, While, TryCatch, Assign, FunDef, ParseNonterminalDef, ParseNonterminal, Type, BaseType, TupleType, ListType, TargetNode


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

def generate_python(expr: TargetNode, indent: str = "", tail_position: bool = False) -> str:
    """Generate Python code from an action expression.

    Args:
        expr: Action expression to generate code for
        indent: Current indentation level
        tail_position: Whether this expression is in tail position (needs return)

    Returns:
        Python code as a string
    """
    # For simple expressions in tail position, generate the expression and wrap with return
    # Let, IfElse, Seq, While, TryCatch, Assign handle tail_position themselves
    is_compound = isinstance(expr, (Let, IfElse, Seq, While, TryCatch, Assign, FunDef))

    if isinstance(expr, Var):
        result = escape_identifier(expr.name)
        return f"return {result}" if tail_position and not is_compound else result

    elif isinstance(expr, Lit):
        # Literal values (strings, numbers, bools, None)
        result = repr(expr.value)
        return f"return {result}" if tail_position and not is_compound else result

    elif isinstance(expr, Symbol):
        # Symbols are typically string literals
        result = f'"{expr.name}"'
        return f"return {result}" if tail_position and not is_compound else result

    elif isinstance(expr, Constructor):
        # Constructor reference
        result = f"ir.{expr.name}"
        return f"return {result}" if tail_position and not is_compound else result

    elif isinstance(expr, Call):
        # Special case: Handle special builtins inline
        if isinstance(expr.func, Builtin):
            if expr.func.name == "list_concat" and len(expr.args) == 2:
                # List concatenation: list1 + list2
                arg1 = generate_python(expr.args[0], indent, tail_position=False)
                arg2 = generate_python(expr.args[1], indent, tail_position=False)
                result = f"{arg1} + {arg2}"
                return f"return {result}" if tail_position and not is_compound else result
            elif expr.func.name == "make_list" and len(expr.args) == 1:
                # Make single-element list: [elem]
                arg = generate_python(expr.args[0], indent, tail_position=False)
                result = f"[{arg}]"
                return f"return {result}" if tail_position and not is_compound else result
            elif expr.func.name == "consume_terminal" and len(expr.args) == 1:
                # consume_terminal(name) -> self.consume_terminal(name)
                arg = generate_python(expr.args[0], indent, tail_position=False)
                result = f"self.consume_terminal({arg})"
                return f"return {result}" if tail_position and not is_compound else result
            elif expr.func.name == "consume_literal" and len(expr.args) == 1:
                # consume_literal(name) -> self.consume_literal(name)
                arg = generate_python(expr.args[0], indent, tail_position=False)
                result = f"self.consume_literal({arg})"
                return f"return {result}" if tail_position and not is_compound else result
            else:
                # Other builtins: map to self.builtin_name
                func_code = f"self.{expr.func.name}"
                if not expr.args:
                    result = f"{func_code}()"
                else:
                    args_code = ', '.join(generate_python(arg, indent, tail_position=False) for arg in expr.args)
                    result = f"{func_code}({args_code})"
                return f"return {result}" if tail_position and not is_compound else result

        # Regular call: Generate function expression (can be Var, Symbol, or arbitrary expression)
        func_code = generate_python(expr.func, indent, tail_position=False)

        if not expr.args:
            result = f"{func_code}()"
        else:
            args_code = ', '.join(generate_python(arg, indent, tail_position=False) for arg in expr.args)
            result = f"{func_code}({args_code})"

        return f"return {result}" if tail_position and not is_compound else result

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
        init_code = generate_python(expr.init, indent, tail_position=False)

        # Check if body is another Let (for proper nesting)
        if isinstance(expr.body, Let):
            # Nested Let: generate as sequence of assignments
            body_code = generate_python_let_sequence(expr.body, indent, tail_position=tail_position)
            return f"{var_name} = {init_code}\n{indent}{body_code}"
        else:
            body_code = generate_python(expr.body, indent, tail_position=False)
            if tail_position:
                return f"{var_name} = {init_code}\n{indent}return {body_code}"
            else:
                return f"{var_name} = {init_code}\n{indent}{body_code}"

    elif isinstance(expr, IfElse):
        # Generate if-else conditional
        cond_code = generate_python(expr.condition, indent, tail_position=False)

        if expr.else_branch:
            # With else branch, generate as expression or statement depending on context
            if tail_position:
                # Generate as if-elif-else statement with returns
                then_code = generate_python(expr.then_branch, indent + "    ", tail_position=False)
                else_code = generate_python(expr.else_branch, indent + "    ", tail_position=False)
                return f"if {cond_code}:\n{indent}    return {then_code}\n{indent}else:\n{indent}    return {else_code}"
            else:
                # Generate as ternary expression
                then_code = generate_python(expr.then_branch, indent, tail_position=False)
                else_code = generate_python(expr.else_branch, indent, tail_position=False)
                return f"({then_code} if {cond_code} else {else_code})"
        else:
            # Without else branch, generate as statement
            then_code = generate_python(expr.then_branch, indent + "    ", tail_position=tail_position)
            return f"if {cond_code}:\n{indent}    {then_code}"

    elif isinstance(expr, Seq):
        # Generate sequence of expressions
        if not expr.exprs:
            return "pass"

        lines = []
        for i, e in enumerate(expr.exprs):
            is_last = (i == len(expr.exprs) - 1)
            e_code = generate_python(e, indent, tail_position=(tail_position and is_last))
            lines.append(e_code)

        return f"\n{indent}".join(lines)

    elif isinstance(expr, While):
        # Generate while loop
        cond_code = generate_python(expr.condition, indent, tail_position=False)
        body_code = generate_python(expr.body, indent + "    ", tail_position=False)
        result = f"while {cond_code}:\n{indent}    {body_code}"
        if tail_position:
            # While loop doesn't return a value, but if in tail position, add return None
            result += f"\n{indent}return None"
        return result

    elif isinstance(expr, TryCatch):
        # Generate try-catch
        try_code = generate_python(expr.try_body, indent + "    ", tail_position=tail_position)

        if expr.catch_body:
            catch_code = generate_python(expr.catch_body, indent + "    ", tail_position=tail_position)
            exc_type = expr.exception_type or "Exception"
            return f"try:\n{indent}    {try_code}\n{indent}except {exc_type}:\n{indent}    {catch_code}"
        else:
            return f"try:\n{indent}    {try_code}\n{indent}except:\n{indent}    pass"

    elif isinstance(expr, Assign):
        # Generate assignment
        var_name = escape_identifier(expr.var)
        expr_code = generate_python(expr.expr, indent, tail_position=False)
        result = f"{var_name} = {expr_code}"
        # Assign doesn't produce a value, but if in tail position return None
        if tail_position:
            result += f"\n{indent}return None"
        return result

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
            body_inner = generate_python(expr.body, indent + "    ", tail_position=True)
            body_code = f"{indent}    {body_inner}"

        return f"def {func_name}({params_str}){ret_hint}:\n{body_code}"

    elif isinstance(expr, ParseNonterminalDef):
        # Generate parse method definition
        func_name = f"parse_{expr.nonterminal.name}"

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
            body_inner = generate_python(expr.body, indent + "    ", tail_position=True)
            body_code = f"{indent}    {body_inner}"

        return f"def {func_name}(self, {params_str}){ret_hint}:\n{body_code}"

    elif isinstance(expr, ParseNonterminal):
        # Generate parse method call
        func_name = f"self.parse_{expr.nonterminal.name}"
        if not expr.args:
            result = f"{func_name}()"
        else:
            args_code = ', '.join(generate_python(arg, indent, tail_position=False) for arg in expr.args)
            result = f"{func_name}({args_code})"
        return f"return {result}" if tail_position and not is_compound else result

    else:
        raise ValueError(f"Unknown action expression type: {type(expr)}")


def generate_python_let_sequence(expr: Let, indent: str = "", tail_position: bool = False) -> str:
    """Generate Python code for a sequence of Let-bindings.

    Handles nested Let-bindings by flattening them into a sequence
    of assignments followed by a return.

    Args:
        expr: Let expression (possibly nested)
        indent: Current indentation level
        tail_position: Whether the final expression is in tail position

    Returns:
        Python code with assignments and final return
    """
    assignments = []
    current = expr

    # Collect all Let-bindings in sequence
    while isinstance(current, Let):
        var_name = escape_identifier(current.var)
        init_code = generate_python(current.init, indent, tail_position=False)
        assignments.append(f"{var_name} = {init_code}")
        current = current.body

    # Generate the final expression (not a Let)
    final_code = generate_python(current, indent, tail_position=False)

    # Combine all assignments and return
    if tail_position:
        lines = assignments + [f"return {final_code}"]
    else:
        lines = assignments + [final_code]
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
