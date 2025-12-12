"""Code generation for Go from semantic action AST.

This module generates Go code from semantic action expressions,
with proper keyword escaping and idiomatic Go style.
"""

from typing import List, Optional, Set, Tuple, Union

from .codegen_base import CodeGenerator, BuiltinResult
from .target import (
    TargetExpr, Var, Lit, Symbol, Call, Lambda, Let, IfElse,
    FunDef, ParseNonterminalDef, gensym
)


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


class GoCodeGenerator(CodeGenerator):
    """Go code generator."""

    keywords = GO_KEYWORDS
    indent_str = "\t"

    base_type_map = {
        'Int64': 'int64',
        'Float64': 'float64',
        'String': 'string',
        'Boolean': 'bool',
    }

    def __init__(self):
        self.builtin_registry = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register builtin generators."""
        self.register_builtin("some", 1,
            lambda args, lines, indent: BuiltinResult(args[0], []))
        self.register_builtin("not", 1,
            lambda args, lines, indent: BuiltinResult(f"!{args[0]}", []))
        self.register_builtin("equal", 2,
            lambda args, lines, indent: BuiltinResult(f"{args[0]} == {args[1]}", []))
        self.register_builtin("not_equal", 2,
            lambda args, lines, indent: BuiltinResult(f"{args[0]} != {args[1]}", []))

        self.register_builtin("fragment_id_from_string", 1,
            lambda args, lines, indent: BuiltinResult(f"&proto.FragmentId{{Id: []byte({args[0]})}}", []))

        def gen_relation_id_from_string(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            tmp = gensym()
            return BuiltinResult(tmp, [
                f"h := sha256.Sum256([]byte({args[0]}))",
                f"{tmp} := &proto.RelationId{{Id: binary.BigEndian.Uint64(h[:8])}}"
            ])
        self.register_builtin("relation_id_from_string", 1, gen_relation_id_from_string)

        self.register_builtin("relation_id_from_int", 1,
            lambda args, lines, indent: BuiltinResult(f"&proto.RelationId{{Id: uint64({args[0]})}}", []))

        self.register_builtin("list_concat", 2,
            lambda args, lines, indent: BuiltinResult(f"append({args[0]}, {args[1]}...)", []))

        self.register_builtin("list_append", 2,
            lambda args, lines, indent: BuiltinResult(f"append({args[0]}, {args[1]})", []))

        self.register_builtin("list_push!", 2,
            lambda args, lines, indent: BuiltinResult("nil", [f"{args[0]} = append({args[0]}, {args[1]})"]))

        def gen_make_list(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            if len(args) == 0:
                return BuiltinResult("[]interface{}{}", [])
            return BuiltinResult(f"[]interface{{{{}}}}{{{', '.join(args)}}}", [])
        self.register_builtin("make_list", -1, gen_make_list)

        self.register_builtin("is_none", 1,
            lambda args, lines, indent: BuiltinResult(f"{args[0]} == nil", []))

        self.register_builtin("fst", 1,
            lambda args, lines, indent: BuiltinResult(f"{args[0]}.F0", []))

        self.register_builtin("snd", 1,
            lambda args, lines, indent: BuiltinResult(f"{args[0]}.F1", []))

        def gen_make_tuple(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            fields = ', '.join(f"F{i}: {a}" for i, a in enumerate(args))
            return BuiltinResult(f"struct{{{fields}}}", [])
        self.register_builtin("make_tuple", -1, gen_make_tuple)

        self.register_builtin("length", 1,
            lambda args, lines, indent: BuiltinResult(f"len({args[0]})", []))

        def gen_unwrap_option_or(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            tmp = gensym()
            return BuiltinResult(tmp, [
                f"var {tmp} = {args[1]}",
                f"if {args[0]} != nil {{",
                f"\t{tmp} = *{args[0]}",
                "}"
            ])
        self.register_builtin("unwrap_option_or", 2, gen_unwrap_option_or)

        self.register_builtin("match_lookahead_terminal", 2,
            lambda args, lines, indent: BuiltinResult(f"parser.matchLookaheadTerminal({args[0]}, {args[1]})", []))

        self.register_builtin("match_lookahead_literal", 2,
            lambda args, lines, indent: BuiltinResult(f"parser.matchLookaheadLiteral({args[0]}, {args[1]})", []))

        self.register_builtin("match_terminal", 1,
            lambda args, lines, indent: BuiltinResult(f"parser.matchTerminal({args[0]})", []))

        self.register_builtin("match_literal", 1,
            lambda args, lines, indent: BuiltinResult(f"parser.matchLiteral({args[0]})", []))

        self.register_builtin("consume_literal", 1,
            lambda args, lines, indent: BuiltinResult("nil", [f"parser.consumeLiteral({args[0]})"]))

        self.register_builtin("consume_terminal", 1,
            lambda args, lines, indent: BuiltinResult("nil", [f"parser.consumeTerminal({args[0]})"]))

        self.register_builtin("current_token", 0,
            lambda args, lines, indent: BuiltinResult("parser.currentToken()", []))

        def gen_error(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            if len(args) == 2:
                return BuiltinResult("nil", [f'panic(fmt.Sprintf("%s: %v", {args[0]}, {args[1]}))'])
            elif len(args) == 1:
                return BuiltinResult("nil", [f"panic({args[0]})"])
            return None
        self.register_builtin("error", -1, gen_error)

    def escape_keyword(self, name: str) -> str:
        return f"{name}_"

    # --- Literal generation ---

    def gen_none(self) -> str:
        return "nil"

    def gen_bool(self, value: bool) -> str:
        return "true" if value else "false"

    def gen_string(self, value: str) -> str:
        return f'"{value}"'

    # --- Symbol and constructor generation ---

    def gen_symbol(self, name: str) -> str:
        return f'"{name}"'

    def gen_constructor(self, name: str) -> str:
        return f"proto.{name}"

    def gen_builtin_ref(self, name: str) -> str:
        return f"parser.{name}"

    def gen_parse_nonterminal_ref(self, name: str) -> str:
        return f"parse{name.title().replace('_', '')}"

    # --- Type generation ---

    def gen_message_type(self, name: str) -> str:
        return f"*proto.{name}"

    def gen_tuple_type(self, element_types: List[str]) -> str:
        if not element_types:
            return 'struct{}'
        fields = [f"F{i} {t}" for i, t in enumerate(element_types)]
        return f"struct{{ {'; '.join(fields)} }}"

    def gen_list_type(self, element_type: str) -> str:
        return f"[]{element_type}"

    def gen_option_type(self, element_type: str) -> str:
        return f"*{element_type}"  # Go uses pointers for optional values

    def gen_function_type(self, param_types: List[str], return_type: str) -> str:
        return f"func({', '.join(param_types)}) {return_type}"

    # --- Control flow syntax ---

    def gen_if_start(self, cond: str) -> str:
        return f"if {cond} {{"

    def gen_else(self) -> str:
        return "} else {"

    def gen_if_end(self) -> str:
        return "}"

    def gen_while_start(self, cond: str) -> str:
        return f"for {cond} {{"

    def gen_while_end(self) -> str:
        return "}"

    def gen_empty_body(self) -> str:
        return "// empty body"

    def gen_assignment(self, var: str, value: str, is_declaration: bool = False) -> str:
        if is_declaration:
            return f"{var} := {value}"
        return f"{var} = {value}"

    def gen_return(self, value: str) -> str:
        return f"return {value}"

    def gen_var_declaration(self, var: str, type_hint: Optional[str] = None) -> str:
        return f"var {var} interface{{}}"

    # --- Lambda and function definition syntax ---

    def gen_lambda_start(self, params: List[str], return_type: Optional[str]) -> Tuple[str, str]:
        param_list = ', '.join(f"{p} interface{{}}" for p in params)
        ret_type = return_type if return_type else "interface{}"
        return (f"__FUNC__ := func({param_list}) {ret_type} {{", "}")

    def gen_func_def_header(self, name: str, params: List[Tuple[str, str]],
                            return_type: Optional[str], is_method: bool = False) -> str:
        params_str = ', '.join(f"{n} {t}" for n, t in params)
        ret_type = return_type if return_type else "interface{}"
        return f"func {name}({params_str}) {ret_type} {{"

    def gen_func_def_end(self) -> str:
        return "}"

    def _generate_if_else(self, expr: IfElse, lines: List[str], indent: str) -> str:
        """Override for Go-specific if-else syntax."""
        cond_code = self.generate_lines(expr.condition, lines, indent)

        # Optimization: short-circuit for boolean literals
        if expr.then_branch == Lit(True):
            else_code = self.generate_lines(expr.else_branch, lines, indent + self.indent_str)
            return f"({cond_code} || {else_code})"
        if expr.else_branch == Lit(False):
            then_code = self.generate_lines(expr.then_branch, lines, indent + self.indent_str)
            return f"({cond_code} && {then_code})"

        tmp = gensym()
        lines.append(f"{indent}{self.gen_var_declaration(tmp)}")
        lines.append(f"{indent}{self.gen_if_start(cond_code)}")

        body_indent = indent + self.indent_str
        then_code = self.generate_lines(expr.then_branch, lines, body_indent)
        lines.append(f"{body_indent}{self.gen_assignment(tmp, then_code)}")

        lines.append(f"{indent}{self.gen_else()}")
        else_code = self.generate_lines(expr.else_branch, lines, body_indent)
        lines.append(f"{body_indent}{self.gen_assignment(tmp, else_code)}")

        lines.append(f"{indent}{self.gen_if_end()}")

        return tmp

    def _generate_parse_def(self, expr: ParseNonterminalDef, indent: str) -> str:
        """Generate a parse method definition."""
        func_name = f"parse{expr.nonterminal.name.title().replace('_', '')}"

        params = [("parser", "*Parser")]
        for param in expr.params:
            escaped_name = self.escape_identifier(param.name)
            go_type = self.gen_type(param.type)
            params.append((escaped_name, go_type))

        params_str = ', '.join(f"{n} {t}" for n, t in params)

        ret_type = self.gen_type(expr.return_type) if expr.return_type else "interface{}"

        if expr.body is None:
            body_code = f"{indent}\t// no body"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(expr.body, body_lines, indent + "\t")
            body_lines.append(f"{indent}\treturn {body_inner}")
            body_code = "\n".join(body_lines)

        return f"{indent}func {func_name}({params_str}) {ret_type} {{\n{body_code}\n{indent}}}"


# Module-level instance for convenience
_generator = GoCodeGenerator()


def escape_identifier(name: str) -> str:
    """Escape a Go identifier if it's a keyword or predeclared."""
    return _generator.escape_identifier(name)


def generate_go_type(typ) -> str:
    """Generate Go type from a Type expression."""
    return _generator.gen_type(typ)


def generate_go_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> str:
    """Generate Go code from a target IR expression."""
    return _generator.generate_lines(expr, lines, indent)


def generate_go_def(expr: Union[FunDef, ParseNonterminalDef], indent: str = "") -> str:
    """Generate Go function definition."""
    return _generator.generate_def(expr, indent)


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
        ret_type = _generator.gen_type(expr.return_type) if expr.return_type else "interface{}"
        return f"func({param_list}) {ret_type} {{ return {body_code} }}"
    elif isinstance(expr, Let):
        lines: List[str] = []
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
    'generate_go_type',
    'generate_go_function_body',
    'GO_KEYWORDS',
    'GoCodeGenerator',
]
