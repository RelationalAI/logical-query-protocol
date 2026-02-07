module Proto

# Include the generated protobuf modules
include("relationalai/relationalai.jl")

# Import and re-export all types from the generated protobuf code
using .relationalai.lqp.v1
export DateTimeType, RelationId, Var, FloatType, UInt128Type, BeTreeConfig, DateTimeValue
export DateValue, OrMonoid, CSVLocator, Int128Type, DecimalType, UnspecifiedType, DateType
export MissingType, MissingValue, CSVConfig, IntType, StringType, Int128Value, UInt128Value
export BooleanType, DecimalValue, BeTreeLocator, var"#Type", Value, RelEDB, MinMonoid
export SumMonoid, MaxMonoid, BeTreeInfo, Binding, CSVColumn, Attribute, Term, Monoid
export BeTreeRelation, CSVData, Cast, Pragma, Atom, RelTerm, Data, Primitive, RelAtom
export Abstraction, Algorithm, Assign, Break, Conjunction, Constraint, Def, Disjunction
export Exists, FFI, FunctionalDependency, MonoidDef, MonusDef, Not, Reduce, Script, Upsert
export Construct, Loop, Declaration, Instruction, Formula

# Import transaction types
using .relationalai.lqp.v1: Transaction, Sync, Epoch, Write, Read, Output, Configure, IVMConfig
export Transaction, Sync, Epoch, Write, Read, Output, Configure, IVMConfig

# Import fragment types
using .relationalai.lqp.v1: Fragment, FragmentId, DebugInfo
export Fragment, FragmentId, DebugInfo

# Import CSV export types
using .relationalai.lqp.v1: ExportCSVConfig
export ExportCSVConfig

# Re-export all types from v1 to simplify usage
for name in names(relationalai.lqp.v1, all=false)
    if !startswith(string(name), "#") && name != :v1
        @eval using .relationalai.lqp.v1: $name
        @eval export $name
    end
end

end # module Proto
