struct LQPFragmentId
    id::Vector{UInt8}
end

Base.:(==)(a::LQPFragmentId, b::LQPFragmentId) = a.id == b.id
Base.hash(a::LQPFragmentId, h::UInt) = hash(a.id, h)

Base.isless(a::LQPFragmentId, b::LQPFragmentId) = a.id < b.id

const LQPRelationId = UInt128
