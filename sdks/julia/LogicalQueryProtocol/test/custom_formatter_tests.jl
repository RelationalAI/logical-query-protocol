@testitem "Custom formatter - decimal only" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_decimal, format_int128, format_uint128
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that only overrides decimal
    struct DecimalOnlyFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_decimal(
        formatter::DecimalOnlyFormatter,
        pp::PrettyPrinter,
        msg::Proto.DecimalValue
    )::String
        return "CUSTOM_DECIMAL"
    end

    # Test decimal formatting
    decimal_msg = Proto.DecimalValue(
        precision=Int32(18),
        scale=Int32(6),
        value=Proto.Int128Value(UInt64(123456789), UInt64(0)),
    )
    pp = PrettyPrinter(constant_formatter=DecimalOnlyFormatter())
    _pprint_dispatch(pp, decimal_msg)
    @test get_output(pp) == "CUSTOM_DECIMAL"

    # Test that int128 still uses default formatting
    int128_msg = Proto.Int128Value(UInt64(42), UInt64(0))
    pp = PrettyPrinter(constant_formatter=DecimalOnlyFormatter())
    _pprint_dispatch(pp, int128_msg)
    @test get_output(pp) == "42i128"

    # Test that uint128 still uses default formatting
    uint128_msg = Proto.UInt128Value(UInt64(255), UInt64(0))
    pp = PrettyPrinter(constant_formatter=DecimalOnlyFormatter())
    _pprint_dispatch(pp, uint128_msg)
    @test get_output(pp) == "0xff"
end

@testitem "Custom formatter - int128 only" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_decimal, format_int128, format_uint128
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that only overrides int128
    struct Int128OnlyFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_int128(
        formatter::Int128OnlyFormatter,
        pp::PrettyPrinter,
        msg::Proto.Int128Value
    )::String
        return "CUSTOM_INT128"
    end

    # Test int128 formatting
    int128_msg = Proto.Int128Value(UInt64(42), UInt64(0))
    pp = PrettyPrinter(constant_formatter=Int128OnlyFormatter())
    _pprint_dispatch(pp, int128_msg)
    @test get_output(pp) == "CUSTOM_INT128"

    # Test that decimal still uses default formatting
    decimal_msg = Proto.DecimalValue(
        precision=Int32(6),
        scale=Int32(3),
        value=Proto.Int128Value(UInt64(123456), UInt64(0)),
    )
    pp = PrettyPrinter(constant_formatter=Int128OnlyFormatter())
    _pprint_dispatch(pp, decimal_msg)
    @test get_output(pp) == "123.456d6"

    # Test that uint128 still uses default formatting
    uint128_msg = Proto.UInt128Value(UInt64(255), UInt64(0))
    pp = PrettyPrinter(constant_formatter=Int128OnlyFormatter())
    _pprint_dispatch(pp, uint128_msg)
    @test get_output(pp) == "0xff"
end

@testitem "Custom formatter - uint128 only" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_decimal, format_int128, format_uint128
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that only overrides uint128
    struct UInt128OnlyFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_uint128(
        formatter::UInt128OnlyFormatter,
        pp::PrettyPrinter,
        msg::Proto.UInt128Value
    )::String
        return "CUSTOM_UINT128"
    end

    # Test uint128 formatting
    uint128_msg = Proto.UInt128Value(UInt64(255), UInt64(0))
    pp = PrettyPrinter(constant_formatter=UInt128OnlyFormatter())
    _pprint_dispatch(pp, uint128_msg)
    @test get_output(pp) == "CUSTOM_UINT128"

    # Test that decimal still uses default formatting
    decimal_msg = Proto.DecimalValue(
        precision=Int32(6),
        scale=Int32(3),
        value=Proto.Int128Value(UInt64(123456), UInt64(0)),
    )
    pp = PrettyPrinter(constant_formatter=UInt128OnlyFormatter())
    _pprint_dispatch(pp, decimal_msg)
    @test get_output(pp) == "123.456d6"

    # Test that int128 still uses default formatting
    int128_msg = Proto.Int128Value(UInt64(42), UInt64(0))
    pp = PrettyPrinter(constant_formatter=UInt128OnlyFormatter())
    _pprint_dispatch(pp, int128_msg)
    @test get_output(pp) == "42i128"
end

@testitem "Custom formatter - all types" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_decimal, format_int128, format_uint128
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that overrides all types
    struct AllCustomFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_decimal(
        formatter::AllCustomFormatter,
        pp::PrettyPrinter,
        msg::Proto.DecimalValue
    )::String
        return "DECIMAL"
    end

    function LogicalQueryProtocol.format_int128(
        formatter::AllCustomFormatter,
        pp::PrettyPrinter,
        msg::Proto.Int128Value
    )::String
        return "INT128"
    end

    function LogicalQueryProtocol.format_uint128(
        formatter::AllCustomFormatter,
        pp::PrettyPrinter,
        msg::Proto.UInt128Value
    )::String
        return "UINT128"
    end

    # Test decimal formatting
    decimal_msg = Proto.DecimalValue(
        precision=Int32(18),
        scale=Int32(6),
        value=Proto.Int128Value(UInt64(123456789), UInt64(0)),
    )
    pp = PrettyPrinter(constant_formatter=AllCustomFormatter())
    _pprint_dispatch(pp, decimal_msg)
    @test get_output(pp) == "DECIMAL"

    # Test int128 formatting
    int128_msg = Proto.Int128Value(UInt64(42), UInt64(0))
    pp = PrettyPrinter(constant_formatter=AllCustomFormatter())
    _pprint_dispatch(pp, int128_msg)
    @test get_output(pp) == "INT128"

    # Test uint128 formatting
    uint128_msg = Proto.UInt128Value(UInt64(255), UInt64(0))
    pp = PrettyPrinter(constant_formatter=AllCustomFormatter())
    _pprint_dispatch(pp, uint128_msg)
    @test get_output(pp) == "UINT128"
end

@testitem "Custom formatter - pprint API integration" begin
    using LogicalQueryProtocol
    using LogicalQueryProtocol: ConstantFormatter, pprint
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter
    struct ApiTestFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_decimal(
        formatter::ApiTestFormatter,
        pp::LogicalQueryProtocol.PrettyPrinter,
        msg::Proto.DecimalValue
    )::String
        return "FORMATTED"
    end

    # Test with pprint(io, x, constant_formatter=...)
    decimal_msg = Proto.DecimalValue(
        precision=Int32(6),
        scale=Int32(3),
        value=Proto.Int128Value(UInt64(123456), UInt64(0)),
    )
    io = IOBuffer()
    pprint(io, decimal_msg, constant_formatter=ApiTestFormatter())
    @test String(take!(io)) == "FORMATTED\n"

    # Test default formatter still works
    io = IOBuffer()
    pprint(io, decimal_msg)
    @test String(take!(io)) == "123.456d6\n"
end

@testitem "Custom formatter - access to pp parameter" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_int128
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that uses pp parameter
    struct PpAwareFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_int128(
        formatter::PpAwareFormatter,
        pp::PrettyPrinter,
        msg::Proto.Int128Value
    )::String
        # Access pp fields to verify we have access
        if pp.max_width > 50
            return "WIDE"
        else
            return "NARROW"
        end
    end

    # Test with wide width
    int128_msg = Proto.Int128Value(UInt64(42), UInt64(0))
    pp = PrettyPrinter(max_width=100, constant_formatter=PpAwareFormatter())
    _pprint_dispatch(pp, int128_msg)
    @test get_output(pp) == "WIDE"

    # Test with narrow width
    pp = PrettyPrinter(max_width=40, constant_formatter=PpAwareFormatter())
    _pprint_dispatch(pp, int128_msg)
    @test get_output(pp) == "NARROW"
end

@testitem "Custom formatter - scientific notation for decimals" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_decimal
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define formatter that uses scientific notation
    struct ScientificFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_decimal(
        formatter::ScientificFormatter,
        pp::PrettyPrinter,
        msg::Proto.DecimalValue
    )::String
        # Extract the integer value
        int_val = Int128(msg.value.high) << 64 | Int128(msg.value.low)
        if msg.value.high & (UInt64(1) << 63) != 0
            int_val -= Int128(1) << 128
        end
        scale = Int(msg.scale)
        # Convert to floating point and format
        float_val = Float64(int_val) / 10.0^scale
        return string(float_val) * "e" * string(msg.precision)
    end

    # Test scientific notation
    decimal_msg = Proto.DecimalValue(
        precision=Int32(18),
        scale=Int32(6),
        value=Proto.Int128Value(UInt64(123456789), UInt64(0)),
    )
    pp = PrettyPrinter(constant_formatter=ScientificFormatter())
    _pprint_dispatch(pp, decimal_msg)
    output = get_output(pp)
    @test contains(output, "e18")
    @test contains(output, "123.456")
end

@testitem "Custom formatter - backward compatibility methods" begin
    using LogicalQueryProtocol: format_decimal, format_int128, format_uint128
    using LogicalQueryProtocol: PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Test that old 2-argument signature still works (backward compatibility)
    pp = PrettyPrinter()

    # Test format_decimal(pp, msg)
    decimal_msg = Proto.DecimalValue(
        precision=Int32(6),
        scale=Int32(3),
        value=Proto.Int128Value(UInt64(123456), UInt64(0)),
    )
    @test format_decimal(pp, decimal_msg) == "123.456d6"

    # Test format_int128(pp, msg)
    int128_msg = Proto.Int128Value(UInt64(42), UInt64(0))
    @test format_int128(pp, int128_msg) == "42i128"

    # Test format_uint128(pp, msg)
    uint128_msg = Proto.UInt128Value(UInt64(255), UInt64(0))
    @test format_uint128(pp, uint128_msg) == "0xff"
end

@testitem "Custom formatter - multiple instances" begin
    using LogicalQueryProtocol: ConstantFormatter
    using LogicalQueryProtocol: format_int128
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define two different formatters
    struct FormatterA <: ConstantFormatter end
    struct FormatterB <: ConstantFormatter end

    function LogicalQueryProtocol.format_int128(
        formatter::FormatterA,
        pp::PrettyPrinter,
        msg::Proto.Int128Value
    )::String
        return "FORMAT_A"
    end

    function LogicalQueryProtocol.format_int128(
        formatter::FormatterB,
        pp::PrettyPrinter,
        msg::Proto.Int128Value
    )::String
        return "FORMAT_B"
    end

    int128_msg = Proto.Int128Value(UInt64(42), UInt64(0))

    # Test formatter A
    pp = PrettyPrinter(constant_formatter=FormatterA())
    _pprint_dispatch(pp, int128_msg)
    @test get_output(pp) == "FORMAT_A"

    # Test formatter B
    pp = PrettyPrinter(constant_formatter=FormatterB())
    _pprint_dispatch(pp, int128_msg)
    @test get_output(pp) == "FORMAT_B"
end
