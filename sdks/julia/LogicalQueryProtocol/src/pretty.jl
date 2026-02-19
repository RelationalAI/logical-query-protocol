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

function relation_id_to_uint128(pp::PrettyPrinter, msg::Proto.RelationId)
    return Proto.UInt128Value(msg.id_low, msg.id_high)
end

# --- Helper functions ---

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1720 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1720
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1721 = Proto.Value(value=OneOf(:int_value, v))
    return _t1721
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1722 = Proto.Value(value=OneOf(:float_value, v))
    return _t1722
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1723 = Proto.Value(value=OneOf(:string_value, v))
    return _t1723
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1724 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1724
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1725 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1725
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1726 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1726,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1727 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1727,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1728 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1728,))
            end
        end
    end
    _t1729 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1729,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1730 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1730,))
    _t1731 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1731,))
    if msg.new_line != ""
        _t1732 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1732,))
    end
    _t1733 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1733,))
    _t1734 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1734,))
    _t1735 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1735,))
    if msg.comment != ""
        _t1736 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1736,))
    end
    for missing_string in msg.missing_strings
        _t1737 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1737,))
    end
    _t1738 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1738,))
    _t1739 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1739,))
    _t1740 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1740,))
    if msg.partition_size_mb != 0
        _t1741 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1741,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1742 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1742,))
    _t1743 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1743,))
    _t1744 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1744,))
    _t1745 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1745,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1746 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1746,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1747 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1747,))
        end
    end
    _t1748 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1748,))
    _t1749 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1749,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1750 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1750,))
    end
    if !isnothing(msg.compression)
        _t1751 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1751,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1752 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1752,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1753 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1753,))
    end
    if !isnothing(msg.syntax_delim)
        _t1754 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1754,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1755 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1755,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1756 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1756,))
    end
    return sort(result)
end

function deconstruct_relation_id_string(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, String}
    name = relation_id_to_string(pp, msg)
    if name != ""
        return name
    else
        _t1757 = nothing
    end
    return nothing
end

function deconstruct_relation_id_uint128(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, Proto.UInt128Value}
    name = relation_id_to_string(pp, msg)
    if name == ""
        return relation_id_to_uint128(pp, msg)
    else
        _t1758 = nothing
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
    flat650 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat650)
        write(pp, flat650)
        return nothing
    else
        function _t1282(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("configure"))
                _t1283 = _dollar_dollar.configure
            else
                _t1283 = nothing
            end
            if _has_proto_field(_dollar_dollar, Symbol("sync"))
                _t1284 = _dollar_dollar.sync
            else
                _t1284 = nothing
            end
            return (_t1283, _t1284, _dollar_dollar.epochs,)
        end
        _t1285 = _t1282(msg)
        fields641 = _t1285
        unwrapped_fields642 = fields641
        write(pp, "(")
        write(pp, "transaction")
        indent_sexp!(pp)
        field643 = unwrapped_fields642[1]
        if !isnothing(field643)
            newline(pp)
            opt_val644 = field643
            pretty_configure(pp, opt_val644)
        end
        field645 = unwrapped_fields642[2]
        if !isnothing(field645)
            newline(pp)
            opt_val646 = field645
            pretty_sync(pp, opt_val646)
        end
        field647 = unwrapped_fields642[3]
        if !isempty(field647)
            newline(pp)
            for (i1286, elem648) in enumerate(field647)
                i649 = i1286 - 1
                if (i649 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem648)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat653 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat653)
        write(pp, flat653)
        return nothing
    else
        function _t1287(_dollar_dollar)
            _t1288 = deconstruct_configure(pp, _dollar_dollar)
            return _t1288
        end
        _t1289 = _t1287(msg)
        fields651 = _t1289
        unwrapped_fields652 = fields651
        write(pp, "(")
        write(pp, "configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields652)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat657 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat657)
        write(pp, flat657)
        return nothing
    else
        fields654 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields654)
            newline(pp)
            for (i1290, elem655) in enumerate(fields654)
                i656 = i1290 - 1
                if (i656 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem655)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat662 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat662)
        write(pp, flat662)
        return nothing
    else
        function _t1291(_dollar_dollar)
            return (_dollar_dollar[1], _dollar_dollar[2],)
        end
        _t1292 = _t1291(msg)
        fields658 = _t1292
        unwrapped_fields659 = fields658
        write(pp, ":")
        field660 = unwrapped_fields659[1]
        write(pp, field660)
        write(pp, " ")
        field661 = unwrapped_fields659[2]
        pretty_value(pp, field661)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat682 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat682)
        write(pp, flat682)
        return nothing
    else
        function _t1293(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("date_value"))
                _t1294 = _get_oneof_field(_dollar_dollar, :date_value)
            else
                _t1294 = nothing
            end
            return _t1294
        end
        _t1295 = _t1293(msg)
        deconstruct_result680 = _t1295
        if !isnothing(deconstruct_result680)
            unwrapped681 = deconstruct_result680
            pretty_date(pp, unwrapped681)
        else
            function _t1296(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                    _t1297 = _get_oneof_field(_dollar_dollar, :datetime_value)
                else
                    _t1297 = nothing
                end
                return _t1297
            end
            _t1298 = _t1296(msg)
            deconstruct_result678 = _t1298
            if !isnothing(deconstruct_result678)
                unwrapped679 = deconstruct_result678
                pretty_datetime(pp, unwrapped679)
            else
                function _t1299(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                        _t1300 = _get_oneof_field(_dollar_dollar, :string_value)
                    else
                        _t1300 = nothing
                    end
                    return _t1300
                end
                _t1301 = _t1299(msg)
                deconstruct_result676 = _t1301
                if !isnothing(deconstruct_result676)
                    unwrapped677 = deconstruct_result676
                    write(pp, format_string_value(unwrapped677))
                else
                    function _t1302(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1303 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1303 = nothing
                        end
                        return _t1303
                    end
                    _t1304 = _t1302(msg)
                    deconstruct_result674 = _t1304
                    if !isnothing(deconstruct_result674)
                        unwrapped675 = deconstruct_result674
                        write(pp, string(unwrapped675))
                    else
                        function _t1305(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                _t1306 = _get_oneof_field(_dollar_dollar, :float_value)
                            else
                                _t1306 = nothing
                            end
                            return _t1306
                        end
                        _t1307 = _t1305(msg)
                        deconstruct_result672 = _t1307
                        if !isnothing(deconstruct_result672)
                            unwrapped673 = deconstruct_result672
                            write(pp, format_float64(unwrapped673))
                        else
                            function _t1308(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                    _t1309 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                else
                                    _t1309 = nothing
                                end
                                return _t1309
                            end
                            _t1310 = _t1308(msg)
                            deconstruct_result670 = _t1310
                            if !isnothing(deconstruct_result670)
                                unwrapped671 = deconstruct_result670
                                write(pp, format_uint128(pp, unwrapped671))
                            else
                                function _t1311(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                        _t1312 = _get_oneof_field(_dollar_dollar, :int128_value)
                                    else
                                        _t1312 = nothing
                                    end
                                    return _t1312
                                end
                                _t1313 = _t1311(msg)
                                deconstruct_result668 = _t1313
                                if !isnothing(deconstruct_result668)
                                    unwrapped669 = deconstruct_result668
                                    write(pp, format_int128(pp, unwrapped669))
                                else
                                    function _t1314(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                            _t1315 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                        else
                                            _t1315 = nothing
                                        end
                                        return _t1315
                                    end
                                    _t1316 = _t1314(msg)
                                    deconstruct_result666 = _t1316
                                    if !isnothing(deconstruct_result666)
                                        unwrapped667 = deconstruct_result666
                                        write(pp, format_decimal(pp, unwrapped667))
                                    else
                                        function _t1317(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                _t1318 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                            else
                                                _t1318 = nothing
                                            end
                                            return _t1318
                                        end
                                        _t1319 = _t1317(msg)
                                        deconstruct_result664 = _t1319
                                        if !isnothing(deconstruct_result664)
                                            unwrapped665 = deconstruct_result664
                                            pretty_boolean_value(pp, unwrapped665)
                                        else
                                            fields663 = msg
                                            write(pp, "missing")
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_date(pp::PrettyPrinter, msg::Proto.DateValue)
    flat688 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat688)
        write(pp, flat688)
        return nothing
    else
        function _t1320(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        end
        _t1321 = _t1320(msg)
        fields683 = _t1321
        unwrapped_fields684 = fields683
        write(pp, "(")
        write(pp, "date")
        indent_sexp!(pp)
        newline(pp)
        field685 = unwrapped_fields684[1]
        write(pp, string(field685))
        newline(pp)
        field686 = unwrapped_fields684[2]
        write(pp, string(field686))
        newline(pp)
        field687 = unwrapped_fields684[3]
        write(pp, string(field687))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat699 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat699)
        write(pp, flat699)
        return nothing
    else
        function _t1322(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        end
        _t1323 = _t1322(msg)
        fields689 = _t1323
        unwrapped_fields690 = fields689
        write(pp, "(")
        write(pp, "datetime")
        indent_sexp!(pp)
        newline(pp)
        field691 = unwrapped_fields690[1]
        write(pp, string(field691))
        newline(pp)
        field692 = unwrapped_fields690[2]
        write(pp, string(field692))
        newline(pp)
        field693 = unwrapped_fields690[3]
        write(pp, string(field693))
        newline(pp)
        field694 = unwrapped_fields690[4]
        write(pp, string(field694))
        newline(pp)
        field695 = unwrapped_fields690[5]
        write(pp, string(field695))
        newline(pp)
        field696 = unwrapped_fields690[6]
        write(pp, string(field696))
        field697 = unwrapped_fields690[7]
        if !isnothing(field697)
            newline(pp)
            opt_val698 = field697
            write(pp, string(opt_val698))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    function _t1324(_dollar_dollar)
        if _dollar_dollar
            _t1325 = ()
        else
            _t1325 = nothing
        end
        return _t1325
    end
    _t1326 = _t1324(msg)
    deconstruct_result702 = _t1326
    if !isnothing(deconstruct_result702)
        unwrapped703 = deconstruct_result702
        write(pp, "true")
    else
        function _t1327(_dollar_dollar)
            if !_dollar_dollar
                _t1328 = ()
            else
                _t1328 = nothing
            end
            return _t1328
        end
        _t1329 = _t1327(msg)
        deconstruct_result700 = _t1329
        if !isnothing(deconstruct_result700)
            unwrapped701 = deconstruct_result700
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat708 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat708)
        write(pp, flat708)
        return nothing
    else
        function _t1330(_dollar_dollar)
            return _dollar_dollar.fragments
        end
        _t1331 = _t1330(msg)
        fields704 = _t1331
        unwrapped_fields705 = fields704
        write(pp, "(")
        write(pp, "sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields705)
            newline(pp)
            for (i1332, elem706) in enumerate(unwrapped_fields705)
                i707 = i1332 - 1
                if (i707 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem706)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat711 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat711)
        write(pp, flat711)
        return nothing
    else
        function _t1333(_dollar_dollar)
            return fragment_id_to_string(pp, _dollar_dollar)
        end
        _t1334 = _t1333(msg)
        fields709 = _t1334
        unwrapped_fields710 = fields709
        write(pp, ":")
        write(pp, unwrapped_fields710)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat718 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat718)
        write(pp, flat718)
        return nothing
    else
        function _t1335(_dollar_dollar)
            if !isempty(_dollar_dollar.writes)
                _t1336 = _dollar_dollar.writes
            else
                _t1336 = nothing
            end
            if !isempty(_dollar_dollar.reads)
                _t1337 = _dollar_dollar.reads
            else
                _t1337 = nothing
            end
            return (_t1336, _t1337,)
        end
        _t1338 = _t1335(msg)
        fields712 = _t1338
        unwrapped_fields713 = fields712
        write(pp, "(")
        write(pp, "epoch")
        indent_sexp!(pp)
        field714 = unwrapped_fields713[1]
        if !isnothing(field714)
            newline(pp)
            opt_val715 = field714
            pretty_epoch_writes(pp, opt_val715)
        end
        field716 = unwrapped_fields713[2]
        if !isnothing(field716)
            newline(pp)
            opt_val717 = field716
            pretty_epoch_reads(pp, opt_val717)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat722 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat722)
        write(pp, flat722)
        return nothing
    else
        fields719 = msg
        write(pp, "(")
        write(pp, "writes")
        indent_sexp!(pp)
        if !isempty(fields719)
            newline(pp)
            for (i1339, elem720) in enumerate(fields719)
                i721 = i1339 - 1
                if (i721 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem720)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat731 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat731)
        write(pp, flat731)
        return nothing
    else
        function _t1340(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("define"))
                _t1341 = _get_oneof_field(_dollar_dollar, :define)
            else
                _t1341 = nothing
            end
            return _t1341
        end
        _t1342 = _t1340(msg)
        deconstruct_result729 = _t1342
        if !isnothing(deconstruct_result729)
            unwrapped730 = deconstruct_result729
            pretty_define(pp, unwrapped730)
        else
            function _t1343(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                    _t1344 = _get_oneof_field(_dollar_dollar, :undefine)
                else
                    _t1344 = nothing
                end
                return _t1344
            end
            _t1345 = _t1343(msg)
            deconstruct_result727 = _t1345
            if !isnothing(deconstruct_result727)
                unwrapped728 = deconstruct_result727
                pretty_undefine(pp, unwrapped728)
            else
                function _t1346(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("context"))
                        _t1347 = _get_oneof_field(_dollar_dollar, :context)
                    else
                        _t1347 = nothing
                    end
                    return _t1347
                end
                _t1348 = _t1346(msg)
                deconstruct_result725 = _t1348
                if !isnothing(deconstruct_result725)
                    unwrapped726 = deconstruct_result725
                    pretty_context(pp, unwrapped726)
                else
                    function _t1349(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                            _t1350 = _get_oneof_field(_dollar_dollar, :snapshot)
                        else
                            _t1350 = nothing
                        end
                        return _t1350
                    end
                    _t1351 = _t1349(msg)
                    deconstruct_result723 = _t1351
                    if !isnothing(deconstruct_result723)
                        unwrapped724 = deconstruct_result723
                        pretty_snapshot(pp, unwrapped724)
                    else
                        throw(ParseError("No matching rule for write"))
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_define(pp::PrettyPrinter, msg::Proto.Define)
    flat734 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat734)
        write(pp, flat734)
        return nothing
    else
        function _t1352(_dollar_dollar)
            return _dollar_dollar.fragment
        end
        _t1353 = _t1352(msg)
        fields732 = _t1353
        unwrapped_fields733 = fields732
        write(pp, "(")
        write(pp, "define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields733)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat741 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat741)
        write(pp, flat741)
        return nothing
    else
        function _t1354(_dollar_dollar)
            start_pretty_fragment(pp, _dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        end
        _t1355 = _t1354(msg)
        fields735 = _t1355
        unwrapped_fields736 = fields735
        write(pp, "(")
        write(pp, "fragment")
        indent_sexp!(pp)
        newline(pp)
        field737 = unwrapped_fields736[1]
        pretty_new_fragment_id(pp, field737)
        field738 = unwrapped_fields736[2]
        if !isempty(field738)
            newline(pp)
            for (i1356, elem739) in enumerate(field738)
                i740 = i1356 - 1
                if (i740 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem739)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat743 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat743)
        write(pp, flat743)
        return nothing
    else
        fields742 = msg
        pretty_fragment_id(pp, fields742)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat752 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat752)
        write(pp, flat752)
        return nothing
    else
        function _t1357(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("def"))
                _t1358 = _get_oneof_field(_dollar_dollar, :def)
            else
                _t1358 = nothing
            end
            return _t1358
        end
        _t1359 = _t1357(msg)
        deconstruct_result750 = _t1359
        if !isnothing(deconstruct_result750)
            unwrapped751 = deconstruct_result750
            pretty_def(pp, unwrapped751)
        else
            function _t1360(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                    _t1361 = _get_oneof_field(_dollar_dollar, :algorithm)
                else
                    _t1361 = nothing
                end
                return _t1361
            end
            _t1362 = _t1360(msg)
            deconstruct_result748 = _t1362
            if !isnothing(deconstruct_result748)
                unwrapped749 = deconstruct_result748
                pretty_algorithm(pp, unwrapped749)
            else
                function _t1363(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                        _t1364 = _get_oneof_field(_dollar_dollar, :constraint)
                    else
                        _t1364 = nothing
                    end
                    return _t1364
                end
                _t1365 = _t1363(msg)
                deconstruct_result746 = _t1365
                if !isnothing(deconstruct_result746)
                    unwrapped747 = deconstruct_result746
                    pretty_constraint(pp, unwrapped747)
                else
                    function _t1366(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("data"))
                            _t1367 = _get_oneof_field(_dollar_dollar, :data)
                        else
                            _t1367 = nothing
                        end
                        return _t1367
                    end
                    _t1368 = _t1366(msg)
                    deconstruct_result744 = _t1368
                    if !isnothing(deconstruct_result744)
                        unwrapped745 = deconstruct_result744
                        pretty_data(pp, unwrapped745)
                    else
                        throw(ParseError("No matching rule for declaration"))
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_def(pp::PrettyPrinter, msg::Proto.Def)
    flat759 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat759)
        write(pp, flat759)
        return nothing
    else
        function _t1369(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1370 = _dollar_dollar.attrs
            else
                _t1370 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1370,)
        end
        _t1371 = _t1369(msg)
        fields753 = _t1371
        unwrapped_fields754 = fields753
        write(pp, "(")
        write(pp, "def")
        indent_sexp!(pp)
        newline(pp)
        field755 = unwrapped_fields754[1]
        pretty_relation_id(pp, field755)
        newline(pp)
        field756 = unwrapped_fields754[2]
        pretty_abstraction(pp, field756)
        field757 = unwrapped_fields754[3]
        if !isnothing(field757)
            newline(pp)
            opt_val758 = field757
            pretty_attrs(pp, opt_val758)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat764 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat764)
        write(pp, flat764)
        return nothing
    else
        function _t1372(_dollar_dollar)
            _t1373 = deconstruct_relation_id_string(pp, _dollar_dollar)
            return _t1373
        end
        _t1374 = _t1372(msg)
        deconstruct_result762 = _t1374
        if !isnothing(deconstruct_result762)
            unwrapped763 = deconstruct_result762
            write(pp, ":")
            write(pp, unwrapped763)
        else
            function _t1375(_dollar_dollar)
                _t1376 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
                return _t1376
            end
            _t1377 = _t1375(msg)
            deconstruct_result760 = _t1377
            if !isnothing(deconstruct_result760)
                unwrapped761 = deconstruct_result760
                write(pp, format_uint128(pp, unwrapped761))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat769 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat769)
        write(pp, flat769)
        return nothing
    else
        function _t1378(_dollar_dollar)
            _t1379 = deconstruct_bindings(pp, _dollar_dollar)
            return (_t1379, _dollar_dollar.value,)
        end
        _t1380 = _t1378(msg)
        fields765 = _t1380
        unwrapped_fields766 = fields765
        write(pp, "(")
        indent!(pp)
        field767 = unwrapped_fields766[1]
        pretty_bindings(pp, field767)
        newline(pp)
        field768 = unwrapped_fields766[2]
        pretty_formula(pp, field768)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat777 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat777)
        write(pp, flat777)
        return nothing
    else
        function _t1381(_dollar_dollar)
            if !isempty(_dollar_dollar[2])
                _t1382 = _dollar_dollar[2]
            else
                _t1382 = nothing
            end
            return (_dollar_dollar[1], _t1382,)
        end
        _t1383 = _t1381(msg)
        fields770 = _t1383
        unwrapped_fields771 = fields770
        write(pp, "[")
        indent!(pp)
        field772 = unwrapped_fields771[1]
        for (i1384, elem773) in enumerate(field772)
            i774 = i1384 - 1
            if (i774 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem773)
        end
        field775 = unwrapped_fields771[2]
        if !isnothing(field775)
            newline(pp)
            opt_val776 = field775
            pretty_value_bindings(pp, opt_val776)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat782 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat782)
        write(pp, flat782)
        return nothing
    else
        function _t1385(_dollar_dollar)
            return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        end
        _t1386 = _t1385(msg)
        fields778 = _t1386
        unwrapped_fields779 = fields778
        field780 = unwrapped_fields779[1]
        write(pp, field780)
        write(pp, "::")
        field781 = unwrapped_fields779[2]
        pretty_type(pp, field781)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat805 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat805)
        write(pp, flat805)
        return nothing
    else
        function _t1387(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
                _t1388 = _get_oneof_field(_dollar_dollar, :unspecified_type)
            else
                _t1388 = nothing
            end
            return _t1388
        end
        _t1389 = _t1387(msg)
        deconstruct_result803 = _t1389
        if !isnothing(deconstruct_result803)
            unwrapped804 = deconstruct_result803
            pretty_unspecified_type(pp, unwrapped804)
        else
            function _t1390(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                    _t1391 = _get_oneof_field(_dollar_dollar, :string_type)
                else
                    _t1391 = nothing
                end
                return _t1391
            end
            _t1392 = _t1390(msg)
            deconstruct_result801 = _t1392
            if !isnothing(deconstruct_result801)
                unwrapped802 = deconstruct_result801
                pretty_string_type(pp, unwrapped802)
            else
                function _t1393(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                        _t1394 = _get_oneof_field(_dollar_dollar, :int_type)
                    else
                        _t1394 = nothing
                    end
                    return _t1394
                end
                _t1395 = _t1393(msg)
                deconstruct_result799 = _t1395
                if !isnothing(deconstruct_result799)
                    unwrapped800 = deconstruct_result799
                    pretty_int_type(pp, unwrapped800)
                else
                    function _t1396(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                            _t1397 = _get_oneof_field(_dollar_dollar, :float_type)
                        else
                            _t1397 = nothing
                        end
                        return _t1397
                    end
                    _t1398 = _t1396(msg)
                    deconstruct_result797 = _t1398
                    if !isnothing(deconstruct_result797)
                        unwrapped798 = deconstruct_result797
                        pretty_float_type(pp, unwrapped798)
                    else
                        function _t1399(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                                _t1400 = _get_oneof_field(_dollar_dollar, :uint128_type)
                            else
                                _t1400 = nothing
                            end
                            return _t1400
                        end
                        _t1401 = _t1399(msg)
                        deconstruct_result795 = _t1401
                        if !isnothing(deconstruct_result795)
                            unwrapped796 = deconstruct_result795
                            pretty_uint128_type(pp, unwrapped796)
                        else
                            function _t1402(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                    _t1403 = _get_oneof_field(_dollar_dollar, :int128_type)
                                else
                                    _t1403 = nothing
                                end
                                return _t1403
                            end
                            _t1404 = _t1402(msg)
                            deconstruct_result793 = _t1404
                            if !isnothing(deconstruct_result793)
                                unwrapped794 = deconstruct_result793
                                pretty_int128_type(pp, unwrapped794)
                            else
                                function _t1405(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                        _t1406 = _get_oneof_field(_dollar_dollar, :date_type)
                                    else
                                        _t1406 = nothing
                                    end
                                    return _t1406
                                end
                                _t1407 = _t1405(msg)
                                deconstruct_result791 = _t1407
                                if !isnothing(deconstruct_result791)
                                    unwrapped792 = deconstruct_result791
                                    pretty_date_type(pp, unwrapped792)
                                else
                                    function _t1408(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                            _t1409 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                        else
                                            _t1409 = nothing
                                        end
                                        return _t1409
                                    end
                                    _t1410 = _t1408(msg)
                                    deconstruct_result789 = _t1410
                                    if !isnothing(deconstruct_result789)
                                        unwrapped790 = deconstruct_result789
                                        pretty_datetime_type(pp, unwrapped790)
                                    else
                                        function _t1411(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                                _t1412 = _get_oneof_field(_dollar_dollar, :missing_type)
                                            else
                                                _t1412 = nothing
                                            end
                                            return _t1412
                                        end
                                        _t1413 = _t1411(msg)
                                        deconstruct_result787 = _t1413
                                        if !isnothing(deconstruct_result787)
                                            unwrapped788 = deconstruct_result787
                                            pretty_missing_type(pp, unwrapped788)
                                        else
                                            function _t1414(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                    _t1415 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                                else
                                                    _t1415 = nothing
                                                end
                                                return _t1415
                                            end
                                            _t1416 = _t1414(msg)
                                            deconstruct_result785 = _t1416
                                            if !isnothing(deconstruct_result785)
                                                unwrapped786 = deconstruct_result785
                                                pretty_decimal_type(pp, unwrapped786)
                                            else
                                                function _t1417(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                        _t1418 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                    else
                                                        _t1418 = nothing
                                                    end
                                                    return _t1418
                                                end
                                                _t1419 = _t1417(msg)
                                                deconstruct_result783 = _t1419
                                                if !isnothing(deconstruct_result783)
                                                    unwrapped784 = deconstruct_result783
                                                    pretty_boolean_type(pp, unwrapped784)
                                                else
                                                    throw(ParseError("No matching rule for type"))
                                                end
                                            end
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_unspecified_type(pp::PrettyPrinter, msg::Proto.UnspecifiedType)
    fields806 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields807 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields808 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields809 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields810 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields811 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields812 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields813 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields814 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat819 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat819)
        write(pp, flat819)
        return nothing
    else
        function _t1420(_dollar_dollar)
            return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        end
        _t1421 = _t1420(msg)
        fields815 = _t1421
        unwrapped_fields816 = fields815
        write(pp, "(")
        write(pp, "DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field817 = unwrapped_fields816[1]
        write(pp, string(field817))
        newline(pp)
        field818 = unwrapped_fields816[2]
        write(pp, string(field818))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields820 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat824 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat824)
        write(pp, flat824)
        return nothing
    else
        fields821 = msg
        write(pp, "|")
        if !isempty(fields821)
            write(pp, " ")
            for (i1422, elem822) in enumerate(fields821)
                i823 = i1422 - 1
                if (i823 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem822)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat851 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat851)
        write(pp, flat851)
        return nothing
    else
        function _t1423(_dollar_dollar)
            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                _t1424 = _get_oneof_field(_dollar_dollar, :conjunction)
            else
                _t1424 = nothing
            end
            return _t1424
        end
        _t1425 = _t1423(msg)
        deconstruct_result849 = _t1425
        if !isnothing(deconstruct_result849)
            unwrapped850 = deconstruct_result849
            pretty_true(pp, unwrapped850)
        else
            function _t1426(_dollar_dollar)
                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                    _t1427 = _get_oneof_field(_dollar_dollar, :disjunction)
                else
                    _t1427 = nothing
                end
                return _t1427
            end
            _t1428 = _t1426(msg)
            deconstruct_result847 = _t1428
            if !isnothing(deconstruct_result847)
                unwrapped848 = deconstruct_result847
                pretty_false(pp, unwrapped848)
            else
                function _t1429(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("exists"))
                        _t1430 = _get_oneof_field(_dollar_dollar, :exists)
                    else
                        _t1430 = nothing
                    end
                    return _t1430
                end
                _t1431 = _t1429(msg)
                deconstruct_result845 = _t1431
                if !isnothing(deconstruct_result845)
                    unwrapped846 = deconstruct_result845
                    pretty_exists(pp, unwrapped846)
                else
                    function _t1432(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                            _t1433 = _get_oneof_field(_dollar_dollar, :reduce)
                        else
                            _t1433 = nothing
                        end
                        return _t1433
                    end
                    _t1434 = _t1432(msg)
                    deconstruct_result843 = _t1434
                    if !isnothing(deconstruct_result843)
                        unwrapped844 = deconstruct_result843
                        pretty_reduce(pp, unwrapped844)
                    else
                        function _t1435(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("conjunction"))
                                _t1436 = _get_oneof_field(_dollar_dollar, :conjunction)
                            else
                                _t1436 = nothing
                            end
                            return _t1436
                        end
                        _t1437 = _t1435(msg)
                        deconstruct_result841 = _t1437
                        if !isnothing(deconstruct_result841)
                            unwrapped842 = deconstruct_result841
                            pretty_conjunction(pp, unwrapped842)
                        else
                            function _t1438(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("disjunction"))
                                    _t1439 = _get_oneof_field(_dollar_dollar, :disjunction)
                                else
                                    _t1439 = nothing
                                end
                                return _t1439
                            end
                            _t1440 = _t1438(msg)
                            deconstruct_result839 = _t1440
                            if !isnothing(deconstruct_result839)
                                unwrapped840 = deconstruct_result839
                                pretty_disjunction(pp, unwrapped840)
                            else
                                function _t1441(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("not"))
                                        _t1442 = _get_oneof_field(_dollar_dollar, :not)
                                    else
                                        _t1442 = nothing
                                    end
                                    return _t1442
                                end
                                _t1443 = _t1441(msg)
                                deconstruct_result837 = _t1443
                                if !isnothing(deconstruct_result837)
                                    unwrapped838 = deconstruct_result837
                                    pretty_not(pp, unwrapped838)
                                else
                                    function _t1444(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                            _t1445 = _get_oneof_field(_dollar_dollar, :ffi)
                                        else
                                            _t1445 = nothing
                                        end
                                        return _t1445
                                    end
                                    _t1446 = _t1444(msg)
                                    deconstruct_result835 = _t1446
                                    if !isnothing(deconstruct_result835)
                                        unwrapped836 = deconstruct_result835
                                        pretty_ffi(pp, unwrapped836)
                                    else
                                        function _t1447(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                                _t1448 = _get_oneof_field(_dollar_dollar, :atom)
                                            else
                                                _t1448 = nothing
                                            end
                                            return _t1448
                                        end
                                        _t1449 = _t1447(msg)
                                        deconstruct_result833 = _t1449
                                        if !isnothing(deconstruct_result833)
                                            unwrapped834 = deconstruct_result833
                                            pretty_atom(pp, unwrapped834)
                                        else
                                            function _t1450(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                    _t1451 = _get_oneof_field(_dollar_dollar, :pragma)
                                                else
                                                    _t1451 = nothing
                                                end
                                                return _t1451
                                            end
                                            _t1452 = _t1450(msg)
                                            deconstruct_result831 = _t1452
                                            if !isnothing(deconstruct_result831)
                                                unwrapped832 = deconstruct_result831
                                                pretty_pragma(pp, unwrapped832)
                                            else
                                                function _t1453(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                        _t1454 = _get_oneof_field(_dollar_dollar, :primitive)
                                                    else
                                                        _t1454 = nothing
                                                    end
                                                    return _t1454
                                                end
                                                _t1455 = _t1453(msg)
                                                deconstruct_result829 = _t1455
                                                if !isnothing(deconstruct_result829)
                                                    unwrapped830 = deconstruct_result829
                                                    pretty_primitive(pp, unwrapped830)
                                                else
                                                    function _t1456(_dollar_dollar)
                                                        if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                            _t1457 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                        else
                                                            _t1457 = nothing
                                                        end
                                                        return _t1457
                                                    end
                                                    _t1458 = _t1456(msg)
                                                    deconstruct_result827 = _t1458
                                                    if !isnothing(deconstruct_result827)
                                                        unwrapped828 = deconstruct_result827
                                                        pretty_rel_atom(pp, unwrapped828)
                                                    else
                                                        function _t1459(_dollar_dollar)
                                                            if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                                _t1460 = _get_oneof_field(_dollar_dollar, :cast)
                                                            else
                                                                _t1460 = nothing
                                                            end
                                                            return _t1460
                                                        end
                                                        _t1461 = _t1459(msg)
                                                        deconstruct_result825 = _t1461
                                                        if !isnothing(deconstruct_result825)
                                                            unwrapped826 = deconstruct_result825
                                                            pretty_cast(pp, unwrapped826)
                                                        else
                                                            throw(ParseError("No matching rule for formula"))
                                                        end
                                                    end
                                                end
                                            end
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_true(pp::PrettyPrinter, msg::Proto.Conjunction)
    fields852 = msg
    write(pp, "(")
    write(pp, "true")
    write(pp, ")")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields853 = msg
    write(pp, "(")
    write(pp, "false")
    write(pp, ")")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat858 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat858)
        write(pp, flat858)
        return nothing
    else
        function _t1462(_dollar_dollar)
            _t1463 = deconstruct_bindings(pp, _dollar_dollar.body)
            return (_t1463, _dollar_dollar.body.value,)
        end
        _t1464 = _t1462(msg)
        fields854 = _t1464
        unwrapped_fields855 = fields854
        write(pp, "(")
        write(pp, "exists")
        indent_sexp!(pp)
        newline(pp)
        field856 = unwrapped_fields855[1]
        pretty_bindings(pp, field856)
        newline(pp)
        field857 = unwrapped_fields855[2]
        pretty_formula(pp, field857)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat864 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat864)
        write(pp, flat864)
        return nothing
    else
        function _t1465(_dollar_dollar)
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        end
        _t1466 = _t1465(msg)
        fields859 = _t1466
        unwrapped_fields860 = fields859
        write(pp, "(")
        write(pp, "reduce")
        indent_sexp!(pp)
        newline(pp)
        field861 = unwrapped_fields860[1]
        pretty_abstraction(pp, field861)
        newline(pp)
        field862 = unwrapped_fields860[2]
        pretty_abstraction(pp, field862)
        newline(pp)
        field863 = unwrapped_fields860[3]
        pretty_terms(pp, field863)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat868 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat868)
        write(pp, flat868)
        return nothing
    else
        fields865 = msg
        write(pp, "(")
        write(pp, "terms")
        indent_sexp!(pp)
        if !isempty(fields865)
            newline(pp)
            for (i1467, elem866) in enumerate(fields865)
                i867 = i1467 - 1
                if (i867 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem866)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat873 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat873)
        write(pp, flat873)
        return nothing
    else
        function _t1468(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("var"))
                _t1469 = _get_oneof_field(_dollar_dollar, :var)
            else
                _t1469 = nothing
            end
            return _t1469
        end
        _t1470 = _t1468(msg)
        deconstruct_result871 = _t1470
        if !isnothing(deconstruct_result871)
            unwrapped872 = deconstruct_result871
            pretty_var(pp, unwrapped872)
        else
            function _t1471(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("constant"))
                    _t1472 = _get_oneof_field(_dollar_dollar, :constant)
                else
                    _t1472 = nothing
                end
                return _t1472
            end
            _t1473 = _t1471(msg)
            deconstruct_result869 = _t1473
            if !isnothing(deconstruct_result869)
                unwrapped870 = deconstruct_result869
                pretty_constant(pp, unwrapped870)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat876 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat876)
        write(pp, flat876)
        return nothing
    else
        function _t1474(_dollar_dollar)
            return _dollar_dollar.name
        end
        _t1475 = _t1474(msg)
        fields874 = _t1475
        unwrapped_fields875 = fields874
        write(pp, unwrapped_fields875)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat878 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat878)
        write(pp, flat878)
        return nothing
    else
        fields877 = msg
        pretty_value(pp, fields877)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat883 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat883)
        write(pp, flat883)
        return nothing
    else
        function _t1476(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1477 = _t1476(msg)
        fields879 = _t1477
        unwrapped_fields880 = fields879
        write(pp, "(")
        write(pp, "and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields880)
            newline(pp)
            for (i1478, elem881) in enumerate(unwrapped_fields880)
                i882 = i1478 - 1
                if (i882 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem881)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat888 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat888)
        write(pp, flat888)
        return nothing
    else
        function _t1479(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1480 = _t1479(msg)
        fields884 = _t1480
        unwrapped_fields885 = fields884
        write(pp, "(")
        write(pp, "or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields885)
            newline(pp)
            for (i1481, elem886) in enumerate(unwrapped_fields885)
                i887 = i1481 - 1
                if (i887 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem886)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat891 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat891)
        write(pp, flat891)
        return nothing
    else
        function _t1482(_dollar_dollar)
            return _dollar_dollar.arg
        end
        _t1483 = _t1482(msg)
        fields889 = _t1483
        unwrapped_fields890 = fields889
        write(pp, "(")
        write(pp, "not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields890)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat897 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat897)
        write(pp, flat897)
        return nothing
    else
        function _t1484(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        end
        _t1485 = _t1484(msg)
        fields892 = _t1485
        unwrapped_fields893 = fields892
        write(pp, "(")
        write(pp, "ffi")
        indent_sexp!(pp)
        newline(pp)
        field894 = unwrapped_fields893[1]
        pretty_name(pp, field894)
        newline(pp)
        field895 = unwrapped_fields893[2]
        pretty_ffi_args(pp, field895)
        newline(pp)
        field896 = unwrapped_fields893[3]
        pretty_terms(pp, field896)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat899 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat899)
        write(pp, flat899)
        return nothing
    else
        fields898 = msg
        write(pp, ":")
        write(pp, fields898)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat903 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat903)
        write(pp, flat903)
        return nothing
    else
        fields900 = msg
        write(pp, "(")
        write(pp, "args")
        indent_sexp!(pp)
        if !isempty(fields900)
            newline(pp)
            for (i1486, elem901) in enumerate(fields900)
                i902 = i1486 - 1
                if (i902 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem901)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat910 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat910)
        write(pp, flat910)
        return nothing
    else
        function _t1487(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1488 = _t1487(msg)
        fields904 = _t1488
        unwrapped_fields905 = fields904
        write(pp, "(")
        write(pp, "atom")
        indent_sexp!(pp)
        newline(pp)
        field906 = unwrapped_fields905[1]
        pretty_relation_id(pp, field906)
        field907 = unwrapped_fields905[2]
        if !isempty(field907)
            newline(pp)
            for (i1489, elem908) in enumerate(field907)
                i909 = i1489 - 1
                if (i909 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem908)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat917 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat917)
        write(pp, flat917)
        return nothing
    else
        function _t1490(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1491 = _t1490(msg)
        fields911 = _t1491
        unwrapped_fields912 = fields911
        write(pp, "(")
        write(pp, "pragma")
        indent_sexp!(pp)
        newline(pp)
        field913 = unwrapped_fields912[1]
        pretty_name(pp, field913)
        field914 = unwrapped_fields912[2]
        if !isempty(field914)
            newline(pp)
            for (i1492, elem915) in enumerate(field914)
                i916 = i1492 - 1
                if (i916 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem915)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat933 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat933)
        write(pp, flat933)
        return nothing
    else
        function _t1493(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1494 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1494 = nothing
            end
            return _t1494
        end
        _t1495 = _t1493(msg)
        guard_result932 = _t1495
        if !isnothing(guard_result932)
            pretty_eq(pp, msg)
        else
            function _t1496(_dollar_dollar)
                if _dollar_dollar.name == "rel_primitive_lt_monotype"
                    _t1497 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1497 = nothing
                end
                return _t1497
            end
            _t1498 = _t1496(msg)
            guard_result931 = _t1498
            if !isnothing(guard_result931)
                pretty_lt(pp, msg)
            else
                function _t1499(_dollar_dollar)
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                        _t1500 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1500 = nothing
                    end
                    return _t1500
                end
                _t1501 = _t1499(msg)
                guard_result930 = _t1501
                if !isnothing(guard_result930)
                    pretty_lt_eq(pp, msg)
                else
                    function _t1502(_dollar_dollar)
                        if _dollar_dollar.name == "rel_primitive_gt_monotype"
                            _t1503 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1503 = nothing
                        end
                        return _t1503
                    end
                    _t1504 = _t1502(msg)
                    guard_result929 = _t1504
                    if !isnothing(guard_result929)
                        pretty_gt(pp, msg)
                    else
                        function _t1505(_dollar_dollar)
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                                _t1506 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                            else
                                _t1506 = nothing
                            end
                            return _t1506
                        end
                        _t1507 = _t1505(msg)
                        guard_result928 = _t1507
                        if !isnothing(guard_result928)
                            pretty_gt_eq(pp, msg)
                        else
                            function _t1508(_dollar_dollar)
                                if _dollar_dollar.name == "rel_primitive_add_monotype"
                                    _t1509 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1509 = nothing
                                end
                                return _t1509
                            end
                            _t1510 = _t1508(msg)
                            guard_result927 = _t1510
                            if !isnothing(guard_result927)
                                pretty_add(pp, msg)
                            else
                                function _t1511(_dollar_dollar)
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                        _t1512 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1512 = nothing
                                    end
                                    return _t1512
                                end
                                _t1513 = _t1511(msg)
                                guard_result926 = _t1513
                                if !isnothing(guard_result926)
                                    pretty_minus(pp, msg)
                                else
                                    function _t1514(_dollar_dollar)
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                            _t1515 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1515 = nothing
                                        end
                                        return _t1515
                                    end
                                    _t1516 = _t1514(msg)
                                    guard_result925 = _t1516
                                    if !isnothing(guard_result925)
                                        pretty_multiply(pp, msg)
                                    else
                                        function _t1517(_dollar_dollar)
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                                _t1518 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                            else
                                                _t1518 = nothing
                                            end
                                            return _t1518
                                        end
                                        _t1519 = _t1517(msg)
                                        guard_result924 = _t1519
                                        if !isnothing(guard_result924)
                                            pretty_divide(pp, msg)
                                        else
                                            function _t1520(_dollar_dollar)
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            end
                                            _t1521 = _t1520(msg)
                                            fields918 = _t1521
                                            unwrapped_fields919 = fields918
                                            write(pp, "(")
                                            write(pp, "primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field920 = unwrapped_fields919[1]
                                            pretty_name(pp, field920)
                                            field921 = unwrapped_fields919[2]
                                            if !isempty(field921)
                                                newline(pp)
                                                for (i1522, elem922) in enumerate(field921)
                                                    i923 = i1522 - 1
                                                    if (i923 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem922)
                                                end
                                            end
                                            dedent!(pp)
                                            write(pp, ")")
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat938 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat938)
        write(pp, flat938)
        return nothing
    else
        function _t1523(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1524 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1524 = nothing
            end
            return _t1524
        end
        _t1525 = _t1523(msg)
        fields934 = _t1525
        unwrapped_fields935 = fields934
        write(pp, "(")
        write(pp, "=")
        indent_sexp!(pp)
        newline(pp)
        field936 = unwrapped_fields935[1]
        pretty_term(pp, field936)
        newline(pp)
        field937 = unwrapped_fields935[2]
        pretty_term(pp, field937)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat943 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat943)
        write(pp, flat943)
        return nothing
    else
        function _t1526(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1527 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1527 = nothing
            end
            return _t1527
        end
        _t1528 = _t1526(msg)
        fields939 = _t1528
        unwrapped_fields940 = fields939
        write(pp, "(")
        write(pp, "<")
        indent_sexp!(pp)
        newline(pp)
        field941 = unwrapped_fields940[1]
        pretty_term(pp, field941)
        newline(pp)
        field942 = unwrapped_fields940[2]
        pretty_term(pp, field942)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat948 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat948)
        write(pp, flat948)
        return nothing
    else
        function _t1529(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                _t1530 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1530 = nothing
            end
            return _t1530
        end
        _t1531 = _t1529(msg)
        fields944 = _t1531
        unwrapped_fields945 = fields944
        write(pp, "(")
        write(pp, "<=")
        indent_sexp!(pp)
        newline(pp)
        field946 = unwrapped_fields945[1]
        pretty_term(pp, field946)
        newline(pp)
        field947 = unwrapped_fields945[2]
        pretty_term(pp, field947)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat953 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat953)
        write(pp, flat953)
        return nothing
    else
        function _t1532(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_monotype"
                _t1533 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1533 = nothing
            end
            return _t1533
        end
        _t1534 = _t1532(msg)
        fields949 = _t1534
        unwrapped_fields950 = fields949
        write(pp, "(")
        write(pp, ">")
        indent_sexp!(pp)
        newline(pp)
        field951 = unwrapped_fields950[1]
        pretty_term(pp, field951)
        newline(pp)
        field952 = unwrapped_fields950[2]
        pretty_term(pp, field952)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat958 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat958)
        write(pp, flat958)
        return nothing
    else
        function _t1535(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                _t1536 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1536 = nothing
            end
            return _t1536
        end
        _t1537 = _t1535(msg)
        fields954 = _t1537
        unwrapped_fields955 = fields954
        write(pp, "(")
        write(pp, ">=")
        indent_sexp!(pp)
        newline(pp)
        field956 = unwrapped_fields955[1]
        pretty_term(pp, field956)
        newline(pp)
        field957 = unwrapped_fields955[2]
        pretty_term(pp, field957)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat964 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat964)
        write(pp, flat964)
        return nothing
    else
        function _t1538(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_add_monotype"
                _t1539 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1539 = nothing
            end
            return _t1539
        end
        _t1540 = _t1538(msg)
        fields959 = _t1540
        unwrapped_fields960 = fields959
        write(pp, "(")
        write(pp, "+")
        indent_sexp!(pp)
        newline(pp)
        field961 = unwrapped_fields960[1]
        pretty_term(pp, field961)
        newline(pp)
        field962 = unwrapped_fields960[2]
        pretty_term(pp, field962)
        newline(pp)
        field963 = unwrapped_fields960[3]
        pretty_term(pp, field963)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat970 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat970)
        write(pp, flat970)
        return nothing
    else
        function _t1541(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                _t1542 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1542 = nothing
            end
            return _t1542
        end
        _t1543 = _t1541(msg)
        fields965 = _t1543
        unwrapped_fields966 = fields965
        write(pp, "(")
        write(pp, "-")
        indent_sexp!(pp)
        newline(pp)
        field967 = unwrapped_fields966[1]
        pretty_term(pp, field967)
        newline(pp)
        field968 = unwrapped_fields966[2]
        pretty_term(pp, field968)
        newline(pp)
        field969 = unwrapped_fields966[3]
        pretty_term(pp, field969)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat976 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat976)
        write(pp, flat976)
        return nothing
    else
        function _t1544(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                _t1545 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1545 = nothing
            end
            return _t1545
        end
        _t1546 = _t1544(msg)
        fields971 = _t1546
        unwrapped_fields972 = fields971
        write(pp, "(")
        write(pp, "*")
        indent_sexp!(pp)
        newline(pp)
        field973 = unwrapped_fields972[1]
        pretty_term(pp, field973)
        newline(pp)
        field974 = unwrapped_fields972[2]
        pretty_term(pp, field974)
        newline(pp)
        field975 = unwrapped_fields972[3]
        pretty_term(pp, field975)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat982 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat982)
        write(pp, flat982)
        return nothing
    else
        function _t1547(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                _t1548 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1548 = nothing
            end
            return _t1548
        end
        _t1549 = _t1547(msg)
        fields977 = _t1549
        unwrapped_fields978 = fields977
        write(pp, "(")
        write(pp, "/")
        indent_sexp!(pp)
        newline(pp)
        field979 = unwrapped_fields978[1]
        pretty_term(pp, field979)
        newline(pp)
        field980 = unwrapped_fields978[2]
        pretty_term(pp, field980)
        newline(pp)
        field981 = unwrapped_fields978[3]
        pretty_term(pp, field981)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat987 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat987)
        write(pp, flat987)
        return nothing
    else
        function _t1550(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
                _t1551 = _get_oneof_field(_dollar_dollar, :specialized_value)
            else
                _t1551 = nothing
            end
            return _t1551
        end
        _t1552 = _t1550(msg)
        deconstruct_result985 = _t1552
        if !isnothing(deconstruct_result985)
            unwrapped986 = deconstruct_result985
            pretty_specialized_value(pp, unwrapped986)
        else
            function _t1553(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("term"))
                    _t1554 = _get_oneof_field(_dollar_dollar, :term)
                else
                    _t1554 = nothing
                end
                return _t1554
            end
            _t1555 = _t1553(msg)
            deconstruct_result983 = _t1555
            if !isnothing(deconstruct_result983)
                unwrapped984 = deconstruct_result983
                pretty_term(pp, unwrapped984)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat989 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat989)
        write(pp, flat989)
        return nothing
    else
        fields988 = msg
        write(pp, "#")
        pretty_value(pp, fields988)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat996 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat996)
        write(pp, flat996)
        return nothing
    else
        function _t1556(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1557 = _t1556(msg)
        fields990 = _t1557
        unwrapped_fields991 = fields990
        write(pp, "(")
        write(pp, "relatom")
        indent_sexp!(pp)
        newline(pp)
        field992 = unwrapped_fields991[1]
        pretty_name(pp, field992)
        field993 = unwrapped_fields991[2]
        if !isempty(field993)
            newline(pp)
            for (i1558, elem994) in enumerate(field993)
                i995 = i1558 - 1
                if (i995 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem994)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1001 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1001)
        write(pp, flat1001)
        return nothing
    else
        function _t1559(_dollar_dollar)
            return (_dollar_dollar.input, _dollar_dollar.result,)
        end
        _t1560 = _t1559(msg)
        fields997 = _t1560
        unwrapped_fields998 = fields997
        write(pp, "(")
        write(pp, "cast")
        indent_sexp!(pp)
        newline(pp)
        field999 = unwrapped_fields998[1]
        pretty_term(pp, field999)
        newline(pp)
        field1000 = unwrapped_fields998[2]
        pretty_term(pp, field1000)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1005 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1005)
        write(pp, flat1005)
        return nothing
    else
        fields1002 = msg
        write(pp, "(")
        write(pp, "attrs")
        indent_sexp!(pp)
        if !isempty(fields1002)
            newline(pp)
            for (i1561, elem1003) in enumerate(fields1002)
                i1004 = i1561 - 1
                if (i1004 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1003)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1012 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1012)
        write(pp, flat1012)
        return nothing
    else
        function _t1562(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args,)
        end
        _t1563 = _t1562(msg)
        fields1006 = _t1563
        unwrapped_fields1007 = fields1006
        write(pp, "(")
        write(pp, "attribute")
        indent_sexp!(pp)
        newline(pp)
        field1008 = unwrapped_fields1007[1]
        pretty_name(pp, field1008)
        field1009 = unwrapped_fields1007[2]
        if !isempty(field1009)
            newline(pp)
            for (i1564, elem1010) in enumerate(field1009)
                i1011 = i1564 - 1
                if (i1011 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem1010)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1019 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1019)
        write(pp, flat1019)
        return nothing
    else
        function _t1565(_dollar_dollar)
            return (_dollar_dollar.var"#global", _dollar_dollar.body,)
        end
        _t1566 = _t1565(msg)
        fields1013 = _t1566
        unwrapped_fields1014 = fields1013
        write(pp, "(")
        write(pp, "algorithm")
        indent_sexp!(pp)
        field1015 = unwrapped_fields1014[1]
        if !isempty(field1015)
            newline(pp)
            for (i1567, elem1016) in enumerate(field1015)
                i1017 = i1567 - 1
                if (i1017 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1016)
            end
        end
        newline(pp)
        field1018 = unwrapped_fields1014[2]
        pretty_script(pp, field1018)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1024 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1024)
        write(pp, flat1024)
        return nothing
    else
        function _t1568(_dollar_dollar)
            return _dollar_dollar.constructs
        end
        _t1569 = _t1568(msg)
        fields1020 = _t1569
        unwrapped_fields1021 = fields1020
        write(pp, "(")
        write(pp, "script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1021)
            newline(pp)
            for (i1570, elem1022) in enumerate(unwrapped_fields1021)
                i1023 = i1570 - 1
                if (i1023 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1022)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1029 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1029)
        write(pp, flat1029)
        return nothing
    else
        function _t1571(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("loop"))
                _t1572 = _get_oneof_field(_dollar_dollar, :loop)
            else
                _t1572 = nothing
            end
            return _t1572
        end
        _t1573 = _t1571(msg)
        deconstruct_result1027 = _t1573
        if !isnothing(deconstruct_result1027)
            unwrapped1028 = deconstruct_result1027
            pretty_loop(pp, unwrapped1028)
        else
            function _t1574(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                    _t1575 = _get_oneof_field(_dollar_dollar, :instruction)
                else
                    _t1575 = nothing
                end
                return _t1575
            end
            _t1576 = _t1574(msg)
            deconstruct_result1025 = _t1576
            if !isnothing(deconstruct_result1025)
                unwrapped1026 = deconstruct_result1025
                pretty_instruction(pp, unwrapped1026)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1034 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1034)
        write(pp, flat1034)
        return nothing
    else
        function _t1577(_dollar_dollar)
            return (_dollar_dollar.init, _dollar_dollar.body,)
        end
        _t1578 = _t1577(msg)
        fields1030 = _t1578
        unwrapped_fields1031 = fields1030
        write(pp, "(")
        write(pp, "loop")
        indent_sexp!(pp)
        newline(pp)
        field1032 = unwrapped_fields1031[1]
        pretty_init(pp, field1032)
        newline(pp)
        field1033 = unwrapped_fields1031[2]
        pretty_script(pp, field1033)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1038 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1038)
        write(pp, flat1038)
        return nothing
    else
        fields1035 = msg
        write(pp, "(")
        write(pp, "init")
        indent_sexp!(pp)
        if !isempty(fields1035)
            newline(pp)
            for (i1579, elem1036) in enumerate(fields1035)
                i1037 = i1579 - 1
                if (i1037 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1036)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1049 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1049)
        write(pp, flat1049)
        return nothing
    else
        function _t1580(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("assign"))
                _t1581 = _get_oneof_field(_dollar_dollar, :assign)
            else
                _t1581 = nothing
            end
            return _t1581
        end
        _t1582 = _t1580(msg)
        deconstruct_result1047 = _t1582
        if !isnothing(deconstruct_result1047)
            unwrapped1048 = deconstruct_result1047
            pretty_assign(pp, unwrapped1048)
        else
            function _t1583(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                    _t1584 = _get_oneof_field(_dollar_dollar, :upsert)
                else
                    _t1584 = nothing
                end
                return _t1584
            end
            _t1585 = _t1583(msg)
            deconstruct_result1045 = _t1585
            if !isnothing(deconstruct_result1045)
                unwrapped1046 = deconstruct_result1045
                pretty_upsert(pp, unwrapped1046)
            else
                function _t1586(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("#break"))
                        _t1587 = _get_oneof_field(_dollar_dollar, :var"#break")
                    else
                        _t1587 = nothing
                    end
                    return _t1587
                end
                _t1588 = _t1586(msg)
                deconstruct_result1043 = _t1588
                if !isnothing(deconstruct_result1043)
                    unwrapped1044 = deconstruct_result1043
                    pretty_break(pp, unwrapped1044)
                else
                    function _t1589(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                            _t1590 = _get_oneof_field(_dollar_dollar, :monoid_def)
                        else
                            _t1590 = nothing
                        end
                        return _t1590
                    end
                    _t1591 = _t1589(msg)
                    deconstruct_result1041 = _t1591
                    if !isnothing(deconstruct_result1041)
                        unwrapped1042 = deconstruct_result1041
                        pretty_monoid_def(pp, unwrapped1042)
                    else
                        function _t1592(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                                _t1593 = _get_oneof_field(_dollar_dollar, :monus_def)
                            else
                                _t1593 = nothing
                            end
                            return _t1593
                        end
                        _t1594 = _t1592(msg)
                        deconstruct_result1039 = _t1594
                        if !isnothing(deconstruct_result1039)
                            unwrapped1040 = deconstruct_result1039
                            pretty_monus_def(pp, unwrapped1040)
                        else
                            throw(ParseError("No matching rule for instruction"))
                        end
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_assign(pp::PrettyPrinter, msg::Proto.Assign)
    flat1056 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1056)
        write(pp, flat1056)
        return nothing
    else
        function _t1595(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1596 = _dollar_dollar.attrs
            else
                _t1596 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1596,)
        end
        _t1597 = _t1595(msg)
        fields1050 = _t1597
        unwrapped_fields1051 = fields1050
        write(pp, "(")
        write(pp, "assign")
        indent_sexp!(pp)
        newline(pp)
        field1052 = unwrapped_fields1051[1]
        pretty_relation_id(pp, field1052)
        newline(pp)
        field1053 = unwrapped_fields1051[2]
        pretty_abstraction(pp, field1053)
        field1054 = unwrapped_fields1051[3]
        if !isnothing(field1054)
            newline(pp)
            opt_val1055 = field1054
            pretty_attrs(pp, opt_val1055)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1063 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1063)
        write(pp, flat1063)
        return nothing
    else
        function _t1598(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1599 = _dollar_dollar.attrs
            else
                _t1599 = nothing
            end
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1599,)
        end
        _t1600 = _t1598(msg)
        fields1057 = _t1600
        unwrapped_fields1058 = fields1057
        write(pp, "(")
        write(pp, "upsert")
        indent_sexp!(pp)
        newline(pp)
        field1059 = unwrapped_fields1058[1]
        pretty_relation_id(pp, field1059)
        newline(pp)
        field1060 = unwrapped_fields1058[2]
        pretty_abstraction_with_arity(pp, field1060)
        field1061 = unwrapped_fields1058[3]
        if !isnothing(field1061)
            newline(pp)
            opt_val1062 = field1061
            pretty_attrs(pp, opt_val1062)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1068 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1068)
        write(pp, flat1068)
        return nothing
    else
        function _t1601(_dollar_dollar)
            _t1602 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
            return (_t1602, _dollar_dollar[1].value,)
        end
        _t1603 = _t1601(msg)
        fields1064 = _t1603
        unwrapped_fields1065 = fields1064
        write(pp, "(")
        indent!(pp)
        field1066 = unwrapped_fields1065[1]
        pretty_bindings(pp, field1066)
        newline(pp)
        field1067 = unwrapped_fields1065[2]
        pretty_formula(pp, field1067)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1075 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1075)
        write(pp, flat1075)
        return nothing
    else
        function _t1604(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1605 = _dollar_dollar.attrs
            else
                _t1605 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1605,)
        end
        _t1606 = _t1604(msg)
        fields1069 = _t1606
        unwrapped_fields1070 = fields1069
        write(pp, "(")
        write(pp, "break")
        indent_sexp!(pp)
        newline(pp)
        field1071 = unwrapped_fields1070[1]
        pretty_relation_id(pp, field1071)
        newline(pp)
        field1072 = unwrapped_fields1070[2]
        pretty_abstraction(pp, field1072)
        field1073 = unwrapped_fields1070[3]
        if !isnothing(field1073)
            newline(pp)
            opt_val1074 = field1073
            pretty_attrs(pp, opt_val1074)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1083 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1083)
        write(pp, flat1083)
        return nothing
    else
        function _t1607(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1608 = _dollar_dollar.attrs
            else
                _t1608 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1608,)
        end
        _t1609 = _t1607(msg)
        fields1076 = _t1609
        unwrapped_fields1077 = fields1076
        write(pp, "(")
        write(pp, "monoid")
        indent_sexp!(pp)
        newline(pp)
        field1078 = unwrapped_fields1077[1]
        pretty_monoid(pp, field1078)
        newline(pp)
        field1079 = unwrapped_fields1077[2]
        pretty_relation_id(pp, field1079)
        newline(pp)
        field1080 = unwrapped_fields1077[3]
        pretty_abstraction_with_arity(pp, field1080)
        field1081 = unwrapped_fields1077[4]
        if !isnothing(field1081)
            newline(pp)
            opt_val1082 = field1081
            pretty_attrs(pp, opt_val1082)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1092 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        function _t1610(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
                _t1611 = _get_oneof_field(_dollar_dollar, :or_monoid)
            else
                _t1611 = nothing
            end
            return _t1611
        end
        _t1612 = _t1610(msg)
        deconstruct_result1090 = _t1612
        if !isnothing(deconstruct_result1090)
            unwrapped1091 = deconstruct_result1090
            pretty_or_monoid(pp, unwrapped1091)
        else
            function _t1613(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                    _t1614 = _get_oneof_field(_dollar_dollar, :min_monoid)
                else
                    _t1614 = nothing
                end
                return _t1614
            end
            _t1615 = _t1613(msg)
            deconstruct_result1088 = _t1615
            if !isnothing(deconstruct_result1088)
                unwrapped1089 = deconstruct_result1088
                pretty_min_monoid(pp, unwrapped1089)
            else
                function _t1616(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                        _t1617 = _get_oneof_field(_dollar_dollar, :max_monoid)
                    else
                        _t1617 = nothing
                    end
                    return _t1617
                end
                _t1618 = _t1616(msg)
                deconstruct_result1086 = _t1618
                if !isnothing(deconstruct_result1086)
                    unwrapped1087 = deconstruct_result1086
                    pretty_max_monoid(pp, unwrapped1087)
                else
                    function _t1619(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                            _t1620 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                        else
                            _t1620 = nothing
                        end
                        return _t1620
                    end
                    _t1621 = _t1619(msg)
                    deconstruct_result1084 = _t1621
                    if !isnothing(deconstruct_result1084)
                        unwrapped1085 = deconstruct_result1084
                        pretty_sum_monoid(pp, unwrapped1085)
                    else
                        throw(ParseError("No matching rule for monoid"))
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_or_monoid(pp::PrettyPrinter, msg::Proto.OrMonoid)
    fields1093 = msg
    write(pp, "(")
    write(pp, "or")
    write(pp, ")")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1096 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        function _t1622(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1623 = _t1622(msg)
        fields1094 = _t1623
        unwrapped_fields1095 = fields1094
        write(pp, "(")
        write(pp, "min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1095)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1099 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1099)
        write(pp, flat1099)
        return nothing
    else
        function _t1624(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1625 = _t1624(msg)
        fields1097 = _t1625
        unwrapped_fields1098 = fields1097
        write(pp, "(")
        write(pp, "max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1098)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1102 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1102)
        write(pp, flat1102)
        return nothing
    else
        function _t1626(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1627 = _t1626(msg)
        fields1100 = _t1627
        unwrapped_fields1101 = fields1100
        write(pp, "(")
        write(pp, "sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1101)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1110 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1110)
        write(pp, flat1110)
        return nothing
    else
        function _t1628(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1629 = _dollar_dollar.attrs
            else
                _t1629 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1629,)
        end
        _t1630 = _t1628(msg)
        fields1103 = _t1630
        unwrapped_fields1104 = fields1103
        write(pp, "(")
        write(pp, "monus")
        indent_sexp!(pp)
        newline(pp)
        field1105 = unwrapped_fields1104[1]
        pretty_monoid(pp, field1105)
        newline(pp)
        field1106 = unwrapped_fields1104[2]
        pretty_relation_id(pp, field1106)
        newline(pp)
        field1107 = unwrapped_fields1104[3]
        pretty_abstraction_with_arity(pp, field1107)
        field1108 = unwrapped_fields1104[4]
        if !isnothing(field1108)
            newline(pp)
            opt_val1109 = field1108
            pretty_attrs(pp, opt_val1109)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1117 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1117)
        write(pp, flat1117)
        return nothing
    else
        function _t1631(_dollar_dollar)
            return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        end
        _t1632 = _t1631(msg)
        fields1111 = _t1632
        unwrapped_fields1112 = fields1111
        write(pp, "(")
        write(pp, "functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1113 = unwrapped_fields1112[1]
        pretty_relation_id(pp, field1113)
        newline(pp)
        field1114 = unwrapped_fields1112[2]
        pretty_abstraction(pp, field1114)
        newline(pp)
        field1115 = unwrapped_fields1112[3]
        pretty_functional_dependency_keys(pp, field1115)
        newline(pp)
        field1116 = unwrapped_fields1112[4]
        pretty_functional_dependency_values(pp, field1116)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1121 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1121)
        write(pp, flat1121)
        return nothing
    else
        fields1118 = msg
        write(pp, "(")
        write(pp, "keys")
        indent_sexp!(pp)
        if !isempty(fields1118)
            newline(pp)
            for (i1633, elem1119) in enumerate(fields1118)
                i1120 = i1633 - 1
                if (i1120 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1119)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1125 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1125)
        write(pp, flat1125)
        return nothing
    else
        fields1122 = msg
        write(pp, "(")
        write(pp, "values")
        indent_sexp!(pp)
        if !isempty(fields1122)
            newline(pp)
            for (i1634, elem1123) in enumerate(fields1122)
                i1124 = i1634 - 1
                if (i1124 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1123)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1132 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1132)
        write(pp, flat1132)
        return nothing
    else
        function _t1635(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("rel_edb"))
                _t1636 = _get_oneof_field(_dollar_dollar, :rel_edb)
            else
                _t1636 = nothing
            end
            return _t1636
        end
        _t1637 = _t1635(msg)
        deconstruct_result1130 = _t1637
        if !isnothing(deconstruct_result1130)
            unwrapped1131 = deconstruct_result1130
            pretty_rel_edb(pp, unwrapped1131)
        else
            function _t1638(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                    _t1639 = _get_oneof_field(_dollar_dollar, :betree_relation)
                else
                    _t1639 = nothing
                end
                return _t1639
            end
            _t1640 = _t1638(msg)
            deconstruct_result1128 = _t1640
            if !isnothing(deconstruct_result1128)
                unwrapped1129 = deconstruct_result1128
                pretty_betree_relation(pp, unwrapped1129)
            else
                function _t1641(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                        _t1642 = _get_oneof_field(_dollar_dollar, :csv_data)
                    else
                        _t1642 = nothing
                    end
                    return _t1642
                end
                _t1643 = _t1641(msg)
                deconstruct_result1126 = _t1643
                if !isnothing(deconstruct_result1126)
                    unwrapped1127 = deconstruct_result1126
                    pretty_csv_data(pp, unwrapped1127)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_rel_edb(pp::PrettyPrinter, msg::Proto.RelEDB)
    flat1138 = try_flat(pp, msg, pretty_rel_edb)
    if !isnothing(flat1138)
        write(pp, flat1138)
        return nothing
    else
        function _t1644(_dollar_dollar)
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        end
        _t1645 = _t1644(msg)
        fields1133 = _t1645
        unwrapped_fields1134 = fields1133
        write(pp, "(")
        write(pp, "rel_edb")
        indent_sexp!(pp)
        newline(pp)
        field1135 = unwrapped_fields1134[1]
        pretty_relation_id(pp, field1135)
        newline(pp)
        field1136 = unwrapped_fields1134[2]
        pretty_rel_edb_path(pp, field1136)
        newline(pp)
        field1137 = unwrapped_fields1134[3]
        pretty_rel_edb_types(pp, field1137)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1142 = try_flat(pp, msg, pretty_rel_edb_path)
    if !isnothing(flat1142)
        write(pp, flat1142)
        return nothing
    else
        fields1139 = msg
        write(pp, "[")
        indent!(pp)
        for (i1646, elem1140) in enumerate(fields1139)
            i1141 = i1646 - 1
            if (i1141 > 0)
                newline(pp)
            end
            write(pp, format_string_value(elem1140))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_rel_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1146 = try_flat(pp, msg, pretty_rel_edb_types)
    if !isnothing(flat1146)
        write(pp, flat1146)
        return nothing
    else
        fields1143 = msg
        write(pp, "[")
        indent!(pp)
        for (i1647, elem1144) in enumerate(fields1143)
            i1145 = i1647 - 1
            if (i1145 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1144)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1151 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1151)
        write(pp, flat1151)
        return nothing
    else
        function _t1648(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        end
        _t1649 = _t1648(msg)
        fields1147 = _t1649
        unwrapped_fields1148 = fields1147
        write(pp, "(")
        write(pp, "betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1149 = unwrapped_fields1148[1]
        pretty_relation_id(pp, field1149)
        newline(pp)
        field1150 = unwrapped_fields1148[2]
        pretty_betree_info(pp, field1150)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1157 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1157)
        write(pp, flat1157)
        return nothing
    else
        function _t1650(_dollar_dollar)
            _t1651 = deconstruct_betree_info_config(pp, _dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1651,)
        end
        _t1652 = _t1650(msg)
        fields1152 = _t1652
        unwrapped_fields1153 = fields1152
        write(pp, "(")
        write(pp, "betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1154 = unwrapped_fields1153[1]
        pretty_betree_info_key_types(pp, field1154)
        newline(pp)
        field1155 = unwrapped_fields1153[2]
        pretty_betree_info_value_types(pp, field1155)
        newline(pp)
        field1156 = unwrapped_fields1153[3]
        pretty_config_dict(pp, field1156)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1161 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1161)
        write(pp, flat1161)
        return nothing
    else
        fields1158 = msg
        write(pp, "(")
        write(pp, "key_types")
        indent_sexp!(pp)
        if !isempty(fields1158)
            newline(pp)
            for (i1653, elem1159) in enumerate(fields1158)
                i1160 = i1653 - 1
                if (i1160 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1159)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1165 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1165)
        write(pp, flat1165)
        return nothing
    else
        fields1162 = msg
        write(pp, "(")
        write(pp, "value_types")
        indent_sexp!(pp)
        if !isempty(fields1162)
            newline(pp)
            for (i1654, elem1163) in enumerate(fields1162)
                i1164 = i1654 - 1
                if (i1164 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1163)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1172 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1172)
        write(pp, flat1172)
        return nothing
    else
        function _t1655(_dollar_dollar)
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        end
        _t1656 = _t1655(msg)
        fields1166 = _t1656
        unwrapped_fields1167 = fields1166
        write(pp, "(")
        write(pp, "csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1168 = unwrapped_fields1167[1]
        pretty_csvlocator(pp, field1168)
        newline(pp)
        field1169 = unwrapped_fields1167[2]
        pretty_csv_config(pp, field1169)
        newline(pp)
        field1170 = unwrapped_fields1167[3]
        pretty_csv_columns(pp, field1170)
        newline(pp)
        field1171 = unwrapped_fields1167[4]
        pretty_csv_asof(pp, field1171)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1179 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        function _t1657(_dollar_dollar)
            if !isempty(_dollar_dollar.paths)
                _t1658 = _dollar_dollar.paths
            else
                _t1658 = nothing
            end
            if String(copy(_dollar_dollar.inline_data)) != ""
                _t1659 = String(copy(_dollar_dollar.inline_data))
            else
                _t1659 = nothing
            end
            return (_t1658, _t1659,)
        end
        _t1660 = _t1657(msg)
        fields1173 = _t1660
        unwrapped_fields1174 = fields1173
        write(pp, "(")
        write(pp, "csv_locator")
        indent_sexp!(pp)
        field1175 = unwrapped_fields1174[1]
        if !isnothing(field1175)
            newline(pp)
            opt_val1176 = field1175
            pretty_csv_locator_paths(pp, opt_val1176)
        end
        field1177 = unwrapped_fields1174[2]
        if !isnothing(field1177)
            newline(pp)
            opt_val1178 = field1177
            pretty_csv_locator_inline_data(pp, opt_val1178)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1183 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1183)
        write(pp, flat1183)
        return nothing
    else
        fields1180 = msg
        write(pp, "(")
        write(pp, "paths")
        indent_sexp!(pp)
        if !isempty(fields1180)
            newline(pp)
            for (i1661, elem1181) in enumerate(fields1180)
                i1182 = i1661 - 1
                if (i1182 > 0)
                    newline(pp)
                end
                write(pp, format_string_value(elem1181))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1185 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1185)
        write(pp, flat1185)
        return nothing
    else
        fields1184 = msg
        write(pp, "(")
        write(pp, "inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(fields1184))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1188 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1188)
        write(pp, flat1188)
        return nothing
    else
        function _t1662(_dollar_dollar)
            _t1663 = deconstruct_csv_config(pp, _dollar_dollar)
            return _t1663
        end
        _t1664 = _t1662(msg)
        fields1186 = _t1664
        unwrapped_fields1187 = fields1186
        write(pp, "(")
        write(pp, "csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1187)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.CSVColumn})
    flat1192 = try_flat(pp, msg, pretty_csv_columns)
    if !isnothing(flat1192)
        write(pp, flat1192)
        return nothing
    else
        fields1189 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1189)
            newline(pp)
            for (i1665, elem1190) in enumerate(fields1189)
                i1191 = i1665 - 1
                if (i1191 > 0)
                    newline(pp)
                end
                pretty_csv_column(pp, elem1190)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_column(pp::PrettyPrinter, msg::Proto.CSVColumn)
    flat1200 = try_flat(pp, msg, pretty_csv_column)
    if !isnothing(flat1200)
        write(pp, flat1200)
        return nothing
    else
        function _t1666(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        end
        _t1667 = _t1666(msg)
        fields1193 = _t1667
        unwrapped_fields1194 = fields1193
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1195 = unwrapped_fields1194[1]
        write(pp, format_string_value(field1195))
        newline(pp)
        field1196 = unwrapped_fields1194[2]
        pretty_relation_id(pp, field1196)
        newline(pp)
        write(pp, "[")
        field1197 = unwrapped_fields1194[3]
        for (i1668, elem1198) in enumerate(field1197)
            i1199 = i1668 - 1
            if (i1199 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1198)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1202 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1202)
        write(pp, flat1202)
        return nothing
    else
        fields1201 = msg
        write(pp, "(")
        write(pp, "asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(fields1201))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1205 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1205)
        write(pp, flat1205)
        return nothing
    else
        function _t1669(_dollar_dollar)
            return _dollar_dollar.fragment_id
        end
        _t1670 = _t1669(msg)
        fields1203 = _t1670
        unwrapped_fields1204 = fields1203
        write(pp, "(")
        write(pp, "undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1204)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1210 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1210)
        write(pp, flat1210)
        return nothing
    else
        function _t1671(_dollar_dollar)
            return _dollar_dollar.relations
        end
        _t1672 = _t1671(msg)
        fields1206 = _t1672
        unwrapped_fields1207 = fields1206
        write(pp, "(")
        write(pp, "context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1207)
            newline(pp)
            for (i1673, elem1208) in enumerate(unwrapped_fields1207)
                i1209 = i1673 - 1
                if (i1209 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1208)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1215 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        function _t1674(_dollar_dollar)
            return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        end
        _t1675 = _t1674(msg)
        fields1211 = _t1675
        unwrapped_fields1212 = fields1211
        write(pp, "(")
        write(pp, "snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1213 = unwrapped_fields1212[1]
        pretty_rel_edb_path(pp, field1213)
        newline(pp)
        field1214 = unwrapped_fields1212[2]
        pretty_relation_id(pp, field1214)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1219 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1219)
        write(pp, flat1219)
        return nothing
    else
        fields1216 = msg
        write(pp, "(")
        write(pp, "reads")
        indent_sexp!(pp)
        if !isempty(fields1216)
            newline(pp)
            for (i1676, elem1217) in enumerate(fields1216)
                i1218 = i1676 - 1
                if (i1218 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1217)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1230 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1230)
        write(pp, flat1230)
        return nothing
    else
        function _t1677(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("demand"))
                _t1678 = _get_oneof_field(_dollar_dollar, :demand)
            else
                _t1678 = nothing
            end
            return _t1678
        end
        _t1679 = _t1677(msg)
        deconstruct_result1228 = _t1679
        if !isnothing(deconstruct_result1228)
            unwrapped1229 = deconstruct_result1228
            pretty_demand(pp, unwrapped1229)
        else
            function _t1680(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("output"))
                    _t1681 = _get_oneof_field(_dollar_dollar, :output)
                else
                    _t1681 = nothing
                end
                return _t1681
            end
            _t1682 = _t1680(msg)
            deconstruct_result1226 = _t1682
            if !isnothing(deconstruct_result1226)
                unwrapped1227 = deconstruct_result1226
                pretty_output(pp, unwrapped1227)
            else
                function _t1683(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                        _t1684 = _get_oneof_field(_dollar_dollar, :what_if)
                    else
                        _t1684 = nothing
                    end
                    return _t1684
                end
                _t1685 = _t1683(msg)
                deconstruct_result1224 = _t1685
                if !isnothing(deconstruct_result1224)
                    unwrapped1225 = deconstruct_result1224
                    pretty_what_if(pp, unwrapped1225)
                else
                    function _t1686(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("abort"))
                            _t1687 = _get_oneof_field(_dollar_dollar, :abort)
                        else
                            _t1687 = nothing
                        end
                        return _t1687
                    end
                    _t1688 = _t1686(msg)
                    deconstruct_result1222 = _t1688
                    if !isnothing(deconstruct_result1222)
                        unwrapped1223 = deconstruct_result1222
                        pretty_abort(pp, unwrapped1223)
                    else
                        function _t1689(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("#export"))
                                _t1690 = _get_oneof_field(_dollar_dollar, :var"#export")
                            else
                                _t1690 = nothing
                            end
                            return _t1690
                        end
                        _t1691 = _t1689(msg)
                        deconstruct_result1220 = _t1691
                        if !isnothing(deconstruct_result1220)
                            unwrapped1221 = deconstruct_result1220
                            pretty_export(pp, unwrapped1221)
                        else
                            throw(ParseError("No matching rule for read"))
                        end
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_demand(pp::PrettyPrinter, msg::Proto.Demand)
    flat1233 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1233)
        write(pp, flat1233)
        return nothing
    else
        function _t1692(_dollar_dollar)
            return _dollar_dollar.relation_id
        end
        _t1693 = _t1692(msg)
        fields1231 = _t1693
        unwrapped_fields1232 = fields1231
        write(pp, "(")
        write(pp, "demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1232)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1238 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1238)
        write(pp, flat1238)
        return nothing
    else
        function _t1694(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        end
        _t1695 = _t1694(msg)
        fields1234 = _t1695
        unwrapped_fields1235 = fields1234
        write(pp, "(")
        write(pp, "output")
        indent_sexp!(pp)
        newline(pp)
        field1236 = unwrapped_fields1235[1]
        pretty_name(pp, field1236)
        newline(pp)
        field1237 = unwrapped_fields1235[2]
        pretty_relation_id(pp, field1237)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1243 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1243)
        write(pp, flat1243)
        return nothing
    else
        function _t1696(_dollar_dollar)
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        end
        _t1697 = _t1696(msg)
        fields1239 = _t1697
        unwrapped_fields1240 = fields1239
        write(pp, "(")
        write(pp, "what_if")
        indent_sexp!(pp)
        newline(pp)
        field1241 = unwrapped_fields1240[1]
        pretty_name(pp, field1241)
        newline(pp)
        field1242 = unwrapped_fields1240[2]
        pretty_epoch(pp, field1242)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1249 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1249)
        write(pp, flat1249)
        return nothing
    else
        function _t1698(_dollar_dollar)
            if _dollar_dollar.name != "abort"
                _t1699 = _dollar_dollar.name
            else
                _t1699 = nothing
            end
            return (_t1699, _dollar_dollar.relation_id,)
        end
        _t1700 = _t1698(msg)
        fields1244 = _t1700
        unwrapped_fields1245 = fields1244
        write(pp, "(")
        write(pp, "abort")
        indent_sexp!(pp)
        field1246 = unwrapped_fields1245[1]
        if !isnothing(field1246)
            newline(pp)
            opt_val1247 = field1246
            pretty_name(pp, opt_val1247)
        end
        newline(pp)
        field1248 = unwrapped_fields1245[2]
        pretty_relation_id(pp, field1248)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1252 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1252)
        write(pp, flat1252)
        return nothing
    else
        function _t1701(_dollar_dollar)
            return _get_oneof_field(_dollar_dollar, :csv_config)
        end
        _t1702 = _t1701(msg)
        fields1250 = _t1702
        unwrapped_fields1251 = fields1250
        write(pp, "(")
        write(pp, "export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1251)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1263 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1263)
        write(pp, flat1263)
        return nothing
    else
        function _t1703(_dollar_dollar)
            if length(_dollar_dollar.data_columns) == 0
                _t1704 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else
                _t1704 = nothing
            end
            return _t1704
        end
        _t1705 = _t1703(msg)
        deconstruct_result1258 = _t1705
        if !isnothing(deconstruct_result1258)
            unwrapped1259 = deconstruct_result1258
            write(pp, "(")
            write(pp, "export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1260 = unwrapped1259[1]
            pretty_export_csv_path(pp, field1260)
            newline(pp)
            field1261 = unwrapped1259[2]
            pretty_export_csv_source(pp, field1261)
            newline(pp)
            field1262 = unwrapped1259[3]
            pretty_csv_config(pp, field1262)
            dedent!(pp)
            write(pp, ")")
        else
            function _t1706(_dollar_dollar)
                if length(_dollar_dollar.data_columns) != 0
                    _t1708 = deconstruct_export_csv_config(pp, _dollar_dollar)
                    _t1707 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1708,)
                else
                    _t1707 = nothing
                end
                return _t1707
            end
            _t1709 = _t1706(msg)
            deconstruct_result1253 = _t1709
            if !isnothing(deconstruct_result1253)
                unwrapped1254 = deconstruct_result1253
                write(pp, "(")
                write(pp, "export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1255 = unwrapped1254[1]
                pretty_export_csv_path(pp, field1255)
                newline(pp)
                field1256 = unwrapped1254[2]
                pretty_export_csv_columns(pp, field1256)
                newline(pp)
                field1257 = unwrapped1254[3]
                pretty_config_dict(pp, field1257)
                dedent!(pp)
                write(pp, ")")
            else
                throw(ParseError("No matching rule for export_csv_config"))
            end
        end
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1265 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1265)
        write(pp, flat1265)
        return nothing
    else
        fields1264 = msg
        write(pp, "(")
        write(pp, "path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(fields1264))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1272 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1272)
        write(pp, flat1272)
        return nothing
    else
        function _t1710(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
                _t1711 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
            else
                _t1711 = nothing
            end
            return _t1711
        end
        _t1712 = _t1710(msg)
        deconstruct_result1268 = _t1712
        if !isnothing(deconstruct_result1268)
            unwrapped1269 = deconstruct_result1268
            write(pp, "(")
            write(pp, "gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1269)
                newline(pp)
                for (i1713, elem1270) in enumerate(unwrapped1269)
                    i1271 = i1713 - 1
                    if (i1271 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1270)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            function _t1714(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                    _t1715 = _get_oneof_field(_dollar_dollar, :table_def)
                else
                    _t1715 = nothing
                end
                return _t1715
            end
            _t1716 = _t1714(msg)
            deconstruct_result1266 = _t1716
            if !isnothing(deconstruct_result1266)
                unwrapped1267 = deconstruct_result1266
                write(pp, "(")
                write(pp, "table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1267)
                dedent!(pp)
                write(pp, ")")
            else
                throw(ParseError("No matching rule for export_csv_source"))
            end
        end
    end
    return nothing
end

function pretty_export_csv_column(pp::PrettyPrinter, msg::Proto.ExportCSVColumn)
    flat1277 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1277)
        write(pp, flat1277)
        return nothing
    else
        function _t1717(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        end
        _t1718 = _t1717(msg)
        fields1273 = _t1718
        unwrapped_fields1274 = fields1273
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1275 = unwrapped_fields1274[1]
        write(pp, format_string_value(field1275))
        newline(pp)
        field1276 = unwrapped_fields1274[2]
        pretty_relation_id(pp, field1276)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1281 = try_flat(pp, msg, pretty_export_csv_columns)
    if !isnothing(flat1281)
        write(pp, flat1281)
        return nothing
    else
        fields1278 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1278)
            newline(pp)
            for (i1719, elem1279) in enumerate(fields1278)
                i1280 = i1719 - 1
                if (i1280 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1279)
            end
        end
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
