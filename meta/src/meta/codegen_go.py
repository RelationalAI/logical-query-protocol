"""Code generation for Go from semantic action AST.

This module generates Go code from semantic action expressions,
with proper keyword escaping and idiomatic Go style.
"""

from .codegen_base import PARSER_CONFIG, CodegenConfig, CodeGenerator
from .codegen_templates import GO_TEMPLATES
from .gensym import gensym
from .target import (
    Call,
    FunDef,
    GetElement,
    Let,
    ListExpr,
    NewMessage,
    OneOf,
    ParseNonterminal,
    ParseNonterminalDef,
    PrintNonterminal,
    PrintNonterminalDef,
    Seq,
    TargetExpr,
    TargetType,
)

# Go keywords that need escaping
GO_KEYWORDS: set[str] = {
    "break",
    "case",
    "chan",
    "const",
    "continue",
    "default",
    "defer",
    "else",
    "fallthrough",
    "for",
    "func",
    "go",
    "goto",
    "if",
    "import",
    "interface",
    "map",
    "package",
    "range",
    "return",
    "select",
    "struct",
    "switch",
    "type",
    "var",
}


def to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase for Go field/type names."""
    parts = name.split("_")
    return "".join(part.capitalize() for part in parts)


class GoCodeGenerator(CodeGenerator):
    """Go code generator.

    Tracks declared variables to generate proper Go variable declarations.
    In Go, first use of a variable requires := (short declaration) and
    subsequent uses require = (assignment).
    """

    keywords = GO_KEYWORDS
    indent_str = "\t"

    base_type_map = {
        "Int32": "int32",
        "Int64": "int64",
        "UInt32": "uint32",
        "UInt64": "uint64",
        "Float32": "float32",
        "Float64": "float64",
        "String": "string",
        "Boolean": "bool",
        "Bytes": "[]byte",
        "Void": "interface{}",
        "Never": "interface{}",
        "None": "interface{}",
        "Any": "interface{}",
        "Symbol": "string",
        "Unknown": "interface{}",
        "EOF": "interface{}",
        # Python-ish names that might appear
        "int": "int64",
        "float": "float64",
        "str": "string",
        "bool": "bool",
        "bytes": "[]byte",
    }

    # Go types that are already nullable (nil-able) without wrapping in a pointer.
    _nullable_prefixes = ("*", "[")

    @staticmethod
    def _is_nullable_go_type(type_str: str) -> bool:
        """Check if a Go type is already nullable (nil represents absent)."""
        return (
            type_str.startswith("*")
            or type_str.startswith("[")
            or type_str.startswith("map[")
            or type_str == "interface{}"
        )

    # Zero values for Go types
    _go_zero_values: dict[str, str] = {
        "int32": "0",
        "int64": "0",
        "float64": "0.0",
        "string": '""',
        "bool": "false",
        "[]byte": "nil",
    }

    def __init__(self, proto_messages=None, config: CodegenConfig = PARSER_CONFIG):
        super().__init__(proto_messages, config)
        self._oneof_field_to_parent = self._build_oneof_field_map()
        self._declared_vars: set[str] = set()
        self._current_return_type: str | None = None
        self._current_return_is_option: bool = False
        self._current_return_option_needs_ptr: bool = False
        self._lambda_return_type_stack: list[str | None] = []
        self._register_builtins()

    def reset_declared_vars(self) -> None:
        """Reset the set of declared variables. Call at start of each function."""
        self._declared_vars = set()

    def set_current_return_type(
        self, return_type: str | None, return_target_type: TargetType | None = None
    ) -> None:
        """Set the current function's return type for zero value generation."""
        from .target import OptionType

        self._current_return_type = return_type
        if return_target_type is not None and isinstance(
            return_target_type, OptionType
        ):
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

        def none_generator(
            args: list[str], lines: list[str], indent: str
        ) -> BuiltinResult:
            return BuiltinResult("nil", [])

        self.register_builtin("none", none_generator)

        # 'consume_terminal' builtin - returns typed value from Token
        # Map terminal names to Go types for type assertion
        terminal_field_map = {
            "INT": "i64",
            "FLOAT": "f64",
            "STRING": "str",
            "SYMBOL": "str",
            "DECIMAL": "decimal",
            "INT128": "int128",
            "UINT128": "uint128",
        }

        def consume_terminal_generator(
            args: list[str], lines: list[str], indent: str
        ) -> BuiltinResult:
            if len(args) != 1:
                return BuiltinResult("p.consumeTerminal()", [])
            terminal_arg = args[0]
            terminal_name = terminal_arg.strip('"')
            field = terminal_field_map.get(terminal_name, "str")
            return BuiltinResult(f"p.consumeTerminal({terminal_arg}).Value.{field}", [])

        self.register_builtin("consume_terminal", consume_terminal_generator)

    def escape_keyword(self, name: str) -> str:
        return f"{name}_"

    # --- Literal generation ---

    def gen_none(self) -> str:
        # For Option return types (now pointer or collapsed nullable), nil works
        if self._current_return_is_option:
            return "nil"
        # For primitive return types, use zero value
        if (
            self._current_return_type
            and self._current_return_type in self._go_zero_values
        ):
            return self._go_zero_values[self._current_return_type]
        return "nil"

    def gen_bool(self, value: bool) -> str:
        return "true" if value else "false"

    def gen_string(self, value: str) -> str:
        # Go uses double quotes for strings
        # Escape backslashes, double quotes, and newlines
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        escaped = escaped.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
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

    def gen_tuple_type(self, element_types: list[str]) -> str:
        # Go doesn't have tuples, use a struct or interface slice
        return "[]interface{}"

    def gen_sequence_type(self, element_type: str) -> str:
        return f"[]{element_type}"

    def gen_list_type(self, element_type: str) -> str:
        return f"[]{element_type}"

    def gen_option_type(self, element_type: str) -> str:
        if self._is_nullable_go_type(element_type):
            return element_type
        return f"*{element_type}"

    def gen_list_literal(self, elements: list[str], element_type: TargetType) -> str:
        from .target import BaseType

        # For empty lists with unknown element type, use nil (Go infers the type from context)
        if not elements:
            if isinstance(element_type, BaseType) and element_type.name in (
                "Unknown",
                "Never",
                "Any",
            ):
                return "nil"
            type_code = self.gen_type(element_type)
            return "[]" + type_code + "{}"
        type_code = self.gen_type(element_type)
        return "[]" + type_code + "{" + ", ".join(elements) + "}"

    def gen_dict_type(self, key_type: str, value_type: str) -> str:
        return f"map[{key_type}]{value_type}"

    def gen_function_type(self, param_types: list[str], return_type: str) -> str:
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

    def gen_foreach_enumerated_start(
        self, index_var: str, var: str, collection: str
    ) -> str:
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

    def gen_var_declaration(self, var: str, type_hint: str | None = None) -> str:
        # Go needs a type or initial value
        # Mark as declared so subsequent assignments use = instead of :=
        self.mark_declared(var)
        if type_hint:
            return f"var {var} {type_hint}"
        return f"var {var} interface{{}}"

    # --- Lambda and function definition syntax ---

    def gen_lambda_start(
        self, params: list[tuple[str, str | None]], return_type: str | None
    ) -> tuple[str, str]:
        params_str = (
            ", ".join(f"{n} {t if t else 'interface{}'}" for n, t in params)
            if params
            else ""
        )
        ret = return_type if return_type else "interface{}"
        return (f"__FUNC__ := func({params_str}) {ret} {{", "}")

    def gen_func_def_header(
        self,
        name: str,
        params: list[tuple[str, str]],
        return_type: str | None,
        is_method: bool = False,
    ) -> str:
        params_str = ", ".join(f"{n} {t}" for n, t in params)
        ret = f" {return_type}" if return_type else ""
        if is_method:
            return f"func (p *{self.config.receiver_type}) {name}({params_str}){ret} {{"
        return f"func {name}({params_str}){ret} {{"

    def gen_func_def_end(self) -> str:
        return "}"

    def _generate_Lambda(self, expr, lines: list[str], indent: str) -> str:
        """Track lambda return type for IfElse type hint inference."""
        from .target import Lambda

        assert isinstance(expr, Lambda)
        ret_type = (
            self.gen_type(expr.return_type)
            if expr.return_type and not self._is_void_type(expr.return_type)
            else None
        )
        self._lambda_return_type_stack.append(ret_type)
        try:
            result = super()._generate_Lambda(expr, lines, indent)
        finally:
            self._lambda_return_type_stack.pop()
        return result

    def _ifelse_type_hint(self, expr) -> str | None:
        """Improve IfElse type hint when the overall type resolves to interface{}.

        When the IfElse type has unresolved type variables (yielding interface{}),
        use the enclosing lambda's return type as a better hint.
        """
        hint = super()._ifelse_type_hint(expr)
        if hint == "interface{}" and self._lambda_return_type_stack:
            lambda_ret = self._lambda_return_type_stack[-1]
            if lambda_ret is not None and lambda_ret != "interface{}":
                return lambda_ret
        return hint

    def _generate_nil_else_branch(
        self,
        tmp: str,
        lines: list[str],
        indent: str,
        body_indent: str,
    ) -> str:
        """Go's var declarations zero-initialize, so no else branch needed."""
        return self.gen_none()

    def _generate_GetElement(
        self, expr: GetElement, lines: list[str], indent: str
    ) -> str:
        """Go uses 0-based indexing with type assertion for tuple elements.

        Type assertions are only needed when the container is []interface{}
        (Go tuple). For typed slices (protobuf repeated fields), the element
        type is already correct and assertion would fail.
        """
        from .target import ListType, SequenceType

        tuple_code = self.generate_lines(expr.tuple_expr, lines, indent)
        # Check if the container is a typed slice (no assertion needed)
        try:
            container_type = expr.tuple_expr.target_type()
            if isinstance(container_type, (SequenceType, ListType)):
                return f"{tuple_code}[{expr.index}]"
        except (NotImplementedError, ValueError, TypeError):
            pass
        # For tuples ([]interface{}), add type assertion
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

    def _generate_GetField(self, expr, lines: list[str], indent: str) -> str:
        if self._is_optional_scalar_field(expr):
            obj_code = self.generate_lines(expr.object, lines, indent)
            assert obj_code is not None
            pascal_field = to_pascal_case(expr.field_name)
            return f"{obj_code}.{pascal_field}"
        return super()._generate_GetField(expr, lines, indent)

    def _generate_Let(self, expr: Let, lines: list[str], indent: str) -> str | None:
        """Generate Go let binding, suppressing unused variable errors."""
        var_name = self.escape_identifier(expr.var.name)
        init_val = self.generate_lines(expr.init, lines, indent)
        assert init_val is not None, "Let initializer should not contain a return"
        lines.append(
            f"{indent}{self.gen_assignment(var_name, init_val, is_declaration=True)}"
        )
        body_start = len(lines)
        result = self.generate_lines(expr.body, lines, indent)
        # Suppress unused variable if the body didn't reference it.
        body_lines = lines[body_start:]
        var_used = any(var_name in line for line in body_lines) or result == var_name
        if not var_used:
            lines.insert(body_start, f"{indent}_ = {var_name}")
        return result

    def _generate_Seq(self, expr: Seq, lines: list[str], indent: str) -> str | None:
        """Generate Go sequence, suppressing unused variable errors.

        In Go, declared-but-unused variables are compile errors. When an
        intermediate expression in a Seq produces a temp variable (e.g., from
        an IfElse used for side effects), we emit `_ = var` to suppress it.
        """
        result: str | None = self.gen_none()
        for i, e in enumerate(expr.exprs):
            result = self.generate_lines(e, lines, indent)
            if result is None:
                break
            # Suppress unused temp variable from non-final expressions
            if (
                i < len(expr.exprs) - 1
                and result is not None
                and result.startswith("_t")
            ):
                lines.append(f"{indent}_ = {result}")
        return result

    def _generate_NewMessage(
        self, expr: NewMessage, lines: list[str], indent: str
    ) -> str:
        """Generate Go code for NewMessage with fields containing OneOf calls.

        In Go protobuf, OneOf fields require wrapping values in the appropriate
        wrapper struct. Multiple OneOf variants in the same group are generated
        as conditional assignments after the struct literal (since only one can be set).
        """
        if not expr.fields:
            # No fields - return constructor directly
            tmp = gensym()
            lines.append(
                f"{indent}{self.gen_assignment(tmp, f'&pb.{expr.name}{{}}', is_declaration=True)}"
            )
            return tmp

        # Separate regular fields from oneof fields
        regular_assignments = []
        # Group oneof fields by their parent oneof name: {oneof_name: [(field_name, option_var, wrapper_code)]}
        # option_var is the original Option variable name for checking .Valid
        oneof_groups: dict[str, list[tuple[str, str, str]]] = {}

        from .target import OptionType, Var

        def unwrap_if_option(field_expr, field_value: str) -> tuple[str, str]:
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
            if (
                isinstance(field_expr, Call)
                and isinstance(field_expr.func, OneOf)
                and len(field_expr.args) == 1
            ):
                # OneOf field with explicit wrapper
                oneof_field_name = field_expr.func.field_name
                oneof_arg = field_expr.args[0]
                field_value = self.generate_lines(oneof_arg, lines, indent)
                assert field_value is not None
                # Unwrap if the argument is an Option type
                option_var, unwrapped = unwrap_if_option(oneof_arg, field_value)

                pascal_field = to_pascal_case(oneof_field_name)
                wrapper = (
                    f"&pb.{expr.name}_{pascal_field}{{{pascal_field}: {unwrapped}}}"
                )

                # field_name here is the oneof parent name
                oneof_name = field_name
                if oneof_name not in oneof_groups:
                    oneof_groups[oneof_name] = []
                oneof_groups[oneof_name].append((oneof_field_name, option_var, wrapper))
            else:
                # Check if this field is a OneOf variant using proto schema info
                oneof_info = self._oneof_field_to_parent.get(
                    (expr.module, expr.name, field_name)
                )
                if oneof_info is not None:
                    # This field is a OneOf variant
                    oneof_name, _field_type = oneof_info
                    field_value = self.generate_lines(field_expr, lines, indent)
                    assert field_value is not None
                    # Unwrap if the value is an Option type
                    option_var, unwrapped = unwrap_if_option(field_expr, field_value)

                    pascal_field = to_pascal_case(field_name)
                    wrapper = (
                        f"&pb.{expr.name}_{pascal_field}{{{pascal_field}: {unwrapped}}}"
                    )

                    if oneof_name not in oneof_groups:
                        oneof_groups[oneof_name] = []
                    oneof_groups[oneof_name].append((field_name, option_var, wrapper))
                else:
                    # Regular field
                    field_value = self.generate_lines(field_expr, lines, indent)
                    assert field_value is not None
                    pascal_field = to_pascal_case(field_name)
                    _, field_value = unwrap_if_option(field_expr, field_value)
                    regular_assignments.append(f"{pascal_field}: {field_value}")

        # Generate struct literal with regular fields only
        fields_code = ", ".join(regular_assignments)
        tmp = gensym()
        lines.append(
            f"{indent}{self.gen_assignment(tmp, f'&pb.{expr.name}{{{fields_code}}}', is_declaration=True)}"
        )

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

    def _generate_Call(self, expr: Call, lines: list[str], indent: str) -> str | None:
        """Override to handle OneOf, Parse/PrintNonterminal, NamedFun, and option builtins for Go."""
        from .target import (
            BaseType,
            Builtin,
            FunctionType,
            ListType,
            NamedFun,
        )

        # Intercept option-related builtins to use pointer/nil idioms
        if isinstance(expr.func, Builtin) and expr.func.name in (
            "some",
            "is_some",
            "is_none",
            "unwrap_option",
            "unwrap_option_or",
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
            args: list[str] = []
            for arg in expr.args:
                arg_code = self.generate_lines(arg, lines, indent)
                assert arg_code is not None, (
                    "Function argument should not contain a return"
                )
                args.append(arg_code)
            args_code = ", ".join(args)
            if self._is_void_expr(expr):
                lines.append(f"{indent}{f}({args_code})")
                return self.gen_none()
            tmp = gensym()
            lines.append(
                f"{indent}{self.gen_assignment(tmp, f'{f}({args_code})', is_declaration=True)}"
            )
            return tmp

        # Handle NamedFun calls - infer list element types from parameter types
        if isinstance(expr.func, NamedFun) and isinstance(expr.func.type, FunctionType):
            func_type = expr.func.type
            args: list[str] = []
            for i, arg in enumerate(expr.args):
                # Check if arg is a ListExpr with Unknown element type
                if isinstance(arg, ListExpr) and isinstance(arg.element_type, BaseType):
                    if arg.element_type.name in ("Unknown", "Never"):
                        # Try to get expected type from parameter
                        if i < len(func_type.param_types):
                            param_type = func_type.param_types[i]
                            if isinstance(param_type, ListType):
                                # Generate list with correct element type
                                arg_code = self.gen_list_literal(
                                    [], param_type.element_type
                                )
                                args.append(arg_code)
                                continue
                arg_code = self.generate_lines(arg, lines, indent)
                assert arg_code is not None, (
                    "Function argument should not contain a return"
                )
                args.append(arg_code)

            # Generate the function call
            assert isinstance(expr.func, NamedFun)
            func_name = f"p.{self.escape_identifier(expr.func.name)}"
            args_code = ", ".join(args)
            tmp = gensym()
            lines.append(
                f"{indent}{self.gen_assignment(tmp, f'{func_name}({args_code})', is_declaration=True)}"
            )
            return tmp

        # Fall back to base implementation
        return super()._generate_Call(expr, lines, indent)

    def _generate_option_builtin(
        self, expr: Call, lines: list[str], indent: str
    ) -> str | None:
        """Generate Go code for option-related builtins using pointer/nil idioms."""
        from .target import Builtin, OptionType

        assert isinstance(expr.func, Builtin)
        name = expr.func.name

        if name in ("is_none", "is_some"):
            assert len(expr.args) == 1
            arg_code = self.generate_lines(expr.args[0], lines, indent)
            assert arg_code is not None
            if name == "is_none":
                return f"{arg_code} == nil"
            return f"{arg_code} != nil"

        if name == "some":
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

        if name == "unwrap_option":
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
                    # Non-OptionType: return as-is (no deref needed).
                    return arg_code
            except (NotImplementedError, ValueError, TypeError):
                pass
            return f"*{arg_code}"

        if name == "unwrap_option_or":
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
        return super()._generate_Call(expr, lines, indent)

    def _generate_OneOf(self, expr: OneOf, lines: list[str], indent: str) -> str:
        """Generate Go OneOf reference.

        OneOf should only appear as the function in Call(OneOf(...), [value]).
        This method shouldn't normally be called.
        """
        raise ValueError(
            f"OneOf should only appear in Call(OneOf(...), [value]) pattern: {expr}"
        )

    def _generate_Return(self, expr, lines: list[str], indent: str) -> None:
        """Generate Go return statement, wrapping with ptr() for Option types when needed."""
        from .target import Builtin, Call, Lit

        expr_code = self.generate_lines(expr.expr, lines, indent)
        assert expr_code is not None, (
            "Return expression should not itself contain a return"
        )

        # Wrap return value with ptr() if returning a ptr-wrapped Option scalar
        if self._current_return_is_option and self._current_return_option_needs_ptr:
            # Don't wrap Lit(None) — that becomes nil
            if isinstance(expr.expr, Lit) and expr.expr.value is None:
                pass
            # Don't wrap if calling some/none builtin (already handled)
            elif (
                isinstance(expr.expr, Call)
                and isinstance(expr.expr.func, Builtin)
                and expr.expr.func.name in ("some", "none")
            ):
                pass
            # Don't wrap if already a ptr() call
            elif expr_code.startswith("ptr("):
                pass
            else:
                expr_code = f"ptr({expr_code})"

        lines.append(f"{indent}{self.gen_return(expr_code)}")
        return None

    def _generate_Assign(self, expr, lines: list[str], indent: str) -> str:
        """Generate Go assignment, handling type-annotated nil declarations.

        In Go, `var_name := nil` is not valid because nil has no type.
        When the value is Lit(None) and the variable has a known type,
        generate a proper var declaration instead.
        """
        from .target import Lit

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
        assert expr_code is not None, (
            "Assignment expression should not contain a return"
        )
        lines.append(f"{indent}{self.gen_assignment(var_name, expr_code)}")
        return self.gen_none()

    def _pre_method_def(self, params) -> None:
        self.reset_declared_vars()
        for p in params:
            self.mark_declared(self.escape_identifier(p.name))

    def _post_method_header(self, ret_type_str, return_type) -> None:
        self.set_current_return_type(ret_type_str, return_type)

    def _post_method_def(self) -> None:
        self.set_current_return_type(None)

    def _method_return_type(self, return_type) -> str | None:
        return self.gen_type(return_type) if return_type else "interface{}"

    def _gen_method_empty_body(self, ret_type_str, indent) -> str:
        zero = self._go_zero_values.get(ret_type_str or "", "nil")
        return f"{indent}{self.indent_str}return {zero}"

    def format_literal_token_spec(self, escaped_literal: str) -> str:
        return f'\t\t{{"LITERAL", regexp.MustCompile(`^{escaped_literal}`), func(s string) TokenValue {{ return TokenValue{{kind: kindString, str: s}} }}}},'

    # Map from token name to (scan function, kind, field) for TokenValue construction
    _token_value_specs = {
        "SYMBOL": ("scanSymbol", "kindString", "str"),
        "STRING": ("scanString", "kindString", "str"),
        "INT": ("scanInt", "kindInt64", "i64"),
        "FLOAT": ("scanFloat", "kindFloat64", "f64"),
        "UINT128": ("scanUint128", "kindUint128", "uint128"),
        "INT128": ("scanInt128", "kindInt128", "int128"),
        "DECIMAL": ("scanDecimal", "kindDecimal", "decimal"),
    }

    def format_named_token_spec(self, token_name: str, token_pattern: str) -> str:
        escaped_pattern = token_pattern.replace("`", '` + "`" + `')
        if not escaped_pattern.startswith("^"):
            escaped_pattern = "^" + escaped_pattern
        scan_func, kind, field = self._token_value_specs.get(
            token_name,
            (f"scan{token_name.capitalize()}", "kindString", "str"),
        )
        return f'\t\t{{"{token_name}", regexp.MustCompile(`{escaped_pattern}`), func(s string) TokenValue {{ return TokenValue{{kind: {kind}, {field}: {scan_func}(s)}} }}}},'

    def format_command_line_comment(self, command_line: str) -> str:
        return f"Command: {command_line}"

    def gen_dispatch_function(
        self, entries: list[tuple[str, str]], enum_entries: list[tuple[str, str]]
    ) -> str:
        """Generate the Go type-switch pprintDispatch method."""
        lines: list[str] = []
        lines.append("func (p *PrettyPrinter) pprintDispatch(msg interface{}) {")
        lines.append("\tswitch m := msg.(type) {")
        for type_str, func_ref in entries:
            lines.append(f"\tcase {type_str}:")
            lines.append(f"\t\t{func_ref}(m)")
        for enum_type, func_ref in enum_entries:
            lines.append(f"\tcase {enum_type}:")
            lines.append(f"\t\t{func_ref}(m)")
        lines.append("\tdefault:")
        lines.append('\t\tpanic(fmt.Sprintf("no pretty printer for %T", msg))')
        lines.append("\t}")
        lines.append("}")
        return "\n".join(lines)


def escape_identifier(name: str) -> str:
    """Escape a Go identifier if it's a keyword."""
    if name in GO_KEYWORDS:
        return f"{name}_"
    return name


def generate_go_type(typ) -> str:
    """Generate Go type annotation from a Type expression."""
    return GoCodeGenerator().gen_type(typ)


def generate_go_lines(
    expr: TargetExpr, lines: list[str], indent: str = ""
) -> str | None:
    """Generate Go code from a target IR expression."""
    return GoCodeGenerator().generate_lines(expr, lines, indent)


def generate_go_def(
    expr: FunDef | ParseNonterminalDef | PrintNonterminalDef, indent: str = ""
) -> str:
    """Generate Go function definition."""
    return GoCodeGenerator().generate_def(expr, indent)


__all__ = [
    "escape_identifier",
    "generate_go_lines",
    "generate_go_def",
    "generate_go_type",
    "GO_KEYWORDS",
    "GoCodeGenerator",
    "to_pascal_case",
]
