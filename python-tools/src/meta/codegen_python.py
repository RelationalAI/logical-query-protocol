"""Code generation for Python from semantic action AST.

This module generates Python code from semantic action expressions,
with proper keyword escaping and idiomatic Python style.
"""

from typing import Set, Union

from meta.proto_ast import ProtoMessage
from .target import TargetExpr, Var, Lit, Symbol, Builtin, Constructor, Call, Lambda, Let, IfElse, Seq, While, TryCatch, Assign, Return, Ok, Err, Try, FunDef, ParseNonterminalDef, ParseNonterminal, Type, BaseType, TupleType, ListType, ResultType, TargetNode
from itertools import count
from more_itertools import peekable


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

# id generator for Clusters
_global_id = peekable(count(0))
def next_id():
    return next(_global_id)

def gensym(prefix: str = "_t") -> str:
    return f"{prefix}{next_id()}"

def generate_python(expr: TargetExpr, sink: str, indent: str = "") -> str:
    """Generate Python code from an action expression.

    Args:
        expr: Action expression to generate code for
        indent: Current indentation level

    Returns:
        Python code as a string
    """
    if isinstance(expr, Var):
        return f"{sink} = {escape_identifier(expr.name)}"

    elif isinstance(expr, Lit):
        return f"{sink} = {repr(expr.value)}"

    elif isinstance(expr, Symbol):
        return f'{sink} = "{expr.name}"'

    elif isinstance(expr, Constructor):
        return f"{sink} = ir.{expr.name}"

    elif isinstance(expr, Call):
        # Special case: Handle special builtins inline
        if isinstance(expr.func, Builtin):
            if expr.func.name == "list_concat" and len(expr.args) == 2:
                v1 = gensym()
                v2 = gensym()
                arg1 = generate_python(expr.args[0], v1, indent)
                arg2 = generate_python(expr.args[1], v2, indent)
                return f"{arg1}\n{indent}{arg2}\n{indent}{sink} = {v1} + {v2}"
            elif expr.func.name == "make_list" and len(expr.args) == 1:
                v = gensym()
                arg = generate_python(expr.args[0], v, indent)
                return f"{arg}\n{indent}{sink} = [{v}]"
            elif expr.func.name == "consume_terminal" and len(expr.args) == 1:
                v = gensym()
                arg = generate_python(expr.args[0], v, indent)
                return f"{arg}\n{indent}{sink} = self.consume_terminal({v})"
            elif expr.func.name == "consume_literal" and len(expr.args) == 1:
                v = gensym()
                arg = generate_python(expr.args[0], v, indent)
                return f"{arg}\n{indent}{sink} = self.consume_literal({v})"
            else:
                func_code = f"self.{expr.func.name}"
                if not expr.args:
                    return f"{sink} = {func_code}()"
                else:
                    vs = [gensym() for _ in expr.args]
                    vs_code = ', '.join(vs)
                    args = []
                    for i in range(len(expr.args)):
                        arg = generate_python(expr.args[i], vs[i], indent)
                        args.append(arg)
                    args_code = f"\n{indent}".join(args)
                    return f"{args_code}\n{indent}{sink} = {func_code}({vs_code})"
        elif isinstance(expr.func, Constructor):
            func_code = f"{expr.func.name}"
            if not expr.args:
                return f"{sink} = {func_code}()"
            else:
                vs = [gensym() for _ in expr.args]
                vs_code = ', '.join(vs)
                args = []
                for i in range(len(expr.args)):
                    arg = generate_python(expr.args[i], vs[i], indent)
                    args.append(arg)
                args_code = f"\n{indent}".join(args)
                return f"{args_code}\n{indent}{sink} = {func_code}({vs_code})"

        assert isinstance(expr.func, (Lambda, Var)), f"Unexpected function type: {type(expr.func)}"

        # Regular call
        f = gensym()
        func_code = generate_python(expr.func, f, indent)

        if not expr.args:
            return f"{func_code}\n{indent}{sink} = {f}()"
        else:
            vs = [gensym() for _ in expr.args]
            vs_code = ', '.join(vs)
            args = []
            for i in range(len(expr.args)):
                arg = generate_python(expr.args[i], vs[i], indent)
                args.append(arg)
            args_code = f"\n{indent}".join(args)
            return f"{func_code}\n{indent}{args_code}\n{indent}{sink} = {f}({vs_code})"

    elif isinstance(expr, Lambda):
        params = [escape_identifier(p) for p in expr.params]
        params_str = ', '.join(params) if params else ''
        v = gensym()
        body_code = generate_python(expr.body, v, indent)
        f = gensym()
        return f"def {f}({params_str}):\n{indent}{body_code}\n{indent}return {v}\n{indent}{sink} = {f}"

    elif isinstance(expr, Let):
        var_name = escape_identifier(expr.var)
        init_code = generate_python(expr.init, var_name, indent)
        body_code = generate_python(expr.body, sink, indent)
        return f"{init_code}\n{indent}{body_code}"

    elif isinstance(expr, IfElse):
        cond = gensym()
        cond_code = generate_python(expr.condition, cond, indent)
        then_code = generate_python(expr.then_branch, sink, indent + "    ")
        else_code = generate_python(expr.else_branch, sink, indent + "    ")
        return f"{cond_code}\n{indent}if {cond}:\n{indent}    {then_code}\n{indent}else:\n{indent}    {else_code}"

    elif isinstance(expr, Seq):
        if not expr.exprs:
            return "pass"

        lines = []
        for i, e in enumerate(expr.exprs):
            if i != len(expr.exprs) - 1:
                v = gensym()
                e_code = generate_python(e, v, indent)
                lines.append(e_code)
            else:
                e_code = generate_python(e, sink, indent)
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
        expr_code = generate_python(expr.expr, var_name, indent)
        return f"{expr_code}\n{indent}{sink} = {var_name}"

    elif isinstance(expr, Return):
        v = gensym()
        expr_code = generate_python(expr.expr, v, indent)
        return f"{expr_code}\n{indent}return {v}"

    elif isinstance(expr, Ok):
        v = gensym()
        expr_code = generate_python(expr.expr, v, indent)
        return f"{expr_code}\n{indent}{sink} = (True, {v})"

    elif isinstance(expr, Err):
        v = gensym()
        expr_code = generate_python(expr.expr, v, indent)
        return f"{expr_code}\n{indent}{sink} = (False, {v})"

    elif isinstance(expr, Try):
        v = gensym()
        expr_code = generate_python(expr.expr, v, indent)
        if expr.rollback:
            junk = gensym()
            undo_code = generate_python(expr.rollback, junk, indent + "    ")
            r = gensym()
            u = gensym()
            isok = gensym()
            return f"{r} = {expr_code}\n{indent}{isok}, {u} = {r}\n{indent}if not {isok}:\n{indent}{undo_code}\n{indent}    return {r}\n{indent}else:{indent}    {sink} = {u}"
        else:
            r = gensym()
            u = gensym()
            isok = gensym()
            return f"{r} = {expr_code}\n{indent}{isok}, {u} = {r}\n{indent}if not {isok}:\n{indent}    return {r}\n{indent}else:{indent}    {sink} = {u}"

    elif isinstance(expr, ParseNonterminal):
        func_name = f"self.parse_{expr.nonterminal.name}"
        if not expr.args:
            return f"{sink} = {func_name}()"
        else:
            vs = [gensym() for _ in expr.args]
            vs_code = ', '.join(vs)
            args = []
            for i in range(len(expr.args)):
                arg = generate_python(expr.args[i], vs[i], indent)
                args.append(arg)
            args_code = f"\n{indent}".join(args)
            return f"{args_code}\n{indent}{sink} = {func_name}({vs_code})"

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
            v = gensym()
            body_inner = generate_python(expr.body, v, indent + "    ")
            body_code = f"{indent}    {body_inner}\n{indent}    return {v}"

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
