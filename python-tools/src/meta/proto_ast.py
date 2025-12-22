"""Protobuf AST data structures.

This module defines data structures for representing parsed protobuf message
definitions, including fields, oneofs, and enums.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class ProtoField:
    """Field in a protobuf message."""
    name: str
    type: str
    number: int
    is_repeated: bool = False
    is_optional: bool = False


@dataclass
class ProtoOneof:
    """Oneof group in a protobuf message."""
    name: str
    fields: List[ProtoField] = field(default_factory=list)


@dataclass
class ProtoEnum:
    """Enum definition in a protobuf message."""
    name: str
    values: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class ProtoReserved:
    """Reserved field numbers or names in a protobuf message."""
    numbers: List[int] = field(default_factory=list)
    ranges: List[Tuple[int, int]] = field(default_factory=list)
    names: List[str] = field(default_factory=list)


@dataclass
class ProtoMessage:
    """Protobuf message definition."""
    name: str
    module: str = ""
    fields: List[ProtoField] = field(default_factory=list)
    oneofs: List[ProtoOneof] = field(default_factory=list)
    enums: List[ProtoEnum] = field(default_factory=list)
    reserved: List[ProtoReserved] = field(default_factory=list)
