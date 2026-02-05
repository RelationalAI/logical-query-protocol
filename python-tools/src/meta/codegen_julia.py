"""Code generation for Julia from semantic action AST.

This module generates Julia code from semantic action expressions,
with proper keyword escaping and idiomatic Julia style.
"""

from typing import List, Optional, Set, Tuple, Union

from .codegen_base import CodeGenerator
from .codegen_templates import JULIA_TEMPLATES
from .target import (
    TargetExpr, Var, Lit, Symbol, NewMessage, OneOf, ListExpr, Call, Lambda, Let,
    FunDef, VisitNonterminalDef, VisitNonterminal, GetElement,
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
        """Register builtin generators from templates."""
        self.register_builtins_from_templates(JULIA_TEMPLATES)

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
        # Handle NewMessage with fields (which may contain OneOf calls)
        if isinstance(expr, NewMessage):
            return self._generate_newmessage(expr, lines, indent)

        # Julia uses 1-based indexing, so convert GetElement indices
        if isinstance(expr, GetElement):
            tuple_code = self.generate_lines(expr.tuple_expr, lines, indent)
            # Convert 0-based index to 1-based
            julia_index = expr.index + 1
            return f"{tuple_code}[{julia_index}]"

        return super().generate_lines(expr, lines, indent)

    def _generate_newmessage(self, expr: NewMessage, lines: List[str], indent: str) -> str:
        """Generate Julia code for NewMessage with fields containing OneOf calls."""
        ctor = self.gen_constructor(expr.module, expr.name)

        if not expr.fields:
            # No fields - return constructor directly
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'{ctor}()', is_declaration=True)}")
            return tmp

        # NewMessage with fields - need to handle OneOf specially
        # Julia protobuf uses positional args in field order
        positional_args = []

        for field_name, field_expr in expr.fields:
            # Check if this field is a Call(OneOf, [value])
            if isinstance(field_expr, Call) and isinstance(field_expr.func, OneOf) and len(field_expr.args) == 1:
                # OneOf field - wrap in OneOf(symbol, value)
                oneof_field_name = field_expr.func.field_name
                field_value = self.generate_lines(field_expr.args[0], lines, indent)
                assert field_value is not None
                field_symbol = self.gen_symbol(oneof_field_name)
                positional_args.append(f"OneOf({field_symbol}, {field_value})")
            else:
                # Regular field
                field_value = self.generate_lines(field_expr, lines, indent)
                assert field_value is not None
                positional_args.append(field_value)

        args_code = ', '.join(positional_args)
        tmp = gensym()
        lines.append(f"{indent}{self.gen_assignment(tmp, f'{ctor}({args_code})', is_declaration=True)}")
        return tmp

    def _generate_call(self, expr: Call, lines: List[str], indent: str) -> Optional[str]:
        """Override to handle OneOf and VisitNonterminal specially for Julia."""
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
