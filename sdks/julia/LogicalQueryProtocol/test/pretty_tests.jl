@testitem "Pretty printer - snapshot" begin
    using LogicalQueryProtocol: parse, pretty, Proto

    test_files_dir = joinpath(@__DIR__, "../../../../tests/lqp")
    snapshot_dir = joinpath(@__DIR__, "lqp_pretty_output")
    @test isdir(test_files_dir)

    update_snapshots = get(ENV, "UPDATE_SNAPSHOTS", "false") == "true"
    update_snapshots && mkpath(snapshot_dir)

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))
    @test !isempty(lqp_files)

    for lqp_file in lqp_files
        lqp_path = joinpath(test_files_dir, lqp_file)
        content = read(lqp_path, String)

        parsed = parse(content)
        @test parsed isa Proto.Transaction

        printed = pretty(parsed)
        @test !isempty(printed)

        snapshot_path = joinpath(snapshot_dir, lqp_file)
        if update_snapshots
            write(snapshot_path, printed)
        else
            @test isfile(snapshot_path)
            expected = read(snapshot_path, String)
            @test printed == expected
        end
    end
end

@testitem "Pretty printer - round trip" begin
    using LogicalQueryProtocol: parse, pretty, Proto

    test_files_dir = joinpath(@__DIR__, "../../../../tests/lqp")
    @test isdir(test_files_dir)

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))
    @test !isempty(lqp_files)

    for lqp_file in lqp_files
        lqp_path = joinpath(test_files_dir, lqp_file)
        content = read(lqp_path, String)

        parsed = parse(content)
        @test parsed isa Proto.Transaction

        printed = pretty(parsed)
        @test !isempty(printed)

        reparsed = parse(printed)
        @test reparsed isa Proto.Transaction
        @test reparsed == parsed
    end
end
