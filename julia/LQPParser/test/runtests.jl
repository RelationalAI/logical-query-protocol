using Test
using LQPParser
import LQPParser: parse, Proto
using ProtoBuf

@testset "LQPParser.jl" begin
    @testset "Basic parsing" begin
        # Test simple transaction parsing
        input = """
        (transaction
          (epoch
            (writes)
            (reads)))
        """

        result = parse(input)
        @test result !== nothing
        @test typeof(result) == Proto.Transaction
        @test length(result.epochs) == 1
    end

    # Test all LQP files against their binary snapshots
    test_files_dir = joinpath(@__DIR__, "../../../tests/lqp")
    bin_files_dir = joinpath(@__DIR__, "../../../tests/bin")

    if isdir(test_files_dir)
        lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))

        for lqp_file in lqp_files
            @testset "Parse $(lqp_file)" begin
                lqp_path = joinpath(test_files_dir, lqp_file)
                bin_path = joinpath(bin_files_dir, replace(lqp_file, ".lqp" => ".bin"))

                # Parse the LQP file
                content = read(lqp_path, String)
                result = parse(content)
                @test result !== nothing
                @test typeof(result) == Proto.Transaction

                # Serialize to binary
                io = IOBuffer()
                encoder = ProtoBuf.ProtoEncoder(io)
                ProtoBuf.encode(encoder, result)
                generated_binary = take!(io)

                # Compare with expected binary
                if isfile(bin_path)
                    expected_binary = read(bin_path)
                    if generated_binary != expected_binary
                        decoder = ProtoBuf.ProtoDecoder(IOBuffer(expected_binary))
                        expected_parsed = ProtoBuf.decode(decoder, Proto.Transaction)
                        @test result == expected_parsed
                    else
                        @test true  # Binaries match exactly
                    end
                else
                    @warn "No binary snapshot found for $(lqp_file), skipping binary comparison"
                end
            end
        end
    else
        @warn "Test files directory not found: $(test_files_dir)"
    end
end
