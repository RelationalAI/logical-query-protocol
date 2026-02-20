@testitem "JET error analysis LogicalQueryProtocol package" begin
    using JET: JET
    using LogicalQueryProtocol: LogicalQueryProtocol

    result = JET.report_package(
        LogicalQueryProtocol;
        toplevel_logger=nothing,
        mode=:typo,
        target_defined_modules=false,
    )
    reports = JET.get_reports(result)

    # Filter known false positives from protobuf OneOf dynamic dispatch.
    # `_get_oneof_field` returns an untyped value extracted from a OneOf wrapper.
    # JET sees that the returned value could be any variant in the union and
    # flags field accesses (`.args`, `.scale`) that only exist on some variants.
    # At runtime, the preceding `_has_proto_field` guard ensures correctness.
    function is_oneof_field_false_positive(report)
        msg = sprint(show, report)
        return occursin("has no field args", msg) || occursin("has no field scale", msg)
    end

    reports = filter(!is_oneof_field_false_positive, reports)

    if !isempty(reports)
        for report in reports
            println(report)
        end
    end
    @test isempty(reports)
end
