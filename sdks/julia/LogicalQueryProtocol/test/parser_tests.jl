@testitem "Parser - basic" begin
    using LogicalQueryProtocol: parse, Proto

    input = """
    (transaction
      (epoch
        (writes)
        (reads)))
    """
    result = parse(input)
    @test !isnothing(result)
    @test result isa Proto.Transaction
    @test length(result.epochs) == 1
end

@testitem "Parser - round trip" begin
    using LogicalQueryProtocol: parse, Proto
    using ProtoBuf: ProtoBuf

    test_files_dir = joinpath(@__DIR__, "../../../../tests/lqp")
    bin_files_dir = joinpath(@__DIR__, "../../../../tests/bin")
    @test isdir(test_files_dir)

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))
    @test !isempty(lqp_files)

    for lqp_file in lqp_files
        lqp_path = joinpath(test_files_dir, lqp_file)
        bin_path = joinpath(bin_files_dir, replace(lqp_file, ".lqp" => ".bin"))

        content = read(lqp_path, String)
        result = parse(content)
        @test !isnothing(result)
        @test result isa Proto.Transaction

        io = IOBuffer()
        ProtoBuf.encode(ProtoBuf.ProtoEncoder(io), result)
        generated_binary = take!(io)

        if isfile(bin_path)
            expected_binary = read(bin_path)
            if generated_binary != expected_binary
                expected_parsed = ProtoBuf.decode(
                    ProtoBuf.ProtoDecoder(IOBuffer(expected_binary)),
                    Proto.Transaction,
                )
                @test result == expected_parsed
            end
        end
    end
end
