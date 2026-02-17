"""Code generation for Go from semantic action AST.

This module generates Go code from semantic action expressions,
with proper keyword escaping and idiomatic Go style.
"""

from typing import Dict, List, Optional, Set, Tuple, Union

from .codegen_base import CodeGenerator
from .codegen_templates import GO_TEMPLATES
from .target import (
    TargetExpr, NewMessage, OneOf, ListExpr, Call, Seq,
    FunDef, ParseNonterminalDef, PrintNonterminalDef, ParseNonterminal, PrintNonterminal,
    GetElement, TargetType,
)
from .gensym import gensym


# Go keywords that need escaping
GO_KEYWORDS: Set[str] = {
    'break', 'case', 'chan', 'const', 'continue', 'default', 'defer', 'else',
    'fallthrough', 'for', 'func', 'go', 'goto', 'if', 'import', 'interface',
    'map', 'package', 'range', 'return', 'select', 'struct', 'switch', 'type', 'var',
}


def to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase for Go field/type names."""
    parts = name.split('_')
    return ''.join(part.capitalize() for part in parts)


class GoCodeGenerator(CodeGenerator):
    """Go code generator.

    Tracks declared variables to generate proper Go variable declarations.
    In Go, first use of a variable requires := (short declaration) and
    subsequent uses require = (assignment).
    """

    keywords = GO_KEYWORDS
    indent_str = "\t"

    base_type_map = {
        'Int32': 'int32',
        'Int64': 'int64',
        'Float64': 'float64',
        'String': 'string',
        'Boolean': 'bool',
        'Bytes': '[]byte',
        'Void': 'interface{}',
        'Never': 'interface{}',
        'None': 'interface{}',
        'Any': 'interface{}',
        'Symbol': 'string',
        'Unknown': 'interface{}',
        'EOF': 'interface{}',
        # Python-ish names that might appear
        'int': 'int64',
        'float': 'float64',
        'str': 'string',
        'bool': 'bool',
        'bytes': '[]byte',
    }

    # Go types that are already nullable (nil-able) without wrapping in a pointer.
    _nullable_prefixes = ('*', '[')

    @staticmethod
    def _is_nullable_go_type(type_str: str) -> bool:
        """Check if a Go type is already nullable (nil represents absent)."""
        return (type_str.startswith('*') or type_str.startswith('[') or
                type_str.startswith('map[') or type_str == 'interface{}')

    # Zero values for Go types
    _go_zero_values: Dict[str, str] = {
        'int32': '0',
        'int64': '0',
        'float64': '0.0',
        'string': '""',
        'bool': 'false',
        '[]byte': 'nil',
    }

    def __init__(self, proto_messages=None):
        super().__init__(proto_messages)
        self._oneof_field_to_parent = self._build_oneof_field_map()
        self._declared_vars: Set[str] = set()
        self._current_return_type: Optional[str] = None
        self._current_return_is_option: bool = False
        self._current_return_option_needs_ptr: bool = False
        self._register_builtins()

    def reset_declared_vars(self) -> None:
        """Reset the set of declared variables. Call at start of each function."""
        self._declared_vars = set()

    def set_current_return_type(self, return_type: Optional[str],
                               return_target_type: Optional[TargetType] = None) -> None:
        """Set the current function's return type for zero value generation."""
        from .target import OptionType
        self._current_return_type = return_type
        if return_target_type is not None and isinstance(return_target_type, OptionType):
            inner = self.gen_type(return_target_type.element_type)
            self._current_return_is_option = True
            self._current_return_option_needs_ptr = not self._is_nullable_go_type(inner)
        else:
            self._current_return_is_option = False
            self._current_return_option_needs_ptr = False

    def is_declared(self, var: str) -> bool:
        """Check if a variable has been declared."""
        return var in self._declared_vars

    def mark_declared(self, var: str) -> None:
        """Mark a variable as declared."""
        self._declared_vars.add(var)

    def _build_oneof_field_map(self):
        """Build a mapping from oneof field names to their parent message and oneof name.

        Returns dict mapping (module, message_name, field_name) -> (oneof_name, field_type).
        """
        field_map = {}
        if not self.proto_messages:
            return field_map

        for (module, msg_name), proto_msg in self.proto_messages.items():
            for oneof in proto_msg.oneofs:
                for f in oneof.fields:
                    field_map[(module, msg_name, f.name)] = (oneof.name, f.type)
        return field_map

    def _register_builtins(self) -> None:
        """Register builtin generators from templates."""
        self.register_builtins_from_templates(GO_TEMPLATES)
        # Override 'none' to use Option zero value when we know the return type
        self._register_none_builtin()

    def _register_none_builtin(self) -> None:
        """Register custom none builtin for Go."""
        from .codegen_base import BuiltinResult

        def none_generator(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            return BuiltinResult("nil", [])

        self.register_builtin("none", none_generator)

        # 'consume_terminal' builtin - returns typed value from Token
        # Map terminal names to Go types for type assertion
        # Map terminal names to TokenValue accessor methods
        terminal_accessor_map = {
            "INT": "AsInt64",
            "FLOAT": "AsFloat64",
            "STRING": "AsString",
            "SYMBOL": "AsString",
            "DECIMAL": "AsDecimal",
            "INT128": "AsInt128",
            "UINT128": "AsUint128",
        }

        def consume_terminal_generator(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            if len(args) != 1:
                return BuiltinResult("p.consumeTerminal()", [])
            terminal_arg = args[0]
            terminal_name = terminal_arg.strip('"')
            accessor = terminal_accessor_map.get(terminal_name)
            if accessor:
                return BuiltinResult(f"p.consumeTerminal({terminal_arg}).Value.{accessor}()", [])
            return BuiltinResult(f"p.consumeTerminal({terminal_arg}).Value.AsString()", [])

        self.register_builtin("consume_terminal", consume_terminal_generator)

    def escape_keyword(self, name: str) -> str:
        return f"{name}_"

    # --- Literal generation ---

    def gen_none(self) -> str:
        # For Option return types (now pointer or collapsed nullable), nil works
        if self._current_return_is_option:
            return "nil"
        # For primitive return types, use zero value
        if self._current_return_type and self._current_return_type in self._go_zero_values:
            return self._go_zero_values[self._current_return_type]
        return "nil"

    def gen_bool(self, value: bool) -> str:
        return "true" if value else "false"

    def gen_string(self, value: str) -> str:
        # Go uses double quotes for strings
        # Escape backslashes, double quotes, and newlines
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return f'"{escaped}"'

    # --- Symbol and constructor generation ---

    def gen_symbol(self, name: str) -> str:
        # In Go, symbols are just strings
        return f'"{name}"'

    def gen_constructor(self, module: str, name: str) -> str:
        # Go protobuf uses pointer to struct
        return f"&pb.{name}{{}}"

    def gen_builtin_ref(self, name: str) -> str:
        return f"p.{name}"

    def gen_named_fun_ref(self, name: str) -> str:
        return f"p.{name}"

    def gen_parse_nonterminal_ref(self, name: str) -> str:
        return f"p.parse_{name}"

    def gen_pretty_nonterminal_ref(self, name: str) -> str:
        return f"p.pretty_{name}"

    # --- Type generation ---

    def gen_message_type(self, module: str, name: str) -> str:
        return f"*pb.{name}"

    def gen_enum_type(self, module: str, name: str) -> str:
        return f"pb.{name}"

    def gen_enum_value(self, module: str, enum_name: str, value_name: str) -> str:
        # Go pattern: pb.EnumName_VALUE_NAME
        return f"pb.{enum_name}_{value_name}"

    def gen_tuple_type(self, element_types: List[str]) -> str:
        # Go doesn't have tuples, use a struct or interface slice
        return f"[]interface{{}}"

    def gen_sequence_type(self, element_type: str) -> str:
        return f"[]{element_type}"

    def gen_list_type(self, element_type: str) -> str:
        return f"[]{element_type}"

    def gen_option_type(self, element_type: str) -> str:
        if self._is_nullable_go_type(element_type):
            return element_type
        return f"*{element_type}"

    def gen_list_literal(self, elements: List[str], element_type: TargetType) -> str:
        from .target import BaseType
        # For empty lists with unknown element type, use nil (Go infers the type from context)
        if not elements:
            if isinstance(element_type, BaseType) and element_type.name in ('Unknown', 'Never', 'Any'):
                return "nil"
            type_code = self.gen_type(element_type)
            return "[]" + type_code + "{}"
        type_code = self.gen_type(element_type)
        return "[]" + type_code + "{" + ', '.join(elements) + "}"

    def gen_dict_type(self, key_type: str, value_type: str) -> str:
        return f"map[{key_type}]{value_type}"

    def gen_function_type(self, param_types: List[str], return_type: str) -> str:
        params = ", ".join(param_types)
        return f"func({params}) {return_type}"

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

    def gen_foreach_start(self, var: str, collection: str) -> str:
        return f"for _, {var} := range {collection} {{"

    def gen_foreach_enumerated_start(self, index_var: str, var: str, collection: str) -> str:
        return f"for {index_var}, {var} := range {collection} {{"

    def gen_foreach_end(self) -> str:
        return "}"

    def gen_empty_body(self) -> str:
        return "// empty"

    def gen_assignment(self, var: str, value: str, is_declaration: bool = False) -> str:
        # In Go, use := for first declaration, = for reassignment
        # We track declared variables to handle this
        if is_declaration or not self.is_declared(var):
            self.mark_declared(var)
            return f"{var} := {value}"
        return f"{var} = {value}"

    def gen_return(self, value: str) -> str:
        return f"return {value}"

    def gen_var_declaration(self, var: str, type_hint: Optional[str] = None) -> str:
        # Go needs a type or initial value
        # Mark as declared so subsequent assignments use = instead of :=
        self.mark_declared(var)
        if type_hint:
            return f"var {var} {type_hint}"
        return f"var {var} interface{{}}"

    # --- Lambda and function definition syntax ---

    def gen_lambda_start(self, params: List[Tuple[str, Optional[str]]], return_type: Optional[str]) -> Tuple[str, str]:
        params_str = ', '.join(f"{n} {t if t else 'interface{}'}" for n, t in params) if params else ''
        ret = return_type if return_type else "interface{}"
        return (f"__FUNC__ := func({params_str}) {ret} {{", "}")

    def gen_func_def_header(self, name: str, params: List[Tuple[str, str]],
                            return_type: Optional[str], is_method: bool = False) -> str:
        params_str = ', '.join(f"{n} {t}" for n, t in params)
        ret = f" {return_type}" if return_type else ""
        if is_method:
            return f"func (p *Parser) {name}({params_str}){ret} {{"
        return f"func {name}({params_str}){ret} {{"

    def gen_func_def_end(self) -> str:
        return "}"

    def _generate_nil_else_branch(
        self, tmp: str, lines: List[str], indent: str, body_indent: str,
    ) -> str:
        """Go's var declarations zero-initialize, so no else branch needed."""
        return self.gen_none()

    def _generate_get_element(self, expr: GetElement, lines: List[str], indent: str) -> str:
        """Go uses 0-based indexing with type assertion for tuple elements."""
        tuple_code = self.generate_lines(expr.tuple_expr, lines, indent)
        # Add type assertion since tuple elements are interface{}
        try:
            elem_type = expr.target_type()
            if elem_type is not None:
                go_type = self.gen_type(elem_type)
                return f"{tuple_code}[{expr.index}].({go_type})"
        except (NotImplementedError, ValueError):
            pass
        return f"{tuple_code}[{expr.index}]"

    def gen_field_access(self, obj_code: str, field_name: str) -> str:
        """Generate Go field access using getter methods (nil-safe)."""
        pascal_field = to_pascal_case(field_name)
        return f"{obj_code}.Get{pascal_field}()"

    def _is_optional_scalar_field(self, expr) -> bool:
        """Check if a GetField accesses an optional scalar proto field.

        Go protobuf getters strip pointer types from optional scalars,
        returning plain values instead of *T. For nil checks and unwrap,
        we need direct PascalCase field access to preserve the pointer type.
        """
        from .target import GetField, OptionType
        if not isinstance(expr, GetField):
            return False
        if not isinstance(expr.field_type, OptionType):
            return False
        inner_go = self.gen_type(expr.field_type.element_type)
        return not self._is_nullable_go_type(inner_go)

    def generate_lines(self, expr: TargetExpr, lines: List[str], indent: str = "") -> Optional[str]:
        from .target import GetField
        # For optional scalar proto fields, use direct PascalCase access
        # to preserve pointer type (getters strip it).
        if isinstance(expr, GetField) and self._is_optional_scalar_field(expr):
            obj_code = self.generate_lines(expr.object, lines, indent)
            assert obj_code is not None
            pascal_field = to_pascal_case(expr.field_name)
            return f"{obj_code}.{pascal_field}"
        return super().generate_lines(expr, lines, indent)

    def _generate_seq(self, expr: Seq, lines: List[str], indent: str) -> Optional[str]:
        """Generate Go sequence, suppressing unused variable errors.

        In Go, declared-but-unused variables are compile errors. When an
        intermediate expression in a Seq produces a temp variable (e.g., from
        an IfElse used for side effects), we emit `_ = var` to suppress it.
        """
        result: Optional[str] = self.gen_none()
        for i, e in enumerate(expr.exprs):
            result = self.generate_lines(e, lines, indent)
            if result is None:
                break
            # Suppress unused temp variable from non-final expressions
            if i < len(expr.exprs) - 1 and result is not None and result.startswith("_t"):
                lines.append(f"{indent}_ = {result}")
        return result

    def _generate_newmessage(self, expr: NewMessage, lines: List[str], indent: str) -> str:
        """Generate Go code for NewMessage with fields containing OneOf calls.

        In Go protobuf, OneOf fields require wrapping values in the appropriate
        wrapper struct. Multiple OneOf variants in the same group are generated
        as conditional assignments after the struct literal (since only one can be set).
        """
        if not expr.fields:
            # No fields - return constructor directly
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'&pb.{expr.name}{{}}', is_declaration=True)}")
            return tmp

        # Separate regular fields from oneof fields
        regular_assignments = []
        # Group oneof fields by their parent oneof name: {oneof_name: [(field_name, option_var, wrapper_code)]}
        # option_var is the original Option variable name for checking .Valid
        oneof_groups: Dict[str, List[Tuple[str, str, str]]] = {}

        from .target import Var, OptionType

        def unwrap_if_option(field_expr, field_value: str) -> Tuple[str, str]:
            """Unwrap Option type values for struct field assignment.

            Returns (option_var, unwrapped_value) where option_var is for != nil check.
            For ptr-wrapped scalars, dereferences with deref(x, zero).
            For collapsed nullable types, returns the value directly (or inline if-else for non-nil defaults).
            """
            if isinstance(field_expr, Var) and field_expr.type is not None:
                if isinstance(field_expr.type, OptionType):
                    inner_type = self.gen_type(field_expr.type.element_type)
                    is_nullable = self._is_nullable_go_type(inner_type)
                    if is_nullable:
                        zero = "nil"
                    else:
                        zero = self._go_zero_values.get(inner_type, "nil")
                    if is_nullable:
                        # Collapsed nullable — nil default means just pass through
                        if zero == "nil":
                            return (field_value, field_value)
                        # Non-nil default: generate inline if-else with temp
                        tmp = gensym()
                        lines.append(f"{indent}{tmp} := {field_value}")
                        self.mark_declared(tmp)
                        lines.append(f"{indent}if {field_value} == nil {{")
                        lines.append(f"{indent}\t{tmp} = {zero}")
                        lines.append(f"{indent}}}")
                        return (field_value, tmp)
                    else:
                        # Ptr-wrapped scalar: use deref()
                        return (field_value, f"deref({field_value}, {zero})")
            return (field_value, field_value)

        for field_name, field_expr in expr.fields:
            # Check if this field is a Call(OneOf, [value])
            if isinstance(field_expr, Call) and isinstance(field_expr.func, OneOf) and len(field_expr.args) == 1:
                # OneOf field with explicit wrapper
                oneof_field_name = field_expr.func.field_name
                oneof_arg = field_expr.args[0]
                field_value = self.generate_lines(oneof_arg, lines, indent)
                assert field_value is not None
                # Unwrap if the argument is an Option type
                option_var, unwrapped = unwrap_if_option(oneof_arg, field_value)

                pascal_field = to_pascal_case(oneof_field_name)
                wrapper = f"&pb.{expr.name}_{pascal_field}{{{pascal_field}: {unwrapped}}}"

                # field_name here is the oneof parent name
                oneof_name = field_name
                if oneof_name not in oneof_groups:
                    oneof_groups[oneof_name] = []
                oneof_groups[oneof_name].append((oneof_field_name, option_var, wrapper))
            else:
                # Check if this field is a OneOf variant using proto schema info
                oneof_info = self._oneof_field_to_parent.get((expr.module, expr.name, field_name))
                if oneof_info is not None:
                    # This field is a OneOf variant
                    oneof_name, _field_type = oneof_info
                    field_value = self.generate_lines(field_expr, lines, indent)
                    assert field_value is not None
                    # Unwrap if the value is an Option type
                    option_var, unwrapped = unwrap_if_option(field_expr, field_value)

                    pascal_field = to_pascal_case(field_name)
                    wrapper = f"&pb.{expr.name}_{pascal_field}{{{pascal_field}: {unwrapped}}}"

                    if oneof_name not in oneof_groups:
                        oneof_groups[oneof_name] = []
                    oneof_groups[oneof_name].append((field_name, option_var, wrapper))
                else:
                    # Regular field
                    field_value = self.generate_lines(field_expr, lines, indent)
                    assert field_value is not None
                    pascal_field = to_pascal_case(field_name)

                    # Unwrap Option type for struct field assignment
                    if isinstance(field_expr, Var) and field_expr.type is not None:
                        if isinstance(field_expr.type, OptionType):
                            inner_type = self.gen_type(field_expr.type.element_type)
                            is_nullable = self._is_nullable_go_type(inner_type)
                            if is_nullable:
                                zero = "nil"
                            else:
                                zero = self._go_zero_values.get(inner_type, "nil")
                            if is_nullable:
                                if zero == "nil":
                                    pass  # already the right value
                                else:
                                    tmp = gensym()
                                    lines.append(f"{indent}{tmp} := {field_value}")
                                    self.mark_declared(tmp)
                                    lines.append(f"{indent}if {field_value} == nil {{")
                                    lines.append(f"{indent}\t{tmp} = {zero}")
                                    lines.append(f"{indent}}}")
                                    field_value = tmp
                            else:
                                field_value = f"deref({field_value}, {zero})"

                    regular_assignments.append(f"{pascal_field}: {field_value}")

        # Generate struct literal with regular fields only
        fields_code = ', '.join(regular_assignments)
        tmp = gensym()
        lines.append(f"{indent}{self.gen_assignment(tmp, f'&pb.{expr.name}{{{fields_code}}}', is_declaration=True)}")

        # Generate conditional assignments for oneof fields
        # For each oneof group, check which variant is present and assign it
        for oneof_name, variants in oneof_groups.items():
            pascal_oneof = to_pascal_case(oneof_name)
            if len(variants) == 1:
                # Single variant - assign directly
                field_name, option_var, wrapper = variants[0]
                lines.append(f"{indent}{tmp}.{pascal_oneof} = {wrapper}")
            else:
                # Multiple variants - generate if-else chain checking which one is valid
                for i, (field_name, option_var, wrapper) in enumerate(variants):
                    if i == 0:
                        lines.append(f"{indent}if {option_var} != nil {{")
                    elif i == len(variants) - 1:
                        lines.append(f"{indent}}} else {{")
                    else:
                        lines.append(f"{indent}}} else if {option_var} != nil {{")
                    lines.append(f"{indent}\t{tmp}.{pascal_oneof} = {wrapper}")
                lines.append(f"{indent}}}")

        return tmp

    def _generate_call(self, expr: Call, lines: List[str], indent: str) -> Optional[str]:
        """Override to handle OneOf, Parse/PrintNonterminal, NamedFun, and option builtins for Go."""
        from .target import NamedFun, FunctionType, ListType, BaseType, Builtin, OptionType

        # Intercept option-related builtins to use pointer/nil idioms
        if isinstance(expr.func, Builtin) and expr.func.name in (
            'some', 'is_some', 'is_none', 'unwrap_option', 'unwrap_option_or',
        ):
            return self._generate_option_builtin(expr, lines, indent)

        # Check for Call(OneOf(Symbol), [value]) pattern (not in Message constructor)
        if isinstance(expr.func, OneOf) and len(expr.args) == 1:
            # This case shouldn't normally happen outside of NewMessage,
            # but handle it by just returning the value
            field_value = self.generate_lines(expr.args[0], lines, indent)
            return field_value

        # Check for Parse/PrintNonterminal calls
        if isinstance(expr.func, (ParseNonterminal, PrintNonterminal)):
            f = self.generate_lines(expr.func, lines, indent)
            args: List[str] = []
            for arg in expr.args:
                arg_code = self.generate_lines(arg, lines, indent)
                assert arg_code is not None, "Function argument should not contain a return"
                args.append(arg_code)
            args_code = ', '.join(args)
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'{f}({args_code})', is_declaration=True)}")
            return tmp

        # Handle NamedFun calls - infer list element types from parameter types
        if isinstance(expr.func, NamedFun) and isinstance(expr.func.type, FunctionType):
            func_type = expr.func.type
            args: List[str] = []
            for i, arg in enumerate(expr.args):
                # Check if arg is a ListExpr with Unknown element type
                if isinstance(arg, ListExpr) and isinstance(arg.element_type, BaseType):
                    if arg.element_type.name in ('Unknown', 'Never'):
                        # Try to get expected type from parameter
                        if i < len(func_type.param_types):
                            param_type = func_type.param_types[i]
                            if isinstance(param_type, ListType):
                                # Generate list with correct element type
                                arg_code = self.gen_list_literal([], param_type.element_type)
                                args.append(arg_code)
                                continue
                arg_code = self.generate_lines(arg, lines, indent)
                assert arg_code is not None, "Function argument should not contain a return"
                args.append(arg_code)

            # Generate the function call
            assert isinstance(expr.func, NamedFun)
            func_name = f"p.{self.escape_identifier(expr.func.name)}"
            args_code = ', '.join(args)
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'{func_name}({args_code})', is_declaration=True)}")
            return tmp

        # Fall back to base implementation
        return super()._generate_call(expr, lines, indent)

    def _generate_option_builtin(self, expr: Call, lines: List[str], indent: str) -> Optional[str]:
        """Generate Go code for option-related builtins using pointer/nil idioms."""
        from .target import Builtin, OptionType
        from .codegen_base import BuiltinResult

        assert isinstance(expr.func, Builtin)
        name = expr.func.name

        if name in ('is_none', 'is_some'):
            assert len(expr.args) == 1
            arg_code = self.generate_lines(expr.args[0], lines, indent)
            assert arg_code is not None
            if name == 'is_none':
                return f"{arg_code} == nil"
            return f"{arg_code} != nil"

        if name == 'some':
            assert len(expr.args) == 1
            arg = expr.args[0]
            arg_code = self.generate_lines(arg, lines, indent)
            assert arg_code is not None
            # Determine if the arg type is already nullable
            try:
                arg_type = arg.target_type()
                go_type = self.gen_type(arg_type)
                if self._is_nullable_go_type(go_type):
                    return arg_code
            except (NotImplementedError, ValueError, TypeError):
                pass
            return f"ptr({arg_code})"

        if name == 'unwrap_option':
            assert len(expr.args) == 1
            arg = expr.args[0]
            arg_code = self.generate_lines(arg, lines, indent)
            assert arg_code is not None
            # Determine if collapsed nullable (no deref needed) or ptr-wrapped
            try:
                arg_type = arg.target_type()
                if isinstance(arg_type, OptionType):
                    inner_go = self.gen_type(arg_type.element_type)
                    if self._is_nullable_go_type(inner_go):
                        return arg_code
                else:
                    # Non-OptionType (e.g., oneof fields): check if the Go
                    # type is already nullable, in which case no deref needed.
                    go_type = self.gen_type(arg_type)
                    if self._is_nullable_go_type(go_type):
                        return arg_code
            except (NotImplementedError, ValueError, TypeError):
                pass
            return f"*{arg_code}"

        if name == 'unwrap_option_or':
            assert len(expr.args) == 2
            opt_arg = expr.args[0]
            default_arg = expr.args[1]
            opt_code = self.generate_lines(opt_arg, lines, indent)
            assert opt_code is not None
            default_code = self.generate_lines(default_arg, lines, indent)
            assert default_code is not None
            # Determine if collapsed or ptr-wrapped
            try:
                opt_type = opt_arg.target_type()
                if isinstance(opt_type, OptionType):
                    inner_go = self.gen_type(opt_type.element_type)
                    if not self._is_nullable_go_type(inner_go):
                        # Ptr-wrapped scalar: use deref()
                        return f"deref({opt_code}, {default_code})"
                    # Collapsed nullable: inline if-else with temp
                    tmp = gensym()
                    lines.append(f"{indent}{tmp} := {opt_code}")
                    self.mark_declared(tmp)
                    lines.append(f"{indent}if {opt_code} == nil {{")
                    lines.append(f"{indent}\t{tmp} = {default_code}")
                    lines.append(f"{indent}}}")
                    return tmp
            except (NotImplementedError, ValueError, TypeError):
                pass
            # Fallback: use deref (assumes ptr-wrapped)
            return f"deref({opt_code}, {default_code})"

        # Should not reach here
        return super()._generate_call(expr, lines, indent)

    def _generate_oneof(self, expr: OneOf, lines: List[str], indent: str) -> str:
        """Generate Go OneOf reference.

        OneOf should only appear as the function in Call(OneOf(...), [value]).
        This method shouldn't normally be called.
        """
        raise ValueError(f"OneOf should only appear in Call(OneOf(...), [value]) pattern: {expr}")

    def _generate_return(self, expr, lines: List[str], indent: str) -> None:
        """Generate Go return statement, wrapping with ptr() for Option types when needed."""
        from .target import Lit, Call, Builtin

        expr_code = self.generate_lines(expr.expr, lines, indent)
        assert expr_code is not None, "Return expression should not itself contain a return"

        # Wrap return value with ptr() if returning a ptr-wrapped Option scalar
        if self._current_return_is_option and self._current_return_option_needs_ptr:
            # Don't wrap Lit(None) — that becomes nil
            if isinstance(expr.expr, Lit) and expr.expr.value is None:
                pass
            # Don't wrap if calling some/none builtin (already handled)
            elif (isinstance(expr.expr, Call) and isinstance(expr.expr.func, Builtin) and
                    expr.expr.func.name in ('some', 'none')):
                pass
            # Don't wrap if already a ptr() call
            elif expr_code.startswith("ptr("):
                pass
            else:
                expr_code = f"ptr({expr_code})"

        lines.append(f"{indent}{self.gen_return(expr_code)}")
        return None

    def _generate_assign(self, expr, lines: List[str], indent: str) -> str:
        """Generate Go assignment, handling type-annotated nil declarations.

        In Go, `var_name := nil` is not valid because nil has no type.
        When the value is Lit(None) and the variable has a known type,
        generate a proper var declaration instead.
        """
        from .target import Assign, Lit
        var_name = self.escape_identifier(expr.var.name)

        # Check for nil assignment with known type
        if isinstance(expr.expr, Lit) and expr.expr.value is None:
            # Use proper var declaration with type
            var_type = self.gen_type(expr.var.type) if expr.var.type else "interface{}"
            lines.append(f"{indent}var {var_name} {var_type}")
            self.mark_declared(var_name)
            return self.gen_none()

        # Regular assignment
        expr_code = self.generate_lines(expr.expr, lines, indent)
        assert expr_code is not None, "Assignment expression should not contain a return"
        lines.append(f"{indent}{self.gen_assignment(var_name, expr_code)}")
        return self.gen_none()

    def _generate_parse_def(self, expr: ParseNonterminalDef, indent: str) -> str:
        """Generate a parse method definition."""
        self.reset_declared_vars()

        func_name = f"parse_{expr.nonterminal.name}"

        params = []
        for param in expr.params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            params.append((escaped_name, type_hint))
            self.mark_declared(escaped_name)

        ret_type = self.gen_type(expr.return_type) if expr.return_type else "interface{}"
        self.set_current_return_type(ret_type, expr.return_type)

        header = self.gen_func_def_header(func_name, params, ret_type, is_method=True)

        if expr.body is None:
            zero = self._go_zero_values.get(ret_type, "nil")
            body_code = f"{indent}{self.indent_str}return {zero}"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(expr.body, body_lines, indent + self.indent_str)
            if body_inner is not None:
                body_lines.append(f"{indent}{self.indent_str}return {body_inner}")
            body_code = "\n".join(body_lines)

        self.set_current_return_type(None)

        end = self.gen_func_def_end()
        return f"{indent}{header}\n{body_code}\n{indent}{end}"

    def _generate_pretty_def(self, expr: PrintNonterminalDef, indent: str) -> str:
        """Generate a pretty-print method definition."""
        self.reset_declared_vars()

        func_name = f"pretty_{expr.nonterminal.name}"

        params = []
        for param in expr.params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            params.append((escaped_name, type_hint))
            self.mark_declared(escaped_name)

        ret_type = self.gen_type(expr.return_type) if expr.return_type else "interface{}"
        self.set_current_return_type(ret_type, expr.return_type)

        header = self.gen_func_def_header(func_name, params, ret_type, is_method=True)

        if expr.body is None:
            zero = self._go_zero_values.get(ret_type, "nil")
            body_code = f"{indent}{self.indent_str}return {zero}"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(expr.body, body_lines, indent + self.indent_str)
            if body_inner is not None:
                body_lines.append(f"{indent}{self.indent_str}return {body_inner}")
            body_code = "\n".join(body_lines)

        self.set_current_return_type(None)

        end = self.gen_func_def_end()
        return f"{indent}{header}\n{body_code}\n{indent}{end}"

    def format_literal_token_spec(self, escaped_literal: str) -> str:
        return f'\t\t{{"LITERAL", regexp.MustCompile(`^{escaped_literal}`), func(s string) TokenValue {{ return stringTokenValue(s) }}}},'

    # Map from token name to the TokenValue wrapper function
    _token_value_wrappers = {
        'SYMBOL': ('scanSymbol', 'stringTokenValue'),
        'STRING': ('scanString', 'stringTokenValue'),
        'INT': ('scanInt', 'intTokenValue'),
        'FLOAT': ('scanFloat', 'floatTokenValue'),
        'UINT128': ('scanUint128', 'uint128TokenValue'),
        'INT128': ('scanInt128', 'int128TokenValue'),
        'DECIMAL': ('scanDecimal', 'decimalTokenValue'),
    }

    def format_named_token_spec(self, token_name: str, token_pattern: str) -> str:
        escaped_pattern = token_pattern.replace('`', '` + "`" + `')
        if not escaped_pattern.startswith('^'):
            escaped_pattern = '^' + escaped_pattern
        scan_func, wrapper_func = self._token_value_wrappers.get(
            token_name,
            (f'scan{token_name.capitalize()}', 'stringTokenValue'),
        )
        return f'\t\t{{"{token_name}", regexp.MustCompile(`{escaped_pattern}`), func(s string) TokenValue {{ return {wrapper_func}({scan_func}(s)) }}}},'

    def format_command_line_comment(self, command_line: str) -> str:
        return f"Command: {command_line}"

    def generate_method_def(self, expr: FunDef, indent: str) -> str:
        """Generate a function definition as a method on Parser."""
        self.reset_declared_vars()

        func_name = self.escape_identifier(expr.name)
        params = []
        for param in expr.params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            params.append((escaped_name, type_hint))
            self.mark_declared(escaped_name)

        ret_type = self.gen_type(expr.return_type) if expr.return_type else "interface{}"
        self.set_current_return_type(ret_type, expr.return_type)

        header = self.gen_func_def_header(func_name, params, ret_type, is_method=True)

        if expr.body is None:
            zero = self._go_zero_values.get(ret_type, "nil")
            body_code = f"{indent}{self.indent_str}return {zero}"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(expr.body, body_lines, indent + self.indent_str)
            if body_inner is not None:
                body_lines.append(f"{indent}{self.indent_str}return {body_inner}")
            body_code = "\n".join(body_lines)

        self.set_current_return_type(None)

        end = self.gen_func_def_end()
        return f"{indent}{header}\n{body_code}\n{indent}{end}"


def escape_identifier(name: str) -> str:
    """Escape a Go identifier if it's a keyword."""
    if name in GO_KEYWORDS:
        return f"{name}_"
    return name


def generate_go_type(typ) -> str:
    """Generate Go type annotation from a Type expression."""
    return GoCodeGenerator().gen_type(typ)


def generate_go_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> Optional[str]:
    """Generate Go code from a target IR expression."""
    return GoCodeGenerator().generate_lines(expr, lines, indent)


def generate_go_def(expr: Union[FunDef, ParseNonterminalDef, PrintNonterminalDef], indent: str = "") -> str:
    """Generate Go function definition."""
    return GoCodeGenerator().generate_def(expr, indent)


__all__ = [
    'escape_identifier',
    'generate_go_lines',
    'generate_go_def',
    'generate_go_type',
    'GO_KEYWORDS',
    'GoCodeGenerator',
    'to_pascal_case',
]
