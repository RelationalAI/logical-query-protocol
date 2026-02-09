using Test
using LQPParser
import LQPParser: parse, Proto
using ProtoBuf

"""
    proto_equal(a, b) -> Bool

Structural equality for protobuf types. Julia's default `==` for immutable
structs uses `===`, which fails for structs containing arrays (arrays compare
by identity with `===`). This function compares field-by-field recursively.
"""
function proto_equal(a, b)
    isnothing(a) && isnothing(b) && return true
    (isnothing(a) || isnothing(b)) && return false
    typeof(a) != typeof(b) && return false
    T = typeof(a)
    (isprimitivetype(T) || T == String || T == Symbol || T == Nothing) && return a == b
    T <: ProtoBuf.OneOf && return a.name == b.name && proto_equal(a.value, b.value)
    if T <: AbstractVector
        length(a) != length(b) && return false
        return all(proto_equal(a[i], b[i]) for i in eachindex(a))
    end
    return all(proto_equal(getfield(a, f), getfield(b, f)) for f in fieldnames(T))
end

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
    test_files_dir = joinpath(@__DIR__, "../../../python-tools/tests/test_files/lqp")
    bin_files_dir = joinpath(@__DIR__, "../../../python-tools/tests/test_files/bin")

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
                        # If binaries don't match, try parsing both and comparing
                        # (protobuf serialization can vary in field order)
                        decoder = ProtoBuf.ProtoDecoder(IOBuffer(expected_binary))
                        expected_parsed = ProtoBuf.decode(decoder, Proto.Transaction)
                        @test proto_equal(result, expected_parsed)
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
