# Equality and hashing for LQP types
# These are auto-generated protobuf types that need proper equality and hashing

using ProtoBuf: OneOf

# Helper function to hash OneOf fields
function _hash_oneof(x::Union{Nothing,OneOf}, h::UInt)
    if isnothing(x)
        return hash(nothing, h)
    else
        return hash((x.name, x[]), h)
    end
end

# Helper function to compare OneOf fields
function _isequal_oneof(a::Union{Nothing,OneOf}, b::Union{Nothing,OneOf})
    if isnothing(a) && isnothing(b)
        return true
    elseif isnothing(a) || isnothing(b)
        return false
    else
        return a.name == b.name && isequal(a[], b[])
    end
end

# Empty struct types - all instances are equal
for T in [
    DateTimeType,
    FloatType,
    UInt128Type,
    Int128Type,
    UnspecifiedType,
    DateType,
    MissingType,
    IntType,
    StringType,
    BooleanType,
]
    @eval begin
        Base.:(==)(::$T, ::$T) = true
        Base.hash(::$T, h::UInt) = hash($(QuoteNode(T)), h)
        Base.isequal(::$T, ::$T) = true
    end
end

# RelationId
Base.:(==)(a::RelationId, b::RelationId) = a.id_low == b.id_low && a.id_high == b.id_high
Base.hash(a::RelationId, h::UInt) = hash(a.id_high, hash(a.id_low, h))
Base.isequal(a::RelationId, b::RelationId) = a == b

# Var
Base.:(==)(a::Var, b::Var) = a.name == b.name
Base.hash(a::Var, h::UInt) = hash(a.name, h)
Base.isequal(a::Var, b::Var) = isequal(a.name, b.name)

# MissingValue
Base.:(==)(::MissingValue, ::MissingValue) = true
Base.hash(::MissingValue, h::UInt) = hash(:MissingValue, h)
Base.isequal(::MissingValue, ::MissingValue) = true

# DateTimeValue
Base.:(==)(a::DateTimeValue, b::DateTimeValue) = a.year == b.year && a.month == b.month && a.day == b.day && a.hour == b.hour && a.minute == b.minute && a.second == b.second && a.microsecond == b.microsecond
Base.hash(a::DateTimeValue, h::UInt) = hash(a.microsecond, hash(a.second, hash(a.minute, hash(a.hour, hash(a.day, hash(a.month, hash(a.year, h)))))))
Base.isequal(a::DateTimeValue, b::DateTimeValue) = isequal(a.year, b.year) && isequal(a.month, b.month) && isequal(a.day, b.day) && isequal(a.hour, b.hour) && isequal(a.minute, b.minute) && isequal(a.second, b.second) && isequal(a.microsecond, b.microsecond)

# DateValue
Base.:(==)(a::DateValue, b::DateValue) = a.year == b.year && a.month == b.month && a.day == b.day
Base.hash(a::DateValue, h::UInt) = hash(a.day, hash(a.month, hash(a.year, h)))
Base.isequal(a::DateValue, b::DateValue) = isequal(a.year, b.year) && isequal(a.month, b.month) && isequal(a.day, b.day)

# DecimalType
Base.:(==)(a::DecimalType, b::DecimalType) = a.precision == b.precision && a.scale == b.scale
Base.hash(a::DecimalType, h::UInt) = hash(a.scale, hash(a.precision, h))
Base.isequal(a::DecimalType, b::DecimalType) = isequal(a.precision, b.precision) && isequal(a.scale, b.scale)

# Int128Value
Base.:(==)(a::Int128Value, b::Int128Value) = a.low == b.low && a.high == b.high
Base.hash(a::Int128Value, h::UInt) = hash(a.high, hash(a.low, h))
Base.isequal(a::Int128Value, b::Int128Value) = isequal(a.low, b.low) && isequal(a.high, b.high)

# UInt128Value
Base.:(==)(a::UInt128Value, b::UInt128Value) = a.low == b.low && a.high == b.high
Base.hash(a::UInt128Value, h::UInt) = hash(a.high, hash(a.low, h))
Base.isequal(a::UInt128Value, b::UInt128Value) = isequal(a.low, b.low) && isequal(a.high, b.high)

# DecimalValue
Base.:(==)(a::DecimalValue, b::DecimalValue) = a.precision == b.precision && a.scale == b.scale && a.value == b.value
Base.hash(a::DecimalValue, h::UInt) = hash(a.value, hash(a.scale, hash(a.precision, h)))
Base.isequal(a::DecimalValue, b::DecimalValue) = isequal(a.precision, b.precision) && isequal(a.scale, b.scale) && isequal(a.value, b.value)

# Type (var"#Type")
function Base.:(==)(a::var"#Type", b::var"#Type")
    _isequal_oneof(a.var"#type", b.var"#type")
end
function Base.hash(a::var"#Type", h::UInt)
    _hash_oneof(a.var"#type", h)
end
function Base.isequal(a::var"#Type", b::var"#Type")
    _isequal_oneof(a.var"#type", b.var"#type")
end

# Value
function Base.:(==)(a::Value, b::Value)
    _isequal_oneof(a.value, b.value)
end
function Base.hash(a::Value, h::UInt)
    _hash_oneof(a.value, h)
end
function Base.isequal(a::Value, b::Value)
    _isequal_oneof(a.value, b.value)
end

# OrMonoid
Base.:(==)(::OrMonoid, ::OrMonoid) = true
Base.hash(::OrMonoid, h::UInt) = hash(:OrMonoid, h)
Base.isequal(::OrMonoid, ::OrMonoid) = true

# MinMonoid
Base.:(==)(a::MinMonoid, b::MinMonoid) = a.var"#type" == b.var"#type"
Base.hash(a::MinMonoid, h::UInt) = hash(a.var"#type", h)
Base.isequal(a::MinMonoid, b::MinMonoid) = isequal(a.var"#type", b.var"#type")

# SumMonoid
Base.:(==)(a::SumMonoid, b::SumMonoid) = a.var"#type" == b.var"#type"
Base.hash(a::SumMonoid, h::UInt) = hash(a.var"#type", h)
Base.isequal(a::SumMonoid, b::SumMonoid) = isequal(a.var"#type", b.var"#type")

# MaxMonoid
Base.:(==)(a::MaxMonoid, b::MaxMonoid) = a.var"#type" == b.var"#type"
Base.hash(a::MaxMonoid, h::UInt) = hash(a.var"#type", h)
Base.isequal(a::MaxMonoid, b::MaxMonoid) = isequal(a.var"#type", b.var"#type")

# Binding
Base.:(==)(a::Binding, b::Binding) = a.var == b.var && a.var"#type" == b.var"#type"
Base.hash(a::Binding, h::UInt) = hash(a.var"#type", hash(a.var, h))
Base.isequal(a::Binding, b::Binding) = isequal(a.var, b.var) && isequal(a.var"#type", b.var"#type")

# Attribute
Base.:(==)(a::Attribute, b::Attribute) = a.name == b.name && a.args == b.args
Base.hash(a::Attribute, h::UInt) = hash(a.args, hash(a.name, h))
Base.isequal(a::Attribute, b::Attribute) = isequal(a.name, b.name) && isequal(a.args, b.args)

# Term
function Base.:(==)(a::Term, b::Term)
    _isequal_oneof(a.term_type, b.term_type)
end
function Base.hash(a::Term, h::UInt)
    _hash_oneof(a.term_type, h)
end
function Base.isequal(a::Term, b::Term)
    _isequal_oneof(a.term_type, b.term_type)
end

# Monoid
function Base.:(==)(a::Monoid, b::Monoid)
    _isequal_oneof(a.value, b.value)
end
function Base.hash(a::Monoid, h::UInt)
    _hash_oneof(a.value, h)
end
function Base.isequal(a::Monoid, b::Monoid)
    _isequal_oneof(a.value, b.value)
end

# Cast
Base.:(==)(a::Cast, b::Cast) = a.input == b.input && a.result == b.result
Base.hash(a::Cast, h::UInt) = hash(a.result, hash(a.input, h))
Base.isequal(a::Cast, b::Cast) = isequal(a.input, b.input) && isequal(a.result, b.result)

# Pragma
Base.:(==)(a::Pragma, b::Pragma) = a.name == b.name && a.terms == b.terms
Base.hash(a::Pragma, h::UInt) = hash(a.terms, hash(a.name, h))
Base.isequal(a::Pragma, b::Pragma) = isequal(a.name, b.name) && isequal(a.terms, b.terms)

# Atom
Base.:(==)(a::Atom, b::Atom) = a.name == b.name && a.terms == b.terms
Base.hash(a::Atom, h::UInt) = hash(a.terms, hash(a.name, h))
Base.isequal(a::Atom, b::Atom) = isequal(a.name, b.name) && isequal(a.terms, b.terms)

# RelTerm
function Base.:(==)(a::RelTerm, b::RelTerm)
    _isequal_oneof(a.rel_term_type, b.rel_term_type)
end
function Base.hash(a::RelTerm, h::UInt)
    _hash_oneof(a.rel_term_type, h)
end
function Base.isequal(a::RelTerm, b::RelTerm)
    _isequal_oneof(a.rel_term_type, b.rel_term_type)
end

# Primitive
Base.:(==)(a::Primitive, b::Primitive) = a.name == b.name && a.terms == b.terms
Base.hash(a::Primitive, h::UInt) = hash(a.terms, hash(a.name, h))
Base.isequal(a::Primitive, b::Primitive) = isequal(a.name, b.name) && isequal(a.terms, b.terms)

# RelAtom
Base.:(==)(a::RelAtom, b::RelAtom) = a.name == b.name && a.terms == b.terms
Base.hash(a::RelAtom, h::UInt) = hash(a.terms, hash(a.name, h))
Base.isequal(a::RelAtom, b::RelAtom) = isequal(a.name, b.name) && isequal(a.terms, b.terms)

# Abstraction
Base.:(==)(a::Abstraction, b::Abstraction) = a.vars == b.vars && a.value == b.value
Base.hash(a::Abstraction, h::UInt) = hash(a.value, hash(a.vars, h))
Base.isequal(a::Abstraction, b::Abstraction) = isequal(a.vars, b.vars) && isequal(a.value, b.value)

# Assign
Base.:(==)(a::Assign, b::Assign) = a.name == b.name && a.body == b.body && a.attrs == b.attrs
Base.hash(a::Assign, h::UInt) = hash(a.attrs, hash(a.body, hash(a.name, h)))
Base.isequal(a::Assign, b::Assign) = isequal(a.name, b.name) && isequal(a.body, b.body) && isequal(a.attrs, b.attrs)

# Break
Base.:(==)(a::Break, b::Break) = a.name == b.name && a.body == b.body && a.attrs == b.attrs
Base.hash(a::Break, h::UInt) = hash(a.attrs, hash(a.body, hash(a.name, h)))
Base.isequal(a::Break, b::Break) = isequal(a.name, b.name) && isequal(a.body, b.body) && isequal(a.attrs, b.attrs)

# Conjunction
Base.:(==)(a::Conjunction, b::Conjunction) = a.args == b.args
Base.hash(a::Conjunction, h::UInt) = hash(a.args, h)
Base.isequal(a::Conjunction, b::Conjunction) = isequal(a.args, b.args)

# Disjunction
Base.:(==)(a::Disjunction, b::Disjunction) = a.args == b.args
Base.hash(a::Disjunction, h::UInt) = hash(a.args, h)
Base.isequal(a::Disjunction, b::Disjunction) = isequal(a.args, b.args)

# Exists
Base.:(==)(a::Exists, b::Exists) = a.body == b.body
Base.hash(a::Exists, h::UInt) = hash(a.body, h)
Base.isequal(a::Exists, b::Exists) = isequal(a.body, b.body)

# FFI
Base.:(==)(a::FFI, b::FFI) = a.name == b.name && a.args == b.args && a.terms == b.terms
Base.hash(a::FFI, h::UInt) = hash(a.terms, hash(a.args, hash(a.name, h)))
Base.isequal(a::FFI, b::FFI) = isequal(a.name, b.name) && isequal(a.args, b.args) && isequal(a.terms, b.terms)

# MonoidDef
Base.:(==)(a::MonoidDef, b::MonoidDef) = a.monoid == b.monoid && a.name == b.name && a.body == b.body && a.attrs == b.attrs && a.value_arity == b.value_arity
Base.hash(a::MonoidDef, h::UInt) = hash(a.value_arity, hash(a.attrs, hash(a.body, hash(a.name, hash(a.monoid, h)))))
Base.isequal(a::MonoidDef, b::MonoidDef) = isequal(a.monoid, b.monoid) && isequal(a.name, b.name) && isequal(a.body, b.body) && isequal(a.attrs, b.attrs) && isequal(a.value_arity, b.value_arity)

# MonusDef
Base.:(==)(a::MonusDef, b::MonusDef) = a.monoid == b.monoid && a.name == b.name && a.body == b.body && a.attrs == b.attrs && a.value_arity == b.value_arity
Base.hash(a::MonusDef, h::UInt) = hash(a.value_arity, hash(a.attrs, hash(a.body, hash(a.name, hash(a.monoid, h)))))
Base.isequal(a::MonusDef, b::MonusDef) = isequal(a.monoid, b.monoid) && isequal(a.name, b.name) && isequal(a.body, b.body) && isequal(a.attrs, b.attrs) && isequal(a.value_arity, b.value_arity)

# Not
Base.:(==)(a::Not, b::Not) = a.arg == b.arg
Base.hash(a::Not, h::UInt) = hash(a.arg, h)
Base.isequal(a::Not, b::Not) = isequal(a.arg, b.arg)

# Reduce
Base.:(==)(a::Reduce, b::Reduce) = a.op == b.op && a.body == b.body && a.terms == b.terms
Base.hash(a::Reduce, h::UInt) = hash(a.terms, hash(a.body, hash(a.op, h)))
Base.isequal(a::Reduce, b::Reduce) = isequal(a.op, b.op) && isequal(a.body, b.body) && isequal(a.terms, b.terms)

# Upsert
Base.:(==)(a::Upsert, b::Upsert) = a.name == b.name && a.body == b.body && a.attrs == b.attrs && a.value_arity == b.value_arity
Base.hash(a::Upsert, h::UInt) = hash(a.value_arity, hash(a.attrs, hash(a.body, hash(a.name, h))))
Base.isequal(a::Upsert, b::Upsert) = isequal(a.name, b.name) && isequal(a.body, b.body) && isequal(a.attrs, b.attrs) && isequal(a.value_arity, b.value_arity)

# Declaration
function Base.:(==)(a::Declaration, b::Declaration)
    _isequal_oneof(a.declaration_type, b.declaration_type)
end
function Base.hash(a::Declaration, h::UInt)
    _hash_oneof(a.declaration_type, h)
end
function Base.isequal(a::Declaration, b::Declaration)
    _isequal_oneof(a.declaration_type, b.declaration_type)
end

# Def
Base.:(==)(a::Def, b::Def) = a.name == b.name && a.body == b.body && a.attrs == b.attrs
Base.hash(a::Def, h::UInt) = hash(a.attrs, hash(a.body, hash(a.name, h)))
Base.isequal(a::Def, b::Def) = isequal(a.name, b.name) && isequal(a.body, b.body) && isequal(a.attrs, b.attrs)

# Algorithm
Base.:(==)(a::Algorithm, b::Algorithm) = a.var"#global" == b.var"#global" && a.body == b.body
Base.hash(a::Algorithm, h::UInt) = hash(a.body, hash(a.var"#global", h))
Base.isequal(a::Algorithm, b::Algorithm) = isequal(a.var"#global", b.var"#global") && isequal(a.body, b.body)

# Script
Base.:(==)(a::Script, b::Script) = a.constructs == b.constructs
Base.hash(a::Script, h::UInt) = hash(a.constructs, h)
Base.isequal(a::Script, b::Script) = isequal(a.constructs, b.constructs)

# Construct
function Base.:(==)(a::Construct, b::Construct)
    _isequal_oneof(a.construct_type, b.construct_type)
end
function Base.hash(a::Construct, h::UInt)
    _hash_oneof(a.construct_type, h)
end
function Base.isequal(a::Construct, b::Construct)
    _isequal_oneof(a.construct_type, b.construct_type)
end

# Loop
Base.:(==)(a::Loop, b::Loop) = a.init == b.init && a.body == b.body
Base.hash(a::Loop, h::UInt) = hash(a.body, hash(a.init, h))
Base.isequal(a::Loop, b::Loop) = isequal(a.init, b.init) && isequal(a.body, b.body)

# Formula
function Base.:(==)(a::Formula, b::Formula)
    _isequal_oneof(a.formula_type, b.formula_type)
end
function Base.hash(a::Formula, h::UInt)
    _hash_oneof(a.formula_type, h)
end
function Base.isequal(a::Formula, b::Formula)
    _isequal_oneof(a.formula_type, b.formula_type)
end

# Instruction
function Base.:(==)(a::Instruction, b::Instruction)
    _isequal_oneof(a.instr_type, b.instr_type)
end
function Base.hash(a::Instruction, h::UInt)
    _hash_oneof(a.instr_type, h)
end
function Base.isequal(a::Instruction, b::Instruction)
    _isequal_oneof(a.instr_type, b.instr_type)
end

# FragmentId
Base.:(==)(a::FragmentId, b::FragmentId) = a.id == b.id
Base.hash(a::FragmentId, h::UInt) = hash(a.id, h)
Base.isequal(a::FragmentId, b::FragmentId) = isequal(a.id, b.id)

# DebugInfo
Base.:(==)(a::DebugInfo, b::DebugInfo) = a.ids == b.ids && a.orig_names == b.orig_names
Base.hash(a::DebugInfo, h::UInt) = hash(a.orig_names, hash(a.ids, h))
Base.isequal(a::DebugInfo, b::DebugInfo) = isequal(a.ids, b.ids) && isequal(a.orig_names, b.orig_names)

# Fragment
Base.:(==)(a::Fragment, b::Fragment) = a.id == b.id && a.declarations == b.declarations && a.debug_info == b.debug_info
Base.hash(a::Fragment, h::UInt) = hash(a.debug_info, hash(a.declarations, hash(a.id, h)))
Base.isequal(a::Fragment, b::Fragment) = isequal(a.id, b.id) && isequal(a.declarations, b.declarations) && isequal(a.debug_info, b.debug_info)

# ExportCSVColumn
Base.:(==)(a::ExportCSVColumn, b::ExportCSVColumn) = a.column_name == b.column_name && a.column_data == b.column_data
Base.hash(a::ExportCSVColumn, h::UInt) = hash(a.column_data, hash(a.column_name, h))
Base.isequal(a::ExportCSVColumn, b::ExportCSVColumn) = isequal(a.column_name, b.column_name) && isequal(a.column_data, b.column_data)

# ExportCSVConfig
Base.:(==)(a::ExportCSVConfig, b::ExportCSVConfig) = a.path == b.path && a.data_columns == b.data_columns && a.partition_size == b.partition_size && a.compression == b.compression && a.syntax_header_row == b.syntax_header_row && a.syntax_missing_string == b.syntax_missing_string && a.syntax_delim == b.syntax_delim && a.syntax_quotechar == b.syntax_quotechar && a.syntax_escapechar == b.syntax_escapechar
Base.hash(a::ExportCSVConfig, h::UInt) = hash(a.syntax_escapechar, hash(a.syntax_quotechar, hash(a.syntax_delim, hash(a.syntax_missing_string, hash(a.syntax_header_row, hash(a.compression, hash(a.partition_size, hash(a.data_columns, hash(a.path, h)))))))))
Base.isequal(a::ExportCSVConfig, b::ExportCSVConfig) = isequal(a.path, b.path) && isequal(a.data_columns, b.data_columns) && isequal(a.partition_size, b.partition_size) && isequal(a.compression, b.compression) && isequal(a.syntax_header_row, b.syntax_header_row) && isequal(a.syntax_missing_string, b.syntax_missing_string) && isequal(a.syntax_delim, b.syntax_delim) && isequal(a.syntax_quotechar, b.syntax_quotechar) && isequal(a.syntax_escapechar, b.syntax_escapechar)

# Demand
Base.:(==)(a::Demand, b::Demand) = a.relation_id == b.relation_id
Base.hash(a::Demand, h::UInt) = hash(a.relation_id, h)
Base.isequal(a::Demand, b::Demand) = isequal(a.relation_id, b.relation_id)

# Undefine
Base.:(==)(a::Undefine, b::Undefine) = a.fragment_id == b.fragment_id
Base.hash(a::Undefine, h::UInt) = hash(a.fragment_id, h)
Base.isequal(a::Undefine, b::Undefine) = isequal(a.fragment_id, b.fragment_id)

# Define
Base.:(==)(a::Define, b::Define) = a.fragment == b.fragment
Base.hash(a::Define, h::UInt) = hash(a.fragment, h)
Base.isequal(a::Define, b::Define) = isequal(a.fragment, b.fragment)

# Snapshot
Base.:(==)(a::Snapshot, b::Snapshot) = a.destination_path == b.destination_path && a.source_relation == b.source_relation
Base.hash(a::Snapshot, h::UInt) = hash(a.source_relation, hash(a.destination_path, h))
Base.isequal(a::Snapshot, b::Snapshot) = isequal(a.destination_path, b.destination_path) && isequal(a.source_relation, b.source_relation)

# Context
Base.:(==)(a::Context, b::Context) = a.relations == b.relations
Base.hash(a::Context, h::UInt) = hash(a.relations, h)
Base.isequal(a::Context, b::Context) = isequal(a.relations, b.relations)

# Sync
Base.:(==)(a::Sync, b::Sync) = a.fragments == b.fragments
Base.hash(a::Sync, h::UInt) = hash(a.fragments, h)
Base.isequal(a::Sync, b::Sync) = isequal(a.fragments, b.fragments)

# Abort
Base.:(==)(a::Abort, b::Abort) = a.name == b.name && a.relation_id == b.relation_id
Base.hash(a::Abort, h::UInt) = hash(a.relation_id, hash(a.name, h))
Base.isequal(a::Abort, b::Abort) = isequal(a.name, b.name) && isequal(a.relation_id, b.relation_id)

# Output
Base.:(==)(a::Output, b::Output) = a.name == b.name && a.relation_id == b.relation_id
Base.hash(a::Output, h::UInt) = hash(a.relation_id, hash(a.name, h))
Base.isequal(a::Output, b::Output) = isequal(a.name, b.name) && isequal(a.relation_id, b.relation_id)

# Write
function Base.:(==)(a::Write, b::Write)
    _isequal_oneof(a.write_type, b.write_type)
end
function Base.hash(a::Write, h::UInt)
    _hash_oneof(a.write_type, h)
end
function Base.isequal(a::Write, b::Write)
    _isequal_oneof(a.write_type, b.write_type)
end

# Export
function Base.:(==)(a::Export, b::Export)
    _isequal_oneof(a.export_config, b.export_config)
end
function Base.hash(a::Export, h::UInt)
    _hash_oneof(a.export_config, h)
end
function Base.isequal(a::Export, b::Export)
    _isequal_oneof(a.export_config, b.export_config)
end

# IVMConfig
Base.:(==)(a::IVMConfig, b::IVMConfig) = a.level == b.level
Base.hash(a::IVMConfig, h::UInt) = hash(a.level, h)
Base.isequal(a::IVMConfig, b::IVMConfig) = isequal(a.level, b.level)

# Configure
Base.:(==)(a::Configure, b::Configure) = a.semantics_version == b.semantics_version && a.ivm_config == b.ivm_config
Base.hash(a::Configure, h::UInt) = hash(a.ivm_config, hash(a.semantics_version, h))
Base.isequal(a::Configure, b::Configure) = isequal(a.semantics_version, b.semantics_version) && isequal(a.ivm_config, b.ivm_config)

# Epoch
Base.:(==)(a::Epoch, b::Epoch) = a.writes == b.writes && a.reads == b.reads
Base.hash(a::Epoch, h::UInt) = hash(a.reads, hash(a.writes, h))
Base.isequal(a::Epoch, b::Epoch) = isequal(a.writes, b.writes) && isequal(a.reads, b.reads)

# Read
function Base.:(==)(a::Read, b::Read)
    _isequal_oneof(a.read_type, b.read_type)
end
function Base.hash(a::Read, h::UInt)
    _hash_oneof(a.read_type, h)
end
function Base.isequal(a::Read, b::Read)
    _isequal_oneof(a.read_type, b.read_type)
end

# Transaction
Base.:(==)(a::Transaction, b::Transaction) = a.epochs == b.epochs && a.configure == b.configure && a.sync == b.sync
Base.hash(a::Transaction, h::UInt) = hash(a.sync, hash(a.configure, hash(a.epochs, h)))
Base.isequal(a::Transaction, b::Transaction) = isequal(a.epochs, b.epochs) && isequal(a.configure, b.configure) && isequal(a.sync, b.sync)

# WhatIf
Base.:(==)(a::WhatIf, b::WhatIf) = a.branch == b.branch && a.epoch == b.epoch
Base.hash(a::WhatIf, h::UInt) = hash(a.epoch, hash(a.branch, h))
Base.isequal(a::WhatIf, b::WhatIf) = isequal(a.branch, b.branch) && isequal(a.epoch, b.epoch)

# Constraint
function Base.:(==)(a::Constraint, b::Constraint)
    _isequal_oneof(a.constraint_type, b.constraint_type)
end
function Base.hash(a::Constraint, h::UInt)
    _hash_oneof(a.constraint_type, h)
end
function Base.isequal(a::Constraint, b::Constraint)
    _isequal_oneof(a.constraint_type, b.constraint_type)
end

# FunctionalDependency
Base.:(==)(a::FunctionalDependency, b::FunctionalDependency) = a.guard == b.guard && a.keys == b.keys && a.values == b.values
Base.hash(a::FunctionalDependency, h::UInt) = hash(a.values, hash(a.keys, hash(a.guard, h)))
Base.isequal(a::FunctionalDependency, b::FunctionalDependency) = isequal(a.guard, b.guard) && isequal(a.keys, b.keys) && isequal(a.values, b.values)

# BeTreeConfig
Base.:(==)(a::BeTreeConfig, b::BeTreeConfig) = a.epsilon == b.epsilon && a.max_pivots == b.max_pivots && a.max_deltas == b.max_deltas && a.max_leaf == b.max_leaf
Base.hash(a::BeTreeConfig, h::UInt) = hash(a.max_leaf, hash(a.max_deltas, hash(a.max_pivots, hash(a.epsilon, h))))
Base.isequal(a::BeTreeConfig, b::BeTreeConfig) = isequal(a.epsilon, b.epsilon) && isequal(a.max_pivots, b.max_pivots) && isequal(a.max_deltas, b.max_deltas) && isequal(a.max_leaf, b.max_leaf)

# CSVLocator
Base.:(==)(a::CSVLocator, b::CSVLocator) = a.paths == b.paths && a.inline_data == b.inline_data
Base.hash(a::CSVLocator, h::UInt) = hash(a.inline_data, hash(a.paths, h))
Base.isequal(a::CSVLocator, b::CSVLocator) = isequal(a.paths, b.paths) && isequal(a.inline_data, b.inline_data)

# CSVConfig
Base.:(==)(a::CSVConfig, b::CSVConfig) = a.header_row == b.header_row && a.skip == b.skip && a.new_line == b.new_line && a.delimiter == b.delimiter && a.quotechar == b.quotechar && a.escapechar == b.escapechar && a.comment == b.comment && a.missing_strings == b.missing_strings && a.decimal_separator == b.decimal_separator && a.encoding == b.encoding && a.compression == b.compression
Base.hash(a::CSVConfig, h::UInt) = hash(a.compression, hash(a.encoding, hash(a.decimal_separator, hash(a.missing_strings, hash(a.comment, hash(a.escapechar, hash(a.quotechar, hash(a.delimiter, hash(a.new_line, hash(a.skip, hash(a.header_row, h)))))))))))
Base.isequal(a::CSVConfig, b::CSVConfig) = isequal(a.header_row, b.header_row) && isequal(a.skip, b.skip) && isequal(a.new_line, b.new_line) && isequal(a.delimiter, b.delimiter) && isequal(a.quotechar, b.quotechar) && isequal(a.escapechar, b.escapechar) && isequal(a.comment, b.comment) && isequal(a.missing_strings, b.missing_strings) && isequal(a.decimal_separator, b.decimal_separator) && isequal(a.encoding, b.encoding) && isequal(a.compression, b.compression)

# BeTreeLocator
function Base.:(==)(a::BeTreeLocator, b::BeTreeLocator)
    _isequal_oneof(a.location, b.location) && a.element_count == b.element_count && a.tree_height == b.tree_height
end
function Base.hash(a::BeTreeLocator, h::UInt)
    hash(a.tree_height, hash(a.element_count, _hash_oneof(a.location, h)))
end
function Base.isequal(a::BeTreeLocator, b::BeTreeLocator)
    _isequal_oneof(a.location, b.location) && isequal(a.element_count, b.element_count) && isequal(a.tree_height, b.tree_height)
end

# RelEDB
Base.:(==)(a::RelEDB, b::RelEDB) = a.target_id == b.target_id && a.path == b.path && a.types == b.types
Base.hash(a::RelEDB, h::UInt) = hash(a.types, hash(a.path, hash(a.target_id, h)))
Base.isequal(a::RelEDB, b::RelEDB) = isequal(a.target_id, b.target_id) && isequal(a.path, b.path) && isequal(a.types, b.types)

# BeTreeInfo
Base.:(==)(a::BeTreeInfo, b::BeTreeInfo) = a.key_types == b.key_types && a.value_types == b.value_types && a.storage_config == b.storage_config && a.relation_locator == b.relation_locator
Base.hash(a::BeTreeInfo, h::UInt) = hash(a.relation_locator, hash(a.storage_config, hash(a.value_types, hash(a.key_types, h))))
Base.isequal(a::BeTreeInfo, b::BeTreeInfo) = isequal(a.key_types, b.key_types) && isequal(a.value_types, b.value_types) && isequal(a.storage_config, b.storage_config) && isequal(a.relation_locator, b.relation_locator)

# CSVColumn
Base.:(==)(a::CSVColumn, b::CSVColumn) = a.column_path == b.column_path && a.target_id == b.target_id && a.types == b.types
Base.hash(a::CSVColumn, h::UInt) = hash(a.types, hash(a.target_id, hash(a.column_path, h)))
Base.isequal(a::CSVColumn, b::CSVColumn) = isequal(a.column_path, b.column_path) && isequal(a.target_id, b.target_id) && isequal(a.types, b.types)

# BeTreeRelation
Base.:(==)(a::BeTreeRelation, b::BeTreeRelation) = a.name == b.name && a.relation_info == b.relation_info
Base.hash(a::BeTreeRelation, h::UInt) = hash(a.relation_info, hash(a.name, h))
Base.isequal(a::BeTreeRelation, b::BeTreeRelation) = isequal(a.name, b.name) && isequal(a.relation_info, b.relation_info)

# CSVData
Base.:(==)(a::CSVData, b::CSVData) = a.locator == b.locator && a.config == b.config && a.columns == b.columns && a.asof == b.asof
Base.hash(a::CSVData, h::UInt) = hash(a.asof, hash(a.columns, hash(a.config, hash(a.locator, h))))
Base.isequal(a::CSVData, b::CSVData) = isequal(a.locator, b.locator) && isequal(a.config, b.config) && isequal(a.columns, b.columns) && isequal(a.asof, b.asof)

# Data
function Base.:(==)(a::Data, b::Data)
    _isequal_oneof(a.data_type, b.data_type)
end
function Base.hash(a::Data, h::UInt)
    _hash_oneof(a.data_type, h)
end
function Base.isequal(a::Data, b::Data)
    _isequal_oneof(a.data_type, b.data_type)
end
