"""Type environment for validating grammar expressions against protobuf specification."""

from .proto_ast import ProtoField, ProtoMessage
from .proto_parser import ProtoParser
from .target import (
    BaseType,
    FunctionType,
    MessageType,
    OptionType,
    SequenceType,
    TargetType,
)
from .target_builtins import BUILTIN_REGISTRY

# Mapping from protobuf primitive types to base type names
_PRIMITIVE_TO_BASE_TYPE = {
    "string": "String",
    "int32": "Int32",
    "int64": "Int64",
    "uint32": "UInt32",
    "uint64": "UInt64",
    "fixed64": "Int64",
    "bool": "Boolean",
    "double": "Float64",
    "float": "Float32",
    "bytes": "Bytes",
}


class TypeEnv:
    """Type environment for validating grammar expressions.

    Maintains:
    - Message field types from protobuf specification
    - Builtin function signatures (from target_builtins registry)
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
        self._message_field_types: dict[tuple[str, str], list[TargetType]] = {}

        # Local variable scopes: stack of frames (innermost first)
        # Each frame is a dict: var_name -> type
        self._local_scopes: list[dict[str, TargetType]] = []

        # Build type information from proto
        self._build_message_types()

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
            raise ValueError(f"Unknown proto type: {proto_field.type}")

        # Wrap in Option if optional
        if proto_field.is_optional:
            base_type = OptionType(base_type)

        # Wrap in Sequence if repeated
        if proto_field.is_repeated:
            base_type = SequenceType(base_type)

        return base_type

    def get_message_field_types(
        self, module: str, name: str
    ) -> list[TargetType] | None:
        """Get field types for a message constructor.

        Args:
            module: Protobuf module name
            name: Message type name

        Returns:
            List of field types, or None if message not found
        """
        return self._message_field_types.get((module, name))

    def get_builtin_type(self, name: str) -> FunctionType | None:
        """Get function type for a builtin.

        Args:
            name: Builtin function name

        Returns:
            Function type, or None if builtin not found
        """
        sig = BUILTIN_REGISTRY.get(name)
        if sig is None:
            return None
        # Convert BuiltinSignature to FunctionType
        # Variadic builtins (param_types == -1) get empty param list
        param_types = [] if isinstance(sig.param_types, int) else list(sig.param_types)
        return FunctionType(param_types=param_types, return_type=sig.return_type)

    def is_oneof_message(self, module: str, name: str) -> bool:
        """Check if a message is a oneof-only message."""
        if name in self.parser.messages:
            return self._is_oneof_only_message(self.parser.messages[name])
        return False

    def lookup_var(self, name: str) -> TargetType | None:
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

    def push_scope(self, bindings: dict[str, TargetType]) -> None:
        """Enter a new lexical scope with given variable bindings.

        Args:
            bindings: Variable name -> type mappings for new scope
        """
        self._local_scopes.append(bindings.copy())

    def pop_scope(self) -> None:
        """Exit the current lexical scope."""
        if self._local_scopes:
            self._local_scopes.pop()
