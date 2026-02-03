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
from typing import Dict, List, Optional, Union
from .target import TargetType, BaseType, VarType, MessageType, ListType, TupleType, OptionType, FunctionType, DictType

# Type aliases for convenience
ANY = VarType("Any")
INT64 = BaseType("Int64")
INT32 = BaseType("Int32")
FLOAT64 = BaseType("Float64")
STRING = BaseType("String")
BOOLEAN = BaseType("Boolean")
BYTES = BaseType("Bytes")


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
    param_types: Union[List[TargetType], int]  # List of types or -1 for variadic
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
BUILTIN_REGISTRY: Dict[str, BuiltinSignature] = {}

def register_builtin(name: str, param_types: Union[List[TargetType], int],
                     return_type: TargetType, is_primitive: bool = True) -> None:
    """Register a builtin in the registry."""
    BUILTIN_REGISTRY[name] = BuiltinSignature(name, param_types, return_type, is_primitive)

def get_builtin(name: str) -> Optional[BuiltinSignature]:
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
register_builtin("some", [T], OptionType(T))
register_builtin("is_some", [OptionType(T)], BOOLEAN)
register_builtin("is_none", [OptionType(T)], BOOLEAN)
register_builtin("unwrap_option", [OptionType(T)], T)
register_builtin("unwrap_option_or", [OptionType(T), T], T)

# === List operations ===
register_builtin("list_concat", [ListType(T), ListType(T)], ListType(T))
register_builtin("list_append", [ListType(T), T], ListType(T))
register_builtin("list_push!", [ListType(T), T], BaseType("None"))  # Mutating operation
register_builtin("length", [ListType(T)], INT64)
register_builtin("map", [FunctionType([T1], T2), ListType(T1)], ListType(T2))

# === Tuple operations ===
register_builtin("get_tuple_element", [TupleType([T1, T2]), INT64], T)
register_builtin("make_tuple", -1, T)  # Variadic: makes tuple from arguments

# === String operations ===
register_builtin("string_concat", [STRING, STRING], STRING)
register_builtin("string_to_upper", [STRING], STRING)
register_builtin("string_to_lower", [STRING], STRING)
register_builtin("string_in_list", [STRING, ListType(STRING)], BOOLEAN)
register_builtin("encode_string", [STRING], BYTES)

# === Type conversions ===
register_builtin("int64_to_int32", [INT64], INT32)

# === Date/time operations ===
register_builtin("make_date", [INT64, INT64, INT64], ANY)  # year, month, day -> DateValue

# === Parser primitives (lexer/parser operations) ===
register_builtin("match_lookahead_terminal", [STRING, INT64], BOOLEAN)
register_builtin("match_lookahead_literal", [STRING, INT64], BOOLEAN)
register_builtin("consume_literal", [STRING], BaseType("None"))
register_builtin("consume_terminal", [STRING], ANY)
register_builtin("current_token", [], ANY)

# === Error handling ===
register_builtin("error", -1, BaseType("Never"))  # Variadic: 1 or 2 args

# === Protobuf-specific ===
register_builtin("fragment_id_from_string", [STRING], MessageType("fragments", "FragmentId"))
register_builtin("relation_id_from_string", [STRING], MessageType("logic", "RelationId"))
register_builtin("relation_id_from_int", [INT64], MessageType("logic", "RelationId"))
register_builtin("construct_fragment",
                 [MessageType("fragments", "FragmentId"),
                  ListType(MessageType("logic", "Declaration"))],
                 MessageType("fragments", "Fragment"))
register_builtin("start_fragment", [MessageType("fragments", "FragmentId")], BaseType("None"))

# === Config construction (primitives that will be replaced by IR implementations) ===
register_builtin("construct_configure",
                 [ListType(TupleType([STRING, MessageType("logic", "Value")]))],
                 MessageType("transactions", "Configure"))
register_builtin("construct_csv_config",
                 [ListType(TupleType([STRING, MessageType("logic", "Value")]))],
                 MessageType("logic", "CSVConfig"))
register_builtin("construct_betree_info",
                 [ListType(ANY), ListType(ANY), ListType(TupleType([STRING, MessageType("logic", "Value")]))],
                 MessageType("logic", "BeTreeInfo"))
register_builtin("export_csv_config",
                 [STRING, ListType(ANY), ListType(TupleType([STRING, MessageType("logic", "Value")]))],
                 MessageType("transactions", "ExportCSVConfig"))

# === Config helper functions (specialized extractors with IR implementations) ===
register_builtin("_extract_value_int64",
                 [OptionType(MessageType("logic", "Value")), INT64],
                 INT64, is_primitive=False)
register_builtin("_extract_value_int32",
                 [OptionType(MessageType("logic", "Value")), INT32],
                 INT32, is_primitive=False)
register_builtin("_extract_value_float64",
                 [OptionType(MessageType("logic", "Value")), FLOAT64],
                 FLOAT64, is_primitive=False)
register_builtin("_extract_value_string",
                 [OptionType(MessageType("logic", "Value")), STRING],
                 STRING, is_primitive=False)
register_builtin("_extract_value_boolean",
                 [OptionType(MessageType("logic", "Value")), BOOLEAN],
                 BOOLEAN, is_primitive=False)
register_builtin("_extract_value_bytes",
                 [OptionType(MessageType("logic", "Value")), BYTES],
                 BYTES, is_primitive=False)
register_builtin("_extract_value_uint128",
                 [OptionType(MessageType("logic", "Value")), MessageType("logic", "UInt128Value")],
                 MessageType("logic", "UInt128Value"), is_primitive=False)
register_builtin("_extract_value_string_list",
                 [OptionType(MessageType("logic", "Value")), ListType(STRING)],
                 ListType(STRING), is_primitive=False)

# === General helpers ===
register_builtin("none", [], OptionType(T))  # Returns None/null
register_builtin("make_empty_bytes", [], BYTES)  # Returns empty bytes b''


# === Validation functions ===

def validate_builtin_call(name: str, num_args: int) -> Optional[str]:
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


__all__ = [
    'BuiltinSignature',
    'BUILTIN_REGISTRY',
    'register_builtin',
    'get_builtin',
    'is_builtin',
    'validate_builtin_call',
    # Type constants
    'ANY', 'INT64', 'INT32', 'FLOAT64', 'STRING', 'BOOLEAN', 'BYTES',
    'T', 'T1', 'T2', 'K', 'V',
]
