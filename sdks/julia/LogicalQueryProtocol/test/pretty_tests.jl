@testitem "Pretty printer - snapshot" begin
    using LogicalQueryProtocol: parse, pretty, Proto

    test_files_dir = joinpath(@__DIR__, "lqp")
    snapshot_dir = joinpath(@__DIR__, "pretty")
    @test isdir(test_files_dir)
    @test isdir(snapshot_dir)

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
        @test isfile(snapshot_path)
        expected = read(snapshot_path, String)
        @test printed == expected
    end
end

@testitem "Pretty printer - round trip" begin
    using LogicalQueryProtocol: parse, pretty, Proto

    test_files_dir = joinpath(@__DIR__, "lqp")
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

        reprinted = pretty(reparsed)
        @test printed == reprinted
    end
end

@testitem "Pretty printer - from binary snapshot" begin
    using LogicalQueryProtocol: pretty, Proto
    using ProtoBuf: ProtoBuf

    bin_files_dir = joinpath(@__DIR__, "bin")
    snapshot_dir = joinpath(@__DIR__, "pretty")
    @test isdir(bin_files_dir)
    @test isdir(snapshot_dir)

    bin_files = sort(filter(f -> endswith(f, ".bin"), readdir(bin_files_dir)))
    @test !isempty(bin_files)

    for bin_file in bin_files
        bin_path = joinpath(bin_files_dir, bin_file)
        data = read(bin_path)

        txn = ProtoBuf.decode(ProtoBuf.ProtoDecoder(IOBuffer(data)), Proto.Transaction)

        printed = pretty(txn)
        @test !isempty(printed)

        snapshot_file = replace(bin_file, ".bin" => ".lqp")
        snapshot_path = joinpath(snapshot_dir, snapshot_file)
        @test isfile(snapshot_path)
        expected = read(snapshot_path, String)
        @test printed == expected
    end
end

@testitem "Pretty printer - binary round trip" begin
    using LogicalQueryProtocol: parse, pretty, Proto
    using ProtoBuf: ProtoBuf

    bin_files_dir = joinpath(@__DIR__, "bin")
    @test isdir(bin_files_dir)

    bin_files = sort(filter(f -> endswith(f, ".bin"), readdir(bin_files_dir)))
    @test !isempty(bin_files)

    for bin_file in bin_files
        bin_path = joinpath(bin_files_dir, bin_file)
        data = read(bin_path)

        txn = ProtoBuf.decode(ProtoBuf.ProtoDecoder(IOBuffer(data)), Proto.Transaction)

        printed = pretty(txn)
        @test !isempty(printed)

        reparsed = parse(printed)
        @test reparsed isa Proto.Transaction
        @test reparsed == txn

        reprinted = pretty(reparsed)
        @test printed == reprinted
    end
end
