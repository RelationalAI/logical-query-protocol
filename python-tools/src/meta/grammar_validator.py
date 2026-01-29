"""Validator for grammar-to-protobuf correspondence.

This module validates that the generated grammar:
1. Covers all protobuf messages (completeness)
2. Correctly types all message constructions, including field coverage
3. Covers all oneof variants with at least one rule per variant
4. Contains no orphan rules without protobuf backing (soundness)
5. Has no unreachable nonterminals
6. Has valid structure (Star/Option children, no nested Sequence)

The validation criteria are:
- Completeness: Every proto message has a corresponding grammar rule
- Type checking: All expressions are well-typed, including NewMessage field coverage
- Oneof coverage: Every oneof variant has at least one alternative production
- Soundness: Every grammar rule corresponds to a proto construct or known builtin
- Reachability: All nonterminals are reachable from the start symbol
- Structure: Grammar elements follow structural constraints

Note: This validator does NOT check if the grammar is LL(k) for any k.
Grammar ambiguity and lookahead conflicts are detected by the parser generator.
"""

from dataclasses import dataclass, field as dataclass_field
from typing import List, Optional, Set, Sequence as PySequence, Dict

from .grammar import Grammar, Rule, Nonterminal, Rhs, LitTerminal, NamedTerminal, Star, Option, Sequence
from .proto_parser import ProtoParser
from .proto_ast import ProtoMessage, ProtoField
from .target import (
    TargetType, TargetExpr, Call, NewMessage, Builtin, Var, IfElse, Let, Seq, ListExpr, GetField,
    GetElement, BaseType, VarType, MessageType, ListType, OptionType, TupleType, FunctionType, Lambda, OneOf
)


# Mapping from protobuf primitive types to base type names
_PRIMITIVE_TO_BASE_TYPE = {
    'string': 'String',
    'int32': 'Int32',
    'int64': 'Int64',
    'uint32': 'UInt32',
    'uint64': 'UInt64',
    'fixed64': 'Int64',
    'bool': 'Boolean',
    'double': 'Float64',
    'float': 'Float32',
    'bytes': 'String',
}



class TypeEnv:
    """Type environment for validating grammar expressions.

    Maintains:
    - Message field types from protobuf specification
    - Builtin function signatures (with polymorphism support)
    - Local variable bindings with lexical scoping for lambda parameters

    Supports arbitrary lambda nesting and variable shadowing.
    """

    def __init__(self, proto_parser: ProtoParser):
        """Initialize type environment from protobuf parser.

        Args:
            proto_parser: Parsed protobuf definitions
        """
        self.parser = proto_parser

        # Message field types: (module, message_name) -> [field_types]
        self._message_field_types: Dict[tuple[str, str], List[TargetType]] = {}

        # Builtin function signatures: name -> FunctionType
        # For polymorphic builtins, we store a representative type
        self._builtin_types: Dict[str, FunctionType] = {}

        # Local variable scopes: stack of frames (innermost first)
        # Each frame is a dict: var_name -> type
        self._local_scopes: List[Dict[str, TargetType]] = []

        # Build type information from proto
        self._build_message_types()
        self._init_builtin_types()

    def _build_message_types(self) -> None:
        """Build message field types from protobuf specification."""
        for message_name, message in self.parser.messages.items():
            field_types = []

            # Check if this is a oneof-only message
            if self._is_oneof_only_message(message):
                # Oneof-only messages take exactly 1 argument: the oneof value
                field_types = []  # Handled specially
            else:
                # Regular message: collect field types, skipping enum fields
                for proto_field in message.fields:
                    # Skip enum fields - they're not included in the grammar
                    if self._is_enum_type(proto_field.type):
                        continue
                    field_type = self._proto_type_to_target(proto_field)
                    field_types.append(field_type)

            key = (message.module, message_name)
            self._message_field_types[key] = field_types

    def _is_oneof_only_message(self, message: ProtoMessage) -> bool:
        """Check if message contains only a single oneof and no other fields."""
        return len(message.oneofs) > 0 and len(message.fields) == 0

    def _is_enum_type(self, type_name: str) -> bool:
        """Check if type is a protobuf enum."""
        return type_name in self.parser.enums

    def _proto_type_to_target(self, proto_field: ProtoField) -> TargetType:
        """Convert a protobuf field to its target type."""
        # Get base type
        base_type: TargetType
        if proto_field.type in _PRIMITIVE_TO_BASE_TYPE:
            base_type = BaseType(_PRIMITIVE_TO_BASE_TYPE[proto_field.type])
        elif proto_field.type in self.parser.messages:
            message = self.parser.messages[proto_field.type]
            base_type = MessageType(message.module, proto_field.type)
        else:
            # Unknown type
            base_type = BaseType("Unknown")

        # Wrap in Option if optional
        if proto_field.is_optional:
            base_type = OptionType(base_type)

        # Wrap in List if repeated
        if proto_field.is_repeated:
            base_type = ListType(base_type)

        return base_type

    def _init_builtin_types(self) -> None:
        """Initialize builtin function type signatures."""
        # Type variables for polymorphic builtins
        T = VarType("T")

        # unwrap_option_or: (Option[T], T) -> T
        self._builtin_types["unwrap_option_or"] = FunctionType(
            param_types=[OptionType(T), T],
            return_type=T
        )

        # make_tuple: (T1, T2, ...) -> (T1, T2, ...)
        # Variable arity - we'll check structurally
        self._builtin_types["make_tuple"] = FunctionType(
            param_types=[],  # Variable arity
            return_type=TupleType([])
        )

        # list_concat: (List[T], List[T]) -> List[T]
        self._builtin_types["list_concat"] = FunctionType(
            param_types=[ListType(T), ListType(T)],
            return_type=ListType(T)
        )

        # length: List[T] -> Int64
        self._builtin_types["length"] = FunctionType(
            param_types=[ListType(T)],
            return_type=BaseType("Int64")
        )

        # int64_to_int32: Int64 -> Int32
        self._builtin_types["int64_to_int32"] = FunctionType(
            param_types=[BaseType("Int64")],
            return_type=BaseType("Int32")
        )

        # equal: (T, T) -> Boolean
        self._builtin_types["equal"] = FunctionType(
            param_types=[T, T],
            return_type=BaseType("Boolean")
        )

        # WhichOneof: (Message, String) -> String
        self._builtin_types["WhichOneof"] = FunctionType(
            param_types=[VarType("Message"), BaseType("String")],
            return_type=BaseType("String")
        )

        # Some: T -> Option[T]
        self._builtin_types["Some"] = FunctionType(
            param_types=[T],
            return_type=OptionType(T)
        )

        # is_empty: List[T] -> Boolean
        self._builtin_types["is_empty"] = FunctionType(
            param_types=[ListType(T)],
            return_type=BaseType("Boolean")
        )

        # Builtins specific to the generated code (from builtin_rules.sexp)
        # construct_configure: List[(String, Value)] -> Configure
        self._builtin_types["construct_configure"] = FunctionType(
            param_types=[ListType(TupleType([BaseType("String"), MessageType("logic", "Value")]))],
            return_type=MessageType("transactions", "Configure")
        )

        # fragment_id_from_string: String -> FragmentId
        self._builtin_types["fragment_id_from_string"] = FunctionType(
            param_types=[BaseType("String")],
            return_type=MessageType("fragments", "FragmentId")
        )

        # relation_id_from_string: String -> RelationId
        self._builtin_types["relation_id_from_string"] = FunctionType(
            param_types=[BaseType("String")],
            return_type=MessageType("logic", "RelationId")
        )

        # relation_id_from_int: Int64 -> RelationId
        self._builtin_types["relation_id_from_int"] = FunctionType(
            param_types=[BaseType("Int64")],
            return_type=MessageType("logic", "RelationId")
        )

        # export_csv_config: (String, List[ExportCSVColumn], List[(String, Value)]) -> ExportCSVConfig
        self._builtin_types["export_csv_config"] = FunctionType(
            param_types=[
                BaseType("String"),
                ListType(MessageType("transactions", "ExportCSVColumn")),
                ListType(TupleType([BaseType("String"), MessageType("logic", "Value")]))
            ],
            return_type=MessageType("transactions", "ExportCSVConfig")
        )

        # start_fragment: FragmentId -> Unit
        self._builtin_types["start_fragment"] = FunctionType(
            param_types=[MessageType("fragments", "FragmentId")],
            return_type=BaseType("Unit")
        )

        # construct_fragment: (FragmentId, List[Declaration]) -> Fragment
        self._builtin_types["construct_fragment"] = FunctionType(
            param_types=[
                MessageType("fragments", "FragmentId"),
                ListType(MessageType("logic", "Declaration"))
            ],
            return_type=MessageType("fragments", "Fragment")
        )

    def get_message_field_types(self, module: str, name: str) -> Optional[List[TargetType]]:
        """Get field types for a message constructor.

        Args:
            module: Protobuf module name
            name: Message type name

        Returns:
            List of field types, or None if message not found
        """
        return self._message_field_types.get((module, name))

    def get_builtin_type(self, name: str) -> Optional[FunctionType]:
        """Get function type for a builtin.

        Args:
            name: Builtin function name

        Returns:
            Function type, or None if builtin not found
        """
        return self._builtin_types.get(name)

    def is_oneof_message(self, module: str, name: str) -> bool:
        """Check if a message is a oneof-only message."""
        if name in self.parser.messages:
            return self._is_oneof_only_message(self.parser.messages[name])
        return False

    def lookup_var(self, name: str) -> Optional[TargetType]:
        """Look up variable in local scopes (innermost to outermost).

        Args:
            name: Variable name

        Returns:
            Variable type, or None if not found
        """
        # Search from innermost to outermost scope
        for scope in reversed(self._local_scopes):
            if name in scope:
                return scope[name]
        return None

    def push_scope(self, bindings: Dict[str, TargetType]) -> None:
        """Enter a new lexical scope with given variable bindings.

        Args:
            bindings: Variable name -> type mappings for new scope
        """
        self._local_scopes.append(bindings.copy())

    def pop_scope(self) -> None:
        """Exit the current lexical scope."""
        if self._local_scopes:
            self._local_scopes.pop()


@dataclass
class ValidationIssue:
    """A single validation issue."""
    category: str  # "completeness", "field_coverage", "oneof_coverage", "soundness"
    severity: str  # "error", "warning"
    message: str
    proto_type: Optional[str] = None
    rule_name: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of grammar validation."""
    issues: List[ValidationIssue] = dataclass_field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings are acceptable for some use cases)."""
        return not any(i.severity == "error" for i in self.issues)

    @property
    def has_any_issues(self) -> bool:
        """True if there are any errors or warnings."""
        return len(self.issues) > 0

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def add_error(self, category: str, message: str, proto_type: Optional[str] = None, rule_name: Optional[str] = None) -> None:
        self.issues.append(ValidationIssue(category, "error", message, proto_type, rule_name))
        return None

    def add_warning(self, category: str, message: str, proto_type: Optional[str] = None, rule_name: Optional[str] = None) -> None:
        self.issues.append(ValidationIssue(category, "warning", message, proto_type, rule_name))
        return None

    def summary(self) -> str:
        """Return a summary of validation results."""
        lines = []
        if self.is_valid:
            lines.append("Validation PASSED")
        else:
            lines.append("Validation FAILED")

        error_count = len(self.errors)
        warning_count = len(self.warnings)
        lines.append(f"  {error_count} error(s), {warning_count} warning(s)")

        if self.errors:
            lines.append("")
            lines.append("Errors:")
            for issue in self.errors:
                lines.append(f"  [{issue.category}] {issue.message}")

        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for issue in self.warnings:
                lines.append(f"  [{issue.category}] {issue.message}")

        return "\n".join(lines)


class GrammarValidator:
    """Validates grammar against protobuf specification."""

    def __init__(
        self,
        grammar: Grammar,
        parser: ProtoParser,
    ):
        self.grammar = grammar
        self.parser = parser
        self.result = ValidationResult()

        # Build lookup structures
        self._rule_names: Set[str] = {nt.name for nt in grammar.rules.keys()}
        self._message_names: Set[str] = set(parser.messages.keys())

        # Build type environment from proto spec
        self.type_env = TypeEnv(parser)

    def validate(self) -> ValidationResult:
        """Run all validation checks."""
        self._check_unreachable()
        self._check_structure()
        self._check_types()
        self._check_message_coverage()
        self._check_oneof_coverage()
        self._check_soundness()
        return self.result

    def _check_unreachable(self) -> None:
        """Check for unreachable nonterminals."""
        _, unreachable = self.grammar.analysis.partition_nonterminals_by_reachability()
        for nt in unreachable:
            self.result.add_error(
                "unreachable",
                f"Grammar rule '{nt.name}' is unreachable from start symbol",
                rule_name=nt.name
            )
        return None

    def _check_structure(self) -> None:
        """Check structural constraints on grammar rules.

        Validates:
        1. Star children must be NamedTerminal or Nonterminal
        2. Option children must be NamedTerminal or Nonterminal
        3. Sequence cannot have nested Sequence elements
        """
        for rules in self.grammar.rules.values():
            for rule in rules:
                self._check_rhs_structure(rule.rhs, rule.lhs.name)
        return None

    def _check_rhs_structure(self, rhs: Rhs, rule_name: str) -> None:
        """Recursively check structural constraints on an RHS."""
        if isinstance(rhs, Star):
            if not isinstance(rhs.rhs, (NamedTerminal, Nonterminal)):
                self.result.add_error(
                    "structure",
                    f"Rule '{rule_name}': Star must contain NamedTerminal or Nonterminal, got {type(rhs.rhs).__name__}",
                    rule_name=rule_name
                )
        elif isinstance(rhs, Option):
            if not isinstance(rhs.rhs, (NamedTerminal, Nonterminal)):
                self.result.add_error(
                    "structure",
                    f"Rule '{rule_name}': Option must contain NamedTerminal or Nonterminal, got {type(rhs.rhs).__name__}",
                    rule_name=rule_name
                )
        elif isinstance(rhs, Sequence):
            for elem in rhs.elements:
                if isinstance(elem, Sequence):
                    self.result.add_error(
                        "structure",
                        f"Rule '{rule_name}': Sequence cannot contain nested Sequence",
                        rule_name=rule_name
                    )
                else:
                    self._check_rhs_structure(elem, rule_name)
        return None

    def _check_types(self) -> None:
        """Check type consistency in grammar rules.

        For each rule, validates:
        1. Arity: Number of lambda params matches non-literal RHS elements
        2. Parameter types: Each param type matches corresponding RHS element type
        3. Return type: Lambda return type matches LHS nonterminal type
        """
        for rules in self.grammar.rules.values():
            for rule in rules:
                self._check_rule_types(rule)
        return None

    def _check_rule_types(self, rule: Rule) -> None:
        """Check types for a single rule."""
        rule_name = rule.lhs.name

        # Get RHS element types (excluding literals)
        rhs_types = self._get_rhs_element_types(rule.rhs)

        # Get lambda parameter types
        param_types = [p.type for p in rule.constructor.params]

        # Check arity (redundant with Rule constructor, but validates post-construction)
        if len(param_types) != len(rhs_types):
            self.result.add_error(
                "type_arity",
                f"Rule '{rule_name}': lambda has {len(param_types)} params but RHS has {len(rhs_types)} non-literal elements",
                rule_name=rule_name
            )
            return None  # Can't check types if arity mismatch

        # Check each parameter type matches corresponding RHS element type
        for i, (param_type, rhs_type) in enumerate(zip(param_types, rhs_types)):
            if not self._types_compatible(param_type, rhs_type):
                param_name = rule.constructor.params[i].name
                self.result.add_error(
                    "type_param",
                    f"Rule '{rule_name}': param '{param_name}' has type {param_type} but RHS element has type {rhs_type}",
                    rule_name=rule_name
                )

        # Check return type matches LHS type
        lhs_type = rule.lhs.type
        return_type = rule.constructor.return_type
        if not self._types_compatible(return_type, lhs_type):
            self.result.add_error(
                "type_return",
                f"Rule '{rule_name}': lambda returns {return_type} but LHS expects {lhs_type}",
                rule_name=rule_name
            )

        # Type check the lambda body expression
        self._check_expr_types(rule.constructor.body, rule_name)

        return None

    def _check_expr_types(self, expr: TargetExpr, context: str) -> None:
        """Recursively type check an expression.

        Validates:
        - Message constructor calls have correct argument types
        - Builtin calls have correct argument types
        """
        if isinstance(expr, Call):
            if isinstance(expr.func, Builtin):
                self._check_builtin_call_types(expr.func, expr.args, context)
            else:
                # Recursively check function and args
                self._check_expr_types(expr.func, context)

            for arg in expr.args:
                self._check_expr_types(arg, context)

        elif isinstance(expr, Let):
            self._check_expr_types(expr.init, context)
            self._check_expr_types(expr.body, context)

        elif isinstance(expr, IfElse):
            self._check_expr_types(expr.condition, context)
            self._check_expr_types(expr.then_branch, context)
            self._check_expr_types(expr.else_branch, context)

        elif isinstance(expr, Seq):
            for sub in expr.exprs:
                self._check_expr_types(sub, context)

        elif isinstance(expr, ListExpr):
            for elem in expr.elements:
                self._check_expr_types(elem, context)

        elif isinstance(expr, GetField):
            # Check the object expression
            self._check_expr_types(expr.object, context)
            # field_name is a string, no need to check

        elif isinstance(expr, GetElement):
            # Check the tuple expression
            self._check_expr_types(expr.tuple_expr, context)
            # Check that tuple_expr has tuple type
            tuple_type = self._infer_expr_type(expr.tuple_expr)
            if tuple_type is not None and not isinstance(tuple_type, TupleType):
                self.result.add_error(
                    "type_tuple_element",
                    f"In {context}: GetElement expects tuple type, got {tuple_type}",
                    rule_name=context
                )
            # Check index bounds
            if isinstance(tuple_type, TupleType):
                if expr.index < 0 or expr.index >= len(tuple_type.elements):
                    self.result.add_error(
                        "type_tuple_element",
                        f"In {context}: GetElement index {expr.index} out of bounds for tuple with {len(tuple_type.elements)} elements",
                        rule_name=context
                    )

        elif isinstance(expr, NewMessage):
            # Check field names and types against proto spec
            self._check_new_message_types(expr, context)
            # Recursively check field expressions
            for _, field_expr in expr.fields:
                self._check_expr_types(field_expr, context)

        # Other expression types (Var, Lit, Symbol, Builtin, etc.) are leaves
        return None

    def _check_new_message_types(self, new_msg: NewMessage, context: str) -> None:
        """Check that NewMessage has correct field names and types.

        Args:
            new_msg: NewMessage node to validate
            context: Rule name or other context for error messages
        """
        # Get the proto message (messages are keyed by name only, not module.name)
        proto_message = self.parser.messages.get(new_msg.name)

        if proto_message is None:
            self.result.add_error(
                "completeness",
                f"In {context}: NewMessage refers to unknown message {new_msg.name}",
                proto_type=new_msg.name,
                rule_name=context
            )
            return None

        # Build map of proto fields by name (both regular fields and oneofs)
        proto_fields_by_name: Dict[str, ProtoField] = {
            field.name: field for field in proto_message.fields
        }
        # Add oneof names as valid fields (oneofs can be set as a whole)
        oneof_names: Set[str] = {oneof.name for oneof in proto_message.oneofs}

        # Track which proto fields were provided
        provided_fields: Set[str] = set()

        # Check each grammar field
        for field_name, field_expr in new_msg.fields:
            provided_fields.add(field_name)

            # Check if field exists in proto (either as regular field or oneof)
            if field_name not in proto_fields_by_name and field_name not in oneof_names:
                self.result.add_error(
                    "field_name",
                    f"In {context}: NewMessage {new_msg.name} has unknown field '{field_name}'",
                    proto_type=new_msg.name,
                    rule_name=context
                )
                continue

            # Skip type checking for oneof fields (they're handled specially)
            if field_name in oneof_names:
                continue

            # Get expected field type from proto
            proto_field = proto_fields_by_name[field_name]
            expected_type = self.type_env._proto_type_to_target(proto_field)

            # Infer actual type from expression
            actual_type = self._infer_expr_type(field_expr)

            if actual_type is not None and not self._types_compatible(actual_type, expected_type):
                self.result.add_error(
                    "field_type",
                    f"In {context}: NewMessage {new_msg.name} field '{field_name}' has type {actual_type}, expected {expected_type}",
                    proto_type=new_msg.name,
                    rule_name=context
                )

        # Check for missing fields (non-repeated, non-optional fields)
        for field in proto_message.fields:
            if field.name not in provided_fields:
                # In proto3, all fields are optional, but we still want to warn about missing fields
                self.result.add_warning(
                    "field_coverage",
                    f"In {context}: NewMessage {new_msg.name} missing field '{field.name}'",
                    proto_type=new_msg.name,
                    rule_name=context
                )

        return None

    def _check_builtin_call_types(self, builtin: Builtin, args: PySequence[TargetExpr], context: str) -> None:
        """Check that Builtin call has correct argument types.

        Args:
            builtin: Builtin function reference
            args: Arguments to the builtin
            context: Rule name or other context for error messages
        """
        name = builtin.name

        # Type check common builtins
        # Some builtins are polymorphic, so we do best-effort checking

        if name == "unwrap_option_or":
            # (Option[T], T) -> T
            if len(args) != 2:
                self.result.add_error(
                    "type_builtin_arity",
                    f"In {context}: builtin 'unwrap_option_or' expects 2 args, got {len(args)}",
                    rule_name=context
                )
            else:
                arg0_type = self._infer_expr_type(args[0])
                arg1_type = self._infer_expr_type(args[1])
                if arg0_type is not None and not isinstance(arg0_type, OptionType):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'unwrap_option_or' arg 0 has type {arg0_type}, expected Option[T]",
                        rule_name=context
                    )
                if arg0_type is not None and arg1_type is not None and isinstance(arg0_type, OptionType):
                    if not self._types_compatible(arg1_type, arg0_type.element_type):
                        self.result.add_error(
                            "type_builtin_arg",
                            f"In {context}: builtin 'unwrap_option_or' arg 1 has type {arg1_type}, expected {arg0_type.element_type}",
                            rule_name=context
                        )

        elif name == "make_tuple":
            # (T1, T2, ...) -> (T1, T2, ...)
            # Any number of args is valid
            pass

        elif name == "list_concat":
            # (List[T], List[T]) -> List[T]
            if len(args) != 2:
                self.result.add_error(
                    "type_builtin_arity",
                    f"In {context}: builtin 'list_concat' expects 2 args, got {len(args)}",
                    rule_name=context
                )
            else:
                arg0_type = self._infer_expr_type(args[0])
                arg1_type = self._infer_expr_type(args[1])
                if arg0_type is not None and not isinstance(arg0_type, ListType):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'list_concat' arg 0 has type {arg0_type}, expected List[T]",
                        rule_name=context
                    )
                if arg1_type is not None and not isinstance(arg1_type, ListType):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'list_concat' arg 1 has type {arg1_type}, expected List[T]",
                        rule_name=context
                    )
                if arg0_type is not None and arg1_type is not None and isinstance(arg0_type, ListType) and isinstance(arg1_type, ListType):
                    if not self._types_compatible(arg0_type.element_type, arg1_type.element_type):
                        self.result.add_error(
                            "type_builtin_arg",
                            f"In {context}: builtin 'list_concat' arg types incompatible: {arg0_type} vs {arg1_type}",
                            rule_name=context
                        )

        elif name == "length":
            # List[T] -> Int64
            if len(args) != 1:
                self.result.add_error(
                    "type_builtin_arity",
                    f"In {context}: builtin 'length' expects 1 arg, got {len(args)}",
                    rule_name=context
                )
            else:
                arg_type = self._infer_expr_type(args[0])
                if arg_type is not None and not isinstance(arg_type, ListType):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'length' arg has type {arg_type}, expected List[T]",
                        rule_name=context
                    )

        elif name == "int64_to_int32":
            # Int64 -> Int32
            if len(args) != 1:
                self.result.add_error(
                    "type_builtin_arity",
                    f"In {context}: builtin 'int64_to_int32' expects 1 arg, got {len(args)}",
                    rule_name=context
                )
            else:
                arg_type = self._infer_expr_type(args[0])
                if arg_type is not None and arg_type != BaseType("Int64"):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'int64_to_int32' arg has type {arg_type}, expected Int64",
                        rule_name=context
                    )

        # For other builtins, we don't have type signatures defined yet
        # We could add more as needed
        return None

    def _infer_expr_type(self, expr: TargetExpr) -> Optional[TargetType]:
        """Infer the type of an expression.

        Returns:
            The type of the expression, or None if it cannot be inferred
        """
        if isinstance(expr, Var):
            return expr.type
        elif isinstance(expr, NewMessage):
            return MessageType(expr.module, expr.name)
        elif isinstance(expr, Call):
            if isinstance(expr.func, Builtin):
                # Infer return type for known builtins
                name = expr.func.name
                if name == "int64_to_int32":
                    return BaseType("Int32")
                elif name == "length":
                    return BaseType("Int64")
                # For other builtins, would need to implement full type inference
                return None
            else:
                return None
        elif isinstance(expr, ListExpr):
            return ListType(expr.element_type)
        elif isinstance(expr, GetField):
            # Would need to look up field type in object's message definition
            # For now, return None (could be enhanced with field type lookup)
            return None
        elif isinstance(expr, GetElement):
            # Infer return type from tuple type and index
            tuple_type = self._infer_expr_type(expr.tuple_expr)
            if isinstance(tuple_type, TupleType):
                if 0 <= expr.index < len(tuple_type.elements):
                    return tuple_type.elements[expr.index]
            return None
        else:
            # Other cases: Lit, Symbol, etc.
            return None

    def _get_rhs_element_types(self, rhs: Rhs) -> List[TargetType]:
        """Get types of non-literal RHS elements in order."""
        types: List[TargetType] = []

        def visit(r: Rhs) -> None:
            if isinstance(r, LitTerminal):
                pass  # Literals don't produce values
            elif isinstance(r, (NamedTerminal, Nonterminal)):
                types.append(r.target_type())
            elif isinstance(r, Star):
                types.append(r.target_type())
            elif isinstance(r, Option):
                types.append(r.target_type())
            elif isinstance(r, Sequence):
                for elem in r.elements:
                    visit(elem)
            return None

        visit(rhs)
        return types

    def _types_compatible(self, t1: TargetType, t2: TargetType) -> bool:
        """Check if two types are compatible.

        Currently checks for exact equality. Could be extended to handle
        subtyping or coercion rules if needed.
        """
        return t1 == t2

    def _check_message_coverage(self) -> None:
        """Check that every proto message has at least one grammar rule producing it."""
        for message_name in self._message_names:
            message = self.parser.messages[message_name]
            message_type = MessageType(message.module, message_name)

            # Find all rules whose LHS type matches this message type
            rules_for_message = []
            for nt, rules in self.grammar.rules.items():
                if nt.type == message_type:
                    rules_for_message.extend(rules)

            if not rules_for_message:
                self.result.add_error(
                    "completeness",
                    f"Proto message '{message_name}' has no grammar rule producing it",
                    proto_type=message_name
                )
        return None

    def _expr_constructs_oneof_variant(self, expr: TargetExpr, variant_name: str) -> bool:
        """Check if expression constructs a oneof variant."""
        if isinstance(expr, Call):
            if isinstance(expr.func, OneOf) and expr.func.field_name == variant_name:
                return True
            # Check func and args recursively
            if self._expr_constructs_oneof_variant(expr.func, variant_name):
                return True
            for arg in expr.args:
                if self._expr_constructs_oneof_variant(arg, variant_name):
                    return True
        elif isinstance(expr, NewMessage):
            # Check all field expressions in NewMessage
            for _, field_expr in expr.fields:
                if self._expr_constructs_oneof_variant(field_expr, variant_name):
                    return True
        elif isinstance(expr, Lambda):
            return self._expr_constructs_oneof_variant(expr.body, variant_name)
        elif isinstance(expr, Let):
            if self._expr_constructs_oneof_variant(expr.init, variant_name):
                return True
            return self._expr_constructs_oneof_variant(expr.body, variant_name)
        elif isinstance(expr, IfElse):
            if self._expr_constructs_oneof_variant(expr.condition, variant_name):
                return True
            if self._expr_constructs_oneof_variant(expr.then_branch, variant_name):
                return True
            return self._expr_constructs_oneof_variant(expr.else_branch, variant_name)
        elif isinstance(expr, ListExpr):
            for elem in expr.elements:
                if self._expr_constructs_oneof_variant(elem, variant_name):
                    return True
        elif isinstance(expr, GetElement):
            return self._expr_constructs_oneof_variant(expr.tuple_expr, variant_name)
        return False

    def _check_oneof_coverage(self) -> None:
        """Check that every oneof variant has at least one alternative production.

        For oneof-only messages, there should be at least one rule per variant.
        Multiple rules for the same variant are allowed (e.g., 'true' and 'conjunction'
        both constructing the conjunction variant).
        """
        for message_name, message in self.parser.messages.items():
            if not self._is_oneof_only_message(message):
                continue

            message_type = MessageType(message.module, message_name)
            rule_nts = self._find_nonterminals_by_type(message_type)
            if not rule_nts:
                continue

            # Collect all rules for this message type
            rules = []
            for rule_nt in rule_nts:
                rules.extend(self.grammar.rules.get(rule_nt, []))

            # Collect all variant names from all oneofs
            all_variants = []
            for oneof in message.oneofs:
                for variant in oneof.fields:
                    all_variants.append(variant.name)

            # Map each variant to the rules that construct it
            variant_to_rules = {v: [] for v in all_variants}
            rules_without_variant = []

            for rule in rules:
                # Find which variant(s) this rule constructs
                constructed_variants = []
                for variant_name in all_variants:
                    if self._expr_constructs_oneof_variant(rule.constructor, variant_name):
                        constructed_variants.append(variant_name)

                if len(constructed_variants) == 0:
                    rules_without_variant.append(rule)
                elif len(constructed_variants) == 1:
                    variant_to_rules[constructed_variants[0]].append(rule)
                else:
                    # Rule constructs multiple variants - error
                    self.result.add_error(
                        "oneof_coverage",
                        f"Rule for '{message_name}' constructs multiple oneof variants: {', '.join(constructed_variants)}",
                        proto_type=message_name,
                        rule_name=rule.lhs.name
                    )

            # Check each variant has at least one rule
            for variant_name in all_variants:
                rules_for_variant = variant_to_rules[variant_name]
                if len(rules_for_variant) == 0:
                    self.result.add_error(
                        "oneof_coverage",
                        f"Oneof variant '{message_name}.{variant_name}' has no grammar alternative",
                        proto_type=message_name
                    )

            # Check for rules that don't construct any variant
            if rules_without_variant:
                self.result.add_error(
                    "oneof_coverage",
                    f"Message '{message_name}' has {len(rules_without_variant)} rule(s) that don't construct any oneof variant",
                    proto_type=message_name
                )

        return None

    def _check_soundness(self) -> None:
        """Check that every grammar rule has a valid type."""
        # Build set of valid proto types
        valid_types: Set[TargetType] = set()

        # Add all message types
        for message_name, message in self.parser.messages.items():
            valid_types.add(MessageType(message.module, message_name))

        # Add all base types
        valid_types.update([
            BaseType("String"),
            BaseType("Int"),
            BaseType("Float"),
            BaseType("Bool"),
            BaseType("Bytes"),
        ])

        # Check each grammar rule's LHS type
        for rule_nt in self.grammar.rules.keys():
            lhs_type = rule_nt.type

            # Check if LHS type is valid
            if lhs_type not in valid_types:
                # Also check if it's a list type wrapping a valid type
                if isinstance(lhs_type, ListType) and lhs_type.element_type in valid_types:
                    continue

                self.result.add_warning(
                    "soundness",
                    f"Grammar rule '{rule_nt.name}' has LHS type {lhs_type} which doesn't correspond to a proto type",
                    rule_name=rule_nt.name
                )
        return None

    def _is_oneof_only_message(self, message: ProtoMessage) -> bool:
        """Check if message contains only a single oneof and no other fields."""
        return len(message.oneofs) > 0 and len(message.fields) == 0

    def _is_message_type(self, type_name: str) -> bool:
        """Check if type is a proto message type."""
        return type_name in self.parser.messages

    def _find_nonterminal(self, name: str) -> Optional[Nonterminal]:
        """Find nonterminal by name."""
        for nt in self.grammar.rules.keys():
            if nt.name == name:
                return nt
        return None

    def _find_nonterminals_by_type(self, target_type: TargetType) -> List[Nonterminal]:
        """Find all nonterminals with the given type."""
        result = []
        for nt in self.grammar.rules.keys():
            if nt.type == target_type:
                result.append(nt)
        return result

    def _get_rhs_nonterminal_names(self, rhs: Rhs) -> Set[str]:
        """Get all nonterminal names referenced in RHS."""
        names: Set[str] = set()

        def visit(r: Rhs) -> None:
            if isinstance(r, Nonterminal):
                names.add(r.name)
            elif isinstance(r, Star):
                visit(r.rhs)
            elif isinstance(r, Option):
                visit(r.rhs)
            elif isinstance(r, Sequence):
                for elem in r.elements:
                    visit(elem)
            return None

        visit(rhs)
        return names

def validate_grammar(
    grammar: Grammar,
    parser: ProtoParser,
) -> ValidationResult:
    """Validate grammar against protobuf specification.

    Args:
        grammar: The generated grammar
        parser: ProtoParser with message definitions

    Returns:
        ValidationResult with any issues found
    """
    validator = GrammarValidator(grammar, parser)
    return validator.validate()
