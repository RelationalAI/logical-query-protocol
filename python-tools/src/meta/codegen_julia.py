"""Code generation for Julia from semantic action AST.

This module generates Julia code from semantic action expressions,
with proper keyword escaping and idiomatic Julia style.
"""

from typing import Dict, List, Optional, Set, Tuple, Union

from .codegen_base import CodeGenerator, CodegenConfig, PARSER_MODE
from .codegen_templates import JULIA_TEMPLATES
from .target import (
    TargetExpr, Var, Lit, Symbol, NamedFun, NewMessage, OneOf, ListExpr, Call, Lambda, Let,
    FunDef, ParseNonterminalDef, PrintNonterminalDef,
    ParseNonterminal, PrintNonterminal,
    GetField, GetElement, MessageType,
)
from .gensym import gensym
from .target_builtins import NEVER


# Julia reserved keywords that ProtoBuf.jl escapes with '#' prefix.
# This must match ProtoBuf.jl's JULIA_RESERVED_KEYWORDS exactly so that
# OneOf discriminator symbols in the generated parser align with the
# protobuf-generated Julia code.
JULIA_KEYWORDS: Set[str] = {
    'abstract', 'baremodule', 'begin', 'break', 'catch', 'const', 'continue',
    'do', 'else', 'elseif', 'end', 'export', 'false', 'finally', 'for',
    'function', 'global', 'if', 'import', 'let', 'local', 'macro', 'module',
    'quote', 'return', 'struct', 'true', 'try', 'type', 'Type', 'using', 'while',
    # Obsolete Julia keywords
    'bitstype', 'ccall', 'immutable', 'importall', 'typealias',
}


class JuliaCodeGenerator(CodeGenerator):
    """Julia code generator."""

    keywords = JULIA_KEYWORDS
    indent_str = "    "

    base_type_map = {
        # Capitalized forms (from protobuf)
        'Int32': 'Int32',
        'Int64': 'Int64',
        'Float64': 'Float64',
        'String': 'String',
        'Boolean': 'Bool',
        'Bytes': 'Vector{UInt8}',
        # Lowercase forms (from target IR / Python-style)
        'int': 'Int64',
        'float': 'Float64',
        'str': 'String',
        'bool': 'Bool',
        'bytes': 'Vector{UInt8}',
    }

    def __init__(self, proto_messages=None, config: CodegenConfig = PARSER_MODE):
        super().__init__(proto_messages, config=config)
        self._oneof_alt_set: Optional[Set[tuple]] = None
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register builtin generators from templates."""
        self.register_builtins_from_templates(JULIA_TEMPLATES)
        # Register custom builtins that need special handling
        self._register_custom_builtins()

    def _register_custom_builtins(self) -> None:
        """Register custom builtins that need special handling."""
        from .codegen_base import BuiltinResult

        def enum_value_handler(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            # Args are string literals like '"MaintenanceLevel"', '"MAINTENANCE_LEVEL_OFF"'
            # Strip quotes to get the actual enum type and value names
            enum_type = args[0].strip('"')
            enum_val = args[1].strip('"')
            return BuiltinResult(f"Proto.{enum_type}.{enum_val}", [])

        self.register_builtin("enum_value", enum_value_handler)

        def tuple_handler(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            if len(args) == 0:
                return BuiltinResult("()", [])
            elif len(args) == 1:
                return BuiltinResult(f"({args[0]},)", [])
            else:
                return BuiltinResult(f"({', '.join(args)},)", [])

        self.register_builtin("tuple", tuple_handler)

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

    def _escape_proto_field(self, name: str) -> str:
        """Escape a proto field name for use as a Julia kwarg.

        ProtoBuf.jl escapes Julia keywords with a '#' prefix in struct fields
        and keyword constructors, e.g. `global` -> `var"#global"`.
        """
        if name in JULIA_KEYWORDS:
            return f'var"#{name}"'
        return name

    def _gen_oneof_symbol(self, name: str) -> str:
        """Generate a Julia symbol for a OneOf field name, escaping keywords.

        ProtoBuf.jl escapes hard Julia keywords in oneof field names with a '#'
        prefix (e.g., `export` becomes `var"#export"`). The OneOf discriminator
        symbol must match.
        """
        if name in JULIA_KEYWORDS:
            return f':var"#{name}"'
        return f":{name}"

    def gen_constructor(self, module: str, name: str) -> str:
        if name in self.keywords:
            return f'Proto.var"#{name}"'
        return f"Proto.{name}"

    def gen_builtin_ref(self, name: str) -> str:
        return f"parser.{name}"

    def gen_named_fun_ref(self, name: str) -> str:
        # In Julia, named functions are regular functions (not methods on Parser)
        # They take parser as the first argument, handled in _generate_call
        return name

    def gen_parse_nonterminal_ref(self, name: str) -> str:
        return f"parse_{name}"

    def gen_pretty_nonterminal_ref(self, name: str) -> str:
        return f"pretty_{name}"

    # --- Type generation ---

    def gen_message_type(self, module: str, name: str) -> str:
        if name in self.keywords:
            return f'Proto.var"#{name}"'
        return f"Proto.{name}"

    def gen_enum_type(self, module: str, name: str) -> str:
        if name in self.keywords:
            return f'Proto.var"#{name}"'
        return f"Proto.{name}"

    def gen_enum_value(self, module: str, enum_name: str, value_name: str) -> str:
        if enum_name in self.keywords:
            return f'Proto.var"#{enum_name}".{value_name}'
        return f"Proto.{enum_name}.{value_name}"

    def gen_tuple_type(self, element_types: List[str]) -> str:
        if not element_types:
            return 'Tuple{}'
        return f"Tuple{{{', '.join(element_types)}}}"

    def gen_sequence_type(self, element_type: str) -> str:
        return f"Vector{{{element_type}}}"

    def gen_list_type(self, element_type: str) -> str:
        return f"Vector{{{element_type}}}"

    def gen_option_type(self, element_type: str) -> str:
        return f"Union{{Nothing, {element_type}}}"

    def gen_list_literal(self, elements: List[str], element_type) -> str:
        # For non-empty lists, Julia can infer the type
        if elements:
            # Optimization: skip type annotation for non-empty lists
            type_code = self.gen_type(element_type)
            return f"{type_code}[{', '.join(elements)}]"
        # For empty lists with Never type (no type info), use untyped []
        if element_type == NEVER:
            return "[]"
        # For empty lists with known type, use typed syntax
        type_code = self.gen_type(element_type)
        return f"{type_code}[]"

    def gen_dict_type(self, key_type: str, value_type: str) -> str:
        return f"Dict{{{key_type},{value_type}}}"

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

    def gen_foreach_start(self, var: str, collection: str) -> str:
        return f"for {var} in {collection}"

    def gen_foreach_enumerated_start(self, index_var: str, var: str, collection: str) -> str:
        return f"for ({index_var}, {var}) in enumerate({collection})"

    def gen_foreach_end(self) -> str:
        return "end"

    def gen_empty_body(self) -> str:
        return "nothing"

    def gen_assignment(self, var: str, value: str, is_declaration: bool = False) -> str:
        return f"{var} = {value}"

    def gen_return(self, value: str) -> str:
        return f"return {value}"

    def gen_var_declaration(self, var: str, type_hint: Optional[str] = None) -> str:
        # Julia doesn't need explicit declaration
        return ""

    # --- Lambda and function definition syntax ---

    def gen_lambda_start(self, params: List[Tuple[str, Optional[str]]], return_type: Optional[str]) -> Tuple[str, str]:
        params_str = ', '.join(n for n, _ in params) if params else ''
        return (f"function __FUNC__({params_str})", "end")

    def gen_func_def_header(self, name: str, params: List[Tuple[str, str]],
                            return_type: Optional[str], is_method: bool = False) -> str:
        params_str = ', '.join(f"{n}::{t}" for n, t in params)
        ret_hint = f"::{return_type}" if return_type else ""
        return f"function {name}({params_str}){ret_hint}"

    def gen_func_def_end(self) -> str:
        return "end"

    def _generate_foreach_enumerated(self, expr, lines: List[str], indent: str) -> str:
        """Override to adjust for Julia's 1-based enumerate.

        The IR generates guards like `index > 0` assuming 0-based indexing.
        Julia's `enumerate` returns 1-based indices, so we use a raw index
        variable and assign the 0-based version at the top of the loop body.
        """
        from .target import ForeachEnumerated
        assert isinstance(expr, ForeachEnumerated)
        collection_code = self.generate_lines(expr.collection, lines, indent)
        assert collection_code is not None
        index_name = self.escape_identifier(expr.index_var.name)
        var_name = self.escape_identifier(expr.var.name)

        raw_index = gensym('i')
        lines.append(f"{indent}for ({raw_index}, {var_name}) in enumerate({collection_code})")
        body_indent = indent + self.indent_str
        lines.append(f"{body_indent}{index_name} = {raw_index} - 1")
        self.generate_lines(expr.body, lines, body_indent)
        lines.append(f"{indent}end")
        return self.gen_none()

    def _generate_get_element(self, expr: GetElement, lines: List[str], indent: str) -> str:
        """Julia uses 1-based indexing."""
        tuple_code = self.generate_lines(expr.tuple_expr, lines, indent)
        julia_index = expr.index + 1
        return f"{tuple_code}[{julia_index}]"

    def _build_oneof_alt_set(self) -> Set[tuple]:
        """Build set of (module, msg_name, alt_name) for oneof alternative fields."""
        if self._oneof_alt_set is not None:
            return self._oneof_alt_set
        result: Set[tuple] = set()
        for (module, msg_name), proto_msg in self.proto_messages.items():
            for oneof in proto_msg.oneofs:
                for field in oneof.fields:
                    result.add((module, msg_name, field.name))
        self._oneof_alt_set = result
        return result

    def _generate_newmessage(self, expr: NewMessage, lines: List[str], indent: str) -> str:
        """Generate NewMessage for Julia proto structs.

        Julia ProtoBuf represents oneof fields as a single struct field
        with the parent oneof name, holding a OneOf{T} value. This method
        maps grammar kwargs (which use oneof alternative names) to the
        actual Julia struct fields.
        """
        ctor = self.gen_constructor(expr.module, expr.name)

        if not expr.fields:
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'{ctor}()', is_declaration=True)}")
            return tmp

        msg_key = (expr.module, expr.name)
        proto_msg = self.proto_messages.get(msg_key)

        if proto_msg is None:
            return super()._generate_newmessage(expr, lines, indent)

        # Build alt_name → oneof_parent_name mapping
        alt_to_parent: Dict[str, str] = {}
        for oneof in proto_msg.oneofs:
            for field in oneof.fields:
                alt_to_parent[field.name] = oneof.name

        regular_fields = {f.name for f in proto_msg.fields}

        # Generate values for each grammar kwarg, grouped by struct field
        # For oneofs: struct_field → [(alt_name, generated_value), ...]
        # For regular: struct_field → generated_value
        oneof_groups: Dict[str, List[Tuple[str, str]]] = {}
        regular_values: Dict[str, str] = {}

        for field_name, field_expr in expr.fields:
            # Check if field_expr is already a Call(OneOf(...), [value])
            is_oneof_call = (
                isinstance(field_expr, Call)
                and isinstance(field_expr.func, OneOf)
                and len(field_expr.args) == 1
            )

            if is_oneof_call:
                assert isinstance(field_expr, Call) and isinstance(field_expr.func, OneOf)
                alt_name = field_expr.func.field_name
                value = self.generate_lines(field_expr.args[0], lines, indent)
                assert value is not None
                parent = alt_to_parent.get(alt_name, alt_name)
                oneof_groups.setdefault(parent, []).append((alt_name, value))
            elif field_name in alt_to_parent:
                # Grammar kwarg is a oneof alternative
                parent = alt_to_parent[field_name]
                value = self.generate_lines(field_expr, lines, indent)
                assert value is not None
                oneof_groups.setdefault(parent, []).append((field_name, value))
            elif field_name in regular_fields:
                value = self.generate_lines(field_expr, lines, indent)
                assert value is not None
                regular_values[field_name] = value
            else:
                # Field not in proto struct (e.g., dropped by Julia proto gen).
                # Generate for side effects but discard.
                self.generate_lines(field_expr, lines, indent)

        # Build keyword constructor args (avoids dependence on positional field order)
        kwargs: List[str] = []
        for oneof in proto_msg.oneofs:
            alts = oneof_groups.get(oneof.name, [])
            if not alts:
                continue
            elif len(alts) == 1:
                alt_name, value = alts[0]
                sym = self._gen_oneof_symbol(alt_name)
                kwargs.append(f"{self._escape_proto_field(oneof.name)}=OneOf({sym}, {value})")
            else:
                # Multiple alternatives: chain ternary expressions
                result_expr = "nothing"
                for alt_name, value in reversed(alts):
                    sym = self._gen_oneof_symbol(alt_name)
                    result_expr = f"(!isnothing({value}) ? OneOf({sym}, {value}) : {result_expr})"
                kwargs.append(f"{self._escape_proto_field(oneof.name)}={result_expr}")
        for f in proto_msg.fields:
            if f.name in regular_values:
                kwargs.append(f"{self._escape_proto_field(f.name)}={regular_values[f.name]}")

        call = f"{ctor}({', '.join(kwargs)})"
        tmp = gensym()
        lines.append(f"{indent}{self.gen_assignment(tmp, call, is_declaration=True)}")
        return tmp

    def _is_oneof_getfield(self, expr: GetField) -> bool:
        """Check if a GetField accesses a OneOf alternative."""
        if not isinstance(expr.message_type, MessageType):
            return False
        key = (expr.message_type.module, expr.message_type.name, expr.field_name)
        return key in self._build_oneof_alt_set()

    def generate_lines(self, expr: 'TargetExpr', lines: List[str], indent: str = "") -> Optional[str]:
        """Override to intercept GetField for OneOf alternatives."""
        if isinstance(expr, GetField) and self._is_oneof_getfield(expr):
            obj_code = self.generate_lines(expr.object, lines, indent)
            sym = self._gen_oneof_symbol(expr.field_name)
            return f"_get_oneof_field({obj_code}, {sym})"
        return super().generate_lines(expr, lines, indent)

    def _generate_call(self, expr: Call, lines: List[str], indent: str) -> Optional[str]:
        """Override to handle OneOf and Parse/PrintNonterminal specially for Julia."""
        # Check for Call(OneOf(Symbol), [value]) pattern (not in Message constructor)
        if isinstance(expr.func, OneOf) and len(expr.args) == 1:
            field_symbol = self._gen_oneof_symbol(expr.func.field_name)
            field_value = self.generate_lines(expr.args[0], lines, indent)
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'OneOf({field_symbol}, {field_value})', is_declaration=True)}")
            return tmp

        # Check for parse/print nonterminal or NamedFun calls - need to add receiver as first argument
        if isinstance(expr.func, (ParseNonterminal, PrintNonterminal, NamedFun)):
            f = self.generate_lines(expr.func, lines, indent)
            args: List[str] = []
            for arg in expr.args:
                arg_code = self.generate_lines(arg, lines, indent)
                assert arg_code is not None, "Function argument should not contain a return"
                args.append(arg_code)
            # PrintNonterminal uses "pp" (PrettyPrinter), others use "parser"
            receiver = "pp" if isinstance(expr.func, PrintNonterminal) else "parser"
            all_args = [receiver] + args
            args_code = ', '.join(all_args)
            if self._is_void_expr(expr):
                lines.append(f"{indent}{f}({args_code})")
                return self.gen_none()
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

    def _generate_julia_function(self, func_name: str, first_param: str, params, body,
                                  return_type, indent: str) -> str:
        """Generate a Julia function definition with a typed first parameter.

        Args:
            func_name: The function name.
            first_param: The first parameter string (e.g. "parser::Parser").
            params: List of Param objects (each with .name and .type).
            body: The function body expression, or None for an empty body.
            return_type: The return type, or None.
            indent: Indentation prefix.
        """
        typed_params = [first_param]
        for param in params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            typed_params.append(f"{escaped_name}::{type_hint}")

        params_str = ', '.join(typed_params)
        ret_hint = f"::{self.gen_type(return_type)}" if return_type and not self._is_void_type(return_type) else ""

        if body is None:
            body_code = f"{indent}{self.indent_str}{self.gen_empty_body()}"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(body, body_lines, indent + self.indent_str)
            if body_inner is not None:
                body_lines.append(f"{indent}{self.indent_str}{self.gen_return(body_inner)}")
            body_code = "\n".join(body_lines)

        return f"{indent}function {func_name}({params_str}){ret_hint}\n{body_code}\n{indent}end"

    def _generate_parse_def(self, expr: ParseNonterminalDef, indent: str) -> str:
        """Generate a parse method definition."""
        return self._generate_julia_function(
            f"parse_{expr.nonterminal.name}", self.config.first_param,
            expr.params, expr.body, expr.return_type, indent
        )

    def _generate_pretty_def(self, expr: PrintNonterminalDef, indent: str) -> str:
        """Generate a pretty-print function definition."""
        return self._generate_julia_function(
            f"pretty_{expr.nonterminal.name}", self.config.first_param,
            expr.params, expr.body, expr.return_type, indent
        )

    def format_literal_token_spec(self, escaped_literal: str) -> str:
        return f'        ("LITERAL", r"{escaped_literal}", identity),'

    def format_named_token_spec(self, token_name: str, token_pattern: str) -> str:
        escaped_pattern = token_pattern.replace('"', '\\"')
        return f'        ("{token_name}", r"{escaped_pattern}", scan_{token_name.lower()}),'

    def format_command_line_comment(self, command_line: str) -> str:
        return f"Command: {command_line}"

    def generate_method_def(self, expr: FunDef, indent: str) -> str:
        """Generate a function definition with receiver as first parameter."""
        return self._generate_julia_function(
            self.escape_identifier(expr.name), self.config.first_param,
            expr.params, expr.body, expr.return_type, indent
        )

def escape_identifier(name: str) -> str:
    """Escape a Julia identifier if it's a keyword."""
    if name in JULIA_KEYWORDS:
        return f'var"{name}"'
    return name


def generate_julia_type(typ) -> str:
    """Generate Julia type annotation from a Type expression."""
    return JuliaCodeGenerator().gen_type(typ)


def generate_julia_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> Optional[str]:
    """Generate Julia code from a target IR expression."""
    return JuliaCodeGenerator().generate_lines(expr, lines, indent)


def generate_julia_def(expr: Union[FunDef, ParseNonterminalDef, PrintNonterminalDef], indent: str = "") -> str:
    """Generate Julia function definition."""
    return JuliaCodeGenerator().generate_def(expr, indent)


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


__all__ = [
    'escape_identifier',
    'generate_julia',
    'generate_julia_lines',
    'generate_julia_def',
    'generate_julia_type',
    'JULIA_KEYWORDS',
    'JuliaCodeGenerator',
]
