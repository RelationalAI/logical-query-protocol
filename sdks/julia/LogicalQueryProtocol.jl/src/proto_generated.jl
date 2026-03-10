module Proto

const _v1 = parentmodule(@__MODULE__).relationalai.lqp.v1
for name in names(_v1; all=true)
    s = string(name)
    # Skip the module name itself, Julia internals, and private names
    name === :v1 && continue
    s in ("eval", "include", "#eval", "#include") && continue
    startswith(s, "_") && continue
    @eval using ..relationalai.lqp.v1: $name
    @eval export $name
end

end # module Proto
