"""Code generation for Python from semantic action AST.

This module generates Python code from semantic action expressions,
with proper keyword escaping and idiomatic Python style.
"""

from typing import List, Optional, Set, Tuple, Union

from .codegen_base import CodeGenerator, BuiltinResult
from .target import (
    TargetExpr, Var, Lit, Symbol, NewMessage, OneOf, ListExpr, Call, Lambda, Let,
    IfElse, FunDef, VisitNonterminalDef
)
from .gensym import gensym


# Python keywords that need escaping
PYTHON_KEYWORDS: Set[str] = {
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
    'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
    'try', 'while', 'with', 'yield',
}


def _format_parse_error_with_token(message_expr: str, token_expr: str) -> str:
    """Format a ParseError raise statement with token information."""
    return f'raise ParseError(f"{{{message_expr}}}: {{{token_expr}.type}}=`{{{token_expr}.value}}`")'


class PythonCodeGenerator(CodeGenerator):
    """Python code generator."""

    keywords = PYTHON_KEYWORDS
    indent_str = "    "

    base_type_map = {
        'Int32': 'int',
        'Int64': 'int',
        'Float64': 'float',
        'String': 'str',
        'Boolean': 'bool',
        'Bytes': 'bytes',
    }

    def __init__(self, proto_messages=None):
        super().__init__()
        self.proto_messages = proto_messages or {}
        self._message_field_map: dict | None = None
        self._register_builtins()

    def _build_message_field_map(self):
        """Build field mapping from proto message definitions.

        Returns dict mapping (module, message_name) to list of (field_name, is_repeated).
        """
        if self._message_field_map is not None:
            return self._message_field_map

        field_map = {}
        for (module, msg_name), proto_msg in self.proto_messages.items():
            # Collect all oneof field names
            oneof_field_names = set()
            for oneof in proto_msg.oneofs:
                oneof_field_names.update(f.name for f in oneof.fields)

            # Only include messages with regular (non-oneof) fields
            regular_fields = [(f.name, f.is_repeated) for f in proto_msg.fields if f.name not in oneof_field_names]
            if regular_fields:
                # Preserve original proto field name; handle keyword fields at call sites via **{...}.
                field_map[(module, msg_name)] = list(regular_fields)

        self._message_field_map = field_map
        return field_map

    def _register_builtins(self) -> None:
        """Register builtin generators.

        Arity is looked up from target_builtins.BUILTIN_REGISTRY.
        """
        self.register_builtin("some",
            lambda args, lines, indent: BuiltinResult(args[0], []))
        self.register_builtin("not",
            lambda args, lines, indent: BuiltinResult(f"not {args[0]}", []))
        self.register_builtin("and",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} and {args[1]})", []))
        self.register_builtin("or",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} or {args[1]})", []))
        self.register_builtin("equal",
            lambda args, lines, indent: BuiltinResult(f"{args[0]} == {args[1]}", []))
        self.register_builtin("not_equal",
            lambda args, lines, indent: BuiltinResult(f"{args[0]} != {args[1]}", []))
        self.register_builtin("add",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} + {args[1]})", []))

        self.register_builtin("fragment_id_from_string",
            lambda args, lines, indent: BuiltinResult(f"fragments_pb2.FragmentId(id={args[0]}.encode())", []))

        self.register_builtin("relation_id_from_string",
            lambda args, lines, indent: BuiltinResult(f"self.relation_id_from_string({args[0]})", []))

        self.register_builtin("relation_id_from_int",
            lambda args, lines, indent: BuiltinResult(f"logic_pb2.RelationId(id_low={args[0]} & 0xFFFFFFFFFFFFFFFF, id_high=({args[0]} >> 64) & 0xFFFFFFFFFFFFFFFF)", []))

        self.register_builtin("list_concat",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} + ({args[1]} if {args[1]} is not None else []))", []))

        self.register_builtin("map",
            lambda args, lines, indent: BuiltinResult(f"[{args[0]}(x) for x in {args[1]}]", []))

        self.register_builtin("is_none",
            lambda args, lines, indent: BuiltinResult(f"{args[0]} is None", []))

        self.register_builtin("is_some",
            lambda args, lines, indent: BuiltinResult(f"{args[0]} is not None", []))

        self.register_builtin("unwrap_option",
            lambda args, lines, indent: BuiltinResult(args[0], []))

        self.register_builtin("none",
            lambda args, lines, indent: BuiltinResult("None", []))

        self.register_builtin("make_empty_bytes",
            lambda args, lines, indent: BuiltinResult("b''", []))

        self.register_builtin("dict_from_list",
            lambda args, lines, indent: BuiltinResult(f"dict({args[0]})", []))

        self.register_builtin("dict_get",
            lambda args, lines, indent: BuiltinResult(f"{args[0]}.get({args[1]})", []))

        self.register_builtin("has_proto_field",
            lambda args, lines, indent: BuiltinResult(f"{args[0]}.HasField({args[1]})", []))

        self.register_builtin("string_to_upper",
            lambda args, lines, indent: BuiltinResult(f"{args[0]}.upper()", []))

        self.register_builtin("string_in_list",
            lambda args, lines, indent: BuiltinResult(f"{args[0]} in {args[1]}", []))

        self.register_builtin("string_concat",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} + {args[1]})", []))

        self.register_builtin("encode_string",
            lambda args, lines, indent: BuiltinResult(f"{args[0]}.encode()", []))

        self.register_builtin("tuple",
            lambda args, lines, indent: BuiltinResult(f"({', '.join(args)},)", []))

        self.register_builtin("length",
            lambda args, lines, indent: BuiltinResult(f"len({args[0]})", []))

        self.register_builtin("unwrap_option_or",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} if {args[0]} is not None else {args[1]})", []))

        self.register_builtin("int64_to_int32",
            lambda args, lines, indent: BuiltinResult(f"int({args[0]})", []))

        self.register_builtin("match_lookahead_terminal",
            lambda args, lines, indent: BuiltinResult(f"self.match_lookahead_terminal({args[0]}, {args[1]})", []))

        self.register_builtin("match_lookahead_literal",
            lambda args, lines, indent: BuiltinResult(f"self.match_lookahead_literal({args[0]}, {args[1]})", []))

        self.register_builtin("consume_literal",
            lambda args, lines, indent: BuiltinResult("None", [f"self.consume_literal({args[0]})"]))

        self.register_builtin("consume_terminal",
            lambda args, lines, indent: BuiltinResult(f"self.consume_terminal({args[0]})", []))

        self.register_builtin("current_token",
            lambda args, lines, indent: BuiltinResult("self.lookahead(0)", []))

        # error builtins do not return
        self.register_builtin("error",
            lambda args, lines, indent: BuiltinResult(None, [f"raise ParseError({args[0]})"]))

        self.register_builtin("error_with_token",
            lambda args, lines, indent: BuiltinResult(None, [_format_parse_error_with_token(args[0], args[1])]))

        self.register_builtin("start_fragment",
            lambda args, lines, indent: BuiltinResult(args[0], [f"self.start_fragment({args[0]})"]))

        self.register_builtin("construct_fragment",
            lambda args, lines, indent: BuiltinResult(f"self.construct_fragment({args[0]}, {args[1]})", []))

        self.register_builtin("export_csv_config",
            lambda args, lines, indent: BuiltinResult(f"self.export_csv_config({args[0]}, {args[1]}, {args[2]})", []))

    def escape_keyword(self, name: str) -> str:
        return f"{name}_"

    # --- Literal generation ---

    def gen_none(self) -> str:
        return "None"

    def gen_bool(self, value: bool) -> str:
        return "True" if value else "False"

    def gen_string(self, value: str) -> str:
        return repr(value)

    # --- Symbol and constructor generation ---

    def gen_symbol(self, name: str) -> str:
        return f'"{name}"'

    def gen_constructor(self, module: str, name: str) -> str:
        return f"{module}_pb2.{name}"

    def gen_builtin_ref(self, name: str) -> str:
        return f"self.{name}"

    def gen_named_fun_ref(self, name: str) -> str:
        return f"Parser.{name}"

    def gen_parse_nonterminal_ref(self, name: str) -> str:
        return f"self.parse_{name}"

    # --- Type generation ---

    def gen_message_type(self, module: str, name: str) -> str:
        return f"{module}_pb2.{name}"

    def gen_tuple_type(self, element_types: List[str]) -> str:
        if not element_types:
            return 'tuple[()]'
        return f"tuple[{', '.join(element_types)}]"

    def gen_list_type(self, element_type: str) -> str:
        return f"list[{element_type}]"

    def gen_option_type(self, element_type: str) -> str:
        return f"Optional[{element_type}]"

    def gen_dict_type(self, key_type: str, value_type: str) -> str:
        return f"dict[{key_type}, {value_type}]"

    def gen_list_literal(self, elements: List[str], element_type) -> str:
        return f"[{', '.join(elements)}]"

    def gen_function_type(self, param_types: List[str], return_type: str) -> str:
        return f"Callable[[{', '.join(param_types)}], {return_type}]"

    # --- Control flow syntax ---

    def gen_if_start(self, cond: str) -> str:
        return f"if {cond}:"

    def gen_else(self) -> str:
        return "else:"

    def gen_if_end(self) -> str:
        return ""  # Python uses indentation, no end marker

    def gen_while_start(self, cond: str) -> str:
        return f"while {cond}:"

    def gen_while_end(self) -> str:
        return ""  # Python uses indentation

    def gen_empty_body(self) -> str:
        return "pass"

    def gen_assignment(self, var: str, value: str, is_declaration: bool = False) -> str:
        return f"{var} = {value}"

    def gen_return(self, value: str) -> str:
        return f"return {value}"

    def gen_var_declaration(self, var: str, type_hint: Optional[str] = None) -> str:
        # Python doesn't need declaration, but we can use a placeholder
        return ""

    # --- Lambda and function definition syntax ---

    def gen_lambda_start(self, params: List[str], return_type: Optional[str]) -> Tuple[str, str]:
        params_str = ', '.join(params) if params else ''
        return (f"def __FUNC__({params_str}):", "")

    def gen_func_def_header(self, name: str, params: List[Tuple[str, str]],
                            return_type: Optional[str], is_method: bool = False) -> str:
        params_str = ', '.join(f"{n}: {t}" for n, t in params)
        ret_hint = f" -> {return_type}" if return_type else ""
        return f"def {name}({params_str}){ret_hint}:"

    def gen_func_def_end(self) -> str:
        return ""  # Python uses indentation

    # --- Override generate_lines for Python-specific special cases ---

    def generate_lines(self, expr: TargetExpr, lines: List[str], indent: str = "") -> Optional[str]:
        # Handle NewMessage with fields (which may contain OneOf calls)
        if isinstance(expr, NewMessage):
            return self._generate_newmessage(expr, lines, indent)

        return super().generate_lines(expr, lines, indent)

    def _generate_newmessage(self, expr: NewMessage, lines: List[str], indent: str) -> str:
        """Override to handle NewMessage with fields containing OneOf calls."""
        if not expr.fields:
            # No fields - return constructor directly
            ctor = self.gen_constructor(expr.module, expr.name)
            return f"{ctor}()"

        # NewMessage with fields - need to handle OneOf specially
        ctor = self.gen_constructor(expr.module, expr.name)
        keyword_args = []
        keyword_field_assignments: List[Tuple[str, str, bool]] = []

        # Get field info from proto message definitions
        field_map = self._build_message_field_map()
        message_fields = field_map.get((expr.module, expr.name), [])
        field_is_repeated = {name: is_rep for name, is_rep in message_fields}

        for field_name, field_expr in expr.fields:
            # Check if this field is a Call(OneOf, [value])
            if isinstance(field_expr, Call) and isinstance(field_expr.func, OneOf) and len(field_expr.args) == 1:
                # OneOf field
                oneof_field_name = field_expr.func.field_name
                field_value = self.generate_lines(field_expr.args[0], lines, indent)
                assert field_value is not None
                is_repeated = field_is_repeated.get(oneof_field_name, False)
                if oneof_field_name in PYTHON_KEYWORDS:
                    keyword_field_assignments.append((oneof_field_name, field_value, is_repeated))
                else:
                    keyword_args.append(f"{oneof_field_name}={field_value}")
            else:
                # Regular field
                field_value = self.generate_lines(field_expr, lines, indent)
                assert field_value is not None
                is_repeated = field_is_repeated.get(field_name, False)
                if field_name in PYTHON_KEYWORDS:
                    keyword_field_assignments.append((field_name, field_value, is_repeated))
                else:
                    keyword_args.append(f"{field_name}={field_value}")

        args_code = ', '.join(keyword_args)
        tmp = gensym()
        lines.append(f"{indent}{self.gen_assignment(tmp, f'{ctor}({args_code})', is_declaration=True)}")

        # Handle keyword field assignments via getattr()
        for field_name, field_value, is_repeated in keyword_field_assignments:
            if is_repeated:
                lines.append(f"{indent}getattr({tmp}, '{field_name}').extend({field_value})")
            else:
                lines.append(f"{indent}getattr({tmp}, '{field_name}').CopyFrom({field_value})")

        return tmp


    def _generate_if_else(self, expr: IfElse, lines: List[str], indent: str) -> Optional[str]:
        """Override to skip var declaration (Python doesn't need it)."""
        cond_code = self.generate_lines(expr.condition, lines, indent)
        assert cond_code is not None, "If condition should not contain a return"

        # Optimization: short-circuit for boolean literals.
        # This is not needed, but makes the generated code more readable.
        if expr.then_branch == Lit(True):
            tmp_lines: List[str] = []
            else_code = self.generate_lines(expr.else_branch, tmp_lines, indent)
            if not tmp_lines and else_code is not None:
                return f"({cond_code} or {else_code})"
        if expr.else_branch == Lit(False):
            tmp_lines = []
            then_code = self.generate_lines(expr.then_branch, tmp_lines, indent)
            if not tmp_lines and then_code is not None:
                return f"({cond_code} and {then_code})"

        tmp = gensym()
        lines.append(f"{indent}{self.gen_if_start(cond_code)}")

        body_indent = indent + self.indent_str
        then_code = self.generate_lines(expr.then_branch, lines, body_indent)
        # Only assign if the branch didn't already return
        if then_code is not None:
            lines.append(f"{body_indent}{self.gen_assignment(tmp, then_code)}")

        lines.append(f"{indent}{self.gen_else()}")
        else_code = self.generate_lines(expr.else_branch, lines, body_indent)
        # Only assign if the branch didn't already return
        if else_code is not None:
            lines.append(f"{body_indent}{self.gen_assignment(tmp, else_code)}")

        # If both branches returned, propagate None
        if then_code is None and else_code is None:
            return None

        return tmp

    def _generate_parse_def(self, expr: VisitNonterminalDef, indent: str) -> str:
        """Generate a parse method definition."""
        func_name = f"parse_{expr.nonterminal.name}"

        params = []
        for param in expr.params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            params.append(f"{escaped_name}: {type_hint}")

        params_str = ', '.join(params) if params else ''
        if params_str:
            params_str = ', ' + params_str

        ret_hint = f" -> {self.gen_type(expr.return_type)}" if expr.return_type else ""

        body_lines: List[str] = []
        body_inner = self.generate_lines(expr.body, body_lines, indent + "    ")
        # Only add return if the body didn't already return
        if body_inner is not None:
            body_lines.append(f"{indent}    return {body_inner}")
        body_code = "\n".join(body_lines)

        return f"{indent}def {func_name}(self{params_str}){ret_hint}:\n{body_code}"

    def _generate_builtin_method_def(self, expr: FunDef, indent: str) -> str:
        """Generate a builtin method definition as a static method."""
        func_name = self.escape_identifier(expr.name)

        params = []
        for param in expr.params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            params.append(f"{escaped_name}: {type_hint}")

        params_str = ', '.join(params) if params else ''

        ret_hint = f" -> {self.gen_type(expr.return_type)}" if expr.return_type else ""

        if expr.body is None:
            body_code = f"{indent}    pass"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(expr.body, body_lines, indent + "    ")
            # Only add return if the body didn't already return
            if body_inner is not None:
                body_lines.append(f"{indent}    return {body_inner}")
            body_code = "\n".join(body_lines)

        return f"{indent}@staticmethod\n{indent}def {func_name}({params_str}){ret_hint}:\n{body_code}"


def escape_identifier(name: str) -> str:
    """Escape a Python identifier if it's a keyword."""
    if name in PYTHON_KEYWORDS:
        return f"{name}_"
    return name


def generate_python_type(typ, generator: Optional[PythonCodeGenerator] = None) -> str:
    """Generate Python type hint from a Type expression."""
    if generator is None:
        generator = PythonCodeGenerator()
    return generator.gen_type(typ)


def generate_python_lines(
    expr: TargetExpr,
    lines: List[str],
    indent: str = "",
    generator: Optional[PythonCodeGenerator] = None,
) -> Optional[str]:
    """Generate Python code from a target IR expression.

    Returns the value expression as a string, or None if the expression
    contains a Return statement.

    For Message construction with field mapping, pass a generator initialized
    with proto_messages.
    """
    if generator is None:
        generator = PythonCodeGenerator()
    return generator.generate_lines(expr, lines, indent)


def generate_python_def(
    expr: Union[FunDef, VisitNonterminalDef],
    indent: str = "",
    generator: Optional[PythonCodeGenerator] = None,
) -> str:
    """Generate Python function definition."""
    if generator is None:
        generator = PythonCodeGenerator()
    return generator.generate_def(expr, indent)


def generate_python(expr: TargetExpr, indent: str = "") -> str:
    """Generate Python code for a single expression (inline style)."""
    if isinstance(expr, Var):
        return escape_identifier(expr.name)
    elif isinstance(expr, Lit):
        return repr(expr.value)
    elif isinstance(expr, Symbol):
        return f'"{expr.name}"'
    elif isinstance(expr, ListExpr):
        if not expr.elements:
            return "[]"
        elements_code = ', '.join(generate_python(elem, indent) for elem in expr.elements)
        return f"[{elements_code}]"
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
        lines: List[str] = []
        result = generate_python_lines(expr, lines, indent)
        assert result is not None
        if lines:
            return '\n'.join(lines) + '\n' + result
        return result
    else:
        lines = []
        result = generate_python_lines(expr, lines, indent)
        assert result is not None
        if lines:
            return '\n'.join(lines) + '\n' + result
        return result


def generate_python_function_body(expr: TargetExpr, indent: str = "    ") -> str:
    """Generate Python code for a function body with proper indentation."""
    return generate_python(expr, indent)


__all__ = [
    'escape_identifier',
    'generate_python',
    'generate_python_lines',
    'generate_python_def',
    'generate_python_type',
    'generate_python_function_body',
    'PYTHON_KEYWORDS',
    'PythonCodeGenerator',
]
