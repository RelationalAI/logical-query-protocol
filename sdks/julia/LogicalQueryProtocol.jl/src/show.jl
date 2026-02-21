# Use pprint for all LQP syntax types.
function Base.show(io::IO, x::LQPSyntax)
    pp = Pretty.PrettyPrinter(max_width=92)
    Pretty._pprint_dispatch(pp, x)
    print(io, rstrip(Pretty.get_output(pp)))
    return nothing
end

function Base.show(io::IO, x::LQPFragmentId)
    Pretty.pprint(io, x)
    return nothing
end
