"""Code generation for Julia from semantic action AST.

This module generates Julia code from semantic action expressions,
with proper keyword escaping and idiomatic Julia style.
"""

from typing import List, Optional, Set, Tuple, Union

from .codegen_base import CodeGenerator, BuiltinResult
from .target import (
    TargetExpr, Var, Lit, Symbol, NewMessage, OneOf, ListExpr, Call, Lambda, Let,
    IfElse, FunDef, VisitNonterminalDef, VisitNonterminal, GetElement
)
from .gensym import gensym


# Julia keywords and reserved names that need escaping
JULIA_KEYWORDS: Set[str] = {
    'abstract', 'baremodule', 'begin', 'break', 'catch', 'const', 'continue',
    'do', 'else', 'elseif', 'end', 'export', 'false', 'finally', 'for',
    'function', 'global', 'if', 'import', 'let', 'local', 'macro', 'module',
    'quote', 'return', 'struct', 'true', 'try', 'type', 'using', 'while',
    # Soft keywords (contextual)
    'as', 'in', 'isa', 'where', 'mutable', 'primitive', 'outer',
    # Built-in types that conflict (capitalized)
    'Type',
}


class JuliaCodeGenerator(CodeGenerator):
    """Julia code generator."""

    keywords = JULIA_KEYWORDS
    indent_str = "    "

    base_type_map = {
        'Int32': 'Int32',
        'Int64': 'Int64',
        'Float64': 'Float64',
        'String': 'String',
        'Boolean': 'Bool',
        'Bytes': 'Vector{UInt8}',
    }

    def __init__(self, proto_messages=None):
        self.builtin_registry = {}
        self.proto_messages = proto_messages or {}
        self._message_field_map: Optional[dict[tuple[str, str], list[tuple[str, bool]]]] = None
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
        """Register builtin generators.

        Arity is looked up from target_builtins.BUILTIN_REGISTRY.
        """
        self.register_builtin("some",
            lambda args, lines, indent: BuiltinResult(args[0], []))
        self.register_builtin("not",
            lambda args, lines, indent: BuiltinResult(f"!{args[0]}", []))
        self.register_builtin("and",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} && {args[1]})", []))
        self.register_builtin("or",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} || {args[1]})", []))
        self.register_builtin("equal",
            lambda args, lines, indent: BuiltinResult(f"{args[0]} == {args[1]}", []))
        self.register_builtin("not_equal",
            lambda args, lines, indent: BuiltinResult(f"{args[0]} != {args[1]}", []))
        self.register_builtin("add",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} + {args[1]})", []))

        self.register_builtin("fragment_id_from_string",
            lambda args, lines, indent: BuiltinResult(f"Proto.FragmentId(Vector{{UInt8}}({args[0]}))", []))

        self.register_builtin("relation_id_from_string",
            lambda args, lines, indent: BuiltinResult(
                f"relation_id_from_string(parser, {args[0]})", []))

        self.register_builtin("relation_id_from_int",
            lambda args, lines, indent: BuiltinResult(
                f"Proto.RelationId({args[0]} & 0xFFFFFFFFFFFFFFFF, ({args[0]} >> 64) & 0xFFFFFFFFFFFFFFFF)", []))

        self.register_builtin("list_concat",
            lambda args, lines, indent: BuiltinResult(
                f"vcat({args[0]}, !isnothing({args[1]}) ? {args[1]} : [])", []))

        self.register_builtin("map",
            lambda args, lines, indent: BuiltinResult(f"map({args[0]}, {args[1]})", []))

        self.register_builtin("is_none",
            lambda args, lines, indent: BuiltinResult(f"isnothing({args[0]})", []))

        self.register_builtin("is_some",
            lambda args, lines, indent: BuiltinResult(f"!isnothing({args[0]})", []))

        self.register_builtin("unwrap_option",
            lambda args, lines, indent: BuiltinResult(args[0], []))

        self.register_builtin("none",
            lambda args, lines, indent: BuiltinResult("nothing", []))

        self.register_builtin("make_empty_bytes",
            lambda args, lines, indent: BuiltinResult("UInt8[]", []))

        self.register_builtin("dict_from_list",
            lambda args, lines, indent: BuiltinResult(f"Dict({args[0]})", []))

        self.register_builtin("dict_get",
            lambda args, lines, indent: BuiltinResult(f"get({args[0]}, {args[1]}, nothing)", []))

        self.register_builtin("has_proto_field",
            lambda args, lines, indent: BuiltinResult(
                f"hasproperty({args[0]}, Symbol({args[1]})) && !isnothing(getproperty({args[0]}, Symbol({args[1]})))", []))

        self.register_builtin("string_to_upper",
            lambda args, lines, indent: BuiltinResult(f"uppercase({args[0]})", []))

        self.register_builtin("string_in_list",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} in {args[1]})", []))

        self.register_builtin("string_concat",
            lambda args, lines, indent: BuiltinResult(f"({args[0]} * {args[1]})", []))

        self.register_builtin("encode_string",
            lambda args, lines, indent: BuiltinResult(f"Vector{{UInt8}}({args[0]})", []))

        self.register_builtin("tuple",
            lambda args, lines, indent: BuiltinResult(f"({', '.join(args)},)", []))

        self.register_builtin("length",
            lambda args, lines, indent: BuiltinResult(f"length({args[0]})", []))

        self.register_builtin("unwrap_option_or",
            lambda args, lines, indent: BuiltinResult(
                f"(!isnothing({args[0]}) ? {args[0]} : {args[1]})", []))

        self.register_builtin("int64_to_int32",
            lambda args, lines, indent: BuiltinResult(f"Int32({args[0]})", []))

        self.register_builtin("match_lookahead_terminal",
            lambda args, lines, indent: BuiltinResult(f"match_lookahead_terminal(parser, {args[0]}, {args[1]})", []))

        self.register_builtin("match_lookahead_literal",
            lambda args, lines, indent: BuiltinResult(f"match_lookahead_literal(parser, {args[0]}, {args[1]})", []))

        self.register_builtin("consume_literal",
            lambda args, lines, indent: BuiltinResult("nothing", [f"consume_literal!(parser, {args[0]})"]))

        self.register_builtin("consume_terminal",
            lambda args, lines, indent: BuiltinResult(f"consume_terminal!(parser, {args[0]})", []))

        self.register_builtin("current_token",
            lambda args, lines, indent: BuiltinResult("current_token(parser)", []))

        # error is variadic (1 or 2 args)
        def gen_error(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            if len(args) == 2:
                return BuiltinResult("nothing", [f'throw(ParseError({args[0]} * ": " * string({args[1]})))'])
            elif len(args) == 1:
                return BuiltinResult("nothing", [f"throw(ParseError({args[0]}))"])
            else:
                raise ValueError("Invalid number of arguments for builtin `error`.")
        self.register_builtin("error", gen_error)

        self.register_builtin("construct_configure",
            lambda args, lines, indent: BuiltinResult(f"construct_configure(parser, {args[0]})", []))

        self.register_builtin("construct_betree_info",
            lambda args, lines, indent: BuiltinResult(f"construct_betree_info(parser, {args[0]}, {args[1]}, {args[2]})", []))

        self.register_builtin("construct_csv_config",
            lambda args, lines, indent: BuiltinResult(f"construct_csv_config(parser, {args[0]})", []))

        self.register_builtin("start_fragment",
            lambda args, lines, indent: BuiltinResult(args[0], [f"start_fragment(parser, {args[0]})"]))

        self.register_builtin("construct_fragment",
            lambda args, lines, indent: BuiltinResult(f"construct_fragment(parser, {args[0]}, {args[1]})", []))

        self.register_builtin("export_csv_config",
            lambda args, lines, indent: BuiltinResult(f"export_csv_config(parser, {args[0]}, {args[1]}, {args[2]})", []))

    def escape_keyword(self, name: str) -> str:
        return f'var"{name}"'

    # --- Literal generation ---

    def gen_none(self) -> str:
        return "nothing"

    def gen_bool(self, value: bool) -> str:
        return "true" if value else "false"

    def gen_string(self, value: str) -> str:
        # Julia uses double quotes for strings (single quotes are for characters)
        # Escape backslashes and double quotes
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'

    # --- Symbol and constructor generation ---

    def gen_symbol(self, name: str) -> str:
        return f":{name}"

    def gen_constructor(self, module: str, name: str) -> str:
        # Escape Julia keywords
        if name in self.keywords:
            return f'Proto.var"#{name}"'
        return f"Proto.{name}"

    def gen_builtin_ref(self, name: str) -> str:
        return f"parser.{name}"

    def gen_named_fun_ref(self, name: str) -> str:
        return f"Parser.{name}"

    def gen_parse_nonterminal_ref(self, name: str) -> str:
        return f"parse_{name}"

    # --- Type generation ---

    def gen_message_type(self, module: str, name: str) -> str:
        # Escape Julia keywords
        if name in self.keywords:
            return f'Proto.var"#{name}"'
        return f"Proto.{name}"

    def gen_tuple_type(self, element_types: List[str]) -> str:
        if not element_types:
            return 'Tuple{}'
        return f"Tuple{{{', '.join(element_types)}}}"

    def gen_list_type(self, element_type: str) -> str:
        return f"Vector{{{element_type}}}"

    def gen_option_type(self, element_type: str) -> str:
        return f"Union{{Nothing, {element_type}}}"

    def gen_list_literal(self, elements: List[str], element_type) -> str:
        type_code = self.gen_type(element_type)
        return f"{type_code}[{', '.join(elements)}]"

    def gen_dict_type(self, key_type: str, value_type: str) -> str:
        return f"Dict{{{key_type},{value_type}}}"

    def gen_dict_from_list(self, pairs: str) -> str:
        return f"Dict({pairs})"

    def gen_dict_lookup(self, dict_expr: str, key: str, default: Optional[str]) -> str:
        if default is None:
            return f"get({dict_expr}, {key}, nothing)"
        return f"get({dict_expr}, {key}, {default})"

    def gen_has_field(self, message: str, field_name: str) -> str:
        return f"hasproperty({message}, :{field_name}) && !isnothing(getproperty({message}, :{field_name}))"

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

    def generate_lines(self, expr: TargetExpr, lines: List[str], indent: str = "") -> Optional[str]:
        # Special case: Proto.Fragment construction with debug_info parameter
        if isinstance(expr, Call) and isinstance(expr.func, NewMessage) and expr.func.name == "Fragment":
            for arg in expr.args:
                if isinstance(arg, Var) and arg.name == "debug_info":
                    lines.append(f"{indent}debug_info = construct_debug_info(parser, get(parser.id_to_debuginfo, id, Dict()))")
                    break

        # Julia uses 1-based indexing, so convert GetElement indices
        if isinstance(expr, GetElement):
            tuple_code = self.generate_lines(expr.tuple_expr, lines, indent)
            # Convert 0-based index to 1-based
            julia_index = expr.index + 1
            return f"{tuple_code}[{julia_index}]"

        return super().generate_lines(expr, lines, indent)

    def _generate_call(self, expr: Call, lines: List[str], indent: str) -> str:
        """Override to handle Message constructors and OneOf specially for Julia."""
        # Check for Message constructor with OneOf call argument
        if isinstance(expr.func, NewMessage):
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
                    field_name = self.escape_identifier(arg.func.field_name)
                    field_value = self.generate_lines(arg.args[0], lines, indent)
                    field_symbol = self.gen_symbol(arg.func.field_name)
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

            # Build argument list - Julia protobuf uses positional args only
            # Combine keyword args (formatted as "name=value") into just values for positional calling
            positional_values = []
            for kw in keyword_args:
                # Extract value from "name=value"
                if '=' in kw:
                    value = kw.split('=', 1)[1]
                    positional_values.append(value)
                else:
                    positional_values.append(kw)

            all_args = positional_args + positional_values
            args_code = ', '.join(all_args)

            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'{f}({args_code})', is_declaration=True)}")
            return tmp

        # Check for Call(OneOf(Symbol), [value]) pattern (not in Message constructor)
        if isinstance(expr.func, OneOf) and len(expr.args) == 1:
            field_symbol = self.gen_symbol(expr.func.field_name)
            field_value = self.generate_lines(expr.args[0], lines, indent)
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'OneOf({field_symbol}, {field_value})', is_declaration=True)}")
            return tmp

        # Check for VisitNonterminal calls - need to add parser as first argument
        if isinstance(expr.func, VisitNonterminal):
            f = self.generate_lines(expr.func, lines, indent)
            args: List[str] = []
            for arg in expr.args:
                arg_code = self.generate_lines(arg, lines, indent)
                assert arg_code is not None, "Function argument should not contain a return"
                args.append(arg_code)
            # Prepend parser as first argument
            all_args = ["parser"] + args
            args_code = ', '.join(all_args)
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'{f}({args_code})', is_declaration=True)}")
            return tmp

        # Fall back to base implementation
        return super()._generate_call(expr, lines, indent)

    def _generate_oneof(self, expr: OneOf, lines: List[str], indent: str) -> str:
        """Generate Julia OneOf reference.

        OneOf should only appear as the function in Call(OneOf(...), [value]).
        This method shouldn't normally be called.
        """
        raise ValueError(f"OneOf should only appear in Call(OneOf(...), [value]) pattern: {expr}")

    def _generate_if_else(self, expr: IfElse, lines: List[str], indent: str) -> Optional[str]:
        """Override to skip var declaration (Julia doesn't need it)."""
        cond_code = self.generate_lines(expr.condition, lines, indent)
        assert cond_code is not None, "If condition should not contain a return"

        # Optimization: short-circuit for boolean literals.
        # This is not needed, but makes the generated code more readable.
        if expr.then_branch == Lit(True):
            tmp_lines: List[str] = []
            else_code = self.generate_lines(expr.else_branch, tmp_lines, indent)
            if not tmp_lines and else_code is not None:
                return f"({cond_code} || {else_code})"
        if expr.else_branch == Lit(False):
            tmp_lines = []
            then_code = self.generate_lines(expr.then_branch, tmp_lines, indent)
            if not tmp_lines and then_code is not None:
                return f"({cond_code} && {then_code})"

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

        lines.append(f"{indent}{self.gen_if_end()}")

        # If both branches returned, propagate None
        if then_code is None and else_code is None:
            return None

        return tmp

    def _generate_parse_def(self, expr: VisitNonterminalDef, indent: str) -> str:
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
            # Only add return if the body didn't already return
            if body_inner is not None:
                body_lines.append(f"{indent}    return {body_inner}")
            body_code = "\n".join(body_lines)

        return f"{indent}function {func_name}({params_str}){ret_hint}\n{body_code}\n{indent}end"

    def _generate_fun_def(self, expr: FunDef, indent: str) -> str:
        """Generate a regular function definition (helper function from grammar)."""
        func_name = self.escape_identifier(expr.name)
        params = [(self.escape_identifier(p.name), self.gen_type(p.type)) for p in expr.params]
        ret_type = self.gen_type(expr.return_type) if expr.return_type else None

        header = self.gen_func_def_header(func_name, params, ret_type)

        if expr.body is None:
            body_code = f"{indent}{self.indent_str}nothing"
        else:
            lines: List[str] = []
            body_inner = self.generate_lines(expr.body, lines, indent + self.indent_str)
            # Only add return if the body didn't already return
            if body_inner is not None:
                lines.append(f"{indent}{self.indent_str}{self.gen_return(body_inner)}")
            body_code = "\n".join(lines)

        end = self.gen_func_def_end()
        return f"{indent}{header}\n{body_code}\n{indent}{end}"


# Module-level instance for convenience
_generator = JuliaCodeGenerator()


def escape_identifier(name: str) -> str:
    """Escape a Julia identifier if it's a keyword."""
    return _generator.escape_identifier(name)


def generate_julia_type(typ) -> str:
    """Generate Julia type annotation from a Type expression."""
    return _generator.gen_type(typ)


def generate_julia_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> Optional[str]:
    """Generate Julia code from a target IR expression."""
    return _generator.generate_lines(expr, lines, indent)


def generate_julia_def(expr: Union[FunDef, VisitNonterminalDef], indent: str = "") -> str:
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
    elif isinstance(expr, ListExpr):
        if not expr.elements:
            return "[]"
        elements_code = ', '.join(generate_julia(elem, indent) for elem in expr.elements)
        return f"[{elements_code}]"
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
        result_str = result if result is not None else ""
        if lines:
            return '\n'.join(lines) + '\n' + result_str
        return result_str
    else:
        lines = []
        result = generate_julia_lines(expr, lines, indent)
        result_str = result if result is not None else ""
        if lines:
            return '\n'.join(lines) + '\n' + result_str
        return result_str


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
