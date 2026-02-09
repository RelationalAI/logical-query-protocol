module Proto

using LogicalQueryProtocol: LogicalQueryProtocol

# Re-export all protobuf types from LogicalQueryProtocol's inner v1 module
const _v1 = LogicalQueryProtocol.relationalai.lqp.v1
for name in names(_v1; all=true)
    s = string(name)
    # Skip the module name itself, Julia internals, and private names
    name === :v1 && continue
    s in ("eval", "include", "#eval", "#include") && continue
    startswith(s, "_") && continue
    @eval using LogicalQueryProtocol.relationalai.lqp.v1: $name
    @eval export $name
end

end # module Proto
