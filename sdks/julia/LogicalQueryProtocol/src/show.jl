# Use pprint for all LQP syntax types.
function Base.show(io::IO, x::LQPSyntax)
    pp = PrettyPrinter(max_width=92)
    _pprint_dispatch(pp, x)
    print(io, rstrip(get_output(pp)))
    return nothing
end

function Base.show(io::IO, x::LQPFragmentId)
    pprint(io, x)
    return nothing
end

# Types without _pprint_dispatch: show using their format helpers or field structure.

function Base.show(io::IO, x::Proto.DecimalValue)
    pp = PrettyPrinter(max_width=92)
    print(io, format_decimal(pp, x))
    return nothing
end

function Base.show(io::IO, x::Proto.UInt128Value)
    pp = PrettyPrinter(max_width=92)
    print(io, format_uint128(pp, x))
    return nothing
end

function Base.show(io::IO, x::Proto.Int128Value)
    pp = PrettyPrinter(max_width=92)
    print(io, format_int128(pp, x))
    return nothing
end

function Base.show(io::IO, ::Proto.MissingValue)
    print(io, "missing")
    return nothing
end

function Base.show(io::IO, x::Proto.DebugInfo)
    for (rid, name) in zip(x.ids, x.orig_names)
        value = UInt128(rid.id_high) << 64 | UInt128(rid.id_low)
        println(io, "0x", string(value; base=16), " -> ", name)
    end
    return nothing
end

# The generated pretty printer has no standalone dispatch for FunctionalDependency because
# it's always printed inline as part of Constraint, which owns the relation_id (name) that
# the S-expression format requires. The textual form `(functional_dependency :name ...)` mixes
# Constraint.name with FunctionalDependency's fields, so there's no standalone representation.
function Base.show(io::IO, x::Proto.FunctionalDependency)
    pp = PrettyPrinter(max_width=92)
    if !isnothing(x.guard)
        _pprint_dispatch(pp, x.guard)
    end
    write(pp, " ")
    pretty_functional_dependency_keys(pp, x.keys)
    write(pp, " ")
    pretty_functional_dependency_values(pp, x.values)
    print(io, rstrip(get_output(pp)))
    return nothing
end
