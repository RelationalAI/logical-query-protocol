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
