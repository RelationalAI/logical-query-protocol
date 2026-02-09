"""Protobuf AST data structures.

This module defines data structures for representing parsed protobuf message
definitions, including fields, oneofs, and enums.

The AST represents the structure of protobuf definitions parsed from .proto files.
These structures are consumed by the grammar generator to produce context-free
grammars with semantic actions.

Example:
    Given a protobuf definition in example.proto:

        message Person {
            string name = 1;
            int32 age = 2;
            repeated string emails = 3;
        }

    The parser produces:

        ProtoMessage(
            name="Person",
            module="example",
            fields=[
                ProtoField(name="name", type="string", number=1),
                ProtoField(name="age", type="int32", number=2),
                ProtoField(name="emails", type="string", number=3, is_repeated=True)
            ]
        )
"""

from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class ProtoField:
    """Field in a protobuf message.

    Attributes:
        name: Field name (e.g., "person_id", "count")
        type: Field type (e.g., "string", "int32", "Person")
        number: Field number in the protobuf definition
        is_repeated: True if the field is repeated (list/array)
        is_optional: True if the field is explicitly optional

    Example:
        repeated string emails = 3;  ->
        ProtoField(name="emails", type="string", number=3, is_repeated=True)

        optional int32 age = 2;  ->
        ProtoField(name="age", type="int32", number=2, is_optional=True)
    """
    name: str
    type: str
    number: int
    is_repeated: bool = False
    is_optional: bool = False


@dataclass
class ProtoOneof:
    """Oneof group in a protobuf message.

    A oneof represents a discriminated union where exactly one of the
    fields can be set at a time.

    Attributes:
        name: Name of the oneof group
        fields: List of fields in the oneof (exactly one will be set)

    Example:
        oneof payload {
            string text = 1;
            bytes binary = 2;
        }  ->
        ProtoOneof(name="payload", fields=[
            ProtoField(name="text", type="string", number=1),
            ProtoField(name="binary", type="bytes", number=2)
        ])
    """
    name: str
    fields: List[ProtoField] = field(default_factory=list)


@dataclass
class ProtoEnum:
    """Enum definition in a protobuf message.

    Attributes:
        name: Enum type name
        module: Module name (protobuf file stem)
        values: List of (enum_value_name, enum_value_number) tuples

    Example:
        enum Status {
            UNKNOWN = 0;
            ACTIVE = 1;
            INACTIVE = 2;
        }  ->
        ProtoEnum(name="Status", module="mymodule", values=[
            ("UNKNOWN", 0),
            ("ACTIVE", 1),
            ("INACTIVE", 2)
        ])
    """
    name: str
    module: str = ""
    values: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class ProtoReserved:
    """Reserved field numbers or names in a protobuf message.

    Reserved entries prevent field numbers or names from being reused,
    maintaining backward compatibility.

    Attributes:
        numbers: List of reserved field numbers
        ranges: List of reserved field number ranges (start, end) inclusive
        names: List of reserved field names

    Example:
        reserved 2, 15, 9 to 11;  ->
        ProtoReserved(numbers=[2, 15], ranges=[(9, 11)])

        reserved "foo", "bar";  ->
        ProtoReserved(names=["foo", "bar"])
    """
    numbers: List[int] = field(default_factory=list)
    ranges: List[Tuple[int, int]] = field(default_factory=list)
    names: List[str] = field(default_factory=list)


@dataclass
class ProtoMessage:
    """Protobuf message definition.

    Represents a complete protobuf message with all its fields, oneofs,
    nested enums, and reserved entries.

    Attributes:
        name: Message type name
        module: Module name (protobuf file stem)
        fields: Regular fields (not in oneofs)
        oneofs: Oneof groups
        enums: Nested enum definitions
        reserved: Reserved field numbers and names

    Example:
        message Account {
            enum Type {
                CHECKING = 0;
                SAVINGS = 1;
            }
            string id = 1;
            Type type = 2;
            oneof balance {
                int64 cents = 3;
                double dollars = 4;
            }
            reserved 5, 6;
        }  ->
        ProtoMessage(
            name="Account",
            module="banking",
            fields=[
                ProtoField(name="id", type="string", number=1),
                ProtoField(name="type", type="Type", number=2)
            ],
            oneofs=[ProtoOneof(name="balance", fields=[...])],
            enums=[ProtoEnum(name="Type", values=[...])],
            reserved=[ProtoReserved(numbers=[5, 6])]
        )
    """
    name: str
    module: str = ""
    fields: List[ProtoField] = field(default_factory=list)
    oneofs: List[ProtoOneof] = field(default_factory=list)
    enums: List[ProtoEnum] = field(default_factory=list)
    reserved: List[ProtoReserved] = field(default_factory=list)
