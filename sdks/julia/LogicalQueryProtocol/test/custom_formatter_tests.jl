@testitem "Default formatter - int" begin
    using LogicalQueryProtocol: format_int, PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    pp = PrettyPrinter()

    # Test positive Int64
    @test format_int(pp, Int64(42)) == "42"

    # Test negative Int64
    @test format_int(pp, Int64(-123)) == "-123"

    # Test zero
    @test format_int(pp, Int64(0)) == "0"

    # Test Int32
    @test format_int(pp, Int32(99)) == "99"

    # Test large values
    @test format_int(pp, Int64(9223372036854775807)) == "9223372036854775807"
end

@testitem "Default formatter - float" begin
    using LogicalQueryProtocol: format_float, PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    pp = PrettyPrinter()

    # Test positive float
    @test format_float(pp, 3.14) == "3.14"

    # Test negative float
    @test format_float(pp, -2.5) == "-2.5"

    # Test zero
    @test format_float(pp, 0.0) == "0.0"

    # Test special values (lowercase for default formatter)
    @test format_float(pp, Inf) == "inf"
    @test format_float(pp, -Inf) == "-inf"
    @test format_float(pp, NaN) == "nan"

    # Test scientific notation
    @test format_float(pp, 1.23e10) == "1.23e10"
end

@testitem "Default formatter - string" begin
    using LogicalQueryProtocol: format_string, PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    pp = PrettyPrinter()

    # Test simple string
    @test format_string(pp, "hello") == "\"hello\""

    # Test empty string
    @test format_string(pp, "") == "\"\""

    # Test string with escaped characters
    @test format_string(pp, "hello\"world") == "\"hello\\\"world\""
    @test format_string(pp, "hello\\world") == "\"hello\\\\world\""
    @test format_string(pp, "hello\nworld") == "\"hello\\nworld\""
    @test format_string(pp, "hello\rworld") == "\"hello\\rworld\""
    @test format_string(pp, "hello\tworld") == "\"hello\\tworld\""

    # Test all escapes together
    @test format_string(pp, "\\\"\n\r\t") == "\"\\\\\\\"\\n\\r\\t\""
end

@testitem "Default formatter - bool" begin
    using LogicalQueryProtocol: format_bool, PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    pp = PrettyPrinter()

    # Test true
    @test format_bool(pp, true) == "true"

    # Test false
    @test format_bool(pp, false) == "false"
end

@testitem "Default formatter - decimal" begin
    using LogicalQueryProtocol: format_decimal, PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    pp = PrettyPrinter()

    # Test positive decimal
    decimal_msg = Proto.DecimalValue(
        precision=Int32(18),
        scale=Int32(6),
        value=Proto.Int128Value(UInt64(123456789), UInt64(0)),
    )
    @test format_decimal(pp, decimal_msg) == "123.456789d18"

    # Test decimal with leading zeros after decimal point
    decimal_msg2 = Proto.DecimalValue(
        precision=Int32(6),
        scale=Int32(5),
        value=Proto.Int128Value(UInt64(123), UInt64(0)),
    )
    @test format_decimal(pp, decimal_msg2) == "0.00123d6"

    # Test decimal with trailing zeros (negative scale)
    decimal_msg3 = Proto.DecimalValue(
        precision=Int32(6),
        scale=Int32(-2),
        value=Proto.Int128Value(UInt64(123), UInt64(0)),
    )
    @test format_decimal(pp, decimal_msg3) == "123.00d6"
end

@testitem "Default formatter - int128" begin
    using LogicalQueryProtocol: format_int128, PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    pp = PrettyPrinter()

    # Test positive int128
    int128_msg = Proto.Int128Value(UInt64(42), UInt64(0))
    @test format_int128(pp, int128_msg) == "42i128"

    # Test negative int128 (using two's complement)
    int128_msg_neg = Proto.Int128Value(UInt64(0xFFFFFFFFFFFFFFFF), UInt64(0xFFFFFFFFFFFFFFFF))
    @test format_int128(pp, int128_msg_neg) == "-1i128"

    # Test zero
    int128_msg_zero = Proto.Int128Value(UInt64(0), UInt64(0))
    @test format_int128(pp, int128_msg_zero) == "0i128"
end

@testitem "Default formatter - uint128" begin
    using LogicalQueryProtocol: format_uint128, PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    pp = PrettyPrinter()

    # Test uint128
    uint128_msg = Proto.UInt128Value(UInt64(255), UInt64(0))
    @test format_uint128(pp, uint128_msg) == "0xff"

    # Test zero
    uint128_msg_zero = Proto.UInt128Value(UInt64(0), UInt64(0))
    @test format_uint128(pp, uint128_msg_zero) == "0x0"

    # Test max value in low part
    uint128_msg_max = Proto.UInt128Value(UInt64(0xFFFFFFFFFFFFFFFF), UInt64(0))
    @test format_uint128(pp, uint128_msg_max) == "0xffffffffffffffff"

    # Test with high part set
    uint128_msg_high = Proto.UInt128Value(UInt64(0x42), UInt64(0x1))
    @test format_uint128(pp, uint128_msg_high) == "0x10000000000000042"
end

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

@testitem "Custom formatter - int (Int64)" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_int
    using LogicalQueryProtocol: PrettyPrinter, format_int
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that overrides int
    struct IntFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_int(
        formatter::IntFormatter,
        pp::PrettyPrinter,
        v::Integer
    )::String
        return "INT[$(v)]"
    end

    # Test with direct format_int call
    pp = PrettyPrinter(constant_formatter=IntFormatter())
    result = format_int(pp, Int64(42))
    @test result == "INT[42]"

    # Test with negative value
    result = format_int(pp, Int64(-123))
    @test result == "INT[-123]"

    # Test with Int32
    result = format_int(pp, Int32(99))
    @test result == "INT[99]"
end

@testitem "Custom formatter - float" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_float
    using LogicalQueryProtocol: PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that overrides float
    struct FloatFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_float(
        formatter::FloatFormatter,
        pp::PrettyPrinter,
        v::Float64
    )::String
        return "FLOAT[$(v)]"
    end

    # Test with direct format_float call
    pp = PrettyPrinter(constant_formatter=FloatFormatter())
    result = format_float(pp, 3.14)
    @test result == "FLOAT[3.14]"

    # Test with negative value
    result = format_float(pp, -2.5)
    @test result == "FLOAT[-2.5]"

    # Test with special values
    result = format_float(pp, Inf)
    @test result == "FLOAT[Inf]"
end

@testitem "Custom formatter - string" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_string
    using LogicalQueryProtocol: PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that overrides string
    struct StringFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_string(
        formatter::StringFormatter,
        pp::PrettyPrinter,
        s::AbstractString
    )::String
        return "STR<$(s)>"
    end

    # Test with direct format_string call
    pp = PrettyPrinter(constant_formatter=StringFormatter())
    result = format_string(pp, "hello")
    @test result == "STR<hello>"

    # Test with empty string
    result = format_string(pp, "")
    @test result == "STR<>"

    # Test with special characters (formatter bypasses escaping)
    result = format_string(pp, "hello\nworld")
    @test result == "STR<hello\nworld>"
end

@testitem "Custom formatter - bool" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_bool
    using LogicalQueryProtocol: PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that overrides bool
    struct BoolFormatter <: ConstantFormatter end

    function LogicalQueryProtocol.format_bool(
        formatter::BoolFormatter,
        pp::PrettyPrinter,
        v::Bool
    )::String
        return v ? "YES" : "NO"
    end

    # Test with direct format_bool call
    pp = PrettyPrinter(constant_formatter=BoolFormatter())
    result = format_bool(pp, true)
    @test result == "YES"

    result = format_bool(pp, false)
    @test result == "NO"
end

@testitem "Custom formatter - all types combined" begin
    using LogicalQueryProtocol: ConstantFormatter, DefaultConstantFormatter
    using LogicalQueryProtocol: format_int, format_float, format_string, format_bool
    using LogicalQueryProtocol: format_decimal, format_int128, format_uint128
    using LogicalQueryProtocol: PrettyPrinter
    const Proto = LogicalQueryProtocol.relationalai.lqp.v1

    # Define custom formatter that overrides all types with a prefix
    struct PrefixFormatter <: ConstantFormatter end

    LogicalQueryProtocol.format_int(formatter::PrefixFormatter, pp::PrettyPrinter, v::Integer)::String = "i:$(v)"
    LogicalQueryProtocol.format_float(formatter::PrefixFormatter, pp::PrettyPrinter, v::Float64)::String = "f:$(v)"
    LogicalQueryProtocol.format_string(formatter::PrefixFormatter, pp::PrettyPrinter, s::AbstractString)::String = "s:$(s)"
    LogicalQueryProtocol.format_bool(formatter::PrefixFormatter, pp::PrettyPrinter, v::Bool)::String = "b:$(v)"
    function LogicalQueryProtocol.format_decimal(formatter::PrefixFormatter, pp::PrettyPrinter, msg::Proto.DecimalValue)::String
        return "d:DECIMAL"
    end
    function LogicalQueryProtocol.format_int128(formatter::PrefixFormatter, pp::PrettyPrinter, msg::Proto.Int128Value)::String
        return "i128:INT128"
    end
    function LogicalQueryProtocol.format_uint128(formatter::PrefixFormatter, pp::PrettyPrinter, msg::Proto.UInt128Value)::String
        return "u128:UINT128"
    end

    pp = PrettyPrinter(constant_formatter=PrefixFormatter())

    # Test all types
    @test format_int(pp, 42) == "i:42"
    @test format_float(pp, 3.14) == "f:3.14"
    @test format_string(pp, "test") == "s:test"
    @test format_bool(pp, true) == "b:true"

    decimal_msg = Proto.DecimalValue(precision=Int32(18), scale=Int32(6), value=Proto.Int128Value(UInt64(123), UInt64(0)))
    @test format_decimal(pp, decimal_msg) == "d:DECIMAL"

    int128_msg = Proto.Int128Value(UInt64(42), UInt64(0))
    @test format_int128(pp, int128_msg) == "i128:INT128"

    uint128_msg = Proto.UInt128Value(UInt64(255), UInt64(0))
    @test format_uint128(pp, uint128_msg) == "u128:UINT128"
end
