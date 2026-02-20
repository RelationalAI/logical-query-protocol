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
    CSVLocator,CSVConfig,CSVColumn,CSVData,
    RelEDB,Data,
}

using ProtoBuf: ProtoBuf

include("types.jl")
include("equality.jl")
include("protobuf-helpers.jl")
include("properties.jl")

# Include parser and pretty printer as submodules
include("parser.jl")
include("pretty.jl")

# Re-export from submodules
using .Parser: parse, ParseError, scan_string, scan_int, scan_float, scan_int128, scan_uint128, scan_decimal, Lexer
using .Pretty: ConstantFormatter, DefaultConstantFormatter, DEFAULT_CONSTANT_FORMATTER
using .Pretty: format_decimal, format_int128, format_uint128, format_int, format_float, format_string, format_bool
using .Pretty: format_float64, format_string_value
using .Pretty: pprint, pretty, pretty_debug, PrettyPrinter, _pprint_dispatch, get_output
using .Pretty: indent_level, indent!, try_flat

export Parser, Pretty, Proto
export parse, ParseError
export ConstantFormatter, DefaultConstantFormatter, DEFAULT_CONSTANT_FORMATTER
export format_decimal, format_int128, format_uint128, format_int, format_float, format_string, format_bool
export pprint, pretty, pretty_debug, PrettyPrinter
# Export for testing
export _pprint_dispatch, get_output
export scan_string, scan_int, scan_float, scan_int128, scan_uint128, scan_decimal, Lexer
export format_float64, format_string_value
export indent_level, indent!, try_flat

include("show.jl")

end
