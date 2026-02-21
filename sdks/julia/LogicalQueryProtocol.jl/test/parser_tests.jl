@testitem "Parser - basic" setup=[ParserSetup] begin

    input = """
    (transaction
      (epoch
        (writes)
        (reads)))
    """
    result = Parser.parse(input)
    @test !isnothing(result)
    @test result isa Proto.Transaction
    @test length(result.epochs) == 1
end

@testitem "Parser - error on empty input" setup=[ParserSetup] begin
    @test_throws ParseError Parser.parse("")
    @test_throws ParseError Parser.parse("   ")
    @test_throws ParseError Parser.parse("\n\n")
end

@testitem "Parser - error on unclosed paren" setup=[ParserSetup] begin
    @test_throws ParseError Parser.parse("(transaction")
    @test_throws ParseError Parser.parse("(transaction (epoch (writes) (reads))")
end

@testitem "Parser - error on missing transaction wrapper" setup=[ParserSetup] begin
    @test_throws ParseError Parser.parse("(epoch (writes) (reads))")
end

@testitem "Parser - error on bad token" setup=[ParserSetup] begin
    @test_throws ParseError Parser.parse("(transaction @@@)")
end

@testitem "Parser - error on trailing garbage" setup=[ParserSetup] begin
    @test_throws ParseError Parser.parse("(transaction (epoch (writes) (reads))) extra")
end

@testitem "Parser - error on unterminated string" setup=[ParserSetup] begin
    @test_throws ParseError Parser.parse("(transaction \"hello")
end

@testitem "Parser - scan_string" setup=[ParserSetup] begin
    @test scan_string("\"hello\"") == "hello"
    @test scan_string("\"\"") == ""
    @test scan_string("\"a\\nb\"") == "a\nb"
    @test scan_string("\"a\\tb\"") == "a\tb"
    @test scan_string("\"a\\rb\"") == "a\rb"
    @test scan_string("\"a\\\\b\"") == "a\\b"
    @test scan_string("\"a\\\"b\"") == "a\"b"
    # \\n should become literal backslash followed by n
    @test scan_string("\"a\\\\nb\"") == "a\\nb"
end

@testitem "Parser - scan_int" setup=[ParserSetup] begin
    @test scan_int("0") == 0
    @test scan_int("42") == 42
    @test scan_int("-1") == -1
    @test scan_int(string(typemax(Int64))) == typemax(Int64)
    @test scan_int(string(typemin(Int64))) == typemin(Int64)
end

@testitem "Parser - scan_float" setup=[ParserSetup] begin
    @test scan_float("3.14") == 3.14
    @test scan_float("-1.5") == -1.5
    @test scan_float("inf") == Inf
    @test scan_float("nan") === NaN  # NaN !== NaN, but === checks bitwise
    @test isnan(scan_float("nan"))
end

@testitem "Parser - scan_int128" setup=[ParserSetup] begin
    r = scan_int128("0i128")
    @test r isa Proto.Int128Value
    @test r.low == 0
    @test r.high == 0

    r = scan_int128("1i128")
    @test r.low == 1
    @test r.high == 0

    r = scan_int128("-1i128")
    @test r.low == typemax(UInt64)
    @test r.high == typemax(UInt64)
end

@testitem "Parser - scan_uint128" setup=[ParserSetup] begin
    r = scan_uint128("0x0")
    @test r isa Proto.UInt128Value
    @test r.low == 0
    @test r.high == 0

    r = scan_uint128("0xffffffffffffffffffffffffffffffff")
    @test r.low == typemax(UInt64)
    @test r.high == typemax(UInt64)

    r = scan_uint128("0x10000000000000000")
    @test r.low == 0
    @test r.high == 1
end

@testitem "Parser - scan_decimal" setup=[ParserSetup] begin
    r = scan_decimal("123.456d6")
    @test r isa Proto.DecimalValue
    @test r.precision == 6
    @test r.scale == 3

    r = scan_decimal("0.0d1")
    @test r.precision == 1
    @test r.scale == 1

    r = scan_decimal("-1.5d4")
    @test r.precision == 4
    @test r.scale == 1
end

@testitem "Parser - Lexer tokenization" setup=[ParserSetup] begin
    lexer = Lexer("(transaction (epoch (writes) (reads)))")
    # Tokens: ( transaction ( epoch ( writes ) ( reads ) ) ) $
    @test length(lexer.tokens) == 13  # 12 meaningful + EOF
    @test lexer.tokens[1].type == "LITERAL"
    @test lexer.tokens[1].value == "("
    @test lexer.tokens[2].type == "SYMBOL"
    @test lexer.tokens[2].value == "transaction"
    @test lexer.tokens[end].type == "\$"
end

@testitem "Parser - round trip" setup=[ParserSetup] begin
    using ProtoBuf: ProtoBuf

    test_files_dir = joinpath(@__DIR__, "lqp")
    bin_files_dir = joinpath(@__DIR__, "bin")
    @test isdir(test_files_dir)

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))
    @test !isempty(lqp_files)

    for lqp_file in lqp_files
        lqp_path = joinpath(test_files_dir, lqp_file)
        bin_path = joinpath(bin_files_dir, replace(lqp_file, ".lqp" => ".bin"))

        content = read(lqp_path, String)
        result = Parser.parse(content)
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
