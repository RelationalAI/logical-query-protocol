@testitem "Pretty printer - format_string_value" begin
    using LogicalQueryProtocol: format_string_value
    @test format_string_value("hello") == "\"hello\""
    @test format_string_value("") == "\"\""
    @test format_string_value("a\"b") == "\"a\\\"b\""
    @test format_string_value("a\nb") == "\"a\\nb\""
    @test format_string_value("a\\b") == "\"a\\\\b\""
    @test format_string_value("a\tb") == "\"a\\tb\""
    @test format_string_value("a\rb") == "\"a\\rb\""
end

@testitem "Pretty printer - format_int128" begin
    using LogicalQueryProtocol: format_int128, PrettyPrinter, Proto
    pp = PrettyPrinter()

    # zero
    msg = Proto.Int128Value(UInt64(0), UInt64(0))
    @test format_int128(pp, msg) == "0i128"

    # positive
    msg = Proto.Int128Value(UInt64(42), UInt64(0))
    @test format_int128(pp, msg) == "42i128"

    # -1: low=0xffffffffffffffff, high=0xffffffffffffffff
    msg = Proto.Int128Value(typemax(UInt64), typemax(UInt64))
    @test format_int128(pp, msg) == "-1i128"
end

@testitem "Pretty printer - format_uint128" begin
    using LogicalQueryProtocol: format_uint128, PrettyPrinter, Proto
    pp = PrettyPrinter()

    msg = Proto.UInt128Value(UInt64(0), UInt64(0))
    @test format_uint128(pp, msg) == "0x0"

    msg = Proto.UInt128Value(typemax(UInt64), typemax(UInt64))
    @test format_uint128(pp, msg) == "0xffffffffffffffffffffffffffffffff"
end

@testitem "Pretty printer - format_decimal" begin
    using LogicalQueryProtocol: format_decimal, PrettyPrinter, Proto
    pp = PrettyPrinter()

    # 123.456d6 => value=123456, scale=3, precision=6
    value = Proto.Int128Value(UInt64(123456), UInt64(0))
    msg = Proto.DecimalValue(Int32(6), Int32(3), value)
    @test format_decimal(pp, msg) == "123.456d6"

    # 0.0d1
    value = Proto.Int128Value(UInt64(0), UInt64(0))
    msg = Proto.DecimalValue(Int32(1), Int32(1), value)
    @test format_decimal(pp, msg) == "0.0d1"
end

@testitem "Pretty printer - format_float64" begin
    using LogicalQueryProtocol: format_float64
    @test format_float64(3.14) == "3.14"
    @test format_float64(-1.5) == "-1.5"
    @test format_float64(Inf) == "inf"
    @test format_float64(NaN) == "nan"
end

@testitem "Pretty printer - indent/dedent" begin
    using LogicalQueryProtocol: PrettyPrinter, indent!, dedent!, indent_sexp!, indent_level
    pp = PrettyPrinter()
    @test indent_level(pp) == 0

    # indent! pushes the current column
    indent!(pp)
    @test length(pp.indent_stack) == 2
    @test indent_level(pp) == 0  # column is 0

    # indent_sexp! pushes current indent + 2
    dedent!(pp)
    indent_sexp!(pp)
    @test indent_level(pp) == 2

    indent_sexp!(pp)
    @test indent_level(pp) == 4

    dedent!(pp)
    @test indent_level(pp) == 2

    dedent!(pp)
    @test indent_level(pp) == 0

    # dedent! doesn't pop below 1 element
    dedent!(pp)
    @test indent_level(pp) == 0
    @test length(pp.indent_stack) == 1
end

@testitem "Pretty printer - try_flat memoization" begin
    using LogicalQueryProtocol: PrettyPrinter, try_flat, Proto

    pp = PrettyPrinter()
    txn = Proto.Transaction(Proto.Epoch[], nothing, nothing)
    msg_id = objectid(txn)

    @test !haskey(pp._memo, msg_id)

    # After try_flat, the memo dict should be populated
    result = try_flat(pp, txn, (pp, msg) -> Base.write(pp, "(transaction)"))
    @test haskey(pp._memo, msg_id)
    @test pp._memo[msg_id] == "(transaction)"
end

@testitem "Pretty printer - narrow width roundtrip" begin
    using LogicalQueryProtocol: parse, pretty, Proto

    test_files_dir = joinpath(@__DIR__, "lqp")
    isdir(test_files_dir) || return

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))
    for lqp_file in lqp_files
        content = read(joinpath(test_files_dir, lqp_file), String)
        parsed = parse(content)

        narrow = pretty(parsed; max_width=40)
        reparsed = parse(narrow)
        @test reparsed == parsed
    end
end

@testitem "Pretty printer - wide width roundtrip" begin
    using LogicalQueryProtocol: parse, pretty, Proto

    test_files_dir = joinpath(@__DIR__, "lqp")
    isdir(test_files_dir) || return

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))
    for lqp_file in lqp_files
        content = read(joinpath(test_files_dir, lqp_file), String)
        parsed = parse(content)

        wide = pretty(parsed; max_width=1000)
        reparsed = parse(wide)
        @test reparsed == parsed
    end
end

@testitem "Pretty printer - width affects line count" begin
    using LogicalQueryProtocol: parse, pretty, Proto

    test_files_dir = joinpath(@__DIR__, "lqp")
    isdir(test_files_dir) || return

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))
    for lqp_file in lqp_files
        content = read(joinpath(test_files_dir, lqp_file), String)
        parsed = parse(content)

        narrow = pretty(parsed; max_width=40)
        default = pretty(parsed)
        wide = pretty(parsed; max_width=1000)

        narrow_lines = count('\n', narrow)
        default_lines = count('\n', default)
        wide_lines = count('\n', wide)

        @test narrow_lines >= default_lines
        @test wide_lines <= default_lines
    end
end

@testitem "Pretty printer - output invariants" begin
    using LogicalQueryProtocol: parse, pretty, Proto

    test_files_dir = joinpath(@__DIR__, "lqp")
    isdir(test_files_dir) || return

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))
    for lqp_file in lqp_files
        content = read(joinpath(test_files_dir, lqp_file), String)
        parsed = parse(content)
        printed = pretty(parsed)

        # Starts with (transaction
        @test startswith(printed, "(transaction")

        # Ends with newline
        @test endswith(printed, "\n")

        # Balanced parens
        @test count('(', printed) == count(')', printed)

        # Balanced brackets
        @test count('[', printed) == count(']', printed)

        # No trailing whitespace on any line
        for line in split(printed, "\n")
            @test line == rstrip(line)
        end
    end
end

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
    end
end
