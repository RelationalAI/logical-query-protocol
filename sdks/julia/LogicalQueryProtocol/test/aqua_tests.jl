@testitem "Aqua" begin
    using Aqua: Aqua
    using LogicalQueryProtocol: LogicalQueryProtocol
    Aqua.test_all(
        LogicalQueryProtocol;
        unbound_args=false, # see https://github.com/JuliaIO/ProtoBuf.jl/issues/272
        deps_compat=false,
        persistent_tasks=false,
        project_extras=false,
    )
end
