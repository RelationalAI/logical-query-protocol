"""Code generation for Python from semantic action AST.

This module generates Python code from semantic action expressions,
with proper keyword escaping and idiomatic Python style.
"""

from typing import List, Optional, Set, Tuple, Union

from lqp.proto.v1.logic_pb2 import Value

from .codegen_base import CodeGenerator, BuiltinResult
from .target import (
    TargetExpr, Var, Lit, Symbol, Builtin, Message, OneOf, ListExpr, Call, Lambda, Let,
    IfElse, FunDef, ParseNonterminalDef, gensym
)


# Python keywords that need escaping
PYTHON_KEYWORDS: Set[str] = {
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
    'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
    'try', 'while', 'with', 'yield',
}


class PythonCodeGenerator(CodeGenerator):
    """Python code generator."""

    keywords = PYTHON_KEYWORDS
    indent_str = "    "

    base_type_map = {
        'Int64': 'int',
        'Float64': 'float',
        'String': 'str',
        'Boolean': 'bool',
    }

    def __init__(self, proto_messages=None):
        self.builtin_registry = {}
        self.proto_messages = proto_messages or {}
        self._message_field_map = None
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
        """Register builtin generators."""
        self.register_builtin("some", 1,
            lambda args, lines, indent: BuiltinResult(args[0], []))
        self.register_builtin("not", 1,
            lambda args, lines, indent: BuiltinResult(f"not {args[0]}", []))
        self.register_builtin("equal", 2,
            lambda args, lines, indent: BuiltinResult(f"{args[0]} == {args[1]}", []))
        self.register_builtin("not_equal", 2,
            lambda args, lines, indent: BuiltinResult(f"{args[0]} != {args[1]}", []))

        self.register_builtin("fragment_id_from_string", 1,
            lambda args, lines, indent: BuiltinResult(f"fragments_pb2.FragmentId(id={args[0]}.encode())", []))

        def gen_relation_id_from_string(args, lines, indent):
            val = gensym('val')
            id_low = gensym('id_low')
            id_high = gensym('id_high')
            return BuiltinResult(f"logic_pb2.RelationId(id_low={id_low}, id_high={id_high})", [
                f"{indent}{val} = int(hashlib.sha256({args[0]}.encode()).hexdigest()[:16], 16)",
                f"{indent}{id_low} = {val} & 0xFFFFFFFFFFFFFFFF",
                f"{indent}{id_high} = ({val} >> 64) & 0xFFFFFFFFFFFFFFFF",
            ])

        self.register_builtin("relation_id_from_string", 1,
            lambda args, lines, indent: BuiltinResult(f"self.relation_id_from_string({args[0]})", []))

        self.register_builtin("relation_id_from_int", 1,
            lambda args, lines, indent: BuiltinResult(f"logic_pb2.RelationId(id_low={args[0]} & 0xFFFFFFFFFFFFFFFF, id_high=({args[0]} >> 64) & 0xFFFFFFFFFFFFFFFF)", []))

        self.register_builtin("list_concat", 2,
            lambda args, lines, indent: BuiltinResult(f"({args[0]} + ({args[1]} if {args[1]} is not None else []))", []))

        self.register_builtin("list_append", 2,
            lambda args, lines, indent: BuiltinResult(f"{args[0]} + [{args[1]}]", []))

        self.register_builtin("list_push!", 2,
            lambda args, lines, indent: BuiltinResult("None", [f"{args[0]}.append({args[1]})"]))

        self.register_builtin("is_none", 1,
            lambda args, lines, indent: BuiltinResult(f"{args[0]} is None", []))

        self.register_builtin("fst", 1,
            lambda args, lines, indent: BuiltinResult(f"{args[0]}[0]", []))

        self.register_builtin("snd", 1,
            lambda args, lines, indent: BuiltinResult(f"{args[0]}[1]", []))

        self.register_builtin("make_tuple", -1,
            lambda args, lines, indent: BuiltinResult(f"({', '.join(args)},)", []))

        self.register_builtin("length", 1,
            lambda args, lines, indent: BuiltinResult(f"len({args[0]})", []))

        self.register_builtin("unwrap_option_or", 2,
            lambda args, lines, indent: BuiltinResult(f"({args[0]} if {args[0]} is not None else {args[1]})", []))

        self.register_builtin("match_lookahead_terminal", 2,
            lambda args, lines, indent: BuiltinResult(f"self.match_lookahead_terminal({args[0]}, {args[1]})", []))

        self.register_builtin("match_lookahead_literal", 2,
            lambda args, lines, indent: BuiltinResult(f"self.match_lookahead_literal({args[0]}, {args[1]})", []))

        self.register_builtin("consume_literal", 1,
            lambda args, lines, indent: BuiltinResult("None", [f"self.consume_literal({args[0]})"]))

        self.register_builtin("consume_terminal", 1,
            lambda args, lines, indent: BuiltinResult(f"self.consume_terminal({args[0]})", []))

        self.register_builtin("current_token", 0,
            lambda args, lines, indent: BuiltinResult("self.lookahead(0)", []))

        # error has two arities, so we use a custom generator
        def gen_error(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            if len(args) == 2:
                return BuiltinResult("None", [f"raise ParseError({args[0]} + f\": {{{{{args[1]}}}}}\")"])
            elif len(args) == 1:
                return BuiltinResult("None", [f"raise ParseError({args[0]})"])
            else:
                raise ValueError("Invalid number of arguments for builtin `error`.")
        self.register_builtin("error", -1, gen_error)

        self.register_builtin("construct_configure", 1,
            lambda args, lines, indent: BuiltinResult(f"self.construct_configure({args[0]})", []))

        self.register_builtin("export_csv_config", 3,
            lambda args, lines, indent: BuiltinResult(f"self.export_csv_config({args[0]}, {args[1]}, {args[2]})", []))

        self.register_builtin("start_fragment", 1,
            lambda args, lines, indent: BuiltinResult(f"self.start_fragment({args[0]})", []))

        self.register_builtin("construct_fragment", 2,
            lambda args, lines, indent: BuiltinResult(f"self.construct_fragment({args[0]}, {args[1]})", []))

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

    def generate_lines(self, expr: TargetExpr, lines: List[str], indent: str = "") -> str:
        # Special case: fragments_pb2.Fragment construction with debug_info parameter
        if isinstance(expr, Call) and isinstance(expr.func, Message) and expr.func.name == "Fragment":
            for arg in expr.args:
                if isinstance(arg, Var) and arg.name == "debug_info":
                    lines.append(f"{indent}debug_info = self.construct_debug_info(self.id_to_debuginfo.get(id, {{}}))")
                    break

        return super().generate_lines(expr, lines, indent)

    def _generate_call(self, expr: Call, lines: List[str], indent: str) -> str:
        """Override to handle OneOf specially for Python protobuf."""
        # Check for Message constructor with OneOf call argument
        if isinstance(expr.func, Message):
            f = self.generate_lines(expr.func, lines, indent)

            # Python protobuf requires keyword arguments
            # Get field mapping from proto message definitions
            message_field_map = self._build_message_field_map()

            # Process arguments, looking for Call(OneOf(...), [value]) patterns
            positional_args = []
            keyword_args = []

            msg_key = (expr.func.module, expr.func.name)
            field_specs = message_field_map.get(msg_key, [])
            arg_idx = 0
            field_idx = 0

            while arg_idx < len(expr.args):
                arg = expr.args[arg_idx]

                if isinstance(arg, Call) and isinstance(arg.func, OneOf) and len(arg.args) == 1:
                    # Extract field name and value from Call(OneOf(Symbol), [value])
                    # For Python keywords, use dictionary unpacking: **{'def': value}
                    field_name = arg.func.field_name.name
                    field_value = self.generate_lines(arg.args[0], lines, indent)
                    if field_name in PYTHON_KEYWORDS:
                        keyword_args.append(f"**{{'{field_name}': {field_value}}}")
                    else:
                        keyword_args.append(f"{field_name}={field_value}")
                    arg_idx += 1
                elif field_idx < len(field_specs):
                    field_name, is_repeated = field_specs[field_idx]

                    if is_repeated:
                        # Determine how many args belong to this repeated field
                        remaining_fields = len(field_specs) - field_idx - 1
                        max_args_for_this_field = len(expr.args) - arg_idx - remaining_fields

                        # If there's exactly one arg for this field, use it directly (it's already a list)
                        # Otherwise, collect multiple args into a list
                        if max_args_for_this_field == 1:
                            field_value = self.generate_lines(arg, lines, indent)
                            if field_name in PYTHON_KEYWORDS:
                                keyword_args.append(f"**{{'{field_name}': {field_value}}}")
                            else:
                                keyword_args.append(f"{field_name}={field_value}")
                            arg_idx += 1
                        else:
                            # Collect multiple args into a list
                            values = []
                            while arg_idx < len(expr.args) and len(values) < max_args_for_this_field:
                                next_arg = expr.args[arg_idx]
                                # Stop if we encounter a oneof
                                if isinstance(next_arg, Call) and isinstance(next_arg.func, OneOf):
                                    break
                                field_value = self.generate_lines(next_arg, lines, indent)
                                values.append(field_value)
                                arg_idx += 1

                            if values:
                                list_value = f"[{', '.join(values)}]"
                            else:
                                list_value = "[]"
                            if field_name in PYTHON_KEYWORDS:
                                keyword_args.append(f"**{{'{field_name}': {list_value}}}")
                            else:
                                keyword_args.append(f"{field_name}={list_value}")
                    else:
                        field_value = self.generate_lines(arg, lines, indent)
                        if field_name in PYTHON_KEYWORDS:
                            keyword_args.append(f"**{{'{field_name}': {field_value}}}")
                        else:
                            keyword_args.append(f"{field_name}={field_value}")
                        arg_idx += 1

                    field_idx += 1
                else:
                    positional_args.append(self.generate_lines(arg, lines, indent))
                    arg_idx += 1

            # Build argument list - use keyword args if we have any
            if keyword_args:
                all_args = keyword_args
            else:
                all_args = positional_args + keyword_args
            args_code = ', '.join(all_args)

            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'{f}({args_code})', is_declaration=True)}")
            return tmp

        # Fall back to base implementation for non-Message calls
        return super()._generate_call(expr, lines, indent)

    def _generate_if_else(self, expr: IfElse, lines: List[str], indent: str) -> str:
        """Override to skip var declaration (Python doesn't need it)."""
        cond_code = self.generate_lines(expr.condition, lines, indent)

        # Optimization: short-circuit for boolean literals.
        # This is not needed, but makes the generated code more readable.
        if expr.then_branch == Lit(True):
            tmp_lines = []
            else_code = self.generate_lines(expr.else_branch, tmp_lines, indent)
            if not tmp_lines:
                return f"({cond_code} or {else_code})"
        if expr.else_branch == Lit(False):
            tmp_lines = []
            then_code = self.generate_lines(expr.then_branch, tmp_lines, indent)
            if not tmp_lines:
                return f"({cond_code} and {then_code})"

        tmp = gensym()
        lines.append(f"{indent}{self.gen_if_start(cond_code)}")

        body_indent = indent + self.indent_str
        then_code = self.generate_lines(expr.then_branch, lines, body_indent)
        lines.append(f"{body_indent}{self.gen_assignment(tmp, then_code)}")

        lines.append(f"{indent}{self.gen_else()}")
        else_code = self.generate_lines(expr.else_branch, lines, body_indent)
        lines.append(f"{body_indent}{self.gen_assignment(tmp, else_code)}")

        return tmp

    def _generate_parse_def(self, expr: ParseNonterminalDef, indent: str) -> str:
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

        if expr.body is None:
            body_code = f"{indent}    pass"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(expr.body, body_lines, indent + "    ")
            body_lines.append(f"{indent}    return {body_inner}")
            body_code = "\n".join(body_lines)

        return f"{indent}def {func_name}(self{params_str}){ret_hint}:\n{body_code}"


# Module-level instance for convenience
_generator = PythonCodeGenerator()


def escape_identifier(name: str) -> str:
    """Escape a Python identifier if it's a keyword."""
    return _generator.escape_identifier(name)


def generate_python_type(typ) -> str:
    """Generate Python type hint from a Type expression."""
    return _generator.gen_type(typ)


def generate_python_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> str:
    """Generate Python code from a target IR expression."""
    return _generator.generate_lines(expr, lines, indent)


def generate_python_def(expr: Union[FunDef, ParseNonterminalDef], indent: str = "") -> str:
    """Generate Python function definition."""
    return _generator.generate_def(expr, indent)


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
        if lines:
            return '\n'.join(lines) + '\n' + result
        return result
    else:
        lines = []
        result = generate_python_lines(expr, lines, indent)
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
