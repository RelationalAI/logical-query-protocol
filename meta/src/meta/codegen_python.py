"""Code generation for Python from semantic action AST.

This module generates Python code from semantic action expressions,
with proper keyword escaping and idiomatic Python style.
"""

from .codegen_base import CodeGenerator
from .codegen_templates import PYTHON_TEMPLATES
from .gensym import gensym
from .target import (
    Call,
    FunDef,
    Lambda,
    Let,
    ListExpr,
    Lit,
    NewMessage,
    OneOf,
    ParseNonterminalDef,
    PrintNonterminalDef,
    Symbol,
    TargetExpr,
    Var,
)

# Python keywords that need escaping
PYTHON_KEYWORDS: set[str] = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
}


class PythonCodeGenerator(CodeGenerator):
    """Python code generator."""

    keywords = PYTHON_KEYWORDS
    indent_str = "    "
    named_fun_class = "self"

    base_type_map = {
        "Int32": "int",
        "Int64": "int",
        "Float64": "float",
        "String": "str",
        "Boolean": "bool",
        "Bytes": "bytes",
        "Void": "None",
        "Never": "NoReturn",
    }

    def __init__(self, proto_messages=None):
        super().__init__(proto_messages)
        self._message_field_map: dict | None = None
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register builtin generators from templates."""
        self.register_builtins_from_templates(PYTHON_TEMPLATES)
        # Override tuple to handle empty and single-element cases correctly
        self.register_builtin("tuple", self._gen_tuple_builtin)
        # Override unwrap_option to emit assert for type narrowing
        self.register_builtin("unwrap_option", self._gen_unwrap_option_builtin)

    @staticmethod
    def _gen_tuple_builtin(args, lines, indent):
        from .codegen_base import BuiltinResult

        if len(args) == 0:
            return BuiltinResult("()", [])
        elif len(args) == 1:
            return BuiltinResult(f"({args[0]},)", [])
        else:
            return BuiltinResult(f"({', '.join(args)},)", [])

    @staticmethod
    def _gen_unwrap_option_builtin(args, lines, indent):
        from .codegen_base import BuiltinResult

        return BuiltinResult(args[0], [f"assert {args[0]} is not None"])

    def escape_keyword(self, name: str) -> str:
        return f"{name}_"

    # --- Field access ---

    def gen_field_access(self, obj_code: str, field_name: str) -> str:
        if field_name in PYTHON_KEYWORDS:
            return f"getattr({obj_code}, {field_name!r})"
        return f"{obj_code}.{field_name}"

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
        return f"{self.named_fun_class}.{name}"

    def gen_parse_nonterminal_ref(self, name: str) -> str:
        return f"self.parse_{name}"

    def gen_pretty_nonterminal_ref(self, name: str) -> str:
        return f"self.pretty_{name}"

    # --- Type generation ---

    def gen_message_type(self, module: str, name: str) -> str:
        return f"{module}_pb2.{name}"

    def gen_enum_type(self, module: str, name: str) -> str:
        return f"{module}_pb2.{name}"

    def gen_enum_value(self, module: str, enum_name: str, value_name: str) -> str:
        return f"{module}_pb2.{enum_name}.{value_name}"

    def gen_tuple_type(self, element_types: list[str]) -> str:
        if not element_types:
            return "tuple[()]"
        return f"tuple[{', '.join(element_types)}]"

    def gen_sequence_type(self, element_type: str) -> str:
        return f"Sequence[{element_type}]"

    def gen_list_type(self, element_type: str) -> str:
        return f"list[{element_type}]"

    def gen_option_type(self, element_type: str) -> str:
        return f"Optional[{element_type}]"

    def gen_dict_type(self, key_type: str, value_type: str) -> str:
        return f"dict[{key_type}, {value_type}]"

    def gen_list_literal(self, elements: list[str], element_type) -> str:
        return f"[{', '.join(elements)}]"

    def gen_function_type(self, param_types: list[str], return_type: str) -> str:
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

    def gen_foreach_start(self, var: str, collection: str) -> str:
        return f"for {var} in {collection}:"

    def gen_foreach_enumerated_start(
        self, index_var: str, var: str, collection: str
    ) -> str:
        return f"for {index_var}, {var} in enumerate({collection}):"

    def gen_foreach_end(self) -> str:
        return ""  # Python uses indentation

    def gen_empty_body(self) -> str:
        return "pass"

    def gen_assignment(self, var: str, value: str, is_declaration: bool = False) -> str:
        return f"{var} = {value}"

    def gen_return(self, value: str) -> str:
        return f"return {value}"

    def gen_var_declaration(self, var: str, type_hint: str | None = None) -> str:
        # Python doesn't need declaration, but we can use a placeholder
        return ""

    # --- Lambda and function definition syntax ---

    def gen_lambda_start(
        self, params: list[tuple[str, str | None]], return_type: str | None
    ) -> tuple[str, str]:
        params_str = ", ".join(n for n, _ in params) if params else ""
        return (f"def __FUNC__({params_str}):", "")

    def gen_func_def_header(
        self,
        name: str,
        params: list[tuple[str, str]],
        return_type: str | None,
        is_method: bool = False,
    ) -> str:
        params_str = ", ".join(f"{n}: {t}" for n, t in params)
        ret_hint = f" -> {return_type}" if return_type else ""
        return f"def {name}({params_str}){ret_hint}:"

    def gen_func_def_end(self) -> str:
        return ""  # Python uses indentation

    # --- NewMessage generation for Python protobuf ---

    def _generate_NewMessage(
        self, expr: NewMessage, lines: list[str], indent: str
    ) -> str:
        """Generate Python code for NewMessage with keyword-safe field handling.

        Python protobuf constructors use keyword arguments, but field names
        that clash with Python keywords (e.g., 'import', 'from') can't be
        passed as kwargs. Those are deferred and set via getattr() after
        construction.
        """
        ctor = self.gen_constructor(expr.module, expr.name)

        if not expr.fields:
            tmp = gensym()
            lines.append(
                f"{indent}{self.gen_assignment(tmp, f'{ctor}()', is_declaration=True)}"
            )
            return tmp

        keyword_args = []
        deferred_fields: list[tuple[str, str]] = []

        for field_name, field_expr in expr.fields:
            is_oneof = (
                isinstance(field_expr, Call)
                and isinstance(field_expr.func, OneOf)
                and len(field_expr.args) == 1
            )
            if is_oneof:
                assert isinstance(field_expr, Call) and isinstance(
                    field_expr.func, OneOf
                )
                oneof_field_name = field_expr.func.field_name
                field_value = self.generate_lines(field_expr.args[0], lines, indent)
                assert field_value is not None
                if oneof_field_name in PYTHON_KEYWORDS:
                    deferred_fields.append((oneof_field_name, field_value))
                else:
                    keyword_args.append(f"{oneof_field_name}={field_value}")
            else:
                field_value = self.generate_lines(field_expr, lines, indent)
                assert field_value is not None
                if field_name in PYTHON_KEYWORDS:
                    deferred_fields.append((field_name, field_value))
                else:
                    keyword_args.append(f"{field_name}={field_value}")

        args_code = ", ".join(keyword_args)
        call = f"{ctor}({args_code})"
        tmp = gensym()
        lines.append(f"{indent}{self.gen_assignment(tmp, call, is_declaration=True)}")

        if deferred_fields:
            self._newmessage_deferred(tmp, expr, deferred_fields, lines, indent)

        return tmp

    def _newmessage_deferred(
        self,
        tmp: str,
        expr: NewMessage,
        deferred_fields: list[tuple[str, str]],
        lines: list[str],
        indent: str,
    ) -> None:
        """Set keyword-conflicting fields via getattr() post-construction."""
        field_map = self._build_message_field_map()
        message_fields = field_map.get((expr.module, expr.name), [])
        field_is_repeated = {name: is_rep for name, is_rep in message_fields}

        for field_name, field_value in deferred_fields:
            if field_is_repeated.get(field_name, False):
                lines.append(
                    f"{indent}getattr({tmp}, '{field_name}').extend({field_value})"
                )
            else:
                lines.append(
                    f"{indent}getattr({tmp}, '{field_name}').CopyFrom({field_value})"
                )

    def _build_message_field_map(self) -> dict:
        """Build field mapping from proto message definitions.

        Returns dict mapping (module, message_name) to list of (field_name, is_repeated).
        Caches the result for subsequent calls.
        """
        if self._message_field_map is not None:
            return self._message_field_map

        field_map = {}
        for (module, msg_name), proto_msg in self.proto_messages.items():
            oneof_field_names = set()
            for oneof in proto_msg.oneofs:
                oneof_field_names.update(f.name for f in oneof.fields)

            regular_fields = [
                (f.name, f.is_repeated)
                for f in proto_msg.fields
                if f.name not in oneof_field_names
            ]
            if regular_fields:
                field_map[(module, msg_name)] = regular_fields

        self._message_field_map = field_map
        return field_map

    def _generate_self_method(
        self, func_name: str, params, body, return_type, indent: str
    ) -> str:
        """Generate a method definition with `self` as first parameter.

        Args:
            func_name: The method name.
            params: List of Param objects (each with .name and .type).
            body: The method body expression, or None for an empty body.
            return_type: The return type, or None.
            indent: Indentation prefix.
        """
        typed_params = []
        for param in params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            typed_params.append(f"{escaped_name}: {type_hint}")

        params_str = ", ".join(typed_params) if typed_params else ""
        if params_str:
            params_str = ", " + params_str

        is_void = return_type is not None and self._is_void_type(return_type)
        ret_hint = (
            "" if not return_type or is_void else f" -> {self.gen_type(return_type)}"
        )

        body_lines: list[str] = []
        if body is None:
            body_lines.append(f"{indent}    pass")
        else:
            body_inner = self.generate_lines(body, body_lines, indent + "    ")
            if body_inner is not None and not is_void:
                body_lines.append(f"{indent}    return {body_inner}")
        body_code = "\n".join(body_lines)

        return f"{indent}def {func_name}(self{params_str}){ret_hint}:\n{body_code}"

    def _generate_parse_def(self, expr: ParseNonterminalDef, indent: str) -> str:
        """Generate a parse method definition."""
        return self._generate_self_method(
            f"parse_{expr.nonterminal.name}",
            expr.params,
            expr.body,
            expr.return_type,
            indent,
        )

    def _generate_pretty_def(self, expr: PrintNonterminalDef, indent: str) -> str:
        """Generate a pretty-print method definition."""
        return self._generate_self_method(
            f"pretty_{expr.nonterminal.name}",
            expr.params,
            expr.body,
            expr.return_type,
            indent,
        )

    # Parser generation settings
    parse_def_indent = "    "

    def format_literal_token_spec(self, escaped_literal: str) -> str:
        return (
            f"            ('LITERAL', re.compile(r'{escaped_literal}'), lambda x: x),"
        )

    def format_named_token_spec(self, token_name: str, token_pattern: str) -> str:
        return f"            ('{token_name}', re.compile(r'{token_pattern}'), lambda x: Lexer.scan_{token_name.lower()}(x)),"

    def format_command_line_comment(self, command_line: str) -> str:
        return f"\nCommand: {command_line}\n"

    def generate_method_def(self, expr: FunDef, indent: str) -> str:
        """Generate a function definition as an instance method."""
        return self._generate_self_method(
            self.escape_identifier(expr.name),
            expr.params,
            expr.body,
            expr.return_type,
            indent,
        )


def escape_identifier(name: str) -> str:
    """Escape a Python identifier if it's a keyword."""
    if name in PYTHON_KEYWORDS:
        return f"{name}_"
    return name


def generate_python_type(typ, generator: PythonCodeGenerator | None = None) -> str:
    """Generate Python type hint from a Type expression."""
    if generator is None:
        generator = PythonCodeGenerator()
    return generator.gen_type(typ)


def generate_python_lines(
    expr: TargetExpr,
    lines: list[str],
    indent: str = "",
    generator: PythonCodeGenerator | None = None,
) -> str | None:
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
    expr: FunDef | ParseNonterminalDef | PrintNonterminalDef,
    indent: str = "",
    generator: PythonCodeGenerator | None = None,
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
        elements_code = ", ".join(
            generate_python(elem, indent) for elem in expr.elements
        )
        return f"[{elements_code}]"
    elif isinstance(expr, Call):
        func_code = generate_python(expr.func, indent)
        args_code = ", ".join(generate_python(arg, indent) for arg in expr.args)
        return f"{func_code}({args_code})"
    elif isinstance(expr, Lambda):
        params = [escape_identifier(p.name) for p in expr.params]
        params_str = ", ".join(params) if params else ""
        body_code = generate_python(expr.body, indent)
        return f"lambda {params_str}: {body_code}"
    elif isinstance(expr, Let):
        lines: list[str] = []
        result = generate_python_lines(expr, lines, indent)
        assert result is not None
        if lines:
            return "\n".join(lines) + "\n" + result
        return result
    else:
        lines = []
        result = generate_python_lines(expr, lines, indent)
        assert result is not None
        if lines:
            return "\n".join(lines) + "\n" + result
        return result


__all__ = [
    "escape_identifier",
    "generate_python",
    "generate_python_lines",
    "generate_python_def",
    "generate_python_type",
    "PYTHON_KEYWORDS",
    "PythonCodeGenerator",
]
