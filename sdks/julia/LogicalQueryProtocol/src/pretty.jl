# Auto-generated pretty printer.
#
# Generated from protobuf specifications.
# Do not modify this file! If you need to modify the pretty printer, edit the generator code
# in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.
#
# Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer julia

mutable struct PrettyPrinter
    io::IOBuffer
    indent_level::Int
    at_line_start::Bool
    debug_info::Dict{Tuple{UInt64,UInt64},String}
end

PrettyPrinter() = PrettyPrinter(IOBuffer(), 0, true, Dict{Tuple{UInt64,UInt64},String}())

function Base.write(pp::PrettyPrinter, s::AbstractString)
    if pp.at_line_start && !isempty(strip(s))
        Base.write(pp.io, repeat("  ", pp.indent_level))
        pp.at_line_start = false
    end
    return Base.write(pp.io, s)
end

function newline(pp::PrettyPrinter)
    Base.write(pp.io, "\n")
    pp.at_line_start = true
    return nothing
end

function indent!(pp::PrettyPrinter)
    pp.indent_level += 1
    return nothing
end

function dedent!(pp::PrettyPrinter)
    pp.indent_level = max(0, pp.indent_level - 1)
    return nothing
end

function get_output(pp::PrettyPrinter)::String
    return String(copy(pp.io.data[1:pp.io.size]))
end

function format_decimal(pp::PrettyPrinter, msg::Proto.DecimalValue)::String
    int_val = Int128(msg.value.high) << 64 | Int128(msg.value.low)
    if msg.value.high & (UInt64(1) << 63) != 0
        int_val -= Int128(1) << 128
    end
    sign = ""
    if int_val < 0
        sign = "-"
        int_val = -int_val
    end
    digits = string(int_val)
    scale = Int(msg.scale)
    if scale <= 0
        decimal_str = digits * "." * repeat("0", -scale)
    elseif scale >= length(digits)
        decimal_str = "0." * repeat("0", scale - length(digits)) * digits
    else
        decimal_str = digits[1:end-scale] * "." * digits[end-scale+1:end]
    end
    return sign * decimal_str * "d" * string(msg.precision)
end

function format_int128(pp::PrettyPrinter, msg::Proto.Int128Value)::String
    value = Int128(msg.high) << 64 | Int128(msg.low)
    if msg.high & (UInt64(1) << 63) != 0
        value -= Int128(1) << 128
    end
    return string(value) * "i128"
end

function format_uint128(pp::PrettyPrinter, msg::Proto.UInt128Value)::String
    value = UInt128(msg.high) << 64 | UInt128(msg.low)
    return "0x" * string(value, base=16)
end

function format_float64(v::Float64)::String
    return lowercase(string(v))
end

function format_string_value(s::AbstractString)::String
    escaped = replace(s, "\\" => "\\\\")
    escaped = replace(escaped, "\"" => "\\\"")
    escaped = replace(escaped, "\n" => "\\n")
    escaped = replace(escaped, "\r" => "\\r")
    escaped = replace(escaped, "\t" => "\\t")
    return "\"" * escaped * "\""
end

function fragment_id_to_string(pp::PrettyPrinter, msg::Proto.FragmentId)::String
    if isempty(msg.id)
        return ""
    end
    return String(copy(msg.id))
end

function start_pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)::Nothing
    debug_info = msg.debug_info
    if isnothing(debug_info)
        return nothing
    end
    for (rid, name) in zip(debug_info.ids, debug_info.orig_names)
        pp.debug_info[(rid.id_low, rid.id_high)] = name
    end
    return nothing
end

function relation_id_to_string(pp::PrettyPrinter, msg::Proto.RelationId)::String
    return get(pp.debug_info, (msg.id_low, msg.id_high), "")
end

function relation_id_to_int(pp::PrettyPrinter, msg::Proto.RelationId)
    if msg.id_high == 0 && msg.id_low <= 0x7FFFFFFFFFFFFFFF
        return Int64(msg.id_low)
    end
    return nothing
end

function relation_id_to_uint128(pp::PrettyPrinter, msg::Proto.RelationId)
    return Proto.UInt128Value(msg.id_low, msg.id_high)
end

# --- Helper functions ---

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1284 = Proto.Value(value=OneOf(:int_value, v))
    return _t1284
end

function deconstruct_bindings_with_arity(pp::PrettyPrinter, abs::Proto.Abstraction, value_arity::Int64)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    n = length(abs.vars)
    key_end = (n - value_arity)
    return (abs.vars[0 + 1:key_end], abs.vars[key_end + 1:n],)
end

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1285 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1285
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1286 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1286
end

function deconstruct_relation_id_uint128(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, Proto.UInt128Value}
    name = relation_id_to_string(pp, msg)
    if name == ""
        return relation_id_to_uint128(pp, msg)
    end
    return nothing
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1287 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1287
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1288 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1288,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1289 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1289,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1290 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1290,))
            end
        end
    end
    _t1291 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1291,))
    return sort(result)
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1292 = Proto.Value(value=OneOf(:float_value, v))
    return _t1292
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1293 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1293,))
    _t1294 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1294,))
    if msg.new_line != ""
        _t1295 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1295,))
    end
    _t1296 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1296,))
    _t1297 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1297,))
    _t1298 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1298,))
    if msg.comment != ""
        _t1299 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1299,))
    end
    for missing_string in msg.missing_strings
        _t1300 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1300,))
    end
    _t1301 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1301,))
    _t1302 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1302,))
    _t1303 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1303,))
    return sort(result)
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1304 = Proto.Value(value=OneOf(:string_value, v))
    return _t1304
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1305 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1305,))
    _t1306 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1306,))
    _t1307 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1307,))
    _t1308 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1308,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1309 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1309,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1310 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1310,))
        end
    end
    _t1311 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1311,))
    _t1312 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1312,))
    return sort(result)
end

function deconstruct_relation_id_string(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, String}
    name = relation_id_to_string(pp, msg)
    if name != ""
        return name
    end
    return nothing
end

function deconstruct_bindings(pp::PrettyPrinter, abs::Proto.Abstraction)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    n = length(abs.vars)
    return (abs.vars[0 + 1:n], Proto.Binding[],)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1313 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1313,))
    end
    if !isnothing(msg.compression)
        _t1314 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1314,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1315 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1315,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1316 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1316,))
    end
    if !isnothing(msg.syntax_delim)
        _t1317 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1317,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1318 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1318,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1319 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1319,))
    end
    return sort(result)
end

# --- Pretty-print functions ---

function pretty_transaction(pp::PrettyPrinter, msg::Proto.Transaction)
    function _t490(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t491 = _dollar_dollar.configure
        else
            _t491 = nothing
        end
        
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t492 = _dollar_dollar.sync
        else
            _t492 = nothing
        end
        return (_t491, _t492, _dollar_dollar.epochs,)
    end
    _t493 = _t490(msg)
    fields0 = _t493
    unwrapped_fields1 = fields0
    write(pp, "(")
    write(pp, "transaction")
    indent!(pp)
    field2 = unwrapped_fields1[1]
    
    if !isnothing(field2)
        newline(pp)
        opt_val3 = field2
        _t495 = pretty_configure(pp, opt_val3)
        _t494 = _t495
    else
        _t494 = nothing
    end
    field4 = unwrapped_fields1[2]
    
    if !isnothing(field4)
        newline(pp)
        opt_val5 = field4
        _t497 = pretty_sync(pp, opt_val5)
        _t496 = _t497
    else
        _t496 = nothing
    end
    field6 = unwrapped_fields1[3]
    if !isempty(field6)
        newline(pp)
        for (i498, elem7) in enumerate(field6)
            i8 = i498 - 1
            if (i8 > 0)
                newline(pp)
            end
            _t499 = pretty_epoch(pp, elem7)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    function _t500(_dollar_dollar)
        _t501 = deconstruct_configure(pp, _dollar_dollar)
        return _t501
    end
    _t502 = _t500(msg)
    fields9 = _t502
    unwrapped_fields10 = fields9
    write(pp, "(")
    write(pp, "configure")
    indent!(pp)
    newline(pp)
    _t503 = pretty_config_dict(pp, unwrapped_fields10)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    function _t504(_dollar_dollar)
        return _dollar_dollar
    end
    _t505 = _t504(msg)
    fields11 = _t505
    unwrapped_fields12 = fields11
    write(pp, "{")
    indent!(pp)
    if !isempty(unwrapped_fields12)
        write(pp, " ")
        for (i506, elem13) in enumerate(unwrapped_fields12)
            i14 = i506 - 1
            if (i14 > 0)
                newline(pp)
            end
            _t507 = pretty_config_key_value(pp, elem13)
        end
    end
    dedent!(pp)
    write(pp, "}")
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    function _t508(_dollar_dollar)
        return (_dollar_dollar[1], _dollar_dollar[2],)
    end
    _t509 = _t508(msg)
    fields15 = _t509
    unwrapped_fields16 = fields15
    write(pp, ":")
    field17 = unwrapped_fields16[1]
    write(pp, field17)
    write(pp, " ")
    field18 = unwrapped_fields16[2]
    _t510 = pretty_value(pp, field18)
    return _t510
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    function _t511(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t512 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t512 = nothing
        end
        return _t512
    end
    _t513 = _t511(msg)
    deconstruct_result29 = _t513
    
    if !isnothing(deconstruct_result29)
        _t515 = pretty_date(pp, deconstruct_result29)
        _t514 = _t515
    else
        function _t516(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t517 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t517 = nothing
            end
            return _t517
        end
        _t518 = _t516(msg)
        deconstruct_result28 = _t518
        
        if !isnothing(deconstruct_result28)
            _t520 = pretty_datetime(pp, deconstruct_result28)
            _t519 = _t520
        else
            function _t521(_dollar_dollar)
                
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t522 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t522 = nothing
                end
                return _t522
            end
            _t523 = _t521(msg)
            deconstruct_result27 = _t523
            
            if !isnothing(deconstruct_result27)
                write(pp, format_string_value(deconstruct_result27))
                _t524 = nothing
            else
                function _t525(_dollar_dollar)
                    
                    if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                        _t526 = _get_oneof_field(_dollar_dollar, :int_value)
                    else
                        _t526 = nothing
                    end
                    return _t526
                end
                _t527 = _t525(msg)
                deconstruct_result26 = _t527
                
                if !isnothing(deconstruct_result26)
                    write(pp, string(deconstruct_result26))
                    _t528 = nothing
                else
                    function _t529(_dollar_dollar)
                        
                        if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                            _t530 = _get_oneof_field(_dollar_dollar, :float_value)
                        else
                            _t530 = nothing
                        end
                        return _t530
                    end
                    _t531 = _t529(msg)
                    deconstruct_result25 = _t531
                    
                    if !isnothing(deconstruct_result25)
                        write(pp, format_float64(deconstruct_result25))
                        _t532 = nothing
                    else
                        function _t533(_dollar_dollar)
                            
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                _t534 = _get_oneof_field(_dollar_dollar, :uint128_value)
                            else
                                _t534 = nothing
                            end
                            return _t534
                        end
                        _t535 = _t533(msg)
                        deconstruct_result24 = _t535
                        
                        if !isnothing(deconstruct_result24)
                            write(pp, format_uint128(pp, deconstruct_result24))
                            _t536 = nothing
                        else
                            function _t537(_dollar_dollar)
                                
                                if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                    _t538 = _get_oneof_field(_dollar_dollar, :int128_value)
                                else
                                    _t538 = nothing
                                end
                                return _t538
                            end
                            _t539 = _t537(msg)
                            deconstruct_result23 = _t539
                            
                            if !isnothing(deconstruct_result23)
                                write(pp, format_int128(pp, deconstruct_result23))
                                _t540 = nothing
                            else
                                function _t541(_dollar_dollar)
                                    
                                    if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                        _t542 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                    else
                                        _t542 = nothing
                                    end
                                    return _t542
                                end
                                _t543 = _t541(msg)
                                deconstruct_result22 = _t543
                                
                                if !isnothing(deconstruct_result22)
                                    write(pp, format_decimal(pp, deconstruct_result22))
                                    _t544 = nothing
                                else
                                    function _t545(_dollar_dollar)
                                        
                                        if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                            _t546 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                        else
                                            _t546 = nothing
                                        end
                                        return _t546
                                    end
                                    _t547 = _t545(msg)
                                    deconstruct_result21 = _t547
                                    
                                    if !isnothing(deconstruct_result21)
                                        _t549 = pretty_boolean_value(pp, deconstruct_result21)
                                        _t548 = _t549
                                    else
                                        function _t550(_dollar_dollar)
                                            return _dollar_dollar
                                        end
                                        _t551 = _t550(msg)
                                        fields19 = _t551
                                        unwrapped_fields20 = fields19
                                        write(pp, "missing")
                                        _t548 = nothing
                                    end
                                    _t544 = _t548
                                end
                                _t540 = _t544
                            end
                            _t536 = _t540
                        end
                        _t532 = _t536
                    end
                    _t528 = _t532
                end
                _t524 = _t528
            end
            _t519 = _t524
        end
        _t514 = _t519
    end
    return _t514
end

function pretty_date(pp::PrettyPrinter, msg::Proto.DateValue)
    function _t552(_dollar_dollar)
        return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
    end
    _t553 = _t552(msg)
    fields30 = _t553
    unwrapped_fields31 = fields30
    write(pp, "(")
    write(pp, "date")
    indent!(pp)
    newline(pp)
    field32 = unwrapped_fields31[1]
    write(pp, string(field32))
    newline(pp)
    field33 = unwrapped_fields31[2]
    write(pp, string(field33))
    newline(pp)
    field34 = unwrapped_fields31[3]
    write(pp, string(field34))
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    function _t554(_dollar_dollar)
        return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
    end
    _t555 = _t554(msg)
    fields35 = _t555
    unwrapped_fields36 = fields35
    write(pp, "(")
    write(pp, "datetime")
    indent!(pp)
    newline(pp)
    field37 = unwrapped_fields36[1]
    write(pp, string(field37))
    newline(pp)
    field38 = unwrapped_fields36[2]
    write(pp, string(field38))
    newline(pp)
    field39 = unwrapped_fields36[3]
    write(pp, string(field39))
    newline(pp)
    field40 = unwrapped_fields36[4]
    write(pp, string(field40))
    newline(pp)
    field41 = unwrapped_fields36[5]
    write(pp, string(field41))
    newline(pp)
    field42 = unwrapped_fields36[6]
    write(pp, string(field42))
    field43 = unwrapped_fields36[7]
    if !isnothing(field43)
        newline(pp)
        opt_val44 = field43
        write(pp, string(opt_val44))
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    function _t556(_dollar_dollar)
        
        if _dollar_dollar
            _t557 = ()
        else
            _t557 = nothing
        end
        return _t557
    end
    _t558 = _t556(msg)
    deconstruct_result46 = _t558
    if !isnothing(deconstruct_result46)
        write(pp, "true")
    else
        function _t559(_dollar_dollar)
            
            if !_dollar_dollar
                _t560 = ()
            else
                _t560 = nothing
            end
            return _t560
        end
        _t561 = _t559(msg)
        deconstruct_result45 = _t561
        if !isnothing(deconstruct_result45)
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    function _t562(_dollar_dollar)
        return _dollar_dollar.fragments
    end
    _t563 = _t562(msg)
    fields47 = _t563
    unwrapped_fields48 = fields47
    write(pp, "(")
    write(pp, "sync")
    indent!(pp)
    if !isempty(unwrapped_fields48)
        newline(pp)
        for (i564, elem49) in enumerate(unwrapped_fields48)
            i50 = i564 - 1
            if (i50 > 0)
                newline(pp)
            end
            _t565 = pretty_fragment_id(pp, elem49)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    function _t566(_dollar_dollar)
        return fragment_id_to_string(pp, _dollar_dollar)
    end
    _t567 = _t566(msg)
    fields51 = _t567
    unwrapped_fields52 = fields51
    write(pp, ":")
    write(pp, unwrapped_fields52)
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    function _t568(_dollar_dollar)
        
        if !isempty(_dollar_dollar.writes)
            _t569 = _dollar_dollar.writes
        else
            _t569 = nothing
        end
        
        if !isempty(_dollar_dollar.reads)
            _t570 = _dollar_dollar.reads
        else
            _t570 = nothing
        end
        return (_t569, _t570,)
    end
    _t571 = _t568(msg)
    fields53 = _t571
    unwrapped_fields54 = fields53
    write(pp, "(")
    write(pp, "epoch")
    indent!(pp)
    field55 = unwrapped_fields54[1]
    
    if !isnothing(field55)
        newline(pp)
        opt_val56 = field55
        _t573 = pretty_epoch_writes(pp, opt_val56)
        _t572 = _t573
    else
        _t572 = nothing
    end
    field57 = unwrapped_fields54[2]
    
    if !isnothing(field57)
        newline(pp)
        opt_val58 = field57
        _t575 = pretty_epoch_reads(pp, opt_val58)
        _t574 = _t575
    else
        _t574 = nothing
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    function _t576(_dollar_dollar)
        return _dollar_dollar
    end
    _t577 = _t576(msg)
    fields59 = _t577
    unwrapped_fields60 = fields59
    write(pp, "(")
    write(pp, "writes")
    indent!(pp)
    if !isempty(unwrapped_fields60)
        newline(pp)
        for (i578, elem61) in enumerate(unwrapped_fields60)
            i62 = i578 - 1
            if (i62 > 0)
                newline(pp)
            end
            _t579 = pretty_write(pp, elem61)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    function _t580(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t581 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t581 = nothing
        end
        return _t581
    end
    _t582 = _t580(msg)
    deconstruct_result65 = _t582
    
    if !isnothing(deconstruct_result65)
        _t584 = pretty_define(pp, deconstruct_result65)
        _t583 = _t584
    else
        function _t585(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t586 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t586 = nothing
            end
            return _t586
        end
        _t587 = _t585(msg)
        deconstruct_result64 = _t587
        
        if !isnothing(deconstruct_result64)
            _t589 = pretty_undefine(pp, deconstruct_result64)
            _t588 = _t589
        else
            function _t590(_dollar_dollar)
                
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t591 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t591 = nothing
                end
                return _t591
            end
            _t592 = _t590(msg)
            deconstruct_result63 = _t592
            
            if !isnothing(deconstruct_result63)
                _t594 = pretty_context(pp, deconstruct_result63)
                _t593 = _t594
            else
                throw(ParseError("No matching rule for write"))
            end
            _t588 = _t593
        end
        _t583 = _t588
    end
    return _t583
end

function pretty_define(pp::PrettyPrinter, msg::Proto.Define)
    function _t595(_dollar_dollar)
        return _dollar_dollar.fragment
    end
    _t596 = _t595(msg)
    fields66 = _t596
    unwrapped_fields67 = fields66
    write(pp, "(")
    write(pp, "define")
    indent!(pp)
    newline(pp)
    _t597 = pretty_fragment(pp, unwrapped_fields67)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    function _t598(_dollar_dollar)
        start_pretty_fragment(pp, _dollar_dollar)
        return (_dollar_dollar.id, _dollar_dollar.declarations,)
    end
    _t599 = _t598(msg)
    fields68 = _t599
    unwrapped_fields69 = fields68
    write(pp, "(")
    write(pp, "fragment")
    indent!(pp)
    newline(pp)
    field70 = unwrapped_fields69[1]
    _t600 = pretty_new_fragment_id(pp, field70)
    field71 = unwrapped_fields69[2]
    if !isempty(field71)
        newline(pp)
        for (i601, elem72) in enumerate(field71)
            i73 = i601 - 1
            if (i73 > 0)
                newline(pp)
            end
            _t602 = pretty_declaration(pp, elem72)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    function _t603(_dollar_dollar)
        return _dollar_dollar
    end
    _t604 = _t603(msg)
    fields74 = _t604
    unwrapped_fields75 = fields74
    _t605 = pretty_fragment_id(pp, unwrapped_fields75)
    return _t605
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    function _t606(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t607 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t607 = nothing
        end
        return _t607
    end
    _t608 = _t606(msg)
    deconstruct_result79 = _t608
    
    if !isnothing(deconstruct_result79)
        _t610 = pretty_def(pp, deconstruct_result79)
        _t609 = _t610
    else
        function _t611(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t612 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t612 = nothing
            end
            return _t612
        end
        _t613 = _t611(msg)
        deconstruct_result78 = _t613
        
        if !isnothing(deconstruct_result78)
            _t615 = pretty_algorithm(pp, deconstruct_result78)
            _t614 = _t615
        else
            function _t616(_dollar_dollar)
                
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t617 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t617 = nothing
                end
                return _t617
            end
            _t618 = _t616(msg)
            deconstruct_result77 = _t618
            
            if !isnothing(deconstruct_result77)
                _t620 = pretty_constraint(pp, deconstruct_result77)
                _t619 = _t620
            else
                function _t621(_dollar_dollar)
                    
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t622 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t622 = nothing
                    end
                    return _t622
                end
                _t623 = _t621(msg)
                deconstruct_result76 = _t623
                
                if !isnothing(deconstruct_result76)
                    _t625 = pretty_data(pp, deconstruct_result76)
                    _t624 = _t625
                else
                    throw(ParseError("No matching rule for declaration"))
                end
                _t619 = _t624
            end
            _t614 = _t619
        end
        _t609 = _t614
    end
    return _t609
end

function pretty_def(pp::PrettyPrinter, msg::Proto.Def)
    function _t626(_dollar_dollar)
        
        if !isempty(_dollar_dollar.attrs)
            _t627 = _dollar_dollar.attrs
        else
            _t627 = nothing
        end
        return (_dollar_dollar.name, _dollar_dollar.body, _t627,)
    end
    _t628 = _t626(msg)
    fields80 = _t628
    unwrapped_fields81 = fields80
    write(pp, "(")
    write(pp, "def")
    indent!(pp)
    newline(pp)
    field82 = unwrapped_fields81[1]
    _t629 = pretty_relation_id(pp, field82)
    newline(pp)
    field83 = unwrapped_fields81[2]
    _t630 = pretty_abstraction(pp, field83)
    field84 = unwrapped_fields81[3]
    
    if !isnothing(field84)
        newline(pp)
        opt_val85 = field84
        _t632 = pretty_attrs(pp, opt_val85)
        _t631 = _t632
    else
        _t631 = nothing
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    function _t633(_dollar_dollar)
        _t634 = deconstruct_relation_id_string(pp, _dollar_dollar)
        return _t634
    end
    _t635 = _t633(msg)
    deconstruct_result87 = _t635
    if !isnothing(deconstruct_result87)
        write(pp, ":")
        write(pp, deconstruct_result87)
    else
        function _t636(_dollar_dollar)
            _t637 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            return _t637
        end
        _t638 = _t636(msg)
        deconstruct_result86 = _t638
        if !isnothing(deconstruct_result86)
            write(pp, format_uint128(pp, deconstruct_result86))
        else
            throw(ParseError("No matching rule for relation_id"))
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    function _t639(_dollar_dollar)
        _t640 = deconstruct_bindings(pp, _dollar_dollar)
        return (_t640, _dollar_dollar.value,)
    end
    _t641 = _t639(msg)
    fields88 = _t641
    unwrapped_fields89 = fields88
    write(pp, "(")
    field90 = unwrapped_fields89[1]
    _t642 = pretty_bindings(pp, field90)
    write(pp, " ")
    field91 = unwrapped_fields89[2]
    _t643 = pretty_formula(pp, field91)
    write(pp, ")")
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    function _t644(_dollar_dollar)
        
        if !isempty(_dollar_dollar[2])
            _t645 = _dollar_dollar[2]
        else
            _t645 = nothing
        end
        return (_dollar_dollar[1], _t645,)
    end
    _t646 = _t644(msg)
    fields92 = _t646
    unwrapped_fields93 = fields92
    write(pp, "[")
    field94 = unwrapped_fields93[1]
    for (i647, elem95) in enumerate(field94)
        i96 = i647 - 1
        if (i96 > 0)
            newline(pp)
        end
        _t648 = pretty_binding(pp, elem95)
    end
    field97 = unwrapped_fields93[2]
    
    if !isnothing(field97)
        write(pp, " ")
        opt_val98 = field97
        _t650 = pretty_value_bindings(pp, opt_val98)
        _t649 = _t650
    else
        _t649 = nothing
    end
    write(pp, "]")
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    function _t651(_dollar_dollar)
        return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
    end
    _t652 = _t651(msg)
    fields99 = _t652
    unwrapped_fields100 = fields99
    field101 = unwrapped_fields100[1]
    write(pp, field101)
    write(pp, "::")
    field102 = unwrapped_fields100[2]
    _t653 = pretty_type(pp, field102)
    return _t653
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    function _t654(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t655 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t655 = nothing
        end
        return _t655
    end
    _t656 = _t654(msg)
    deconstruct_result113 = _t656
    
    if !isnothing(deconstruct_result113)
        _t658 = pretty_unspecified_type(pp, deconstruct_result113)
        _t657 = _t658
    else
        function _t659(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t660 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t660 = nothing
            end
            return _t660
        end
        _t661 = _t659(msg)
        deconstruct_result112 = _t661
        
        if !isnothing(deconstruct_result112)
            _t663 = pretty_string_type(pp, deconstruct_result112)
            _t662 = _t663
        else
            function _t664(_dollar_dollar)
                
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t665 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t665 = nothing
                end
                return _t665
            end
            _t666 = _t664(msg)
            deconstruct_result111 = _t666
            
            if !isnothing(deconstruct_result111)
                _t668 = pretty_int_type(pp, deconstruct_result111)
                _t667 = _t668
            else
                function _t669(_dollar_dollar)
                    
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t670 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t670 = nothing
                    end
                    return _t670
                end
                _t671 = _t669(msg)
                deconstruct_result110 = _t671
                
                if !isnothing(deconstruct_result110)
                    _t673 = pretty_float_type(pp, deconstruct_result110)
                    _t672 = _t673
                else
                    function _t674(_dollar_dollar)
                        
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t675 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t675 = nothing
                        end
                        return _t675
                    end
                    _t676 = _t674(msg)
                    deconstruct_result109 = _t676
                    
                    if !isnothing(deconstruct_result109)
                        _t678 = pretty_uint128_type(pp, deconstruct_result109)
                        _t677 = _t678
                    else
                        function _t679(_dollar_dollar)
                            
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t680 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t680 = nothing
                            end
                            return _t680
                        end
                        _t681 = _t679(msg)
                        deconstruct_result108 = _t681
                        
                        if !isnothing(deconstruct_result108)
                            _t683 = pretty_int128_type(pp, deconstruct_result108)
                            _t682 = _t683
                        else
                            function _t684(_dollar_dollar)
                                
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t685 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t685 = nothing
                                end
                                return _t685
                            end
                            _t686 = _t684(msg)
                            deconstruct_result107 = _t686
                            
                            if !isnothing(deconstruct_result107)
                                _t688 = pretty_date_type(pp, deconstruct_result107)
                                _t687 = _t688
                            else
                                function _t689(_dollar_dollar)
                                    
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t690 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t690 = nothing
                                    end
                                    return _t690
                                end
                                _t691 = _t689(msg)
                                deconstruct_result106 = _t691
                                
                                if !isnothing(deconstruct_result106)
                                    _t693 = pretty_datetime_type(pp, deconstruct_result106)
                                    _t692 = _t693
                                else
                                    function _t694(_dollar_dollar)
                                        
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t695 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t695 = nothing
                                        end
                                        return _t695
                                    end
                                    _t696 = _t694(msg)
                                    deconstruct_result105 = _t696
                                    
                                    if !isnothing(deconstruct_result105)
                                        _t698 = pretty_missing_type(pp, deconstruct_result105)
                                        _t697 = _t698
                                    else
                                        function _t699(_dollar_dollar)
                                            
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t700 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t700 = nothing
                                            end
                                            return _t700
                                        end
                                        _t701 = _t699(msg)
                                        deconstruct_result104 = _t701
                                        
                                        if !isnothing(deconstruct_result104)
                                            _t703 = pretty_decimal_type(pp, deconstruct_result104)
                                            _t702 = _t703
                                        else
                                            function _t704(_dollar_dollar)
                                                
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t705 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t705 = nothing
                                                end
                                                return _t705
                                            end
                                            _t706 = _t704(msg)
                                            deconstruct_result103 = _t706
                                            
                                            if !isnothing(deconstruct_result103)
                                                _t708 = pretty_boolean_type(pp, deconstruct_result103)
                                                _t707 = _t708
                                            else
                                                throw(ParseError("No matching rule for type"))
                                            end
                                            _t702 = _t707
                                        end
                                        _t697 = _t702
                                    end
                                    _t692 = _t697
                                end
                                _t687 = _t692
                            end
                            _t682 = _t687
                        end
                        _t677 = _t682
                    end
                    _t672 = _t677
                end
                _t667 = _t672
            end
            _t662 = _t667
        end
        _t657 = _t662
    end
    return _t657
end

function pretty_unspecified_type(pp::PrettyPrinter, msg::Proto.UnspecifiedType)
    function _t709(_dollar_dollar)
        return _dollar_dollar
    end
    _t710 = _t709(msg)
    fields114 = _t710
    unwrapped_fields115 = fields114
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    function _t711(_dollar_dollar)
        return _dollar_dollar
    end
    _t712 = _t711(msg)
    fields116 = _t712
    unwrapped_fields117 = fields116
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    function _t713(_dollar_dollar)
        return _dollar_dollar
    end
    _t714 = _t713(msg)
    fields118 = _t714
    unwrapped_fields119 = fields118
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    function _t715(_dollar_dollar)
        return _dollar_dollar
    end
    _t716 = _t715(msg)
    fields120 = _t716
    unwrapped_fields121 = fields120
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    function _t717(_dollar_dollar)
        return _dollar_dollar
    end
    _t718 = _t717(msg)
    fields122 = _t718
    unwrapped_fields123 = fields122
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    function _t719(_dollar_dollar)
        return _dollar_dollar
    end
    _t720 = _t719(msg)
    fields124 = _t720
    unwrapped_fields125 = fields124
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    function _t721(_dollar_dollar)
        return _dollar_dollar
    end
    _t722 = _t721(msg)
    fields126 = _t722
    unwrapped_fields127 = fields126
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    function _t723(_dollar_dollar)
        return _dollar_dollar
    end
    _t724 = _t723(msg)
    fields128 = _t724
    unwrapped_fields129 = fields128
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    function _t725(_dollar_dollar)
        return _dollar_dollar
    end
    _t726 = _t725(msg)
    fields130 = _t726
    unwrapped_fields131 = fields130
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    function _t727(_dollar_dollar)
        return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
    end
    _t728 = _t727(msg)
    fields132 = _t728
    unwrapped_fields133 = fields132
    write(pp, "(")
    write(pp, "DECIMAL")
    indent!(pp)
    newline(pp)
    field134 = unwrapped_fields133[1]
    write(pp, string(field134))
    newline(pp)
    field135 = unwrapped_fields133[2]
    write(pp, string(field135))
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    function _t729(_dollar_dollar)
        return _dollar_dollar
    end
    _t730 = _t729(msg)
    fields136 = _t730
    unwrapped_fields137 = fields136
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    function _t731(_dollar_dollar)
        return _dollar_dollar
    end
    _t732 = _t731(msg)
    fields138 = _t732
    unwrapped_fields139 = fields138
    write(pp, "|")
    if !isempty(unwrapped_fields139)
        write(pp, " ")
        for (i733, elem140) in enumerate(unwrapped_fields139)
            i141 = i733 - 1
            if (i141 > 0)
                newline(pp)
            end
            _t734 = pretty_binding(pp, elem140)
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    function _t735(_dollar_dollar)
        
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t736 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t736 = nothing
        end
        return _t736
    end
    _t737 = _t735(msg)
    deconstruct_result154 = _t737
    
    if !isnothing(deconstruct_result154)
        _t739 = pretty_true(pp, deconstruct_result154)
        _t738 = _t739
    else
        function _t740(_dollar_dollar)
            
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t741 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t741 = nothing
            end
            return _t741
        end
        _t742 = _t740(msg)
        deconstruct_result153 = _t742
        
        if !isnothing(deconstruct_result153)
            _t744 = pretty_false(pp, deconstruct_result153)
            _t743 = _t744
        else
            function _t745(_dollar_dollar)
                
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t746 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t746 = nothing
                end
                return _t746
            end
            _t747 = _t745(msg)
            deconstruct_result152 = _t747
            
            if !isnothing(deconstruct_result152)
                _t749 = pretty_exists(pp, deconstruct_result152)
                _t748 = _t749
            else
                function _t750(_dollar_dollar)
                    
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t751 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t751 = nothing
                    end
                    return _t751
                end
                _t752 = _t750(msg)
                deconstruct_result151 = _t752
                
                if !isnothing(deconstruct_result151)
                    _t754 = pretty_reduce(pp, deconstruct_result151)
                    _t753 = _t754
                else
                    function _t755(_dollar_dollar)
                        
                        if _has_proto_field(_dollar_dollar, Symbol("conjunction"))
                            _t756 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t756 = nothing
                        end
                        return _t756
                    end
                    _t757 = _t755(msg)
                    deconstruct_result150 = _t757
                    
                    if !isnothing(deconstruct_result150)
                        _t759 = pretty_conjunction(pp, deconstruct_result150)
                        _t758 = _t759
                    else
                        function _t760(_dollar_dollar)
                            
                            if _has_proto_field(_dollar_dollar, Symbol("disjunction"))
                                _t761 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t761 = nothing
                            end
                            return _t761
                        end
                        _t762 = _t760(msg)
                        deconstruct_result149 = _t762
                        
                        if !isnothing(deconstruct_result149)
                            _t764 = pretty_disjunction(pp, deconstruct_result149)
                            _t763 = _t764
                        else
                            function _t765(_dollar_dollar)
                                
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t766 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t766 = nothing
                                end
                                return _t766
                            end
                            _t767 = _t765(msg)
                            deconstruct_result148 = _t767
                            
                            if !isnothing(deconstruct_result148)
                                _t769 = pretty_not(pp, deconstruct_result148)
                                _t768 = _t769
                            else
                                function _t770(_dollar_dollar)
                                    
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t771 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t771 = nothing
                                    end
                                    return _t771
                                end
                                _t772 = _t770(msg)
                                deconstruct_result147 = _t772
                                
                                if !isnothing(deconstruct_result147)
                                    _t774 = pretty_ffi(pp, deconstruct_result147)
                                    _t773 = _t774
                                else
                                    function _t775(_dollar_dollar)
                                        
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t776 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t776 = nothing
                                        end
                                        return _t776
                                    end
                                    _t777 = _t775(msg)
                                    deconstruct_result146 = _t777
                                    
                                    if !isnothing(deconstruct_result146)
                                        _t779 = pretty_atom(pp, deconstruct_result146)
                                        _t778 = _t779
                                    else
                                        function _t780(_dollar_dollar)
                                            
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t781 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t781 = nothing
                                            end
                                            return _t781
                                        end
                                        _t782 = _t780(msg)
                                        deconstruct_result145 = _t782
                                        
                                        if !isnothing(deconstruct_result145)
                                            _t784 = pretty_pragma(pp, deconstruct_result145)
                                            _t783 = _t784
                                        else
                                            function _t785(_dollar_dollar)
                                                
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t786 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t786 = nothing
                                                end
                                                return _t786
                                            end
                                            _t787 = _t785(msg)
                                            deconstruct_result144 = _t787
                                            
                                            if !isnothing(deconstruct_result144)
                                                _t789 = pretty_primitive(pp, deconstruct_result144)
                                                _t788 = _t789
                                            else
                                                function _t790(_dollar_dollar)
                                                    
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t791 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t791 = nothing
                                                    end
                                                    return _t791
                                                end
                                                _t792 = _t790(msg)
                                                deconstruct_result143 = _t792
                                                
                                                if !isnothing(deconstruct_result143)
                                                    _t794 = pretty_rel_atom(pp, deconstruct_result143)
                                                    _t793 = _t794
                                                else
                                                    function _t795(_dollar_dollar)
                                                        
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t796 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t796 = nothing
                                                        end
                                                        return _t796
                                                    end
                                                    _t797 = _t795(msg)
                                                    deconstruct_result142 = _t797
                                                    
                                                    if !isnothing(deconstruct_result142)
                                                        _t799 = pretty_cast(pp, deconstruct_result142)
                                                        _t798 = _t799
                                                    else
                                                        throw(ParseError("No matching rule for formula"))
                                                    end
                                                    _t793 = _t798
                                                end
                                                _t788 = _t793
                                            end
                                            _t783 = _t788
                                        end
                                        _t778 = _t783
                                    end
                                    _t773 = _t778
                                end
                                _t768 = _t773
                            end
                            _t763 = _t768
                        end
                        _t758 = _t763
                    end
                    _t753 = _t758
                end
                _t748 = _t753
            end
            _t743 = _t748
        end
        _t738 = _t743
    end
    return _t738
end

function pretty_true(pp::PrettyPrinter, msg::Proto.Conjunction)
    function _t800(_dollar_dollar)
        return _dollar_dollar
    end
    _t801 = _t800(msg)
    fields155 = _t801
    unwrapped_fields156 = fields155
    write(pp, "(")
    write(pp, "true")
    write(pp, ")")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    function _t802(_dollar_dollar)
        return _dollar_dollar
    end
    _t803 = _t802(msg)
    fields157 = _t803
    unwrapped_fields158 = fields157
    write(pp, "(")
    write(pp, "false")
    write(pp, ")")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    function _t804(_dollar_dollar)
        _t805 = deconstruct_bindings(pp, _dollar_dollar.body)
        return (_t805, _dollar_dollar.body.value,)
    end
    _t806 = _t804(msg)
    fields159 = _t806
    unwrapped_fields160 = fields159
    write(pp, "(")
    write(pp, "exists")
    indent!(pp)
    newline(pp)
    field161 = unwrapped_fields160[1]
    _t807 = pretty_bindings(pp, field161)
    newline(pp)
    field162 = unwrapped_fields160[2]
    _t808 = pretty_formula(pp, field162)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    function _t809(_dollar_dollar)
        return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
    end
    _t810 = _t809(msg)
    fields163 = _t810
    unwrapped_fields164 = fields163
    write(pp, "(")
    write(pp, "reduce")
    indent!(pp)
    newline(pp)
    field165 = unwrapped_fields164[1]
    _t811 = pretty_abstraction(pp, field165)
    newline(pp)
    field166 = unwrapped_fields164[2]
    _t812 = pretty_abstraction(pp, field166)
    newline(pp)
    field167 = unwrapped_fields164[3]
    _t813 = pretty_terms(pp, field167)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    function _t814(_dollar_dollar)
        return _dollar_dollar
    end
    _t815 = _t814(msg)
    fields168 = _t815
    unwrapped_fields169 = fields168
    write(pp, "(")
    write(pp, "terms")
    indent!(pp)
    if !isempty(unwrapped_fields169)
        newline(pp)
        for (i816, elem170) in enumerate(unwrapped_fields169)
            i171 = i816 - 1
            if (i171 > 0)
                newline(pp)
            end
            _t817 = pretty_term(pp, elem170)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    function _t818(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t819 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t819 = nothing
        end
        return _t819
    end
    _t820 = _t818(msg)
    deconstruct_result173 = _t820
    
    if !isnothing(deconstruct_result173)
        _t822 = pretty_var(pp, deconstruct_result173)
        _t821 = _t822
    else
        function _t823(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t824 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t824 = nothing
            end
            return _t824
        end
        _t825 = _t823(msg)
        deconstruct_result172 = _t825
        
        if !isnothing(deconstruct_result172)
            _t827 = pretty_constant(pp, deconstruct_result172)
            _t826 = _t827
        else
            throw(ParseError("No matching rule for term"))
        end
        _t821 = _t826
    end
    return _t821
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    function _t828(_dollar_dollar)
        return _dollar_dollar.name
    end
    _t829 = _t828(msg)
    fields174 = _t829
    unwrapped_fields175 = fields174
    write(pp, unwrapped_fields175)
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    function _t830(_dollar_dollar)
        return _dollar_dollar
    end
    _t831 = _t830(msg)
    fields176 = _t831
    unwrapped_fields177 = fields176
    _t832 = pretty_value(pp, unwrapped_fields177)
    return _t832
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    function _t833(_dollar_dollar)
        return _dollar_dollar.args
    end
    _t834 = _t833(msg)
    fields178 = _t834
    unwrapped_fields179 = fields178
    write(pp, "(")
    write(pp, "and")
    indent!(pp)
    if !isempty(unwrapped_fields179)
        newline(pp)
        for (i835, elem180) in enumerate(unwrapped_fields179)
            i181 = i835 - 1
            if (i181 > 0)
                newline(pp)
            end
            _t836 = pretty_formula(pp, elem180)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    function _t837(_dollar_dollar)
        return _dollar_dollar.args
    end
    _t838 = _t837(msg)
    fields182 = _t838
    unwrapped_fields183 = fields182
    write(pp, "(")
    write(pp, "or")
    indent!(pp)
    if !isempty(unwrapped_fields183)
        newline(pp)
        for (i839, elem184) in enumerate(unwrapped_fields183)
            i185 = i839 - 1
            if (i185 > 0)
                newline(pp)
            end
            _t840 = pretty_formula(pp, elem184)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    function _t841(_dollar_dollar)
        return _dollar_dollar.arg
    end
    _t842 = _t841(msg)
    fields186 = _t842
    unwrapped_fields187 = fields186
    write(pp, "(")
    write(pp, "not")
    indent!(pp)
    newline(pp)
    _t843 = pretty_formula(pp, unwrapped_fields187)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    function _t844(_dollar_dollar)
        return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
    end
    _t845 = _t844(msg)
    fields188 = _t845
    unwrapped_fields189 = fields188
    write(pp, "(")
    write(pp, "ffi")
    indent!(pp)
    newline(pp)
    field190 = unwrapped_fields189[1]
    _t846 = pretty_name(pp, field190)
    newline(pp)
    field191 = unwrapped_fields189[2]
    _t847 = pretty_ffi_args(pp, field191)
    newline(pp)
    field192 = unwrapped_fields189[3]
    _t848 = pretty_terms(pp, field192)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    function _t849(_dollar_dollar)
        return _dollar_dollar
    end
    _t850 = _t849(msg)
    fields193 = _t850
    unwrapped_fields194 = fields193
    write(pp, ":")
    write(pp, unwrapped_fields194)
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    function _t851(_dollar_dollar)
        return _dollar_dollar
    end
    _t852 = _t851(msg)
    fields195 = _t852
    unwrapped_fields196 = fields195
    write(pp, "(")
    write(pp, "args")
    indent!(pp)
    if !isempty(unwrapped_fields196)
        newline(pp)
        for (i853, elem197) in enumerate(unwrapped_fields196)
            i198 = i853 - 1
            if (i198 > 0)
                newline(pp)
            end
            _t854 = pretty_abstraction(pp, elem197)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    function _t855(_dollar_dollar)
        return (_dollar_dollar.name, _dollar_dollar.terms,)
    end
    _t856 = _t855(msg)
    fields199 = _t856
    unwrapped_fields200 = fields199
    write(pp, "(")
    write(pp, "atom")
    indent!(pp)
    newline(pp)
    field201 = unwrapped_fields200[1]
    _t857 = pretty_relation_id(pp, field201)
    field202 = unwrapped_fields200[2]
    if !isempty(field202)
        newline(pp)
        for (i858, elem203) in enumerate(field202)
            i204 = i858 - 1
            if (i204 > 0)
                newline(pp)
            end
            _t859 = pretty_term(pp, elem203)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    function _t860(_dollar_dollar)
        return (_dollar_dollar.name, _dollar_dollar.terms,)
    end
    _t861 = _t860(msg)
    fields205 = _t861
    unwrapped_fields206 = fields205
    write(pp, "(")
    write(pp, "pragma")
    indent!(pp)
    newline(pp)
    field207 = unwrapped_fields206[1]
    _t862 = pretty_name(pp, field207)
    field208 = unwrapped_fields206[2]
    if !isempty(field208)
        newline(pp)
        for (i863, elem209) in enumerate(field208)
            i210 = i863 - 1
            if (i210 > 0)
                newline(pp)
            end
            _t864 = pretty_term(pp, elem209)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t865(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_eq"
            _t866 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t866 = nothing
        end
        return _t866
    end
    _t867 = _t865(msg)
    guard_result225 = _t867
    
    if !isnothing(guard_result225)
        _t869 = pretty_eq(pp, msg)
        _t868 = _t869
    else
        function _t870(_dollar_dollar)
            
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t871 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t871 = nothing
            end
            return _t871
        end
        _t872 = _t870(msg)
        guard_result224 = _t872
        
        if !isnothing(guard_result224)
            _t874 = pretty_lt(pp, msg)
            _t873 = _t874
        else
            function _t875(_dollar_dollar)
                
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t876 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t876 = nothing
                end
                return _t876
            end
            _t877 = _t875(msg)
            guard_result223 = _t877
            
            if !isnothing(guard_result223)
                _t879 = pretty_lt_eq(pp, msg)
                _t878 = _t879
            else
                function _t880(_dollar_dollar)
                    
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t881 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t881 = nothing
                    end
                    return _t881
                end
                _t882 = _t880(msg)
                guard_result222 = _t882
                
                if !isnothing(guard_result222)
                    _t884 = pretty_gt(pp, msg)
                    _t883 = _t884
                else
                    function _t885(_dollar_dollar)
                        
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t886 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t886 = nothing
                        end
                        return _t886
                    end
                    _t887 = _t885(msg)
                    guard_result221 = _t887
                    
                    if !isnothing(guard_result221)
                        _t889 = pretty_gt_eq(pp, msg)
                        _t888 = _t889
                    else
                        function _t890(_dollar_dollar)
                            
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t891 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t891 = nothing
                            end
                            return _t891
                        end
                        _t892 = _t890(msg)
                        guard_result220 = _t892
                        
                        if !isnothing(guard_result220)
                            _t894 = pretty_add(pp, msg)
                            _t893 = _t894
                        else
                            function _t895(_dollar_dollar)
                                
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t896 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t896 = nothing
                                end
                                return _t896
                            end
                            _t897 = _t895(msg)
                            guard_result219 = _t897
                            
                            if !isnothing(guard_result219)
                                _t899 = pretty_minus(pp, msg)
                                _t898 = _t899
                            else
                                function _t900(_dollar_dollar)
                                    
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t901 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t901 = nothing
                                    end
                                    return _t901
                                end
                                _t902 = _t900(msg)
                                guard_result218 = _t902
                                
                                if !isnothing(guard_result218)
                                    _t904 = pretty_multiply(pp, msg)
                                    _t903 = _t904
                                else
                                    function _t905(_dollar_dollar)
                                        
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t906 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t906 = nothing
                                        end
                                        return _t906
                                    end
                                    _t907 = _t905(msg)
                                    guard_result217 = _t907
                                    
                                    if !isnothing(guard_result217)
                                        _t909 = pretty_divide(pp, msg)
                                        _t908 = _t909
                                    else
                                        function _t910(_dollar_dollar)
                                            return (_dollar_dollar.name, _dollar_dollar.terms,)
                                        end
                                        _t911 = _t910(msg)
                                        fields211 = _t911
                                        unwrapped_fields212 = fields211
                                        write(pp, "(")
                                        write(pp, "primitive")
                                        indent!(pp)
                                        newline(pp)
                                        field213 = unwrapped_fields212[1]
                                        _t912 = pretty_name(pp, field213)
                                        field214 = unwrapped_fields212[2]
                                        if !isempty(field214)
                                            newline(pp)
                                            for (i913, elem215) in enumerate(field214)
                                                i216 = i913 - 1
                                                if (i216 > 0)
                                                    newline(pp)
                                                end
                                                _t914 = pretty_rel_term(pp, elem215)
                                            end
                                        end
                                        dedent!(pp)
                                        write(pp, ")")
                                        _t908 = nothing
                                    end
                                    _t903 = _t908
                                end
                                _t898 = _t903
                            end
                            _t893 = _t898
                        end
                        _t888 = _t893
                    end
                    _t883 = _t888
                end
                _t878 = _t883
            end
            _t873 = _t878
        end
        _t868 = _t873
    end
    return _t868
end

function pretty_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t915(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_eq"
            _t916 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t916 = nothing
        end
        return _t916
    end
    _t917 = _t915(msg)
    fields226 = _t917
    unwrapped_fields227 = fields226
    write(pp, "(")
    write(pp, "=")
    indent!(pp)
    newline(pp)
    field228 = unwrapped_fields227[1]
    _t918 = pretty_term(pp, field228)
    newline(pp)
    field229 = unwrapped_fields227[2]
    _t919 = pretty_term(pp, field229)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t920(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t921 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t921 = nothing
        end
        return _t921
    end
    _t922 = _t920(msg)
    fields230 = _t922
    unwrapped_fields231 = fields230
    write(pp, "(")
    write(pp, "<")
    indent!(pp)
    newline(pp)
    field232 = unwrapped_fields231[1]
    _t923 = pretty_term(pp, field232)
    newline(pp)
    field233 = unwrapped_fields231[2]
    _t924 = pretty_term(pp, field233)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t925(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t926 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t926 = nothing
        end
        return _t926
    end
    _t927 = _t925(msg)
    fields234 = _t927
    unwrapped_fields235 = fields234
    write(pp, "(")
    write(pp, "<=")
    indent!(pp)
    newline(pp)
    field236 = unwrapped_fields235[1]
    _t928 = pretty_term(pp, field236)
    newline(pp)
    field237 = unwrapped_fields235[2]
    _t929 = pretty_term(pp, field237)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t930(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t931 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t931 = nothing
        end
        return _t931
    end
    _t932 = _t930(msg)
    fields238 = _t932
    unwrapped_fields239 = fields238
    write(pp, "(")
    write(pp, ">")
    indent!(pp)
    newline(pp)
    field240 = unwrapped_fields239[1]
    _t933 = pretty_term(pp, field240)
    newline(pp)
    field241 = unwrapped_fields239[2]
    _t934 = pretty_term(pp, field241)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t935(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t936 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t936 = nothing
        end
        return _t936
    end
    _t937 = _t935(msg)
    fields242 = _t937
    unwrapped_fields243 = fields242
    write(pp, "(")
    write(pp, ">=")
    indent!(pp)
    newline(pp)
    field244 = unwrapped_fields243[1]
    _t938 = pretty_term(pp, field244)
    newline(pp)
    field245 = unwrapped_fields243[2]
    _t939 = pretty_term(pp, field245)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t940(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t941 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t941 = nothing
        end
        return _t941
    end
    _t942 = _t940(msg)
    fields246 = _t942
    unwrapped_fields247 = fields246
    write(pp, "(")
    write(pp, "+")
    indent!(pp)
    newline(pp)
    field248 = unwrapped_fields247[1]
    _t943 = pretty_term(pp, field248)
    newline(pp)
    field249 = unwrapped_fields247[2]
    _t944 = pretty_term(pp, field249)
    newline(pp)
    field250 = unwrapped_fields247[3]
    _t945 = pretty_term(pp, field250)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t946(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t947 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t947 = nothing
        end
        return _t947
    end
    _t948 = _t946(msg)
    fields251 = _t948
    unwrapped_fields252 = fields251
    write(pp, "(")
    write(pp, "-")
    indent!(pp)
    newline(pp)
    field253 = unwrapped_fields252[1]
    _t949 = pretty_term(pp, field253)
    newline(pp)
    field254 = unwrapped_fields252[2]
    _t950 = pretty_term(pp, field254)
    newline(pp)
    field255 = unwrapped_fields252[3]
    _t951 = pretty_term(pp, field255)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t952(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t953 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t953 = nothing
        end
        return _t953
    end
    _t954 = _t952(msg)
    fields256 = _t954
    unwrapped_fields257 = fields256
    write(pp, "(")
    write(pp, "*")
    indent!(pp)
    newline(pp)
    field258 = unwrapped_fields257[1]
    _t955 = pretty_term(pp, field258)
    newline(pp)
    field259 = unwrapped_fields257[2]
    _t956 = pretty_term(pp, field259)
    newline(pp)
    field260 = unwrapped_fields257[3]
    _t957 = pretty_term(pp, field260)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    function _t958(_dollar_dollar)
        
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t959 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t959 = nothing
        end
        return _t959
    end
    _t960 = _t958(msg)
    fields261 = _t960
    unwrapped_fields262 = fields261
    write(pp, "(")
    write(pp, "/")
    indent!(pp)
    newline(pp)
    field263 = unwrapped_fields262[1]
    _t961 = pretty_term(pp, field263)
    newline(pp)
    field264 = unwrapped_fields262[2]
    _t962 = pretty_term(pp, field264)
    newline(pp)
    field265 = unwrapped_fields262[3]
    _t963 = pretty_term(pp, field265)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    function _t964(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t965 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t965 = nothing
        end
        return _t965
    end
    _t966 = _t964(msg)
    deconstruct_result267 = _t966
    
    if !isnothing(deconstruct_result267)
        _t968 = pretty_specialized_value(pp, deconstruct_result267)
        _t967 = _t968
    else
        function _t969(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t970 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t970 = nothing
            end
            return _t970
        end
        _t971 = _t969(msg)
        deconstruct_result266 = _t971
        
        if !isnothing(deconstruct_result266)
            _t973 = pretty_term(pp, deconstruct_result266)
            _t972 = _t973
        else
            throw(ParseError("No matching rule for rel_term"))
        end
        _t967 = _t972
    end
    return _t967
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    function _t974(_dollar_dollar)
        return _dollar_dollar
    end
    _t975 = _t974(msg)
    fields268 = _t975
    unwrapped_fields269 = fields268
    write(pp, "#")
    _t976 = pretty_value(pp, unwrapped_fields269)
    return _t976
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    function _t977(_dollar_dollar)
        return (_dollar_dollar.name, _dollar_dollar.terms,)
    end
    _t978 = _t977(msg)
    fields270 = _t978
    unwrapped_fields271 = fields270
    write(pp, "(")
    write(pp, "relatom")
    indent!(pp)
    newline(pp)
    field272 = unwrapped_fields271[1]
    _t979 = pretty_name(pp, field272)
    field273 = unwrapped_fields271[2]
    if !isempty(field273)
        newline(pp)
        for (i980, elem274) in enumerate(field273)
            i275 = i980 - 1
            if (i275 > 0)
                newline(pp)
            end
            _t981 = pretty_rel_term(pp, elem274)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    function _t982(_dollar_dollar)
        return (_dollar_dollar.input, _dollar_dollar.result,)
    end
    _t983 = _t982(msg)
    fields276 = _t983
    unwrapped_fields277 = fields276
    write(pp, "(")
    write(pp, "cast")
    indent!(pp)
    newline(pp)
    field278 = unwrapped_fields277[1]
    _t984 = pretty_term(pp, field278)
    newline(pp)
    field279 = unwrapped_fields277[2]
    _t985 = pretty_term(pp, field279)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    function _t986(_dollar_dollar)
        return _dollar_dollar
    end
    _t987 = _t986(msg)
    fields280 = _t987
    unwrapped_fields281 = fields280
    write(pp, "(")
    write(pp, "attrs")
    indent!(pp)
    if !isempty(unwrapped_fields281)
        newline(pp)
        for (i988, elem282) in enumerate(unwrapped_fields281)
            i283 = i988 - 1
            if (i283 > 0)
                newline(pp)
            end
            _t989 = pretty_attribute(pp, elem282)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    function _t990(_dollar_dollar)
        return (_dollar_dollar.name, _dollar_dollar.args,)
    end
    _t991 = _t990(msg)
    fields284 = _t991
    unwrapped_fields285 = fields284
    write(pp, "(")
    write(pp, "attribute")
    indent!(pp)
    newline(pp)
    field286 = unwrapped_fields285[1]
    _t992 = pretty_name(pp, field286)
    field287 = unwrapped_fields285[2]
    if !isempty(field287)
        newline(pp)
        for (i993, elem288) in enumerate(field287)
            i289 = i993 - 1
            if (i289 > 0)
                newline(pp)
            end
            _t994 = pretty_value(pp, elem288)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    function _t995(_dollar_dollar)
        return (_dollar_dollar.var"#global", _dollar_dollar.body,)
    end
    _t996 = _t995(msg)
    fields290 = _t996
    unwrapped_fields291 = fields290
    write(pp, "(")
    write(pp, "algorithm")
    indent!(pp)
    field292 = unwrapped_fields291[1]
    if !isempty(field292)
        newline(pp)
        for (i997, elem293) in enumerate(field292)
            i294 = i997 - 1
            if (i294 > 0)
                newline(pp)
            end
            _t998 = pretty_relation_id(pp, elem293)
        end
    end
    newline(pp)
    field295 = unwrapped_fields291[2]
    _t999 = pretty_script(pp, field295)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    function _t1000(_dollar_dollar)
        return _dollar_dollar.constructs
    end
    _t1001 = _t1000(msg)
    fields296 = _t1001
    unwrapped_fields297 = fields296
    write(pp, "(")
    write(pp, "script")
    indent!(pp)
    if !isempty(unwrapped_fields297)
        newline(pp)
        for (i1002, elem298) in enumerate(unwrapped_fields297)
            i299 = i1002 - 1
            if (i299 > 0)
                newline(pp)
            end
            _t1003 = pretty_construct(pp, elem298)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    function _t1004(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1005 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1005 = nothing
        end
        return _t1005
    end
    _t1006 = _t1004(msg)
    deconstruct_result301 = _t1006
    
    if !isnothing(deconstruct_result301)
        _t1008 = pretty_loop(pp, deconstruct_result301)
        _t1007 = _t1008
    else
        function _t1009(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1010 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1010 = nothing
            end
            return _t1010
        end
        _t1011 = _t1009(msg)
        deconstruct_result300 = _t1011
        
        if !isnothing(deconstruct_result300)
            _t1013 = pretty_instruction(pp, deconstruct_result300)
            _t1012 = _t1013
        else
            throw(ParseError("No matching rule for construct"))
        end
        _t1007 = _t1012
    end
    return _t1007
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    function _t1014(_dollar_dollar)
        return (_dollar_dollar.init, _dollar_dollar.body,)
    end
    _t1015 = _t1014(msg)
    fields302 = _t1015
    unwrapped_fields303 = fields302
    write(pp, "(")
    write(pp, "loop")
    indent!(pp)
    newline(pp)
    field304 = unwrapped_fields303[1]
    _t1016 = pretty_init(pp, field304)
    newline(pp)
    field305 = unwrapped_fields303[2]
    _t1017 = pretty_script(pp, field305)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    function _t1018(_dollar_dollar)
        return _dollar_dollar
    end
    _t1019 = _t1018(msg)
    fields306 = _t1019
    unwrapped_fields307 = fields306
    write(pp, "(")
    write(pp, "init")
    indent!(pp)
    if !isempty(unwrapped_fields307)
        newline(pp)
        for (i1020, elem308) in enumerate(unwrapped_fields307)
            i309 = i1020 - 1
            if (i309 > 0)
                newline(pp)
            end
            _t1021 = pretty_instruction(pp, elem308)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    function _t1022(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1023 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1023 = nothing
        end
        return _t1023
    end
    _t1024 = _t1022(msg)
    deconstruct_result314 = _t1024
    
    if !isnothing(deconstruct_result314)
        _t1026 = pretty_assign(pp, deconstruct_result314)
        _t1025 = _t1026
    else
        function _t1027(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1028 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1028 = nothing
            end
            return _t1028
        end
        _t1029 = _t1027(msg)
        deconstruct_result313 = _t1029
        
        if !isnothing(deconstruct_result313)
            _t1031 = pretty_upsert(pp, deconstruct_result313)
            _t1030 = _t1031
        else
            function _t1032(_dollar_dollar)
                
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1033 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1033 = nothing
                end
                return _t1033
            end
            _t1034 = _t1032(msg)
            deconstruct_result312 = _t1034
            
            if !isnothing(deconstruct_result312)
                _t1036 = pretty_break(pp, deconstruct_result312)
                _t1035 = _t1036
            else
                function _t1037(_dollar_dollar)
                    
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1038 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1038 = nothing
                    end
                    return _t1038
                end
                _t1039 = _t1037(msg)
                deconstruct_result311 = _t1039
                
                if !isnothing(deconstruct_result311)
                    _t1041 = pretty_monoid_def(pp, deconstruct_result311)
                    _t1040 = _t1041
                else
                    function _t1042(_dollar_dollar)
                        
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1043 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1043 = nothing
                        end
                        return _t1043
                    end
                    _t1044 = _t1042(msg)
                    deconstruct_result310 = _t1044
                    
                    if !isnothing(deconstruct_result310)
                        _t1046 = pretty_monus_def(pp, deconstruct_result310)
                        _t1045 = _t1046
                    else
                        throw(ParseError("No matching rule for instruction"))
                    end
                    _t1040 = _t1045
                end
                _t1035 = _t1040
            end
            _t1030 = _t1035
        end
        _t1025 = _t1030
    end
    return _t1025
end

function pretty_assign(pp::PrettyPrinter, msg::Proto.Assign)
    function _t1047(_dollar_dollar)
        
        if !isempty(_dollar_dollar.attrs)
            _t1048 = _dollar_dollar.attrs
        else
            _t1048 = nothing
        end
        return (_dollar_dollar.name, _dollar_dollar.body, _t1048,)
    end
    _t1049 = _t1047(msg)
    fields315 = _t1049
    unwrapped_fields316 = fields315
    write(pp, "(")
    write(pp, "assign")
    indent!(pp)
    newline(pp)
    field317 = unwrapped_fields316[1]
    _t1050 = pretty_relation_id(pp, field317)
    newline(pp)
    field318 = unwrapped_fields316[2]
    _t1051 = pretty_abstraction(pp, field318)
    field319 = unwrapped_fields316[3]
    
    if !isnothing(field319)
        newline(pp)
        opt_val320 = field319
        _t1053 = pretty_attrs(pp, opt_val320)
        _t1052 = _t1053
    else
        _t1052 = nothing
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    function _t1054(_dollar_dollar)
        
        if !isempty(_dollar_dollar.attrs)
            _t1055 = _dollar_dollar.attrs
        else
            _t1055 = nothing
        end
        return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1055,)
    end
    _t1056 = _t1054(msg)
    fields321 = _t1056
    unwrapped_fields322 = fields321
    write(pp, "(")
    write(pp, "upsert")
    indent!(pp)
    newline(pp)
    field323 = unwrapped_fields322[1]
    _t1057 = pretty_relation_id(pp, field323)
    newline(pp)
    field324 = unwrapped_fields322[2]
    _t1058 = pretty_abstraction_with_arity(pp, field324)
    field325 = unwrapped_fields322[3]
    
    if !isnothing(field325)
        newline(pp)
        opt_val326 = field325
        _t1060 = pretty_attrs(pp, opt_val326)
        _t1059 = _t1060
    else
        _t1059 = nothing
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    function _t1061(_dollar_dollar)
        _t1062 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        return (_t1062, _dollar_dollar[1].value,)
    end
    _t1063 = _t1061(msg)
    fields327 = _t1063
    unwrapped_fields328 = fields327
    write(pp, "(")
    field329 = unwrapped_fields328[1]
    _t1064 = pretty_bindings(pp, field329)
    write(pp, " ")
    field330 = unwrapped_fields328[2]
    _t1065 = pretty_formula(pp, field330)
    write(pp, ")")
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    function _t1066(_dollar_dollar)
        
        if !isempty(_dollar_dollar.attrs)
            _t1067 = _dollar_dollar.attrs
        else
            _t1067 = nothing
        end
        return (_dollar_dollar.name, _dollar_dollar.body, _t1067,)
    end
    _t1068 = _t1066(msg)
    fields331 = _t1068
    unwrapped_fields332 = fields331
    write(pp, "(")
    write(pp, "break")
    indent!(pp)
    newline(pp)
    field333 = unwrapped_fields332[1]
    _t1069 = pretty_relation_id(pp, field333)
    newline(pp)
    field334 = unwrapped_fields332[2]
    _t1070 = pretty_abstraction(pp, field334)
    field335 = unwrapped_fields332[3]
    
    if !isnothing(field335)
        newline(pp)
        opt_val336 = field335
        _t1072 = pretty_attrs(pp, opt_val336)
        _t1071 = _t1072
    else
        _t1071 = nothing
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    function _t1073(_dollar_dollar)
        
        if !isempty(_dollar_dollar.attrs)
            _t1074 = _dollar_dollar.attrs
        else
            _t1074 = nothing
        end
        return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1074,)
    end
    _t1075 = _t1073(msg)
    fields337 = _t1075
    unwrapped_fields338 = fields337
    write(pp, "(")
    write(pp, "monoid")
    indent!(pp)
    newline(pp)
    field339 = unwrapped_fields338[1]
    _t1076 = pretty_monoid(pp, field339)
    newline(pp)
    field340 = unwrapped_fields338[2]
    _t1077 = pretty_relation_id(pp, field340)
    newline(pp)
    field341 = unwrapped_fields338[3]
    _t1078 = pretty_abstraction_with_arity(pp, field341)
    field342 = unwrapped_fields338[4]
    
    if !isnothing(field342)
        newline(pp)
        opt_val343 = field342
        _t1080 = pretty_attrs(pp, opt_val343)
        _t1079 = _t1080
    else
        _t1079 = nothing
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    function _t1081(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1082 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1082 = nothing
        end
        return _t1082
    end
    _t1083 = _t1081(msg)
    deconstruct_result347 = _t1083
    
    if !isnothing(deconstruct_result347)
        _t1085 = pretty_or_monoid(pp, deconstruct_result347)
        _t1084 = _t1085
    else
        function _t1086(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1087 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1087 = nothing
            end
            return _t1087
        end
        _t1088 = _t1086(msg)
        deconstruct_result346 = _t1088
        
        if !isnothing(deconstruct_result346)
            _t1090 = pretty_min_monoid(pp, deconstruct_result346)
            _t1089 = _t1090
        else
            function _t1091(_dollar_dollar)
                
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1092 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1092 = nothing
                end
                return _t1092
            end
            _t1093 = _t1091(msg)
            deconstruct_result345 = _t1093
            
            if !isnothing(deconstruct_result345)
                _t1095 = pretty_max_monoid(pp, deconstruct_result345)
                _t1094 = _t1095
            else
                function _t1096(_dollar_dollar)
                    
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1097 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1097 = nothing
                    end
                    return _t1097
                end
                _t1098 = _t1096(msg)
                deconstruct_result344 = _t1098
                
                if !isnothing(deconstruct_result344)
                    _t1100 = pretty_sum_monoid(pp, deconstruct_result344)
                    _t1099 = _t1100
                else
                    throw(ParseError("No matching rule for monoid"))
                end
                _t1094 = _t1099
            end
            _t1089 = _t1094
        end
        _t1084 = _t1089
    end
    return _t1084
end

function pretty_or_monoid(pp::PrettyPrinter, msg::Proto.OrMonoid)
    function _t1101(_dollar_dollar)
        return _dollar_dollar
    end
    _t1102 = _t1101(msg)
    fields348 = _t1102
    unwrapped_fields349 = fields348
    write(pp, "(")
    write(pp, "or")
    write(pp, ")")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    function _t1103(_dollar_dollar)
        return _dollar_dollar.var"#type"
    end
    _t1104 = _t1103(msg)
    fields350 = _t1104
    unwrapped_fields351 = fields350
    write(pp, "(")
    write(pp, "min")
    indent!(pp)
    newline(pp)
    _t1105 = pretty_type(pp, unwrapped_fields351)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    function _t1106(_dollar_dollar)
        return _dollar_dollar.var"#type"
    end
    _t1107 = _t1106(msg)
    fields352 = _t1107
    unwrapped_fields353 = fields352
    write(pp, "(")
    write(pp, "max")
    indent!(pp)
    newline(pp)
    _t1108 = pretty_type(pp, unwrapped_fields353)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    function _t1109(_dollar_dollar)
        return _dollar_dollar.var"#type"
    end
    _t1110 = _t1109(msg)
    fields354 = _t1110
    unwrapped_fields355 = fields354
    write(pp, "(")
    write(pp, "sum")
    indent!(pp)
    newline(pp)
    _t1111 = pretty_type(pp, unwrapped_fields355)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    function _t1112(_dollar_dollar)
        
        if !isempty(_dollar_dollar.attrs)
            _t1113 = _dollar_dollar.attrs
        else
            _t1113 = nothing
        end
        return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1113,)
    end
    _t1114 = _t1112(msg)
    fields356 = _t1114
    unwrapped_fields357 = fields356
    write(pp, "(")
    write(pp, "monus")
    indent!(pp)
    newline(pp)
    field358 = unwrapped_fields357[1]
    _t1115 = pretty_monoid(pp, field358)
    newline(pp)
    field359 = unwrapped_fields357[2]
    _t1116 = pretty_relation_id(pp, field359)
    newline(pp)
    field360 = unwrapped_fields357[3]
    _t1117 = pretty_abstraction_with_arity(pp, field360)
    field361 = unwrapped_fields357[4]
    
    if !isnothing(field361)
        newline(pp)
        opt_val362 = field361
        _t1119 = pretty_attrs(pp, opt_val362)
        _t1118 = _t1119
    else
        _t1118 = nothing
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    function _t1120(_dollar_dollar)
        return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
    end
    _t1121 = _t1120(msg)
    fields363 = _t1121
    unwrapped_fields364 = fields363
    write(pp, "(")
    write(pp, "functional_dependency")
    indent!(pp)
    newline(pp)
    field365 = unwrapped_fields364[1]
    _t1122 = pretty_relation_id(pp, field365)
    newline(pp)
    field366 = unwrapped_fields364[2]
    _t1123 = pretty_abstraction(pp, field366)
    newline(pp)
    field367 = unwrapped_fields364[3]
    _t1124 = pretty_functional_dependency_keys(pp, field367)
    newline(pp)
    field368 = unwrapped_fields364[4]
    _t1125 = pretty_functional_dependency_values(pp, field368)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    function _t1126(_dollar_dollar)
        return _dollar_dollar
    end
    _t1127 = _t1126(msg)
    fields369 = _t1127
    unwrapped_fields370 = fields369
    write(pp, "(")
    write(pp, "keys")
    indent!(pp)
    if !isempty(unwrapped_fields370)
        newline(pp)
        for (i1128, elem371) in enumerate(unwrapped_fields370)
            i372 = i1128 - 1
            if (i372 > 0)
                newline(pp)
            end
            _t1129 = pretty_var(pp, elem371)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    function _t1130(_dollar_dollar)
        return _dollar_dollar
    end
    _t1131 = _t1130(msg)
    fields373 = _t1131
    unwrapped_fields374 = fields373
    write(pp, "(")
    write(pp, "values")
    indent!(pp)
    if !isempty(unwrapped_fields374)
        newline(pp)
        for (i1132, elem375) in enumerate(unwrapped_fields374)
            i376 = i1132 - 1
            if (i376 > 0)
                newline(pp)
            end
            _t1133 = pretty_var(pp, elem375)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    function _t1134(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("rel_edb"))
            _t1135 = _get_oneof_field(_dollar_dollar, :rel_edb)
        else
            _t1135 = nothing
        end
        return _t1135
    end
    _t1136 = _t1134(msg)
    deconstruct_result379 = _t1136
    
    if !isnothing(deconstruct_result379)
        _t1138 = pretty_rel_edb(pp, deconstruct_result379)
        _t1137 = _t1138
    else
        function _t1139(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1140 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1140 = nothing
            end
            return _t1140
        end
        _t1141 = _t1139(msg)
        deconstruct_result378 = _t1141
        
        if !isnothing(deconstruct_result378)
            _t1143 = pretty_betree_relation(pp, deconstruct_result378)
            _t1142 = _t1143
        else
            function _t1144(_dollar_dollar)
                
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1145 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1145 = nothing
                end
                return _t1145
            end
            _t1146 = _t1144(msg)
            deconstruct_result377 = _t1146
            
            if !isnothing(deconstruct_result377)
                _t1148 = pretty_csv_data(pp, deconstruct_result377)
                _t1147 = _t1148
            else
                throw(ParseError("No matching rule for data"))
            end
            _t1142 = _t1147
        end
        _t1137 = _t1142
    end
    return _t1137
end

function pretty_rel_edb(pp::PrettyPrinter, msg::Proto.RelEDB)
    function _t1149(_dollar_dollar)
        return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
    end
    _t1150 = _t1149(msg)
    fields380 = _t1150
    unwrapped_fields381 = fields380
    write(pp, "(")
    write(pp, "rel_edb")
    indent!(pp)
    newline(pp)
    field382 = unwrapped_fields381[1]
    _t1151 = pretty_relation_id(pp, field382)
    newline(pp)
    field383 = unwrapped_fields381[2]
    _t1152 = pretty_rel_edb_path(pp, field383)
    newline(pp)
    field384 = unwrapped_fields381[3]
    _t1153 = pretty_rel_edb_types(pp, field384)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_rel_edb_path(pp::PrettyPrinter, msg::Vector{String})
    function _t1154(_dollar_dollar)
        return _dollar_dollar
    end
    _t1155 = _t1154(msg)
    fields385 = _t1155
    unwrapped_fields386 = fields385
    write(pp, "[")
    for (i1156, elem387) in enumerate(unwrapped_fields386)
        i388 = i1156 - 1
        if (i388 > 0)
            newline(pp)
        end
        write(pp, format_string_value(elem387))
    end
    write(pp, "]")
    return nothing
end

function pretty_rel_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    function _t1157(_dollar_dollar)
        return _dollar_dollar
    end
    _t1158 = _t1157(msg)
    fields389 = _t1158
    unwrapped_fields390 = fields389
    write(pp, "[")
    for (i1159, elem391) in enumerate(unwrapped_fields390)
        i392 = i1159 - 1
        if (i392 > 0)
            newline(pp)
        end
        _t1160 = pretty_type(pp, elem391)
    end
    write(pp, "]")
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    function _t1161(_dollar_dollar)
        return (_dollar_dollar.name, _dollar_dollar.relation_info,)
    end
    _t1162 = _t1161(msg)
    fields393 = _t1162
    unwrapped_fields394 = fields393
    write(pp, "(")
    write(pp, "betree_relation")
    indent!(pp)
    newline(pp)
    field395 = unwrapped_fields394[1]
    _t1163 = pretty_relation_id(pp, field395)
    newline(pp)
    field396 = unwrapped_fields394[2]
    _t1164 = pretty_betree_info(pp, field396)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    function _t1165(_dollar_dollar)
        _t1166 = deconstruct_betree_info_config(pp, _dollar_dollar)
        return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1166,)
    end
    _t1167 = _t1165(msg)
    fields397 = _t1167
    unwrapped_fields398 = fields397
    write(pp, "(")
    write(pp, "betree_info")
    indent!(pp)
    newline(pp)
    field399 = unwrapped_fields398[1]
    _t1168 = pretty_betree_info_key_types(pp, field399)
    newline(pp)
    field400 = unwrapped_fields398[2]
    _t1169 = pretty_betree_info_value_types(pp, field400)
    newline(pp)
    field401 = unwrapped_fields398[3]
    _t1170 = pretty_config_dict(pp, field401)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    function _t1171(_dollar_dollar)
        return _dollar_dollar
    end
    _t1172 = _t1171(msg)
    fields402 = _t1172
    unwrapped_fields403 = fields402
    write(pp, "(")
    write(pp, "key_types")
    indent!(pp)
    if !isempty(unwrapped_fields403)
        newline(pp)
        for (i1173, elem404) in enumerate(unwrapped_fields403)
            i405 = i1173 - 1
            if (i405 > 0)
                newline(pp)
            end
            _t1174 = pretty_type(pp, elem404)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    function _t1175(_dollar_dollar)
        return _dollar_dollar
    end
    _t1176 = _t1175(msg)
    fields406 = _t1176
    unwrapped_fields407 = fields406
    write(pp, "(")
    write(pp, "value_types")
    indent!(pp)
    if !isempty(unwrapped_fields407)
        newline(pp)
        for (i1177, elem408) in enumerate(unwrapped_fields407)
            i409 = i1177 - 1
            if (i409 > 0)
                newline(pp)
            end
            _t1178 = pretty_type(pp, elem408)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    function _t1179(_dollar_dollar)
        return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
    end
    _t1180 = _t1179(msg)
    fields410 = _t1180
    unwrapped_fields411 = fields410
    write(pp, "(")
    write(pp, "csv_data")
    indent!(pp)
    newline(pp)
    field412 = unwrapped_fields411[1]
    _t1181 = pretty_csvlocator(pp, field412)
    newline(pp)
    field413 = unwrapped_fields411[2]
    _t1182 = pretty_csv_config(pp, field413)
    newline(pp)
    field414 = unwrapped_fields411[3]
    _t1183 = pretty_csv_columns(pp, field414)
    newline(pp)
    field415 = unwrapped_fields411[4]
    _t1184 = pretty_csv_asof(pp, field415)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    function _t1185(_dollar_dollar)
        
        if !isempty(_dollar_dollar.paths)
            _t1186 = _dollar_dollar.paths
        else
            _t1186 = nothing
        end
        
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1187 = String(copy(_dollar_dollar.inline_data))
        else
            _t1187 = nothing
        end
        return (_t1186, _t1187,)
    end
    _t1188 = _t1185(msg)
    fields416 = _t1188
    unwrapped_fields417 = fields416
    write(pp, "(")
    write(pp, "csv_locator")
    indent!(pp)
    field418 = unwrapped_fields417[1]
    
    if !isnothing(field418)
        newline(pp)
        opt_val419 = field418
        _t1190 = pretty_csv_locator_paths(pp, opt_val419)
        _t1189 = _t1190
    else
        _t1189 = nothing
    end
    field420 = unwrapped_fields417[2]
    
    if !isnothing(field420)
        newline(pp)
        opt_val421 = field420
        _t1192 = pretty_csv_locator_inline_data(pp, opt_val421)
        _t1191 = _t1192
    else
        _t1191 = nothing
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    function _t1193(_dollar_dollar)
        return _dollar_dollar
    end
    _t1194 = _t1193(msg)
    fields422 = _t1194
    unwrapped_fields423 = fields422
    write(pp, "(")
    write(pp, "paths")
    indent!(pp)
    if !isempty(unwrapped_fields423)
        newline(pp)
        for (i1195, elem424) in enumerate(unwrapped_fields423)
            i425 = i1195 - 1
            if (i425 > 0)
                newline(pp)
            end
            write(pp, format_string_value(elem424))
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    function _t1196(_dollar_dollar)
        return _dollar_dollar
    end
    _t1197 = _t1196(msg)
    fields426 = _t1197
    unwrapped_fields427 = fields426
    write(pp, "(")
    write(pp, "inline_data")
    indent!(pp)
    newline(pp)
    write(pp, format_string_value(unwrapped_fields427))
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    function _t1198(_dollar_dollar)
        _t1199 = deconstruct_csv_config(pp, _dollar_dollar)
        return _t1199
    end
    _t1200 = _t1198(msg)
    fields428 = _t1200
    unwrapped_fields429 = fields428
    write(pp, "(")
    write(pp, "csv_config")
    indent!(pp)
    newline(pp)
    _t1201 = pretty_config_dict(pp, unwrapped_fields429)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.CSVColumn})
    function _t1202(_dollar_dollar)
        return _dollar_dollar
    end
    _t1203 = _t1202(msg)
    fields430 = _t1203
    unwrapped_fields431 = fields430
    write(pp, "(")
    write(pp, "columns")
    indent!(pp)
    if !isempty(unwrapped_fields431)
        newline(pp)
        for (i1204, elem432) in enumerate(unwrapped_fields431)
            i433 = i1204 - 1
            if (i433 > 0)
                newline(pp)
            end
            _t1205 = pretty_csv_column(pp, elem432)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_csv_column(pp::PrettyPrinter, msg::Proto.CSVColumn)
    function _t1206(_dollar_dollar)
        return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
    end
    _t1207 = _t1206(msg)
    fields434 = _t1207
    unwrapped_fields435 = fields434
    write(pp, "(")
    write(pp, "column")
    indent!(pp)
    newline(pp)
    field436 = unwrapped_fields435[1]
    write(pp, format_string_value(field436))
    newline(pp)
    field437 = unwrapped_fields435[2]
    _t1208 = pretty_relation_id(pp, field437)
    newline(pp)
    write(pp, "[")
    field438 = unwrapped_fields435[3]
    for (i1209, elem439) in enumerate(field438)
        i440 = i1209 - 1
        if (i440 > 0)
            newline(pp)
        end
        _t1210 = pretty_type(pp, elem439)
    end
    write(pp, "]")
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    function _t1211(_dollar_dollar)
        return _dollar_dollar
    end
    _t1212 = _t1211(msg)
    fields441 = _t1212
    unwrapped_fields442 = fields441
    write(pp, "(")
    write(pp, "asof")
    indent!(pp)
    newline(pp)
    write(pp, format_string_value(unwrapped_fields442))
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    function _t1213(_dollar_dollar)
        return _dollar_dollar.fragment_id
    end
    _t1214 = _t1213(msg)
    fields443 = _t1214
    unwrapped_fields444 = fields443
    write(pp, "(")
    write(pp, "undefine")
    indent!(pp)
    newline(pp)
    _t1215 = pretty_fragment_id(pp, unwrapped_fields444)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    function _t1216(_dollar_dollar)
        return _dollar_dollar.relations
    end
    _t1217 = _t1216(msg)
    fields445 = _t1217
    unwrapped_fields446 = fields445
    write(pp, "(")
    write(pp, "context")
    indent!(pp)
    if !isempty(unwrapped_fields446)
        newline(pp)
        for (i1218, elem447) in enumerate(unwrapped_fields446)
            i448 = i1218 - 1
            if (i448 > 0)
                newline(pp)
            end
            _t1219 = pretty_relation_id(pp, elem447)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    function _t1220(_dollar_dollar)
        return _dollar_dollar
    end
    _t1221 = _t1220(msg)
    fields449 = _t1221
    unwrapped_fields450 = fields449
    write(pp, "(")
    write(pp, "reads")
    indent!(pp)
    if !isempty(unwrapped_fields450)
        newline(pp)
        for (i1222, elem451) in enumerate(unwrapped_fields450)
            i452 = i1222 - 1
            if (i452 > 0)
                newline(pp)
            end
            _t1223 = pretty_read(pp, elem451)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    function _t1224(_dollar_dollar)
        
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1225 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1225 = nothing
        end
        return _t1225
    end
    _t1226 = _t1224(msg)
    deconstruct_result457 = _t1226
    
    if !isnothing(deconstruct_result457)
        _t1228 = pretty_demand(pp, deconstruct_result457)
        _t1227 = _t1228
    else
        function _t1229(_dollar_dollar)
            
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1230 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1230 = nothing
            end
            return _t1230
        end
        _t1231 = _t1229(msg)
        deconstruct_result456 = _t1231
        
        if !isnothing(deconstruct_result456)
            _t1233 = pretty_output(pp, deconstruct_result456)
            _t1232 = _t1233
        else
            function _t1234(_dollar_dollar)
                
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1235 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1235 = nothing
                end
                return _t1235
            end
            _t1236 = _t1234(msg)
            deconstruct_result455 = _t1236
            
            if !isnothing(deconstruct_result455)
                _t1238 = pretty_what_if(pp, deconstruct_result455)
                _t1237 = _t1238
            else
                function _t1239(_dollar_dollar)
                    
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1240 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1240 = nothing
                    end
                    return _t1240
                end
                _t1241 = _t1239(msg)
                deconstruct_result454 = _t1241
                
                if !isnothing(deconstruct_result454)
                    _t1243 = pretty_abort(pp, deconstruct_result454)
                    _t1242 = _t1243
                else
                    function _t1244(_dollar_dollar)
                        
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1245 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1245 = nothing
                        end
                        return _t1245
                    end
                    _t1246 = _t1244(msg)
                    deconstruct_result453 = _t1246
                    
                    if !isnothing(deconstruct_result453)
                        _t1248 = pretty_export(pp, deconstruct_result453)
                        _t1247 = _t1248
                    else
                        throw(ParseError("No matching rule for read"))
                    end
                    _t1242 = _t1247
                end
                _t1237 = _t1242
            end
            _t1232 = _t1237
        end
        _t1227 = _t1232
    end
    return _t1227
end

function pretty_demand(pp::PrettyPrinter, msg::Proto.Demand)
    function _t1249(_dollar_dollar)
        return _dollar_dollar.relation_id
    end
    _t1250 = _t1249(msg)
    fields458 = _t1250
    unwrapped_fields459 = fields458
    write(pp, "(")
    write(pp, "demand")
    indent!(pp)
    newline(pp)
    _t1251 = pretty_relation_id(pp, unwrapped_fields459)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    function _t1252(_dollar_dollar)
        return (_dollar_dollar.name, _dollar_dollar.relation_id,)
    end
    _t1253 = _t1252(msg)
    fields460 = _t1253
    unwrapped_fields461 = fields460
    write(pp, "(")
    write(pp, "output")
    indent!(pp)
    newline(pp)
    field462 = unwrapped_fields461[1]
    _t1254 = pretty_name(pp, field462)
    newline(pp)
    field463 = unwrapped_fields461[2]
    _t1255 = pretty_relation_id(pp, field463)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    function _t1256(_dollar_dollar)
        return (_dollar_dollar.branch, _dollar_dollar.epoch,)
    end
    _t1257 = _t1256(msg)
    fields464 = _t1257
    unwrapped_fields465 = fields464
    write(pp, "(")
    write(pp, "what_if")
    indent!(pp)
    newline(pp)
    field466 = unwrapped_fields465[1]
    _t1258 = pretty_name(pp, field466)
    newline(pp)
    field467 = unwrapped_fields465[2]
    _t1259 = pretty_epoch(pp, field467)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    function _t1260(_dollar_dollar)
        
        if _dollar_dollar.name != "abort"
            _t1261 = _dollar_dollar.name
        else
            _t1261 = nothing
        end
        return (_t1261, _dollar_dollar.relation_id,)
    end
    _t1262 = _t1260(msg)
    fields468 = _t1262
    unwrapped_fields469 = fields468
    write(pp, "(")
    write(pp, "abort")
    indent!(pp)
    field470 = unwrapped_fields469[1]
    
    if !isnothing(field470)
        newline(pp)
        opt_val471 = field470
        _t1264 = pretty_name(pp, opt_val471)
        _t1263 = _t1264
    else
        _t1263 = nothing
    end
    newline(pp)
    field472 = unwrapped_fields469[2]
    _t1265 = pretty_relation_id(pp, field472)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    function _t1266(_dollar_dollar)
        return _get_oneof_field(_dollar_dollar, :csv_config)
    end
    _t1267 = _t1266(msg)
    fields473 = _t1267
    unwrapped_fields474 = fields473
    write(pp, "(")
    write(pp, "export")
    indent!(pp)
    newline(pp)
    _t1268 = pretty_export_csv_config(pp, unwrapped_fields474)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    function _t1269(_dollar_dollar)
        _t1270 = deconstruct_export_csv_config(pp, _dollar_dollar)
        return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1270,)
    end
    _t1271 = _t1269(msg)
    fields475 = _t1271
    unwrapped_fields476 = fields475
    write(pp, "(")
    write(pp, "export_csv_config")
    indent!(pp)
    newline(pp)
    field477 = unwrapped_fields476[1]
    _t1272 = pretty_export_csv_path(pp, field477)
    newline(pp)
    field478 = unwrapped_fields476[2]
    _t1273 = pretty_export_csv_columns(pp, field478)
    newline(pp)
    field479 = unwrapped_fields476[3]
    _t1274 = pretty_config_dict(pp, field479)
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    function _t1275(_dollar_dollar)
        return _dollar_dollar
    end
    _t1276 = _t1275(msg)
    fields480 = _t1276
    unwrapped_fields481 = fields480
    write(pp, "(")
    write(pp, "path")
    indent!(pp)
    newline(pp)
    write(pp, format_string_value(unwrapped_fields481))
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    function _t1277(_dollar_dollar)
        return _dollar_dollar
    end
    _t1278 = _t1277(msg)
    fields482 = _t1278
    unwrapped_fields483 = fields482
    write(pp, "(")
    write(pp, "columns")
    indent!(pp)
    if !isempty(unwrapped_fields483)
        newline(pp)
        for (i1279, elem484) in enumerate(unwrapped_fields483)
            i485 = i1279 - 1
            if (i485 > 0)
                newline(pp)
            end
            _t1280 = pretty_export_csv_column(pp, elem484)
        end
    end
    dedent!(pp)
    write(pp, ")")
    return nothing
end

function pretty_export_csv_column(pp::PrettyPrinter, msg::Proto.ExportCSVColumn)
    function _t1281(_dollar_dollar)
        return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
    end
    _t1282 = _t1281(msg)
    fields486 = _t1282
    unwrapped_fields487 = fields486
    write(pp, "(")
    write(pp, "column")
    indent!(pp)
    newline(pp)
    field488 = unwrapped_fields487[1]
    write(pp, format_string_value(field488))
    newline(pp)
    field489 = unwrapped_fields487[2]
    _t1283 = pretty_relation_id(pp, field489)
    dedent!(pp)
    write(pp, ")")
    return nothing
end


function pretty(msg::Proto.Transaction)::String
    pp = PrettyPrinter()
    pretty_transaction(pp, msg)
    newline(pp)
    return get_output(pp)
end
