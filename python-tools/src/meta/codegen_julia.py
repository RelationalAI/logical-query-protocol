"""Code generation for Julia from semantic action AST.

This module generates Julia code from semantic action expressions,
with proper keyword escaping and idiomatic Julia style.
"""

from typing import Set, Union, List

from .target import TargetExpr, Var, Lit, Symbol, Builtin, Constructor, Call, Lambda, Let, IfElse, Seq, While, Assign, Return, FunDef, ParseNonterminalDef, ParseNonterminal, Type, BaseType, TupleType, ListType, OptionType, MessageType, FunctionType, gensym


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
    """
    if name in JULIA_KEYWORDS:
        return f'var"{name}"'
    return name


def generate_julia_type(typ: Type) -> str:
    """Generate Julia type annotation from a Type expression."""
    if isinstance(typ, BaseType):
        type_map = {
            'Int64': 'Int64',
            'Float64': 'Float64',
            'String': 'String',
            'Boolean': 'Bool',
        }
        return type_map.get(typ.name, typ.name)

    elif isinstance(typ, MessageType):
        return f"Proto.{typ.name}"

    elif isinstance(typ, TupleType):
        if not typ.elements:
            return 'Tuple{}'
        element_types = ', '.join(generate_julia_type(e) for e in typ.elements)
        return f"Tuple{{{element_types}}}"

    elif isinstance(typ, ListType):
        element_type = generate_julia_type(typ.element_type)
        return f"Vector{{{element_type}}}"

    elif isinstance(typ, OptionType):
        element_type = generate_julia_type(typ.element_type)
        return f"Union{{Nothing, {element_type}}}"

    elif isinstance(typ, FunctionType):
        param_types = ', '.join(generate_julia_type(pt) for pt in typ.param_types)
        return_type = generate_julia_type(typ.return_type)
        return f"Function"  # Julia doesn't have precise function types

    else:
        raise ValueError(f"Unknown type: {type(typ)}")


def generate_julia_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> str:
    """Generate Julia code from a target IR expression.

    Code with side effects should be appended to the lines list.
    The function returns a string containing a Julia value expression.
    """
    if isinstance(expr, Var):
        return escape_identifier(expr.name)

    elif isinstance(expr, Lit):
        if expr.value is None:
            return "nothing"
        elif isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        elif isinstance(expr.value, str):
            return repr(expr.value)
        else:
            return repr(expr.value)

    elif isinstance(expr, Symbol):
        return f":{expr.name}"

    elif isinstance(expr, Constructor):
        return f"Proto.{expr.name}"

    elif isinstance(expr, Builtin):
        # These are handled specially in Call
        return f"parser.{expr.name}"

    elif isinstance(expr, ParseNonterminal):
        return f"parse_{expr.nonterminal.name}"

    elif isinstance(expr, Call):
        # Handle builtin special cases
        if isinstance(expr.func, Builtin):
            if expr.func.name == "fragment_id_from_string" and len(expr.args) == 1:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                return f"Proto.FragmentId(id=Vector{{UInt8}}({arg1}))"
            if expr.func.name == "relation_id_from_string" and len(expr.args) == 1:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                return f"Proto.RelationId(id=parse(UInt64, bytes2hex(sha256({arg1})[1:8]), base=16))"
            if expr.func.name == "relation_id_from_int" and len(expr.args) == 1:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                return f"Proto.RelationId(id={arg1})"
            if expr.func.name == "list_concat" and len(expr.args) == 2:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                arg2 = generate_julia_lines(expr.args[1], lines, indent)
                return f"vcat({arg1}, {arg2})"
            if expr.func.name == "list_append" and len(expr.args) == 2:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                arg2 = generate_julia_lines(expr.args[1], lines, indent)
                return f"vcat({arg1}, [{arg2}])"
            if expr.func.name == "list_push!" and len(expr.args) == 2:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                arg2 = generate_julia_lines(expr.args[1], lines, indent)
                lines.append(f"{indent}push!({arg1}, {arg2})")
                return "nothing"
            if expr.func.name == "error" and len(expr.args) == 2:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                arg2 = generate_julia_lines(expr.args[1], lines, indent)
                lines.append(f"{indent}throw(ParseError({arg1} * \": \" * string({arg2})))")
                return "nothing"
            if expr.func.name == "error" and len(expr.args) == 1:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                lines.append(f"{indent}throw(ParseError({arg1}))")
                return "nothing"
            elif expr.func.name == "make_list":
                args = []
                for arg in expr.args:
                    args.append(generate_julia_lines(arg, lines, indent))
                args_code = ', '.join(args)
                return f"[{args_code}]"
            elif expr.func.name == "not" and len(expr.args) == 1:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                return f"!{arg1}"
            elif expr.func.name == "equal" and len(expr.args) == 2:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                arg2 = generate_julia_lines(expr.args[1], lines, indent)
                return f"{arg1} == {arg2}"
            elif expr.func.name == "not_equal" and len(expr.args) == 2:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                arg2 = generate_julia_lines(expr.args[1], lines, indent)
                return f"{arg1} != {arg2}"
            elif expr.func.name == "is_none" and len(expr.args) == 1:
                arg = generate_julia_lines(expr.args[0], lines, indent)
                return f"isnothing({arg})"
            elif expr.func.name == "some" and len(expr.args) == 1:
                arg = generate_julia_lines(expr.args[0], lines, indent)
                return arg
            elif expr.func.name == "fst" and len(expr.args) == 1:
                arg = generate_julia_lines(expr.args[0], lines, indent)
                return f"{arg}[1]"
            elif expr.func.name == "snd" and len(expr.args) == 1:
                arg = generate_julia_lines(expr.args[0], lines, indent)
                return f"{arg}[2]"
            elif expr.func.name == "Tuple" and len(expr.args) >= 2:
                args = [generate_julia_lines(arg, lines, indent) for arg in expr.args]
                return f"({', '.join(args)},)"
            elif expr.func.name == "length" and len(expr.args) == 1:
                arg = generate_julia_lines(expr.args[0], lines, indent)
                return f"length({arg})"
            elif expr.func.name == "unwrap_option_or" and len(expr.args) == 2:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                arg2 = generate_julia_lines(expr.args[1], lines, indent)
                return f"something({arg1}, {arg2})"
            elif expr.func.name == "match_lookahead_terminal" and len(expr.args) == 2:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                arg2 = generate_julia_lines(expr.args[1], lines, indent)
                return f"match_lookahead_terminal(parser, {arg1}, {arg2})"
            elif expr.func.name == "match_lookahead_literal" and len(expr.args) == 2:
                arg1 = generate_julia_lines(expr.args[0], lines, indent)
                arg2 = generate_julia_lines(expr.args[1], lines, indent)
                return f"match_lookahead_literal(parser, {arg1}, {arg2})"
            elif expr.func.name == "match_terminal" and len(expr.args) == 1:
                arg = generate_julia_lines(expr.args[0], lines, indent)
                return f"match_terminal(parser, {arg})"
            elif expr.func.name == "match_literal" and len(expr.args) == 1:
                arg = generate_julia_lines(expr.args[0], lines, indent)
                return f"match_literal(parser, {arg})"
            elif expr.func.name == "consume_literal" and len(expr.args) == 1:
                arg = generate_julia_lines(expr.args[0], lines, indent)
                lines.append(f"{indent}consume_literal(parser, {arg})")
                return "nothing"

        # Regular call
        f = generate_julia_lines(expr.func, lines, indent)

        args = []
        for arg in expr.args:
            args.append(generate_julia_lines(arg, lines, indent))
        args_code = ', '.join(args)
        tmp = gensym()
        lines.append(f"{indent}{tmp} = {f}({args_code})")
        return tmp

    elif isinstance(expr, Lambda):
        params = [escape_identifier(p.name) for p in expr.params]
        params_str = ', '.join(params) if params else ''
        f = gensym()
        lines.append(f"{indent}function {f}({params_str})")
        v = generate_julia_lines(expr.body, lines, indent + "    ")
        lines.append(f"{indent}    return {v}")
        lines.append(f"{indent}end")
        return f

    elif isinstance(expr, Let):
        var_name = escape_identifier(expr.var.name)
        tmp1 = generate_julia_lines(expr.init, lines, indent)
        lines.append(f"{indent}{var_name} = {tmp1}")
        tmp2 = generate_julia_lines(expr.body, lines, indent)
        return tmp2

    elif isinstance(expr, IfElse):
        cond_code = generate_julia_lines(expr.condition, lines, indent)
        if expr.then_branch == Lit(True):
            else_code = generate_julia_lines(expr.else_branch, lines, indent + "    ")
            return f"({cond_code} || {else_code})"
        if expr.else_branch == Lit(False):
            then_code = generate_julia_lines(expr.then_branch, lines, indent + "    ")
            return f"({cond_code} && {then_code})"

        tmp = gensym()
        lines.append(f"{indent}if {cond_code}")
        then_code = generate_julia_lines(expr.then_branch, lines, indent + "    ")
        lines.append(f"{indent}    {tmp} = {then_code}")
        lines.append(f"{indent}else")
        else_code = generate_julia_lines(expr.else_branch, lines, indent + "    ")
        lines.append(f"{indent}    {tmp} = {else_code}")
        lines.append(f"{indent}end")
        return tmp

    elif isinstance(expr, Seq):
        tmp = "nothing"
        for e in expr.exprs:
            tmp = generate_julia_lines(e, lines, indent)
        return tmp

    elif isinstance(expr, While):
        m = len(lines)
        cond_code = generate_julia_lines(expr.condition, lines, indent)
        non_trivial_cond = len(lines) > m
        cond_code_is_lvalue = cond_code.isidentifier()
        lines.append(f"{indent}while {cond_code}")
        n = len(lines)
        body_code = generate_julia_lines(expr.body, lines, indent + "    ")
        if len(lines) == n:
            lines.append(f"{indent}    # empty body")
        # Update the condition variable
        if non_trivial_cond and cond_code_is_lvalue:
            cond_code2 = generate_julia_lines(expr.condition, lines, indent + "    ")
            lines.append(f"{indent}    {cond_code} = {cond_code2}")
        lines.append(f"{indent}end")
        return "nothing"

    elif isinstance(expr, Assign):
        var_name = escape_identifier(expr.var.name)
        expr_code = generate_julia_lines(expr.expr, lines, indent)
        lines.append(f"{indent}{var_name} = {expr_code}")
        return "nothing"

    elif isinstance(expr, Return):
        expr_code = generate_julia_lines(expr.expr, lines, indent)
        lines.append(f"{indent}return {expr_code}")
        return "nothing"

    else:
        raise ValueError(f"Unknown action expression type: {type(expr)}")


def generate_julia_def(expr: Union[FunDef, ParseNonterminalDef], indent: str = "") -> str:
    """Generate Julia function definition."""
    if isinstance(expr, FunDef):
        func_name = escape_identifier(expr.name)

        params = []
        for param in expr.params:
            escaped_name = escape_identifier(param.name)
            type_hint = generate_julia_type(param.type)
            params.append(f"{escaped_name}::{type_hint}")

        params_str = ', '.join(params)

        ret_hint = f"::{generate_julia_type(expr.return_type)}" if expr.return_type else ""

        if expr.body is None:
            body_code = f"{indent}    nothing"
        else:
            lines = []
            body_inner = generate_julia_lines(expr.body, lines, indent + "    ")
            lines.append(f"{indent}    return {body_inner}")
            body_code = "\n".join(lines)

        return f"{indent}function {func_name}({params_str}){ret_hint}\n{body_code}\n{indent}end"

    elif isinstance(expr, ParseNonterminalDef):
        func_name = f"parse_{expr.nonterminal.name}"

        params = ["parser::Parser"]
        for param in expr.params:
            escaped_name = escape_identifier(param.name)
            type_hint = generate_julia_type(param.type)
            params.append(f"{escaped_name}::{type_hint}")

        params_str = ', '.join(params)

        ret_hint = f"::{generate_julia_type(expr.return_type)}" if expr.return_type else ""

        if expr.body is None:
            body_code = f"{indent}    nothing"
        else:
            lines = []
            body_inner = generate_julia_lines(expr.body, lines, indent + "    ")
            lines.append(f"{indent}    return {body_inner}")
            body_code = "\n".join(lines)

        return f"{indent}function {func_name}({params_str}){ret_hint}\n{body_code}\n{indent}end"


def generate_julia(expr: TargetExpr, indent: str = "") -> str:
    """Generate Julia code for a single expression (inline style)."""
    if isinstance(expr, Var):
        return escape_identifier(expr.name)
    elif isinstance(expr, Lit):
        if expr.value is None:
            return "nothing"
        elif isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        return repr(expr.value)
    elif isinstance(expr, Symbol):
        return f":{expr.name}"
    elif isinstance(expr, Call):
        func_code = generate_julia(expr.func, indent)
        args_code = ', '.join(generate_julia(arg, indent) for arg in expr.args)
        return f"{func_code}({args_code})"
    elif isinstance(expr, Lambda):
        params = [escape_identifier(p.name) for p in expr.params]
        params_str = ', '.join(params) if params else ''
        body_code = generate_julia(expr.body, indent)
        if params:
            return f"({params_str}) -> {body_code}"
        else:
            return f"() -> {body_code}"
    elif isinstance(expr, Let):
        lines = []
        result = generate_julia_lines(expr, lines, indent)
        if lines:
            return '\n'.join(lines) + '\n' + result
        return result
    else:
        lines = []
        result = generate_julia_lines(expr, lines, indent)
        if lines:
            return '\n'.join(lines) + '\n' + result
        return result


def generate_julia_function_body(expr: TargetExpr, indent: str = "    ") -> str:
    """Generate Julia code for a function body with proper indentation."""
    return generate_julia(expr, indent)


__all__ = [
    'escape_identifier',
    'generate_julia',
    'generate_julia_lines',
    'generate_julia_def',
    'generate_julia_function_body',
    'JULIA_KEYWORDS',
]
