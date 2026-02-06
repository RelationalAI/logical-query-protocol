"""Code generation for Go from semantic action AST.

This module generates Go code from semantic action expressions,
with proper keyword escaping and idiomatic Go style.
"""

from typing import Dict, List, Optional, Set, Tuple, Union

from .codegen_base import CodeGenerator
from .codegen_templates import GO_TEMPLATES
from .target import (
    TargetExpr, Var, Lit, Symbol, NewMessage, OneOf, ListExpr, Call, Lambda, Let,
    FunDef, VisitNonterminalDef, VisitNonterminal, GetElement, GetField, TargetType,
    IfElse, OptionType,
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
        self._register_builtins()

    def reset_declared_vars(self) -> None:
        """Reset the set of declared variables. Call at start of each function."""
        self._declared_vars = set()

    def set_current_return_type(self, return_type: Optional[str]) -> None:
        """Set the current function's return type for zero value generation."""
        self._current_return_type = return_type

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

    def _escape_field_for_map(self, field_name: str) -> str:
        """Escape Go keywords in field names by adding underscore suffix."""
        if field_name in self.keywords:
            return field_name + '_'
        return field_name

    def _register_builtins(self) -> None:
        """Register builtin generators from templates."""
        self.register_builtins_from_templates(GO_TEMPLATES)
        # Override 'none' to use Option zero value when we know the return type
        self._register_none_builtin()

    def _register_none_builtin(self) -> None:
        """Register custom builtins for Go option handling.

        Go uses two representations for optional values:
        - Option[T] for scalars (int, float, string, bool) to distinguish None from zero
        - nil for pointer types and slices (already nullable)

        The builtins need to handle both cases.
        """
        from .codegen_base import BuiltinResult
        from .gensym import gensym

        # 'none' builtin - returns Option[T]{} for scalars or nil for pointers
        def none_generator(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            # If we know the return type is Option[T], use zero value
            if self._current_return_type and self._current_return_type.startswith("Option["):
                return BuiltinResult(f"{self._current_return_type}{{}}", [])
            return BuiltinResult("nil", [])

        self.register_builtin("none", none_generator)

        # 'unwrap_option_or' builtin - uses .UnwrapOr() for Option[T], nil check for pointers
        def unwrap_option_or_generator(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            if len(args) != 2:
                return BuiltinResult(args[0], [])
            opt, default = args[0], args[1]
            # Use the Option.UnwrapOr method - works for Option[T]
            # For pointer types, this won't compile but we handle those separately
            return BuiltinResult(f"{opt}.UnwrapOr({default})", [])

        self.register_builtin("unwrap_option_or", unwrap_option_or_generator)

        # 'consume_terminal' builtin - returns typed value from Token
        # Map terminal names to Go types for type assertion
        terminal_type_map = {
            "INT": "int64",
            "FLOAT": "float64",
            "STRING": "string",
            "SYMBOL": "string",
            "DECIMAL": "*pb.DecimalValue",
            "INT128": "*pb.Int128Value",
            "UINT128": "*pb.UInt128Value",
        }

        def consume_terminal_generator(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            if len(args) != 1:
                return BuiltinResult("p.consumeTerminal()", [])
            terminal_arg = args[0]
            # Extract terminal name from quoted string (e.g., '"INT"' -> 'INT')
            terminal_name = terminal_arg.strip('"')
            go_type = terminal_type_map.get(terminal_name)
            if go_type:
                return BuiltinResult(f"p.consumeTerminal({terminal_arg}).Value.({go_type})", [])
            # Fallback for unknown terminals
            return BuiltinResult(f"p.consumeTerminal({terminal_arg}).Value", [])

        self.register_builtin("consume_terminal", consume_terminal_generator)

    def escape_keyword(self, name: str) -> str:
        return f"{name}_"

    # --- Literal generation ---

    def gen_none(self) -> str:
        # If return type is Option[T], use zero value of Option
        if self._current_return_type and self._current_return_type.startswith("Option["):
            return f"{self._current_return_type}{{}}"
        # For primitive return types, use zero value
        if self._current_return_type and self._current_return_type in self._go_zero_values:
            return self._go_zero_values[self._current_return_type]
        # For pointer/slice types, nil represents None
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

    def gen_list_type(self, element_type: str) -> str:
        return f"[]{element_type}"

    def gen_option_type(self, element_type: str) -> str:
        # Always use Option[T] for consistency and to distinguish None from zero/nil
        return f"Option[{element_type}]"

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

    def gen_lambda_start(self, params: List[str], return_type: Optional[str]) -> Tuple[str, str]:
        params_str = ', '.join(f"{p} interface{{}}" for p in params) if params else ''
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

    def generate_lines(self, expr: TargetExpr, lines: List[str], indent: str = "") -> Optional[str]:
        """Override to handle Go-specific GetField with getter methods."""
        from .target import Var

        if isinstance(expr, GetField):
            # In Go protobuf, field access uses getter methods: obj.GetFieldName()
            obj_code = super().generate_lines(expr.object, lines, indent)
            pascal_field = to_pascal_case(expr.field_name)

            # Check if the object expression might be an Option type
            # If the object is a variable with a type that looks like Option[...],
            # we need to access .Value first
            if isinstance(expr.object, Var) and expr.object.type is not None:
                obj_type = self.gen_type(expr.object.type)
                if obj_type.startswith("Option["):
                    # Access the inner value: opt.Value.GetField()
                    return f"{obj_code}.Value.Get{pascal_field}()"

            return f"{obj_code}.Get{pascal_field}()"

        return super().generate_lines(expr, lines, indent)

    def _generate_if_else(self, expr: IfElse, lines: List[str], indent: str) -> Optional[str]:
        """Generate Go code for if-else with proper Option typing.

        Override base class to handle Option types properly in Go, where we can't
        use interface{} for variables that will have methods called on them.
        """
        cond_code = self.generate_lines(expr.condition, lines, indent)
        assert cond_code is not None, "If condition should not contain a return"

        # Determine the type of this if-else expression
        # Note: target_type() may not be implemented for all expression types,
        # and gen_type() may not handle all type representations
        expr_type = None
        go_type: Optional[str] = None
        is_option_type = False

        try:
            expr_type = expr.target_type()
            if expr_type is not None:
                go_type = self.gen_type(expr_type)
                is_option_type = isinstance(expr_type, OptionType)
                # If the type is Option[Never] or Option[None], it means both branches
                # return None - don't treat as Option, just use nil
                if is_option_type:
                    from .target import BaseType
                    inner = expr_type.element_type
                    if isinstance(inner, BaseType) and inner.name in ('Never', 'None', 'Void'):
                        is_option_type = False
                        go_type = None
        except (NotImplementedError, ValueError):
            # Fall back to interface{} if type determination fails
            pass

        # Detect pattern: one branch is Lit(None), other has a type -> Option[T]
        # This handles cases like: if cond then parse_something() else None
        if not is_option_type:
            non_nil_branch = None
            if expr.else_branch == Lit(None) and expr.then_branch != Lit(None):
                non_nil_branch = expr.then_branch
            elif expr.then_branch == Lit(None) and expr.else_branch != Lit(None):
                non_nil_branch = expr.else_branch

            if non_nil_branch is not None:
                try:
                    branch_type = non_nil_branch.target_type()
                    if branch_type is not None:
                        # Skip Option detection if branch type is already Option[Never/None/Void]
                        if isinstance(branch_type, OptionType):
                            from .target import BaseType
                            inner = branch_type.element_type
                            if isinstance(inner, BaseType) and inner.name in ('Never', 'None', 'Void'):
                                # Both branches effectively return None - don't create Option
                                pass
                            else:
                                # Branch returns a real Option type - use it directly
                                go_type = self.gen_type(branch_type)
                                is_option_type = True
                        else:
                            inner_go_type = self.gen_type(branch_type)
                            go_type = f"Option[{inner_go_type}]"
                            is_option_type = True
                except (NotImplementedError, ValueError):
                    pass

        # Optimization: if then branch returns and else is Lit(None), generate simple if without else.
        if expr.else_branch == Lit(None):
            then_lines: List[str] = []
            then_code = self.generate_lines(expr.then_branch, then_lines, indent + self.indent_str)
            if then_code is None:  # then branch returns
                lines.append(f"{indent}{self.gen_if_start(cond_code)}")
                lines.extend(then_lines)
                lines.append(f"{indent}{self.gen_if_end()}")
                return self.gen_none()

        # Optimization: if else branch returns and then is Lit(None), generate negated if.
        if expr.then_branch == Lit(None):
            else_lines: List[str] = []
            else_code = self.generate_lines(expr.else_branch, else_lines, indent + self.indent_str)
            if else_code is None:  # else branch returns
                # Generate: if !cond { else_branch }
                negated = self.gen_builtin_call("not", [cond_code], lines, indent)
                neg_cond = negated.value if negated else f"!({cond_code})"
                lines.append(f"{indent}{self.gen_if_start(neg_cond)}")
                lines.extend(else_lines)
                lines.append(f"{indent}{self.gen_if_end()}")
                return self.gen_none()

        # Optimization: if both branches return nil and no Option type needed,
        # generate if-else for side effects only without temp variable.
        if not is_option_type and go_type is None:
            then_lines: List[str] = []
            else_lines: List[str] = []
            then_code = self.generate_lines(expr.then_branch, then_lines, indent + self.indent_str)
            else_code = self.generate_lines(expr.else_branch, else_lines, indent + self.indent_str)
            if then_code == "nil" and else_code == "nil":
                lines.append(f"{indent}{self.gen_if_start(cond_code)}")
                lines.extend(then_lines)
                lines.append(f"{indent}{self.gen_else()}")
                lines.extend(else_lines)
                lines.append(f"{indent}{self.gen_if_end()}")
                return "nil"

        tmp = gensym()

        # Use proper type for Option types, otherwise fall back to interface{}
        if go_type and is_option_type:
            lines.append(f"{indent}var {tmp} {go_type}")
            self.mark_declared(tmp)
        else:
            lines.append(f"{indent}{self.gen_var_declaration(tmp, go_type)}")

        lines.append(f"{indent}{self.gen_if_start(cond_code)}")

        body_indent = indent + self.indent_str
        then_code = self.generate_lines(expr.then_branch, lines, body_indent)
        if then_code is not None:
            # Wrap with Some() if the result type is Option and this value is not None/nil
            if is_option_type and then_code != "nil":
                then_code = f"Some({then_code})"
            elif is_option_type and then_code == "nil" and go_type:
                # Convert nil to properly typed empty Option
                then_code = f"{go_type}{{}}"
            lines.append(f"{body_indent}{self.gen_assignment(tmp, then_code)}")

        lines.append(f"{indent}{self.gen_else()}")
        else_code = self.generate_lines(expr.else_branch, lines, body_indent)
        if else_code is not None:
            # Wrap with Some() if the result type is Option and this value is not None/nil
            if is_option_type and else_code != "nil":
                else_code = f"Some({else_code})"
            elif is_option_type and else_code == "nil" and go_type:
                # Convert nil to properly typed empty Option
                else_code = f"{go_type}{{}}"
            lines.append(f"{body_indent}{self.gen_assignment(tmp, else_code)}")

        end = self.gen_if_end()
        if end:
            lines.append(f"{indent}{end}")

        # If both branches returned, propagate None
        if then_code is None and else_code is None:
            return None

        return tmp

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
            Returns (option_var, unwrapped_value) where option_var is for .Valid check."""
            if isinstance(field_expr, Var) and field_expr.type is not None:
                if isinstance(field_expr.type, OptionType):
                    inner_type = self.gen_type(field_expr.type.element_type)
                    if inner_type.startswith('*') or inner_type.startswith('['):
                        zero = "nil"
                    else:
                        zero = self._go_zero_values.get(inner_type, "nil")
                    return (field_value, f"{field_value}.UnwrapOr({zero})")
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

                    # Check if the expression is a variable with Option type - unwrap it
                    if isinstance(field_expr, Var) and field_expr.type is not None:
                        if isinstance(field_expr.type, OptionType):
                            # Unwrap Option with zero value default
                            inner_type = self.gen_type(field_expr.type.element_type)
                            # For pointers and slices, use nil; for scalars use zero value
                            if inner_type.startswith('*') or inner_type.startswith('['):
                                zero = "nil"
                            else:
                                zero = self._go_zero_values.get(inner_type, "nil")
                            field_value = f"{field_value}.UnwrapOr({zero})"

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
                # Use .Valid on the original Option variable
                for i, (field_name, option_var, wrapper) in enumerate(variants):
                    if i == 0:
                        lines.append(f"{indent}if {option_var}.Valid {{")
                    elif i == len(variants) - 1:
                        lines.append(f"{indent}}} else {{")
                    else:
                        lines.append(f"{indent}}} else if {option_var}.Valid {{")
                    lines.append(f"{indent}\t{tmp}.{pascal_oneof} = {wrapper}")
                lines.append(f"{indent}}}")

        return tmp

    def _generate_call(self, expr: Call, lines: List[str], indent: str) -> Optional[str]:
        """Override to handle OneOf, VisitNonterminal, and NamedFun specially for Go."""
        from .target import NamedFun, FunctionType, ListType, BaseType

        # Check for Call(OneOf(Symbol), [value]) pattern (not in Message constructor)
        if isinstance(expr.func, OneOf) and len(expr.args) == 1:
            # This case shouldn't normally happen outside of NewMessage,
            # but handle it by just returning the value
            field_value = self.generate_lines(expr.args[0], lines, indent)
            return field_value

        # Check for VisitNonterminal calls
        if isinstance(expr.func, VisitNonterminal):
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
            func_name = f"p.{self.escape_identifier(expr.func.name)}"
            args_code = ', '.join(args)
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'{func_name}({args_code})', is_declaration=True)}")
            return tmp

        # Fall back to base implementation
        return super()._generate_call(expr, lines, indent)

    def _generate_oneof(self, expr: OneOf, lines: List[str], indent: str) -> str:
        """Generate Go OneOf reference.

        OneOf should only appear as the function in Call(OneOf(...), [value]).
        This method shouldn't normally be called.
        """
        raise ValueError(f"OneOf should only appear in Call(OneOf(...), [value]) pattern: {expr}")

    def _generate_return(self, expr, lines: List[str], indent: str) -> None:
        """Generate Go return statement, wrapping with Some() for Option types."""
        from .target import Lit, Call, Builtin

        expr_code = self.generate_lines(expr.expr, lines, indent)
        assert expr_code is not None, "Return expression should not itself contain a return"

        # Check if returning to Option[T] type and value needs wrapping
        if (self._current_return_type and
            self._current_return_type.startswith("Option[") and
            not isinstance(expr.expr, Lit) or (isinstance(expr.expr, Lit) and expr.expr.value is not None)):
            # Don't wrap if already an Option expression
            if not expr_code.startswith("Some(") and not expr_code.startswith(f"{self._current_return_type}{{"):
                # Don't wrap if calling 'some' or 'none' builtin
                if not (isinstance(expr.expr, Call) and isinstance(expr.expr.func, Builtin) and
                        expr.expr.func.name in ('some', 'none')):
                    expr_code = f"Some({expr_code})"

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

    def _generate_parse_def(self, expr: VisitNonterminalDef, indent: str) -> str:
        """Generate a parse method definition."""
        # Reset declared variables for this function scope
        self.reset_declared_vars()

        func_name = f"parse_{expr.nonterminal.name}"

        params = []
        for param in expr.params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            params.append(f"{escaped_name} {type_hint}")
            # Mark parameters as declared
            self.mark_declared(escaped_name)

        params_str = ', '.join(params)

        ret_type = self.gen_type(expr.return_type) if expr.return_type else "interface{}"
        # Track return type for zero value generation
        self.set_current_return_type(ret_type)

        if expr.body is None:
            zero = self._go_zero_values.get(ret_type, "nil")
            body_code = f"{indent}{self.indent_str}return {zero}"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(expr.body, body_lines, indent + self.indent_str)
            # Only add return if the body didn't already return
            if body_inner is not None:
                body_lines.append(f"{indent}{self.indent_str}return {body_inner}")
            body_code = "\n".join(body_lines)

        # Clear return type after generating
        self.set_current_return_type(None)

        return f"{indent}func (p *Parser) {func_name}({params_str}) {ret_type} {{\n{body_code}\n{indent}}}"

    def _generate_builtin_method_def(self, expr: FunDef, indent: str) -> str:
        """Generate a builtin/helper function definition as a method."""
        # Reset declared variables for this function scope
        self.reset_declared_vars()

        func_name = self.escape_identifier(expr.name)

        params = []
        for param in expr.params:
            escaped_name = self.escape_identifier(param.name)
            type_hint = self.gen_type(param.type)
            params.append(f"{escaped_name} {type_hint}")
            # Mark parameters as declared
            self.mark_declared(escaped_name)

        params_str = ', '.join(params)

        ret_type = self.gen_type(expr.return_type) if expr.return_type else "interface{}"
        # Track return type for zero value generation
        self.set_current_return_type(ret_type)

        if expr.body is None:
            zero = self._go_zero_values.get(ret_type, "nil")
            body_code = f"{indent}{self.indent_str}return {zero}"
        else:
            body_lines: List[str] = []
            body_inner = self.generate_lines(expr.body, body_lines, indent + self.indent_str)
            # Only add return if the body didn't already return
            if body_inner is not None:
                body_lines.append(f"{indent}{self.indent_str}return {body_inner}")
            body_code = "\n".join(body_lines)

        # Clear return type after generating
        self.set_current_return_type(None)

        return f"{indent}func (p *Parser) {func_name}({params_str}) {ret_type} {{\n{body_code}\n{indent}}}"


# Module-level instance for convenience
_generator = GoCodeGenerator()


def escape_identifier(name: str) -> str:
    """Escape a Go identifier if it's a keyword."""
    return _generator.escape_identifier(name)


def generate_go_type(typ) -> str:
    """Generate Go type annotation from a Type expression."""
    return _generator.gen_type(typ)


def generate_go_lines(expr: TargetExpr, lines: List[str], indent: str = "") -> Optional[str]:
    """Generate Go code from a target IR expression."""
    return _generator.generate_lines(expr, lines, indent)


def generate_go_def(expr: Union[FunDef, VisitNonterminalDef], indent: str = "") -> str:
    """Generate Go function definition."""
    return _generator.generate_def(expr, indent)


__all__ = [
    'escape_identifier',
    'generate_go_lines',
    'generate_go_def',
    'generate_go_type',
    'GO_KEYWORDS',
    'GoCodeGenerator',
    'to_pascal_case',
]
