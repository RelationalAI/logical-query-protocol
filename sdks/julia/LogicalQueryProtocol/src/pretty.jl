# Auto-generated pretty printer.
#
# Generated from protobuf specifications.
# Do not modify this file! If you need to modify the pretty printer, edit the generator code
# in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.
#
# Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer julia

mutable struct PrettyPrinter
    io::IOBuffer
    indent_stack::Vector{Int}
    column::Int
    at_line_start::Bool
    separator::String
    max_width::Int
    _computing::Set{UInt}
    _memo::Dict{UInt,String}
    _memo_refs::Vector{Any}
    debug_info::Dict{Tuple{UInt64,UInt64},String}
end

function PrettyPrinter(; max_width::Int=92)
    return PrettyPrinter(
        IOBuffer(), [0], 0, true, "\n", max_width,
        Set{UInt}(), Dict{UInt,String}(), Any[],
        Dict{Tuple{UInt64,UInt64},String}(),
    )
end

function indent_level(pp::PrettyPrinter)::Int
    return isempty(pp.indent_stack) ? 0 : last(pp.indent_stack)
end

function Base.write(pp::PrettyPrinter, s::AbstractString)
    if pp.separator == "\n" && pp.at_line_start && !isempty(strip(s))
        spaces = indent_level(pp)
        Base.write(pp.io, " " ^ spaces)
        pp.column = spaces
        pp.at_line_start = false
    end
    Base.write(pp.io, s)
    nl_pos = findlast('\n', s)
    if !isnothing(nl_pos)
        pp.column = length(s) - nl_pos
    else
        pp.column += length(s)
    end
    return nothing
end

function newline(pp::PrettyPrinter)
    Base.write(pp.io, pp.separator)
    if pp.separator == "\n"
        pp.at_line_start = true
        pp.column = 0
    end
    return nothing
end

function indent!(pp::PrettyPrinter)
    if pp.separator == "\n"
        push!(pp.indent_stack, pp.column)
    end
    return nothing
end

function indent_sexp!(pp::PrettyPrinter)
    if pp.separator == "\n"
        push!(pp.indent_stack, indent_level(pp) + 2)
    end
    return nothing
end

function dedent!(pp::PrettyPrinter)
    if pp.separator == "\n" && length(pp.indent_stack) > 1
        pop!(pp.indent_stack)
    end
    return nothing
end

function try_flat(pp::PrettyPrinter, msg, pretty_fn::Function)
    msg_id = objectid(msg)
    if !haskey(pp._memo, msg_id) && !(msg_id in pp._computing)
        push!(pp._computing, msg_id)
        saved_io = pp.io
        saved_sep = pp.separator
        saved_indent = pp.indent_stack
        saved_col = pp.column
        saved_at_line_start = pp.at_line_start
        try
            pp.io = IOBuffer()
            pp.separator = " "
            pp.indent_stack = [0]
            pp.column = 0
            pp.at_line_start = false
            pretty_fn(pp, msg)
            pp._memo[msg_id] = String(copy(pp.io.data[1:pp.io.size]))
            push!(pp._memo_refs, msg)
        finally
            pp.io = saved_io
            pp.separator = saved_sep
            pp.indent_stack = saved_indent
            pp.column = saved_col
            pp.at_line_start = saved_at_line_start
            delete!(pp._computing, msg_id)
        end
    end
    if haskey(pp._memo, msg_id)
        flat = pp._memo[msg_id]
        if pp.separator != "\n"
            return flat
        end
        effective_col = pp.at_line_start ? indent_level(pp) : pp.column
        if length(flat) + effective_col <= pp.max_width
            return flat
        end
    end
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

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1419 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1419
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1420 = Proto.Value(value=OneOf(:int_value, v))
    return _t1420
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1421 = Proto.Value(value=OneOf(:float_value, v))
    return _t1421
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1422 = Proto.Value(value=OneOf(:string_value, v))
    return _t1422
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1423 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1423
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1424 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1424
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1425 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1425,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1426 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1426,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1427 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1427,))
            end
        end
    end
    _t1428 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1428,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1429 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1429,))
    _t1430 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1430,))
    if msg.new_line != ""
        _t1431 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1431,))
    end
    _t1432 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1432,))
    _t1433 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1433,))
    _t1434 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1434,))
    if msg.comment != ""
        _t1435 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1435,))
    end
    for missing_string in msg.missing_strings
        _t1436 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1436,))
    end
    _t1437 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1437,))
    _t1438 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1438,))
    _t1439 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1439,))
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1440 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1440,))
    _t1441 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1441,))
    _t1442 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1442,))
    _t1443 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1443,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1444 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1444,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1445 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1445,))
        end
    end
    _t1446 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1446,))
    _t1447 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1447,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1448 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1448,))
    end
    if !isnothing(msg.compression)
        _t1449 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1449,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1450 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1450,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1451 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1451,))
    end
    if !isnothing(msg.syntax_delim)
        _t1452 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1452,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1453 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1453,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1454 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1454,))
    end
    return sort(result)
end

function deconstruct_relation_id_string(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, String}
    name = relation_id_to_string(pp, msg)
    if name != ""
        return name
    end
    return nothing
end

function deconstruct_relation_id_uint128(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, Proto.UInt128Value}
    name = relation_id_to_string(pp, msg)
    if name == ""
        return relation_id_to_uint128(pp, msg)
    end
    return nothing
end

function deconstruct_bindings(pp::PrettyPrinter, abs::Proto.Abstraction)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    n = length(abs.vars)
    return (abs.vars[0 + 1:n], Proto.Binding[],)
end

function deconstruct_bindings_with_arity(pp::PrettyPrinter, abs::Proto.Abstraction, value_arity::Int64)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    n = length(abs.vars)
    key_end = (n - value_arity)
    return (abs.vars[0 + 1:key_end], abs.vars[key_end + 1:n],)
end

# --- Pretty-print functions ---

function pretty_transaction(pp::PrettyPrinter, msg::Proto.Transaction)
    flat9 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat9)
        write(pp, flat9)
        return nothing
    else
        function _t607(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("configure"))
                _t608 = _dollar_dollar.configure
            else
                _t608 = nothing
            end
            if _has_proto_field(_dollar_dollar, Symbol("sync"))
                _t609 = _dollar_dollar.sync
            else
                _t609 = nothing
            end
            return (_t608, _t609, _dollar_dollar.epochs,)
        end
        _t610 = _t607(msg)
        fields0 = _t610
        unwrapped_fields1 = fields0
        write(pp, "(")
        write(pp, "transaction")
        indent_sexp!(pp)
        field2 = unwrapped_fields1[1]
        if !isnothing(field2)
            newline(pp)
            opt_val3 = field2
            _t612 = pretty_configure(pp, opt_val3)
            _t611 = _t612
        else
            _t611 = nothing
        end
        field4 = unwrapped_fields1[2]
        if !isnothing(field4)
            newline(pp)
            opt_val5 = field4
            _t614 = pretty_sync(pp, opt_val5)
            _t613 = _t614
        else
            _t613 = nothing
        end
        field6 = unwrapped_fields1[3]
        if !isempty(field6)
            newline(pp)
            for (i615, elem7) in enumerate(field6)
                i8 = i615 - 1
                if (i8 > 0)
                    newline(pp)
                end
                _t616 = pretty_epoch(pp, elem7)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat12 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat12)
        write(pp, flat12)
        return nothing
    else
        function _t617(_dollar_dollar)
            _t618 = deconstruct_configure(pp, _dollar_dollar)
            return _t618
        end
        _t619 = _t617(msg)
        fields10 = _t619
        unwrapped_fields11 = fields10
        write(pp, "(")
        write(pp, "configure")
        indent_sexp!(pp)
        newline(pp)
        _t620 = pretty_config_dict(pp, unwrapped_fields11)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat17 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat17)
        write(pp, flat17)
        return nothing
    else
        function _t621(_dollar_dollar)
            return _dollar_dollar
        end
        _t622 = _t621(msg)
        fields13 = _t622
        unwrapped_fields14 = fields13
        write(pp, "{")
        indent!(pp)
        if !isempty(unwrapped_fields14)
            newline(pp)
            for (i623, elem15) in enumerate(unwrapped_fields14)
                i16 = i623 - 1
                if (i16 > 0)
                    newline(pp)
                end
                _t624 = pretty_config_key_value(pp, elem15)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat22 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat22)
        write(pp, flat22)
        return nothing
    else
        function _t626(_dollar_dollar)
            return (_dollar_dollar[1], _dollar_dollar[2],)
        end
        _t627 = _t626(msg)
        fields18 = _t627
        unwrapped_fields19 = fields18
        write(pp, ":")
        field20 = unwrapped_fields19[1]
        write(pp, field20)
        write(pp, " ")
        field21 = unwrapped_fields19[2]
        _t628 = pretty_value(pp, field21)
        _t625 = _t628
    end
    return _t625
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat34 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat34)
        write(pp, flat34)
        return nothing
    else
        function _t630(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("date_value"))
                _t631 = _get_oneof_field(_dollar_dollar, :date_value)
            else
                _t631 = nothing
            end
            return _t631
        end
        _t632 = _t630(msg)
        deconstruct_result33 = _t632
        if !isnothing(deconstruct_result33)
            _t634 = pretty_date(pp, deconstruct_result33)
            _t633 = _t634
        else
            function _t635(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                    _t636 = _get_oneof_field(_dollar_dollar, :datetime_value)
                else
                    _t636 = nothing
                end
                return _t636
            end
            _t637 = _t635(msg)
            deconstruct_result32 = _t637
            if !isnothing(deconstruct_result32)
                _t639 = pretty_datetime(pp, deconstruct_result32)
                _t638 = _t639
            else
                function _t640(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                        _t641 = _get_oneof_field(_dollar_dollar, :string_value)
                    else
                        _t641 = nothing
                    end
                    return _t641
                end
                _t642 = _t640(msg)
                deconstruct_result31 = _t642
                if !isnothing(deconstruct_result31)
                    write(pp, format_string_value(deconstruct_result31))
                    _t643 = nothing
                else
                    function _t644(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t645 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t645 = nothing
                        end
                        return _t645
                    end
                    _t646 = _t644(msg)
                    deconstruct_result30 = _t646
                    if !isnothing(deconstruct_result30)
                        write(pp, string(deconstruct_result30))
                        _t647 = nothing
                    else
                        function _t648(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                _t649 = _get_oneof_field(_dollar_dollar, :float_value)
                            else
                                _t649 = nothing
                            end
                            return _t649
                        end
                        _t650 = _t648(msg)
                        deconstruct_result29 = _t650
                        if !isnothing(deconstruct_result29)
                            write(pp, format_float64(deconstruct_result29))
                            _t651 = nothing
                        else
                            function _t652(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                    _t653 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                else
                                    _t653 = nothing
                                end
                                return _t653
                            end
                            _t654 = _t652(msg)
                            deconstruct_result28 = _t654
                            if !isnothing(deconstruct_result28)
                                write(pp, format_uint128(pp, deconstruct_result28))
                                _t655 = nothing
                            else
                                function _t656(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                        _t657 = _get_oneof_field(_dollar_dollar, :int128_value)
                                    else
                                        _t657 = nothing
                                    end
                                    return _t657
                                end
                                _t658 = _t656(msg)
                                deconstruct_result27 = _t658
                                if !isnothing(deconstruct_result27)
                                    write(pp, format_int128(pp, deconstruct_result27))
                                    _t659 = nothing
                                else
                                    function _t660(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                            _t661 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                        else
                                            _t661 = nothing
                                        end
                                        return _t661
                                    end
                                    _t662 = _t660(msg)
                                    deconstruct_result26 = _t662
                                    if !isnothing(deconstruct_result26)
                                        write(pp, format_decimal(pp, deconstruct_result26))
                                        _t663 = nothing
                                    else
                                        function _t664(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                _t665 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                            else
                                                _t665 = nothing
                                            end
                                            return _t665
                                        end
                                        _t666 = _t664(msg)
                                        deconstruct_result25 = _t666
                                        if !isnothing(deconstruct_result25)
                                            _t668 = pretty_boolean_value(pp, deconstruct_result25)
                                            _t667 = _t668
                                        else
                                            function _t669(_dollar_dollar)
                                                return _dollar_dollar
                                            end
                                            _t670 = _t669(msg)
                                            fields23 = _t670
                                            unwrapped_fields24 = fields23
                                            write(pp, "missing")
                                            _t667 = nothing
                                        end
                                        _t663 = _t667
                                    end
                                    _t659 = _t663
                                end
                                _t655 = _t659
                            end
                            _t651 = _t655
                        end
                        _t647 = _t651
                    end
                    _t643 = _t647
                end
                _t638 = _t643
            end
            _t633 = _t638
        end
        _t629 = _t633
    end
    return _t629
end

function pretty_date(pp::PrettyPrinter, msg::Proto.DateValue)
    flat40 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat40)
        write(pp, flat40)
        return nothing
    else
        function _t671(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        end
        _t672 = _t671(msg)
        fields35 = _t672
        unwrapped_fields36 = fields35
        write(pp, "(")
        write(pp, "date")
        indent_sexp!(pp)
        newline(pp)
        field37 = unwrapped_fields36[1]
        write(pp, string(field37))
        newline(pp)
        field38 = unwrapped_fields36[2]
        write(pp, string(field38))
        newline(pp)
        field39 = unwrapped_fields36[3]
        write(pp, string(field39))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat51 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat51)
        write(pp, flat51)
        return nothing
    else
        function _t673(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        end
        _t674 = _t673(msg)
        fields41 = _t674
        unwrapped_fields42 = fields41
        write(pp, "(")
        write(pp, "datetime")
        indent_sexp!(pp)
        newline(pp)
        field43 = unwrapped_fields42[1]
        write(pp, string(field43))
        newline(pp)
        field44 = unwrapped_fields42[2]
        write(pp, string(field44))
        newline(pp)
        field45 = unwrapped_fields42[3]
        write(pp, string(field45))
        newline(pp)
        field46 = unwrapped_fields42[4]
        write(pp, string(field46))
        newline(pp)
        field47 = unwrapped_fields42[5]
        write(pp, string(field47))
        newline(pp)
        field48 = unwrapped_fields42[6]
        write(pp, string(field48))
        field49 = unwrapped_fields42[7]
        if !isnothing(field49)
            newline(pp)
            opt_val50 = field49
            write(pp, string(opt_val50))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    flat54 = try_flat(pp, msg, pretty_boolean_value)
    if !isnothing(flat54)
        write(pp, flat54)
        return nothing
    else
        function _t675(_dollar_dollar)
            if _dollar_dollar
                _t676 = ()
            else
                _t676 = nothing
            end
            return _t676
        end
        _t677 = _t675(msg)
        deconstruct_result53 = _t677
        if !isnothing(deconstruct_result53)
            write(pp, "true")
        else
            function _t678(_dollar_dollar)
                if !_dollar_dollar
                    _t679 = ()
                else
                    _t679 = nothing
                end
                return _t679
            end
            _t680 = _t678(msg)
            deconstruct_result52 = _t680
            if !isnothing(deconstruct_result52)
                write(pp, "false")
            else
                throw(ParseError("No matching rule for boolean_value"))
            end
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat59 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat59)
        write(pp, flat59)
        return nothing
    else
        function _t681(_dollar_dollar)
            return _dollar_dollar.fragments
        end
        _t682 = _t681(msg)
        fields55 = _t682
        unwrapped_fields56 = fields55
        write(pp, "(")
        write(pp, "sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields56)
            newline(pp)
            for (i683, elem57) in enumerate(unwrapped_fields56)
                i58 = i683 - 1
                if (i58 > 0)
                    newline(pp)
                end
                _t684 = pretty_fragment_id(pp, elem57)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat62 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat62)
        write(pp, flat62)
        return nothing
    else
        function _t685(_dollar_dollar)
            return fragment_id_to_string(pp, _dollar_dollar)
        end
        _t686 = _t685(msg)
        fields60 = _t686
        unwrapped_fields61 = fields60
        write(pp, ":")
        write(pp, unwrapped_fields61)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat69 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat69)
        write(pp, flat69)
        return nothing
    else
        function _t687(_dollar_dollar)
            if !isempty(_dollar_dollar.writes)
                _t688 = _dollar_dollar.writes
            else
                _t688 = nothing
            end
            if !isempty(_dollar_dollar.reads)
                _t689 = _dollar_dollar.reads
            else
                _t689 = nothing
            end
            return (_t688, _t689,)
        end
        _t690 = _t687(msg)
        fields63 = _t690
        unwrapped_fields64 = fields63
        write(pp, "(")
        write(pp, "epoch")
        indent_sexp!(pp)
        field65 = unwrapped_fields64[1]
        if !isnothing(field65)
            newline(pp)
            opt_val66 = field65
            _t692 = pretty_epoch_writes(pp, opt_val66)
            _t691 = _t692
        else
            _t691 = nothing
        end
        field67 = unwrapped_fields64[2]
        if !isnothing(field67)
            newline(pp)
            opt_val68 = field67
            _t694 = pretty_epoch_reads(pp, opt_val68)
            _t693 = _t694
        else
            _t693 = nothing
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat74 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat74)
        write(pp, flat74)
        return nothing
    else
        function _t695(_dollar_dollar)
            return _dollar_dollar
        end
        _t696 = _t695(msg)
        fields70 = _t696
        unwrapped_fields71 = fields70
        write(pp, "(")
        write(pp, "writes")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields71)
            newline(pp)
            for (i697, elem72) in enumerate(unwrapped_fields71)
                i73 = i697 - 1
                if (i73 > 0)
                    newline(pp)
                end
                _t698 = pretty_write(pp, elem72)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat78 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat78)
        write(pp, flat78)
        return nothing
    else
        function _t700(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("define"))
                _t701 = _get_oneof_field(_dollar_dollar, :define)
            else
                _t701 = nothing
            end
            return _t701
        end
        _t702 = _t700(msg)
        deconstruct_result77 = _t702
        if !isnothing(deconstruct_result77)
            _t704 = pretty_define(pp, deconstruct_result77)
            _t703 = _t704
        else
            function _t705(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                    _t706 = _get_oneof_field(_dollar_dollar, :undefine)
                else
                    _t706 = nothing
                end
                return _t706
            end
            _t707 = _t705(msg)
            deconstruct_result76 = _t707
            if !isnothing(deconstruct_result76)
                _t709 = pretty_undefine(pp, deconstruct_result76)
                _t708 = _t709
            else
                function _t710(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("context"))
                        _t711 = _get_oneof_field(_dollar_dollar, :context)
                    else
                        _t711 = nothing
                    end
                    return _t711
                end
                _t712 = _t710(msg)
                deconstruct_result75 = _t712
                if !isnothing(deconstruct_result75)
                    _t714 = pretty_context(pp, deconstruct_result75)
                    _t713 = _t714
                else
                    throw(ParseError("No matching rule for write"))
                end
                _t708 = _t713
            end
            _t703 = _t708
        end
        _t699 = _t703
    end
    return _t699
end

function pretty_define(pp::PrettyPrinter, msg::Proto.Define)
    flat81 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat81)
        write(pp, flat81)
        return nothing
    else
        function _t715(_dollar_dollar)
            return _dollar_dollar.fragment
        end
        _t716 = _t715(msg)
        fields79 = _t716
        unwrapped_fields80 = fields79
        write(pp, "(")
        write(pp, "define")
        indent_sexp!(pp)
        newline(pp)
        _t717 = pretty_fragment(pp, unwrapped_fields80)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat88 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat88)
        write(pp, flat88)
        return nothing
    else
        function _t718(_dollar_dollar)
            start_pretty_fragment(pp, _dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        end
        _t719 = _t718(msg)
        fields82 = _t719
        unwrapped_fields83 = fields82
        write(pp, "(")
        write(pp, "fragment")
        indent_sexp!(pp)
        newline(pp)
        field84 = unwrapped_fields83[1]
        _t720 = pretty_new_fragment_id(pp, field84)
        field85 = unwrapped_fields83[2]
        if !isempty(field85)
            newline(pp)
            for (i721, elem86) in enumerate(field85)
                i87 = i721 - 1
                if (i87 > 0)
                    newline(pp)
                end
                _t722 = pretty_declaration(pp, elem86)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat91 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat91)
        write(pp, flat91)
        return nothing
    else
        function _t724(_dollar_dollar)
            return _dollar_dollar
        end
        _t725 = _t724(msg)
        fields89 = _t725
        unwrapped_fields90 = fields89
        _t726 = pretty_fragment_id(pp, unwrapped_fields90)
        _t723 = _t726
    end
    return _t723
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat96 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat96)
        write(pp, flat96)
        return nothing
    else
        function _t728(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("def"))
                _t729 = _get_oneof_field(_dollar_dollar, :def)
            else
                _t729 = nothing
            end
            return _t729
        end
        _t730 = _t728(msg)
        deconstruct_result95 = _t730
        if !isnothing(deconstruct_result95)
            _t732 = pretty_def(pp, deconstruct_result95)
            _t731 = _t732
        else
            function _t733(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                    _t734 = _get_oneof_field(_dollar_dollar, :algorithm)
                else
                    _t734 = nothing
                end
                return _t734
            end
            _t735 = _t733(msg)
            deconstruct_result94 = _t735
            if !isnothing(deconstruct_result94)
                _t737 = pretty_algorithm(pp, deconstruct_result94)
                _t736 = _t737
            else
                function _t738(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                        _t739 = _get_oneof_field(_dollar_dollar, :constraint)
                    else
                        _t739 = nothing
                    end
                    return _t739
                end
                _t740 = _t738(msg)
                deconstruct_result93 = _t740
                if !isnothing(deconstruct_result93)
                    _t742 = pretty_constraint(pp, deconstruct_result93)
                    _t741 = _t742
                else
                    function _t743(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("data"))
                            _t744 = _get_oneof_field(_dollar_dollar, :data)
                        else
                            _t744 = nothing
                        end
                        return _t744
                    end
                    _t745 = _t743(msg)
                    deconstruct_result92 = _t745
                    if !isnothing(deconstruct_result92)
                        _t747 = pretty_data(pp, deconstruct_result92)
                        _t746 = _t747
                    else
                        throw(ParseError("No matching rule for declaration"))
                    end
                    _t741 = _t746
                end
                _t736 = _t741
            end
            _t731 = _t736
        end
        _t727 = _t731
    end
    return _t727
end

function pretty_def(pp::PrettyPrinter, msg::Proto.Def)
    flat103 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat103)
        write(pp, flat103)
        return nothing
    else
        function _t748(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t749 = _dollar_dollar.attrs
            else
                _t749 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t749,)
        end
        _t750 = _t748(msg)
        fields97 = _t750
        unwrapped_fields98 = fields97
        write(pp, "(")
        write(pp, "def")
        indent_sexp!(pp)
        newline(pp)
        field99 = unwrapped_fields98[1]
        _t751 = pretty_relation_id(pp, field99)
        newline(pp)
        field100 = unwrapped_fields98[2]
        _t752 = pretty_abstraction(pp, field100)
        field101 = unwrapped_fields98[3]
        if !isnothing(field101)
            newline(pp)
            opt_val102 = field101
            _t754 = pretty_attrs(pp, opt_val102)
            _t753 = _t754
        else
            _t753 = nothing
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat106 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat106)
        write(pp, flat106)
        return nothing
    else
        function _t755(_dollar_dollar)
            _t756 = deconstruct_relation_id_string(pp, _dollar_dollar)
            return _t756
        end
        _t757 = _t755(msg)
        deconstruct_result105 = _t757
        if !isnothing(deconstruct_result105)
            write(pp, ":")
            write(pp, deconstruct_result105)
        else
            function _t758(_dollar_dollar)
                _t759 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
                return _t759
            end
            _t760 = _t758(msg)
            deconstruct_result104 = _t760
            if !isnothing(deconstruct_result104)
                write(pp, format_uint128(pp, deconstruct_result104))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat111 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat111)
        write(pp, flat111)
        return nothing
    else
        function _t761(_dollar_dollar)
            _t762 = deconstruct_bindings(pp, _dollar_dollar)
            return (_t762, _dollar_dollar.value,)
        end
        _t763 = _t761(msg)
        fields107 = _t763
        unwrapped_fields108 = fields107
        write(pp, "(")
        indent!(pp)
        field109 = unwrapped_fields108[1]
        _t764 = pretty_bindings(pp, field109)
        newline(pp)
        field110 = unwrapped_fields108[2]
        _t765 = pretty_formula(pp, field110)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat119 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat119)
        write(pp, flat119)
        return nothing
    else
        function _t766(_dollar_dollar)
            if !isempty(_dollar_dollar[2])
                _t767 = _dollar_dollar[2]
            else
                _t767 = nothing
            end
            return (_dollar_dollar[1], _t767,)
        end
        _t768 = _t766(msg)
        fields112 = _t768
        unwrapped_fields113 = fields112
        write(pp, "[")
        indent!(pp)
        field114 = unwrapped_fields113[1]
        for (i769, elem115) in enumerate(field114)
            i116 = i769 - 1
            if (i116 > 0)
                newline(pp)
            end
            _t770 = pretty_binding(pp, elem115)
        end
        field117 = unwrapped_fields113[2]
        if !isnothing(field117)
            newline(pp)
            opt_val118 = field117
            _t772 = pretty_value_bindings(pp, opt_val118)
            _t771 = _t772
        else
            _t771 = nothing
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat124 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat124)
        write(pp, flat124)
        return nothing
    else
        function _t774(_dollar_dollar)
            return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        end
        _t775 = _t774(msg)
        fields120 = _t775
        unwrapped_fields121 = fields120
        field122 = unwrapped_fields121[1]
        write(pp, field122)
        write(pp, "::")
        field123 = unwrapped_fields121[2]
        _t776 = pretty_type(pp, field123)
        _t773 = _t776
    end
    return _t773
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat136 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat136)
        write(pp, flat136)
        return nothing
    else
        function _t778(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
                _t779 = _get_oneof_field(_dollar_dollar, :unspecified_type)
            else
                _t779 = nothing
            end
            return _t779
        end
        _t780 = _t778(msg)
        deconstruct_result135 = _t780
        if !isnothing(deconstruct_result135)
            _t782 = pretty_unspecified_type(pp, deconstruct_result135)
            _t781 = _t782
        else
            function _t783(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                    _t784 = _get_oneof_field(_dollar_dollar, :string_type)
                else
                    _t784 = nothing
                end
                return _t784
            end
            _t785 = _t783(msg)
            deconstruct_result134 = _t785
            if !isnothing(deconstruct_result134)
                _t787 = pretty_string_type(pp, deconstruct_result134)
                _t786 = _t787
            else
                function _t788(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                        _t789 = _get_oneof_field(_dollar_dollar, :int_type)
                    else
                        _t789 = nothing
                    end
                    return _t789
                end
                _t790 = _t788(msg)
                deconstruct_result133 = _t790
                if !isnothing(deconstruct_result133)
                    _t792 = pretty_int_type(pp, deconstruct_result133)
                    _t791 = _t792
                else
                    function _t793(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                            _t794 = _get_oneof_field(_dollar_dollar, :float_type)
                        else
                            _t794 = nothing
                        end
                        return _t794
                    end
                    _t795 = _t793(msg)
                    deconstruct_result132 = _t795
                    if !isnothing(deconstruct_result132)
                        _t797 = pretty_float_type(pp, deconstruct_result132)
                        _t796 = _t797
                    else
                        function _t798(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                                _t799 = _get_oneof_field(_dollar_dollar, :uint128_type)
                            else
                                _t799 = nothing
                            end
                            return _t799
                        end
                        _t800 = _t798(msg)
                        deconstruct_result131 = _t800
                        if !isnothing(deconstruct_result131)
                            _t802 = pretty_uint128_type(pp, deconstruct_result131)
                            _t801 = _t802
                        else
                            function _t803(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                    _t804 = _get_oneof_field(_dollar_dollar, :int128_type)
                                else
                                    _t804 = nothing
                                end
                                return _t804
                            end
                            _t805 = _t803(msg)
                            deconstruct_result130 = _t805
                            if !isnothing(deconstruct_result130)
                                _t807 = pretty_int128_type(pp, deconstruct_result130)
                                _t806 = _t807
                            else
                                function _t808(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                        _t809 = _get_oneof_field(_dollar_dollar, :date_type)
                                    else
                                        _t809 = nothing
                                    end
                                    return _t809
                                end
                                _t810 = _t808(msg)
                                deconstruct_result129 = _t810
                                if !isnothing(deconstruct_result129)
                                    _t812 = pretty_date_type(pp, deconstruct_result129)
                                    _t811 = _t812
                                else
                                    function _t813(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                            _t814 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                        else
                                            _t814 = nothing
                                        end
                                        return _t814
                                    end
                                    _t815 = _t813(msg)
                                    deconstruct_result128 = _t815
                                    if !isnothing(deconstruct_result128)
                                        _t817 = pretty_datetime_type(pp, deconstruct_result128)
                                        _t816 = _t817
                                    else
                                        function _t818(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                                _t819 = _get_oneof_field(_dollar_dollar, :missing_type)
                                            else
                                                _t819 = nothing
                                            end
                                            return _t819
                                        end
                                        _t820 = _t818(msg)
                                        deconstruct_result127 = _t820
                                        if !isnothing(deconstruct_result127)
                                            _t822 = pretty_missing_type(pp, deconstruct_result127)
                                            _t821 = _t822
                                        else
                                            function _t823(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                    _t824 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                                else
                                                    _t824 = nothing
                                                end
                                                return _t824
                                            end
                                            _t825 = _t823(msg)
                                            deconstruct_result126 = _t825
                                            if !isnothing(deconstruct_result126)
                                                _t827 = pretty_decimal_type(pp, deconstruct_result126)
                                                _t826 = _t827
                                            else
                                                function _t828(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                        _t829 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                    else
                                                        _t829 = nothing
                                                    end
                                                    return _t829
                                                end
                                                _t830 = _t828(msg)
                                                deconstruct_result125 = _t830
                                                if !isnothing(deconstruct_result125)
                                                    _t832 = pretty_boolean_type(pp, deconstruct_result125)
                                                    _t831 = _t832
                                                else
                                                    throw(ParseError("No matching rule for type"))
                                                end
                                                _t826 = _t831
                                            end
                                            _t821 = _t826
                                        end
                                        _t816 = _t821
                                    end
                                    _t811 = _t816
                                end
                                _t806 = _t811
                            end
                            _t801 = _t806
                        end
                        _t796 = _t801
                    end
                    _t791 = _t796
                end
                _t786 = _t791
            end
            _t781 = _t786
        end
        _t777 = _t781
    end
    return _t777
end

function pretty_unspecified_type(pp::PrettyPrinter, msg::Proto.UnspecifiedType)
    flat139 = try_flat(pp, msg, pretty_unspecified_type)
    if !isnothing(flat139)
        write(pp, flat139)
        return nothing
    else
        function _t833(_dollar_dollar)
            return _dollar_dollar
        end
        _t834 = _t833(msg)
        fields137 = _t834
        unwrapped_fields138 = fields137
        write(pp, "UNKNOWN")
    end
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    flat142 = try_flat(pp, msg, pretty_string_type)
    if !isnothing(flat142)
        write(pp, flat142)
        return nothing
    else
        function _t835(_dollar_dollar)
            return _dollar_dollar
        end
        _t836 = _t835(msg)
        fields140 = _t836
        unwrapped_fields141 = fields140
        write(pp, "STRING")
    end
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    flat145 = try_flat(pp, msg, pretty_int_type)
    if !isnothing(flat145)
        write(pp, flat145)
        return nothing
    else
        function _t837(_dollar_dollar)
            return _dollar_dollar
        end
        _t838 = _t837(msg)
        fields143 = _t838
        unwrapped_fields144 = fields143
        write(pp, "INT")
    end
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    flat148 = try_flat(pp, msg, pretty_float_type)
    if !isnothing(flat148)
        write(pp, flat148)
        return nothing
    else
        function _t839(_dollar_dollar)
            return _dollar_dollar
        end
        _t840 = _t839(msg)
        fields146 = _t840
        unwrapped_fields147 = fields146
        write(pp, "FLOAT")
    end
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    flat151 = try_flat(pp, msg, pretty_uint128_type)
    if !isnothing(flat151)
        write(pp, flat151)
        return nothing
    else
        function _t841(_dollar_dollar)
            return _dollar_dollar
        end
        _t842 = _t841(msg)
        fields149 = _t842
        unwrapped_fields150 = fields149
        write(pp, "UINT128")
    end
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    flat154 = try_flat(pp, msg, pretty_int128_type)
    if !isnothing(flat154)
        write(pp, flat154)
        return nothing
    else
        function _t843(_dollar_dollar)
            return _dollar_dollar
        end
        _t844 = _t843(msg)
        fields152 = _t844
        unwrapped_fields153 = fields152
        write(pp, "INT128")
    end
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    flat157 = try_flat(pp, msg, pretty_date_type)
    if !isnothing(flat157)
        write(pp, flat157)
        return nothing
    else
        function _t845(_dollar_dollar)
            return _dollar_dollar
        end
        _t846 = _t845(msg)
        fields155 = _t846
        unwrapped_fields156 = fields155
        write(pp, "DATE")
    end
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    flat160 = try_flat(pp, msg, pretty_datetime_type)
    if !isnothing(flat160)
        write(pp, flat160)
        return nothing
    else
        function _t847(_dollar_dollar)
            return _dollar_dollar
        end
        _t848 = _t847(msg)
        fields158 = _t848
        unwrapped_fields159 = fields158
        write(pp, "DATETIME")
    end
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    flat163 = try_flat(pp, msg, pretty_missing_type)
    if !isnothing(flat163)
        write(pp, flat163)
        return nothing
    else
        function _t849(_dollar_dollar)
            return _dollar_dollar
        end
        _t850 = _t849(msg)
        fields161 = _t850
        unwrapped_fields162 = fields161
        write(pp, "MISSING")
    end
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat168 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat168)
        write(pp, flat168)
        return nothing
    else
        function _t851(_dollar_dollar)
            return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        end
        _t852 = _t851(msg)
        fields164 = _t852
        unwrapped_fields165 = fields164
        write(pp, "(")
        write(pp, "DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field166 = unwrapped_fields165[1]
        write(pp, string(field166))
        newline(pp)
        field167 = unwrapped_fields165[2]
        write(pp, string(field167))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    flat171 = try_flat(pp, msg, pretty_boolean_type)
    if !isnothing(flat171)
        write(pp, flat171)
        return nothing
    else
        function _t853(_dollar_dollar)
            return _dollar_dollar
        end
        _t854 = _t853(msg)
        fields169 = _t854
        unwrapped_fields170 = fields169
        write(pp, "BOOLEAN")
    end
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat176 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat176)
        write(pp, flat176)
        return nothing
    else
        function _t855(_dollar_dollar)
            return _dollar_dollar
        end
        _t856 = _t855(msg)
        fields172 = _t856
        unwrapped_fields173 = fields172
        write(pp, "|")
        if !isempty(unwrapped_fields173)
            write(pp, " ")
            for (i857, elem174) in enumerate(unwrapped_fields173)
                i175 = i857 - 1
                if (i175 > 0)
                    newline(pp)
                end
                _t858 = pretty_binding(pp, elem174)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat190 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat190)
        write(pp, flat190)
        return nothing
    else
        function _t860(_dollar_dollar)
            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                _t861 = _get_oneof_field(_dollar_dollar, :conjunction)
            else
                _t861 = nothing
            end
            return _t861
        end
        _t862 = _t860(msg)
        deconstruct_result189 = _t862
        if !isnothing(deconstruct_result189)
            _t864 = pretty_true(pp, deconstruct_result189)
            _t863 = _t864
        else
            function _t865(_dollar_dollar)
                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                    _t866 = _get_oneof_field(_dollar_dollar, :disjunction)
                else
                    _t866 = nothing
                end
                return _t866
            end
            _t867 = _t865(msg)
            deconstruct_result188 = _t867
            if !isnothing(deconstruct_result188)
                _t869 = pretty_false(pp, deconstruct_result188)
                _t868 = _t869
            else
                function _t870(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("exists"))
                        _t871 = _get_oneof_field(_dollar_dollar, :exists)
                    else
                        _t871 = nothing
                    end
                    return _t871
                end
                _t872 = _t870(msg)
                deconstruct_result187 = _t872
                if !isnothing(deconstruct_result187)
                    _t874 = pretty_exists(pp, deconstruct_result187)
                    _t873 = _t874
                else
                    function _t875(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                            _t876 = _get_oneof_field(_dollar_dollar, :reduce)
                        else
                            _t876 = nothing
                        end
                        return _t876
                    end
                    _t877 = _t875(msg)
                    deconstruct_result186 = _t877
                    if !isnothing(deconstruct_result186)
                        _t879 = pretty_reduce(pp, deconstruct_result186)
                        _t878 = _t879
                    else
                        function _t880(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("conjunction"))
                                _t881 = _get_oneof_field(_dollar_dollar, :conjunction)
                            else
                                _t881 = nothing
                            end
                            return _t881
                        end
                        _t882 = _t880(msg)
                        deconstruct_result185 = _t882
                        if !isnothing(deconstruct_result185)
                            _t884 = pretty_conjunction(pp, deconstruct_result185)
                            _t883 = _t884
                        else
                            function _t885(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("disjunction"))
                                    _t886 = _get_oneof_field(_dollar_dollar, :disjunction)
                                else
                                    _t886 = nothing
                                end
                                return _t886
                            end
                            _t887 = _t885(msg)
                            deconstruct_result184 = _t887
                            if !isnothing(deconstruct_result184)
                                _t889 = pretty_disjunction(pp, deconstruct_result184)
                                _t888 = _t889
                            else
                                function _t890(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("not"))
                                        _t891 = _get_oneof_field(_dollar_dollar, :not)
                                    else
                                        _t891 = nothing
                                    end
                                    return _t891
                                end
                                _t892 = _t890(msg)
                                deconstruct_result183 = _t892
                                if !isnothing(deconstruct_result183)
                                    _t894 = pretty_not(pp, deconstruct_result183)
                                    _t893 = _t894
                                else
                                    function _t895(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                            _t896 = _get_oneof_field(_dollar_dollar, :ffi)
                                        else
                                            _t896 = nothing
                                        end
                                        return _t896
                                    end
                                    _t897 = _t895(msg)
                                    deconstruct_result182 = _t897
                                    if !isnothing(deconstruct_result182)
                                        _t899 = pretty_ffi(pp, deconstruct_result182)
                                        _t898 = _t899
                                    else
                                        function _t900(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                                _t901 = _get_oneof_field(_dollar_dollar, :atom)
                                            else
                                                _t901 = nothing
                                            end
                                            return _t901
                                        end
                                        _t902 = _t900(msg)
                                        deconstruct_result181 = _t902
                                        if !isnothing(deconstruct_result181)
                                            _t904 = pretty_atom(pp, deconstruct_result181)
                                            _t903 = _t904
                                        else
                                            function _t905(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                    _t906 = _get_oneof_field(_dollar_dollar, :pragma)
                                                else
                                                    _t906 = nothing
                                                end
                                                return _t906
                                            end
                                            _t907 = _t905(msg)
                                            deconstruct_result180 = _t907
                                            if !isnothing(deconstruct_result180)
                                                _t909 = pretty_pragma(pp, deconstruct_result180)
                                                _t908 = _t909
                                            else
                                                function _t910(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                        _t911 = _get_oneof_field(_dollar_dollar, :primitive)
                                                    else
                                                        _t911 = nothing
                                                    end
                                                    return _t911
                                                end
                                                _t912 = _t910(msg)
                                                deconstruct_result179 = _t912
                                                if !isnothing(deconstruct_result179)
                                                    _t914 = pretty_primitive(pp, deconstruct_result179)
                                                    _t913 = _t914
                                                else
                                                    function _t915(_dollar_dollar)
                                                        if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                            _t916 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                        else
                                                            _t916 = nothing
                                                        end
                                                        return _t916
                                                    end
                                                    _t917 = _t915(msg)
                                                    deconstruct_result178 = _t917
                                                    if !isnothing(deconstruct_result178)
                                                        _t919 = pretty_rel_atom(pp, deconstruct_result178)
                                                        _t918 = _t919
                                                    else
                                                        function _t920(_dollar_dollar)
                                                            if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                                _t921 = _get_oneof_field(_dollar_dollar, :cast)
                                                            else
                                                                _t921 = nothing
                                                            end
                                                            return _t921
                                                        end
                                                        _t922 = _t920(msg)
                                                        deconstruct_result177 = _t922
                                                        if !isnothing(deconstruct_result177)
                                                            _t924 = pretty_cast(pp, deconstruct_result177)
                                                            _t923 = _t924
                                                        else
                                                            throw(ParseError("No matching rule for formula"))
                                                        end
                                                        _t918 = _t923
                                                    end
                                                    _t913 = _t918
                                                end
                                                _t908 = _t913
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
            _t863 = _t868
        end
        _t859 = _t863
    end
    return _t859
end

function pretty_true(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat193 = try_flat(pp, msg, pretty_true)
    if !isnothing(flat193)
        write(pp, flat193)
        return nothing
    else
        function _t925(_dollar_dollar)
            return _dollar_dollar
        end
        _t926 = _t925(msg)
        fields191 = _t926
        unwrapped_fields192 = fields191
        write(pp, "(")
        write(pp, "true")
        write(pp, ")")
    end
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat196 = try_flat(pp, msg, pretty_false)
    if !isnothing(flat196)
        write(pp, flat196)
        return nothing
    else
        function _t927(_dollar_dollar)
            return _dollar_dollar
        end
        _t928 = _t927(msg)
        fields194 = _t928
        unwrapped_fields195 = fields194
        write(pp, "(")
        write(pp, "false")
        write(pp, ")")
    end
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat201 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat201)
        write(pp, flat201)
        return nothing
    else
        function _t929(_dollar_dollar)
            _t930 = deconstruct_bindings(pp, _dollar_dollar.body)
            return (_t930, _dollar_dollar.body.value,)
        end
        _t931 = _t929(msg)
        fields197 = _t931
        unwrapped_fields198 = fields197
        write(pp, "(")
        write(pp, "exists")
        indent_sexp!(pp)
        newline(pp)
        field199 = unwrapped_fields198[1]
        _t932 = pretty_bindings(pp, field199)
        newline(pp)
        field200 = unwrapped_fields198[2]
        _t933 = pretty_formula(pp, field200)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat207 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat207)
        write(pp, flat207)
        return nothing
    else
        function _t934(_dollar_dollar)
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        end
        _t935 = _t934(msg)
        fields202 = _t935
        unwrapped_fields203 = fields202
        write(pp, "(")
        write(pp, "reduce")
        indent_sexp!(pp)
        newline(pp)
        field204 = unwrapped_fields203[1]
        _t936 = pretty_abstraction(pp, field204)
        newline(pp)
        field205 = unwrapped_fields203[2]
        _t937 = pretty_abstraction(pp, field205)
        newline(pp)
        field206 = unwrapped_fields203[3]
        _t938 = pretty_terms(pp, field206)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat212 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat212)
        write(pp, flat212)
        return nothing
    else
        function _t939(_dollar_dollar)
            return _dollar_dollar
        end
        _t940 = _t939(msg)
        fields208 = _t940
        unwrapped_fields209 = fields208
        write(pp, "(")
        write(pp, "terms")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields209)
            newline(pp)
            for (i941, elem210) in enumerate(unwrapped_fields209)
                i211 = i941 - 1
                if (i211 > 0)
                    newline(pp)
                end
                _t942 = pretty_term(pp, elem210)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat215 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat215)
        write(pp, flat215)
        return nothing
    else
        function _t944(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("var"))
                _t945 = _get_oneof_field(_dollar_dollar, :var)
            else
                _t945 = nothing
            end
            return _t945
        end
        _t946 = _t944(msg)
        deconstruct_result214 = _t946
        if !isnothing(deconstruct_result214)
            _t948 = pretty_var(pp, deconstruct_result214)
            _t947 = _t948
        else
            function _t949(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("constant"))
                    _t950 = _get_oneof_field(_dollar_dollar, :constant)
                else
                    _t950 = nothing
                end
                return _t950
            end
            _t951 = _t949(msg)
            deconstruct_result213 = _t951
            if !isnothing(deconstruct_result213)
                _t953 = pretty_constant(pp, deconstruct_result213)
                _t952 = _t953
            else
                throw(ParseError("No matching rule for term"))
            end
            _t947 = _t952
        end
        _t943 = _t947
    end
    return _t943
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat218 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat218)
        write(pp, flat218)
        return nothing
    else
        function _t954(_dollar_dollar)
            return _dollar_dollar.name
        end
        _t955 = _t954(msg)
        fields216 = _t955
        unwrapped_fields217 = fields216
        write(pp, unwrapped_fields217)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat221 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat221)
        write(pp, flat221)
        return nothing
    else
        function _t957(_dollar_dollar)
            return _dollar_dollar
        end
        _t958 = _t957(msg)
        fields219 = _t958
        unwrapped_fields220 = fields219
        _t959 = pretty_value(pp, unwrapped_fields220)
        _t956 = _t959
    end
    return _t956
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat226 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat226)
        write(pp, flat226)
        return nothing
    else
        function _t960(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t961 = _t960(msg)
        fields222 = _t961
        unwrapped_fields223 = fields222
        write(pp, "(")
        write(pp, "and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields223)
            newline(pp)
            for (i962, elem224) in enumerate(unwrapped_fields223)
                i225 = i962 - 1
                if (i225 > 0)
                    newline(pp)
                end
                _t963 = pretty_formula(pp, elem224)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat231 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat231)
        write(pp, flat231)
        return nothing
    else
        function _t964(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t965 = _t964(msg)
        fields227 = _t965
        unwrapped_fields228 = fields227
        write(pp, "(")
        write(pp, "or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields228)
            newline(pp)
            for (i966, elem229) in enumerate(unwrapped_fields228)
                i230 = i966 - 1
                if (i230 > 0)
                    newline(pp)
                end
                _t967 = pretty_formula(pp, elem229)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat234 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat234)
        write(pp, flat234)
        return nothing
    else
        function _t968(_dollar_dollar)
            return _dollar_dollar.arg
        end
        _t969 = _t968(msg)
        fields232 = _t969
        unwrapped_fields233 = fields232
        write(pp, "(")
        write(pp, "not")
        indent_sexp!(pp)
        newline(pp)
        _t970 = pretty_formula(pp, unwrapped_fields233)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat240 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat240)
        write(pp, flat240)
        return nothing
    else
        function _t971(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        end
        _t972 = _t971(msg)
        fields235 = _t972
        unwrapped_fields236 = fields235
        write(pp, "(")
        write(pp, "ffi")
        indent_sexp!(pp)
        newline(pp)
        field237 = unwrapped_fields236[1]
        _t973 = pretty_name(pp, field237)
        newline(pp)
        field238 = unwrapped_fields236[2]
        _t974 = pretty_ffi_args(pp, field238)
        newline(pp)
        field239 = unwrapped_fields236[3]
        _t975 = pretty_terms(pp, field239)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat243 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat243)
        write(pp, flat243)
        return nothing
    else
        function _t976(_dollar_dollar)
            return _dollar_dollar
        end
        _t977 = _t976(msg)
        fields241 = _t977
        unwrapped_fields242 = fields241
        write(pp, ":")
        write(pp, unwrapped_fields242)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat248 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat248)
        write(pp, flat248)
        return nothing
    else
        function _t978(_dollar_dollar)
            return _dollar_dollar
        end
        _t979 = _t978(msg)
        fields244 = _t979
        unwrapped_fields245 = fields244
        write(pp, "(")
        write(pp, "args")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields245)
            newline(pp)
            for (i980, elem246) in enumerate(unwrapped_fields245)
                i247 = i980 - 1
                if (i247 > 0)
                    newline(pp)
                end
                _t981 = pretty_abstraction(pp, elem246)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat255 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat255)
        write(pp, flat255)
        return nothing
    else
        function _t982(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t983 = _t982(msg)
        fields249 = _t983
        unwrapped_fields250 = fields249
        write(pp, "(")
        write(pp, "atom")
        indent_sexp!(pp)
        newline(pp)
        field251 = unwrapped_fields250[1]
        _t984 = pretty_relation_id(pp, field251)
        field252 = unwrapped_fields250[2]
        if !isempty(field252)
            newline(pp)
            for (i985, elem253) in enumerate(field252)
                i254 = i985 - 1
                if (i254 > 0)
                    newline(pp)
                end
                _t986 = pretty_term(pp, elem253)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat262 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat262)
        write(pp, flat262)
        return nothing
    else
        function _t987(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t988 = _t987(msg)
        fields256 = _t988
        unwrapped_fields257 = fields256
        write(pp, "(")
        write(pp, "pragma")
        indent_sexp!(pp)
        newline(pp)
        field258 = unwrapped_fields257[1]
        _t989 = pretty_name(pp, field258)
        field259 = unwrapped_fields257[2]
        if !isempty(field259)
            newline(pp)
            for (i990, elem260) in enumerate(field259)
                i261 = i990 - 1
                if (i261 > 0)
                    newline(pp)
                end
                _t991 = pretty_term(pp, elem260)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat278 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat278)
        write(pp, flat278)
        return nothing
    else
        function _t993(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t994 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t994 = nothing
            end
            return _t994
        end
        _t995 = _t993(msg)
        guard_result277 = _t995
        if !isnothing(guard_result277)
            _t997 = pretty_eq(pp, msg)
            _t996 = _t997
        else
            function _t998(_dollar_dollar)
                if _dollar_dollar.name == "rel_primitive_lt_monotype"
                    _t999 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t999 = nothing
                end
                return _t999
            end
            _t1000 = _t998(msg)
            guard_result276 = _t1000
            if !isnothing(guard_result276)
                _t1002 = pretty_lt(pp, msg)
                _t1001 = _t1002
            else
                function _t1003(_dollar_dollar)
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                        _t1004 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1004 = nothing
                    end
                    return _t1004
                end
                _t1005 = _t1003(msg)
                guard_result275 = _t1005
                if !isnothing(guard_result275)
                    _t1007 = pretty_lt_eq(pp, msg)
                    _t1006 = _t1007
                else
                    function _t1008(_dollar_dollar)
                        if _dollar_dollar.name == "rel_primitive_gt_monotype"
                            _t1009 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1009 = nothing
                        end
                        return _t1009
                    end
                    _t1010 = _t1008(msg)
                    guard_result274 = _t1010
                    if !isnothing(guard_result274)
                        _t1012 = pretty_gt(pp, msg)
                        _t1011 = _t1012
                    else
                        function _t1013(_dollar_dollar)
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                                _t1014 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                            else
                                _t1014 = nothing
                            end
                            return _t1014
                        end
                        _t1015 = _t1013(msg)
                        guard_result273 = _t1015
                        if !isnothing(guard_result273)
                            _t1017 = pretty_gt_eq(pp, msg)
                            _t1016 = _t1017
                        else
                            function _t1018(_dollar_dollar)
                                if _dollar_dollar.name == "rel_primitive_add_monotype"
                                    _t1019 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1019 = nothing
                                end
                                return _t1019
                            end
                            _t1020 = _t1018(msg)
                            guard_result272 = _t1020
                            if !isnothing(guard_result272)
                                _t1022 = pretty_add(pp, msg)
                                _t1021 = _t1022
                            else
                                function _t1023(_dollar_dollar)
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                        _t1024 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1024 = nothing
                                    end
                                    return _t1024
                                end
                                _t1025 = _t1023(msg)
                                guard_result271 = _t1025
                                if !isnothing(guard_result271)
                                    _t1027 = pretty_minus(pp, msg)
                                    _t1026 = _t1027
                                else
                                    function _t1028(_dollar_dollar)
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                            _t1029 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1029 = nothing
                                        end
                                        return _t1029
                                    end
                                    _t1030 = _t1028(msg)
                                    guard_result270 = _t1030
                                    if !isnothing(guard_result270)
                                        _t1032 = pretty_multiply(pp, msg)
                                        _t1031 = _t1032
                                    else
                                        function _t1033(_dollar_dollar)
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                                _t1034 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                            else
                                                _t1034 = nothing
                                            end
                                            return _t1034
                                        end
                                        _t1035 = _t1033(msg)
                                        guard_result269 = _t1035
                                        if !isnothing(guard_result269)
                                            _t1037 = pretty_divide(pp, msg)
                                            _t1036 = _t1037
                                        else
                                            function _t1038(_dollar_dollar)
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            end
                                            _t1039 = _t1038(msg)
                                            fields263 = _t1039
                                            unwrapped_fields264 = fields263
                                            write(pp, "(")
                                            write(pp, "primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field265 = unwrapped_fields264[1]
                                            _t1040 = pretty_name(pp, field265)
                                            field266 = unwrapped_fields264[2]
                                            if !isempty(field266)
                                                newline(pp)
                                                for (i1041, elem267) in enumerate(field266)
                                                    i268 = i1041 - 1
                                                    if (i268 > 0)
                                                        newline(pp)
                                                    end
                                                    _t1042 = pretty_rel_term(pp, elem267)
                                                end
                                            end
                                            dedent!(pp)
                                            write(pp, ")")
                                            _t1036 = nothing
                                        end
                                        _t1031 = _t1036
                                    end
                                    _t1026 = _t1031
                                end
                                _t1021 = _t1026
                            end
                            _t1016 = _t1021
                        end
                        _t1011 = _t1016
                    end
                    _t1006 = _t1011
                end
                _t1001 = _t1006
            end
            _t996 = _t1001
        end
        _t992 = _t996
    end
    return _t992
end

function pretty_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat283 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat283)
        write(pp, flat283)
        return nothing
    else
        function _t1043(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1044 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1044 = nothing
            end
            return _t1044
        end
        _t1045 = _t1043(msg)
        fields279 = _t1045
        unwrapped_fields280 = fields279
        write(pp, "(")
        write(pp, "=")
        indent_sexp!(pp)
        newline(pp)
        field281 = unwrapped_fields280[1]
        _t1046 = pretty_term(pp, field281)
        newline(pp)
        field282 = unwrapped_fields280[2]
        _t1047 = pretty_term(pp, field282)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat288 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat288)
        write(pp, flat288)
        return nothing
    else
        function _t1048(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1049 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1049 = nothing
            end
            return _t1049
        end
        _t1050 = _t1048(msg)
        fields284 = _t1050
        unwrapped_fields285 = fields284
        write(pp, "(")
        write(pp, "<")
        indent_sexp!(pp)
        newline(pp)
        field286 = unwrapped_fields285[1]
        _t1051 = pretty_term(pp, field286)
        newline(pp)
        field287 = unwrapped_fields285[2]
        _t1052 = pretty_term(pp, field287)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat293 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat293)
        write(pp, flat293)
        return nothing
    else
        function _t1053(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                _t1054 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1054 = nothing
            end
            return _t1054
        end
        _t1055 = _t1053(msg)
        fields289 = _t1055
        unwrapped_fields290 = fields289
        write(pp, "(")
        write(pp, "<=")
        indent_sexp!(pp)
        newline(pp)
        field291 = unwrapped_fields290[1]
        _t1056 = pretty_term(pp, field291)
        newline(pp)
        field292 = unwrapped_fields290[2]
        _t1057 = pretty_term(pp, field292)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat298 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat298)
        write(pp, flat298)
        return nothing
    else
        function _t1058(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_monotype"
                _t1059 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1059 = nothing
            end
            return _t1059
        end
        _t1060 = _t1058(msg)
        fields294 = _t1060
        unwrapped_fields295 = fields294
        write(pp, "(")
        write(pp, ">")
        indent_sexp!(pp)
        newline(pp)
        field296 = unwrapped_fields295[1]
        _t1061 = pretty_term(pp, field296)
        newline(pp)
        field297 = unwrapped_fields295[2]
        _t1062 = pretty_term(pp, field297)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat303 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat303)
        write(pp, flat303)
        return nothing
    else
        function _t1063(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                _t1064 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1064 = nothing
            end
            return _t1064
        end
        _t1065 = _t1063(msg)
        fields299 = _t1065
        unwrapped_fields300 = fields299
        write(pp, "(")
        write(pp, ">=")
        indent_sexp!(pp)
        newline(pp)
        field301 = unwrapped_fields300[1]
        _t1066 = pretty_term(pp, field301)
        newline(pp)
        field302 = unwrapped_fields300[2]
        _t1067 = pretty_term(pp, field302)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat309 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat309)
        write(pp, flat309)
        return nothing
    else
        function _t1068(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_add_monotype"
                _t1069 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1069 = nothing
            end
            return _t1069
        end
        _t1070 = _t1068(msg)
        fields304 = _t1070
        unwrapped_fields305 = fields304
        write(pp, "(")
        write(pp, "+")
        indent_sexp!(pp)
        newline(pp)
        field306 = unwrapped_fields305[1]
        _t1071 = pretty_term(pp, field306)
        newline(pp)
        field307 = unwrapped_fields305[2]
        _t1072 = pretty_term(pp, field307)
        newline(pp)
        field308 = unwrapped_fields305[3]
        _t1073 = pretty_term(pp, field308)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat315 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat315)
        write(pp, flat315)
        return nothing
    else
        function _t1074(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                _t1075 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1075 = nothing
            end
            return _t1075
        end
        _t1076 = _t1074(msg)
        fields310 = _t1076
        unwrapped_fields311 = fields310
        write(pp, "(")
        write(pp, "-")
        indent_sexp!(pp)
        newline(pp)
        field312 = unwrapped_fields311[1]
        _t1077 = pretty_term(pp, field312)
        newline(pp)
        field313 = unwrapped_fields311[2]
        _t1078 = pretty_term(pp, field313)
        newline(pp)
        field314 = unwrapped_fields311[3]
        _t1079 = pretty_term(pp, field314)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat321 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat321)
        write(pp, flat321)
        return nothing
    else
        function _t1080(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                _t1081 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1081 = nothing
            end
            return _t1081
        end
        _t1082 = _t1080(msg)
        fields316 = _t1082
        unwrapped_fields317 = fields316
        write(pp, "(")
        write(pp, "*")
        indent_sexp!(pp)
        newline(pp)
        field318 = unwrapped_fields317[1]
        _t1083 = pretty_term(pp, field318)
        newline(pp)
        field319 = unwrapped_fields317[2]
        _t1084 = pretty_term(pp, field319)
        newline(pp)
        field320 = unwrapped_fields317[3]
        _t1085 = pretty_term(pp, field320)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat327 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat327)
        write(pp, flat327)
        return nothing
    else
        function _t1086(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                _t1087 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1087 = nothing
            end
            return _t1087
        end
        _t1088 = _t1086(msg)
        fields322 = _t1088
        unwrapped_fields323 = fields322
        write(pp, "(")
        write(pp, "/")
        indent_sexp!(pp)
        newline(pp)
        field324 = unwrapped_fields323[1]
        _t1089 = pretty_term(pp, field324)
        newline(pp)
        field325 = unwrapped_fields323[2]
        _t1090 = pretty_term(pp, field325)
        newline(pp)
        field326 = unwrapped_fields323[3]
        _t1091 = pretty_term(pp, field326)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat330 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat330)
        write(pp, flat330)
        return nothing
    else
        function _t1093(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
                _t1094 = _get_oneof_field(_dollar_dollar, :specialized_value)
            else
                _t1094 = nothing
            end
            return _t1094
        end
        _t1095 = _t1093(msg)
        deconstruct_result329 = _t1095
        if !isnothing(deconstruct_result329)
            _t1097 = pretty_specialized_value(pp, deconstruct_result329)
            _t1096 = _t1097
        else
            function _t1098(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("term"))
                    _t1099 = _get_oneof_field(_dollar_dollar, :term)
                else
                    _t1099 = nothing
                end
                return _t1099
            end
            _t1100 = _t1098(msg)
            deconstruct_result328 = _t1100
            if !isnothing(deconstruct_result328)
                _t1102 = pretty_term(pp, deconstruct_result328)
                _t1101 = _t1102
            else
                throw(ParseError("No matching rule for rel_term"))
            end
            _t1096 = _t1101
        end
        _t1092 = _t1096
    end
    return _t1092
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat333 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat333)
        write(pp, flat333)
        return nothing
    else
        function _t1104(_dollar_dollar)
            return _dollar_dollar
        end
        _t1105 = _t1104(msg)
        fields331 = _t1105
        unwrapped_fields332 = fields331
        write(pp, "#")
        _t1106 = pretty_value(pp, unwrapped_fields332)
        _t1103 = _t1106
    end
    return _t1103
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat340 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat340)
        write(pp, flat340)
        return nothing
    else
        function _t1107(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1108 = _t1107(msg)
        fields334 = _t1108
        unwrapped_fields335 = fields334
        write(pp, "(")
        write(pp, "relatom")
        indent_sexp!(pp)
        newline(pp)
        field336 = unwrapped_fields335[1]
        _t1109 = pretty_name(pp, field336)
        field337 = unwrapped_fields335[2]
        if !isempty(field337)
            newline(pp)
            for (i1110, elem338) in enumerate(field337)
                i339 = i1110 - 1
                if (i339 > 0)
                    newline(pp)
                end
                _t1111 = pretty_rel_term(pp, elem338)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat345 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat345)
        write(pp, flat345)
        return nothing
    else
        function _t1112(_dollar_dollar)
            return (_dollar_dollar.input, _dollar_dollar.result,)
        end
        _t1113 = _t1112(msg)
        fields341 = _t1113
        unwrapped_fields342 = fields341
        write(pp, "(")
        write(pp, "cast")
        indent_sexp!(pp)
        newline(pp)
        field343 = unwrapped_fields342[1]
        _t1114 = pretty_term(pp, field343)
        newline(pp)
        field344 = unwrapped_fields342[2]
        _t1115 = pretty_term(pp, field344)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat350 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat350)
        write(pp, flat350)
        return nothing
    else
        function _t1116(_dollar_dollar)
            return _dollar_dollar
        end
        _t1117 = _t1116(msg)
        fields346 = _t1117
        unwrapped_fields347 = fields346
        write(pp, "(")
        write(pp, "attrs")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields347)
            newline(pp)
            for (i1118, elem348) in enumerate(unwrapped_fields347)
                i349 = i1118 - 1
                if (i349 > 0)
                    newline(pp)
                end
                _t1119 = pretty_attribute(pp, elem348)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat357 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat357)
        write(pp, flat357)
        return nothing
    else
        function _t1120(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args,)
        end
        _t1121 = _t1120(msg)
        fields351 = _t1121
        unwrapped_fields352 = fields351
        write(pp, "(")
        write(pp, "attribute")
        indent_sexp!(pp)
        newline(pp)
        field353 = unwrapped_fields352[1]
        _t1122 = pretty_name(pp, field353)
        field354 = unwrapped_fields352[2]
        if !isempty(field354)
            newline(pp)
            for (i1123, elem355) in enumerate(field354)
                i356 = i1123 - 1
                if (i356 > 0)
                    newline(pp)
                end
                _t1124 = pretty_value(pp, elem355)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat364 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat364)
        write(pp, flat364)
        return nothing
    else
        function _t1125(_dollar_dollar)
            return (_dollar_dollar.var"#global", _dollar_dollar.body,)
        end
        _t1126 = _t1125(msg)
        fields358 = _t1126
        unwrapped_fields359 = fields358
        write(pp, "(")
        write(pp, "algorithm")
        indent_sexp!(pp)
        field360 = unwrapped_fields359[1]
        if !isempty(field360)
            newline(pp)
            for (i1127, elem361) in enumerate(field360)
                i362 = i1127 - 1
                if (i362 > 0)
                    newline(pp)
                end
                _t1128 = pretty_relation_id(pp, elem361)
            end
        end
        newline(pp)
        field363 = unwrapped_fields359[2]
        _t1129 = pretty_script(pp, field363)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat369 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat369)
        write(pp, flat369)
        return nothing
    else
        function _t1130(_dollar_dollar)
            return _dollar_dollar.constructs
        end
        _t1131 = _t1130(msg)
        fields365 = _t1131
        unwrapped_fields366 = fields365
        write(pp, "(")
        write(pp, "script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields366)
            newline(pp)
            for (i1132, elem367) in enumerate(unwrapped_fields366)
                i368 = i1132 - 1
                if (i368 > 0)
                    newline(pp)
                end
                _t1133 = pretty_construct(pp, elem367)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat372 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat372)
        write(pp, flat372)
        return nothing
    else
        function _t1135(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("loop"))
                _t1136 = _get_oneof_field(_dollar_dollar, :loop)
            else
                _t1136 = nothing
            end
            return _t1136
        end
        _t1137 = _t1135(msg)
        deconstruct_result371 = _t1137
        if !isnothing(deconstruct_result371)
            _t1139 = pretty_loop(pp, deconstruct_result371)
            _t1138 = _t1139
        else
            function _t1140(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                    _t1141 = _get_oneof_field(_dollar_dollar, :instruction)
                else
                    _t1141 = nothing
                end
                return _t1141
            end
            _t1142 = _t1140(msg)
            deconstruct_result370 = _t1142
            if !isnothing(deconstruct_result370)
                _t1144 = pretty_instruction(pp, deconstruct_result370)
                _t1143 = _t1144
            else
                throw(ParseError("No matching rule for construct"))
            end
            _t1138 = _t1143
        end
        _t1134 = _t1138
    end
    return _t1134
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat377 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat377)
        write(pp, flat377)
        return nothing
    else
        function _t1145(_dollar_dollar)
            return (_dollar_dollar.init, _dollar_dollar.body,)
        end
        _t1146 = _t1145(msg)
        fields373 = _t1146
        unwrapped_fields374 = fields373
        write(pp, "(")
        write(pp, "loop")
        indent_sexp!(pp)
        newline(pp)
        field375 = unwrapped_fields374[1]
        _t1147 = pretty_init(pp, field375)
        newline(pp)
        field376 = unwrapped_fields374[2]
        _t1148 = pretty_script(pp, field376)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat382 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat382)
        write(pp, flat382)
        return nothing
    else
        function _t1149(_dollar_dollar)
            return _dollar_dollar
        end
        _t1150 = _t1149(msg)
        fields378 = _t1150
        unwrapped_fields379 = fields378
        write(pp, "(")
        write(pp, "init")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields379)
            newline(pp)
            for (i1151, elem380) in enumerate(unwrapped_fields379)
                i381 = i1151 - 1
                if (i381 > 0)
                    newline(pp)
                end
                _t1152 = pretty_instruction(pp, elem380)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat388 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat388)
        write(pp, flat388)
        return nothing
    else
        function _t1154(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("assign"))
                _t1155 = _get_oneof_field(_dollar_dollar, :assign)
            else
                _t1155 = nothing
            end
            return _t1155
        end
        _t1156 = _t1154(msg)
        deconstruct_result387 = _t1156
        if !isnothing(deconstruct_result387)
            _t1158 = pretty_assign(pp, deconstruct_result387)
            _t1157 = _t1158
        else
            function _t1159(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                    _t1160 = _get_oneof_field(_dollar_dollar, :upsert)
                else
                    _t1160 = nothing
                end
                return _t1160
            end
            _t1161 = _t1159(msg)
            deconstruct_result386 = _t1161
            if !isnothing(deconstruct_result386)
                _t1163 = pretty_upsert(pp, deconstruct_result386)
                _t1162 = _t1163
            else
                function _t1164(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("#break"))
                        _t1165 = _get_oneof_field(_dollar_dollar, :var"#break")
                    else
                        _t1165 = nothing
                    end
                    return _t1165
                end
                _t1166 = _t1164(msg)
                deconstruct_result385 = _t1166
                if !isnothing(deconstruct_result385)
                    _t1168 = pretty_break(pp, deconstruct_result385)
                    _t1167 = _t1168
                else
                    function _t1169(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                            _t1170 = _get_oneof_field(_dollar_dollar, :monoid_def)
                        else
                            _t1170 = nothing
                        end
                        return _t1170
                    end
                    _t1171 = _t1169(msg)
                    deconstruct_result384 = _t1171
                    if !isnothing(deconstruct_result384)
                        _t1173 = pretty_monoid_def(pp, deconstruct_result384)
                        _t1172 = _t1173
                    else
                        function _t1174(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                                _t1175 = _get_oneof_field(_dollar_dollar, :monus_def)
                            else
                                _t1175 = nothing
                            end
                            return _t1175
                        end
                        _t1176 = _t1174(msg)
                        deconstruct_result383 = _t1176
                        if !isnothing(deconstruct_result383)
                            _t1178 = pretty_monus_def(pp, deconstruct_result383)
                            _t1177 = _t1178
                        else
                            throw(ParseError("No matching rule for instruction"))
                        end
                        _t1172 = _t1177
                    end
                    _t1167 = _t1172
                end
                _t1162 = _t1167
            end
            _t1157 = _t1162
        end
        _t1153 = _t1157
    end
    return _t1153
end

function pretty_assign(pp::PrettyPrinter, msg::Proto.Assign)
    flat395 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat395)
        write(pp, flat395)
        return nothing
    else
        function _t1179(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1180 = _dollar_dollar.attrs
            else
                _t1180 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1180,)
        end
        _t1181 = _t1179(msg)
        fields389 = _t1181
        unwrapped_fields390 = fields389
        write(pp, "(")
        write(pp, "assign")
        indent_sexp!(pp)
        newline(pp)
        field391 = unwrapped_fields390[1]
        _t1182 = pretty_relation_id(pp, field391)
        newline(pp)
        field392 = unwrapped_fields390[2]
        _t1183 = pretty_abstraction(pp, field392)
        field393 = unwrapped_fields390[3]
        if !isnothing(field393)
            newline(pp)
            opt_val394 = field393
            _t1185 = pretty_attrs(pp, opt_val394)
            _t1184 = _t1185
        else
            _t1184 = nothing
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat402 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat402)
        write(pp, flat402)
        return nothing
    else
        function _t1186(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1187 = _dollar_dollar.attrs
            else
                _t1187 = nothing
            end
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1187,)
        end
        _t1188 = _t1186(msg)
        fields396 = _t1188
        unwrapped_fields397 = fields396
        write(pp, "(")
        write(pp, "upsert")
        indent_sexp!(pp)
        newline(pp)
        field398 = unwrapped_fields397[1]
        _t1189 = pretty_relation_id(pp, field398)
        newline(pp)
        field399 = unwrapped_fields397[2]
        _t1190 = pretty_abstraction_with_arity(pp, field399)
        field400 = unwrapped_fields397[3]
        if !isnothing(field400)
            newline(pp)
            opt_val401 = field400
            _t1192 = pretty_attrs(pp, opt_val401)
            _t1191 = _t1192
        else
            _t1191 = nothing
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat407 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat407)
        write(pp, flat407)
        return nothing
    else
        function _t1193(_dollar_dollar)
            _t1194 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
            return (_t1194, _dollar_dollar[1].value,)
        end
        _t1195 = _t1193(msg)
        fields403 = _t1195
        unwrapped_fields404 = fields403
        write(pp, "(")
        indent!(pp)
        field405 = unwrapped_fields404[1]
        _t1196 = pretty_bindings(pp, field405)
        newline(pp)
        field406 = unwrapped_fields404[2]
        _t1197 = pretty_formula(pp, field406)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat414 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat414)
        write(pp, flat414)
        return nothing
    else
        function _t1198(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1199 = _dollar_dollar.attrs
            else
                _t1199 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1199,)
        end
        _t1200 = _t1198(msg)
        fields408 = _t1200
        unwrapped_fields409 = fields408
        write(pp, "(")
        write(pp, "break")
        indent_sexp!(pp)
        newline(pp)
        field410 = unwrapped_fields409[1]
        _t1201 = pretty_relation_id(pp, field410)
        newline(pp)
        field411 = unwrapped_fields409[2]
        _t1202 = pretty_abstraction(pp, field411)
        field412 = unwrapped_fields409[3]
        if !isnothing(field412)
            newline(pp)
            opt_val413 = field412
            _t1204 = pretty_attrs(pp, opt_val413)
            _t1203 = _t1204
        else
            _t1203 = nothing
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat422 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat422)
        write(pp, flat422)
        return nothing
    else
        function _t1205(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1206 = _dollar_dollar.attrs
            else
                _t1206 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1206,)
        end
        _t1207 = _t1205(msg)
        fields415 = _t1207
        unwrapped_fields416 = fields415
        write(pp, "(")
        write(pp, "monoid")
        indent_sexp!(pp)
        newline(pp)
        field417 = unwrapped_fields416[1]
        _t1208 = pretty_monoid(pp, field417)
        newline(pp)
        field418 = unwrapped_fields416[2]
        _t1209 = pretty_relation_id(pp, field418)
        newline(pp)
        field419 = unwrapped_fields416[3]
        _t1210 = pretty_abstraction_with_arity(pp, field419)
        field420 = unwrapped_fields416[4]
        if !isnothing(field420)
            newline(pp)
            opt_val421 = field420
            _t1212 = pretty_attrs(pp, opt_val421)
            _t1211 = _t1212
        else
            _t1211 = nothing
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat427 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat427)
        write(pp, flat427)
        return nothing
    else
        function _t1214(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
                _t1215 = _get_oneof_field(_dollar_dollar, :or_monoid)
            else
                _t1215 = nothing
            end
            return _t1215
        end
        _t1216 = _t1214(msg)
        deconstruct_result426 = _t1216
        if !isnothing(deconstruct_result426)
            _t1218 = pretty_or_monoid(pp, deconstruct_result426)
            _t1217 = _t1218
        else
            function _t1219(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                    _t1220 = _get_oneof_field(_dollar_dollar, :min_monoid)
                else
                    _t1220 = nothing
                end
                return _t1220
            end
            _t1221 = _t1219(msg)
            deconstruct_result425 = _t1221
            if !isnothing(deconstruct_result425)
                _t1223 = pretty_min_monoid(pp, deconstruct_result425)
                _t1222 = _t1223
            else
                function _t1224(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                        _t1225 = _get_oneof_field(_dollar_dollar, :max_monoid)
                    else
                        _t1225 = nothing
                    end
                    return _t1225
                end
                _t1226 = _t1224(msg)
                deconstruct_result424 = _t1226
                if !isnothing(deconstruct_result424)
                    _t1228 = pretty_max_monoid(pp, deconstruct_result424)
                    _t1227 = _t1228
                else
                    function _t1229(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                            _t1230 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                        else
                            _t1230 = nothing
                        end
                        return _t1230
                    end
                    _t1231 = _t1229(msg)
                    deconstruct_result423 = _t1231
                    if !isnothing(deconstruct_result423)
                        _t1233 = pretty_sum_monoid(pp, deconstruct_result423)
                        _t1232 = _t1233
                    else
                        throw(ParseError("No matching rule for monoid"))
                    end
                    _t1227 = _t1232
                end
                _t1222 = _t1227
            end
            _t1217 = _t1222
        end
        _t1213 = _t1217
    end
    return _t1213
end

function pretty_or_monoid(pp::PrettyPrinter, msg::Proto.OrMonoid)
    flat430 = try_flat(pp, msg, pretty_or_monoid)
    if !isnothing(flat430)
        write(pp, flat430)
        return nothing
    else
        function _t1234(_dollar_dollar)
            return _dollar_dollar
        end
        _t1235 = _t1234(msg)
        fields428 = _t1235
        unwrapped_fields429 = fields428
        write(pp, "(")
        write(pp, "or")
        write(pp, ")")
    end
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat433 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat433)
        write(pp, flat433)
        return nothing
    else
        function _t1236(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1237 = _t1236(msg)
        fields431 = _t1237
        unwrapped_fields432 = fields431
        write(pp, "(")
        write(pp, "min")
        indent_sexp!(pp)
        newline(pp)
        _t1238 = pretty_type(pp, unwrapped_fields432)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat436 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat436)
        write(pp, flat436)
        return nothing
    else
        function _t1239(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1240 = _t1239(msg)
        fields434 = _t1240
        unwrapped_fields435 = fields434
        write(pp, "(")
        write(pp, "max")
        indent_sexp!(pp)
        newline(pp)
        _t1241 = pretty_type(pp, unwrapped_fields435)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat439 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat439)
        write(pp, flat439)
        return nothing
    else
        function _t1242(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1243 = _t1242(msg)
        fields437 = _t1243
        unwrapped_fields438 = fields437
        write(pp, "(")
        write(pp, "sum")
        indent_sexp!(pp)
        newline(pp)
        _t1244 = pretty_type(pp, unwrapped_fields438)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat447 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat447)
        write(pp, flat447)
        return nothing
    else
        function _t1245(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1246 = _dollar_dollar.attrs
            else
                _t1246 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1246,)
        end
        _t1247 = _t1245(msg)
        fields440 = _t1247
        unwrapped_fields441 = fields440
        write(pp, "(")
        write(pp, "monus")
        indent_sexp!(pp)
        newline(pp)
        field442 = unwrapped_fields441[1]
        _t1248 = pretty_monoid(pp, field442)
        newline(pp)
        field443 = unwrapped_fields441[2]
        _t1249 = pretty_relation_id(pp, field443)
        newline(pp)
        field444 = unwrapped_fields441[3]
        _t1250 = pretty_abstraction_with_arity(pp, field444)
        field445 = unwrapped_fields441[4]
        if !isnothing(field445)
            newline(pp)
            opt_val446 = field445
            _t1252 = pretty_attrs(pp, opt_val446)
            _t1251 = _t1252
        else
            _t1251 = nothing
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat454 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat454)
        write(pp, flat454)
        return nothing
    else
        function _t1253(_dollar_dollar)
            return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        end
        _t1254 = _t1253(msg)
        fields448 = _t1254
        unwrapped_fields449 = fields448
        write(pp, "(")
        write(pp, "functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field450 = unwrapped_fields449[1]
        _t1255 = pretty_relation_id(pp, field450)
        newline(pp)
        field451 = unwrapped_fields449[2]
        _t1256 = pretty_abstraction(pp, field451)
        newline(pp)
        field452 = unwrapped_fields449[3]
        _t1257 = pretty_functional_dependency_keys(pp, field452)
        newline(pp)
        field453 = unwrapped_fields449[4]
        _t1258 = pretty_functional_dependency_values(pp, field453)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat459 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat459)
        write(pp, flat459)
        return nothing
    else
        function _t1259(_dollar_dollar)
            return _dollar_dollar
        end
        _t1260 = _t1259(msg)
        fields455 = _t1260
        unwrapped_fields456 = fields455
        write(pp, "(")
        write(pp, "keys")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields456)
            newline(pp)
            for (i1261, elem457) in enumerate(unwrapped_fields456)
                i458 = i1261 - 1
                if (i458 > 0)
                    newline(pp)
                end
                _t1262 = pretty_var(pp, elem457)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat464 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat464)
        write(pp, flat464)
        return nothing
    else
        function _t1263(_dollar_dollar)
            return _dollar_dollar
        end
        _t1264 = _t1263(msg)
        fields460 = _t1264
        unwrapped_fields461 = fields460
        write(pp, "(")
        write(pp, "values")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields461)
            newline(pp)
            for (i1265, elem462) in enumerate(unwrapped_fields461)
                i463 = i1265 - 1
                if (i463 > 0)
                    newline(pp)
                end
                _t1266 = pretty_var(pp, elem462)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat468 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat468)
        write(pp, flat468)
        return nothing
    else
        function _t1268(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("rel_edb"))
                _t1269 = _get_oneof_field(_dollar_dollar, :rel_edb)
            else
                _t1269 = nothing
            end
            return _t1269
        end
        _t1270 = _t1268(msg)
        deconstruct_result467 = _t1270
        if !isnothing(deconstruct_result467)
            _t1272 = pretty_rel_edb(pp, deconstruct_result467)
            _t1271 = _t1272
        else
            function _t1273(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                    _t1274 = _get_oneof_field(_dollar_dollar, :betree_relation)
                else
                    _t1274 = nothing
                end
                return _t1274
            end
            _t1275 = _t1273(msg)
            deconstruct_result466 = _t1275
            if !isnothing(deconstruct_result466)
                _t1277 = pretty_betree_relation(pp, deconstruct_result466)
                _t1276 = _t1277
            else
                function _t1278(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                        _t1279 = _get_oneof_field(_dollar_dollar, :csv_data)
                    else
                        _t1279 = nothing
                    end
                    return _t1279
                end
                _t1280 = _t1278(msg)
                deconstruct_result465 = _t1280
                if !isnothing(deconstruct_result465)
                    _t1282 = pretty_csv_data(pp, deconstruct_result465)
                    _t1281 = _t1282
                else
                    throw(ParseError("No matching rule for data"))
                end
                _t1276 = _t1281
            end
            _t1271 = _t1276
        end
        _t1267 = _t1271
    end
    return _t1267
end

function pretty_rel_edb(pp::PrettyPrinter, msg::Proto.RelEDB)
    flat474 = try_flat(pp, msg, pretty_rel_edb)
    if !isnothing(flat474)
        write(pp, flat474)
        return nothing
    else
        function _t1283(_dollar_dollar)
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        end
        _t1284 = _t1283(msg)
        fields469 = _t1284
        unwrapped_fields470 = fields469
        write(pp, "(")
        write(pp, "rel_edb")
        indent_sexp!(pp)
        newline(pp)
        field471 = unwrapped_fields470[1]
        _t1285 = pretty_relation_id(pp, field471)
        newline(pp)
        field472 = unwrapped_fields470[2]
        _t1286 = pretty_rel_edb_path(pp, field472)
        newline(pp)
        field473 = unwrapped_fields470[3]
        _t1287 = pretty_rel_edb_types(pp, field473)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat479 = try_flat(pp, msg, pretty_rel_edb_path)
    if !isnothing(flat479)
        write(pp, flat479)
        return nothing
    else
        function _t1288(_dollar_dollar)
            return _dollar_dollar
        end
        _t1289 = _t1288(msg)
        fields475 = _t1289
        unwrapped_fields476 = fields475
        write(pp, "[")
        indent!(pp)
        for (i1290, elem477) in enumerate(unwrapped_fields476)
            i478 = i1290 - 1
            if (i478 > 0)
                newline(pp)
            end
            write(pp, format_string_value(elem477))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_rel_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat484 = try_flat(pp, msg, pretty_rel_edb_types)
    if !isnothing(flat484)
        write(pp, flat484)
        return nothing
    else
        function _t1291(_dollar_dollar)
            return _dollar_dollar
        end
        _t1292 = _t1291(msg)
        fields480 = _t1292
        unwrapped_fields481 = fields480
        write(pp, "[")
        indent!(pp)
        for (i1293, elem482) in enumerate(unwrapped_fields481)
            i483 = i1293 - 1
            if (i483 > 0)
                newline(pp)
            end
            _t1294 = pretty_type(pp, elem482)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat489 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat489)
        write(pp, flat489)
        return nothing
    else
        function _t1295(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        end
        _t1296 = _t1295(msg)
        fields485 = _t1296
        unwrapped_fields486 = fields485
        write(pp, "(")
        write(pp, "betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field487 = unwrapped_fields486[1]
        _t1297 = pretty_relation_id(pp, field487)
        newline(pp)
        field488 = unwrapped_fields486[2]
        _t1298 = pretty_betree_info(pp, field488)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat495 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat495)
        write(pp, flat495)
        return nothing
    else
        function _t1299(_dollar_dollar)
            _t1300 = deconstruct_betree_info_config(pp, _dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1300,)
        end
        _t1301 = _t1299(msg)
        fields490 = _t1301
        unwrapped_fields491 = fields490
        write(pp, "(")
        write(pp, "betree_info")
        indent_sexp!(pp)
        newline(pp)
        field492 = unwrapped_fields491[1]
        _t1302 = pretty_betree_info_key_types(pp, field492)
        newline(pp)
        field493 = unwrapped_fields491[2]
        _t1303 = pretty_betree_info_value_types(pp, field493)
        newline(pp)
        field494 = unwrapped_fields491[3]
        _t1304 = pretty_config_dict(pp, field494)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat500 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat500)
        write(pp, flat500)
        return nothing
    else
        function _t1305(_dollar_dollar)
            return _dollar_dollar
        end
        _t1306 = _t1305(msg)
        fields496 = _t1306
        unwrapped_fields497 = fields496
        write(pp, "(")
        write(pp, "key_types")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields497)
            newline(pp)
            for (i1307, elem498) in enumerate(unwrapped_fields497)
                i499 = i1307 - 1
                if (i499 > 0)
                    newline(pp)
                end
                _t1308 = pretty_type(pp, elem498)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat505 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat505)
        write(pp, flat505)
        return nothing
    else
        function _t1309(_dollar_dollar)
            return _dollar_dollar
        end
        _t1310 = _t1309(msg)
        fields501 = _t1310
        unwrapped_fields502 = fields501
        write(pp, "(")
        write(pp, "value_types")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields502)
            newline(pp)
            for (i1311, elem503) in enumerate(unwrapped_fields502)
                i504 = i1311 - 1
                if (i504 > 0)
                    newline(pp)
                end
                _t1312 = pretty_type(pp, elem503)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat512 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat512)
        write(pp, flat512)
        return nothing
    else
        function _t1313(_dollar_dollar)
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        end
        _t1314 = _t1313(msg)
        fields506 = _t1314
        unwrapped_fields507 = fields506
        write(pp, "(")
        write(pp, "csv_data")
        indent_sexp!(pp)
        newline(pp)
        field508 = unwrapped_fields507[1]
        _t1315 = pretty_csvlocator(pp, field508)
        newline(pp)
        field509 = unwrapped_fields507[2]
        _t1316 = pretty_csv_config(pp, field509)
        newline(pp)
        field510 = unwrapped_fields507[3]
        _t1317 = pretty_csv_columns(pp, field510)
        newline(pp)
        field511 = unwrapped_fields507[4]
        _t1318 = pretty_csv_asof(pp, field511)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat519 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat519)
        write(pp, flat519)
        return nothing
    else
        function _t1319(_dollar_dollar)
            if !isempty(_dollar_dollar.paths)
                _t1320 = _dollar_dollar.paths
            else
                _t1320 = nothing
            end
            if String(copy(_dollar_dollar.inline_data)) != ""
                _t1321 = String(copy(_dollar_dollar.inline_data))
            else
                _t1321 = nothing
            end
            return (_t1320, _t1321,)
        end
        _t1322 = _t1319(msg)
        fields513 = _t1322
        unwrapped_fields514 = fields513
        write(pp, "(")
        write(pp, "csv_locator")
        indent_sexp!(pp)
        field515 = unwrapped_fields514[1]
        if !isnothing(field515)
            newline(pp)
            opt_val516 = field515
            _t1324 = pretty_csv_locator_paths(pp, opt_val516)
            _t1323 = _t1324
        else
            _t1323 = nothing
        end
        field517 = unwrapped_fields514[2]
        if !isnothing(field517)
            newline(pp)
            opt_val518 = field517
            _t1326 = pretty_csv_locator_inline_data(pp, opt_val518)
            _t1325 = _t1326
        else
            _t1325 = nothing
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat524 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat524)
        write(pp, flat524)
        return nothing
    else
        function _t1327(_dollar_dollar)
            return _dollar_dollar
        end
        _t1328 = _t1327(msg)
        fields520 = _t1328
        unwrapped_fields521 = fields520
        write(pp, "(")
        write(pp, "paths")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields521)
            newline(pp)
            for (i1329, elem522) in enumerate(unwrapped_fields521)
                i523 = i1329 - 1
                if (i523 > 0)
                    newline(pp)
                end
                write(pp, format_string_value(elem522))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat527 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat527)
        write(pp, flat527)
        return nothing
    else
        function _t1330(_dollar_dollar)
            return _dollar_dollar
        end
        _t1331 = _t1330(msg)
        fields525 = _t1331
        unwrapped_fields526 = fields525
        write(pp, "(")
        write(pp, "inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(unwrapped_fields526))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat530 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat530)
        write(pp, flat530)
        return nothing
    else
        function _t1332(_dollar_dollar)
            _t1333 = deconstruct_csv_config(pp, _dollar_dollar)
            return _t1333
        end
        _t1334 = _t1332(msg)
        fields528 = _t1334
        unwrapped_fields529 = fields528
        write(pp, "(")
        write(pp, "csv_config")
        indent_sexp!(pp)
        newline(pp)
        _t1335 = pretty_config_dict(pp, unwrapped_fields529)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.CSVColumn})
    flat535 = try_flat(pp, msg, pretty_csv_columns)
    if !isnothing(flat535)
        write(pp, flat535)
        return nothing
    else
        function _t1336(_dollar_dollar)
            return _dollar_dollar
        end
        _t1337 = _t1336(msg)
        fields531 = _t1337
        unwrapped_fields532 = fields531
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields532)
            newline(pp)
            for (i1338, elem533) in enumerate(unwrapped_fields532)
                i534 = i1338 - 1
                if (i534 > 0)
                    newline(pp)
                end
                _t1339 = pretty_csv_column(pp, elem533)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_column(pp::PrettyPrinter, msg::Proto.CSVColumn)
    flat543 = try_flat(pp, msg, pretty_csv_column)
    if !isnothing(flat543)
        write(pp, flat543)
        return nothing
    else
        function _t1340(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        end
        _t1341 = _t1340(msg)
        fields536 = _t1341
        unwrapped_fields537 = fields536
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field538 = unwrapped_fields537[1]
        write(pp, format_string_value(field538))
        newline(pp)
        field539 = unwrapped_fields537[2]
        _t1342 = pretty_relation_id(pp, field539)
        newline(pp)
        write(pp, "[")
        field540 = unwrapped_fields537[3]
        for (i1343, elem541) in enumerate(field540)
            i542 = i1343 - 1
            if (i542 > 0)
                newline(pp)
            end
            _t1344 = pretty_type(pp, elem541)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat546 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat546)
        write(pp, flat546)
        return nothing
    else
        function _t1345(_dollar_dollar)
            return _dollar_dollar
        end
        _t1346 = _t1345(msg)
        fields544 = _t1346
        unwrapped_fields545 = fields544
        write(pp, "(")
        write(pp, "asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(unwrapped_fields545))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat549 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat549)
        write(pp, flat549)
        return nothing
    else
        function _t1347(_dollar_dollar)
            return _dollar_dollar.fragment_id
        end
        _t1348 = _t1347(msg)
        fields547 = _t1348
        unwrapped_fields548 = fields547
        write(pp, "(")
        write(pp, "undefine")
        indent_sexp!(pp)
        newline(pp)
        _t1349 = pretty_fragment_id(pp, unwrapped_fields548)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat554 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat554)
        write(pp, flat554)
        return nothing
    else
        function _t1350(_dollar_dollar)
            return _dollar_dollar.relations
        end
        _t1351 = _t1350(msg)
        fields550 = _t1351
        unwrapped_fields551 = fields550
        write(pp, "(")
        write(pp, "context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields551)
            newline(pp)
            for (i1352, elem552) in enumerate(unwrapped_fields551)
                i553 = i1352 - 1
                if (i553 > 0)
                    newline(pp)
                end
                _t1353 = pretty_relation_id(pp, elem552)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat559 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat559)
        write(pp, flat559)
        return nothing
    else
        function _t1354(_dollar_dollar)
            return _dollar_dollar
        end
        _t1355 = _t1354(msg)
        fields555 = _t1355
        unwrapped_fields556 = fields555
        write(pp, "(")
        write(pp, "reads")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields556)
            newline(pp)
            for (i1356, elem557) in enumerate(unwrapped_fields556)
                i558 = i1356 - 1
                if (i558 > 0)
                    newline(pp)
                end
                _t1357 = pretty_read(pp, elem557)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat565 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat565)
        write(pp, flat565)
        return nothing
    else
        function _t1359(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("demand"))
                _t1360 = _get_oneof_field(_dollar_dollar, :demand)
            else
                _t1360 = nothing
            end
            return _t1360
        end
        _t1361 = _t1359(msg)
        deconstruct_result564 = _t1361
        if !isnothing(deconstruct_result564)
            _t1363 = pretty_demand(pp, deconstruct_result564)
            _t1362 = _t1363
        else
            function _t1364(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("output"))
                    _t1365 = _get_oneof_field(_dollar_dollar, :output)
                else
                    _t1365 = nothing
                end
                return _t1365
            end
            _t1366 = _t1364(msg)
            deconstruct_result563 = _t1366
            if !isnothing(deconstruct_result563)
                _t1368 = pretty_output(pp, deconstruct_result563)
                _t1367 = _t1368
            else
                function _t1369(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                        _t1370 = _get_oneof_field(_dollar_dollar, :what_if)
                    else
                        _t1370 = nothing
                    end
                    return _t1370
                end
                _t1371 = _t1369(msg)
                deconstruct_result562 = _t1371
                if !isnothing(deconstruct_result562)
                    _t1373 = pretty_what_if(pp, deconstruct_result562)
                    _t1372 = _t1373
                else
                    function _t1374(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("abort"))
                            _t1375 = _get_oneof_field(_dollar_dollar, :abort)
                        else
                            _t1375 = nothing
                        end
                        return _t1375
                    end
                    _t1376 = _t1374(msg)
                    deconstruct_result561 = _t1376
                    if !isnothing(deconstruct_result561)
                        _t1378 = pretty_abort(pp, deconstruct_result561)
                        _t1377 = _t1378
                    else
                        function _t1379(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("#export"))
                                _t1380 = _get_oneof_field(_dollar_dollar, :var"#export")
                            else
                                _t1380 = nothing
                            end
                            return _t1380
                        end
                        _t1381 = _t1379(msg)
                        deconstruct_result560 = _t1381
                        if !isnothing(deconstruct_result560)
                            _t1383 = pretty_export(pp, deconstruct_result560)
                            _t1382 = _t1383
                        else
                            throw(ParseError("No matching rule for read"))
                        end
                        _t1377 = _t1382
                    end
                    _t1372 = _t1377
                end
                _t1367 = _t1372
            end
            _t1362 = _t1367
        end
        _t1358 = _t1362
    end
    return _t1358
end

function pretty_demand(pp::PrettyPrinter, msg::Proto.Demand)
    flat568 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat568)
        write(pp, flat568)
        return nothing
    else
        function _t1384(_dollar_dollar)
            return _dollar_dollar.relation_id
        end
        _t1385 = _t1384(msg)
        fields566 = _t1385
        unwrapped_fields567 = fields566
        write(pp, "(")
        write(pp, "demand")
        indent_sexp!(pp)
        newline(pp)
        _t1386 = pretty_relation_id(pp, unwrapped_fields567)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat573 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat573)
        write(pp, flat573)
        return nothing
    else
        function _t1387(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        end
        _t1388 = _t1387(msg)
        fields569 = _t1388
        unwrapped_fields570 = fields569
        write(pp, "(")
        write(pp, "output")
        indent_sexp!(pp)
        newline(pp)
        field571 = unwrapped_fields570[1]
        _t1389 = pretty_name(pp, field571)
        newline(pp)
        field572 = unwrapped_fields570[2]
        _t1390 = pretty_relation_id(pp, field572)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat578 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat578)
        write(pp, flat578)
        return nothing
    else
        function _t1391(_dollar_dollar)
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        end
        _t1392 = _t1391(msg)
        fields574 = _t1392
        unwrapped_fields575 = fields574
        write(pp, "(")
        write(pp, "what_if")
        indent_sexp!(pp)
        newline(pp)
        field576 = unwrapped_fields575[1]
        _t1393 = pretty_name(pp, field576)
        newline(pp)
        field577 = unwrapped_fields575[2]
        _t1394 = pretty_epoch(pp, field577)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat584 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat584)
        write(pp, flat584)
        return nothing
    else
        function _t1395(_dollar_dollar)
            if _dollar_dollar.name != "abort"
                _t1396 = _dollar_dollar.name
            else
                _t1396 = nothing
            end
            return (_t1396, _dollar_dollar.relation_id,)
        end
        _t1397 = _t1395(msg)
        fields579 = _t1397
        unwrapped_fields580 = fields579
        write(pp, "(")
        write(pp, "abort")
        indent_sexp!(pp)
        field581 = unwrapped_fields580[1]
        if !isnothing(field581)
            newline(pp)
            opt_val582 = field581
            _t1399 = pretty_name(pp, opt_val582)
            _t1398 = _t1399
        else
            _t1398 = nothing
        end
        newline(pp)
        field583 = unwrapped_fields580[2]
        _t1400 = pretty_relation_id(pp, field583)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat587 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat587)
        write(pp, flat587)
        return nothing
    else
        function _t1401(_dollar_dollar)
            return _get_oneof_field(_dollar_dollar, :csv_config)
        end
        _t1402 = _t1401(msg)
        fields585 = _t1402
        unwrapped_fields586 = fields585
        write(pp, "(")
        write(pp, "export")
        indent_sexp!(pp)
        newline(pp)
        _t1403 = pretty_export_csv_config(pp, unwrapped_fields586)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat593 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat593)
        write(pp, flat593)
        return nothing
    else
        function _t1404(_dollar_dollar)
            _t1405 = deconstruct_export_csv_config(pp, _dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1405,)
        end
        _t1406 = _t1404(msg)
        fields588 = _t1406
        unwrapped_fields589 = fields588
        write(pp, "(")
        write(pp, "export_csv_config")
        indent_sexp!(pp)
        newline(pp)
        field590 = unwrapped_fields589[1]
        _t1407 = pretty_export_csv_path(pp, field590)
        newline(pp)
        field591 = unwrapped_fields589[2]
        _t1408 = pretty_export_csv_columns(pp, field591)
        newline(pp)
        field592 = unwrapped_fields589[3]
        _t1409 = pretty_config_dict(pp, field592)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat596 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat596)
        write(pp, flat596)
        return nothing
    else
        function _t1410(_dollar_dollar)
            return _dollar_dollar
        end
        _t1411 = _t1410(msg)
        fields594 = _t1411
        unwrapped_fields595 = fields594
        write(pp, "(")
        write(pp, "path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(unwrapped_fields595))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat601 = try_flat(pp, msg, pretty_export_csv_columns)
    if !isnothing(flat601)
        write(pp, flat601)
        return nothing
    else
        function _t1412(_dollar_dollar)
            return _dollar_dollar
        end
        _t1413 = _t1412(msg)
        fields597 = _t1413
        unwrapped_fields598 = fields597
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields598)
            newline(pp)
            for (i1414, elem599) in enumerate(unwrapped_fields598)
                i600 = i1414 - 1
                if (i600 > 0)
                    newline(pp)
                end
                _t1415 = pretty_export_csv_column(pp, elem599)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_column(pp::PrettyPrinter, msg::Proto.ExportCSVColumn)
    flat606 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat606)
        write(pp, flat606)
        return nothing
    else
        function _t1416(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        end
        _t1417 = _t1416(msg)
        fields602 = _t1417
        unwrapped_fields603 = fields602
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field604 = unwrapped_fields603[1]
        write(pp, format_string_value(field604))
        newline(pp)
        field605 = unwrapped_fields603[2]
        _t1418 = pretty_relation_id(pp, field605)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


function pretty(msg::Proto.Transaction; max_width::Int=92)::String
    pp = PrettyPrinter(max_width=max_width)
    pretty_transaction(pp, msg)
    newline(pp)
    return get_output(pp)
end
