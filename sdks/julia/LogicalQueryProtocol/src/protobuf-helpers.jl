"""
    unwrap(obj)

Extract the actual value from a OneOf field in a protobuf message.
Returns `nothing` if the OneOf field is not set.
"""
function unwrap end

unwrap(t::Write) = isnothing(t.write_type) ? nothing : t.write_type[]
unwrap(d::Declaration) = isnothing(d.declaration_type) ? nothing : d.declaration_type[]
unwrap(c::Constraint) = isnothing(c.constraint_type) ? nothing : c.constraint_type[]
unwrap(f::Formula) = isnothing(f.formula_type) ? nothing : f.formula_type[]
unwrap(t::Term) = isnothing(t.term_type) ? nothing : t.term_type[]
unwrap(v::Value) = isnothing(v.value) ? nothing : v.value[]
unwrap(c::Construct) = isnothing(c.construct_type) ? nothing : c.construct_type[]
unwrap(i::Instruction) = isnothing(i.instr_type) ? nothing : i.instr_type[]
unwrap(t::RelTerm) = isnothing(t.rel_term_type) ? nothing : t.rel_term_type[]
unwrap(t::var"#Type") = isnothing(t.var"#type") ? nothing : t.var"#type"[]
unwrap(t::Read) = isnothing(t.read_type) ? nothing : t.read_type[]

"""
Wrapping functions for LQP protobuf types.

These functions wrap protobuf values into their corresponding OneOf container types.
They are the inverse operations of `unwrap`.
"""

# Instruction wrappers
wrap_in_instruction(x::Break) = Instruction(ProtoBuf.OneOf(:var"#break", x))
wrap_in_instruction(x::Upsert) = Instruction(ProtoBuf.OneOf(:upsert, x))
wrap_in_instruction(x::Assign) = Instruction(ProtoBuf.OneOf(:assign, x))
wrap_in_instruction(x::MonoidDef) = Instruction(ProtoBuf.OneOf(:monoid_def, x))
wrap_in_instruction(x::MonusDef) = Instruction(ProtoBuf.OneOf(:monus_def, x))

# Construct wrappers
wrap_in_construct(x::Loop) = Construct(ProtoBuf.OneOf(:loop, x))
wrap_in_construct(x::Instruction) = Construct(ProtoBuf.OneOf(:instruction, x))

# Declaration wrappers
wrap_in_declaration(x::Def) = Declaration(ProtoBuf.OneOf(:def, x))
wrap_in_declaration(x::Algorithm) = Declaration(ProtoBuf.OneOf(:algorithm, x))

# Monoid wrappers
wrap_in_monoid(x::OrMonoid) = Monoid(ProtoBuf.OneOf(:or_monoid, x))
wrap_in_monoid(x::SumMonoid) = Monoid(ProtoBuf.OneOf(:sum_monoid, x))
wrap_in_monoid(x::MinMonoid) = Monoid(ProtoBuf.OneOf(:min_monoid, x))
wrap_in_monoid(x::MaxMonoid) = Monoid(ProtoBuf.OneOf(:max_monoid, x))

# Term wrappers
wrap_in_term(x::Var) = Term(ProtoBuf.OneOf(:var, x))
wrap_in_term(x::Value) = Term(ProtoBuf.OneOf(:constant, x))

# RelTerm wrappers
wrap_in_relterm(x::Value) = RelTerm(ProtoBuf.OneOf(:specialized_value, x))
wrap_in_relterm(x::Term) = RelTerm(ProtoBuf.OneOf(:term, x))

# Formula wrappers
wrap_in_formula(x::Atom) = Formula(ProtoBuf.OneOf(:atom, x))
wrap_in_formula(x::Cast) = Formula(ProtoBuf.OneOf(:cast, x))
wrap_in_formula(x::RelAtom) = Formula(ProtoBuf.OneOf(:rel_atom, x))
wrap_in_formula(x::Primitive) = Formula(ProtoBuf.OneOf(:primitive, x))
wrap_in_formula(x::Pragma) = Formula(ProtoBuf.OneOf(:pragma, x))
wrap_in_formula(x::Reduce) = Formula(ProtoBuf.OneOf(:reduce, x))
wrap_in_formula(x::FFI) = Formula(ProtoBuf.OneOf(:ffi, x))
wrap_in_formula(x::Conjunction) = Formula(ProtoBuf.OneOf(:conjunction, x))
wrap_in_formula(x::Disjunction) = Formula(ProtoBuf.OneOf(:disjunction, x))
wrap_in_formula(x::Not) = Formula(ProtoBuf.OneOf(:not, x))
wrap_in_formula(x::Exists) = Formula(ProtoBuf.OneOf(:exists, x))

"""
    value_to_type(value::Value)::LogicalQueryProtocol.var"#Type"

Returns the LQP type corresponding to the given LQP value.
"""
function value_to_type(value::Value)
    value_field = value.value
    @assert !isnothing(value_field)
    value_type_tag = value_field.name
    if value_type_tag == :string_value
        return var"#Type"(OneOf(:string_type, StringType()))
    elseif value_type_tag == :missing_value
        return var"#Type"(OneOf(:missing_type, MissingType()))
    elseif value_type_tag == :int_value
        return var"#Type"(OneOf(:int_type, IntType()))
    elseif value_type_tag == :float_value
        return var"#Type"(OneOf(:float_type, FloatType()))
    elseif value_type_tag == :int128_value
        return var"#Type"(OneOf(:int128_type, Int128Type()))
    elseif value_type_tag == :uint128_value
        return var"#Type"(OneOf(:uint128_type, UInt128Type()))
    elseif value_type_tag == :date_value
        return var"#Type"(OneOf(:date_type, DateType()))
    elseif value_type_tag == :datetime_value
        return var"#Type"(OneOf(:datetime_type, DateTimeType()))
    elseif value_type_tag == :decimal_value
        precision = Int64(value_field.value.precision)
        scale = Int64(value_field.value.scale)
        return var"#Type"(OneOf(:decimal_type, DecimalType(precision, scale)))
    elseif value_type_tag == :boolean_value
        return var"#Type"(OneOf(:boolean_type, BooleanType()))
    else
        @assert false
    end
end
