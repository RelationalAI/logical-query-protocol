"""Code generation for Python from semantic action AST.

This module generates Python code from semantic action expressions,
with proper keyword escaping and idiomatic Python style.
"""

from typing import Set, Union, List

from .target import TargetExpr, Var, Lit, Symbol, Builtin, Constructor, Call, Lambda, Let, IfElse, Seq, While, TryCatch, Assign, Return, Ok, Err, Try, FunDef, ParseNonterminalDef, ParseNonterminal, Type, BaseType, TupleType, ListType, ResultType, TargetNode, gensym


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

    elif isinstance(typ, ResultType):
        ok_type = generate_python_type(typ.ok_type)
        err_type = generate_python_type(typ.err_type)
        return f"Tuple[bool, Union[{ok_type}, {err_type}]]"

    else:
        raise ValueError(f"Unknown type: {type(typ)}")

def generate_python_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> str:
    """Generate Python code from a target IR expression.

    Code with side effects (e.g., consuming tokens) should be appended to the lines list.
    The function should then return a string containing Python value.

    Args:
        expr: Target expression for which to generate code
        lines: List of lines to which to append side effecting statements
        indent: Current indentation level

    Returns:
        A Python value as a string
    """
    if isinstance(expr, Var):
        return escape_identifier(expr.name)

    elif isinstance(expr, Lit):
        return repr(expr.value)

    elif isinstance(expr, Symbol):
        return f'"{expr.name}"'

    elif isinstance(expr, Constructor):
        return f"ir.{expr.name}"

    elif isinstance(expr, Builtin):
        assert expr.name != "list_concat"
        assert expr.name != "make_list"
        assert expr.name != "equal"
        return f"self.{expr.name}"

    elif isinstance(expr, ParseNonterminal):
        return f"self.parse_{expr.nonterminal.name}"

    elif isinstance(expr, Call):
        # Handle some special cases that don't turn into python calls.
        if isinstance(expr.func, Builtin):
            if expr.func.name == "list_concat" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                return f"{arg1} + {arg2}"
            if expr.func.name == "list_append" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                return f"{arg1} + [{arg2}]"
            if expr.func.name == "list_push" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                lines.append(f"{indent}{arg1}.append({arg2})")
                return "None"
            elif expr.func.name == "make_list":
                args = []
                for i in range(len(expr.args)):
                    arg = generate_python_lines(expr.args[i], lines, indent)
                    args.append(arg)
                args_code = ', '.join(args)
                return f"[{args_code}]"
            elif expr.func.name == "equal" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                return f"{arg1} == {arg2}"
            elif expr.func.name == "match_terminal" and len(expr.args) == 1:
                arg = generate_python_lines(expr.args[0], lines, indent)
                return f"self.match_terminal({arg})"
            elif expr.func.name == "match_literal" and len(expr.args) == 1:
                arg = generate_python_lines(expr.args[0], lines, indent)
                return f"self.match_literal({arg})"

        # Regular call
        f = generate_python_lines(expr.func, lines, indent)

        args = []
        for i in range(len(expr.args)):
            arg = generate_python_lines(expr.args[i], lines, indent)
            args.append(arg)
        args_code = ', '.join(args)
        tmp = gensym()
        lines.append(f"{indent}{tmp} = {f}({args_code})")
        return tmp

    elif isinstance(expr, Lambda):
        params = [escape_identifier(p) for p in expr.params]
        params_str = ', '.join(params) if params else ''
        f = gensym()
        body_lines = []
        lines.append(f"{indent}def {f}({params_str}):")
        v = generate_python_lines(expr.body, lines, indent + "    ")
        lines.append(f"{indent}    return {v}")
        return f

    elif isinstance(expr, Let):
        var_name = escape_identifier(expr.var)
        tmp1 = generate_python_lines(expr.init, lines, indent)
        lines.append(f"{indent}{var_name} = {tmp1}")
        tmp2 = generate_python_lines(expr.body, lines, indent)
        return tmp2

    elif isinstance(expr, IfElse):
        cond_code = generate_python_lines(expr.condition, lines, indent)
        tmp = gensym()
        lines.append(f"{indent}if {cond_code}:")
        then_code = generate_python_lines(expr.then_branch, lines, indent + "    ")
        lines.append(f"{indent}    {tmp} = {then_code}")
        lines.append(f"{indent}else:")
        else_code = generate_python_lines(expr.else_branch, lines, indent + "    ")
        lines.append(f"{indent}    {tmp} = {else_code}")
        return tmp

    elif isinstance(expr, Seq):
        tmp = "None"
        for e in expr.exprs:
            tmp = generate_python_lines(e, lines, indent)
        return tmp

    elif isinstance(expr, While):
        cond_code = generate_python_lines(expr.condition, lines, indent)
        lines.append(f"{indent}while {cond_code}:")
        then_code = generate_python_lines(expr.body, lines, indent + "    ")
        cond_code2 = generate_python_lines(expr.condition, lines, indent + "    ")
        lines.append(f"{indent}    {cond_code} = {cond_code2}")
        return "None"

    elif isinstance(expr, TryCatch):
        lines.append(f"{indent}try:")
        tmp = gensym()
        try_code = generate_python_lines(expr.try_body, lines, indent + "    ")
        lines.append(f"{indent}    {tmp} = {try_code}")
        exc_type = expr.exception_type or "Exception"
        lines.append(f"{indent}catch {exc_type}:")
        catch_code = generate_python_lines(expr.catch_body, lines, indent + "    ")
        lines.append(f"{indent}    {tmp} = {catch_code}")

    elif isinstance(expr, Assign):
        var_name = escape_identifier(expr.var)
        expr_code = generate_python_lines(expr.expr, lines, indent)
        lines.append(f"{indent}{var_name} = {expr_code}")
        return "None"

    elif isinstance(expr, Return):
        expr_code = generate_python_lines(expr.expr, lines, indent)
        lines.append(f"{indent}return {expr_code}")
        return "None"

    elif isinstance(expr, Ok):
        expr_code = generate_python_lines(expr.expr, lines, indent)
        return f"(True, {expr_code})"

    elif isinstance(expr, Err):
        expr_code = generate_python_lines(expr.expr, lines, indent)
        return f"(False, {expr_code})"

    elif isinstance(expr, Try):
        expr_code = generate_python_lines(expr.expr, lines, indent)
        isok = gensym('isok')
        unwrapped = gensym('unwrapped')
        lines.append(f"{indent}{isok}, {unwrapped} = {expr_code}")
        lines.append(f"{indent}if not {isok}:")
        if expr.rollback:
            generate_python_lines(expr.rollback, lines, indent + "    ")
        lines.append(f"{indent}    return {expr_code}")
        return unwrapped

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
            lines = []
            body_inner = generate_python_lines(expr.body, lines, indent + "    ")
            lines.append(f"{indent}    return {body_inner}")
            body_code = "\n".join(lines)

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
            lines = []
            body_inner = generate_python_lines(expr.body, lines, indent + "    ")
            lines.append(f"{indent}    return {body_inner}")
            body_code = "\n".join(lines)

        return f"{indent}def {func_name}(self{params_str}){ret_hint}:\n{body_code}"


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
