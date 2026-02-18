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
    _t1666 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1666
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1667 = Proto.Value(value=OneOf(:int_value, v))
    return _t1667
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1668 = Proto.Value(value=OneOf(:float_value, v))
    return _t1668
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1669 = Proto.Value(value=OneOf(:string_value, v))
    return _t1669
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1670 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1670
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1671 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1671
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1672 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1672,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1673 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1673,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1674 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1674,))
            end
        end
    end
    _t1675 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1675,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1676 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1676,))
    _t1677 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1677,))
    if msg.new_line != ""
        _t1678 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1678,))
    end
    _t1679 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1679,))
    _t1680 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1680,))
    _t1681 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1681,))
    if msg.comment != ""
        _t1682 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1682,))
    end
    for missing_string in msg.missing_strings
        _t1683 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1683,))
    end
    _t1684 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1684,))
    _t1685 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1685,))
    _t1686 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1686,))
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1687 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1687,))
    _t1688 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1688,))
    _t1689 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1689,))
    _t1690 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1690,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1691 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1691,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1692 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1692,))
        end
    end
    _t1693 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1693,))
    _t1694 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1694,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1695 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1695,))
    end
    if !isnothing(msg.compression)
        _t1696 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1696,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1697 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1697,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1698 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1698,))
    end
    if !isnothing(msg.syntax_delim)
        _t1699 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1699,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1700 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1700,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1701 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1701,))
    end
    return sort(result)
end

function deconstruct_relation_id_string(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, String}
    name = relation_id_to_string(pp, msg)
    if name != ""
        return name
    else
        _t1702 = nothing
    end
    return nothing
end

function deconstruct_relation_id_uint128(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, Proto.UInt128Value}
    name = relation_id_to_string(pp, msg)
    if name == ""
        return relation_id_to_uint128(pp, msg)
    else
        _t1703 = nothing
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
    flat631 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat631)
        write(pp, flat631)
        return nothing
    else
        function _t1244(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("configure"))
                _t1245 = _dollar_dollar.configure
            else
                _t1245 = nothing
            end
            if _has_proto_field(_dollar_dollar, Symbol("sync"))
                _t1246 = _dollar_dollar.sync
            else
                _t1246 = nothing
            end
            return (_t1245, _t1246, _dollar_dollar.epochs,)
        end
        _t1247 = _t1244(msg)
        fields622 = _t1247
        unwrapped_fields623 = fields622
        write(pp, "(")
        write(pp, "transaction")
        indent_sexp!(pp)
        field624 = unwrapped_fields623[1]
        if !isnothing(field624)
            newline(pp)
            opt_val625 = field624
            pretty_configure(pp, opt_val625)
        end
        field626 = unwrapped_fields623[2]
        if !isnothing(field626)
            newline(pp)
            opt_val627 = field626
            pretty_sync(pp, opt_val627)
        end
        field628 = unwrapped_fields623[3]
        if !isempty(field628)
            newline(pp)
            for (i1248, elem629) in enumerate(field628)
                i630 = i1248 - 1
                if (i630 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem629)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat634 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat634)
        write(pp, flat634)
        return nothing
    else
        function _t1249(_dollar_dollar)
            _t1250 = deconstruct_configure(pp, _dollar_dollar)
            return _t1250
        end
        _t1251 = _t1249(msg)
        fields632 = _t1251
        unwrapped_fields633 = fields632
        write(pp, "(")
        write(pp, "configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields633)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat638 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat638)
        write(pp, flat638)
        return nothing
    else
        fields635 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields635)
            newline(pp)
            for (i1252, elem636) in enumerate(fields635)
                i637 = i1252 - 1
                if (i637 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem636)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat643 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat643)
        write(pp, flat643)
        return nothing
    else
        function _t1253(_dollar_dollar)
            return (_dollar_dollar[1], _dollar_dollar[2],)
        end
        _t1254 = _t1253(msg)
        fields639 = _t1254
        unwrapped_fields640 = fields639
        write(pp, ":")
        field641 = unwrapped_fields640[1]
        write(pp, field641)
        write(pp, " ")
        field642 = unwrapped_fields640[2]
        pretty_value(pp, field642)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat663 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat663)
        write(pp, flat663)
        return nothing
    else
        function _t1255(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("date_value"))
                _t1256 = _get_oneof_field(_dollar_dollar, :date_value)
            else
                _t1256 = nothing
            end
            return _t1256
        end
        _t1257 = _t1255(msg)
        deconstruct_result661 = _t1257
        if !isnothing(deconstruct_result661)
            unwrapped662 = deconstruct_result661
            pretty_date(pp, unwrapped662)
        else
            function _t1258(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                    _t1259 = _get_oneof_field(_dollar_dollar, :datetime_value)
                else
                    _t1259 = nothing
                end
                return _t1259
            end
            _t1260 = _t1258(msg)
            deconstruct_result659 = _t1260
            if !isnothing(deconstruct_result659)
                unwrapped660 = deconstruct_result659
                pretty_datetime(pp, unwrapped660)
            else
                function _t1261(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                        _t1262 = _get_oneof_field(_dollar_dollar, :string_value)
                    else
                        _t1262 = nothing
                    end
                    return _t1262
                end
                _t1263 = _t1261(msg)
                deconstruct_result657 = _t1263
                if !isnothing(deconstruct_result657)
                    unwrapped658 = deconstruct_result657
                    write(pp, format_string_value(unwrapped658))
                else
                    function _t1264(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1265 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1265 = nothing
                        end
                        return _t1265
                    end
                    _t1266 = _t1264(msg)
                    deconstruct_result655 = _t1266
                    if !isnothing(deconstruct_result655)
                        unwrapped656 = deconstruct_result655
                        write(pp, string(unwrapped656))
                    else
                        function _t1267(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                _t1268 = _get_oneof_field(_dollar_dollar, :float_value)
                            else
                                _t1268 = nothing
                            end
                            return _t1268
                        end
                        _t1269 = _t1267(msg)
                        deconstruct_result653 = _t1269
                        if !isnothing(deconstruct_result653)
                            unwrapped654 = deconstruct_result653
                            write(pp, format_float64(unwrapped654))
                        else
                            function _t1270(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                    _t1271 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                else
                                    _t1271 = nothing
                                end
                                return _t1271
                            end
                            _t1272 = _t1270(msg)
                            deconstruct_result651 = _t1272
                            if !isnothing(deconstruct_result651)
                                unwrapped652 = deconstruct_result651
                                write(pp, format_uint128(pp, unwrapped652))
                            else
                                function _t1273(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                        _t1274 = _get_oneof_field(_dollar_dollar, :int128_value)
                                    else
                                        _t1274 = nothing
                                    end
                                    return _t1274
                                end
                                _t1275 = _t1273(msg)
                                deconstruct_result649 = _t1275
                                if !isnothing(deconstruct_result649)
                                    unwrapped650 = deconstruct_result649
                                    write(pp, format_int128(pp, unwrapped650))
                                else
                                    function _t1276(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                            _t1277 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                        else
                                            _t1277 = nothing
                                        end
                                        return _t1277
                                    end
                                    _t1278 = _t1276(msg)
                                    deconstruct_result647 = _t1278
                                    if !isnothing(deconstruct_result647)
                                        unwrapped648 = deconstruct_result647
                                        write(pp, format_decimal(pp, unwrapped648))
                                    else
                                        function _t1279(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                _t1280 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                            else
                                                _t1280 = nothing
                                            end
                                            return _t1280
                                        end
                                        _t1281 = _t1279(msg)
                                        deconstruct_result645 = _t1281
                                        if !isnothing(deconstruct_result645)
                                            unwrapped646 = deconstruct_result645
                                            pretty_boolean_value(pp, unwrapped646)
                                        else
                                            fields644 = msg
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
    flat669 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat669)
        write(pp, flat669)
        return nothing
    else
        function _t1282(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        end
        _t1283 = _t1282(msg)
        fields664 = _t1283
        unwrapped_fields665 = fields664
        write(pp, "(")
        write(pp, "date")
        indent_sexp!(pp)
        newline(pp)
        field666 = unwrapped_fields665[1]
        write(pp, string(field666))
        newline(pp)
        field667 = unwrapped_fields665[2]
        write(pp, string(field667))
        newline(pp)
        field668 = unwrapped_fields665[3]
        write(pp, string(field668))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat680 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat680)
        write(pp, flat680)
        return nothing
    else
        function _t1284(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        end
        _t1285 = _t1284(msg)
        fields670 = _t1285
        unwrapped_fields671 = fields670
        write(pp, "(")
        write(pp, "datetime")
        indent_sexp!(pp)
        newline(pp)
        field672 = unwrapped_fields671[1]
        write(pp, string(field672))
        newline(pp)
        field673 = unwrapped_fields671[2]
        write(pp, string(field673))
        newline(pp)
        field674 = unwrapped_fields671[3]
        write(pp, string(field674))
        newline(pp)
        field675 = unwrapped_fields671[4]
        write(pp, string(field675))
        newline(pp)
        field676 = unwrapped_fields671[5]
        write(pp, string(field676))
        newline(pp)
        field677 = unwrapped_fields671[6]
        write(pp, string(field677))
        field678 = unwrapped_fields671[7]
        if !isnothing(field678)
            newline(pp)
            opt_val679 = field678
            write(pp, string(opt_val679))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    function _t1286(_dollar_dollar)
        if _dollar_dollar
            _t1287 = ()
        else
            _t1287 = nothing
        end
        return _t1287
    end
    _t1288 = _t1286(msg)
    deconstruct_result683 = _t1288
    if !isnothing(deconstruct_result683)
        unwrapped684 = deconstruct_result683
        write(pp, "true")
    else
        function _t1289(_dollar_dollar)
            if !_dollar_dollar
                _t1290 = ()
            else
                _t1290 = nothing
            end
            return _t1290
        end
        _t1291 = _t1289(msg)
        deconstruct_result681 = _t1291
        if !isnothing(deconstruct_result681)
            unwrapped682 = deconstruct_result681
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat689 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat689)
        write(pp, flat689)
        return nothing
    else
        function _t1292(_dollar_dollar)
            return _dollar_dollar.fragments
        end
        _t1293 = _t1292(msg)
        fields685 = _t1293
        unwrapped_fields686 = fields685
        write(pp, "(")
        write(pp, "sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields686)
            newline(pp)
            for (i1294, elem687) in enumerate(unwrapped_fields686)
                i688 = i1294 - 1
                if (i688 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem687)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat692 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat692)
        write(pp, flat692)
        return nothing
    else
        function _t1295(_dollar_dollar)
            return fragment_id_to_string(pp, _dollar_dollar)
        end
        _t1296 = _t1295(msg)
        fields690 = _t1296
        unwrapped_fields691 = fields690
        write(pp, ":")
        write(pp, unwrapped_fields691)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat699 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat699)
        write(pp, flat699)
        return nothing
    else
        function _t1297(_dollar_dollar)
            if !isempty(_dollar_dollar.writes)
                _t1298 = _dollar_dollar.writes
            else
                _t1298 = nothing
            end
            if !isempty(_dollar_dollar.reads)
                _t1299 = _dollar_dollar.reads
            else
                _t1299 = nothing
            end
            return (_t1298, _t1299,)
        end
        _t1300 = _t1297(msg)
        fields693 = _t1300
        unwrapped_fields694 = fields693
        write(pp, "(")
        write(pp, "epoch")
        indent_sexp!(pp)
        field695 = unwrapped_fields694[1]
        if !isnothing(field695)
            newline(pp)
            opt_val696 = field695
            pretty_epoch_writes(pp, opt_val696)
        end
        field697 = unwrapped_fields694[2]
        if !isnothing(field697)
            newline(pp)
            opt_val698 = field697
            pretty_epoch_reads(pp, opt_val698)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat703 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat703)
        write(pp, flat703)
        return nothing
    else
        fields700 = msg
        write(pp, "(")
        write(pp, "writes")
        indent_sexp!(pp)
        if !isempty(fields700)
            newline(pp)
            for (i1301, elem701) in enumerate(fields700)
                i702 = i1301 - 1
                if (i702 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem701)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat710 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat710)
        write(pp, flat710)
        return nothing
    else
        function _t1302(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("define"))
                _t1303 = _get_oneof_field(_dollar_dollar, :define)
            else
                _t1303 = nothing
            end
            return _t1303
        end
        _t1304 = _t1302(msg)
        deconstruct_result708 = _t1304
        if !isnothing(deconstruct_result708)
            unwrapped709 = deconstruct_result708
            pretty_define(pp, unwrapped709)
        else
            function _t1305(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                    _t1306 = _get_oneof_field(_dollar_dollar, :undefine)
                else
                    _t1306 = nothing
                end
                return _t1306
            end
            _t1307 = _t1305(msg)
            deconstruct_result706 = _t1307
            if !isnothing(deconstruct_result706)
                unwrapped707 = deconstruct_result706
                pretty_undefine(pp, unwrapped707)
            else
                function _t1308(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("context"))
                        _t1309 = _get_oneof_field(_dollar_dollar, :context)
                    else
                        _t1309 = nothing
                    end
                    return _t1309
                end
                _t1310 = _t1308(msg)
                deconstruct_result704 = _t1310
                if !isnothing(deconstruct_result704)
                    unwrapped705 = deconstruct_result704
                    pretty_context(pp, unwrapped705)
                else
                    throw(ParseError("No matching rule for write"))
                end
            end
        end
    end
    return nothing
end

function pretty_define(pp::PrettyPrinter, msg::Proto.Define)
    flat713 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat713)
        write(pp, flat713)
        return nothing
    else
        function _t1311(_dollar_dollar)
            return _dollar_dollar.fragment
        end
        _t1312 = _t1311(msg)
        fields711 = _t1312
        unwrapped_fields712 = fields711
        write(pp, "(")
        write(pp, "define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields712)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat720 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat720)
        write(pp, flat720)
        return nothing
    else
        function _t1313(_dollar_dollar)
            start_pretty_fragment(pp, _dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        end
        _t1314 = _t1313(msg)
        fields714 = _t1314
        unwrapped_fields715 = fields714
        write(pp, "(")
        write(pp, "fragment")
        indent_sexp!(pp)
        newline(pp)
        field716 = unwrapped_fields715[1]
        pretty_new_fragment_id(pp, field716)
        field717 = unwrapped_fields715[2]
        if !isempty(field717)
            newline(pp)
            for (i1315, elem718) in enumerate(field717)
                i719 = i1315 - 1
                if (i719 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem718)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat722 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat722)
        write(pp, flat722)
        return nothing
    else
        fields721 = msg
        pretty_fragment_id(pp, fields721)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat731 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat731)
        write(pp, flat731)
        return nothing
    else
        function _t1316(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("def"))
                _t1317 = _get_oneof_field(_dollar_dollar, :def)
            else
                _t1317 = nothing
            end
            return _t1317
        end
        _t1318 = _t1316(msg)
        deconstruct_result729 = _t1318
        if !isnothing(deconstruct_result729)
            unwrapped730 = deconstruct_result729
            pretty_def(pp, unwrapped730)
        else
            function _t1319(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                    _t1320 = _get_oneof_field(_dollar_dollar, :algorithm)
                else
                    _t1320 = nothing
                end
                return _t1320
            end
            _t1321 = _t1319(msg)
            deconstruct_result727 = _t1321
            if !isnothing(deconstruct_result727)
                unwrapped728 = deconstruct_result727
                pretty_algorithm(pp, unwrapped728)
            else
                function _t1322(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                        _t1323 = _get_oneof_field(_dollar_dollar, :constraint)
                    else
                        _t1323 = nothing
                    end
                    return _t1323
                end
                _t1324 = _t1322(msg)
                deconstruct_result725 = _t1324
                if !isnothing(deconstruct_result725)
                    unwrapped726 = deconstruct_result725
                    pretty_constraint(pp, unwrapped726)
                else
                    function _t1325(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("data"))
                            _t1326 = _get_oneof_field(_dollar_dollar, :data)
                        else
                            _t1326 = nothing
                        end
                        return _t1326
                    end
                    _t1327 = _t1325(msg)
                    deconstruct_result723 = _t1327
                    if !isnothing(deconstruct_result723)
                        unwrapped724 = deconstruct_result723
                        pretty_data(pp, unwrapped724)
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
    flat738 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat738)
        write(pp, flat738)
        return nothing
    else
        function _t1328(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1329 = _dollar_dollar.attrs
            else
                _t1329 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1329,)
        end
        _t1330 = _t1328(msg)
        fields732 = _t1330
        unwrapped_fields733 = fields732
        write(pp, "(")
        write(pp, "def")
        indent_sexp!(pp)
        newline(pp)
        field734 = unwrapped_fields733[1]
        pretty_relation_id(pp, field734)
        newline(pp)
        field735 = unwrapped_fields733[2]
        pretty_abstraction(pp, field735)
        field736 = unwrapped_fields733[3]
        if !isnothing(field736)
            newline(pp)
            opt_val737 = field736
            pretty_attrs(pp, opt_val737)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat743 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat743)
        write(pp, flat743)
        return nothing
    else
        function _t1331(_dollar_dollar)
            _t1332 = deconstruct_relation_id_string(pp, _dollar_dollar)
            return _t1332
        end
        _t1333 = _t1331(msg)
        deconstruct_result741 = _t1333
        if !isnothing(deconstruct_result741)
            unwrapped742 = deconstruct_result741
            write(pp, ":")
            write(pp, unwrapped742)
        else
            function _t1334(_dollar_dollar)
                _t1335 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
                return _t1335
            end
            _t1336 = _t1334(msg)
            deconstruct_result739 = _t1336
            if !isnothing(deconstruct_result739)
                unwrapped740 = deconstruct_result739
                write(pp, format_uint128(pp, unwrapped740))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat748 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat748)
        write(pp, flat748)
        return nothing
    else
        function _t1337(_dollar_dollar)
            _t1338 = deconstruct_bindings(pp, _dollar_dollar)
            return (_t1338, _dollar_dollar.value,)
        end
        _t1339 = _t1337(msg)
        fields744 = _t1339
        unwrapped_fields745 = fields744
        write(pp, "(")
        indent!(pp)
        field746 = unwrapped_fields745[1]
        pretty_bindings(pp, field746)
        newline(pp)
        field747 = unwrapped_fields745[2]
        pretty_formula(pp, field747)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat756 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat756)
        write(pp, flat756)
        return nothing
    else
        function _t1340(_dollar_dollar)
            if !isempty(_dollar_dollar[2])
                _t1341 = _dollar_dollar[2]
            else
                _t1341 = nothing
            end
            return (_dollar_dollar[1], _t1341,)
        end
        _t1342 = _t1340(msg)
        fields749 = _t1342
        unwrapped_fields750 = fields749
        write(pp, "[")
        indent!(pp)
        field751 = unwrapped_fields750[1]
        for (i1343, elem752) in enumerate(field751)
            i753 = i1343 - 1
            if (i753 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem752)
        end
        field754 = unwrapped_fields750[2]
        if !isnothing(field754)
            newline(pp)
            opt_val755 = field754
            pretty_value_bindings(pp, opt_val755)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat761 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat761)
        write(pp, flat761)
        return nothing
    else
        function _t1344(_dollar_dollar)
            return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        end
        _t1345 = _t1344(msg)
        fields757 = _t1345
        unwrapped_fields758 = fields757
        field759 = unwrapped_fields758[1]
        write(pp, field759)
        write(pp, "::")
        field760 = unwrapped_fields758[2]
        pretty_type(pp, field760)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat784 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat784)
        write(pp, flat784)
        return nothing
    else
        function _t1346(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
                _t1347 = _get_oneof_field(_dollar_dollar, :unspecified_type)
            else
                _t1347 = nothing
            end
            return _t1347
        end
        _t1348 = _t1346(msg)
        deconstruct_result782 = _t1348
        if !isnothing(deconstruct_result782)
            unwrapped783 = deconstruct_result782
            pretty_unspecified_type(pp, unwrapped783)
        else
            function _t1349(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                    _t1350 = _get_oneof_field(_dollar_dollar, :string_type)
                else
                    _t1350 = nothing
                end
                return _t1350
            end
            _t1351 = _t1349(msg)
            deconstruct_result780 = _t1351
            if !isnothing(deconstruct_result780)
                unwrapped781 = deconstruct_result780
                pretty_string_type(pp, unwrapped781)
            else
                function _t1352(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                        _t1353 = _get_oneof_field(_dollar_dollar, :int_type)
                    else
                        _t1353 = nothing
                    end
                    return _t1353
                end
                _t1354 = _t1352(msg)
                deconstruct_result778 = _t1354
                if !isnothing(deconstruct_result778)
                    unwrapped779 = deconstruct_result778
                    pretty_int_type(pp, unwrapped779)
                else
                    function _t1355(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                            _t1356 = _get_oneof_field(_dollar_dollar, :float_type)
                        else
                            _t1356 = nothing
                        end
                        return _t1356
                    end
                    _t1357 = _t1355(msg)
                    deconstruct_result776 = _t1357
                    if !isnothing(deconstruct_result776)
                        unwrapped777 = deconstruct_result776
                        pretty_float_type(pp, unwrapped777)
                    else
                        function _t1358(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                                _t1359 = _get_oneof_field(_dollar_dollar, :uint128_type)
                            else
                                _t1359 = nothing
                            end
                            return _t1359
                        end
                        _t1360 = _t1358(msg)
                        deconstruct_result774 = _t1360
                        if !isnothing(deconstruct_result774)
                            unwrapped775 = deconstruct_result774
                            pretty_uint128_type(pp, unwrapped775)
                        else
                            function _t1361(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                    _t1362 = _get_oneof_field(_dollar_dollar, :int128_type)
                                else
                                    _t1362 = nothing
                                end
                                return _t1362
                            end
                            _t1363 = _t1361(msg)
                            deconstruct_result772 = _t1363
                            if !isnothing(deconstruct_result772)
                                unwrapped773 = deconstruct_result772
                                pretty_int128_type(pp, unwrapped773)
                            else
                                function _t1364(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                        _t1365 = _get_oneof_field(_dollar_dollar, :date_type)
                                    else
                                        _t1365 = nothing
                                    end
                                    return _t1365
                                end
                                _t1366 = _t1364(msg)
                                deconstruct_result770 = _t1366
                                if !isnothing(deconstruct_result770)
                                    unwrapped771 = deconstruct_result770
                                    pretty_date_type(pp, unwrapped771)
                                else
                                    function _t1367(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                            _t1368 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                        else
                                            _t1368 = nothing
                                        end
                                        return _t1368
                                    end
                                    _t1369 = _t1367(msg)
                                    deconstruct_result768 = _t1369
                                    if !isnothing(deconstruct_result768)
                                        unwrapped769 = deconstruct_result768
                                        pretty_datetime_type(pp, unwrapped769)
                                    else
                                        function _t1370(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                                _t1371 = _get_oneof_field(_dollar_dollar, :missing_type)
                                            else
                                                _t1371 = nothing
                                            end
                                            return _t1371
                                        end
                                        _t1372 = _t1370(msg)
                                        deconstruct_result766 = _t1372
                                        if !isnothing(deconstruct_result766)
                                            unwrapped767 = deconstruct_result766
                                            pretty_missing_type(pp, unwrapped767)
                                        else
                                            function _t1373(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                    _t1374 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                                else
                                                    _t1374 = nothing
                                                end
                                                return _t1374
                                            end
                                            _t1375 = _t1373(msg)
                                            deconstruct_result764 = _t1375
                                            if !isnothing(deconstruct_result764)
                                                unwrapped765 = deconstruct_result764
                                                pretty_decimal_type(pp, unwrapped765)
                                            else
                                                function _t1376(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                        _t1377 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                    else
                                                        _t1377 = nothing
                                                    end
                                                    return _t1377
                                                end
                                                _t1378 = _t1376(msg)
                                                deconstruct_result762 = _t1378
                                                if !isnothing(deconstruct_result762)
                                                    unwrapped763 = deconstruct_result762
                                                    pretty_boolean_type(pp, unwrapped763)
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
    fields785 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields786 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields787 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields788 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields789 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields790 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields791 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields792 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields793 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat798 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat798)
        write(pp, flat798)
        return nothing
    else
        function _t1379(_dollar_dollar)
            return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        end
        _t1380 = _t1379(msg)
        fields794 = _t1380
        unwrapped_fields795 = fields794
        write(pp, "(")
        write(pp, "DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field796 = unwrapped_fields795[1]
        write(pp, string(field796))
        newline(pp)
        field797 = unwrapped_fields795[2]
        write(pp, string(field797))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields799 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat803 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat803)
        write(pp, flat803)
        return nothing
    else
        fields800 = msg
        write(pp, "|")
        if !isempty(fields800)
            write(pp, " ")
            for (i1381, elem801) in enumerate(fields800)
                i802 = i1381 - 1
                if (i802 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem801)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat830 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat830)
        write(pp, flat830)
        return nothing
    else
        function _t1382(_dollar_dollar)
            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                _t1383 = _get_oneof_field(_dollar_dollar, :conjunction)
            else
                _t1383 = nothing
            end
            return _t1383
        end
        _t1384 = _t1382(msg)
        deconstruct_result828 = _t1384
        if !isnothing(deconstruct_result828)
            unwrapped829 = deconstruct_result828
            pretty_true(pp, unwrapped829)
        else
            function _t1385(_dollar_dollar)
                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                    _t1386 = _get_oneof_field(_dollar_dollar, :disjunction)
                else
                    _t1386 = nothing
                end
                return _t1386
            end
            _t1387 = _t1385(msg)
            deconstruct_result826 = _t1387
            if !isnothing(deconstruct_result826)
                unwrapped827 = deconstruct_result826
                pretty_false(pp, unwrapped827)
            else
                function _t1388(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("exists"))
                        _t1389 = _get_oneof_field(_dollar_dollar, :exists)
                    else
                        _t1389 = nothing
                    end
                    return _t1389
                end
                _t1390 = _t1388(msg)
                deconstruct_result824 = _t1390
                if !isnothing(deconstruct_result824)
                    unwrapped825 = deconstruct_result824
                    pretty_exists(pp, unwrapped825)
                else
                    function _t1391(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                            _t1392 = _get_oneof_field(_dollar_dollar, :reduce)
                        else
                            _t1392 = nothing
                        end
                        return _t1392
                    end
                    _t1393 = _t1391(msg)
                    deconstruct_result822 = _t1393
                    if !isnothing(deconstruct_result822)
                        unwrapped823 = deconstruct_result822
                        pretty_reduce(pp, unwrapped823)
                    else
                        function _t1394(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("conjunction"))
                                _t1395 = _get_oneof_field(_dollar_dollar, :conjunction)
                            else
                                _t1395 = nothing
                            end
                            return _t1395
                        end
                        _t1396 = _t1394(msg)
                        deconstruct_result820 = _t1396
                        if !isnothing(deconstruct_result820)
                            unwrapped821 = deconstruct_result820
                            pretty_conjunction(pp, unwrapped821)
                        else
                            function _t1397(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("disjunction"))
                                    _t1398 = _get_oneof_field(_dollar_dollar, :disjunction)
                                else
                                    _t1398 = nothing
                                end
                                return _t1398
                            end
                            _t1399 = _t1397(msg)
                            deconstruct_result818 = _t1399
                            if !isnothing(deconstruct_result818)
                                unwrapped819 = deconstruct_result818
                                pretty_disjunction(pp, unwrapped819)
                            else
                                function _t1400(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("not"))
                                        _t1401 = _get_oneof_field(_dollar_dollar, :not)
                                    else
                                        _t1401 = nothing
                                    end
                                    return _t1401
                                end
                                _t1402 = _t1400(msg)
                                deconstruct_result816 = _t1402
                                if !isnothing(deconstruct_result816)
                                    unwrapped817 = deconstruct_result816
                                    pretty_not(pp, unwrapped817)
                                else
                                    function _t1403(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                            _t1404 = _get_oneof_field(_dollar_dollar, :ffi)
                                        else
                                            _t1404 = nothing
                                        end
                                        return _t1404
                                    end
                                    _t1405 = _t1403(msg)
                                    deconstruct_result814 = _t1405
                                    if !isnothing(deconstruct_result814)
                                        unwrapped815 = deconstruct_result814
                                        pretty_ffi(pp, unwrapped815)
                                    else
                                        function _t1406(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                                _t1407 = _get_oneof_field(_dollar_dollar, :atom)
                                            else
                                                _t1407 = nothing
                                            end
                                            return _t1407
                                        end
                                        _t1408 = _t1406(msg)
                                        deconstruct_result812 = _t1408
                                        if !isnothing(deconstruct_result812)
                                            unwrapped813 = deconstruct_result812
                                            pretty_atom(pp, unwrapped813)
                                        else
                                            function _t1409(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                    _t1410 = _get_oneof_field(_dollar_dollar, :pragma)
                                                else
                                                    _t1410 = nothing
                                                end
                                                return _t1410
                                            end
                                            _t1411 = _t1409(msg)
                                            deconstruct_result810 = _t1411
                                            if !isnothing(deconstruct_result810)
                                                unwrapped811 = deconstruct_result810
                                                pretty_pragma(pp, unwrapped811)
                                            else
                                                function _t1412(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                        _t1413 = _get_oneof_field(_dollar_dollar, :primitive)
                                                    else
                                                        _t1413 = nothing
                                                    end
                                                    return _t1413
                                                end
                                                _t1414 = _t1412(msg)
                                                deconstruct_result808 = _t1414
                                                if !isnothing(deconstruct_result808)
                                                    unwrapped809 = deconstruct_result808
                                                    pretty_primitive(pp, unwrapped809)
                                                else
                                                    function _t1415(_dollar_dollar)
                                                        if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                            _t1416 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                        else
                                                            _t1416 = nothing
                                                        end
                                                        return _t1416
                                                    end
                                                    _t1417 = _t1415(msg)
                                                    deconstruct_result806 = _t1417
                                                    if !isnothing(deconstruct_result806)
                                                        unwrapped807 = deconstruct_result806
                                                        pretty_rel_atom(pp, unwrapped807)
                                                    else
                                                        function _t1418(_dollar_dollar)
                                                            if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                                _t1419 = _get_oneof_field(_dollar_dollar, :cast)
                                                            else
                                                                _t1419 = nothing
                                                            end
                                                            return _t1419
                                                        end
                                                        _t1420 = _t1418(msg)
                                                        deconstruct_result804 = _t1420
                                                        if !isnothing(deconstruct_result804)
                                                            unwrapped805 = deconstruct_result804
                                                            pretty_cast(pp, unwrapped805)
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
    fields831 = msg
    write(pp, "(")
    write(pp, "true")
    write(pp, ")")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields832 = msg
    write(pp, "(")
    write(pp, "false")
    write(pp, ")")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat837 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat837)
        write(pp, flat837)
        return nothing
    else
        function _t1421(_dollar_dollar)
            _t1422 = deconstruct_bindings(pp, _dollar_dollar.body)
            return (_t1422, _dollar_dollar.body.value,)
        end
        _t1423 = _t1421(msg)
        fields833 = _t1423
        unwrapped_fields834 = fields833
        write(pp, "(")
        write(pp, "exists")
        indent_sexp!(pp)
        newline(pp)
        field835 = unwrapped_fields834[1]
        pretty_bindings(pp, field835)
        newline(pp)
        field836 = unwrapped_fields834[2]
        pretty_formula(pp, field836)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat843 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat843)
        write(pp, flat843)
        return nothing
    else
        function _t1424(_dollar_dollar)
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        end
        _t1425 = _t1424(msg)
        fields838 = _t1425
        unwrapped_fields839 = fields838
        write(pp, "(")
        write(pp, "reduce")
        indent_sexp!(pp)
        newline(pp)
        field840 = unwrapped_fields839[1]
        pretty_abstraction(pp, field840)
        newline(pp)
        field841 = unwrapped_fields839[2]
        pretty_abstraction(pp, field841)
        newline(pp)
        field842 = unwrapped_fields839[3]
        pretty_terms(pp, field842)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat847 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat847)
        write(pp, flat847)
        return nothing
    else
        fields844 = msg
        write(pp, "(")
        write(pp, "terms")
        indent_sexp!(pp)
        if !isempty(fields844)
            newline(pp)
            for (i1426, elem845) in enumerate(fields844)
                i846 = i1426 - 1
                if (i846 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem845)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat852 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat852)
        write(pp, flat852)
        return nothing
    else
        function _t1427(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("var"))
                _t1428 = _get_oneof_field(_dollar_dollar, :var)
            else
                _t1428 = nothing
            end
            return _t1428
        end
        _t1429 = _t1427(msg)
        deconstruct_result850 = _t1429
        if !isnothing(deconstruct_result850)
            unwrapped851 = deconstruct_result850
            pretty_var(pp, unwrapped851)
        else
            function _t1430(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("constant"))
                    _t1431 = _get_oneof_field(_dollar_dollar, :constant)
                else
                    _t1431 = nothing
                end
                return _t1431
            end
            _t1432 = _t1430(msg)
            deconstruct_result848 = _t1432
            if !isnothing(deconstruct_result848)
                unwrapped849 = deconstruct_result848
                pretty_constant(pp, unwrapped849)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat855 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat855)
        write(pp, flat855)
        return nothing
    else
        function _t1433(_dollar_dollar)
            return _dollar_dollar.name
        end
        _t1434 = _t1433(msg)
        fields853 = _t1434
        unwrapped_fields854 = fields853
        write(pp, unwrapped_fields854)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat857 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat857)
        write(pp, flat857)
        return nothing
    else
        fields856 = msg
        pretty_value(pp, fields856)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat862 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat862)
        write(pp, flat862)
        return nothing
    else
        function _t1435(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1436 = _t1435(msg)
        fields858 = _t1436
        unwrapped_fields859 = fields858
        write(pp, "(")
        write(pp, "and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields859)
            newline(pp)
            for (i1437, elem860) in enumerate(unwrapped_fields859)
                i861 = i1437 - 1
                if (i861 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem860)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat867 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat867)
        write(pp, flat867)
        return nothing
    else
        function _t1438(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1439 = _t1438(msg)
        fields863 = _t1439
        unwrapped_fields864 = fields863
        write(pp, "(")
        write(pp, "or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields864)
            newline(pp)
            for (i1440, elem865) in enumerate(unwrapped_fields864)
                i866 = i1440 - 1
                if (i866 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem865)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat870 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat870)
        write(pp, flat870)
        return nothing
    else
        function _t1441(_dollar_dollar)
            return _dollar_dollar.arg
        end
        _t1442 = _t1441(msg)
        fields868 = _t1442
        unwrapped_fields869 = fields868
        write(pp, "(")
        write(pp, "not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields869)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat876 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat876)
        write(pp, flat876)
        return nothing
    else
        function _t1443(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        end
        _t1444 = _t1443(msg)
        fields871 = _t1444
        unwrapped_fields872 = fields871
        write(pp, "(")
        write(pp, "ffi")
        indent_sexp!(pp)
        newline(pp)
        field873 = unwrapped_fields872[1]
        pretty_name(pp, field873)
        newline(pp)
        field874 = unwrapped_fields872[2]
        pretty_ffi_args(pp, field874)
        newline(pp)
        field875 = unwrapped_fields872[3]
        pretty_terms(pp, field875)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat878 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat878)
        write(pp, flat878)
        return nothing
    else
        fields877 = msg
        write(pp, ":")
        write(pp, fields877)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat882 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat882)
        write(pp, flat882)
        return nothing
    else
        fields879 = msg
        write(pp, "(")
        write(pp, "args")
        indent_sexp!(pp)
        if !isempty(fields879)
            newline(pp)
            for (i1445, elem880) in enumerate(fields879)
                i881 = i1445 - 1
                if (i881 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem880)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat889 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat889)
        write(pp, flat889)
        return nothing
    else
        function _t1446(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1447 = _t1446(msg)
        fields883 = _t1447
        unwrapped_fields884 = fields883
        write(pp, "(")
        write(pp, "atom")
        indent_sexp!(pp)
        newline(pp)
        field885 = unwrapped_fields884[1]
        pretty_relation_id(pp, field885)
        field886 = unwrapped_fields884[2]
        if !isempty(field886)
            newline(pp)
            for (i1448, elem887) in enumerate(field886)
                i888 = i1448 - 1
                if (i888 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem887)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat896 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat896)
        write(pp, flat896)
        return nothing
    else
        function _t1449(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1450 = _t1449(msg)
        fields890 = _t1450
        unwrapped_fields891 = fields890
        write(pp, "(")
        write(pp, "pragma")
        indent_sexp!(pp)
        newline(pp)
        field892 = unwrapped_fields891[1]
        pretty_name(pp, field892)
        field893 = unwrapped_fields891[2]
        if !isempty(field893)
            newline(pp)
            for (i1451, elem894) in enumerate(field893)
                i895 = i1451 - 1
                if (i895 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem894)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat912 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat912)
        write(pp, flat912)
        return nothing
    else
        function _t1452(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1453 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1453 = nothing
            end
            return _t1453
        end
        _t1454 = _t1452(msg)
        guard_result911 = _t1454
        if !isnothing(guard_result911)
            pretty_eq(pp, msg)
        else
            function _t1455(_dollar_dollar)
                if _dollar_dollar.name == "rel_primitive_lt_monotype"
                    _t1456 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1456 = nothing
                end
                return _t1456
            end
            _t1457 = _t1455(msg)
            guard_result910 = _t1457
            if !isnothing(guard_result910)
                pretty_lt(pp, msg)
            else
                function _t1458(_dollar_dollar)
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                        _t1459 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1459 = nothing
                    end
                    return _t1459
                end
                _t1460 = _t1458(msg)
                guard_result909 = _t1460
                if !isnothing(guard_result909)
                    pretty_lt_eq(pp, msg)
                else
                    function _t1461(_dollar_dollar)
                        if _dollar_dollar.name == "rel_primitive_gt_monotype"
                            _t1462 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1462 = nothing
                        end
                        return _t1462
                    end
                    _t1463 = _t1461(msg)
                    guard_result908 = _t1463
                    if !isnothing(guard_result908)
                        pretty_gt(pp, msg)
                    else
                        function _t1464(_dollar_dollar)
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                                _t1465 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                            else
                                _t1465 = nothing
                            end
                            return _t1465
                        end
                        _t1466 = _t1464(msg)
                        guard_result907 = _t1466
                        if !isnothing(guard_result907)
                            pretty_gt_eq(pp, msg)
                        else
                            function _t1467(_dollar_dollar)
                                if _dollar_dollar.name == "rel_primitive_add_monotype"
                                    _t1468 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1468 = nothing
                                end
                                return _t1468
                            end
                            _t1469 = _t1467(msg)
                            guard_result906 = _t1469
                            if !isnothing(guard_result906)
                                pretty_add(pp, msg)
                            else
                                function _t1470(_dollar_dollar)
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                        _t1471 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1471 = nothing
                                    end
                                    return _t1471
                                end
                                _t1472 = _t1470(msg)
                                guard_result905 = _t1472
                                if !isnothing(guard_result905)
                                    pretty_minus(pp, msg)
                                else
                                    function _t1473(_dollar_dollar)
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                            _t1474 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1474 = nothing
                                        end
                                        return _t1474
                                    end
                                    _t1475 = _t1473(msg)
                                    guard_result904 = _t1475
                                    if !isnothing(guard_result904)
                                        pretty_multiply(pp, msg)
                                    else
                                        function _t1476(_dollar_dollar)
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                                _t1477 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                            else
                                                _t1477 = nothing
                                            end
                                            return _t1477
                                        end
                                        _t1478 = _t1476(msg)
                                        guard_result903 = _t1478
                                        if !isnothing(guard_result903)
                                            pretty_divide(pp, msg)
                                        else
                                            function _t1479(_dollar_dollar)
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            end
                                            _t1480 = _t1479(msg)
                                            fields897 = _t1480
                                            unwrapped_fields898 = fields897
                                            write(pp, "(")
                                            write(pp, "primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field899 = unwrapped_fields898[1]
                                            pretty_name(pp, field899)
                                            field900 = unwrapped_fields898[2]
                                            if !isempty(field900)
                                                newline(pp)
                                                for (i1481, elem901) in enumerate(field900)
                                                    i902 = i1481 - 1
                                                    if (i902 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem901)
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
    flat917 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat917)
        write(pp, flat917)
        return nothing
    else
        function _t1482(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1483 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1483 = nothing
            end
            return _t1483
        end
        _t1484 = _t1482(msg)
        fields913 = _t1484
        unwrapped_fields914 = fields913
        write(pp, "(")
        write(pp, "=")
        indent_sexp!(pp)
        newline(pp)
        field915 = unwrapped_fields914[1]
        pretty_term(pp, field915)
        newline(pp)
        field916 = unwrapped_fields914[2]
        pretty_term(pp, field916)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat922 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat922)
        write(pp, flat922)
        return nothing
    else
        function _t1485(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1486 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1486 = nothing
            end
            return _t1486
        end
        _t1487 = _t1485(msg)
        fields918 = _t1487
        unwrapped_fields919 = fields918
        write(pp, "(")
        write(pp, "<")
        indent_sexp!(pp)
        newline(pp)
        field920 = unwrapped_fields919[1]
        pretty_term(pp, field920)
        newline(pp)
        field921 = unwrapped_fields919[2]
        pretty_term(pp, field921)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat927 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat927)
        write(pp, flat927)
        return nothing
    else
        function _t1488(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                _t1489 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1489 = nothing
            end
            return _t1489
        end
        _t1490 = _t1488(msg)
        fields923 = _t1490
        unwrapped_fields924 = fields923
        write(pp, "(")
        write(pp, "<=")
        indent_sexp!(pp)
        newline(pp)
        field925 = unwrapped_fields924[1]
        pretty_term(pp, field925)
        newline(pp)
        field926 = unwrapped_fields924[2]
        pretty_term(pp, field926)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat932 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat932)
        write(pp, flat932)
        return nothing
    else
        function _t1491(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_monotype"
                _t1492 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1492 = nothing
            end
            return _t1492
        end
        _t1493 = _t1491(msg)
        fields928 = _t1493
        unwrapped_fields929 = fields928
        write(pp, "(")
        write(pp, ">")
        indent_sexp!(pp)
        newline(pp)
        field930 = unwrapped_fields929[1]
        pretty_term(pp, field930)
        newline(pp)
        field931 = unwrapped_fields929[2]
        pretty_term(pp, field931)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat937 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat937)
        write(pp, flat937)
        return nothing
    else
        function _t1494(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                _t1495 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1495 = nothing
            end
            return _t1495
        end
        _t1496 = _t1494(msg)
        fields933 = _t1496
        unwrapped_fields934 = fields933
        write(pp, "(")
        write(pp, ">=")
        indent_sexp!(pp)
        newline(pp)
        field935 = unwrapped_fields934[1]
        pretty_term(pp, field935)
        newline(pp)
        field936 = unwrapped_fields934[2]
        pretty_term(pp, field936)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat943 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat943)
        write(pp, flat943)
        return nothing
    else
        function _t1497(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_add_monotype"
                _t1498 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1498 = nothing
            end
            return _t1498
        end
        _t1499 = _t1497(msg)
        fields938 = _t1499
        unwrapped_fields939 = fields938
        write(pp, "(")
        write(pp, "+")
        indent_sexp!(pp)
        newline(pp)
        field940 = unwrapped_fields939[1]
        pretty_term(pp, field940)
        newline(pp)
        field941 = unwrapped_fields939[2]
        pretty_term(pp, field941)
        newline(pp)
        field942 = unwrapped_fields939[3]
        pretty_term(pp, field942)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat949 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat949)
        write(pp, flat949)
        return nothing
    else
        function _t1500(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                _t1501 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1501 = nothing
            end
            return _t1501
        end
        _t1502 = _t1500(msg)
        fields944 = _t1502
        unwrapped_fields945 = fields944
        write(pp, "(")
        write(pp, "-")
        indent_sexp!(pp)
        newline(pp)
        field946 = unwrapped_fields945[1]
        pretty_term(pp, field946)
        newline(pp)
        field947 = unwrapped_fields945[2]
        pretty_term(pp, field947)
        newline(pp)
        field948 = unwrapped_fields945[3]
        pretty_term(pp, field948)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat955 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat955)
        write(pp, flat955)
        return nothing
    else
        function _t1503(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                _t1504 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1504 = nothing
            end
            return _t1504
        end
        _t1505 = _t1503(msg)
        fields950 = _t1505
        unwrapped_fields951 = fields950
        write(pp, "(")
        write(pp, "*")
        indent_sexp!(pp)
        newline(pp)
        field952 = unwrapped_fields951[1]
        pretty_term(pp, field952)
        newline(pp)
        field953 = unwrapped_fields951[2]
        pretty_term(pp, field953)
        newline(pp)
        field954 = unwrapped_fields951[3]
        pretty_term(pp, field954)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat961 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat961)
        write(pp, flat961)
        return nothing
    else
        function _t1506(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                _t1507 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1507 = nothing
            end
            return _t1507
        end
        _t1508 = _t1506(msg)
        fields956 = _t1508
        unwrapped_fields957 = fields956
        write(pp, "(")
        write(pp, "/")
        indent_sexp!(pp)
        newline(pp)
        field958 = unwrapped_fields957[1]
        pretty_term(pp, field958)
        newline(pp)
        field959 = unwrapped_fields957[2]
        pretty_term(pp, field959)
        newline(pp)
        field960 = unwrapped_fields957[3]
        pretty_term(pp, field960)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat966 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat966)
        write(pp, flat966)
        return nothing
    else
        function _t1509(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
                _t1510 = _get_oneof_field(_dollar_dollar, :specialized_value)
            else
                _t1510 = nothing
            end
            return _t1510
        end
        _t1511 = _t1509(msg)
        deconstruct_result964 = _t1511
        if !isnothing(deconstruct_result964)
            unwrapped965 = deconstruct_result964
            pretty_specialized_value(pp, unwrapped965)
        else
            function _t1512(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("term"))
                    _t1513 = _get_oneof_field(_dollar_dollar, :term)
                else
                    _t1513 = nothing
                end
                return _t1513
            end
            _t1514 = _t1512(msg)
            deconstruct_result962 = _t1514
            if !isnothing(deconstruct_result962)
                unwrapped963 = deconstruct_result962
                pretty_term(pp, unwrapped963)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat968 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat968)
        write(pp, flat968)
        return nothing
    else
        fields967 = msg
        write(pp, "#")
        pretty_value(pp, fields967)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat975 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat975)
        write(pp, flat975)
        return nothing
    else
        function _t1515(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1516 = _t1515(msg)
        fields969 = _t1516
        unwrapped_fields970 = fields969
        write(pp, "(")
        write(pp, "relatom")
        indent_sexp!(pp)
        newline(pp)
        field971 = unwrapped_fields970[1]
        pretty_name(pp, field971)
        field972 = unwrapped_fields970[2]
        if !isempty(field972)
            newline(pp)
            for (i1517, elem973) in enumerate(field972)
                i974 = i1517 - 1
                if (i974 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem973)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat980 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat980)
        write(pp, flat980)
        return nothing
    else
        function _t1518(_dollar_dollar)
            return (_dollar_dollar.input, _dollar_dollar.result,)
        end
        _t1519 = _t1518(msg)
        fields976 = _t1519
        unwrapped_fields977 = fields976
        write(pp, "(")
        write(pp, "cast")
        indent_sexp!(pp)
        newline(pp)
        field978 = unwrapped_fields977[1]
        pretty_term(pp, field978)
        newline(pp)
        field979 = unwrapped_fields977[2]
        pretty_term(pp, field979)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat984 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat984)
        write(pp, flat984)
        return nothing
    else
        fields981 = msg
        write(pp, "(")
        write(pp, "attrs")
        indent_sexp!(pp)
        if !isempty(fields981)
            newline(pp)
            for (i1520, elem982) in enumerate(fields981)
                i983 = i1520 - 1
                if (i983 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem982)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat991 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat991)
        write(pp, flat991)
        return nothing
    else
        function _t1521(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args,)
        end
        _t1522 = _t1521(msg)
        fields985 = _t1522
        unwrapped_fields986 = fields985
        write(pp, "(")
        write(pp, "attribute")
        indent_sexp!(pp)
        newline(pp)
        field987 = unwrapped_fields986[1]
        pretty_name(pp, field987)
        field988 = unwrapped_fields986[2]
        if !isempty(field988)
            newline(pp)
            for (i1523, elem989) in enumerate(field988)
                i990 = i1523 - 1
                if (i990 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem989)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat998 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat998)
        write(pp, flat998)
        return nothing
    else
        function _t1524(_dollar_dollar)
            return (_dollar_dollar.var"#global", _dollar_dollar.body,)
        end
        _t1525 = _t1524(msg)
        fields992 = _t1525
        unwrapped_fields993 = fields992
        write(pp, "(")
        write(pp, "algorithm")
        indent_sexp!(pp)
        field994 = unwrapped_fields993[1]
        if !isempty(field994)
            newline(pp)
            for (i1526, elem995) in enumerate(field994)
                i996 = i1526 - 1
                if (i996 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem995)
            end
        end
        newline(pp)
        field997 = unwrapped_fields993[2]
        pretty_script(pp, field997)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1003 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1003)
        write(pp, flat1003)
        return nothing
    else
        function _t1527(_dollar_dollar)
            return _dollar_dollar.constructs
        end
        _t1528 = _t1527(msg)
        fields999 = _t1528
        unwrapped_fields1000 = fields999
        write(pp, "(")
        write(pp, "script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1000)
            newline(pp)
            for (i1529, elem1001) in enumerate(unwrapped_fields1000)
                i1002 = i1529 - 1
                if (i1002 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1001)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1008 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1008)
        write(pp, flat1008)
        return nothing
    else
        function _t1530(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("loop"))
                _t1531 = _get_oneof_field(_dollar_dollar, :loop)
            else
                _t1531 = nothing
            end
            return _t1531
        end
        _t1532 = _t1530(msg)
        deconstruct_result1006 = _t1532
        if !isnothing(deconstruct_result1006)
            unwrapped1007 = deconstruct_result1006
            pretty_loop(pp, unwrapped1007)
        else
            function _t1533(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                    _t1534 = _get_oneof_field(_dollar_dollar, :instruction)
                else
                    _t1534 = nothing
                end
                return _t1534
            end
            _t1535 = _t1533(msg)
            deconstruct_result1004 = _t1535
            if !isnothing(deconstruct_result1004)
                unwrapped1005 = deconstruct_result1004
                pretty_instruction(pp, unwrapped1005)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1013 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1013)
        write(pp, flat1013)
        return nothing
    else
        function _t1536(_dollar_dollar)
            return (_dollar_dollar.init, _dollar_dollar.body,)
        end
        _t1537 = _t1536(msg)
        fields1009 = _t1537
        unwrapped_fields1010 = fields1009
        write(pp, "(")
        write(pp, "loop")
        indent_sexp!(pp)
        newline(pp)
        field1011 = unwrapped_fields1010[1]
        pretty_init(pp, field1011)
        newline(pp)
        field1012 = unwrapped_fields1010[2]
        pretty_script(pp, field1012)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1017 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1017)
        write(pp, flat1017)
        return nothing
    else
        fields1014 = msg
        write(pp, "(")
        write(pp, "init")
        indent_sexp!(pp)
        if !isempty(fields1014)
            newline(pp)
            for (i1538, elem1015) in enumerate(fields1014)
                i1016 = i1538 - 1
                if (i1016 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1015)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1028 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1028)
        write(pp, flat1028)
        return nothing
    else
        function _t1539(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("assign"))
                _t1540 = _get_oneof_field(_dollar_dollar, :assign)
            else
                _t1540 = nothing
            end
            return _t1540
        end
        _t1541 = _t1539(msg)
        deconstruct_result1026 = _t1541
        if !isnothing(deconstruct_result1026)
            unwrapped1027 = deconstruct_result1026
            pretty_assign(pp, unwrapped1027)
        else
            function _t1542(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                    _t1543 = _get_oneof_field(_dollar_dollar, :upsert)
                else
                    _t1543 = nothing
                end
                return _t1543
            end
            _t1544 = _t1542(msg)
            deconstruct_result1024 = _t1544
            if !isnothing(deconstruct_result1024)
                unwrapped1025 = deconstruct_result1024
                pretty_upsert(pp, unwrapped1025)
            else
                function _t1545(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("#break"))
                        _t1546 = _get_oneof_field(_dollar_dollar, :var"#break")
                    else
                        _t1546 = nothing
                    end
                    return _t1546
                end
                _t1547 = _t1545(msg)
                deconstruct_result1022 = _t1547
                if !isnothing(deconstruct_result1022)
                    unwrapped1023 = deconstruct_result1022
                    pretty_break(pp, unwrapped1023)
                else
                    function _t1548(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                            _t1549 = _get_oneof_field(_dollar_dollar, :monoid_def)
                        else
                            _t1549 = nothing
                        end
                        return _t1549
                    end
                    _t1550 = _t1548(msg)
                    deconstruct_result1020 = _t1550
                    if !isnothing(deconstruct_result1020)
                        unwrapped1021 = deconstruct_result1020
                        pretty_monoid_def(pp, unwrapped1021)
                    else
                        function _t1551(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                                _t1552 = _get_oneof_field(_dollar_dollar, :monus_def)
                            else
                                _t1552 = nothing
                            end
                            return _t1552
                        end
                        _t1553 = _t1551(msg)
                        deconstruct_result1018 = _t1553
                        if !isnothing(deconstruct_result1018)
                            unwrapped1019 = deconstruct_result1018
                            pretty_monus_def(pp, unwrapped1019)
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
    flat1035 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1035)
        write(pp, flat1035)
        return nothing
    else
        function _t1554(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1555 = _dollar_dollar.attrs
            else
                _t1555 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1555,)
        end
        _t1556 = _t1554(msg)
        fields1029 = _t1556
        unwrapped_fields1030 = fields1029
        write(pp, "(")
        write(pp, "assign")
        indent_sexp!(pp)
        newline(pp)
        field1031 = unwrapped_fields1030[1]
        pretty_relation_id(pp, field1031)
        newline(pp)
        field1032 = unwrapped_fields1030[2]
        pretty_abstraction(pp, field1032)
        field1033 = unwrapped_fields1030[3]
        if !isnothing(field1033)
            newline(pp)
            opt_val1034 = field1033
            pretty_attrs(pp, opt_val1034)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1042 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1042)
        write(pp, flat1042)
        return nothing
    else
        function _t1557(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1558 = _dollar_dollar.attrs
            else
                _t1558 = nothing
            end
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1558,)
        end
        _t1559 = _t1557(msg)
        fields1036 = _t1559
        unwrapped_fields1037 = fields1036
        write(pp, "(")
        write(pp, "upsert")
        indent_sexp!(pp)
        newline(pp)
        field1038 = unwrapped_fields1037[1]
        pretty_relation_id(pp, field1038)
        newline(pp)
        field1039 = unwrapped_fields1037[2]
        pretty_abstraction_with_arity(pp, field1039)
        field1040 = unwrapped_fields1037[3]
        if !isnothing(field1040)
            newline(pp)
            opt_val1041 = field1040
            pretty_attrs(pp, opt_val1041)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1047 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1047)
        write(pp, flat1047)
        return nothing
    else
        function _t1560(_dollar_dollar)
            _t1561 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
            return (_t1561, _dollar_dollar[1].value,)
        end
        _t1562 = _t1560(msg)
        fields1043 = _t1562
        unwrapped_fields1044 = fields1043
        write(pp, "(")
        indent!(pp)
        field1045 = unwrapped_fields1044[1]
        pretty_bindings(pp, field1045)
        newline(pp)
        field1046 = unwrapped_fields1044[2]
        pretty_formula(pp, field1046)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1054 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1054)
        write(pp, flat1054)
        return nothing
    else
        function _t1563(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1564 = _dollar_dollar.attrs
            else
                _t1564 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1564,)
        end
        _t1565 = _t1563(msg)
        fields1048 = _t1565
        unwrapped_fields1049 = fields1048
        write(pp, "(")
        write(pp, "break")
        indent_sexp!(pp)
        newline(pp)
        field1050 = unwrapped_fields1049[1]
        pretty_relation_id(pp, field1050)
        newline(pp)
        field1051 = unwrapped_fields1049[2]
        pretty_abstraction(pp, field1051)
        field1052 = unwrapped_fields1049[3]
        if !isnothing(field1052)
            newline(pp)
            opt_val1053 = field1052
            pretty_attrs(pp, opt_val1053)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1062 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1062)
        write(pp, flat1062)
        return nothing
    else
        function _t1566(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1567 = _dollar_dollar.attrs
            else
                _t1567 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1567,)
        end
        _t1568 = _t1566(msg)
        fields1055 = _t1568
        unwrapped_fields1056 = fields1055
        write(pp, "(")
        write(pp, "monoid")
        indent_sexp!(pp)
        newline(pp)
        field1057 = unwrapped_fields1056[1]
        pretty_monoid(pp, field1057)
        newline(pp)
        field1058 = unwrapped_fields1056[2]
        pretty_relation_id(pp, field1058)
        newline(pp)
        field1059 = unwrapped_fields1056[3]
        pretty_abstraction_with_arity(pp, field1059)
        field1060 = unwrapped_fields1056[4]
        if !isnothing(field1060)
            newline(pp)
            opt_val1061 = field1060
            pretty_attrs(pp, opt_val1061)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1071 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1071)
        write(pp, flat1071)
        return nothing
    else
        function _t1569(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
                _t1570 = _get_oneof_field(_dollar_dollar, :or_monoid)
            else
                _t1570 = nothing
            end
            return _t1570
        end
        _t1571 = _t1569(msg)
        deconstruct_result1069 = _t1571
        if !isnothing(deconstruct_result1069)
            unwrapped1070 = deconstruct_result1069
            pretty_or_monoid(pp, unwrapped1070)
        else
            function _t1572(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                    _t1573 = _get_oneof_field(_dollar_dollar, :min_monoid)
                else
                    _t1573 = nothing
                end
                return _t1573
            end
            _t1574 = _t1572(msg)
            deconstruct_result1067 = _t1574
            if !isnothing(deconstruct_result1067)
                unwrapped1068 = deconstruct_result1067
                pretty_min_monoid(pp, unwrapped1068)
            else
                function _t1575(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                        _t1576 = _get_oneof_field(_dollar_dollar, :max_monoid)
                    else
                        _t1576 = nothing
                    end
                    return _t1576
                end
                _t1577 = _t1575(msg)
                deconstruct_result1065 = _t1577
                if !isnothing(deconstruct_result1065)
                    unwrapped1066 = deconstruct_result1065
                    pretty_max_monoid(pp, unwrapped1066)
                else
                    function _t1578(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                            _t1579 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                        else
                            _t1579 = nothing
                        end
                        return _t1579
                    end
                    _t1580 = _t1578(msg)
                    deconstruct_result1063 = _t1580
                    if !isnothing(deconstruct_result1063)
                        unwrapped1064 = deconstruct_result1063
                        pretty_sum_monoid(pp, unwrapped1064)
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
    fields1072 = msg
    write(pp, "(")
    write(pp, "or")
    write(pp, ")")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1075 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1075)
        write(pp, flat1075)
        return nothing
    else
        function _t1581(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1582 = _t1581(msg)
        fields1073 = _t1582
        unwrapped_fields1074 = fields1073
        write(pp, "(")
        write(pp, "min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1074)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1078 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1078)
        write(pp, flat1078)
        return nothing
    else
        function _t1583(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1584 = _t1583(msg)
        fields1076 = _t1584
        unwrapped_fields1077 = fields1076
        write(pp, "(")
        write(pp, "max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1077)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1081 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1081)
        write(pp, flat1081)
        return nothing
    else
        function _t1585(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1586 = _t1585(msg)
        fields1079 = _t1586
        unwrapped_fields1080 = fields1079
        write(pp, "(")
        write(pp, "sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1080)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1089 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1089)
        write(pp, flat1089)
        return nothing
    else
        function _t1587(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1588 = _dollar_dollar.attrs
            else
                _t1588 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1588,)
        end
        _t1589 = _t1587(msg)
        fields1082 = _t1589
        unwrapped_fields1083 = fields1082
        write(pp, "(")
        write(pp, "monus")
        indent_sexp!(pp)
        newline(pp)
        field1084 = unwrapped_fields1083[1]
        pretty_monoid(pp, field1084)
        newline(pp)
        field1085 = unwrapped_fields1083[2]
        pretty_relation_id(pp, field1085)
        newline(pp)
        field1086 = unwrapped_fields1083[3]
        pretty_abstraction_with_arity(pp, field1086)
        field1087 = unwrapped_fields1083[4]
        if !isnothing(field1087)
            newline(pp)
            opt_val1088 = field1087
            pretty_attrs(pp, opt_val1088)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1096 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        function _t1590(_dollar_dollar)
            return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        end
        _t1591 = _t1590(msg)
        fields1090 = _t1591
        unwrapped_fields1091 = fields1090
        write(pp, "(")
        write(pp, "functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1092 = unwrapped_fields1091[1]
        pretty_relation_id(pp, field1092)
        newline(pp)
        field1093 = unwrapped_fields1091[2]
        pretty_abstraction(pp, field1093)
        newline(pp)
        field1094 = unwrapped_fields1091[3]
        pretty_functional_dependency_keys(pp, field1094)
        newline(pp)
        field1095 = unwrapped_fields1091[4]
        pretty_functional_dependency_values(pp, field1095)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1100 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1100)
        write(pp, flat1100)
        return nothing
    else
        fields1097 = msg
        write(pp, "(")
        write(pp, "keys")
        indent_sexp!(pp)
        if !isempty(fields1097)
            newline(pp)
            for (i1592, elem1098) in enumerate(fields1097)
                i1099 = i1592 - 1
                if (i1099 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1098)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1104 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1104)
        write(pp, flat1104)
        return nothing
    else
        fields1101 = msg
        write(pp, "(")
        write(pp, "values")
        indent_sexp!(pp)
        if !isempty(fields1101)
            newline(pp)
            for (i1593, elem1102) in enumerate(fields1101)
                i1103 = i1593 - 1
                if (i1103 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1102)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1111 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1111)
        write(pp, flat1111)
        return nothing
    else
        function _t1594(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("rel_edb"))
                _t1595 = _get_oneof_field(_dollar_dollar, :rel_edb)
            else
                _t1595 = nothing
            end
            return _t1595
        end
        _t1596 = _t1594(msg)
        deconstruct_result1109 = _t1596
        if !isnothing(deconstruct_result1109)
            unwrapped1110 = deconstruct_result1109
            pretty_rel_edb(pp, unwrapped1110)
        else
            function _t1597(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                    _t1598 = _get_oneof_field(_dollar_dollar, :betree_relation)
                else
                    _t1598 = nothing
                end
                return _t1598
            end
            _t1599 = _t1597(msg)
            deconstruct_result1107 = _t1599
            if !isnothing(deconstruct_result1107)
                unwrapped1108 = deconstruct_result1107
                pretty_betree_relation(pp, unwrapped1108)
            else
                function _t1600(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                        _t1601 = _get_oneof_field(_dollar_dollar, :csv_data)
                    else
                        _t1601 = nothing
                    end
                    return _t1601
                end
                _t1602 = _t1600(msg)
                deconstruct_result1105 = _t1602
                if !isnothing(deconstruct_result1105)
                    unwrapped1106 = deconstruct_result1105
                    pretty_csv_data(pp, unwrapped1106)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_rel_edb(pp::PrettyPrinter, msg::Proto.RelEDB)
    flat1117 = try_flat(pp, msg, pretty_rel_edb)
    if !isnothing(flat1117)
        write(pp, flat1117)
        return nothing
    else
        function _t1603(_dollar_dollar)
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        end
        _t1604 = _t1603(msg)
        fields1112 = _t1604
        unwrapped_fields1113 = fields1112
        write(pp, "(")
        write(pp, "rel_edb")
        indent_sexp!(pp)
        newline(pp)
        field1114 = unwrapped_fields1113[1]
        pretty_relation_id(pp, field1114)
        newline(pp)
        field1115 = unwrapped_fields1113[2]
        pretty_rel_edb_path(pp, field1115)
        newline(pp)
        field1116 = unwrapped_fields1113[3]
        pretty_rel_edb_types(pp, field1116)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1121 = try_flat(pp, msg, pretty_rel_edb_path)
    if !isnothing(flat1121)
        write(pp, flat1121)
        return nothing
    else
        fields1118 = msg
        write(pp, "[")
        indent!(pp)
        for (i1605, elem1119) in enumerate(fields1118)
            i1120 = i1605 - 1
            if (i1120 > 0)
                newline(pp)
            end
            write(pp, format_string_value(elem1119))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_rel_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1125 = try_flat(pp, msg, pretty_rel_edb_types)
    if !isnothing(flat1125)
        write(pp, flat1125)
        return nothing
    else
        fields1122 = msg
        write(pp, "[")
        indent!(pp)
        for (i1606, elem1123) in enumerate(fields1122)
            i1124 = i1606 - 1
            if (i1124 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1123)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1130 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1130)
        write(pp, flat1130)
        return nothing
    else
        function _t1607(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        end
        _t1608 = _t1607(msg)
        fields1126 = _t1608
        unwrapped_fields1127 = fields1126
        write(pp, "(")
        write(pp, "betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1128 = unwrapped_fields1127[1]
        pretty_relation_id(pp, field1128)
        newline(pp)
        field1129 = unwrapped_fields1127[2]
        pretty_betree_info(pp, field1129)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1136 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1136)
        write(pp, flat1136)
        return nothing
    else
        function _t1609(_dollar_dollar)
            _t1610 = deconstruct_betree_info_config(pp, _dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1610,)
        end
        _t1611 = _t1609(msg)
        fields1131 = _t1611
        unwrapped_fields1132 = fields1131
        write(pp, "(")
        write(pp, "betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1133 = unwrapped_fields1132[1]
        pretty_betree_info_key_types(pp, field1133)
        newline(pp)
        field1134 = unwrapped_fields1132[2]
        pretty_betree_info_value_types(pp, field1134)
        newline(pp)
        field1135 = unwrapped_fields1132[3]
        pretty_config_dict(pp, field1135)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1140 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1140)
        write(pp, flat1140)
        return nothing
    else
        fields1137 = msg
        write(pp, "(")
        write(pp, "key_types")
        indent_sexp!(pp)
        if !isempty(fields1137)
            newline(pp)
            for (i1612, elem1138) in enumerate(fields1137)
                i1139 = i1612 - 1
                if (i1139 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1138)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1144 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1144)
        write(pp, flat1144)
        return nothing
    else
        fields1141 = msg
        write(pp, "(")
        write(pp, "value_types")
        indent_sexp!(pp)
        if !isempty(fields1141)
            newline(pp)
            for (i1613, elem1142) in enumerate(fields1141)
                i1143 = i1613 - 1
                if (i1143 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1142)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1151 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1151)
        write(pp, flat1151)
        return nothing
    else
        function _t1614(_dollar_dollar)
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        end
        _t1615 = _t1614(msg)
        fields1145 = _t1615
        unwrapped_fields1146 = fields1145
        write(pp, "(")
        write(pp, "csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1147 = unwrapped_fields1146[1]
        pretty_csvlocator(pp, field1147)
        newline(pp)
        field1148 = unwrapped_fields1146[2]
        pretty_csv_config(pp, field1148)
        newline(pp)
        field1149 = unwrapped_fields1146[3]
        pretty_csv_columns(pp, field1149)
        newline(pp)
        field1150 = unwrapped_fields1146[4]
        pretty_csv_asof(pp, field1150)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1158 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1158)
        write(pp, flat1158)
        return nothing
    else
        function _t1616(_dollar_dollar)
            if !isempty(_dollar_dollar.paths)
                _t1617 = _dollar_dollar.paths
            else
                _t1617 = nothing
            end
            if String(copy(_dollar_dollar.inline_data)) != ""
                _t1618 = String(copy(_dollar_dollar.inline_data))
            else
                _t1618 = nothing
            end
            return (_t1617, _t1618,)
        end
        _t1619 = _t1616(msg)
        fields1152 = _t1619
        unwrapped_fields1153 = fields1152
        write(pp, "(")
        write(pp, "csv_locator")
        indent_sexp!(pp)
        field1154 = unwrapped_fields1153[1]
        if !isnothing(field1154)
            newline(pp)
            opt_val1155 = field1154
            pretty_csv_locator_paths(pp, opt_val1155)
        end
        field1156 = unwrapped_fields1153[2]
        if !isnothing(field1156)
            newline(pp)
            opt_val1157 = field1156
            pretty_csv_locator_inline_data(pp, opt_val1157)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1162 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1162)
        write(pp, flat1162)
        return nothing
    else
        fields1159 = msg
        write(pp, "(")
        write(pp, "paths")
        indent_sexp!(pp)
        if !isempty(fields1159)
            newline(pp)
            for (i1620, elem1160) in enumerate(fields1159)
                i1161 = i1620 - 1
                if (i1161 > 0)
                    newline(pp)
                end
                write(pp, format_string_value(elem1160))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1164 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1164)
        write(pp, flat1164)
        return nothing
    else
        fields1163 = msg
        write(pp, "(")
        write(pp, "inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(fields1163))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1167 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        function _t1621(_dollar_dollar)
            _t1622 = deconstruct_csv_config(pp, _dollar_dollar)
            return _t1622
        end
        _t1623 = _t1621(msg)
        fields1165 = _t1623
        unwrapped_fields1166 = fields1165
        write(pp, "(")
        write(pp, "csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1166)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.CSVColumn})
    flat1171 = try_flat(pp, msg, pretty_csv_columns)
    if !isnothing(flat1171)
        write(pp, flat1171)
        return nothing
    else
        fields1168 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1168)
            newline(pp)
            for (i1624, elem1169) in enumerate(fields1168)
                i1170 = i1624 - 1
                if (i1170 > 0)
                    newline(pp)
                end
                pretty_csv_column(pp, elem1169)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_column(pp::PrettyPrinter, msg::Proto.CSVColumn)
    flat1179 = try_flat(pp, msg, pretty_csv_column)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        function _t1625(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        end
        _t1626 = _t1625(msg)
        fields1172 = _t1626
        unwrapped_fields1173 = fields1172
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1174 = unwrapped_fields1173[1]
        write(pp, format_string_value(field1174))
        newline(pp)
        field1175 = unwrapped_fields1173[2]
        pretty_relation_id(pp, field1175)
        newline(pp)
        write(pp, "[")
        field1176 = unwrapped_fields1173[3]
        for (i1627, elem1177) in enumerate(field1176)
            i1178 = i1627 - 1
            if (i1178 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1177)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1181 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1181)
        write(pp, flat1181)
        return nothing
    else
        fields1180 = msg
        write(pp, "(")
        write(pp, "asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(fields1180))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1184 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1184)
        write(pp, flat1184)
        return nothing
    else
        function _t1628(_dollar_dollar)
            return _dollar_dollar.fragment_id
        end
        _t1629 = _t1628(msg)
        fields1182 = _t1629
        unwrapped_fields1183 = fields1182
        write(pp, "(")
        write(pp, "undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1183)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1189 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1189)
        write(pp, flat1189)
        return nothing
    else
        function _t1630(_dollar_dollar)
            return _dollar_dollar.relations
        end
        _t1631 = _t1630(msg)
        fields1185 = _t1631
        unwrapped_fields1186 = fields1185
        write(pp, "(")
        write(pp, "context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1186)
            newline(pp)
            for (i1632, elem1187) in enumerate(unwrapped_fields1186)
                i1188 = i1632 - 1
                if (i1188 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1187)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1193 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1193)
        write(pp, flat1193)
        return nothing
    else
        fields1190 = msg
        write(pp, "(")
        write(pp, "reads")
        indent_sexp!(pp)
        if !isempty(fields1190)
            newline(pp)
            for (i1633, elem1191) in enumerate(fields1190)
                i1192 = i1633 - 1
                if (i1192 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1191)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1204 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1204)
        write(pp, flat1204)
        return nothing
    else
        function _t1634(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("demand"))
                _t1635 = _get_oneof_field(_dollar_dollar, :demand)
            else
                _t1635 = nothing
            end
            return _t1635
        end
        _t1636 = _t1634(msg)
        deconstruct_result1202 = _t1636
        if !isnothing(deconstruct_result1202)
            unwrapped1203 = deconstruct_result1202
            pretty_demand(pp, unwrapped1203)
        else
            function _t1637(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("output"))
                    _t1638 = _get_oneof_field(_dollar_dollar, :output)
                else
                    _t1638 = nothing
                end
                return _t1638
            end
            _t1639 = _t1637(msg)
            deconstruct_result1200 = _t1639
            if !isnothing(deconstruct_result1200)
                unwrapped1201 = deconstruct_result1200
                pretty_output(pp, unwrapped1201)
            else
                function _t1640(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                        _t1641 = _get_oneof_field(_dollar_dollar, :what_if)
                    else
                        _t1641 = nothing
                    end
                    return _t1641
                end
                _t1642 = _t1640(msg)
                deconstruct_result1198 = _t1642
                if !isnothing(deconstruct_result1198)
                    unwrapped1199 = deconstruct_result1198
                    pretty_what_if(pp, unwrapped1199)
                else
                    function _t1643(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("abort"))
                            _t1644 = _get_oneof_field(_dollar_dollar, :abort)
                        else
                            _t1644 = nothing
                        end
                        return _t1644
                    end
                    _t1645 = _t1643(msg)
                    deconstruct_result1196 = _t1645
                    if !isnothing(deconstruct_result1196)
                        unwrapped1197 = deconstruct_result1196
                        pretty_abort(pp, unwrapped1197)
                    else
                        function _t1646(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("#export"))
                                _t1647 = _get_oneof_field(_dollar_dollar, :var"#export")
                            else
                                _t1647 = nothing
                            end
                            return _t1647
                        end
                        _t1648 = _t1646(msg)
                        deconstruct_result1194 = _t1648
                        if !isnothing(deconstruct_result1194)
                            unwrapped1195 = deconstruct_result1194
                            pretty_export(pp, unwrapped1195)
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
    flat1207 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1207)
        write(pp, flat1207)
        return nothing
    else
        function _t1649(_dollar_dollar)
            return _dollar_dollar.relation_id
        end
        _t1650 = _t1649(msg)
        fields1205 = _t1650
        unwrapped_fields1206 = fields1205
        write(pp, "(")
        write(pp, "demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1206)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1212 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1212)
        write(pp, flat1212)
        return nothing
    else
        function _t1651(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        end
        _t1652 = _t1651(msg)
        fields1208 = _t1652
        unwrapped_fields1209 = fields1208
        write(pp, "(")
        write(pp, "output")
        indent_sexp!(pp)
        newline(pp)
        field1210 = unwrapped_fields1209[1]
        pretty_name(pp, field1210)
        newline(pp)
        field1211 = unwrapped_fields1209[2]
        pretty_relation_id(pp, field1211)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1217 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1217)
        write(pp, flat1217)
        return nothing
    else
        function _t1653(_dollar_dollar)
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        end
        _t1654 = _t1653(msg)
        fields1213 = _t1654
        unwrapped_fields1214 = fields1213
        write(pp, "(")
        write(pp, "what_if")
        indent_sexp!(pp)
        newline(pp)
        field1215 = unwrapped_fields1214[1]
        pretty_name(pp, field1215)
        newline(pp)
        field1216 = unwrapped_fields1214[2]
        pretty_epoch(pp, field1216)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1223 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1223)
        write(pp, flat1223)
        return nothing
    else
        function _t1655(_dollar_dollar)
            if _dollar_dollar.name != "abort"
                _t1656 = _dollar_dollar.name
            else
                _t1656 = nothing
            end
            return (_t1656, _dollar_dollar.relation_id,)
        end
        _t1657 = _t1655(msg)
        fields1218 = _t1657
        unwrapped_fields1219 = fields1218
        write(pp, "(")
        write(pp, "abort")
        indent_sexp!(pp)
        field1220 = unwrapped_fields1219[1]
        if !isnothing(field1220)
            newline(pp)
            opt_val1221 = field1220
            pretty_name(pp, opt_val1221)
        end
        newline(pp)
        field1222 = unwrapped_fields1219[2]
        pretty_relation_id(pp, field1222)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1226 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1226)
        write(pp, flat1226)
        return nothing
    else
        function _t1658(_dollar_dollar)
            return _get_oneof_field(_dollar_dollar, :csv_config)
        end
        _t1659 = _t1658(msg)
        fields1224 = _t1659
        unwrapped_fields1225 = fields1224
        write(pp, "(")
        write(pp, "export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1225)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1232 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1232)
        write(pp, flat1232)
        return nothing
    else
        function _t1660(_dollar_dollar)
            _t1661 = deconstruct_export_csv_config(pp, _dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1661,)
        end
        _t1662 = _t1660(msg)
        fields1227 = _t1662
        unwrapped_fields1228 = fields1227
        write(pp, "(")
        write(pp, "export_csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1229 = unwrapped_fields1228[1]
        pretty_export_csv_path(pp, field1229)
        newline(pp)
        field1230 = unwrapped_fields1228[2]
        pretty_export_csv_columns(pp, field1230)
        newline(pp)
        field1231 = unwrapped_fields1228[3]
        pretty_config_dict(pp, field1231)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1234 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1234)
        write(pp, flat1234)
        return nothing
    else
        fields1233 = msg
        write(pp, "(")
        write(pp, "path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(fields1233))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1238 = try_flat(pp, msg, pretty_export_csv_columns)
    if !isnothing(flat1238)
        write(pp, flat1238)
        return nothing
    else
        fields1235 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1235)
            newline(pp)
            for (i1663, elem1236) in enumerate(fields1235)
                i1237 = i1663 - 1
                if (i1237 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1236)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_column(pp::PrettyPrinter, msg::Proto.ExportCSVColumn)
    flat1243 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1243)
        write(pp, flat1243)
        return nothing
    else
        function _t1664(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        end
        _t1665 = _t1664(msg)
        fields1239 = _t1665
        unwrapped_fields1240 = fields1239
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1241 = unwrapped_fields1240[1]
        write(pp, format_string_value(field1241))
        newline(pp)
        field1242 = unwrapped_fields1240[2]
        pretty_relation_id(pp, field1242)
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
