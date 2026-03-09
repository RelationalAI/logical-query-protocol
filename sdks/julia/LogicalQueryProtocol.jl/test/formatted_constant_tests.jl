@testitem "Default formatter - int32" setup=[PrettySetup] begin
    pp = PrettyPrinter()

    @test format_int32(pp, Int32(42)) == "42i32"
    @test format_int32(pp, Int32(-123)) == "-123i32"
    @test format_int32(pp, Int32(0)) == "0i32"
    @test format_int32(pp, typemax(Int32)) == "2147483647i32"
    @test format_int32(pp, typemin(Int32)) == "-2147483648i32"
end

@testitem "Default formatter - float32" setup=[PrettySetup] begin
    pp = PrettyPrinter()

    @test format_float32(pp, Float32(3.14)) == "3.14f32"
    @test format_float32(pp, Float32(-2.5)) == "-2.5f32"
    @test format_float32(pp, Float32(0.0)) == "0.0f32"
    @test format_float32(pp, Float32(Inf)) == "inff32"
    @test format_float32(pp, Float32(NaN)) == "nanf32"
end

@testitem "Custom formatter - int32" setup=[PrettySetup] begin
    struct Int32Formatter <: ConstantFormatter end

    function Pretty.format_int32(
        formatter::Int32Formatter,
        pp::PrettyPrinter,
        v::Int32,
    )::String
        return "I32[$(v)]"
    end

    pp = PrettyPrinter(constant_formatter=Int32Formatter())
    @test format_int32(pp, Int32(42)) == "I32[42]"
    @test format_int32(pp, Int32(-1)) == "I32[-1]"

    # Other types still use default formatting
    @test format_int(pp, Int64(42)) == "42"
    @test format_float(pp, 3.14) == "3.14"
end

@testitem "Custom formatter - float32" setup=[PrettySetup] begin
    struct Float32Formatter <: ConstantFormatter end

    function Pretty.format_float32(
        formatter::Float32Formatter,
        pp::PrettyPrinter,
        v::Float32,
    )::String
        return "F32[$(v)]"
    end

    pp = PrettyPrinter(constant_formatter=Float32Formatter())
    @test format_float32(pp, Float32(1.5)) == "F32[1.5]"

    # Other types still use default formatting
    @test format_float(pp, 3.14) == "3.14"
    @test format_int(pp, Int64(42)) == "42"
end

@testitem "Custom formatter - int32/float32 with all types" setup=[PrettySetup] begin
    struct AllFormatter32 <: ConstantFormatter end

    Pretty.format_int(::AllFormatter32, ::PrettyPrinter, v::Int64)::String = "i:$(v)"
    Pretty.format_int32(::AllFormatter32, ::PrettyPrinter, v::Int32)::String = "i32:$(v)"
    Pretty.format_float(::AllFormatter32, ::PrettyPrinter, v::Float64)::String = "f:$(v)"
    Pretty.format_float32(::AllFormatter32, ::PrettyPrinter, v::Float32)::String = "f32:$(v)"
    Pretty.format_string(::AllFormatter32, ::PrettyPrinter, s::AbstractString)::String = "s:$(s)"
    Pretty.format_bool(::AllFormatter32, ::PrettyPrinter, v::Bool)::String = "b:$(v)"
    function Pretty.format_decimal(::AllFormatter32, ::PrettyPrinter, msg::Proto.DecimalValue)::String
        return "dec"
    end
    function Pretty.format_int128(::AllFormatter32, ::PrettyPrinter, msg::Proto.Int128Value)::String
        return "i128"
    end
    function Pretty.format_uint128(::AllFormatter32, ::PrettyPrinter, msg::Proto.UInt128Value)::String
        return "u128"
    end

    pp = PrettyPrinter(constant_formatter=AllFormatter32())

    @test format_int(pp, Int64(1)) == "i:1"
    @test format_int32(pp, Int32(2)) == "i32:2"
    @test format_float(pp, 3.14) == "f:3.14"
    @test format_float32(pp, Float32(1.5)) == "f32:1.5"
    @test format_string(pp, "hello") == "s:hello"
    @test format_bool(pp, true) == "b:true"
end

@testitem "Custom formatter - int32 via _pprint_dispatch" setup=[PrettySetup] begin
    struct I32DispatchFormatter <: ConstantFormatter end

    function Pretty.format_int32(
        formatter::I32DispatchFormatter,
        pp::PrettyPrinter,
        v::Int32,
    )::String
        return "CUSTOM_I32"
    end

    # Proto.Value with int32_value goes through the formatted path
    val = Proto.Value(OneOf(:int32_value, Int32(42)))
    pp = PrettyPrinter(constant_formatter=I32DispatchFormatter())
    _pprint_dispatch(pp, val)
    @test get_output(pp) == "CUSTOM_I32"

    # Default formatter still works
    pp_default = PrettyPrinter()
    _pprint_dispatch(pp_default, val)
    @test get_output(pp_default) == "42i32"
end

@testitem "Custom formatter - float32 via _pprint_dispatch" setup=[PrettySetup] begin
    struct F32DispatchFormatter <: ConstantFormatter end

    function Pretty.format_float32(
        formatter::F32DispatchFormatter,
        pp::PrettyPrinter,
        v::Float32,
    )::String
        return "CUSTOM_F32"
    end

    val = Proto.Value(OneOf(:float32_value, Float32(1.5)))
    pp = PrettyPrinter(constant_formatter=F32DispatchFormatter())
    _pprint_dispatch(pp, val)
    @test get_output(pp) == "CUSTOM_F32"

    pp_default = PrettyPrinter()
    _pprint_dispatch(pp_default, val)
    @test get_output(pp_default) == "1.5f32"
end

@testitem "Custom formatter - int via _pprint_dispatch" setup=[PrettySetup] begin
    struct IntDispatchFormatter <: ConstantFormatter end

    Pretty.format_int(::IntDispatchFormatter, ::PrettyPrinter, v::Int64)::String = "INT<$(v)>"

    val = Proto.Value(OneOf(:int_value, Int64(42)))
    pp = PrettyPrinter(constant_formatter=IntDispatchFormatter())
    _pprint_dispatch(pp, val)
    @test get_output(pp) == "INT<42>"
end

@testitem "Custom formatter - float via _pprint_dispatch" setup=[PrettySetup] begin
    struct FloatDispatchFormatter <: ConstantFormatter end

    Pretty.format_float(::FloatDispatchFormatter, ::PrettyPrinter, v::Float64)::String = "FLT<$(v)>"

    val = Proto.Value(OneOf(:float_value, Float64(3.14)))
    pp = PrettyPrinter(constant_formatter=FloatDispatchFormatter())
    _pprint_dispatch(pp, val)
    @test get_output(pp) == "FLT<3.14>"
end

@testitem "Custom formatter - string via _pprint_dispatch" setup=[PrettySetup] begin
    struct StrDispatchFormatter <: ConstantFormatter end

    Pretty.format_string(::StrDispatchFormatter, ::PrettyPrinter, s::AbstractString)::String = "STR<$(s)>"

    val = Proto.Value(OneOf(:string_value, "hello"))
    pp = PrettyPrinter(constant_formatter=StrDispatchFormatter())
    _pprint_dispatch(pp, val)
    @test get_output(pp) == "STR<hello>"
end

@testitem "Formatted constants - round trip with default formatter" setup=[ParserSetup, PrettySetup] begin
    lqp = """
    (transaction
      (configure
        { :semantics_version 1
          :ivm.maintenance_level "auto"})
      (epoch
        (writes
          (define
            (fragment :f1
              (def :output ([v::INT] (+ 1 1 v))))))
        (reads
          (output :output :output))))
    """
    parsed, _ = Parser.parse(lqp)

    printed = pretty(parsed)
    reparsed, _ = Parser.parse(printed)
    @test reparsed == parsed

    reprinted = pretty(reparsed)
    @test printed == reprinted
end

@testitem "Formatted constants - int32/float32 value types round trip" setup=[ParserSetup, PrettySetup] begin
    # Test that int32 and float32 values survive parse/pretty round trip
    lqp = """
    (transaction
      (epoch
        (writes
          (define
            (fragment :f1
              (def :foo ([v::INT32] (= v 42i32)))
              (def :bar ([w::FLOAT32] (= w 3.14f32))))))
        (reads
          (output :foo :foo)
          (output :bar :bar))))
    """
    parsed, _ = Parser.parse(lqp)
    printed = pretty(parsed)
    reparsed, _ = Parser.parse(printed)
    @test reparsed == parsed
end
