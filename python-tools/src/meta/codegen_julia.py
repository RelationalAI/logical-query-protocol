"""Code generation for Julia from semantic action AST.

This module generates Julia code from semantic action expressions,
with proper keyword escaping and idiomatic Julia style.
"""

from typing import List, Optional, Set, Tuple, Union

from lqp.proto.v1.logic_pb2 import Value

from .codegen_base import CodeGenerator, BuiltinResult
from .target import (
    TargetExpr, Var, Lit, Symbol, Builtin, Message, OneOf, Call, Lambda, Let, IfElse,
    FunDef, ParseNonterminalDef, gensym
)


# Julia keywords that need escaping
JULIA_KEYWORDS: Set[str] = {
    'abstract', 'baremodule', 'begin', 'break', 'catch', 'const', 'continue',
    'do', 'else', 'elseif', 'end', 'export', 'false', 'finally', 'for',
    'function', 'global', 'if', 'import', 'let', 'local', 'macro', 'module',
    'quote', 'return', 'struct', 'true', 'try', 'type', 'using', 'while',
    # Soft keywords (contextual)
    'as', 'in', 'isa', 'where', 'mutable', 'primitive', 'outer',
}


class JuliaCodeGenerator(CodeGenerator):
    """Julia code generator."""

    keywords = JULIA_KEYWORDS
    indent_str = "    "

    base_type_map = {
        'Int64': 'Int64',
        'Float64': 'Float64',
        'String': 'String',
        'Boolean': 'Bool',
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
                # Escape Julia keywords and preserve repeated flag
                escaped_fields = []
                for fname, is_repeated in regular_fields:
                    if fname in self.keywords:
                        escaped_fields.append((fname + '_', is_repeated))
                    else:
                        escaped_fields.append((fname, is_repeated))
                field_map[(module, msg_name)] = escaped_fields

        self._message_field_map = field_map
        return field_map

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
            lambda args, lines, indent: BuiltinResult(f"Proto.FragmentId(id=Vector{{UInt8}}({args[0]}))", []))

        self.register_builtin("relation_id_from_string", 1,
            lambda args, lines, indent: BuiltinResult(
                f"Proto.RelationId(id=parse(UInt64, bytes2hex(sha256({args[0]})[1:8]), base=16))", []))

        self.register_builtin("relation_id_from_int", 1,
            lambda args, lines, indent: BuiltinResult(f"Proto.RelationId(id={args[0]})", []))

        self.register_builtin("list_concat", 2,
            lambda args, lines, indent: BuiltinResult(f"vcat({args[0]}, {args[1]})", []))

        self.register_builtin("list_append", 2,
            lambda args, lines, indent: BuiltinResult(f"vcat({args[0]}, [{args[1]}])", []))

        self.register_builtin("list_push!", 2,
            lambda args, lines, indent: BuiltinResult("nothing", [f"push!({args[0]}, {args[1]})"]))

        self.register_builtin("make_list", -1,
            lambda args, lines, indent: BuiltinResult(f"[{', '.join(args)}]", []))

        self.register_builtin("is_none", 1,
            lambda args, lines, indent: BuiltinResult(f"isnothing({args[0]})", []))

        self.register_builtin("fst", 1,
            lambda args, lines, indent: BuiltinResult(f"{args[0]}[1]", []))

        self.register_builtin("snd", 1,
            lambda args, lines, indent: BuiltinResult(f"{args[0]}[2]", []))

        self.register_builtin("make_tuple", -1,
            lambda args, lines, indent: BuiltinResult(f"({', '.join(args)},)", []))

        self.register_builtin("length", 1,
            lambda args, lines, indent: BuiltinResult(f"length({args[0]})", []))

        self.register_builtin("unwrap_option_or", 2,
            lambda args, lines, indent: BuiltinResult(f"something({args[0]}, {args[1]})", []))

        self.register_builtin("match_lookahead_terminal", 2,
            lambda args, lines, indent: BuiltinResult(f"match_lookahead_terminal(parser, {args[0]}, {args[1]})", []))

        self.register_builtin("match_lookahead_literal", 2,
            lambda args, lines, indent: BuiltinResult(f"match_lookahead_literal(parser, {args[0]}, {args[1]})", []))

        self.register_builtin("consume_literal", 1,
            lambda args, lines, indent: BuiltinResult("nothing", [f"consume_literal(parser, {args[0]})"]))

        self.register_builtin("consume_terminal", 1,
            lambda args, lines, indent: BuiltinResult(f"consume_terminal(parser, {args[0]})", []))

        self.register_builtin("current_token", 0,
            lambda args, lines, indent: BuiltinResult("current_token(parser)", []))

        def gen_error(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            if len(args) == 2:
                return BuiltinResult("nothing", [f'throw(ParseError({args[0]} * ": " * string({args[1]})))'])
            elif len(args) == 1:
                return BuiltinResult("nothing", [f"throw(ParseError({args[0]}))"])
            else:
                raise ValueError("Invalid number of arguments for `error`")
        self.register_builtin("error", -1, gen_error)

        self.register_builtin("construct_configure", 1,
            lambda args, lines, indent: BuiltinResult(f"construct_configure(parser, {args[0]})", []))

        self.register_builtin("export_csv_config", 3,
            lambda args, lines, indent: BuiltinResult(f"export_csv_config(parser, {args[0]}, {args[1]}, {args[2]})", []))

        self.register_builtin("start_fragment", 1,
            lambda args, lines, indent: BuiltinResult(f"start_fragment(parser, {args[0]})", []))

        self.register_builtin("construct_fragment", 2,
            lambda args, lines, indent: BuiltinResult(f"construct_fragment(parser, {args[0]}, {args[1]})", []))

    def escape_keyword(self, name: str) -> str:
        return f'var"{name}"'

    # --- Literal generation ---

    def gen_none(self) -> str:
        return "nothing"

    def gen_bool(self, value: bool) -> str:
        return "true" if value else "false"

    def gen_string(self, value: str) -> str:
        return repr(value)

    # --- Symbol and constructor generation ---

    def gen_symbol(self, name: str) -> str:
        return f":{name}"

    def gen_constructor(self, module: str, name: str) -> str:
        return f"Proto.{name}"

    def gen_builtin_ref(self, name: str) -> str:
        return f"parser.{name}"

    def gen_parse_nonterminal_ref(self, name: str) -> str:
        return f"parse_{name}"

    # --- Type generation ---

    def gen_message_type(self, module: str, name: str) -> str:
        return f"Proto.{name}"

    def gen_tuple_type(self, element_types: List[str]) -> str:
        if not element_types:
            return 'Tuple{}'
        return f"Tuple{{{', '.join(element_types)}}}"

    def gen_list_type(self, element_type: str) -> str:
        return f"Vector{{{element_type}}}"

    def gen_option_type(self, element_type: str) -> str:
        return f"Union{{Nothing, {element_type}}}"

    def gen_function_type(self, param_types: List[str], return_type: str) -> str:
        return "Function"  # Julia doesn't have precise function types

    # --- Control flow syntax ---

    def gen_if_start(self, cond: str) -> str:
        return f"if {cond}"

    def gen_else(self) -> str:
        return "else"

    def gen_if_end(self) -> str:
        return "end"

    def gen_while_start(self, cond: str) -> str:
        return f"while {cond}"

    def gen_while_end(self) -> str:
        return "end"

    def gen_empty_body(self) -> str:
        return "# empty body"

    def gen_assignment(self, var: str, value: str, is_declaration: bool = False) -> str:
        return f"{var} = {value}"

    def gen_return(self, value: str) -> str:
        return f"return {value}"

    def gen_var_declaration(self, var: str, type_hint: Optional[str] = None) -> str:
        # Julia doesn't need explicit declaration
        return ""

    # --- Lambda and function definition syntax ---

    def gen_lambda_start(self, params: List[str], return_type: Optional[str]) -> Tuple[str, str]:
        params_str = ', '.join(params) if params else ''
        return (f"function __FUNC__({params_str})", "end")

    def gen_func_def_header(self, name: str, params: List[Tuple[str, str]],
                            return_type: Optional[str], is_method: bool = False) -> str:
        params_str = ', '.join(f"{n}::{t}" for n, t in params)
        ret_hint = f"::{return_type}" if return_type else ""
        return f"function {name}({params_str}){ret_hint}"

    def gen_func_def_end(self) -> str:
        return "end"

    # --- Override generate_lines for Julia-specific special cases ---

    def generate_lines(self, expr: TargetExpr, lines: List[str], indent: str = "") -> str:
        # Special case: Proto.Fragment construction with debug_info parameter
        if isinstance(expr, Call) and isinstance(expr.func, Message) and expr.func.name == "Fragment":
            for arg in expr.args:
                if isinstance(arg, Var) and arg.name == "debug_info":
                    lines.append(f"{indent}debug_info = construct_debug_info(parser, get(parser.id_to_debuginfo, id, Dict()))")
                    break

        return super().generate_lines(expr, lines, indent)

    def _generate_call(self, expr: Call, lines: List[str], indent: str) -> str:
        """Override to handle Message constructors and OneOf specially for Julia."""
        # Check for Message constructor with OneOf call argument
        if isinstance(expr.func, Message):
            f = self.generate_lines(expr.func, lines, indent)

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
                    field_name = self.escape_identifier(arg.func.field_name.name)
                    field_value = self.generate_lines(arg.args[0], lines, indent)
                    field_symbol = self.gen_symbol(arg.func.field_name.name)
                    keyword_args.append(f"{field_name}=OneOf({field_symbol}, {field_value})")
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
                                keyword_args.append(f"{field_name}=[{', '.join(values)}]")
                            else:
                                keyword_args.append(f"{field_name}=[]")
                    else:
                        field_value = self.generate_lines(arg, lines, indent)
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

        # Check for Call(OneOf(Symbol), [value]) pattern (not in Message constructor)
        if isinstance(expr.func, OneOf) and len(expr.args) == 1:
            field_symbol = self.gen_symbol(expr.func.field_name.name)
            field_value = self.generate_lines(expr.args[0], lines, indent)
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'OneOf({field_symbol}, {field_value})', is_declaration=True)}")
            return tmp

        # Fall back to base implementation
        return super()._generate_call(expr, lines, indent)

    def _generate_oneof(self, expr: OneOf, lines: List[str], indent: str) -> str:
        """Generate Julia OneOf reference.

        OneOf should only appear as the function in Call(OneOf(...), [value]).
        This method shouldn't normally be called.
        """
        raise ValueError(f"OneOf should only appear in Call(OneOf(...), [value]) pattern: {expr}")

    def _generate_if_else(self, expr: IfElse, lines: List[str], indent: str) -> str:
        """Override to skip var declaration (Julia doesn't need it)."""
        cond_code = self.generate_lines(expr.condition, lines, indent)

        # Optimization: short-circuit for boolean literals
        if expr.then_branch == Lit(True):
            else_code = self.generate_lines(expr.else_branch, lines, indent + self.indent_str)
            return f"({cond_code} || {else_code})"
        if expr.else_branch == Lit(False):
            then_code = self.generate_lines(expr.then_branch, lines, indent + self.indent_str)
            return f"({cond_code} && {then_code})"

        tmp = gensym()
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
        func_name = f"parse_{expr.nonterminal.name}"

        params = ["parser::Parser"]
        for param in expr.params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            params.append(f"{escaped_name}::{type_hint}")

        params_str = ', '.join(params)

        ret_hint = f"::{self.gen_type(expr.return_type)}" if expr.return_type else ""

        if expr.body is None:
            body_code = f"{indent}    nothing"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(expr.body, body_lines, indent + "    ")
            body_lines.append(f"{indent}    return {body_inner}")
            body_code = "\n".join(body_lines)

        return f"{indent}function {func_name}({params_str}){ret_hint}\n{body_code}\n{indent}end"


# Module-level instance for convenience
_generator = JuliaCodeGenerator()


def escape_identifier(name: str) -> str:
    """Escape a Julia identifier if it's a keyword."""
    return _generator.escape_identifier(name)


def generate_julia_type(typ) -> str:
    """Generate Julia type annotation from a Type expression."""
    return _generator.gen_type(typ)


def generate_julia_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> str:
    """Generate Julia code from a target IR expression."""
    return _generator.generate_lines(expr, lines, indent)


def generate_julia_def(expr: Union[FunDef, ParseNonterminalDef], indent: str = "") -> str:
    """Generate Julia function definition."""
    return _generator.generate_def(expr, indent)


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
        lines: List[str] = []
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
    'generate_julia_type',
    'generate_julia_function_body',
    'JULIA_KEYWORDS',
    'JuliaCodeGenerator',
]
