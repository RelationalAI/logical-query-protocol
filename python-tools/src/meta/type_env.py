"""Type environment for validating grammar expressions against protobuf specification."""

from typing import Dict, List, Optional

from .proto_parser import ProtoParser
from .proto_ast import ProtoMessage, ProtoField
from .target import (
    TargetType, BaseType, VarType, MessageType, ListType, OptionType, TupleType, FunctionType
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
