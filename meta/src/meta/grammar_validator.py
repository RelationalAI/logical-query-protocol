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

from collections.abc import Sequence as PySequence

from .grammar import (
    Grammar,
    LitTerminal,
    NamedTerminal,
    Nonterminal,
    Option,
    Rhs,
    Rule,
    Sequence,
    Star,
)
from .proto_ast import ProtoField, ProtoMessage
from .proto_parser import ProtoParser
from .target import (
    BaseType,
    Builtin,
    Call,
    GetElement,
    GetField,
    IfElse,
    Lambda,
    Let,
    ListExpr,
    ListType,
    MessageType,
    NewMessage,
    OneOf,
    OptionType,
    SequenceType,
    TargetExpr,
    TargetType,
    TupleType,
    VarType,
)
from .target_utils import is_subtype, types_compatible
from .target_visitor import TargetExprVisitor
from .type_env import TypeEnv
from .validation_result import ValidationResult


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
        self._rule_names: set[str] = {nt.name for nt in grammar.rules.keys()}
        self._message_names: set[str] = set(parser.messages.keys())

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
                rule_name=nt.name,
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
                    rule_name=rule_name,
                )
        elif isinstance(rhs, Option):
            if not isinstance(rhs.rhs, (NamedTerminal, Nonterminal)):
                self.result.add_error(
                    "structure",
                    f"Rule '{rule_name}': Option must contain NamedTerminal or Nonterminal, got {type(rhs.rhs).__name__}",
                    rule_name=rule_name,
                )
        elif isinstance(rhs, Sequence):
            for elem in rhs.elements:
                if isinstance(elem, Sequence):
                    self.result.add_error(
                        "structure",
                        f"Rule '{rule_name}': Sequence cannot contain nested Sequence",
                        rule_name=rule_name,
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
                rule_name=rule_name,
            )
            return None  # Can't check types if arity mismatch

        # Check each parameter type matches corresponding RHS element type
        # RHS element type should be a subtype of param type (rhs_type <: param_type)
        for i, (param_type, rhs_type) in enumerate(zip(param_types, rhs_types)):
            if not is_subtype(rhs_type, param_type):
                param_name = rule.constructor.params[i].name
                self.result.add_error(
                    "type_param",
                    f"Rule '{rule_name}': param '{param_name}' has type {param_type} but RHS element has type {rhs_type}",
                    rule_name=rule_name,
                )

        # Check return type matches LHS type
        lhs_type = rule.lhs.type

        # Infer the actual type of the body expression
        body_type = self._infer_expr_type(rule.constructor.body)

        # If we can infer the body type, check it is a subtype of the declared return type
        if body_type is not None and not is_subtype(body_type, lhs_type):
            self.result.add_error(
                "type_return",
                f"Rule '{rule_name}': lambda body has type {body_type} but LHS expects {lhs_type}",
                rule_name=rule_name,
            )

        # Type check the lambda body expression
        self._check_expr_types(rule.constructor.body, rule_name)

        return None

    def _check_expr_types(self, expr: TargetExpr, context: str) -> None:
        """Recursively type check an expression."""
        _ExprTypeChecker(self, context).visit(expr)

    def _check_new_message_types(self, new_msg: NewMessage, context: str) -> None:
        """Check that NewMessage has correct field names and types.

        Args:
            new_msg: NewMessage node to validate
            context: Rule name or other context for error messages
        """
        # Get the proto message (messages are keyed by name only, not module.name)
        proto_message = self.parser.messages.get(new_msg.name)

        if proto_message is None:
            # Skip if message is in ignored list
            if new_msg.name not in self.grammar.ignored_completeness:
                self.result.add_error(
                    "completeness",
                    f"In {context}: NewMessage refers to unknown message {new_msg.name}",
                    proto_type=new_msg.name,
                    rule_name=context,
                )
            return None

        # Build map of proto fields by name (both regular fields and oneofs)
        proto_fields_by_name: dict[str, ProtoField] = {
            field.name: field for field in proto_message.fields
        }
        # Add oneof variant fields to the map
        for oneof in proto_message.oneofs:
            for variant_field in oneof.fields:
                proto_fields_by_name[variant_field.name] = variant_field
        # Add oneof names as valid fields (oneofs can be set as a whole)
        oneof_names: set[str] = {oneof.name for oneof in proto_message.oneofs}

        # Track which proto fields were provided
        provided_fields: set[str] = set()

        # Check each grammar field
        for field_name, field_expr in new_msg.fields:
            provided_fields.add(field_name)

            # Check if field exists in proto (either as regular field or oneof)
            if field_name not in proto_fields_by_name and field_name not in oneof_names:
                self.result.add_error(
                    "field_name",
                    f"In {context}: NewMessage {new_msg.name} has unknown field '{field_name}'",
                    proto_type=new_msg.name,
                    rule_name=context,
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

            # Check actual type is a subtype of expected type (actual_type <: expected_type)
            if actual_type is not None and not is_subtype(actual_type, expected_type):
                self.result.add_error(
                    "field_type",
                    f"In {context}: NewMessage {new_msg.name} field '{field_name}' has type {actual_type}, expected {expected_type}",
                    proto_type=new_msg.name,
                    rule_name=context,
                )

        # Check for missing fields
        for field in proto_message.fields:
            if field.name not in provided_fields:
                self.result.add_error(
                    "field_coverage",
                    f"In {context}: NewMessage {new_msg.name} missing field '{field.name}'",
                    proto_type=new_msg.name,
                    rule_name=context,
                )

        return None

    def _check_builtin_call_types(
        self, builtin: Builtin, args: PySequence[TargetExpr], context: str
    ) -> None:
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
            # (Option[T], U) -> Join[T, U] where Join is the common supertype
            # Valid if T <: U or U <: T (types have a common supertype)
            if len(args) != 2:
                self.result.add_error(
                    "type_builtin_arity",
                    f"In {context}: builtin 'unwrap_option_or' expects 2 args, got {len(args)}",
                    rule_name=context,
                )
            else:
                arg0_type = self._infer_expr_type(args[0])
                arg1_type = self._infer_expr_type(args[1])
                if arg0_type is not None and not isinstance(arg0_type, OptionType):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'unwrap_option_or' arg 0 has type {arg0_type}, expected Option[T]",
                        rule_name=context,
                    )
                if (
                    arg0_type is not None
                    and arg1_type is not None
                    and isinstance(arg0_type, OptionType)
                ):
                    # Check that types have a common supertype
                    t = arg0_type.element_type
                    u = arg1_type
                    if not types_compatible(t, u):
                        self.result.add_error(
                            "type_builtin_arg",
                            f"In {context}: builtin 'unwrap_option_or' types {t} and {u} have no common supertype",
                            rule_name=context,
                        )

        elif name == "tuple":
            # (T1, T2, ...) -> (T1, T2, ...)
            # Any number of args is valid
            pass

        elif name == "list_concat":
            # (List[T], List[U]) -> List[Join[T, U]] where Join is the common supertype
            if len(args) != 2:
                self.result.add_error(
                    "type_builtin_arity",
                    f"In {context}: builtin 'list_concat' expects 2 args, got {len(args)}",
                    rule_name=context,
                )
            else:
                arg0_type = self._infer_expr_type(args[0])
                arg1_type = self._infer_expr_type(args[1])
                if arg0_type is not None and not isinstance(
                    arg0_type, (SequenceType, ListType)
                ):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'list_concat' arg 0 has type {arg0_type}, expected Sequence[T]",
                        rule_name=context,
                    )
                if arg1_type is not None and not isinstance(
                    arg1_type, (SequenceType, ListType)
                ):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'list_concat' arg 1 has type {arg1_type}, expected Sequence[T]",
                        rule_name=context,
                    )
                if (
                    arg0_type is not None
                    and arg1_type is not None
                    and isinstance(arg0_type, (SequenceType, ListType))
                    and isinstance(arg1_type, (SequenceType, ListType))
                ):
                    # Check that element types have a common supertype
                    t = arg0_type.element_type
                    u = arg1_type.element_type
                    if not types_compatible(t, u):
                        self.result.add_error(
                            "type_builtin_arg",
                            f"In {context}: builtin 'list_concat' element types {t} and {u} have no common supertype",
                            rule_name=context,
                        )

        elif name == "length":
            # List[T] -> Int64
            if len(args) != 1:
                self.result.add_error(
                    "type_builtin_arity",
                    f"In {context}: builtin 'length' expects 1 arg, got {len(args)}",
                    rule_name=context,
                )
            else:
                arg_type = self._infer_expr_type(args[0])
                if arg_type is not None and not isinstance(
                    arg_type, (SequenceType, ListType)
                ):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'length' arg has type {arg_type}, expected Sequence[T]",
                        rule_name=context,
                    )

        elif name == "int64_to_int32":
            # Int64 -> Int32
            if len(args) != 1:
                self.result.add_error(
                    "type_builtin_arity",
                    f"In {context}: builtin 'int64_to_int32' expects 1 arg, got {len(args)}",
                    rule_name=context,
                )
            else:
                arg_type = self._infer_expr_type(args[0])
                if arg_type is not None and arg_type != BaseType("Int64"):
                    self.result.add_error(
                        "type_builtin_arg",
                        f"In {context}: builtin 'int64_to_int32' arg has type {arg_type}, expected Int64",
                        rule_name=context,
                    )

        # For other builtins, we don't have type signatures defined yet
        # We could add more as needed
        return None

    def _infer_expr_type(self, expr: TargetExpr) -> TargetType | None:
        """Infer the type of an expression.

        Returns:
            The type of the expression, or None if it cannot be inferred.
        """
        # Special case for tuple builtin - need to compute TupleType from args
        if (
            isinstance(expr, Call)
            and isinstance(expr.func, Builtin)
            and expr.func.name == "tuple"
        ):
            arg_types = [self._infer_expr_type(arg) for arg in expr.args]
            if all(t is not None for t in arg_types):
                return TupleType(tuple(t for t in arg_types if t is not None))
            return None

        try:
            result = expr.target_type()
            # Don't return VarType - treat as unknown
            if isinstance(result, VarType):
                return None
            return result
        except (NotImplementedError, ValueError):
            return None

    def _get_rhs_element_types(self, rhs: Rhs) -> list[TargetType]:
        """Get types of non-literal RHS elements in order."""
        types: list[TargetType] = []

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

    def _check_message_coverage(self) -> None:
        """Check that every proto message has at least one grammar rule producing it.

        Skip messages that are only used as oneof variant types, as these don't need
        standalone rules - they are constructed inline within the parent message rule.
        """
        # Find messages that are only used as oneof variant types
        oneof_only_messages = set()
        for message in self.parser.messages.values():
            for oneof in message.oneofs:
                for field in oneof.fields:
                    # Check if this field's type is a message type used only in oneofs
                    field_type = field.type
                    if field_type in self.parser.messages:
                        oneof_only_messages.add(field_type)

        for message_name in self._message_names:
            # Skip messages that are only used in oneofs
            if message_name in oneof_only_messages:
                continue

            message = self.parser.messages[message_name]
            message_type = MessageType(message.module, message_name)

            # Find all rules whose LHS type matches this message type
            rules_for_message = []
            for nt, rules in self.grammar.rules.items():
                if nt.type == message_type:
                    rules_for_message.extend(rules)

            if not rules_for_message:
                # Skip if message is in ignored list
                if message_name not in self.grammar.ignored_completeness:
                    self.result.add_error(
                        "completeness",
                        f"Proto message '{message_name}' has no grammar rule producing it",
                        proto_type=message_name,
                    )
        return None

    def _expr_constructs_oneof_variant(
        self, expr: TargetExpr, variant_name: str
    ) -> bool:
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
            # Check if this NewMessage directly sets the variant field
            for field_name, field_expr in expr.fields:
                if field_name == variant_name:
                    return True
                # Also check recursively in field expressions
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
                    if self._expr_constructs_oneof_variant(
                        rule.constructor, variant_name
                    ):
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
                        rule_name=rule.lhs.name,
                    )

            # Check each variant has at least one rule
            for variant_name in all_variants:
                rules_for_variant = variant_to_rules[variant_name]
                if len(rules_for_variant) == 0:
                    self.result.add_error(
                        "oneof_coverage",
                        f"Oneof variant '{message_name}.{variant_name}' has no grammar alternative",
                        proto_type=message_name,
                    )

            # Note: We don't report an error for rules that don't construct any variant.
            # Pass-through rules (that just return a value from another nonterminal) are
            # legitimate as long as all variants have at least one rule that constructs them.

        return None

    def _is_valid_type(self, typ: TargetType) -> bool:
        """Check if a type is valid.

        A type is valid if:
        - It's a BaseType (primitive like String, Int64, Boolean, etc.)
        - It's a MessageType that exists in the proto spec
        - It's a ListType where the element type is valid
        - It's an OptionType where the element type is valid
        - It's a TupleType where all element types are valid
        """
        if isinstance(typ, BaseType):
            # All base types are valid primitives
            return True

        if isinstance(typ, MessageType):
            # Check if message exists in proto spec
            # ProtoParser.messages is a flat dict mapping message_name -> ProtoMessage
            # where ProtoMessage has a module attribute
            msg = self.parser.messages.get(typ.name)
            if msg and msg.module == typ.module:
                return True
            return False

        if isinstance(typ, SequenceType):
            return self._is_valid_type(typ.element_type)

        if isinstance(typ, ListType):
            # List is valid if element type is valid
            return self._is_valid_type(typ.element_type)

        if isinstance(typ, OptionType):
            # Option is valid if element type is valid
            return self._is_valid_type(typ.element_type)

        if isinstance(typ, TupleType):
            # Tuple is valid if all element types are valid
            return all(self._is_valid_type(elem_type) for elem_type in typ.elements)

        # VarType, FunctionType, etc. are not directly valid for nonterminal LHS types
        return False

    def _check_soundness(self) -> None:
        """Check that all grammar rules have valid types.

        A rule's LHS type is valid if it's composed of:
        - Base types (primitives)
        - Proto message types
        - Lists, Options, or Tuples of valid types
        """
        # Check each nonterminal
        for rule_nt in self.grammar.rules.keys():
            lhs_type = rule_nt.type
            if not self._is_valid_type(lhs_type):
                self.result.add_error(
                    "soundness",
                    f"Grammar rule '{rule_nt.name}' has LHS type {lhs_type} which is not a valid type",
                    rule_name=rule_nt.name,
                )
        return None

    def _is_oneof_only_message(self, message: ProtoMessage) -> bool:
        """Check if message contains only a single oneof and no other fields."""
        return len(message.oneofs) > 0 and len(message.fields) == 0

    def _find_nonterminals_by_type(self, target_type: TargetType) -> list[Nonterminal]:
        """Find all nonterminals with the given type."""
        result = []
        for nt in self.grammar.rules.keys():
            if nt.type == target_type:
                result.append(nt)
        return result

class _ExprTypeChecker(TargetExprVisitor):
    """Type checker for TargetExpr trees."""

    def __init__(self, validator: GrammarValidator, context: str):
        super().__init__()
        self._validator = validator
        self._context = context

    def visit_Call(self, expr: Call) -> None:
        if isinstance(expr.func, Builtin):
            self._validator._check_builtin_call_types(
                expr.func, expr.args, self._context
            )
        else:
            self.visit(expr.func)
        for arg in expr.args:
            self.visit(arg)

    def visit_NewMessage(self, expr: NewMessage) -> None:
        self._validator._check_new_message_types(expr, self._context)
        for _, field_expr in expr.fields:
            self.visit(field_expr)

    def visit_GetField(self, expr: GetField) -> None:
        self.visit(expr.object)
        obj_type = self._validator._infer_expr_type(expr.object)
        if obj_type is not None and not is_subtype(obj_type, expr.message_type):
            self._validator.result.add_error(
                "type_field_access",
                f"In {self._context}: GetField expects object of type {expr.message_type}, got {obj_type}",
                rule_name=self._context,
            )

    def visit_GetElement(self, expr: GetElement) -> None:
        self.visit(expr.tuple_expr)
        tuple_type = self._validator._infer_expr_type(expr.tuple_expr)
        if tuple_type is not None and not isinstance(tuple_type, TupleType):
            self._validator.result.add_error(
                "type_tuple_element",
                f"In {self._context}: GetElement expects tuple type, got {tuple_type}",
                rule_name=self._context,
            )
        if isinstance(tuple_type, TupleType):
            if expr.index < 0 or expr.index >= len(tuple_type.elements):
                self._validator.result.add_error(
                    "type_tuple_element",
                    f"In {self._context}: GetElement index {expr.index} out of bounds for tuple with {len(tuple_type.elements)} elements",
                    rule_name=self._context,
                )


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
