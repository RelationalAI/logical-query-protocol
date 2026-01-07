from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Union, Tuple, Sequence, Optional, Dict
import datetime as dt
from decimal import Decimal

# Tree representation of LQP. Each non-terminal (those with more than one
# option) is an "abstract" class and each terminal is its own class. All of
# which are children of LqpNode. Value is an exception -- it is just a value.

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

# Declaration := Def | Algorithm
@dataclass(frozen=True)
class Declaration(LqpNode):
    pass

# Def(name::RelationId, body::Abstraction, attrs::Attribute[])
@dataclass(frozen=True)
class Def(Declaration):
    name: RelationId
    body: Abstraction
    attrs: Sequence[Attribute]

# Constraint := FunctionalDependency
@dataclass(frozen=True)
class Constraint(Declaration):
    pass

# FunctionalDependency(guard::Abstraction, x::Var[], y::Var[])
@dataclass(frozen=True)
class FunctionalDependency(Constraint):
    guard: Abstraction
    keys: Sequence[Var]
    values: Sequence[Var]

# Algorithm(globals::RelationId[], body::Script)
@dataclass(frozen=True)
class Algorithm(Declaration):
    global_: Sequence[RelationId]
    body: Script

# Script := Construct[]
@dataclass(frozen=True)
class Script(LqpNode):
    constructs: Sequence[Construct]

# Construct := Loop | Instruction
@dataclass(frozen=True)
class Construct(LqpNode):
    pass

# Loop(init::Instruction[], body::Algorithm)
@dataclass(frozen=True)
class Loop(Construct):
    init: Sequence[Instruction]
    body: Script

# Instruction := Assign | Break | Upsert | MonoidDef | MonusDef
@dataclass(frozen=True)
class Instruction(Construct):
    pass

# Assign(name::RelationId, body::Abstraction, attrs::Attribute[])
@dataclass(frozen=True)
class Assign(Instruction):
    name: RelationId
    body: Abstraction
    attrs: Sequence[Attribute]

# Upsert(arity::int, name::RelationId, body::Abstraction, attrs::Attribute[])
@dataclass(frozen=True)
class Upsert(Instruction):
    value_arity: int
    name: RelationId
    body: Abstraction
    attrs: Sequence[Attribute]

# Break(name::RelationId, body::Abstraction, attrs::Attribute[])
@dataclass(frozen=True)
class Break(Instruction):
    name: RelationId
    body: Abstraction
    attrs: Sequence[Attribute]

# MonoidDef(arity::int, monoid::Monoid, name::RelationId, body::Abstraction, attrs::Attribute[])
@dataclass(frozen=True)
class MonoidDef(Instruction):
    value_arity: int
    monoid: Monoid
    name: RelationId
    body: Abstraction
    attrs: Sequence[Attribute]

# MonusDef(arity::int, monoid::Monoid, name::RelationId, body::Abstraction, attrs::Attribute[])
@dataclass(frozen=True)
class MonusDef(Instruction):
    value_arity: int
    monoid: Monoid
    name: RelationId
    body: Abstraction
    attrs: Sequence[Attribute]

# Monoid := OrMonoid | MinMonoid | MaxMonoid | SumMonoid
@dataclass(frozen=True)
class Monoid(LqpNode):
    pass

# OrMonoid
@dataclass(frozen=True)
class OrMonoid(Monoid):
    pass

# MinMonoid
@dataclass(frozen=True)
class MinMonoid(Monoid):
    type: Type

# MaxMonoid
@dataclass(frozen=True)
class MaxMonoid(Monoid):
    type: Type

# SumMonoid
@dataclass(frozen=True)
class SumMonoid(Monoid):
    type: Type

# Abstraction(vars::Binding[], value::Formula)
@dataclass(frozen=True)
class Abstraction(LqpNode):
    vars: Sequence[Tuple[Var, Type]]
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

# Cast(input::Term, result::Term)
@dataclass(frozen=True)
class Cast(Formula):
    input: Term
    result: Term

# Var(name::string)
@dataclass(frozen=True)
class Var(LqpNode):
    name: str

# UInt128Value(low::fixed64, high::fixed64)
@dataclass(frozen=True)
class UInt128Value(LqpNode):
    value: int

# Int128Value(low::fixed64, high::fixed64)
@dataclass(frozen=True)
class Int128Value(LqpNode):
    value: int

@dataclass(frozen=True)
class MissingValue(LqpNode):
    pass

# DateValue(year: int, month: int, day: int)
@dataclass(frozen=True)
class DateValue(LqpNode):
    value: dt.date

# DatetimeValue(year: int, month: int, day: int, hour: int, minute: int, second: int, microsecond: int)
@dataclass(frozen=True)
class DateTimeValue(LqpNode):
    value: dt.datetime

# DecimalValue(precision: int, scale: int, value: Decimal)
@dataclass(frozen=True)
class DecimalValue(LqpNode):
    precision: int
    scale: int
    value: Decimal

# BooleanValue(value: bool)
# Note: We need a custom BooleanValue class to distinguish it from Python's `int` type.
# Python's built-in `bool` is a subclass of `int`.
@dataclass(frozen=True)
class BooleanValue(LqpNode):
    value: bool

@dataclass(frozen=True)
class Value(LqpNode):
    value: Union[
        str,
        int,
        float,
        UInt128Value,
        Int128Value,
        MissingValue,
        DateValue,
        DateTimeValue,
        DecimalValue,
        BooleanValue
    ]

# SpecializedValue(value::Value)
@dataclass(frozen=True)
class SpecializedValue(LqpNode):
    value: Value

# Term := Var | Value
Term = Union[Var, Value]

# RelTerm := Term | SpecializedValue
RelTerm = Union[Term, SpecializedValue]

# Attribute(name::string, args::Constant[])
@dataclass(frozen=True)
class Attribute(LqpNode):
    name: str
    args: Sequence[Value]

# RelationId(id::UInt128)
@dataclass(frozen=True)
class RelationId(LqpNode):
    id: int
    def __post_init__(self):
        if self.id < 0 or self.id > 0xffffffffffffffffffffffffffffffff:
            raise ValueError("RelationId constructed with out of range (UInt128) number: {}".format(self.id))

    def __str__(self) -> str:
        if self.meta:
            return f"RelationId(meta={self.meta}, id={self.id})"
        return f"RelationId(id={self.id})"

    def __eq__(self, other) -> bool:
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

class TypeName(Enum):
    UNSPECIFIED = 0
    STRING = 1
    INT = 2
    FLOAT = 3
    UINT128 = 4
    INT128 = 5
    DATE = 6
    DATETIME = 7
    MISSING = 8
    DECIMAL = 9
    BOOLEAN = 10

    def __str__(self) -> str:
        return self.name

@dataclass(frozen=True)
class Type(LqpNode):
    type_name: TypeName
    parameters: Sequence[Value]

# --- Data Types (Base Relations, BeTree Config) ---

# BeTreeConfig(epsilon::float, max_pivots::int, max_deltas::int, max_leaf::int)
@dataclass(frozen=True)
class BeTreeConfig(LqpNode):
    epsilon: float
    max_pivots: int
    max_deltas: int
    max_leaf: int

# BeTreeLocator(root_pageid::UInt128Value?, inline_data::bytes?, element_count::int, tree_height::int)
# Note: Exactly one of root_pageid or inline_data must be set (oneof in protobuf)
@dataclass(frozen=True)
class BeTreeLocator(LqpNode):
    root_pageid: Optional[UInt128Value]
    inline_data: Optional[bytes]
    element_count: int
    tree_height: int

# BeTreeInfo(key_types::Type[], value_types::Type[], storage_config::BeTreeConfig, relation_locator::BeTreeLocator)
@dataclass(frozen=True)
class BeTreeInfo(LqpNode):
    key_types: Sequence[Type]
    value_types: Sequence[Type]
    storage_config: BeTreeConfig
    relation_locator: BeTreeLocator

# Data := RelEDB | BeTreeRelation | CSVData | IcebergRelation
@dataclass(frozen=True)
class Data(Declaration):
    pass

# RelEDB(target_id::RelationId, path::string[], types::Type[])
@dataclass(frozen=True)
class RelEDB(Data):
    target_id: RelationId
    path: Sequence[str]
    types: Sequence[Type]

# BeTreeRelation(name::RelationId, relation_info::BeTreeInfo)
@dataclass(frozen=True)
class BeTreeRelation(Data):
    name: RelationId
    relation_info: BeTreeInfo

# CSVData(locator::CSVLocator, config::CSVConfig, columns::CSVColumn[], asof::string)
@dataclass(frozen=True)
class CSVData(Data):
    locator: 'CSVLocator'
    config: 'CSVConfig'
    columns: Sequence['CSVColumn']
    asof: str

# CSVLocator(paths::string[], inline_data::bytes?)
# Note: Exactly one of paths or inline_data should be set (mutually exclusive)
@dataclass(frozen=True)
class CSVLocator(LqpNode):
    paths: Sequence[str]
    inline_data: Optional[bytes]

# CSVConfig(header_row::int, skip::int, new_line::string, delimiter::string, quotechar::string,
#           escapechar::string, comment::string, missing_strings::string[], decimal_separator::string,
#           encoding::string, compression::string)
@dataclass(frozen=True)
class CSVConfig(LqpNode):
    header_row: int
    skip: int
    new_line: str
    delimiter: str
    quotechar: str
    escapechar: str
    comment: str
    missing_strings: Sequence[str]
    decimal_separator: str
    encoding: str
    compression: str

# CSVColumn(column_name::string, target_id::RelationId, types::Type[])
@dataclass(frozen=True)
class CSVColumn(LqpNode):
    column_name: str
    target_id: RelationId
    types: Sequence[Type]

# --- Fragment Types ---

# FragmentId(id::bytes)
@dataclass(frozen=True)
class FragmentId(LqpNode):
    id: bytes

    def __eq__(self, other) -> bool:
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

# Fragment(id::FragmentId, declarations::Declaration[], debug_info::DebugInfo)
@dataclass(frozen=True)
class Fragment(LqpNode):
    id: FragmentId
    declarations: Sequence[Declaration]
    debug_info: DebugInfo

@dataclass(frozen=True)
class DebugInfo(LqpNode):
    id_to_orig_name: Dict[RelationId, str]

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

# ExportCSVConfig
@dataclass(frozen=True)
class ExportCSVConfig(LqpNode):
    path: str
    data_columns: Sequence[ExportCSVColumn]
    partition_size: Optional[int] = None
    compression: Optional[str] = None

    syntax_header_row: Optional[int] = None
    syntax_missing_string: Optional[str] = None
    syntax_delim: Optional[str] = None
    syntax_quotechar: Optional[str] = None
    syntax_escapechar: Optional[str] = None

@dataclass(frozen=True)
class ExportCSVColumn(LqpNode):
    column_name: str
    column_data: RelationId

# Export(name::string, relation_id::RelationId)
@dataclass(frozen=True)
class Export(LqpNode):
    # TODO: Once we add a JSON export, this should be union[ExportCSVConfig, ExportJSONConfig]
    config: ExportCSVConfig

# Abort(name::string?, relation_id::RelationId)
@dataclass(frozen=True)
class Abort(LqpNode):
    name: Union[str, None]
    relation_id: RelationId

# Read := Demand | Output | Export | WhatIf | Abort
@dataclass(frozen=True)
class Read(LqpNode):
    read_type: Union[Demand, Output, Export, WhatIf, Abort]

# Epoch(writes::Write[], reads::Read[])
@dataclass(frozen=True)
class Epoch(LqpNode):
    writes: Sequence[Write] = field(default_factory=list)
    reads: Sequence[Read] = field(default_factory=list)

# WhatIf(branch::string?, epoch::Epoch)
@dataclass(frozen=True)
class WhatIf(LqpNode):
    branch: Union[str, None]
    epoch: Epoch

# Transaction(epochs::Epoch[], configure::Configure)
@dataclass(frozen=True)
class Transaction(LqpNode):
    epochs: Sequence[Epoch]
    configure: Configure
    sync: Optional[Sync]

# Configure(semantics_version::int, ivm_config::IVMConfig)
@dataclass(frozen=True)
class Configure(LqpNode):
    semantics_version: int
    ivm_config: IVMConfig

# Sync(fragments::FragmentId[])
@dataclass(frozen=True)
class Sync(LqpNode):
    fragments: Sequence[FragmentId]

# IVMConfig(level::MaintenanceLevel)
@dataclass(frozen=True)
class IVMConfig(LqpNode):
    level: MaintenanceLevel

class MaintenanceLevel(Enum):
    UNSPECIFIED = 0
    OFF = 1
    AUTO = 2
    ALL = 3

    def __str__(self) -> str:
        return self.name
