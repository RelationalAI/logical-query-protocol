"""Code generation for Python from semantic action AST.

This module generates Python code from semantic action expressions,
with proper keyword escaping and idiomatic Python style.
"""

from typing import Set, Union, List

from .target import TargetExpr, Var, Lit, Symbol, Builtin, Constructor, Call, Lambda, Let, IfElse, Seq, While, Assign, Return, FunDef, ParseNonterminalDef, ParseNonterminal, Type, BaseType, TupleType, ListType, OptionType, MessageType, FunctionType, TargetNode, gensym


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

    elif isinstance(typ, MessageType):
        return f"proto.{typ.name}"

    elif isinstance(typ, TupleType):
        if not typ.elements:
            return 'tuple[()]'
        element_types = ', '.join(generate_python_type(e) for e in typ.elements)
        return f"tuple[{element_types}]"

    elif isinstance(typ, ListType):
        element_type = generate_python_type(typ.element_type)
        return f"list[{element_type}]"

    elif isinstance(typ, OptionType):
        element_type = generate_python_type(typ.element_type)
        return f"Optional[{element_type}]"

    elif isinstance(typ, FunctionType):
        param_types = ', '.join(generate_python_type(param_type) for param_type in typ.param_types)
        return_type = generate_python_type(typ.return_type)
        return f"Callable[[{param_types}], {return_type}]"

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
        return f"proto.{expr.name}"

    elif isinstance(expr, Builtin):
        assert expr.name != "list_concat"
        assert expr.name != "make_list"
        assert expr.name != "equal"
        return f"self.{expr.name}"

    elif isinstance(expr, ParseNonterminal):
        return f"self.parse_{expr.nonterminal.name}"

    elif isinstance(expr, Call):
        # Special case: proto.Fragment construction with debug_info parameter
        if isinstance(expr.func, Constructor) and expr.func.name == "Fragment":
            # Check if one of the args is a Var named "debug_info"
            for i, arg in enumerate(expr.args):
                if isinstance(arg, Var) and arg.name == "debug_info":
                    # Generate debug_info computation before constructing Fragment
                    lines.append(f"{indent}debug_info = proto.DebugInfo(id_to_orig_name=self.id_to_debuginfo.get(id, {{}}), meta=self.meta(self.current()))")
                    break

        # Handle some special cases that don't turn into python calls.
        if isinstance(expr.func, Builtin):
            if expr.func.name == "fragment_id_from_string" and len(expr.args) == 1:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                return f"proto.FragmentId(id={arg1}.encode())"
            if expr.func.name == "relation_id_from_string" and len(expr.args) == 1:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                return f"proto.RelationId(id=int(hashlib.sha256({arg1}.encode()).hexdigest()[:16], 16))"
            if expr.func.name == "relation_id_from_int" and len(expr.args) == 1:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                return f"proto.RelationId(id={arg1})"
            if expr.func.name == "list_concat" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                return f"{arg1} + {arg2}"
            if expr.func.name == "list_append" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                return f"{arg1} + [{arg2}]"
            if expr.func.name == "list_push!" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                lines.append(f"{indent}{arg1}.append({arg2})")
                return "None"
            if expr.func.name == "error" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                lines.append(f"{indent}raise ParseError({arg1} + \": {{{arg2}}}\")")
                return "None"
            if expr.func.name == "error" and len(expr.args) == 1:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                lines.append(f"{indent}raise ParseError({arg1})")
                return "None"
            elif expr.func.name == "make_list":
                args = []
                for i in range(len(expr.args)):
                    arg = generate_python_lines(expr.args[i], lines, indent)
                    args.append(arg)
                args_code = ', '.join(args)
                return f"[{args_code}]"
            elif expr.func.name == "not" and len(expr.args) == 1:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                return f"not {arg1}"
            elif expr.func.name == "equal" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                return f"{arg1} == {arg2}"
            elif expr.func.name == "not_equal" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                return f"{arg1} != {arg2}"
            elif expr.func.name == "is_none" and len(expr.args) == 1:
                arg = generate_python_lines(expr.args[0], lines, indent)
                return f"{arg} is None"
            elif expr.func.name == "some" and len(expr.args) == 1:
                # In Python, 'some' is just the identity function for Optional values
                arg = generate_python_lines(expr.args[0], lines, indent)
                return arg
            elif expr.func.name == "match_lookahead_terminal" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                return f"self.match_lookahead_terminal({arg1}, {arg2})"
            elif expr.func.name == "match_lookahead_literal" and len(expr.args) == 2:
                arg1 = generate_python_lines(expr.args[0], lines, indent)
                arg2 = generate_python_lines(expr.args[1], lines, indent)
                return f"self.match_lookahead_literal({arg1}, {arg2})"
            elif expr.func.name == "match_terminal" and len(expr.args) == 1:
                arg = generate_python_lines(expr.args[0], lines, indent)
                return f"self.match_terminal({arg})"
            elif expr.func.name == "match_literal" and len(expr.args) == 1:
                arg = generate_python_lines(expr.args[0], lines, indent)
                return f"self.match_literal({arg})"
            elif expr.func.name == "consume_literal" and len(expr.args) == 1:
                arg = generate_python_lines(expr.args[0], lines, indent)
                lines.append(f"{indent}self.consume_literal({arg})")
                return "None"

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
        params = [escape_identifier(p.name) for p in expr.params]
        params_str = ', '.join(params) if params else ''
        f = gensym()
        body_lines = []
        lines.append(f"{indent}def {f}({params_str}):")
        v = generate_python_lines(expr.body, lines, indent + "    ")
        lines.append(f"{indent}    return {v}")
        return f

    elif isinstance(expr, Let):
        var_name = escape_identifier(expr.var.name)
        tmp1 = generate_python_lines(expr.init, lines, indent)
        lines.append(f"{indent}{var_name} = {tmp1}")
        tmp2 = generate_python_lines(expr.body, lines, indent)
        return tmp2

    elif isinstance(expr, IfElse):
        cond_code = generate_python_lines(expr.condition, lines, indent)
        if expr.then_branch == Lit(True):
            else_code = generate_python_lines(expr.else_branch, lines, indent + "    ")
            return f"({cond_code} or {else_code})"
        if expr.else_branch == Lit(False):
            then_code = generate_python_lines(expr.then_branch, lines, indent + "    ")
            return f"({cond_code} and {then_code})"

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
        m = len(lines)
        cond_code = generate_python_lines(expr.condition, lines, indent)
        non_trivial_cond = len(lines) > m
        # TODO This is a bit hacky!
        cond_code_is_lvalue = cond_code.isidentifier()
        lines.append(f"{indent}while {cond_code}:")
        n = len(lines)
        body_code = generate_python_lines(expr.body, lines, indent + "    ")
        if len(lines) == n:
            lines.append(f"{indent}    pass")
        # Update the condition variable
        if non_trivial_cond and cond_code_is_lvalue:
            cond_code2 = generate_python_lines(expr.condition, lines, indent + "    ")
            lines.append(f"{indent}    {cond_code} = {cond_code2}")
        return "None"

    elif isinstance(expr, Assign):
        var_name = escape_identifier(expr.var.name)
        expr_code = generate_python_lines(expr.expr, lines, indent)
        lines.append(f"{indent}{var_name} = {expr_code}")
        return "None"

    elif isinstance(expr, Return):
        expr_code = generate_python_lines(expr.expr, lines, indent)
        lines.append(f"{indent}return {expr_code}")
        return "None"

    else:
        raise ValueError(f"Unknown action expression type: {type(expr)}")


def generate_python_def(expr: Union[FunDef, ParseNonterminalDef], indent: str = "") -> str:
    if isinstance(expr, FunDef):
        func_name = escape_identifier(expr.name)

        params = []
        for param in expr.params:
            escaped_name = escape_identifier(param.name)
            type_hint = generate_python_type(param.type)
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
        for param in expr.params:
            escaped_name = escape_identifier(param.name)
            type_hint = generate_python_type(param.type)
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


def generate_python(expr: TargetExpr, indent: str = "") -> str:
    """Generate Python code for a single expression (inline style).

    Args:
        expr: Action expression to generate code for
        indent: Indentation string (default: no indent)

    Returns:
        Python code as a string
    """
    if isinstance(expr, Var):
        return escape_identifier(expr.name)
    elif isinstance(expr, Lit):
        return repr(expr.value)
    elif isinstance(expr, Symbol):
        return f'"{expr.name}"'
    elif isinstance(expr, Call):
        func_code = generate_python(expr.func, indent)
        args_code = ', '.join(generate_python(arg, indent) for arg in expr.args)
        return f"{func_code}({args_code})"
    elif isinstance(expr, Lambda):
        params = [escape_identifier(p.name) for p in expr.params]
        params_str = ', '.join(params) if params else ''
        body_code = generate_python(expr.body, indent)
        return f"lambda {params_str}: {body_code}"
    elif isinstance(expr, Let):
        # For Let, we need multi-line
        lines = []
        result = generate_python_lines(expr, lines, indent)
        if lines:
            return '\n'.join(lines) + '\n' + result
        return result
    else:
        # Fall back to generate_python_lines for complex expressions
        lines = []
        result = generate_python_lines(expr, lines, indent)
        if lines:
            return '\n'.join(lines) + '\n' + result
        return result


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
    'generate_python_lines',
    'generate_python_function_body',
    'PYTHON_KEYWORDS',
]
