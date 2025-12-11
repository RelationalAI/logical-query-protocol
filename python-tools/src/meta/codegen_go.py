"""Code generation for Go from semantic action AST.

This module generates Go code from semantic action expressions,
with proper keyword escaping and idiomatic Go style.
"""

from typing import Set, Union, List

from .target import TargetExpr, Var, Lit, Symbol, Builtin, Constructor, Call, Lambda, Let, IfElse, Seq, While, Assign, Return, FunDef, ParseNonterminalDef, ParseNonterminal, Type, BaseType, TupleType, ListType, OptionType, MessageType, FunctionType, gensym


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
    """
    if name in GO_KEYWORDS:
        return f"{name}_"
    return name


def generate_go_type(typ: Type) -> str:
    """Generate Go type from a Type expression."""
    if isinstance(typ, BaseType):
        type_map = {
            'Int64': 'int64',
            'Float64': 'float64',
            'String': 'string',
            'Boolean': 'bool',
        }
        return type_map.get(typ.name, typ.name)

    elif isinstance(typ, MessageType):
        return f"*proto.{typ.name}"

    elif isinstance(typ, TupleType):
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

    elif isinstance(typ, OptionType):
        element_type = generate_go_type(typ.element_type)
        return f"*{element_type}"  # Go uses pointers for optional values

    elif isinstance(typ, FunctionType):
        param_types = ', '.join(generate_go_type(pt) for pt in typ.param_types)
        return_type = generate_go_type(typ.return_type)
        return f"func({param_types}) {return_type}"

    else:
        raise ValueError(f"Unknown type: {type(typ)}")


def generate_go_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> str:
    """Generate Go code from a target IR expression.

    Code with side effects should be appended to the lines list.
    The function returns a string containing a Go value expression.
    """
    if isinstance(expr, Var):
        return escape_identifier(expr.name)

    elif isinstance(expr, Lit):
        if expr.value is None:
            return "nil"
        elif isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        elif isinstance(expr.value, str):
            return f'"{expr.value}"'
        else:
            return repr(expr.value)

    elif isinstance(expr, Symbol):
        return f'"{expr.name}"'

    elif isinstance(expr, Constructor):
        return f"proto.{expr.name}"

    elif isinstance(expr, Builtin):
        return f"parser.{expr.name}"

    elif isinstance(expr, ParseNonterminal):
        return f"parse{expr.nonterminal.name.title().replace('_', '')}"

    elif isinstance(expr, Call):
        # Handle builtin special cases
        if isinstance(expr.func, Builtin):
            if expr.func.name == "fragment_id_from_string" and len(expr.args) == 1:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                return f"&proto.FragmentId{{Id: []byte({arg1})}}"
            if expr.func.name == "relation_id_from_string" and len(expr.args) == 1:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                tmp = gensym()
                lines.append(f"{indent}h := sha256.Sum256([]byte({arg1}))")
                lines.append(f"{indent}{tmp} := &proto.RelationId{{Id: binary.BigEndian.Uint64(h[:8])}}")
                return tmp
            if expr.func.name == "relation_id_from_int" and len(expr.args) == 1:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                return f"&proto.RelationId{{Id: uint64({arg1})}}"
            if expr.func.name == "list_concat" and len(expr.args) == 2:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                arg2 = generate_go_lines(expr.args[1], lines, indent)
                return f"append({arg1}, {arg2}...)"
            if expr.func.name == "list_append" and len(expr.args) == 2:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                arg2 = generate_go_lines(expr.args[1], lines, indent)
                return f"append({arg1}, {arg2})"
            if expr.func.name == "list_push!" and len(expr.args) == 2:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                arg2 = generate_go_lines(expr.args[1], lines, indent)
                lines.append(f"{indent}{arg1} = append({arg1}, {arg2})")
                return "nil"
            if expr.func.name == "error" and len(expr.args) == 2:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                arg2 = generate_go_lines(expr.args[1], lines, indent)
                lines.append(f'{indent}panic(fmt.Sprintf("%s: %v", {arg1}, {arg2}))')
                return "nil"
            if expr.func.name == "error" and len(expr.args) == 1:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                lines.append(f"{indent}panic({arg1})")
                return "nil"
            elif expr.func.name == "make_list":
                if len(expr.args) == 0:
                    return "[]interface{}{}"
                args = []
                for arg in expr.args:
                    args.append(generate_go_lines(arg, lines, indent))
                args_code = ', '.join(args)
                return f"[]interface{{{{}}}}{{{args_code}}}"
            elif expr.func.name == "not" and len(expr.args) == 1:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                return f"!{arg1}"
            elif expr.func.name == "equal" and len(expr.args) == 2:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                arg2 = generate_go_lines(expr.args[1], lines, indent)
                return f"{arg1} == {arg2}"
            elif expr.func.name == "not_equal" and len(expr.args) == 2:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                arg2 = generate_go_lines(expr.args[1], lines, indent)
                return f"{arg1} != {arg2}"
            elif expr.func.name == "is_none" and len(expr.args) == 1:
                arg = generate_go_lines(expr.args[0], lines, indent)
                return f"{arg} == nil"
            elif expr.func.name == "some" and len(expr.args) == 1:
                arg = generate_go_lines(expr.args[0], lines, indent)
                return arg
            elif expr.func.name == "fst" and len(expr.args) == 1:
                arg = generate_go_lines(expr.args[0], lines, indent)
                return f"{arg}.F0"
            elif expr.func.name == "snd" and len(expr.args) == 1:
                arg = generate_go_lines(expr.args[0], lines, indent)
                return f"{arg}.F1"
            elif expr.func.name == "Tuple" and len(expr.args) >= 2:
                args = [generate_go_lines(arg, lines, indent) for arg in expr.args]
                fields = ', '.join(f"F{i}: {a}" for i, a in enumerate(args))
                return f"struct{{{fields}}}"
            elif expr.func.name == "length" and len(expr.args) == 1:
                arg = generate_go_lines(expr.args[0], lines, indent)
                return f"len({arg})"
            elif expr.func.name == "unwrap_option_or" and len(expr.args) == 2:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                arg2 = generate_go_lines(expr.args[1], lines, indent)
                tmp = gensym()
                lines.append(f"{indent}var {tmp} = {arg2}")
                lines.append(f"{indent}if {arg1} != nil {{")
                lines.append(f"{indent}\t{tmp} = *{arg1}")
                lines.append(f"{indent}}}")
                return tmp
            elif expr.func.name == "match_lookahead_terminal" and len(expr.args) == 2:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                arg2 = generate_go_lines(expr.args[1], lines, indent)
                return f"parser.matchLookaheadTerminal({arg1}, {arg2})"
            elif expr.func.name == "match_lookahead_literal" and len(expr.args) == 2:
                arg1 = generate_go_lines(expr.args[0], lines, indent)
                arg2 = generate_go_lines(expr.args[1], lines, indent)
                return f"parser.matchLookaheadLiteral({arg1}, {arg2})"
            elif expr.func.name == "match_terminal" and len(expr.args) == 1:
                arg = generate_go_lines(expr.args[0], lines, indent)
                return f"parser.matchTerminal({arg})"
            elif expr.func.name == "match_literal" and len(expr.args) == 1:
                arg = generate_go_lines(expr.args[0], lines, indent)
                return f"parser.matchLiteral({arg})"
            elif expr.func.name == "consume_literal" and len(expr.args) == 1:
                arg = generate_go_lines(expr.args[0], lines, indent)
                lines.append(f"{indent}parser.consumeLiteral({arg})")
                return "nil"

        # Regular call
        f = generate_go_lines(expr.func, lines, indent)

        args = []
        for arg in expr.args:
            args.append(generate_go_lines(arg, lines, indent))
        args_code = ', '.join(args)
        tmp = gensym()
        lines.append(f"{indent}{tmp} := {f}({args_code})")
        return tmp

    elif isinstance(expr, Lambda):
        params = [escape_identifier(p.name) for p in expr.params]
        f = gensym()
        param_list = ', '.join(f"{p} interface{{}}" for p in params)
        ret_type = generate_go_type(expr.return_type) if expr.return_type else "interface{}"
        lines.append(f"{indent}{f} := func({param_list}) {ret_type} {{")
        v = generate_go_lines(expr.body, lines, indent + "\t")
        lines.append(f"{indent}\treturn {v}")
        lines.append(f"{indent}}}")
        return f

    elif isinstance(expr, Let):
        var_name = escape_identifier(expr.var.name)
        tmp1 = generate_go_lines(expr.init, lines, indent)
        lines.append(f"{indent}{var_name} := {tmp1}")
        tmp2 = generate_go_lines(expr.body, lines, indent)
        return tmp2

    elif isinstance(expr, IfElse):
        cond_code = generate_go_lines(expr.condition, lines, indent)
        if expr.then_branch == Lit(True):
            else_code = generate_go_lines(expr.else_branch, lines, indent + "\t")
            return f"({cond_code} || {else_code})"
        if expr.else_branch == Lit(False):
            then_code = generate_go_lines(expr.then_branch, lines, indent + "\t")
            return f"({cond_code} && {then_code})"

        tmp = gensym()
        lines.append(f"{indent}var {tmp} interface{{}}")
        lines.append(f"{indent}if {cond_code} {{")
        then_code = generate_go_lines(expr.then_branch, lines, indent + "\t")
        lines.append(f"{indent}\t{tmp} = {then_code}")
        lines.append(f"{indent}}} else {{")
        else_code = generate_go_lines(expr.else_branch, lines, indent + "\t")
        lines.append(f"{indent}\t{tmp} = {else_code}")
        lines.append(f"{indent}}}")
        return tmp

    elif isinstance(expr, Seq):
        tmp = "nil"
        for e in expr.exprs:
            tmp = generate_go_lines(e, lines, indent)
        return tmp

    elif isinstance(expr, While):
        m = len(lines)
        cond_code = generate_go_lines(expr.condition, lines, indent)
        non_trivial_cond = len(lines) > m
        cond_code_is_lvalue = cond_code.isidentifier()
        lines.append(f"{indent}for {cond_code} {{")
        n = len(lines)
        body_code = generate_go_lines(expr.body, lines, indent + "\t")
        if len(lines) == n:
            lines.append(f"{indent}\t// empty body")
        # Update the condition variable
        if non_trivial_cond and cond_code_is_lvalue:
            cond_code2 = generate_go_lines(expr.condition, lines, indent + "\t")
            lines.append(f"{indent}\t{cond_code} = {cond_code2}")
        lines.append(f"{indent}}}")
        return "nil"

    elif isinstance(expr, Assign):
        var_name = escape_identifier(expr.var.name)
        expr_code = generate_go_lines(expr.expr, lines, indent)
        lines.append(f"{indent}{var_name} = {expr_code}")
        return "nil"

    elif isinstance(expr, Return):
        expr_code = generate_go_lines(expr.expr, lines, indent)
        lines.append(f"{indent}return {expr_code}")
        return "nil"

    else:
        raise ValueError(f"Unknown action expression type: {type(expr)}")


def generate_go_def(expr: Union[FunDef, ParseNonterminalDef], indent: str = "") -> str:
    """Generate Go function definition."""
    if isinstance(expr, FunDef):
        func_name = escape_identifier(expr.name)

        params = []
        for param in expr.params:
            escaped_name = escape_identifier(param.name)
            go_type = generate_go_type(param.type)
            params.append(f"{escaped_name} {go_type}")

        params_str = ', '.join(params)

        ret_type = generate_go_type(expr.return_type) if expr.return_type else "interface{}"

        if expr.body is None:
            body_code = f"{indent}\t// no body"
        else:
            lines = []
            body_inner = generate_go_lines(expr.body, lines, indent + "\t")
            lines.append(f"{indent}\treturn {body_inner}")
            body_code = "\n".join(lines)

        return f"{indent}func {func_name}({params_str}) {ret_type} {{\n{body_code}\n{indent}}}"

    elif isinstance(expr, ParseNonterminalDef):
        func_name = f"parse{expr.nonterminal.name.title().replace('_', '')}"

        params = ["parser *Parser"]
        for param in expr.params:
            escaped_name = escape_identifier(param.name)
            go_type = generate_go_type(param.type)
            params.append(f"{escaped_name} {go_type}")

        params_str = ', '.join(params)

        ret_type = generate_go_type(expr.return_type) if expr.return_type else "interface{}"

        if expr.body is None:
            body_code = f"{indent}\t// no body"
        else:
            lines = []
            body_inner = generate_go_lines(expr.body, lines, indent + "\t")
            lines.append(f"{indent}\treturn {body_inner}")
            body_code = "\n".join(lines)

        return f"{indent}func {func_name}({params_str}) {ret_type} {{\n{body_code}\n{indent}}}"


def generate_go(expr: TargetExpr, indent: str = "") -> str:
    """Generate Go code for a single expression (inline style)."""
    if isinstance(expr, Var):
        return escape_identifier(expr.name)
    elif isinstance(expr, Lit):
        if expr.value is None:
            return "nil"
        elif isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        elif isinstance(expr.value, str):
            return f'"{expr.value}"'
        return repr(expr.value)
    elif isinstance(expr, Symbol):
        return f'"{expr.name}"'
    elif isinstance(expr, Call):
        func_code = generate_go(expr.func, indent)
        args_code = ', '.join(generate_go(arg, indent) for arg in expr.args)
        return f"{func_code}({args_code})"
    elif isinstance(expr, Lambda):
        params = [escape_identifier(p.name) for p in expr.params]
        param_list = ', '.join(f"{p} interface{{}}" for p in params)
        body_code = generate_go(expr.body, indent)
        ret_type = generate_go_type(expr.return_type) if expr.return_type else "interface{}"
        return f"func({param_list}) {ret_type} {{ return {body_code} }}"
    elif isinstance(expr, Let):
        lines = []
        result = generate_go_lines(expr, lines, indent)
        if lines:
            return '\n'.join(lines) + '\n' + result
        return result
    else:
        lines = []
        result = generate_go_lines(expr, lines, indent)
        if lines:
            return '\n'.join(lines) + '\n' + result
        return result


def generate_go_function_body(expr: TargetExpr, indent: str = "\t") -> str:
    """Generate Go code for a function body with proper indentation."""
    return generate_go(expr, indent)


__all__ = [
    'escape_identifier',
    'generate_go',
    'generate_go_lines',
    'generate_go_def',
    'generate_go_function_body',
    'GO_KEYWORDS',
]
