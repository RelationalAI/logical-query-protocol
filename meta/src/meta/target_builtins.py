"""Builtin function registry for target IR.

This module provides a registry of all builtin functions available in the target IR,
including their type signatures. This is used by:
- sexp_target.py: Validate builtin names during parsing
- codegen_*.py: Reference for builtin signatures
- Grammar validation: Ensure builtins referenced in grammar are defined

The code generators maintain their own implementation registries for how to generate
code for each builtin, but they should validate against this registry.
"""

from dataclasses import dataclass

from .target import (
    BaseType,
    Builtin,
    DictType,
    FunctionType,
    ListType,
    MessageType,
    OptionType,
    SequenceType,
    TargetType,
    TupleType,
    VarType,
)

# Type aliases for convenience
ANY = VarType("Any")
INT32 = BaseType("Int32")
INT64 = BaseType("Int64")
FLOAT64 = BaseType("Float64")
STRING = BaseType("String")
BOOLEAN = BaseType("Boolean")
BYTES = BaseType("Bytes")
TOKEN = VarType("Token")
VOID = BaseType("Void")
NONE = OptionType(BaseType("Never"))  # the type of None
NEVER = BaseType("Never")


@dataclass(frozen=True)
class BuiltinSignature:
    """Signature of a builtin function.

    name: Name of the builtin
    param_types: List of parameter types (empty for zero-arity builtins)
                 Use VarType("T") for polymorphic parameters
                 Use -1 for variadic (any number of args)
    return_type: Return type of the builtin
    is_primitive: True if this builtin has no IR body and must be implemented
                  by the code generator. False if it has an IR definition.
    """

    name: str
    param_types: list[TargetType] | int  # List of types or -1 for variadic
    return_type: TargetType
    is_primitive: bool = True

    @property
    def arity(self) -> int:
        """Get arity of builtin. Returns -1 for variadic."""
        if isinstance(self.param_types, int):
            return self.param_types
        return len(self.param_types)

    def is_variadic(self) -> bool:
        """Check if builtin accepts variable number of arguments."""
        return isinstance(self.param_types, int) and self.param_types == -1


# Registry of all known builtins
# This should be kept in sync with what code generators implement
BUILTIN_REGISTRY: dict[str, BuiltinSignature] = {}


def register_builtin(
    name: str,
    param_types: list[TargetType] | int,
    return_type: TargetType,
    is_primitive: bool = True,
) -> None:
    """Register a builtin in the registry."""
    BUILTIN_REGISTRY[name] = BuiltinSignature(
        name, param_types, return_type, is_primitive
    )


def get_builtin(name: str) -> BuiltinSignature | None:
    """Get builtin signature by name, or None if not found."""
    return BUILTIN_REGISTRY.get(name)


def is_builtin(name: str) -> bool:
    """Check if a name is a registered builtin."""
    return name in BUILTIN_REGISTRY


# === Polymorphic helper type variables ===
T = VarType("T")
T1 = VarType("T1")
T2 = VarType("T2")
K = VarType("K")
V = VarType("V")

# === Basic operations ===
register_builtin("add", [INT64, INT64], INT64)
register_builtin("subtract", [INT64, INT64], INT64)
register_builtin("multiply", [INT64, INT64], INT64)
register_builtin("divide", [INT64, INT64], INT64)
register_builtin("modulo", [INT64, INT64], INT64)

# === Comparison operations ===
register_builtin("equal", [T, T], BOOLEAN)
register_builtin("not_equal", [T, T], BOOLEAN)
register_builtin("less_than", [T, T], BOOLEAN)
register_builtin("less_equal", [T, T], BOOLEAN)
register_builtin("greater_than", [T, T], BOOLEAN)
register_builtin("greater_equal", [T, T], BOOLEAN)

# === Boolean operations ===
register_builtin("not", [BOOLEAN], BOOLEAN)
register_builtin("and", [BOOLEAN, BOOLEAN], BOOLEAN)
register_builtin("or", [BOOLEAN, BOOLEAN], BOOLEAN)

# === Option operations ===
register_builtin("none", [], OptionType(T))  # Returns None/nothing/null
register_builtin("some", [T], OptionType(T))
register_builtin("is_some", [OptionType(T)], BOOLEAN)
register_builtin("is_none", [OptionType(T)], BOOLEAN)
register_builtin("unwrap_option", [OptionType(T)], T)
register_builtin("unwrap_option_or", [OptionType(T), T], T)

# === List/Sequence operations ===
register_builtin("list_concat", [SequenceType(T), SequenceType(T)], ListType(T))
register_builtin(
    "list_push", [ListType(T), T], VOID
)  # Mutating push: list.append(item) / push!(list, item)
register_builtin(
    "list_slice", [SequenceType(T), INT64, INT64], ListType(T)
)  # list[start:end]
register_builtin("list_sort", [SequenceType(T)], ListType(T))
register_builtin("length", [SequenceType(T)], INT64)
register_builtin("map", [FunctionType([T1], T2), SequenceType(T1)], ListType(T2))
register_builtin("append", [SequenceType(T), T], ListType(T))  # non-mutating append

# === Tuple operations ===
register_builtin("tuple", -1, T)  # Variadic: makes tuple from arguments

# === String operations ===
register_builtin("string_concat", [STRING, STRING], STRING)
register_builtin("string_to_upper", [STRING], STRING)
register_builtin("string_to_lower", [STRING], STRING)
register_builtin("string_in_list", [STRING, SequenceType(STRING)], BOOLEAN)
register_builtin("encode_string", [STRING], BYTES)

# === Type conversions ===
register_builtin("int64_to_int32", [INT64], INT32)
register_builtin("int32_to_int64", [INT32], INT64)
register_builtin("decode_string", [BYTES], STRING)
register_builtin("to_ptr_int64", [INT64], OptionType(INT64))
register_builtin("to_ptr_string", [STRING], OptionType(STRING))
register_builtin("to_ptr_bool", [BOOLEAN], OptionType(BOOLEAN))

# === Parser primitives (lexer/parser operations) ===
register_builtin("match_lookahead_terminal", [STRING, INT64], BOOLEAN)
register_builtin("match_lookahead_literal", [STRING, INT64], BOOLEAN)
register_builtin("consume_literal", [STRING], VOID)
register_builtin("consume_terminal", [STRING], TOKEN)
register_builtin("consume", [STRING], TOKEN)  # Generic consume
register_builtin("current_token", [], TOKEN)

# === Error handling ===
register_builtin("error", [STRING], BaseType("Never"))
register_builtin("error_with_token", [STRING, TOKEN], BaseType("Never"))

# === Protobuf-specific ===
register_builtin(
    "fragment_id_from_string", [STRING], MessageType("fragments", "FragmentId")
)
register_builtin(
    "fragment_id_to_string", [MessageType("fragments", "FragmentId")], STRING
)
register_builtin(
    "relation_id_from_string", [STRING], MessageType("logic", "RelationId")
)
register_builtin(
    "relation_id_from_uint128",
    [MessageType("logic", "UInt128Value")],
    MessageType("logic", "RelationId"),
)
register_builtin(
    "relation_id_to_string", [MessageType("logic", "RelationId")], OptionType(STRING)
)
register_builtin(
    "relation_id_to_uint128",
    [MessageType("logic", "RelationId")],
    MessageType("logic", "UInt128Value"),
)
register_builtin(
    "construct_fragment",
    [
        MessageType("fragments", "FragmentId"),
        SequenceType(MessageType("logic", "Declaration")),
    ],
    MessageType("fragments", "Fragment"),
)
register_builtin("start_fragment", [MessageType("fragments", "FragmentId")], VOID)
register_builtin("start_pretty_fragment", [MessageType("fragments", "Fragment")], VOID)

# === Dict operations ===
register_builtin("dict_from_list", [SequenceType(TupleType([K, V]))], DictType(K, V))
register_builtin("dict_get", [DictType(K, V), K], OptionType(V))

# === Protobuf operations ===
register_builtin("has_proto_field", [T, STRING], BOOLEAN)  # msg.HasField(field_name)
register_builtin("which_one_of", [T, STRING], STRING)  # msg.WhichOneof(oneof_name)

# === General helpers ===
register_builtin("is_empty", [SequenceType(T)], BOOLEAN)  # len(list) == 0
register_builtin("enum_value", [STRING, STRING], T)  # enum_value(EnumType, ValueName)
register_builtin("greater", [INT64, INT64], BOOLEAN)
register_builtin("to_string", [T], STRING)

# === Pretty-printing IO operations ===
register_builtin("write_io", [STRING], VOID)
register_builtin("newline_io", [], VOID)
register_builtin("indent_io", [], VOID)
register_builtin("indent_sexp_io", [], VOID)
register_builtin("dedent_io", [], VOID)
register_builtin("try_flat_io", [T, T1], OptionType(STRING))

# === Formatting for terminal types ===
register_builtin("format_int64", [INT64], STRING)
register_builtin("format_int32", [INT32], STRING)
register_builtin("format_float64", [FLOAT64], STRING)
register_builtin("format_string", [STRING], STRING)
register_builtin("format_symbol", [STRING], STRING)
register_builtin("format_bool", [BOOLEAN], STRING)
register_builtin("format_decimal", [MessageType("logic", "DecimalValue")], STRING)
register_builtin("format_int128", [MessageType("logic", "Int128Value")], STRING)
register_builtin("format_uint128", [MessageType("logic", "UInt128Value")], STRING)
register_builtin("format_bytes", [BYTES], STRING)

# === Pretty-printing dispatch ===
register_builtin("pp_dispatch", [T], VOID)

# === Sequence indexing ===
register_builtin("get_at", [SequenceType(T), INT64], T)

# === Provenance tracking ===
register_builtin("span_start", [], INT64)
register_builtin("record_span", [INT64], VOID)


# === Validation functions ===


def validate_builtin_call(name: str, num_args: int) -> str | None:
    """Validate a builtin call.

    Returns None if valid, or an error message if invalid.
    Only validates known builtins - unknown builtins are allowed.
    """
    builtin = get_builtin(name)
    if builtin is None:
        return None  # Unknown builtins are allowed

    if builtin.is_variadic():
        return None  # Any number of args is valid

    expected = builtin.arity
    if num_args != expected:
        return f"Builtin '{name}' expects {expected} arguments, got {num_args}"

    return None


def make_builtin(name: str) -> Builtin:
    """Create a Builtin expression with type looked up from the registry.

    Args:
        name: Name of the builtin function

    Returns:
        Builtin expression with its FunctionType

    Raises:
        ValueError: If the builtin is not registered
    """
    sig = get_builtin(name)
    if sig is None:
        raise ValueError(f"Unknown builtin: {name}")
    # Convert BuiltinSignature to FunctionType
    param_types: list[TargetType] = (
        [] if isinstance(sig.param_types, int) else list(sig.param_types)
    )
    func_type = FunctionType(param_types, sig.return_type)
    return Builtin(name, func_type)


def make_builtin_with_type(name: str, func_type: FunctionType) -> Builtin:
    """Create a Builtin expression with a specified type.

    This is useful for tests that need builtins not in the registry,
    or when the type is known from context.

    Args:
        name: Name of the builtin function
        func_type: The function type for this builtin

    Returns:
        Builtin expression with the specified type
    """
    return Builtin(name, func_type)


__all__ = [
    "BuiltinSignature",
    "BUILTIN_REGISTRY",
    "register_builtin",
    "get_builtin",
    "is_builtin",
    "validate_builtin_call",
    "make_builtin",
    "make_builtin_with_type",
    # Type constants
    "ANY",
    "INT64",
    "INT32",
    "FLOAT64",
    "STRING",
    "BOOLEAN",
    "BYTES",
    "VOID",
    "NONE",
    "NEVER",
    "T",
    "T1",
    "T2",
    "K",
    "V",
]
