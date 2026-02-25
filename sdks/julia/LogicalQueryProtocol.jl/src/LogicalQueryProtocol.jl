module LogicalQueryProtocol

include("gen/relationalai/relationalai.jl")
using .relationalai.lqp.v1
const Proto = relationalai.lqp.v1

# Convenience identifiers for LQP Syntax.
const LQPFormula = Union{Atom,Cast,RelAtom,Primitive,Reduce,FFI,
    Conjunction,Disjunction,Not,Exists,Pragma}

const LQPDeclaration = Union{Constraint,Def,Algorithm}

const LQPMonoid = Union{MinMonoid,MaxMonoid,SumMonoid,OrMonoid}

const LQPInstruction = Union{Assign,Break,Upsert,MonoidDef,MonusDef}

const LQPSyntax = Union{
    DateTimeType,RelationId,Var,FloatType,UInt128Type,OrMonoid,Int128Type,
    DecimalType,UnspecifiedType,DateType,UInt128Value,MissingType,MissingValue,
    IntType,BooleanType,Int128Value,StringType,var"#Type",Value,MinMonoid,SumMonoid,
    MaxMonoid,Binding,Attribute,Term,Monoid,Cast,Pragma,Atom,RelTerm,Primitive,
    RelAtom,Abstraction,Algorithm,Assign,Break,Conjunction,Def,Disjunction,
    Exists,FFI,MonoidDef,MonusDef,Not,Reduce,Script,Upsert,Construct,Declaration,
    Loop,Formula,Instruction,FragmentId,DebugInfo,Fragment,ExportCSVColumn,
    ExportCSVConfig,Demand,Undefine,Configure,Snapshot,Define,Context,Sync,Abort,Output,Write,
    Export,Epoch,Read,Transaction,WhatIf,Constraint,FunctionalDependency,
    DateTimeValue,DateValue,DecimalValue,
    BeTreeInfo,BeTreeRelation,
    CSVLocator,CSVConfig,GNFColumn,CSVData,
    EDB,Data,
}

using ProtoBuf: ProtoBuf

include("types.jl")
include("equality.jl")
include("protobuf-helpers.jl")
include("properties.jl")

# Include parser and pretty printer as submodules
include("parser.jl")
include("pretty.jl")

# Export submodules for access as LogicalQueryProtocol.Parser, LogicalQueryProtocol.Pretty
export Parser, Pretty, Proto


include("show.jl")

end
