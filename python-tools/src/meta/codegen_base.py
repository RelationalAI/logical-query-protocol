"""Base code generation infrastructure for target languages.

This module provides an abstract base class and shared logic for generating
code from the target IR. Language-specific code generators (Python, Julia)
inherit from CodeGenerator and provide language-specific implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Tuple, Union

if TYPE_CHECKING:
    from .proto_ast import ProtoMessage

from .target import (
    TargetExpr, Var, Lit, Symbol, Builtin, NamedFun, NewMessage, EnumValue, OneOf, ListExpr, Call, Lambda, Let,
    IfElse, Seq, While, Foreach, ForeachEnumerated, Assign, Return, FunDef, VisitNonterminalDef,
    VisitNonterminal, TargetType, BaseType, TupleType, ListType, DictType, OptionType,
    MessageType, EnumType, FunctionType, VarType, GetField, GetElement
)
from .target_builtins import get_builtin
from .gensym import gensym
from .codegen_templates import BuiltinTemplate


@dataclass
class BuiltinResult:
    """Result of generating a builtin call."""
    value: Optional[str]  # The value expression to return, or None if the builtin does not return
    statements: List[str]  # Statements to prepend (may be empty)


# Type alias for builtin generator functions
BuiltinGenerator = Callable[[List[str], List[str], str], BuiltinResult]


@dataclass
class BuiltinSpec:
    """Specification for a builtin function.

    name: Name of the builtin (e.g., "list_concat")
    generator: Function that generates code for this builtin.
               Takes (args, lines, indent) and returns BuiltinResult.

    Arity is looked up from target_builtins.BUILTIN_REGISTRY.
    """
    name: str
    generator: BuiltinGenerator


class CodeGenerator(ABC):
    """Abstract base class for language-specific code generators.

    Subclasses must implement the abstract methods to provide language-specific
    syntax for literals, types, and control flow constructs.
    """

    # Subclasses should override these class attributes
    keywords: Set[str] = set()
    indent_str: str = "    "  # Default indentation (4 spaces)

    # Type mappings: base type name -> target language type
    base_type_map: Dict[str, str] = {}

    def __init__(self, proto_messages: Optional[Dict[Tuple[str, str], Any]] = None) -> None:
        self.builtin_registry: Dict[str, BuiltinSpec] = {}
        self.proto_messages = proto_messages or {}

    @abstractmethod
    def escape_keyword(self, name: str) -> str:
        """Escape a keyword if necessary. Each language has different syntax."""
        pass

    def escape_identifier(self, name: str) -> str:
        """Escape an identifier if it's a keyword."""
        if name in self.keywords:
            return self.escape_keyword(name)
        return name

    # --- Field access ---

    def gen_field_access(self, obj_code: str, field_name: str) -> str:
        """Generate field access expression: obj.field_name."""
        return f"{obj_code}.{field_name}"

    # --- Literal generation ---

    @abstractmethod
    def gen_none(self) -> str:
        """Generate the null/None/nil literal."""
        pass

    @abstractmethod
    def gen_bool(self, value: bool) -> str:
        """Generate a boolean literal."""
        pass

    @abstractmethod
    def gen_string(self, value: str) -> str:
        """Generate a string literal."""
        pass

    def gen_number(self, value: Any) -> str:
        """Generate a numeric literal. Default uses repr()."""
        return repr(value)

    def gen_literal(self, value: Any) -> str:
        """Generate a literal value."""
        if value is None:
            return self.gen_none()
        elif isinstance(value, bool):
            return self.gen_bool(value)
        elif isinstance(value, str):
            return self.gen_string(value)
        else:
            return self.gen_number(value)

    # --- Symbol and constructor generation ---

    @abstractmethod
    def gen_symbol(self, name: str) -> str:
        """Generate a symbol literal (e.g., :name or 'name')."""
        pass

    @abstractmethod
    def gen_constructor(self, module: str, name: str) -> str:
        """Generate a constructor reference (e.g., proto.Name)."""
        pass

    @abstractmethod
    def gen_enum_value(self, module: str, enum_name: str, value_name: str) -> str:
        """Generate an enum value reference (e.g., pb.EnumName_VALUE)."""
        pass

    @abstractmethod
    def gen_builtin_ref(self, name: str) -> str:
        """Generate a reference to a builtin function."""
        pass

    @abstractmethod
    def gen_named_fun_ref(self, name: str) -> str:
        """Generate a reference to a user-defined named function."""
        pass

    @abstractmethod
    def gen_parse_nonterminal_ref(self, name: str) -> str:
        """Generate a reference to a parse method for a nonterminal."""
        pass

    @abstractmethod
    def gen_pretty_nonterminal_ref(self, name: str) -> str:
        """Generate a reference to a pretty-print method for a nonterminal."""
        pass

    # --- Type generation ---

    @abstractmethod
    def gen_message_type(self, module: str, name: str) -> str:
        """Generate a message/protobuf type reference."""
        pass

    @abstractmethod
    def gen_enum_type(self, module: str, name: str) -> str:
        """Generate an enum type reference."""
        pass

    @abstractmethod
    def gen_tuple_type(self, element_types: List[str]) -> str:
        """Generate a tuple type with the given element types."""
        pass

    @abstractmethod
    def gen_list_type(self, element_type: str) -> str:
        """Generate a list/array type."""
        pass

    @abstractmethod
    def gen_option_type(self, element_type: str) -> str:
        """Generate an optional type."""
        pass

    @abstractmethod
    def gen_dict_type(self, key_type: str, value_type: str) -> str:
        """Generate a dictionary/map type."""
        pass

    @abstractmethod
    def gen_list_literal(self, elements: List[str], element_type: TargetType) -> str:
        """Generate a list literal with the given elements (may be empty)."""
        pass

    @abstractmethod
    def gen_function_type(self, param_types: List[str], return_type: str) -> str:
        """Generate a function type."""
        pass

    def gen_type(self, typ: TargetType) -> str:
        """Generate a type expression."""
        if isinstance(typ, BaseType):
            return self.base_type_map.get(typ.name, typ.name)
        elif isinstance(typ, MessageType):
            return self.gen_message_type(typ.module, typ.name)
        elif isinstance(typ, EnumType):
            return self.gen_enum_type(typ.module, typ.name)
        elif isinstance(typ, TupleType):
            element_types = [self.gen_type(e) for e in typ.elements]
            return self.gen_tuple_type(element_types)
        elif isinstance(typ, ListType):
            return self.gen_list_type(self.gen_type(typ.element_type))
        elif isinstance(typ, DictType):
            return self.gen_dict_type(self.gen_type(typ.key_type), self.gen_type(typ.value_type))
        elif isinstance(typ, OptionType):
            return self.gen_option_type(self.gen_type(typ.element_type))
        elif isinstance(typ, FunctionType):
            param_types = [self.gen_type(pt) for pt in typ.param_types]
            return_type = self.gen_type(typ.return_type)
            return self.gen_function_type(param_types, return_type)
        elif isinstance(typ, VarType):
            return self.base_type_map.get("Any", "Any")
        else:
            raise ValueError(f"Unknown type: {type(typ)}")

    # --- Control flow syntax ---

    @abstractmethod
    def gen_if_start(self, cond: str) -> str:
        """Generate start of if statement (e.g., 'if cond:' or 'if cond {')."""
        pass

    @abstractmethod
    def gen_else(self) -> str:
        """Generate else clause (e.g., 'else:' or '} else {')."""
        pass

    @abstractmethod
    def gen_if_end(self) -> str:
        """Generate end of if statement (e.g., '' or '}' or 'end')."""
        pass

    @abstractmethod
    def gen_while_start(self, cond: str) -> str:
        """Generate start of while loop."""
        pass

    @abstractmethod
    def gen_while_end(self) -> str:
        """Generate end of while loop."""
        pass

    @abstractmethod
    def gen_foreach_start(self, var: str, collection: str) -> str:
        """Generate start of foreach loop."""
        pass

    @abstractmethod
    def gen_foreach_enumerated_start(self, index_var: str, var: str, collection: str) -> str:
        """Generate start of foreach enumerated loop."""
        pass

    @abstractmethod
    def gen_foreach_end(self) -> str:
        """Generate end of foreach loop."""
        pass

    @abstractmethod
    def gen_empty_body(self) -> str:
        """Generate placeholder for empty body (e.g., 'pass' or '// empty')."""
        pass

    @abstractmethod
    def gen_assignment(self, var: str, value: str, is_declaration: bool = False) -> str:
        """Generate an assignment statement."""
        pass

    @abstractmethod
    def gen_return(self, value: str) -> str:
        """Generate a return statement."""
        pass

    @abstractmethod
    def gen_var_declaration(self, var: str, type_hint: Optional[str] = None) -> str:
        """Generate a variable declaration without initialization."""
        pass

    # --- Lambda and function definition syntax ---

    @abstractmethod
    def gen_lambda_start(self, params: List[str], return_type: Optional[str]) -> Tuple[str, str]:
        """Generate start of lambda definition.

        Returns (before_body, after_body) strings.
        For Python: ('def _t0():', '')
        For Julia: ('function _t0()', 'end')
        """
        pass

    @abstractmethod
    def gen_func_def_header(self, name: str, params: List[Tuple[str, str]],
                            return_type: Optional[str], is_method: bool = False) -> str:
        """Generate function definition header.

        params is list of (name, type) tuples.
        """
        pass

    @abstractmethod
    def gen_func_def_end(self) -> str:
        """Generate function definition end (e.g., '' or 'end' or '}')."""
        pass

    # --- Builtin operations ---

    def register_builtin(self, name: str, generator: BuiltinGenerator) -> None:
        """Register a builtin function generator.

        Arity is looked up from target_builtins.BUILTIN_REGISTRY.
        """
        self.builtin_registry[name] = BuiltinSpec(name, generator)

    def register_builtin_from_template(self, name: str, template: BuiltinTemplate) -> None:
        """Register a builtin from a template."""
        def generator(args: List[str], lines: List[str], indent: str) -> BuiltinResult:
            # Handle None value (non-returning builtins like error)
            if template.value_template is None:
                value = None
            elif "{args}" in template.value_template:
                # Handle variadic {args} placeholder
                value = template.value_template.replace("{args}", ", ".join(args))
            else:
                value = template.value_template.format(*args)

            statements = []
            for stmt_template in template.statement_templates:
                if "{args}" in stmt_template:
                    statements.append(stmt_template.replace("{args}", ", ".join(args)))
                else:
                    statements.append(stmt_template.format(*args))

            return BuiltinResult(value, statements)

        self.register_builtin(name, generator)

    def register_builtins_from_templates(self, templates: Dict[str, BuiltinTemplate]) -> None:
        """Register builtins from template dictionaries."""
        for name, template in templates.items():
            self.register_builtin_from_template(name, template)

    def gen_builtin_call(self, name: str, args: List[str],
                         lines: List[str], indent: str) -> Optional[BuiltinResult]:
        """Generate code for a builtin function call.

        Returns BuiltinResult if handled, None if should use default call generation.

        Checks the builtin_registry. Arity validation uses target_builtins.
        """
        if name in self.builtin_registry:
            spec = self.builtin_registry[name]
            # Look up arity from the central builtin registry
            builtin_sig = get_builtin(name)
            if builtin_sig is None or builtin_sig.is_variadic() or len(args) == builtin_sig.arity:
                return spec.generator(args, lines, indent)
        return None

    # --- Type-based expression classification ---

    def _is_void_expr(self, expr: TargetExpr) -> bool:
        """Check if expression has type OptionType(Never) — side-effect only, value always None."""
        try:
            t = expr.target_type()
            return isinstance(t, OptionType) and isinstance(t.element_type, BaseType) and t.element_type.name == "Never"
        except (NotImplementedError, ValueError, TypeError):
            return False

    def _is_never_expr(self, expr: TargetExpr) -> bool:
        """Check if expression has type Never — diverges (return/error), no value produced."""
        try:
            t = expr.target_type()
            return isinstance(t, BaseType) and t.name == "Never"
        except (NotImplementedError, ValueError, TypeError):
            return False

    def _is_boolean_expr(self, expr: TargetExpr) -> bool:
        """Check if expression has type Boolean."""
        try:
            t = expr.target_type()
            return isinstance(t, BaseType) and t.name == "Boolean"
        except (NotImplementedError, ValueError, TypeError):
            return False

    # --- Expression generation ---

    def generate_lines(self, expr: TargetExpr, lines: List[str], indent: str = "") -> Optional[str]:
        """Generate code for an expression, appending statements to lines.

        Returns the value expression as a string, or None if the expression
        returns (i.e., contains a Return node that was executed).
        """
        if isinstance(expr, Var):
            return self.escape_identifier(expr.name)

        elif isinstance(expr, Lit):
            return self.gen_literal(expr.value)

        elif isinstance(expr, Symbol):
            return self.gen_symbol(expr.name)

        elif isinstance(expr, NewMessage):
            return self._generate_newmessage(expr, lines, indent)

        elif isinstance(expr, EnumValue):
            return self._generate_enum_value(expr, lines, indent)

        elif isinstance(expr, Builtin):
            return self.gen_builtin_ref(expr.name)

        elif isinstance(expr, NamedFun):
            return self.gen_named_fun_ref(expr.name)

        elif isinstance(expr, VisitNonterminal):
            if expr.visitor_name == 'pretty':
                return self.gen_pretty_nonterminal_ref(expr.nonterminal.name)
            return self.gen_parse_nonterminal_ref(expr.nonterminal.name)

        elif isinstance(expr, OneOf):
            return self._generate_oneof(expr, lines, indent)

        elif isinstance(expr, ListExpr):
            return self._generate_list_expr(expr, lines, indent)

        elif isinstance(expr, GetField):
            obj_code = self.generate_lines(expr.object, lines, indent)
            return self.gen_field_access(obj_code, expr.field_name)

        elif isinstance(expr, GetElement):
            return self._generate_get_element(expr, lines, indent)

        elif isinstance(expr, Call):
            return self._generate_call(expr, lines, indent)

        elif isinstance(expr, Lambda):
            return self._generate_lambda(expr, lines, indent)

        elif isinstance(expr, Let):
            return self._generate_let(expr, lines, indent)

        elif isinstance(expr, IfElse):
            return self._generate_if_else(expr, lines, indent)

        elif isinstance(expr, Seq):
            return self._generate_seq(expr, lines, indent)

        elif isinstance(expr, While):
            return self._generate_while(expr, lines, indent)

        elif isinstance(expr, Foreach):
            return self._generate_foreach(expr, lines, indent)

        elif isinstance(expr, ForeachEnumerated):
            return self._generate_foreach_enumerated(expr, lines, indent)

        elif isinstance(expr, Assign):
            return self._generate_assign(expr, lines, indent)

        elif isinstance(expr, Return):
            return self._generate_return(expr, lines, indent)

        else:
            raise ValueError(f"Unknown expression type: {type(expr)}")

    def _generate_call(self, expr: Call, lines: List[str], indent: str) -> Optional[str]:
        """Generate code for a function call."""
        # NewMessage should be handled directly, not wrapped in Call
        assert not isinstance(expr.func, NewMessage), \
            f"Call(NewMessage, ...) should not occur in target IR; use NewMessage with fields instead: {expr}"

        # First, check for builtin special cases
        if isinstance(expr.func, Builtin):
            # Evaluate arguments (they should not contain return statements)
            args: List[str] = []
            for arg in expr.args:
                arg_code = self.generate_lines(arg, lines, indent)
                assert arg_code is not None, "Function argument should not contain a return"
                args.append(arg_code)
            result = self.gen_builtin_call(expr.func.name, args, lines, indent)
            if result is not None:
                for stmt in result.statements:
                    lines.append(f"{indent}{stmt}")
                # Check if builtin returns Never (like error builtins)
                builtin_sig = get_builtin(expr.func.name)
                if builtin_sig is not None and builtin_sig.return_type == BaseType("Never"):
                    return None
                return result.value

        # Regular call
        f = self.generate_lines(expr.func, lines, indent)
        assert f is not None, "Function expression should not contain a return"
        args = []
        for arg in expr.args:
            arg_code = self.generate_lines(arg, lines, indent)
            assert arg_code is not None, "Function argument should not contain a return"
            args.append(arg_code)
        args_code = ', '.join(args)

        if self._is_void_expr(expr):
            lines.append(f"{indent}{f}({args_code})")
            return self.gen_none()

        tmp = gensym()
        lines.append(f"{indent}{self.gen_assignment(tmp, f'{f}({args_code})', is_declaration=True)}")
        return tmp

    def _generate_newmessage(self, expr: NewMessage, lines: List[str], indent: str) -> str:
        """Generate code for a NewMessage expression.

        Default implementation uses positional constructor args.
        Subclasses should override for language-specific protobuf semantics.
        """
        ctor = self.gen_constructor(expr.module, expr.name)

        if not expr.fields:
            tmp = gensym()
            lines.append(f"{indent}{self.gen_assignment(tmp, f'{ctor}()', is_declaration=True)}")
            return tmp

        args = []
        for field_name, field_expr in expr.fields:
            if (isinstance(field_expr, Call)
                    and isinstance(field_expr.func, OneOf)
                    and len(field_expr.args) == 1):
                field_value = self.generate_lines(field_expr.args[0], lines, indent)
            else:
                field_value = self.generate_lines(field_expr, lines, indent)
            assert field_value is not None
            args.append(f"{field_name}={field_value}")

        args_code = ', '.join(args)
        call = f"{ctor}({args_code})"
        tmp = gensym()
        lines.append(f"{indent}{self.gen_assignment(tmp, call, is_declaration=True)}")
        return tmp

    def _generate_get_element(self, expr: GetElement, lines: List[str], indent: str) -> str:
        """Generate code for a GetElement expression.

        Default implementation uses 0-based indexing.
        Subclasses can override for different indexing (e.g., Julia uses 1-based).
        """
        tuple_code = self.generate_lines(expr.tuple_expr, lines, indent)
        return f"{tuple_code}[{expr.index}]"

    def _generate_enum_value(self, expr: EnumValue, lines: List[str], indent: str) -> str:
        """Generate code for an enum value reference."""
        return self.gen_enum_value(expr.module, expr.enum_name, expr.value_name)

    def _generate_oneof(self, expr: OneOf, lines: List[str], indent: str) -> str:
        """Generate code for a OneOf expression.

        Default implementation treats it as an error since OneOf should only
        appear as arguments to Message constructors. Subclasses should override
        this to handle the language-specific semantics.
        """
        raise ValueError(f"OneOf should only appear as arguments to Message constructors: {expr}")

    def _generate_list_expr(self, expr: ListExpr, lines: List[str], indent: str) -> str:
        """Generate code for a list expression."""
        elements: List[str] = []
        for elem in expr.elements:
            elem_code = self.generate_lines(elem, lines, indent)
            assert elem_code is not None, "List element should not contain a return"
            elements.append(elem_code)
        return self.gen_list_literal(elements, expr.element_type)

    def _generate_lambda(self, expr: Lambda, lines: List[str], indent: str) -> str:
        """Generate code for a lambda expression."""
        params = [self.escape_identifier(p.name) for p in expr.params]
        f = gensym()
        ret_type = self.gen_type(expr.return_type) if expr.return_type else None

        before, after = self.gen_lambda_start(params, ret_type)
        # Replace placeholder with actual function name
        before = before.replace("__FUNC__", f)

        lines.append(f"{indent}{before}")
        body_indent = indent + self.indent_str
        v = self.generate_lines(expr.body, lines, body_indent)
        # Only add return if the body didn't already return
        if v is not None:
            lines.append(f"{body_indent}{self.gen_return(v)}")
        if after:
            lines.append(f"{indent}{after}")
        return f

    def _generate_let(self, expr: Let, lines: List[str], indent: str) -> Optional[str]:
        """Generate code for a let binding."""
        var_name = self.escape_identifier(expr.var.name)
        init_val = self.generate_lines(expr.init, lines, indent)
        assert init_val is not None, "Let initializer should not contain a return"
        lines.append(f"{indent}{self.gen_assignment(var_name, init_val, is_declaration=True)}")
        return self.generate_lines(expr.body, lines, indent)

    def _generate_if_else(self, expr: IfElse, lines: List[str], indent: str) -> Optional[str]:
        """Generate code for an if-else expression."""
        cond_code = self.generate_lines(expr.condition, lines, indent)
        assert cond_code is not None, "If condition should not contain a return"

        # Both branches diverge — generate for side effects only, no value.
        if self._is_never_expr(expr):
            lines.append(f"{indent}{self.gen_if_start(cond_code)}")
            body_indent = indent + self.indent_str
            self.generate_lines(expr.then_branch, lines, body_indent)
            lines.append(f"{indent}{self.gen_else()}")
            self.generate_lines(expr.else_branch, lines, body_indent)
            end = self.gen_if_end()
            if end:
                lines.append(f"{indent}{end}")
            return None

        # Side-effect only (value always None) — no temp needed.
        if self._is_void_expr(expr):
            lines.append(f"{indent}{self.gen_if_start(cond_code)}")
            body_indent = indent + self.indent_str
            self.generate_lines(expr.then_branch, lines, body_indent)
            if expr.else_branch != Lit(None):
                lines.append(f"{indent}{self.gen_else()}")
                self.generate_lines(expr.else_branch, lines, body_indent)
            end = self.gen_if_end()
            if end:
                lines.append(f"{indent}{end}")
            return self.gen_none()

        # Short-circuit boolean if-else to and/or.
        if self._is_boolean_expr(expr):
            # `if cond then True else x` -> or(cond, x)
            if expr.then_branch == Lit(True):
                tmp_lines: List[str] = []
                else_code = self.generate_lines(expr.else_branch, tmp_lines, indent)
                if not tmp_lines and else_code is not None:
                    result = self.gen_builtin_call("or", [cond_code, else_code], lines, indent)
                    if result is not None:
                        return result.value

            # `if cond then x else False` -> and(cond, x)
            if expr.else_branch == Lit(False):
                tmp_lines = []
                then_code = self.generate_lines(expr.then_branch, tmp_lines, indent)
                if not tmp_lines and then_code is not None:
                    result = self.gen_builtin_call("and", [cond_code, then_code], lines, indent)
                    if result is not None:
                        return result.value

        # Determine expression type for typed variable declarations.
        type_hint = None
        try:
            expr_type = expr.target_type()
            if expr_type is not None:
                type_hint = self.gen_type(expr_type)
        except (NotImplementedError, ValueError, TypeError):
            pass

        tmp = gensym()
        lines.append(f"{indent}{self.gen_var_declaration(tmp, type_hint)}")
        lines.append(f"{indent}{self.gen_if_start(cond_code)}")

        body_indent = indent + self.indent_str
        then_code = self.generate_lines(expr.then_branch, lines, body_indent)
        if then_code is not None:
            lines.append(f"{body_indent}{self.gen_assignment(tmp, then_code)}")

        if expr.else_branch != Lit(None):
            lines.append(f"{indent}{self.gen_else()}")
            else_code = self.generate_lines(expr.else_branch, lines, body_indent)
            if else_code is not None:
                lines.append(f"{body_indent}{self.gen_assignment(tmp, else_code)}")
        else:
            else_code = self._generate_nil_else_branch(tmp, lines, indent, body_indent)

        end = self.gen_if_end()
        if end:
            lines.append(f"{indent}{end}")

        # If both branches returned, propagate None
        if then_code is None and else_code is None:
            return None

        return tmp

    def _generate_nil_else_branch(
        self, tmp: str, lines: List[str], indent: str, body_indent: str,
    ) -> str:
        """Generate else branch for Lit(None). Returns the else_code value.

        Subclasses may override to skip the else branch.
        """
        else_code = self.gen_none()
        lines.append(f"{indent}{self.gen_else()}")
        lines.append(f"{body_indent}{self.gen_assignment(tmp, else_code)}")
        return else_code

    def _generate_seq(self, expr: Seq, lines: List[str], indent: str) -> Optional[str]:
        """Generate code for a sequence of expressions.

        If any expression returns None (indicating a return statement was executed),
        stop processing and propagate None (subsequent expressions are unreachable).
        """
        result: Optional[str] = self.gen_none()
        for e in expr.exprs:
            result = self.generate_lines(e, lines, indent)
            if result is None:
                break
        return result

    def _generate_while(self, expr: While, lines: List[str], indent: str) -> str:
        """Generate code for a while loop."""
        m = len(lines)
        cond_code = self.generate_lines(expr.condition, lines, indent)
        assert cond_code is not None, "While condition should not contain a return"
        non_trivial_cond = len(lines) > m
        cond_code_is_lvalue = cond_code.isidentifier()

        lines.append(f"{indent}{self.gen_while_start(cond_code)}")
        n = len(lines)

        body_indent = indent + self.indent_str
        self.generate_lines(expr.body, lines, body_indent)

        if len(lines) == n:
            lines.append(f"{body_indent}{self.gen_empty_body()}")

        # Update the condition variable if needed
        if non_trivial_cond and cond_code_is_lvalue:
            cond_code2 = self.generate_lines(expr.condition, lines, body_indent)
            assert cond_code2 is not None, "While condition should not contain a return"
            lines.append(f"{body_indent}{self.gen_assignment(cond_code, cond_code2)}")

        end = self.gen_while_end()
        if end:
            lines.append(f"{indent}{end}")

        return self.gen_none()

    def _generate_foreach(self, expr: Foreach, lines: List[str], indent: str) -> str:
        """Generate code for a foreach loop."""
        collection_code = self.generate_lines(expr.collection, lines, indent)
        assert collection_code is not None, "Foreach collection should not contain a return"
        var_name = self.escape_identifier(expr.var.name)

        lines.append(f"{indent}{self.gen_foreach_start(var_name, collection_code)}")
        body_indent = indent + self.indent_str
        self.generate_lines(expr.body, lines, body_indent)

        end = self.gen_foreach_end()
        if end:
            lines.append(f"{indent}{end}")

        return self.gen_none()

    def _generate_foreach_enumerated(self, expr: ForeachEnumerated, lines: List[str], indent: str) -> str:
        """Generate code for a foreach enumerated loop."""
        collection_code = self.generate_lines(expr.collection, lines, indent)
        assert collection_code is not None, "ForeachEnumerated collection should not contain a return"
        index_name = self.escape_identifier(expr.index_var.name)
        var_name = self.escape_identifier(expr.var.name)

        lines.append(f"{indent}{self.gen_foreach_enumerated_start(index_name, var_name, collection_code)}")
        body_indent = indent + self.indent_str
        self.generate_lines(expr.body, lines, body_indent)

        end = self.gen_foreach_end()
        if end:
            lines.append(f"{indent}{end}")

        return self.gen_none()

    def _generate_assign(self, expr: Assign, lines: List[str], indent: str) -> str:
        """Generate code for an assignment."""
        var_name = self.escape_identifier(expr.var.name)
        expr_code = self.generate_lines(expr.expr, lines, indent)
        assert expr_code is not None, "Assignment expression should not contain a return"
        lines.append(f"{indent}{self.gen_assignment(var_name, expr_code)}")
        return self.gen_none()

    def _generate_return(self, expr: Return, lines: List[str], indent: str) -> None:
        """Generate code for a return statement.

        Returns None to indicate that the caller should not add another return
        statement.
        """
        expr_code = self.generate_lines(expr.expr, lines, indent)
        assert expr_code is not None, "Return expression should not itself contain a return"
        lines.append(f"{indent}{self.gen_return(expr_code)}")
        return None

    # --- Function definition generation ---

    def generate_def(self, expr: Union[FunDef, VisitNonterminalDef], indent: str = "") -> str:
        """Generate a function definition."""
        if isinstance(expr, FunDef):
            return self._generate_fun_def(expr, indent)
        elif isinstance(expr, VisitNonterminalDef):
            if expr.visitor_name == 'pretty':
                return self._generate_pretty_def(expr, indent)
            return self._generate_parse_def(expr, indent)
        else:
            raise ValueError(f"Unknown definition type: {type(expr)}")

    def _generate_fun_def(self, expr: FunDef, indent: str) -> str:
        """Generate a regular function definition."""
        func_name = self.escape_identifier(expr.name)
        params = [(self.escape_identifier(p.name), self.gen_type(p.type)) for p in expr.params]
        ret_type = self.gen_type(expr.return_type) if expr.return_type else None

        header = self.gen_func_def_header(func_name, params, ret_type)

        if expr.body is None:
            body_code = f"{indent}{self.indent_str}{self.gen_empty_body()}"
        else:
            lines: List[str] = []
            body_inner = self.generate_lines(expr.body, lines, indent + self.indent_str)
            # Only add return if the body didn't already return
            if body_inner is not None:
                lines.append(f"{indent}{self.indent_str}{self.gen_return(body_inner)}")
            body_code = "\n".join(lines)

        end = self.gen_func_def_end()
        if end:
            return f"{indent}{header}\n{body_code}\n{indent}{end}"
        return f"{indent}{header}\n{body_code}"

    @abstractmethod
    def generate_method_def(self, expr: FunDef, indent: str) -> str:
        """Generate a function definition as a method on Parser."""
        pass

    @abstractmethod
    def _generate_parse_def(self, expr: VisitNonterminalDef, indent: str) -> str:
        """Generate a parse method definition. Language-specific due to method syntax."""
        pass

    @abstractmethod
    def _generate_pretty_def(self, expr: VisitNonterminalDef, indent: str) -> str:
        """Generate a pretty-print method definition. Language-specific due to method syntax."""
        pass

    # --- Token spec formatting for parser generation ---

    @abstractmethod
    def format_literal_token_spec(self, escaped_literal: str) -> str:
        """Format a literal token spec line for the lexer."""
        pass

    @abstractmethod
    def format_named_token_spec(self, token_name: str, token_pattern: str) -> str:
        """Format a named token spec line for the lexer."""
        pass

    @abstractmethod
    def format_command_line_comment(self, command_line: str) -> str:
        """Format a command line comment for the generated file header."""
        pass

    # Parser generation indent for parse method definitions
    parse_def_indent: str = ""
