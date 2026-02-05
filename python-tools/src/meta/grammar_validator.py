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

from typing import List, Optional, Set, Sequence as PySequence, Dict

from .grammar import Grammar, Rule, Nonterminal, Rhs, LitTerminal, NamedTerminal, Star, Option, Sequence
from .proto_parser import ProtoParser
from .proto_ast import ProtoMessage, ProtoField
from .target import (
    TargetType, TargetExpr, Call, NewMessage, Builtin, Var, IfElse, Let, Seq, ListExpr, GetField,
    GetElement, BaseType, BottomType, VarType, MessageType, ListType, OptionType, TupleType, FunctionType, Lambda, OneOf, Lit
)
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
        # RHS element type should be a subtype of param type (rhs_type <: param_type)
        for i, (param_type, rhs_type) in enumerate(zip(param_types, rhs_types)):
            if not self._is_subtype(rhs_type, param_type):
                param_name = rule.constructor.params[i].name
                self.result.add_error(
                    "type_param",
                    f"Rule '{rule_name}': param '{param_name}' has type {param_type} but RHS element has type {rhs_type}",
                    rule_name=rule_name
                )

        # Check return type matches LHS type
        lhs_type = rule.lhs.type

        # Infer the actual type of the body expression
        body_type = self._infer_expr_type(rule.constructor.body)

        # If we can infer the body type, check it is a subtype of the declared return type
        if body_type is not None and not self._is_subtype(body_type, lhs_type):
            self.result.add_error(
                "type_return",
                f"Rule '{rule_name}': lambda body has type {body_type} but LHS expects {lhs_type}",
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
            # Skip if message is in ignored list
            if new_msg.name not in self.grammar.ignored_completeness:
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
        # Add oneof variant fields to the map
        for oneof in proto_message.oneofs:
            for variant_field in oneof.fields:
                proto_fields_by_name[variant_field.name] = variant_field
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

            # Check actual type is a subtype of expected type (actual_type <: expected_type)
            if actual_type is not None and not self._is_subtype(actual_type, expected_type):
                self.result.add_error(
                    "field_type",
                    f"In {context}: NewMessage {new_msg.name} field '{field_name}' has type {actual_type}, expected {expected_type}",
                    proto_type=new_msg.name,
                    rule_name=context
                )

        # Check for missing fields
        for field in proto_message.fields:
            if field.name not in provided_fields:
                self.result.add_error(
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
            # (Option[T], U) -> Join[T, U] where Join is the common supertype
            # Valid if T <: U or U <: T (types have a common supertype)
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
                    # Check that types have a common supertype
                    t = arg0_type.element_type
                    u = arg1_type
                    if not self._types_compatible(t, u):
                        self.result.add_error(
                            "type_builtin_arg",
                            f"In {context}: builtin 'unwrap_option_or' types {t} and {u} have no common supertype",
                            rule_name=context
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
                    # Check that element types have a common supertype
                    t = arg0_type.element_type
                    u = arg1_type.element_type
                    if not self._types_compatible(t, u):
                        self.result.add_error(
                            "type_builtin_arg",
                            f"In {context}: builtin 'list_concat' element types {t} and {u} have no common supertype",
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
                elif name == "tuple":
                    # Infer tuple type from argument types
                    arg_types = [self._infer_expr_type(arg) for arg in expr.args]
                    if all(t is not None for t in arg_types):
                        return TupleType(tuple(t for t in arg_types if t is not None))
                    return None
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
        elif isinstance(expr, Lit):
            # Infer type from literal value
            if isinstance(expr.value, bool):
                return BaseType("Boolean")
            elif isinstance(expr.value, int):
                return BaseType("Int64")
            elif isinstance(expr.value, float):
                return BaseType("Float64")
            elif isinstance(expr.value, str):
                return BaseType("String")
            return None
        else:
            # Other cases: Symbol, etc.
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

    def _is_subtype(self, t1: TargetType, t2: TargetType) -> bool:
        """Check if t1 is a subtype of t2 (t1 <: t2).

        Subtyping rules:
        - Reflexivity: T <: T
        - Bottom <: T for all T (Bottom is the empty type)
        - T <: Any for all T (Any is the top type)
        - List is covariant: List[A] <: List[B] if A <: B
        - Option is covariant: Option[A] <: Option[B] if A <: B
        - Tuple is covariant: (A1, A2, ...) <: (B1, B2, ...) if Ai <: Bi for all i
        """
        if t1 == t2:
            return True
        # Bottom is a subtype of everything
        if isinstance(t1, BottomType):
            return True
        # T <: Any for all T (Any is the top type)
        if isinstance(t2, BaseType) and t2.name == "Any":
            return True
        # List is covariant: List[A] <: List[B] if A <: B
        if isinstance(t1, ListType) and isinstance(t2, ListType):
            return self._is_subtype(t1.element_type, t2.element_type)
        # Option is covariant: Option[A] <: Option[B] if A <: B
        if isinstance(t1, OptionType) and isinstance(t2, OptionType):
            return self._is_subtype(t1.element_type, t2.element_type)
        # Tuple is covariant: check element-wise
        if isinstance(t1, TupleType) and isinstance(t2, TupleType):
            if len(t1.elements) != len(t2.elements):
                return False
            return all(self._is_subtype(e1, e2) for e1, e2 in zip(t1.elements, t2.elements))
        return False

    def _types_compatible(self, t1: TargetType, t2: TargetType) -> bool:
        """Check if types are compatible (t1 <: t2 or t2 <: t1).

        Two types are compatible if one is a subtype of the other,
        meaning they have a common supertype.
        """
        return self._is_subtype(t1, t2) or self._is_subtype(t2, t1)

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
