"""
    lqp_semantics_version(txn::Transaction)::Int64

Returns the LQP semantics version specified by the client in the transaction's
configuration. This should be used to guard changes in engine behaviour that would break
existing clients.
"""
function lqp_semantics_version(txn::Transaction)
    isnothing(txn.configure) && return 0
    return txn.configure.semantics_version
end

"""
    is_read_only(txn::Transaction)::Bool
    is_read_only(epoch::Epoch)::Bool

Returns `true` if the transaction or epoch is read-only, meaning it does not contain write
actions. This is helpful to know, because read-only transactions can sometimes be executed
more efficiently.
"""
function is_read_only(txn::Transaction)
    return all(is_read_only(epoch) for epoch in txn.epochs)
end
function is_read_only(epoch::Epoch)
    # If there are any writes, the epoch is not read-only.
    return isempty(epoch.writes)
end

"""
    is_write_only(txn::Transaction)::Bool
    is_write_only(epoch::Epoch)::Bool

Returns `true` if the transaction or epoch is write-only, meaning it does not contain read
actions. This is very helpful to know, because write-only epochs can be merged together
before execution to avoid some overheads.
"""
function is_write_only(txn::Transaction)
    return all(is_write_only(epoch) for epoch in txn.epochs)
end
function is_write_only(epoch::Epoch)
    # If there are any reads, the epoch is not write-only.
    return isempty(epoch.reads)
end

"""
    read_transaction(path::String)::Transaction

Utility function that reads the transaction from the given `path`.
"""
function read_transaction(path::String)
    bytes = IOBuffer(read(path))
    return ProtoBuf.decode(ProtoBuf.ProtoDecoder(bytes), Transaction)
end

# When mapping LQP decimal types to and from the RAI engine, we need to map precision
# and scale correctly. Snowflake and LQP use:
#   - precision: total number of digits (0 <= precision <= 38)
#   - scale: number of digits after the decimal point (0 <= scale <= precision)
# Meanwhile, the engine uses:
#   - bits: number of bits in the physical representation (bits ∈ {8, 16, 32, 64, 128})
#   - precision: number of digits after the decimal point
#
# Thus, the mapping between LQP and the engine decimal types is:
#   - LQP precision <-> engine bits (with a log factor, roughly)
#   - LQP scale <-> engine precision
function decimal_precision_to_bits(precision::Integer)
    if precision <= 2
        return 8
    elseif precision <= 4
        return 16
    elseif precision <= 9
        return 32
    elseif precision <= 18
        return 64
    else
        @assert precision <= 38
        return 128
    end
end

function decimal_bits_to_precision(bits::Integer)
    if bits == 8
        return 2
    elseif bits == 16
        return 4
    elseif bits == 32
        return 9
    elseif bits == 64
        return 18
    elseif bits == 128
        return 38
    else
        @assert is_supported_decimal_bits(bits)
    end
end

function is_supported_decimal_bits(bits::Integer)
    return bits in [8, 16, 32, 64, 128]
end

persistent_id(fragment::Fragment) = persistent_id(fragment.id::FragmentId)
persistent_id(id::FragmentId) = LQPFragmentId(id.id)
persistent_id(id::RelationId) = UInt128(id.id_low) + (UInt128(id.id_high) << 64)
persistent_id(def::Def) = persistent_id(def.name::RelationId)
persistent_id(constraint::Constraint) = persistent_id(constraint.name::RelationId)

function global_ids(declaration::Declaration)
    dt = declaration.declaration_type
    isnothing(dt) && error("Declaration has no declaration_type set")
    if dt.name == :def
        def = unwrap(declaration)::Def
        return [persistent_id(def)]
    elseif dt.name == :algorithm
        algorithm = unwrap(declaration)::Algorithm
        return [persistent_id(out) for out in algorithm.var"#global"]
    elseif dt.name == :data
        data = dt[]::Data
        return global_ids(data)
    elseif dt.name == :constraint
        constraint = unwrap(declaration)::Constraint
        return [persistent_id(constraint)]
    else
        @assert _is_valid_declaration(declaration)
    end
end

function _is_valid_declaration(declaration::Declaration)
    dt = declaration.declaration_type
    return !isnothing(dt) && dt.name in [:def, :algorithm, :data, :constraint]
end

function global_ids(data::Data)
    dt = data.data_type
    isnothing(dt) && error("Data has no data_type set")
    if dt.name == :rel_edb
        rel_edb = dt[]::RelEDB
        @assert !isnothing(rel_edb.target_id)
        return [persistent_id(rel_edb.target_id)]
    elseif dt.name == :betree_relation
        betree_relation = dt[]::BeTreeRelation
        @assert !isnothing(betree_relation.name)
        return [persistent_id(betree_relation.name)]
    elseif dt.name == :csv_data
        csv_data = dt[]::CSVData
        ids = LQPRelationId[]
        for column in csv_data.columns
            if !isnothing(column.target_id)
                push!(ids, persistent_id(column.target_id))
            end
        end
        return ids
    else
        @assert _is_valid_data(data)
    end
end

function _is_valid_data(data::Data)
    dt = data.data_type
    return !isnothing(dt) && dt.name in [:rel_edb, :betree_relation, :csv_data]
end
