from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Union, Tuple, Sequence, Optional, Dict
import datetime as dt

# Tree representation of LQP. Each non-terminal (those with more than one
# option) is an "abstract" class and each terminal is its own class. All of
# which are children of LqpNode. PrimitiveType and PrimitiveValue are
# exceptions. PrimitiveType is an enum and PrimitiveValue is just a value.

@dataclass(frozen=True)
class SourceInfo:
    file: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"

# --- Logic Types ---

@dataclass(frozen=True)
class LqpNode:
    meta: Optional[SourceInfo]

# Declaration := Def | Loop
@dataclass(frozen=True)
class Declaration(LqpNode):
    pass

# Def(name::RelationId, body::Abstraction, attrs::Attribute[])
@dataclass(frozen=True)
class Def(Declaration):
    name: RelationId
    body: Abstraction
    attrs: Sequence[Attribute]

# LoopIndex(name::string)
@dataclass(frozen=True)
class LoopIndex(LqpNode):
    name: str

# Loop(temporal_var::LoopIndex, inits::Def[], body::Declaration[])
@dataclass(frozen=True)
class Loop(Declaration):
    temporal_var: LoopIndex
    inits: Sequence[Def]
    body: Sequence[Declaration]

# Abstraction(vars::Binding[], value::Formula)
@dataclass(frozen=True)
class Abstraction(LqpNode):
    vars: Sequence[Tuple[Var, RelType]]
    value: Formula

# Formula := Exists | Reduce | Conjunction | Disjunction | Not | FFI | Atom | Pragma | Primitive | TrueVal | FalseVal | RelAtom | Cast
@dataclass(frozen=True)
class Formula(LqpNode):
    pass

# Exists(body::Abstraction)
@dataclass(frozen=True)
class Exists(Formula):
    body: Abstraction

# Reduce(op::Abstraction, body::Abstraction, terms::Term[])
@dataclass(frozen=True)
class Reduce(Formula):
    op: Abstraction
    body: Abstraction
    terms: Sequence[Term]

# Conjunction(args::Formula[])
@dataclass(frozen=True)
class Conjunction(Formula):
    args: Sequence[Formula]

# Disjunction(args::Formula[])
@dataclass(frozen=True)
class Disjunction(Formula):
    args: Sequence[Formula]

# Not(arg::Formula)
@dataclass(frozen=True)
class Not(Formula):
    arg: Formula

# FFI(name::string, args::Abstraction[], terms::Term[])
@dataclass(frozen=True)
class FFI(Formula):
    name: str
    args: Sequence[Abstraction]
    terms: Sequence[Term]

# Atom(name::RelationId, terms::Term[])
@dataclass(frozen=True)
class Atom(Formula):
    name: RelationId
    terms: Sequence[Term]

# Pragma(name::string, terms::Term[])
@dataclass(frozen=True)
class Pragma(Formula):
    name: str
    terms: Sequence[Term]

# Primitive(name::string, terms::RelTerm[])
@dataclass(frozen=True)
class Primitive(Formula):
    name: str
    terms: Sequence[RelTerm]

# RelAtom(name::string, terms::RelTerm[])
@dataclass(frozen=True)
class RelAtom(Formula):
    name: str
    terms: Sequence[RelTerm]

# Cast(type::RelType, input::Term, result::Term)
@dataclass(frozen=True)
class Cast(Formula):
    type: RelType
    input: Term
    result: Term

# Var(name::string)
@dataclass(frozen=True)
class Var(LqpNode):
    name: str

# UInt128(low::fixed64, high::fixed64)
@dataclass(frozen=True)
class UInt128(LqpNode):
    low: int
    high: int

# PrimitiveValue union type for Constant
PrimitiveValue = Union[str, int, float, UInt128]

# Constant(value::PrimitiveValue)
Constant = Union[PrimitiveValue]

# Term := Var | Constant
Term = Union[Var, Constant]

# SpecializedValue(value::PrimitiveValue)
@dataclass(frozen=True)
class Specialized(LqpNode):
    value: PrimitiveValue

RelTerm = Union[Term, Specialized]

# Attribute(name::string, args::Constant[])
@dataclass(frozen=True)
class Attribute(LqpNode):
    name: str
    args: Sequence[Constant]

# RelationId(id_low::fixed64, id_high::fixed64)
@dataclass(frozen=True)
class RelationId(LqpNode):
    id_low: int
    id_high: int

class PrimitiveType(Enum):
    UNSPECIFIED = 0
    STRING = 1
    INT = 2
    FLOAT = 3
    UINT128 = 4

class RelValueType(Enum):
    UNSPECIFIED = 0
    DECIMAL = 1
    DATE = 2
    DATETIME = 3
    NANOSECOND = 4
    MICROSECOND = 5
    MILLISECOND = 6
    SECOND = 7
    MINUTE = 8
    HOUR = 9
    DAY = 10
    WEEK = 11
    MONTH = 12
    YEAR = 13

RelType = Union[PrimitiveType, RelValueType]

# --- Fragment Types ---

# FragmentId(id::bytes)
@dataclass(frozen=True)
class FragmentId(LqpNode):
    id: bytes

# Fragment(id::FragmentId, declarations::Declaration[])
@dataclass(frozen=True)
class Fragment(LqpNode):
    id: FragmentId
    declarations: Sequence[Declaration]

# --- Transaction Types ---

# Define(fragment::Fragment)
@dataclass(frozen=True)
class Define(LqpNode):
    fragment: Fragment

# Undefine(fragment_id::FragmentId)
@dataclass(frozen=True)
class Undefine(LqpNode):
    fragment_id: FragmentId

# Context(relations::RelationId[])
@dataclass(frozen=True)
class Context(LqpNode):
    relations: Sequence[RelationId]

# Write := Define | Undefine | Context
@dataclass(frozen=True)
class Write(LqpNode):
    write_type: Union[Define, Undefine, Context]

# Demand(relation_id::RelationId)
@dataclass(frozen=True)
class Demand(LqpNode):
    relation_id: RelationId

# Output(name::string?, relation_id::RelationId)
@dataclass(frozen=True)
class Output(LqpNode):
    name: Union[str, None]
    relation_id: RelationId

# Abort(name::string?, relation_id::RelationId)
@dataclass(frozen=True)
class Abort(LqpNode):
    name: Union[str, None]
    relation_id: RelationId

# Read := Demand | Output | WhatIf | Abort
@dataclass(frozen=True)
class Read(LqpNode):
    read_type: Union[Demand, Output, WhatIf, Abort]

# Epoch(persistent_writes::Write[], local_writes::Write[], reads::Read[])
@dataclass(frozen=True)
class Epoch(LqpNode):
    persistent_writes: Sequence[Write] = field(default_factory=list)
    local_writes: Sequence[Write] = field(default_factory=list)
    reads: Sequence[Read] = field(default_factory=list)

# WhatIf(branch::string?, epoch::Epoch)
@dataclass(frozen=True)
class WhatIf(LqpNode):
    branch: Union[str, None]
    epoch: Epoch

# Transaction(epochs::Epoch[])
@dataclass(frozen=True)
class Transaction(LqpNode):
    epochs: Sequence[Epoch]
