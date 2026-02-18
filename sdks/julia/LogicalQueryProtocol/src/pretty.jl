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
    _t1846 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1846
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1847 = Proto.Value(value=OneOf(:int_value, v))
    return _t1847
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1848 = Proto.Value(value=OneOf(:float_value, v))
    return _t1848
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1849 = Proto.Value(value=OneOf(:string_value, v))
    return _t1849
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1850 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1850
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1851 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1851
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1852 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1852,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1853 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1853,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1854 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1854,))
            end
        end
    end
    _t1855 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1855,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1856 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1856,))
    _t1857 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1857,))
    if msg.new_line != ""
        _t1858 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1858,))
    end
    _t1859 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1859,))
    _t1860 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1860,))
    _t1861 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1861,))
    if msg.comment != ""
        _t1862 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1862,))
    end
    for missing_string in msg.missing_strings
        _t1863 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1863,))
    end
    _t1864 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1864,))
    _t1865 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1865,))
    _t1866 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1866,))
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1867 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1867,))
    _t1868 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1868,))
    _t1869 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1869,))
    _t1870 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1870,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1871 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1871,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1872 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1872,))
        end
    end
    _t1873 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1873,))
    _t1874 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1874,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1875 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1875,))
    end
    if !isnothing(msg.compression)
        _t1876 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1876,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1877 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1877,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1878 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1878,))
    end
    if !isnothing(msg.syntax_delim)
        _t1879 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1879,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1880 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1880,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1881 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1881,))
    end
    return sort(result)
end

function deconstruct_relation_id_string(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, String}
    name = relation_id_to_string(pp, msg)
    if name != ""
        return name
    else
        _t1882 = nothing
    end
    return nothing
end

function deconstruct_relation_id_uint128(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, Proto.UInt128Value}
    name = relation_id_to_string(pp, msg)
    if name == ""
        return relation_id_to_uint128(pp, msg)
    else
        _t1883 = nothing
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
    flat683 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat683)
        write(pp, flat683)
        return nothing
    else
        function _t1348(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("configure"))
                _t1349 = _dollar_dollar.configure
            else
                _t1349 = nothing
            end
            if _has_proto_field(_dollar_dollar, Symbol("sync"))
                _t1350 = _dollar_dollar.sync
            else
                _t1350 = nothing
            end
            return (_t1349, _t1350, _dollar_dollar.epochs,)
        end
        _t1351 = _t1348(msg)
        fields674 = _t1351
        unwrapped_fields675 = fields674
        write(pp, "(")
        write(pp, "transaction")
        indent_sexp!(pp)
        field676 = unwrapped_fields675[1]
        if !isnothing(field676)
            newline(pp)
            opt_val677 = field676
            pretty_configure(pp, opt_val677)
        end
        field678 = unwrapped_fields675[2]
        if !isnothing(field678)
            newline(pp)
            opt_val679 = field678
            pretty_sync(pp, opt_val679)
        end
        field680 = unwrapped_fields675[3]
        if !isempty(field680)
            newline(pp)
            for (i1352, elem681) in enumerate(field680)
                i682 = i1352 - 1
                if (i682 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem681)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat686 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat686)
        write(pp, flat686)
        return nothing
    else
        function _t1353(_dollar_dollar)
            _t1354 = deconstruct_configure(pp, _dollar_dollar)
            return _t1354
        end
        _t1355 = _t1353(msg)
        fields684 = _t1355
        unwrapped_fields685 = fields684
        write(pp, "(")
        write(pp, "configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields685)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat691 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat691)
        write(pp, flat691)
        return nothing
    else
        function _t1356(_dollar_dollar)
            return _dollar_dollar
        end
        _t1357 = _t1356(msg)
        fields687 = _t1357
        unwrapped_fields688 = fields687
        write(pp, "{")
        indent!(pp)
        if !isempty(unwrapped_fields688)
            newline(pp)
            for (i1358, elem689) in enumerate(unwrapped_fields688)
                i690 = i1358 - 1
                if (i690 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem689)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat696 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat696)
        write(pp, flat696)
        return nothing
    else
        function _t1359(_dollar_dollar)
            return (_dollar_dollar[1], _dollar_dollar[2],)
        end
        _t1360 = _t1359(msg)
        fields692 = _t1360
        unwrapped_fields693 = fields692
        write(pp, ":")
        field694 = unwrapped_fields693[1]
        write(pp, field694)
        write(pp, " ")
        field695 = unwrapped_fields693[2]
        pretty_value(pp, field695)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat717 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat717)
        write(pp, flat717)
        return nothing
    else
        function _t1361(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("date_value"))
                _t1362 = _get_oneof_field(_dollar_dollar, :date_value)
            else
                _t1362 = nothing
            end
            return _t1362
        end
        _t1363 = _t1361(msg)
        deconstruct_result715 = _t1363
        if !isnothing(deconstruct_result715)
            unwrapped716 = deconstruct_result715
            pretty_date(pp, unwrapped716)
        else
            function _t1364(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                    _t1365 = _get_oneof_field(_dollar_dollar, :datetime_value)
                else
                    _t1365 = nothing
                end
                return _t1365
            end
            _t1366 = _t1364(msg)
            deconstruct_result713 = _t1366
            if !isnothing(deconstruct_result713)
                unwrapped714 = deconstruct_result713
                pretty_datetime(pp, unwrapped714)
            else
                function _t1367(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                        _t1368 = _get_oneof_field(_dollar_dollar, :string_value)
                    else
                        _t1368 = nothing
                    end
                    return _t1368
                end
                _t1369 = _t1367(msg)
                deconstruct_result711 = _t1369
                if !isnothing(deconstruct_result711)
                    unwrapped712 = deconstruct_result711
                    write(pp, format_string_value(unwrapped712))
                else
                    function _t1370(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1371 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1371 = nothing
                        end
                        return _t1371
                    end
                    _t1372 = _t1370(msg)
                    deconstruct_result709 = _t1372
                    if !isnothing(deconstruct_result709)
                        unwrapped710 = deconstruct_result709
                        write(pp, string(unwrapped710))
                    else
                        function _t1373(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                _t1374 = _get_oneof_field(_dollar_dollar, :float_value)
                            else
                                _t1374 = nothing
                            end
                            return _t1374
                        end
                        _t1375 = _t1373(msg)
                        deconstruct_result707 = _t1375
                        if !isnothing(deconstruct_result707)
                            unwrapped708 = deconstruct_result707
                            write(pp, format_float64(unwrapped708))
                        else
                            function _t1376(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                    _t1377 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                else
                                    _t1377 = nothing
                                end
                                return _t1377
                            end
                            _t1378 = _t1376(msg)
                            deconstruct_result705 = _t1378
                            if !isnothing(deconstruct_result705)
                                unwrapped706 = deconstruct_result705
                                write(pp, format_uint128(pp, unwrapped706))
                            else
                                function _t1379(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                        _t1380 = _get_oneof_field(_dollar_dollar, :int128_value)
                                    else
                                        _t1380 = nothing
                                    end
                                    return _t1380
                                end
                                _t1381 = _t1379(msg)
                                deconstruct_result703 = _t1381
                                if !isnothing(deconstruct_result703)
                                    unwrapped704 = deconstruct_result703
                                    write(pp, format_int128(pp, unwrapped704))
                                else
                                    function _t1382(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                            _t1383 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                        else
                                            _t1383 = nothing
                                        end
                                        return _t1383
                                    end
                                    _t1384 = _t1382(msg)
                                    deconstruct_result701 = _t1384
                                    if !isnothing(deconstruct_result701)
                                        unwrapped702 = deconstruct_result701
                                        write(pp, format_decimal(pp, unwrapped702))
                                    else
                                        function _t1385(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                _t1386 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                            else
                                                _t1386 = nothing
                                            end
                                            return _t1386
                                        end
                                        _t1387 = _t1385(msg)
                                        deconstruct_result699 = _t1387
                                        if !isnothing(deconstruct_result699)
                                            unwrapped700 = deconstruct_result699
                                            pretty_boolean_value(pp, unwrapped700)
                                        else
                                            function _t1388(_dollar_dollar)
                                                return _dollar_dollar
                                            end
                                            _t1389 = _t1388(msg)
                                            fields697 = _t1389
                                            unwrapped_fields698 = fields697
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
    flat723 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat723)
        write(pp, flat723)
        return nothing
    else
        function _t1390(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        end
        _t1391 = _t1390(msg)
        fields718 = _t1391
        unwrapped_fields719 = fields718
        write(pp, "(")
        write(pp, "date")
        indent_sexp!(pp)
        newline(pp)
        field720 = unwrapped_fields719[1]
        write(pp, string(field720))
        newline(pp)
        field721 = unwrapped_fields719[2]
        write(pp, string(field721))
        newline(pp)
        field722 = unwrapped_fields719[3]
        write(pp, string(field722))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat734 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat734)
        write(pp, flat734)
        return nothing
    else
        function _t1392(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        end
        _t1393 = _t1392(msg)
        fields724 = _t1393
        unwrapped_fields725 = fields724
        write(pp, "(")
        write(pp, "datetime")
        indent_sexp!(pp)
        newline(pp)
        field726 = unwrapped_fields725[1]
        write(pp, string(field726))
        newline(pp)
        field727 = unwrapped_fields725[2]
        write(pp, string(field727))
        newline(pp)
        field728 = unwrapped_fields725[3]
        write(pp, string(field728))
        newline(pp)
        field729 = unwrapped_fields725[4]
        write(pp, string(field729))
        newline(pp)
        field730 = unwrapped_fields725[5]
        write(pp, string(field730))
        newline(pp)
        field731 = unwrapped_fields725[6]
        write(pp, string(field731))
        field732 = unwrapped_fields725[7]
        if !isnothing(field732)
            newline(pp)
            opt_val733 = field732
            write(pp, string(opt_val733))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    flat739 = try_flat(pp, msg, pretty_boolean_value)
    if !isnothing(flat739)
        write(pp, flat739)
        return nothing
    else
        function _t1394(_dollar_dollar)
            if _dollar_dollar
                _t1395 = ()
            else
                _t1395 = nothing
            end
            return _t1395
        end
        _t1396 = _t1394(msg)
        deconstruct_result737 = _t1396
        if !isnothing(deconstruct_result737)
            unwrapped738 = deconstruct_result737
            write(pp, "true")
        else
            function _t1397(_dollar_dollar)
                if !_dollar_dollar
                    _t1398 = ()
                else
                    _t1398 = nothing
                end
                return _t1398
            end
            _t1399 = _t1397(msg)
            deconstruct_result735 = _t1399
            if !isnothing(deconstruct_result735)
                unwrapped736 = deconstruct_result735
                write(pp, "false")
            else
                throw(ParseError("No matching rule for boolean_value"))
            end
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat744 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat744)
        write(pp, flat744)
        return nothing
    else
        function _t1400(_dollar_dollar)
            return _dollar_dollar.fragments
        end
        _t1401 = _t1400(msg)
        fields740 = _t1401
        unwrapped_fields741 = fields740
        write(pp, "(")
        write(pp, "sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields741)
            newline(pp)
            for (i1402, elem742) in enumerate(unwrapped_fields741)
                i743 = i1402 - 1
                if (i743 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem742)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat747 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat747)
        write(pp, flat747)
        return nothing
    else
        function _t1403(_dollar_dollar)
            return fragment_id_to_string(pp, _dollar_dollar)
        end
        _t1404 = _t1403(msg)
        fields745 = _t1404
        unwrapped_fields746 = fields745
        write(pp, ":")
        write(pp, unwrapped_fields746)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat754 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat754)
        write(pp, flat754)
        return nothing
    else
        function _t1405(_dollar_dollar)
            if !isempty(_dollar_dollar.writes)
                _t1406 = _dollar_dollar.writes
            else
                _t1406 = nothing
            end
            if !isempty(_dollar_dollar.reads)
                _t1407 = _dollar_dollar.reads
            else
                _t1407 = nothing
            end
            return (_t1406, _t1407,)
        end
        _t1408 = _t1405(msg)
        fields748 = _t1408
        unwrapped_fields749 = fields748
        write(pp, "(")
        write(pp, "epoch")
        indent_sexp!(pp)
        field750 = unwrapped_fields749[1]
        if !isnothing(field750)
            newline(pp)
            opt_val751 = field750
            pretty_epoch_writes(pp, opt_val751)
        end
        field752 = unwrapped_fields749[2]
        if !isnothing(field752)
            newline(pp)
            opt_val753 = field752
            pretty_epoch_reads(pp, opt_val753)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat759 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat759)
        write(pp, flat759)
        return nothing
    else
        function _t1409(_dollar_dollar)
            return _dollar_dollar
        end
        _t1410 = _t1409(msg)
        fields755 = _t1410
        unwrapped_fields756 = fields755
        write(pp, "(")
        write(pp, "writes")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields756)
            newline(pp)
            for (i1411, elem757) in enumerate(unwrapped_fields756)
                i758 = i1411 - 1
                if (i758 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem757)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat766 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat766)
        write(pp, flat766)
        return nothing
    else
        function _t1412(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("define"))
                _t1413 = _get_oneof_field(_dollar_dollar, :define)
            else
                _t1413 = nothing
            end
            return _t1413
        end
        _t1414 = _t1412(msg)
        deconstruct_result764 = _t1414
        if !isnothing(deconstruct_result764)
            unwrapped765 = deconstruct_result764
            pretty_define(pp, unwrapped765)
        else
            function _t1415(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                    _t1416 = _get_oneof_field(_dollar_dollar, :undefine)
                else
                    _t1416 = nothing
                end
                return _t1416
            end
            _t1417 = _t1415(msg)
            deconstruct_result762 = _t1417
            if !isnothing(deconstruct_result762)
                unwrapped763 = deconstruct_result762
                pretty_undefine(pp, unwrapped763)
            else
                function _t1418(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("context"))
                        _t1419 = _get_oneof_field(_dollar_dollar, :context)
                    else
                        _t1419 = nothing
                    end
                    return _t1419
                end
                _t1420 = _t1418(msg)
                deconstruct_result760 = _t1420
                if !isnothing(deconstruct_result760)
                    unwrapped761 = deconstruct_result760
                    pretty_context(pp, unwrapped761)
                else
                    throw(ParseError("No matching rule for write"))
                end
            end
        end
    end
    return nothing
end

function pretty_define(pp::PrettyPrinter, msg::Proto.Define)
    flat769 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat769)
        write(pp, flat769)
        return nothing
    else
        function _t1421(_dollar_dollar)
            return _dollar_dollar.fragment
        end
        _t1422 = _t1421(msg)
        fields767 = _t1422
        unwrapped_fields768 = fields767
        write(pp, "(")
        write(pp, "define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields768)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat776 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat776)
        write(pp, flat776)
        return nothing
    else
        function _t1423(_dollar_dollar)
            start_pretty_fragment(pp, _dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        end
        _t1424 = _t1423(msg)
        fields770 = _t1424
        unwrapped_fields771 = fields770
        write(pp, "(")
        write(pp, "fragment")
        indent_sexp!(pp)
        newline(pp)
        field772 = unwrapped_fields771[1]
        pretty_new_fragment_id(pp, field772)
        field773 = unwrapped_fields771[2]
        if !isempty(field773)
            newline(pp)
            for (i1425, elem774) in enumerate(field773)
                i775 = i1425 - 1
                if (i775 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem774)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat779 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat779)
        write(pp, flat779)
        return nothing
    else
        function _t1426(_dollar_dollar)
            return _dollar_dollar
        end
        _t1427 = _t1426(msg)
        fields777 = _t1427
        unwrapped_fields778 = fields777
        pretty_fragment_id(pp, unwrapped_fields778)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat788 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat788)
        write(pp, flat788)
        return nothing
    else
        function _t1428(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("def"))
                _t1429 = _get_oneof_field(_dollar_dollar, :def)
            else
                _t1429 = nothing
            end
            return _t1429
        end
        _t1430 = _t1428(msg)
        deconstruct_result786 = _t1430
        if !isnothing(deconstruct_result786)
            unwrapped787 = deconstruct_result786
            pretty_def(pp, unwrapped787)
        else
            function _t1431(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                    _t1432 = _get_oneof_field(_dollar_dollar, :algorithm)
                else
                    _t1432 = nothing
                end
                return _t1432
            end
            _t1433 = _t1431(msg)
            deconstruct_result784 = _t1433
            if !isnothing(deconstruct_result784)
                unwrapped785 = deconstruct_result784
                pretty_algorithm(pp, unwrapped785)
            else
                function _t1434(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                        _t1435 = _get_oneof_field(_dollar_dollar, :constraint)
                    else
                        _t1435 = nothing
                    end
                    return _t1435
                end
                _t1436 = _t1434(msg)
                deconstruct_result782 = _t1436
                if !isnothing(deconstruct_result782)
                    unwrapped783 = deconstruct_result782
                    pretty_constraint(pp, unwrapped783)
                else
                    function _t1437(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("data"))
                            _t1438 = _get_oneof_field(_dollar_dollar, :data)
                        else
                            _t1438 = nothing
                        end
                        return _t1438
                    end
                    _t1439 = _t1437(msg)
                    deconstruct_result780 = _t1439
                    if !isnothing(deconstruct_result780)
                        unwrapped781 = deconstruct_result780
                        pretty_data(pp, unwrapped781)
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
    flat795 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat795)
        write(pp, flat795)
        return nothing
    else
        function _t1440(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1441 = _dollar_dollar.attrs
            else
                _t1441 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1441,)
        end
        _t1442 = _t1440(msg)
        fields789 = _t1442
        unwrapped_fields790 = fields789
        write(pp, "(")
        write(pp, "def")
        indent_sexp!(pp)
        newline(pp)
        field791 = unwrapped_fields790[1]
        pretty_relation_id(pp, field791)
        newline(pp)
        field792 = unwrapped_fields790[2]
        pretty_abstraction(pp, field792)
        field793 = unwrapped_fields790[3]
        if !isnothing(field793)
            newline(pp)
            opt_val794 = field793
            pretty_attrs(pp, opt_val794)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat800 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat800)
        write(pp, flat800)
        return nothing
    else
        function _t1443(_dollar_dollar)
            _t1444 = deconstruct_relation_id_string(pp, _dollar_dollar)
            return _t1444
        end
        _t1445 = _t1443(msg)
        deconstruct_result798 = _t1445
        if !isnothing(deconstruct_result798)
            unwrapped799 = deconstruct_result798
            write(pp, ":")
            write(pp, unwrapped799)
        else
            function _t1446(_dollar_dollar)
                _t1447 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
                return _t1447
            end
            _t1448 = _t1446(msg)
            deconstruct_result796 = _t1448
            if !isnothing(deconstruct_result796)
                unwrapped797 = deconstruct_result796
                write(pp, format_uint128(pp, unwrapped797))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat805 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat805)
        write(pp, flat805)
        return nothing
    else
        function _t1449(_dollar_dollar)
            _t1450 = deconstruct_bindings(pp, _dollar_dollar)
            return (_t1450, _dollar_dollar.value,)
        end
        _t1451 = _t1449(msg)
        fields801 = _t1451
        unwrapped_fields802 = fields801
        write(pp, "(")
        indent!(pp)
        field803 = unwrapped_fields802[1]
        pretty_bindings(pp, field803)
        newline(pp)
        field804 = unwrapped_fields802[2]
        pretty_formula(pp, field804)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat813 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat813)
        write(pp, flat813)
        return nothing
    else
        function _t1452(_dollar_dollar)
            if !isempty(_dollar_dollar[2])
                _t1453 = _dollar_dollar[2]
            else
                _t1453 = nothing
            end
            return (_dollar_dollar[1], _t1453,)
        end
        _t1454 = _t1452(msg)
        fields806 = _t1454
        unwrapped_fields807 = fields806
        write(pp, "[")
        indent!(pp)
        field808 = unwrapped_fields807[1]
        for (i1455, elem809) in enumerate(field808)
            i810 = i1455 - 1
            if (i810 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem809)
        end
        field811 = unwrapped_fields807[2]
        if !isnothing(field811)
            newline(pp)
            opt_val812 = field811
            pretty_value_bindings(pp, opt_val812)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat818 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat818)
        write(pp, flat818)
        return nothing
    else
        function _t1456(_dollar_dollar)
            return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        end
        _t1457 = _t1456(msg)
        fields814 = _t1457
        unwrapped_fields815 = fields814
        field816 = unwrapped_fields815[1]
        write(pp, field816)
        write(pp, "::")
        field817 = unwrapped_fields815[2]
        pretty_type(pp, field817)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat841 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat841)
        write(pp, flat841)
        return nothing
    else
        function _t1458(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
                _t1459 = _get_oneof_field(_dollar_dollar, :unspecified_type)
            else
                _t1459 = nothing
            end
            return _t1459
        end
        _t1460 = _t1458(msg)
        deconstruct_result839 = _t1460
        if !isnothing(deconstruct_result839)
            unwrapped840 = deconstruct_result839
            pretty_unspecified_type(pp, unwrapped840)
        else
            function _t1461(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                    _t1462 = _get_oneof_field(_dollar_dollar, :string_type)
                else
                    _t1462 = nothing
                end
                return _t1462
            end
            _t1463 = _t1461(msg)
            deconstruct_result837 = _t1463
            if !isnothing(deconstruct_result837)
                unwrapped838 = deconstruct_result837
                pretty_string_type(pp, unwrapped838)
            else
                function _t1464(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                        _t1465 = _get_oneof_field(_dollar_dollar, :int_type)
                    else
                        _t1465 = nothing
                    end
                    return _t1465
                end
                _t1466 = _t1464(msg)
                deconstruct_result835 = _t1466
                if !isnothing(deconstruct_result835)
                    unwrapped836 = deconstruct_result835
                    pretty_int_type(pp, unwrapped836)
                else
                    function _t1467(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                            _t1468 = _get_oneof_field(_dollar_dollar, :float_type)
                        else
                            _t1468 = nothing
                        end
                        return _t1468
                    end
                    _t1469 = _t1467(msg)
                    deconstruct_result833 = _t1469
                    if !isnothing(deconstruct_result833)
                        unwrapped834 = deconstruct_result833
                        pretty_float_type(pp, unwrapped834)
                    else
                        function _t1470(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                                _t1471 = _get_oneof_field(_dollar_dollar, :uint128_type)
                            else
                                _t1471 = nothing
                            end
                            return _t1471
                        end
                        _t1472 = _t1470(msg)
                        deconstruct_result831 = _t1472
                        if !isnothing(deconstruct_result831)
                            unwrapped832 = deconstruct_result831
                            pretty_uint128_type(pp, unwrapped832)
                        else
                            function _t1473(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                    _t1474 = _get_oneof_field(_dollar_dollar, :int128_type)
                                else
                                    _t1474 = nothing
                                end
                                return _t1474
                            end
                            _t1475 = _t1473(msg)
                            deconstruct_result829 = _t1475
                            if !isnothing(deconstruct_result829)
                                unwrapped830 = deconstruct_result829
                                pretty_int128_type(pp, unwrapped830)
                            else
                                function _t1476(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                        _t1477 = _get_oneof_field(_dollar_dollar, :date_type)
                                    else
                                        _t1477 = nothing
                                    end
                                    return _t1477
                                end
                                _t1478 = _t1476(msg)
                                deconstruct_result827 = _t1478
                                if !isnothing(deconstruct_result827)
                                    unwrapped828 = deconstruct_result827
                                    pretty_date_type(pp, unwrapped828)
                                else
                                    function _t1479(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                            _t1480 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                        else
                                            _t1480 = nothing
                                        end
                                        return _t1480
                                    end
                                    _t1481 = _t1479(msg)
                                    deconstruct_result825 = _t1481
                                    if !isnothing(deconstruct_result825)
                                        unwrapped826 = deconstruct_result825
                                        pretty_datetime_type(pp, unwrapped826)
                                    else
                                        function _t1482(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                                _t1483 = _get_oneof_field(_dollar_dollar, :missing_type)
                                            else
                                                _t1483 = nothing
                                            end
                                            return _t1483
                                        end
                                        _t1484 = _t1482(msg)
                                        deconstruct_result823 = _t1484
                                        if !isnothing(deconstruct_result823)
                                            unwrapped824 = deconstruct_result823
                                            pretty_missing_type(pp, unwrapped824)
                                        else
                                            function _t1485(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                    _t1486 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                                else
                                                    _t1486 = nothing
                                                end
                                                return _t1486
                                            end
                                            _t1487 = _t1485(msg)
                                            deconstruct_result821 = _t1487
                                            if !isnothing(deconstruct_result821)
                                                unwrapped822 = deconstruct_result821
                                                pretty_decimal_type(pp, unwrapped822)
                                            else
                                                function _t1488(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                        _t1489 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                    else
                                                        _t1489 = nothing
                                                    end
                                                    return _t1489
                                                end
                                                _t1490 = _t1488(msg)
                                                deconstruct_result819 = _t1490
                                                if !isnothing(deconstruct_result819)
                                                    unwrapped820 = deconstruct_result819
                                                    pretty_boolean_type(pp, unwrapped820)
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
    flat844 = try_flat(pp, msg, pretty_unspecified_type)
    if !isnothing(flat844)
        write(pp, flat844)
        return nothing
    else
        function _t1491(_dollar_dollar)
            return _dollar_dollar
        end
        _t1492 = _t1491(msg)
        fields842 = _t1492
        unwrapped_fields843 = fields842
        write(pp, "UNKNOWN")
    end
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    flat847 = try_flat(pp, msg, pretty_string_type)
    if !isnothing(flat847)
        write(pp, flat847)
        return nothing
    else
        function _t1493(_dollar_dollar)
            return _dollar_dollar
        end
        _t1494 = _t1493(msg)
        fields845 = _t1494
        unwrapped_fields846 = fields845
        write(pp, "STRING")
    end
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    flat850 = try_flat(pp, msg, pretty_int_type)
    if !isnothing(flat850)
        write(pp, flat850)
        return nothing
    else
        function _t1495(_dollar_dollar)
            return _dollar_dollar
        end
        _t1496 = _t1495(msg)
        fields848 = _t1496
        unwrapped_fields849 = fields848
        write(pp, "INT")
    end
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    flat853 = try_flat(pp, msg, pretty_float_type)
    if !isnothing(flat853)
        write(pp, flat853)
        return nothing
    else
        function _t1497(_dollar_dollar)
            return _dollar_dollar
        end
        _t1498 = _t1497(msg)
        fields851 = _t1498
        unwrapped_fields852 = fields851
        write(pp, "FLOAT")
    end
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    flat856 = try_flat(pp, msg, pretty_uint128_type)
    if !isnothing(flat856)
        write(pp, flat856)
        return nothing
    else
        function _t1499(_dollar_dollar)
            return _dollar_dollar
        end
        _t1500 = _t1499(msg)
        fields854 = _t1500
        unwrapped_fields855 = fields854
        write(pp, "UINT128")
    end
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    flat859 = try_flat(pp, msg, pretty_int128_type)
    if !isnothing(flat859)
        write(pp, flat859)
        return nothing
    else
        function _t1501(_dollar_dollar)
            return _dollar_dollar
        end
        _t1502 = _t1501(msg)
        fields857 = _t1502
        unwrapped_fields858 = fields857
        write(pp, "INT128")
    end
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    flat862 = try_flat(pp, msg, pretty_date_type)
    if !isnothing(flat862)
        write(pp, flat862)
        return nothing
    else
        function _t1503(_dollar_dollar)
            return _dollar_dollar
        end
        _t1504 = _t1503(msg)
        fields860 = _t1504
        unwrapped_fields861 = fields860
        write(pp, "DATE")
    end
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    flat865 = try_flat(pp, msg, pretty_datetime_type)
    if !isnothing(flat865)
        write(pp, flat865)
        return nothing
    else
        function _t1505(_dollar_dollar)
            return _dollar_dollar
        end
        _t1506 = _t1505(msg)
        fields863 = _t1506
        unwrapped_fields864 = fields863
        write(pp, "DATETIME")
    end
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    flat868 = try_flat(pp, msg, pretty_missing_type)
    if !isnothing(flat868)
        write(pp, flat868)
        return nothing
    else
        function _t1507(_dollar_dollar)
            return _dollar_dollar
        end
        _t1508 = _t1507(msg)
        fields866 = _t1508
        unwrapped_fields867 = fields866
        write(pp, "MISSING")
    end
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat873 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat873)
        write(pp, flat873)
        return nothing
    else
        function _t1509(_dollar_dollar)
            return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        end
        _t1510 = _t1509(msg)
        fields869 = _t1510
        unwrapped_fields870 = fields869
        write(pp, "(")
        write(pp, "DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field871 = unwrapped_fields870[1]
        write(pp, string(field871))
        newline(pp)
        field872 = unwrapped_fields870[2]
        write(pp, string(field872))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    flat876 = try_flat(pp, msg, pretty_boolean_type)
    if !isnothing(flat876)
        write(pp, flat876)
        return nothing
    else
        function _t1511(_dollar_dollar)
            return _dollar_dollar
        end
        _t1512 = _t1511(msg)
        fields874 = _t1512
        unwrapped_fields875 = fields874
        write(pp, "BOOLEAN")
    end
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat881 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat881)
        write(pp, flat881)
        return nothing
    else
        function _t1513(_dollar_dollar)
            return _dollar_dollar
        end
        _t1514 = _t1513(msg)
        fields877 = _t1514
        unwrapped_fields878 = fields877
        write(pp, "|")
        if !isempty(unwrapped_fields878)
            write(pp, " ")
            for (i1515, elem879) in enumerate(unwrapped_fields878)
                i880 = i1515 - 1
                if (i880 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem879)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat908 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat908)
        write(pp, flat908)
        return nothing
    else
        function _t1516(_dollar_dollar)
            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                _t1517 = _get_oneof_field(_dollar_dollar, :conjunction)
            else
                _t1517 = nothing
            end
            return _t1517
        end
        _t1518 = _t1516(msg)
        deconstruct_result906 = _t1518
        if !isnothing(deconstruct_result906)
            unwrapped907 = deconstruct_result906
            pretty_true(pp, unwrapped907)
        else
            function _t1519(_dollar_dollar)
                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                    _t1520 = _get_oneof_field(_dollar_dollar, :disjunction)
                else
                    _t1520 = nothing
                end
                return _t1520
            end
            _t1521 = _t1519(msg)
            deconstruct_result904 = _t1521
            if !isnothing(deconstruct_result904)
                unwrapped905 = deconstruct_result904
                pretty_false(pp, unwrapped905)
            else
                function _t1522(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("exists"))
                        _t1523 = _get_oneof_field(_dollar_dollar, :exists)
                    else
                        _t1523 = nothing
                    end
                    return _t1523
                end
                _t1524 = _t1522(msg)
                deconstruct_result902 = _t1524
                if !isnothing(deconstruct_result902)
                    unwrapped903 = deconstruct_result902
                    pretty_exists(pp, unwrapped903)
                else
                    function _t1525(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                            _t1526 = _get_oneof_field(_dollar_dollar, :reduce)
                        else
                            _t1526 = nothing
                        end
                        return _t1526
                    end
                    _t1527 = _t1525(msg)
                    deconstruct_result900 = _t1527
                    if !isnothing(deconstruct_result900)
                        unwrapped901 = deconstruct_result900
                        pretty_reduce(pp, unwrapped901)
                    else
                        function _t1528(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("conjunction"))
                                _t1529 = _get_oneof_field(_dollar_dollar, :conjunction)
                            else
                                _t1529 = nothing
                            end
                            return _t1529
                        end
                        _t1530 = _t1528(msg)
                        deconstruct_result898 = _t1530
                        if !isnothing(deconstruct_result898)
                            unwrapped899 = deconstruct_result898
                            pretty_conjunction(pp, unwrapped899)
                        else
                            function _t1531(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("disjunction"))
                                    _t1532 = _get_oneof_field(_dollar_dollar, :disjunction)
                                else
                                    _t1532 = nothing
                                end
                                return _t1532
                            end
                            _t1533 = _t1531(msg)
                            deconstruct_result896 = _t1533
                            if !isnothing(deconstruct_result896)
                                unwrapped897 = deconstruct_result896
                                pretty_disjunction(pp, unwrapped897)
                            else
                                function _t1534(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("not"))
                                        _t1535 = _get_oneof_field(_dollar_dollar, :not)
                                    else
                                        _t1535 = nothing
                                    end
                                    return _t1535
                                end
                                _t1536 = _t1534(msg)
                                deconstruct_result894 = _t1536
                                if !isnothing(deconstruct_result894)
                                    unwrapped895 = deconstruct_result894
                                    pretty_not(pp, unwrapped895)
                                else
                                    function _t1537(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                            _t1538 = _get_oneof_field(_dollar_dollar, :ffi)
                                        else
                                            _t1538 = nothing
                                        end
                                        return _t1538
                                    end
                                    _t1539 = _t1537(msg)
                                    deconstruct_result892 = _t1539
                                    if !isnothing(deconstruct_result892)
                                        unwrapped893 = deconstruct_result892
                                        pretty_ffi(pp, unwrapped893)
                                    else
                                        function _t1540(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                                _t1541 = _get_oneof_field(_dollar_dollar, :atom)
                                            else
                                                _t1541 = nothing
                                            end
                                            return _t1541
                                        end
                                        _t1542 = _t1540(msg)
                                        deconstruct_result890 = _t1542
                                        if !isnothing(deconstruct_result890)
                                            unwrapped891 = deconstruct_result890
                                            pretty_atom(pp, unwrapped891)
                                        else
                                            function _t1543(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                    _t1544 = _get_oneof_field(_dollar_dollar, :pragma)
                                                else
                                                    _t1544 = nothing
                                                end
                                                return _t1544
                                            end
                                            _t1545 = _t1543(msg)
                                            deconstruct_result888 = _t1545
                                            if !isnothing(deconstruct_result888)
                                                unwrapped889 = deconstruct_result888
                                                pretty_pragma(pp, unwrapped889)
                                            else
                                                function _t1546(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                        _t1547 = _get_oneof_field(_dollar_dollar, :primitive)
                                                    else
                                                        _t1547 = nothing
                                                    end
                                                    return _t1547
                                                end
                                                _t1548 = _t1546(msg)
                                                deconstruct_result886 = _t1548
                                                if !isnothing(deconstruct_result886)
                                                    unwrapped887 = deconstruct_result886
                                                    pretty_primitive(pp, unwrapped887)
                                                else
                                                    function _t1549(_dollar_dollar)
                                                        if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                            _t1550 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                        else
                                                            _t1550 = nothing
                                                        end
                                                        return _t1550
                                                    end
                                                    _t1551 = _t1549(msg)
                                                    deconstruct_result884 = _t1551
                                                    if !isnothing(deconstruct_result884)
                                                        unwrapped885 = deconstruct_result884
                                                        pretty_rel_atom(pp, unwrapped885)
                                                    else
                                                        function _t1552(_dollar_dollar)
                                                            if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                                _t1553 = _get_oneof_field(_dollar_dollar, :cast)
                                                            else
                                                                _t1553 = nothing
                                                            end
                                                            return _t1553
                                                        end
                                                        _t1554 = _t1552(msg)
                                                        deconstruct_result882 = _t1554
                                                        if !isnothing(deconstruct_result882)
                                                            unwrapped883 = deconstruct_result882
                                                            pretty_cast(pp, unwrapped883)
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
    flat911 = try_flat(pp, msg, pretty_true)
    if !isnothing(flat911)
        write(pp, flat911)
        return nothing
    else
        function _t1555(_dollar_dollar)
            return _dollar_dollar
        end
        _t1556 = _t1555(msg)
        fields909 = _t1556
        unwrapped_fields910 = fields909
        write(pp, "(")
        write(pp, "true")
        write(pp, ")")
    end
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat914 = try_flat(pp, msg, pretty_false)
    if !isnothing(flat914)
        write(pp, flat914)
        return nothing
    else
        function _t1557(_dollar_dollar)
            return _dollar_dollar
        end
        _t1558 = _t1557(msg)
        fields912 = _t1558
        unwrapped_fields913 = fields912
        write(pp, "(")
        write(pp, "false")
        write(pp, ")")
    end
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat919 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat919)
        write(pp, flat919)
        return nothing
    else
        function _t1559(_dollar_dollar)
            _t1560 = deconstruct_bindings(pp, _dollar_dollar.body)
            return (_t1560, _dollar_dollar.body.value,)
        end
        _t1561 = _t1559(msg)
        fields915 = _t1561
        unwrapped_fields916 = fields915
        write(pp, "(")
        write(pp, "exists")
        indent_sexp!(pp)
        newline(pp)
        field917 = unwrapped_fields916[1]
        pretty_bindings(pp, field917)
        newline(pp)
        field918 = unwrapped_fields916[2]
        pretty_formula(pp, field918)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat925 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat925)
        write(pp, flat925)
        return nothing
    else
        function _t1562(_dollar_dollar)
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        end
        _t1563 = _t1562(msg)
        fields920 = _t1563
        unwrapped_fields921 = fields920
        write(pp, "(")
        write(pp, "reduce")
        indent_sexp!(pp)
        newline(pp)
        field922 = unwrapped_fields921[1]
        pretty_abstraction(pp, field922)
        newline(pp)
        field923 = unwrapped_fields921[2]
        pretty_abstraction(pp, field923)
        newline(pp)
        field924 = unwrapped_fields921[3]
        pretty_terms(pp, field924)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat930 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat930)
        write(pp, flat930)
        return nothing
    else
        function _t1564(_dollar_dollar)
            return _dollar_dollar
        end
        _t1565 = _t1564(msg)
        fields926 = _t1565
        unwrapped_fields927 = fields926
        write(pp, "(")
        write(pp, "terms")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields927)
            newline(pp)
            for (i1566, elem928) in enumerate(unwrapped_fields927)
                i929 = i1566 - 1
                if (i929 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem928)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat935 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat935)
        write(pp, flat935)
        return nothing
    else
        function _t1567(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("var"))
                _t1568 = _get_oneof_field(_dollar_dollar, :var)
            else
                _t1568 = nothing
            end
            return _t1568
        end
        _t1569 = _t1567(msg)
        deconstruct_result933 = _t1569
        if !isnothing(deconstruct_result933)
            unwrapped934 = deconstruct_result933
            pretty_var(pp, unwrapped934)
        else
            function _t1570(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("constant"))
                    _t1571 = _get_oneof_field(_dollar_dollar, :constant)
                else
                    _t1571 = nothing
                end
                return _t1571
            end
            _t1572 = _t1570(msg)
            deconstruct_result931 = _t1572
            if !isnothing(deconstruct_result931)
                unwrapped932 = deconstruct_result931
                pretty_constant(pp, unwrapped932)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat938 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat938)
        write(pp, flat938)
        return nothing
    else
        function _t1573(_dollar_dollar)
            return _dollar_dollar.name
        end
        _t1574 = _t1573(msg)
        fields936 = _t1574
        unwrapped_fields937 = fields936
        write(pp, unwrapped_fields937)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat941 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat941)
        write(pp, flat941)
        return nothing
    else
        function _t1575(_dollar_dollar)
            return _dollar_dollar
        end
        _t1576 = _t1575(msg)
        fields939 = _t1576
        unwrapped_fields940 = fields939
        pretty_value(pp, unwrapped_fields940)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat946 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        function _t1577(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1578 = _t1577(msg)
        fields942 = _t1578
        unwrapped_fields943 = fields942
        write(pp, "(")
        write(pp, "and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields943)
            newline(pp)
            for (i1579, elem944) in enumerate(unwrapped_fields943)
                i945 = i1579 - 1
                if (i945 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem944)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat951 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat951)
        write(pp, flat951)
        return nothing
    else
        function _t1580(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1581 = _t1580(msg)
        fields947 = _t1581
        unwrapped_fields948 = fields947
        write(pp, "(")
        write(pp, "or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields948)
            newline(pp)
            for (i1582, elem949) in enumerate(unwrapped_fields948)
                i950 = i1582 - 1
                if (i950 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem949)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat954 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat954)
        write(pp, flat954)
        return nothing
    else
        function _t1583(_dollar_dollar)
            return _dollar_dollar.arg
        end
        _t1584 = _t1583(msg)
        fields952 = _t1584
        unwrapped_fields953 = fields952
        write(pp, "(")
        write(pp, "not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields953)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat960 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat960)
        write(pp, flat960)
        return nothing
    else
        function _t1585(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        end
        _t1586 = _t1585(msg)
        fields955 = _t1586
        unwrapped_fields956 = fields955
        write(pp, "(")
        write(pp, "ffi")
        indent_sexp!(pp)
        newline(pp)
        field957 = unwrapped_fields956[1]
        pretty_name(pp, field957)
        newline(pp)
        field958 = unwrapped_fields956[2]
        pretty_ffi_args(pp, field958)
        newline(pp)
        field959 = unwrapped_fields956[3]
        pretty_terms(pp, field959)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat963 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat963)
        write(pp, flat963)
        return nothing
    else
        function _t1587(_dollar_dollar)
            return _dollar_dollar
        end
        _t1588 = _t1587(msg)
        fields961 = _t1588
        unwrapped_fields962 = fields961
        write(pp, ":")
        write(pp, unwrapped_fields962)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat968 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat968)
        write(pp, flat968)
        return nothing
    else
        function _t1589(_dollar_dollar)
            return _dollar_dollar
        end
        _t1590 = _t1589(msg)
        fields964 = _t1590
        unwrapped_fields965 = fields964
        write(pp, "(")
        write(pp, "args")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields965)
            newline(pp)
            for (i1591, elem966) in enumerate(unwrapped_fields965)
                i967 = i1591 - 1
                if (i967 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem966)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat975 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat975)
        write(pp, flat975)
        return nothing
    else
        function _t1592(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1593 = _t1592(msg)
        fields969 = _t1593
        unwrapped_fields970 = fields969
        write(pp, "(")
        write(pp, "atom")
        indent_sexp!(pp)
        newline(pp)
        field971 = unwrapped_fields970[1]
        pretty_relation_id(pp, field971)
        field972 = unwrapped_fields970[2]
        if !isempty(field972)
            newline(pp)
            for (i1594, elem973) in enumerate(field972)
                i974 = i1594 - 1
                if (i974 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem973)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat982 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat982)
        write(pp, flat982)
        return nothing
    else
        function _t1595(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1596 = _t1595(msg)
        fields976 = _t1596
        unwrapped_fields977 = fields976
        write(pp, "(")
        write(pp, "pragma")
        indent_sexp!(pp)
        newline(pp)
        field978 = unwrapped_fields977[1]
        pretty_name(pp, field978)
        field979 = unwrapped_fields977[2]
        if !isempty(field979)
            newline(pp)
            for (i1597, elem980) in enumerate(field979)
                i981 = i1597 - 1
                if (i981 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem980)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat998 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat998)
        write(pp, flat998)
        return nothing
    else
        function _t1598(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1599 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1599 = nothing
            end
            return _t1599
        end
        _t1600 = _t1598(msg)
        guard_result997 = _t1600
        if !isnothing(guard_result997)
            pretty_eq(pp, msg)
        else
            function _t1601(_dollar_dollar)
                if _dollar_dollar.name == "rel_primitive_lt_monotype"
                    _t1602 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1602 = nothing
                end
                return _t1602
            end
            _t1603 = _t1601(msg)
            guard_result996 = _t1603
            if !isnothing(guard_result996)
                pretty_lt(pp, msg)
            else
                function _t1604(_dollar_dollar)
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                        _t1605 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1605 = nothing
                    end
                    return _t1605
                end
                _t1606 = _t1604(msg)
                guard_result995 = _t1606
                if !isnothing(guard_result995)
                    pretty_lt_eq(pp, msg)
                else
                    function _t1607(_dollar_dollar)
                        if _dollar_dollar.name == "rel_primitive_gt_monotype"
                            _t1608 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1608 = nothing
                        end
                        return _t1608
                    end
                    _t1609 = _t1607(msg)
                    guard_result994 = _t1609
                    if !isnothing(guard_result994)
                        pretty_gt(pp, msg)
                    else
                        function _t1610(_dollar_dollar)
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                                _t1611 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                            else
                                _t1611 = nothing
                            end
                            return _t1611
                        end
                        _t1612 = _t1610(msg)
                        guard_result993 = _t1612
                        if !isnothing(guard_result993)
                            pretty_gt_eq(pp, msg)
                        else
                            function _t1613(_dollar_dollar)
                                if _dollar_dollar.name == "rel_primitive_add_monotype"
                                    _t1614 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1614 = nothing
                                end
                                return _t1614
                            end
                            _t1615 = _t1613(msg)
                            guard_result992 = _t1615
                            if !isnothing(guard_result992)
                                pretty_add(pp, msg)
                            else
                                function _t1616(_dollar_dollar)
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                        _t1617 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1617 = nothing
                                    end
                                    return _t1617
                                end
                                _t1618 = _t1616(msg)
                                guard_result991 = _t1618
                                if !isnothing(guard_result991)
                                    pretty_minus(pp, msg)
                                else
                                    function _t1619(_dollar_dollar)
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                            _t1620 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1620 = nothing
                                        end
                                        return _t1620
                                    end
                                    _t1621 = _t1619(msg)
                                    guard_result990 = _t1621
                                    if !isnothing(guard_result990)
                                        pretty_multiply(pp, msg)
                                    else
                                        function _t1622(_dollar_dollar)
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                                _t1623 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                            else
                                                _t1623 = nothing
                                            end
                                            return _t1623
                                        end
                                        _t1624 = _t1622(msg)
                                        guard_result989 = _t1624
                                        if !isnothing(guard_result989)
                                            pretty_divide(pp, msg)
                                        else
                                            function _t1625(_dollar_dollar)
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            end
                                            _t1626 = _t1625(msg)
                                            fields983 = _t1626
                                            unwrapped_fields984 = fields983
                                            write(pp, "(")
                                            write(pp, "primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field985 = unwrapped_fields984[1]
                                            pretty_name(pp, field985)
                                            field986 = unwrapped_fields984[2]
                                            if !isempty(field986)
                                                newline(pp)
                                                for (i1627, elem987) in enumerate(field986)
                                                    i988 = i1627 - 1
                                                    if (i988 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem987)
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
    flat1003 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1003)
        write(pp, flat1003)
        return nothing
    else
        function _t1628(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1629 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1629 = nothing
            end
            return _t1629
        end
        _t1630 = _t1628(msg)
        fields999 = _t1630
        unwrapped_fields1000 = fields999
        write(pp, "(")
        write(pp, "=")
        indent_sexp!(pp)
        newline(pp)
        field1001 = unwrapped_fields1000[1]
        pretty_term(pp, field1001)
        newline(pp)
        field1002 = unwrapped_fields1000[2]
        pretty_term(pp, field1002)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1008 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1008)
        write(pp, flat1008)
        return nothing
    else
        function _t1631(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1632 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1632 = nothing
            end
            return _t1632
        end
        _t1633 = _t1631(msg)
        fields1004 = _t1633
        unwrapped_fields1005 = fields1004
        write(pp, "(")
        write(pp, "<")
        indent_sexp!(pp)
        newline(pp)
        field1006 = unwrapped_fields1005[1]
        pretty_term(pp, field1006)
        newline(pp)
        field1007 = unwrapped_fields1005[2]
        pretty_term(pp, field1007)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1013 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1013)
        write(pp, flat1013)
        return nothing
    else
        function _t1634(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                _t1635 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1635 = nothing
            end
            return _t1635
        end
        _t1636 = _t1634(msg)
        fields1009 = _t1636
        unwrapped_fields1010 = fields1009
        write(pp, "(")
        write(pp, "<=")
        indent_sexp!(pp)
        newline(pp)
        field1011 = unwrapped_fields1010[1]
        pretty_term(pp, field1011)
        newline(pp)
        field1012 = unwrapped_fields1010[2]
        pretty_term(pp, field1012)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1018 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1018)
        write(pp, flat1018)
        return nothing
    else
        function _t1637(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_monotype"
                _t1638 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1638 = nothing
            end
            return _t1638
        end
        _t1639 = _t1637(msg)
        fields1014 = _t1639
        unwrapped_fields1015 = fields1014
        write(pp, "(")
        write(pp, ">")
        indent_sexp!(pp)
        newline(pp)
        field1016 = unwrapped_fields1015[1]
        pretty_term(pp, field1016)
        newline(pp)
        field1017 = unwrapped_fields1015[2]
        pretty_term(pp, field1017)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1023 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1023)
        write(pp, flat1023)
        return nothing
    else
        function _t1640(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                _t1641 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1641 = nothing
            end
            return _t1641
        end
        _t1642 = _t1640(msg)
        fields1019 = _t1642
        unwrapped_fields1020 = fields1019
        write(pp, "(")
        write(pp, ">=")
        indent_sexp!(pp)
        newline(pp)
        field1021 = unwrapped_fields1020[1]
        pretty_term(pp, field1021)
        newline(pp)
        field1022 = unwrapped_fields1020[2]
        pretty_term(pp, field1022)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1029 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1029)
        write(pp, flat1029)
        return nothing
    else
        function _t1643(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_add_monotype"
                _t1644 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1644 = nothing
            end
            return _t1644
        end
        _t1645 = _t1643(msg)
        fields1024 = _t1645
        unwrapped_fields1025 = fields1024
        write(pp, "(")
        write(pp, "+")
        indent_sexp!(pp)
        newline(pp)
        field1026 = unwrapped_fields1025[1]
        pretty_term(pp, field1026)
        newline(pp)
        field1027 = unwrapped_fields1025[2]
        pretty_term(pp, field1027)
        newline(pp)
        field1028 = unwrapped_fields1025[3]
        pretty_term(pp, field1028)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1035 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1035)
        write(pp, flat1035)
        return nothing
    else
        function _t1646(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                _t1647 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1647 = nothing
            end
            return _t1647
        end
        _t1648 = _t1646(msg)
        fields1030 = _t1648
        unwrapped_fields1031 = fields1030
        write(pp, "(")
        write(pp, "-")
        indent_sexp!(pp)
        newline(pp)
        field1032 = unwrapped_fields1031[1]
        pretty_term(pp, field1032)
        newline(pp)
        field1033 = unwrapped_fields1031[2]
        pretty_term(pp, field1033)
        newline(pp)
        field1034 = unwrapped_fields1031[3]
        pretty_term(pp, field1034)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1041 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1041)
        write(pp, flat1041)
        return nothing
    else
        function _t1649(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                _t1650 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1650 = nothing
            end
            return _t1650
        end
        _t1651 = _t1649(msg)
        fields1036 = _t1651
        unwrapped_fields1037 = fields1036
        write(pp, "(")
        write(pp, "*")
        indent_sexp!(pp)
        newline(pp)
        field1038 = unwrapped_fields1037[1]
        pretty_term(pp, field1038)
        newline(pp)
        field1039 = unwrapped_fields1037[2]
        pretty_term(pp, field1039)
        newline(pp)
        field1040 = unwrapped_fields1037[3]
        pretty_term(pp, field1040)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1047 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1047)
        write(pp, flat1047)
        return nothing
    else
        function _t1652(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                _t1653 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1653 = nothing
            end
            return _t1653
        end
        _t1654 = _t1652(msg)
        fields1042 = _t1654
        unwrapped_fields1043 = fields1042
        write(pp, "(")
        write(pp, "/")
        indent_sexp!(pp)
        newline(pp)
        field1044 = unwrapped_fields1043[1]
        pretty_term(pp, field1044)
        newline(pp)
        field1045 = unwrapped_fields1043[2]
        pretty_term(pp, field1045)
        newline(pp)
        field1046 = unwrapped_fields1043[3]
        pretty_term(pp, field1046)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1052 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1052)
        write(pp, flat1052)
        return nothing
    else
        function _t1655(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
                _t1656 = _get_oneof_field(_dollar_dollar, :specialized_value)
            else
                _t1656 = nothing
            end
            return _t1656
        end
        _t1657 = _t1655(msg)
        deconstruct_result1050 = _t1657
        if !isnothing(deconstruct_result1050)
            unwrapped1051 = deconstruct_result1050
            pretty_specialized_value(pp, unwrapped1051)
        else
            function _t1658(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("term"))
                    _t1659 = _get_oneof_field(_dollar_dollar, :term)
                else
                    _t1659 = nothing
                end
                return _t1659
            end
            _t1660 = _t1658(msg)
            deconstruct_result1048 = _t1660
            if !isnothing(deconstruct_result1048)
                unwrapped1049 = deconstruct_result1048
                pretty_term(pp, unwrapped1049)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1055 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1055)
        write(pp, flat1055)
        return nothing
    else
        function _t1661(_dollar_dollar)
            return _dollar_dollar
        end
        _t1662 = _t1661(msg)
        fields1053 = _t1662
        unwrapped_fields1054 = fields1053
        write(pp, "#")
        pretty_value(pp, unwrapped_fields1054)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1062 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1062)
        write(pp, flat1062)
        return nothing
    else
        function _t1663(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1664 = _t1663(msg)
        fields1056 = _t1664
        unwrapped_fields1057 = fields1056
        write(pp, "(")
        write(pp, "relatom")
        indent_sexp!(pp)
        newline(pp)
        field1058 = unwrapped_fields1057[1]
        pretty_name(pp, field1058)
        field1059 = unwrapped_fields1057[2]
        if !isempty(field1059)
            newline(pp)
            for (i1665, elem1060) in enumerate(field1059)
                i1061 = i1665 - 1
                if (i1061 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1060)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1067 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1067)
        write(pp, flat1067)
        return nothing
    else
        function _t1666(_dollar_dollar)
            return (_dollar_dollar.input, _dollar_dollar.result,)
        end
        _t1667 = _t1666(msg)
        fields1063 = _t1667
        unwrapped_fields1064 = fields1063
        write(pp, "(")
        write(pp, "cast")
        indent_sexp!(pp)
        newline(pp)
        field1065 = unwrapped_fields1064[1]
        pretty_term(pp, field1065)
        newline(pp)
        field1066 = unwrapped_fields1064[2]
        pretty_term(pp, field1066)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1072 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1072)
        write(pp, flat1072)
        return nothing
    else
        function _t1668(_dollar_dollar)
            return _dollar_dollar
        end
        _t1669 = _t1668(msg)
        fields1068 = _t1669
        unwrapped_fields1069 = fields1068
        write(pp, "(")
        write(pp, "attrs")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1069)
            newline(pp)
            for (i1670, elem1070) in enumerate(unwrapped_fields1069)
                i1071 = i1670 - 1
                if (i1071 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1070)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1079 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1079)
        write(pp, flat1079)
        return nothing
    else
        function _t1671(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args,)
        end
        _t1672 = _t1671(msg)
        fields1073 = _t1672
        unwrapped_fields1074 = fields1073
        write(pp, "(")
        write(pp, "attribute")
        indent_sexp!(pp)
        newline(pp)
        field1075 = unwrapped_fields1074[1]
        pretty_name(pp, field1075)
        field1076 = unwrapped_fields1074[2]
        if !isempty(field1076)
            newline(pp)
            for (i1673, elem1077) in enumerate(field1076)
                i1078 = i1673 - 1
                if (i1078 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem1077)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1086 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1086)
        write(pp, flat1086)
        return nothing
    else
        function _t1674(_dollar_dollar)
            return (_dollar_dollar.var"#global", _dollar_dollar.body,)
        end
        _t1675 = _t1674(msg)
        fields1080 = _t1675
        unwrapped_fields1081 = fields1080
        write(pp, "(")
        write(pp, "algorithm")
        indent_sexp!(pp)
        field1082 = unwrapped_fields1081[1]
        if !isempty(field1082)
            newline(pp)
            for (i1676, elem1083) in enumerate(field1082)
                i1084 = i1676 - 1
                if (i1084 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1083)
            end
        end
        newline(pp)
        field1085 = unwrapped_fields1081[2]
        pretty_script(pp, field1085)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1091 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1091)
        write(pp, flat1091)
        return nothing
    else
        function _t1677(_dollar_dollar)
            return _dollar_dollar.constructs
        end
        _t1678 = _t1677(msg)
        fields1087 = _t1678
        unwrapped_fields1088 = fields1087
        write(pp, "(")
        write(pp, "script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1088)
            newline(pp)
            for (i1679, elem1089) in enumerate(unwrapped_fields1088)
                i1090 = i1679 - 1
                if (i1090 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1089)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1096 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        function _t1680(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("loop"))
                _t1681 = _get_oneof_field(_dollar_dollar, :loop)
            else
                _t1681 = nothing
            end
            return _t1681
        end
        _t1682 = _t1680(msg)
        deconstruct_result1094 = _t1682
        if !isnothing(deconstruct_result1094)
            unwrapped1095 = deconstruct_result1094
            pretty_loop(pp, unwrapped1095)
        else
            function _t1683(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                    _t1684 = _get_oneof_field(_dollar_dollar, :instruction)
                else
                    _t1684 = nothing
                end
                return _t1684
            end
            _t1685 = _t1683(msg)
            deconstruct_result1092 = _t1685
            if !isnothing(deconstruct_result1092)
                unwrapped1093 = deconstruct_result1092
                pretty_instruction(pp, unwrapped1093)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1101 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1101)
        write(pp, flat1101)
        return nothing
    else
        function _t1686(_dollar_dollar)
            return (_dollar_dollar.init, _dollar_dollar.body,)
        end
        _t1687 = _t1686(msg)
        fields1097 = _t1687
        unwrapped_fields1098 = fields1097
        write(pp, "(")
        write(pp, "loop")
        indent_sexp!(pp)
        newline(pp)
        field1099 = unwrapped_fields1098[1]
        pretty_init(pp, field1099)
        newline(pp)
        field1100 = unwrapped_fields1098[2]
        pretty_script(pp, field1100)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1106 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1106)
        write(pp, flat1106)
        return nothing
    else
        function _t1688(_dollar_dollar)
            return _dollar_dollar
        end
        _t1689 = _t1688(msg)
        fields1102 = _t1689
        unwrapped_fields1103 = fields1102
        write(pp, "(")
        write(pp, "init")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1103)
            newline(pp)
            for (i1690, elem1104) in enumerate(unwrapped_fields1103)
                i1105 = i1690 - 1
                if (i1105 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1104)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1117 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1117)
        write(pp, flat1117)
        return nothing
    else
        function _t1691(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("assign"))
                _t1692 = _get_oneof_field(_dollar_dollar, :assign)
            else
                _t1692 = nothing
            end
            return _t1692
        end
        _t1693 = _t1691(msg)
        deconstruct_result1115 = _t1693
        if !isnothing(deconstruct_result1115)
            unwrapped1116 = deconstruct_result1115
            pretty_assign(pp, unwrapped1116)
        else
            function _t1694(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                    _t1695 = _get_oneof_field(_dollar_dollar, :upsert)
                else
                    _t1695 = nothing
                end
                return _t1695
            end
            _t1696 = _t1694(msg)
            deconstruct_result1113 = _t1696
            if !isnothing(deconstruct_result1113)
                unwrapped1114 = deconstruct_result1113
                pretty_upsert(pp, unwrapped1114)
            else
                function _t1697(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("#break"))
                        _t1698 = _get_oneof_field(_dollar_dollar, :var"#break")
                    else
                        _t1698 = nothing
                    end
                    return _t1698
                end
                _t1699 = _t1697(msg)
                deconstruct_result1111 = _t1699
                if !isnothing(deconstruct_result1111)
                    unwrapped1112 = deconstruct_result1111
                    pretty_break(pp, unwrapped1112)
                else
                    function _t1700(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                            _t1701 = _get_oneof_field(_dollar_dollar, :monoid_def)
                        else
                            _t1701 = nothing
                        end
                        return _t1701
                    end
                    _t1702 = _t1700(msg)
                    deconstruct_result1109 = _t1702
                    if !isnothing(deconstruct_result1109)
                        unwrapped1110 = deconstruct_result1109
                        pretty_monoid_def(pp, unwrapped1110)
                    else
                        function _t1703(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                                _t1704 = _get_oneof_field(_dollar_dollar, :monus_def)
                            else
                                _t1704 = nothing
                            end
                            return _t1704
                        end
                        _t1705 = _t1703(msg)
                        deconstruct_result1107 = _t1705
                        if !isnothing(deconstruct_result1107)
                            unwrapped1108 = deconstruct_result1107
                            pretty_monus_def(pp, unwrapped1108)
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
    flat1124 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1124)
        write(pp, flat1124)
        return nothing
    else
        function _t1706(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1707 = _dollar_dollar.attrs
            else
                _t1707 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1707,)
        end
        _t1708 = _t1706(msg)
        fields1118 = _t1708
        unwrapped_fields1119 = fields1118
        write(pp, "(")
        write(pp, "assign")
        indent_sexp!(pp)
        newline(pp)
        field1120 = unwrapped_fields1119[1]
        pretty_relation_id(pp, field1120)
        newline(pp)
        field1121 = unwrapped_fields1119[2]
        pretty_abstraction(pp, field1121)
        field1122 = unwrapped_fields1119[3]
        if !isnothing(field1122)
            newline(pp)
            opt_val1123 = field1122
            pretty_attrs(pp, opt_val1123)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1131 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1131)
        write(pp, flat1131)
        return nothing
    else
        function _t1709(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1710 = _dollar_dollar.attrs
            else
                _t1710 = nothing
            end
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1710,)
        end
        _t1711 = _t1709(msg)
        fields1125 = _t1711
        unwrapped_fields1126 = fields1125
        write(pp, "(")
        write(pp, "upsert")
        indent_sexp!(pp)
        newline(pp)
        field1127 = unwrapped_fields1126[1]
        pretty_relation_id(pp, field1127)
        newline(pp)
        field1128 = unwrapped_fields1126[2]
        pretty_abstraction_with_arity(pp, field1128)
        field1129 = unwrapped_fields1126[3]
        if !isnothing(field1129)
            newline(pp)
            opt_val1130 = field1129
            pretty_attrs(pp, opt_val1130)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1136 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1136)
        write(pp, flat1136)
        return nothing
    else
        function _t1712(_dollar_dollar)
            _t1713 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
            return (_t1713, _dollar_dollar[1].value,)
        end
        _t1714 = _t1712(msg)
        fields1132 = _t1714
        unwrapped_fields1133 = fields1132
        write(pp, "(")
        indent!(pp)
        field1134 = unwrapped_fields1133[1]
        pretty_bindings(pp, field1134)
        newline(pp)
        field1135 = unwrapped_fields1133[2]
        pretty_formula(pp, field1135)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1143 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1143)
        write(pp, flat1143)
        return nothing
    else
        function _t1715(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1716 = _dollar_dollar.attrs
            else
                _t1716 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1716,)
        end
        _t1717 = _t1715(msg)
        fields1137 = _t1717
        unwrapped_fields1138 = fields1137
        write(pp, "(")
        write(pp, "break")
        indent_sexp!(pp)
        newline(pp)
        field1139 = unwrapped_fields1138[1]
        pretty_relation_id(pp, field1139)
        newline(pp)
        field1140 = unwrapped_fields1138[2]
        pretty_abstraction(pp, field1140)
        field1141 = unwrapped_fields1138[3]
        if !isnothing(field1141)
            newline(pp)
            opt_val1142 = field1141
            pretty_attrs(pp, opt_val1142)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1151 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1151)
        write(pp, flat1151)
        return nothing
    else
        function _t1718(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1719 = _dollar_dollar.attrs
            else
                _t1719 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1719,)
        end
        _t1720 = _t1718(msg)
        fields1144 = _t1720
        unwrapped_fields1145 = fields1144
        write(pp, "(")
        write(pp, "monoid")
        indent_sexp!(pp)
        newline(pp)
        field1146 = unwrapped_fields1145[1]
        pretty_monoid(pp, field1146)
        newline(pp)
        field1147 = unwrapped_fields1145[2]
        pretty_relation_id(pp, field1147)
        newline(pp)
        field1148 = unwrapped_fields1145[3]
        pretty_abstraction_with_arity(pp, field1148)
        field1149 = unwrapped_fields1145[4]
        if !isnothing(field1149)
            newline(pp)
            opt_val1150 = field1149
            pretty_attrs(pp, opt_val1150)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1160 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1160)
        write(pp, flat1160)
        return nothing
    else
        function _t1721(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
                _t1722 = _get_oneof_field(_dollar_dollar, :or_monoid)
            else
                _t1722 = nothing
            end
            return _t1722
        end
        _t1723 = _t1721(msg)
        deconstruct_result1158 = _t1723
        if !isnothing(deconstruct_result1158)
            unwrapped1159 = deconstruct_result1158
            pretty_or_monoid(pp, unwrapped1159)
        else
            function _t1724(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                    _t1725 = _get_oneof_field(_dollar_dollar, :min_monoid)
                else
                    _t1725 = nothing
                end
                return _t1725
            end
            _t1726 = _t1724(msg)
            deconstruct_result1156 = _t1726
            if !isnothing(deconstruct_result1156)
                unwrapped1157 = deconstruct_result1156
                pretty_min_monoid(pp, unwrapped1157)
            else
                function _t1727(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                        _t1728 = _get_oneof_field(_dollar_dollar, :max_monoid)
                    else
                        _t1728 = nothing
                    end
                    return _t1728
                end
                _t1729 = _t1727(msg)
                deconstruct_result1154 = _t1729
                if !isnothing(deconstruct_result1154)
                    unwrapped1155 = deconstruct_result1154
                    pretty_max_monoid(pp, unwrapped1155)
                else
                    function _t1730(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                            _t1731 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                        else
                            _t1731 = nothing
                        end
                        return _t1731
                    end
                    _t1732 = _t1730(msg)
                    deconstruct_result1152 = _t1732
                    if !isnothing(deconstruct_result1152)
                        unwrapped1153 = deconstruct_result1152
                        pretty_sum_monoid(pp, unwrapped1153)
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
    flat1163 = try_flat(pp, msg, pretty_or_monoid)
    if !isnothing(flat1163)
        write(pp, flat1163)
        return nothing
    else
        function _t1733(_dollar_dollar)
            return _dollar_dollar
        end
        _t1734 = _t1733(msg)
        fields1161 = _t1734
        unwrapped_fields1162 = fields1161
        write(pp, "(")
        write(pp, "or")
        write(pp, ")")
    end
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1166 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1166)
        write(pp, flat1166)
        return nothing
    else
        function _t1735(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1736 = _t1735(msg)
        fields1164 = _t1736
        unwrapped_fields1165 = fields1164
        write(pp, "(")
        write(pp, "min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1165)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1169 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1169)
        write(pp, flat1169)
        return nothing
    else
        function _t1737(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1738 = _t1737(msg)
        fields1167 = _t1738
        unwrapped_fields1168 = fields1167
        write(pp, "(")
        write(pp, "max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1168)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1172 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1172)
        write(pp, flat1172)
        return nothing
    else
        function _t1739(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1740 = _t1739(msg)
        fields1170 = _t1740
        unwrapped_fields1171 = fields1170
        write(pp, "(")
        write(pp, "sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1171)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1180 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1180)
        write(pp, flat1180)
        return nothing
    else
        function _t1741(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1742 = _dollar_dollar.attrs
            else
                _t1742 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1742,)
        end
        _t1743 = _t1741(msg)
        fields1173 = _t1743
        unwrapped_fields1174 = fields1173
        write(pp, "(")
        write(pp, "monus")
        indent_sexp!(pp)
        newline(pp)
        field1175 = unwrapped_fields1174[1]
        pretty_monoid(pp, field1175)
        newline(pp)
        field1176 = unwrapped_fields1174[2]
        pretty_relation_id(pp, field1176)
        newline(pp)
        field1177 = unwrapped_fields1174[3]
        pretty_abstraction_with_arity(pp, field1177)
        field1178 = unwrapped_fields1174[4]
        if !isnothing(field1178)
            newline(pp)
            opt_val1179 = field1178
            pretty_attrs(pp, opt_val1179)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1187 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1187)
        write(pp, flat1187)
        return nothing
    else
        function _t1744(_dollar_dollar)
            return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        end
        _t1745 = _t1744(msg)
        fields1181 = _t1745
        unwrapped_fields1182 = fields1181
        write(pp, "(")
        write(pp, "functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1183 = unwrapped_fields1182[1]
        pretty_relation_id(pp, field1183)
        newline(pp)
        field1184 = unwrapped_fields1182[2]
        pretty_abstraction(pp, field1184)
        newline(pp)
        field1185 = unwrapped_fields1182[3]
        pretty_functional_dependency_keys(pp, field1185)
        newline(pp)
        field1186 = unwrapped_fields1182[4]
        pretty_functional_dependency_values(pp, field1186)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1192 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1192)
        write(pp, flat1192)
        return nothing
    else
        function _t1746(_dollar_dollar)
            return _dollar_dollar
        end
        _t1747 = _t1746(msg)
        fields1188 = _t1747
        unwrapped_fields1189 = fields1188
        write(pp, "(")
        write(pp, "keys")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1189)
            newline(pp)
            for (i1748, elem1190) in enumerate(unwrapped_fields1189)
                i1191 = i1748 - 1
                if (i1191 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1190)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1197 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1197)
        write(pp, flat1197)
        return nothing
    else
        function _t1749(_dollar_dollar)
            return _dollar_dollar
        end
        _t1750 = _t1749(msg)
        fields1193 = _t1750
        unwrapped_fields1194 = fields1193
        write(pp, "(")
        write(pp, "values")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1194)
            newline(pp)
            for (i1751, elem1195) in enumerate(unwrapped_fields1194)
                i1196 = i1751 - 1
                if (i1196 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1195)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1204 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1204)
        write(pp, flat1204)
        return nothing
    else
        function _t1752(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("rel_edb"))
                _t1753 = _get_oneof_field(_dollar_dollar, :rel_edb)
            else
                _t1753 = nothing
            end
            return _t1753
        end
        _t1754 = _t1752(msg)
        deconstruct_result1202 = _t1754
        if !isnothing(deconstruct_result1202)
            unwrapped1203 = deconstruct_result1202
            pretty_rel_edb(pp, unwrapped1203)
        else
            function _t1755(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                    _t1756 = _get_oneof_field(_dollar_dollar, :betree_relation)
                else
                    _t1756 = nothing
                end
                return _t1756
            end
            _t1757 = _t1755(msg)
            deconstruct_result1200 = _t1757
            if !isnothing(deconstruct_result1200)
                unwrapped1201 = deconstruct_result1200
                pretty_betree_relation(pp, unwrapped1201)
            else
                function _t1758(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                        _t1759 = _get_oneof_field(_dollar_dollar, :csv_data)
                    else
                        _t1759 = nothing
                    end
                    return _t1759
                end
                _t1760 = _t1758(msg)
                deconstruct_result1198 = _t1760
                if !isnothing(deconstruct_result1198)
                    unwrapped1199 = deconstruct_result1198
                    pretty_csv_data(pp, unwrapped1199)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_rel_edb(pp::PrettyPrinter, msg::Proto.RelEDB)
    flat1210 = try_flat(pp, msg, pretty_rel_edb)
    if !isnothing(flat1210)
        write(pp, flat1210)
        return nothing
    else
        function _t1761(_dollar_dollar)
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        end
        _t1762 = _t1761(msg)
        fields1205 = _t1762
        unwrapped_fields1206 = fields1205
        write(pp, "(")
        write(pp, "rel_edb")
        indent_sexp!(pp)
        newline(pp)
        field1207 = unwrapped_fields1206[1]
        pretty_relation_id(pp, field1207)
        newline(pp)
        field1208 = unwrapped_fields1206[2]
        pretty_rel_edb_path(pp, field1208)
        newline(pp)
        field1209 = unwrapped_fields1206[3]
        pretty_rel_edb_types(pp, field1209)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1215 = try_flat(pp, msg, pretty_rel_edb_path)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        function _t1763(_dollar_dollar)
            return _dollar_dollar
        end
        _t1764 = _t1763(msg)
        fields1211 = _t1764
        unwrapped_fields1212 = fields1211
        write(pp, "[")
        indent!(pp)
        for (i1765, elem1213) in enumerate(unwrapped_fields1212)
            i1214 = i1765 - 1
            if (i1214 > 0)
                newline(pp)
            end
            write(pp, format_string_value(elem1213))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_rel_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1220 = try_flat(pp, msg, pretty_rel_edb_types)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        function _t1766(_dollar_dollar)
            return _dollar_dollar
        end
        _t1767 = _t1766(msg)
        fields1216 = _t1767
        unwrapped_fields1217 = fields1216
        write(pp, "[")
        indent!(pp)
        for (i1768, elem1218) in enumerate(unwrapped_fields1217)
            i1219 = i1768 - 1
            if (i1219 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1218)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1225 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1225)
        write(pp, flat1225)
        return nothing
    else
        function _t1769(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        end
        _t1770 = _t1769(msg)
        fields1221 = _t1770
        unwrapped_fields1222 = fields1221
        write(pp, "(")
        write(pp, "betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1223 = unwrapped_fields1222[1]
        pretty_relation_id(pp, field1223)
        newline(pp)
        field1224 = unwrapped_fields1222[2]
        pretty_betree_info(pp, field1224)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1231 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1231)
        write(pp, flat1231)
        return nothing
    else
        function _t1771(_dollar_dollar)
            _t1772 = deconstruct_betree_info_config(pp, _dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1772,)
        end
        _t1773 = _t1771(msg)
        fields1226 = _t1773
        unwrapped_fields1227 = fields1226
        write(pp, "(")
        write(pp, "betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1228 = unwrapped_fields1227[1]
        pretty_betree_info_key_types(pp, field1228)
        newline(pp)
        field1229 = unwrapped_fields1227[2]
        pretty_betree_info_value_types(pp, field1229)
        newline(pp)
        field1230 = unwrapped_fields1227[3]
        pretty_config_dict(pp, field1230)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1236 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1236)
        write(pp, flat1236)
        return nothing
    else
        function _t1774(_dollar_dollar)
            return _dollar_dollar
        end
        _t1775 = _t1774(msg)
        fields1232 = _t1775
        unwrapped_fields1233 = fields1232
        write(pp, "(")
        write(pp, "key_types")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1233)
            newline(pp)
            for (i1776, elem1234) in enumerate(unwrapped_fields1233)
                i1235 = i1776 - 1
                if (i1235 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1234)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1241 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1241)
        write(pp, flat1241)
        return nothing
    else
        function _t1777(_dollar_dollar)
            return _dollar_dollar
        end
        _t1778 = _t1777(msg)
        fields1237 = _t1778
        unwrapped_fields1238 = fields1237
        write(pp, "(")
        write(pp, "value_types")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1238)
            newline(pp)
            for (i1779, elem1239) in enumerate(unwrapped_fields1238)
                i1240 = i1779 - 1
                if (i1240 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1239)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1248 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1248)
        write(pp, flat1248)
        return nothing
    else
        function _t1780(_dollar_dollar)
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        end
        _t1781 = _t1780(msg)
        fields1242 = _t1781
        unwrapped_fields1243 = fields1242
        write(pp, "(")
        write(pp, "csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1244 = unwrapped_fields1243[1]
        pretty_csvlocator(pp, field1244)
        newline(pp)
        field1245 = unwrapped_fields1243[2]
        pretty_csv_config(pp, field1245)
        newline(pp)
        field1246 = unwrapped_fields1243[3]
        pretty_csv_columns(pp, field1246)
        newline(pp)
        field1247 = unwrapped_fields1243[4]
        pretty_csv_asof(pp, field1247)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1255 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1255)
        write(pp, flat1255)
        return nothing
    else
        function _t1782(_dollar_dollar)
            if !isempty(_dollar_dollar.paths)
                _t1783 = _dollar_dollar.paths
            else
                _t1783 = nothing
            end
            if String(copy(_dollar_dollar.inline_data)) != ""
                _t1784 = String(copy(_dollar_dollar.inline_data))
            else
                _t1784 = nothing
            end
            return (_t1783, _t1784,)
        end
        _t1785 = _t1782(msg)
        fields1249 = _t1785
        unwrapped_fields1250 = fields1249
        write(pp, "(")
        write(pp, "csv_locator")
        indent_sexp!(pp)
        field1251 = unwrapped_fields1250[1]
        if !isnothing(field1251)
            newline(pp)
            opt_val1252 = field1251
            pretty_csv_locator_paths(pp, opt_val1252)
        end
        field1253 = unwrapped_fields1250[2]
        if !isnothing(field1253)
            newline(pp)
            opt_val1254 = field1253
            pretty_csv_locator_inline_data(pp, opt_val1254)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1260 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1260)
        write(pp, flat1260)
        return nothing
    else
        function _t1786(_dollar_dollar)
            return _dollar_dollar
        end
        _t1787 = _t1786(msg)
        fields1256 = _t1787
        unwrapped_fields1257 = fields1256
        write(pp, "(")
        write(pp, "paths")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1257)
            newline(pp)
            for (i1788, elem1258) in enumerate(unwrapped_fields1257)
                i1259 = i1788 - 1
                if (i1259 > 0)
                    newline(pp)
                end
                write(pp, format_string_value(elem1258))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1263 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1263)
        write(pp, flat1263)
        return nothing
    else
        function _t1789(_dollar_dollar)
            return _dollar_dollar
        end
        _t1790 = _t1789(msg)
        fields1261 = _t1790
        unwrapped_fields1262 = fields1261
        write(pp, "(")
        write(pp, "inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(unwrapped_fields1262))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1266 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1266)
        write(pp, flat1266)
        return nothing
    else
        function _t1791(_dollar_dollar)
            _t1792 = deconstruct_csv_config(pp, _dollar_dollar)
            return _t1792
        end
        _t1793 = _t1791(msg)
        fields1264 = _t1793
        unwrapped_fields1265 = fields1264
        write(pp, "(")
        write(pp, "csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1265)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.CSVColumn})
    flat1271 = try_flat(pp, msg, pretty_csv_columns)
    if !isnothing(flat1271)
        write(pp, flat1271)
        return nothing
    else
        function _t1794(_dollar_dollar)
            return _dollar_dollar
        end
        _t1795 = _t1794(msg)
        fields1267 = _t1795
        unwrapped_fields1268 = fields1267
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1268)
            newline(pp)
            for (i1796, elem1269) in enumerate(unwrapped_fields1268)
                i1270 = i1796 - 1
                if (i1270 > 0)
                    newline(pp)
                end
                pretty_csv_column(pp, elem1269)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_column(pp::PrettyPrinter, msg::Proto.CSVColumn)
    flat1279 = try_flat(pp, msg, pretty_csv_column)
    if !isnothing(flat1279)
        write(pp, flat1279)
        return nothing
    else
        function _t1797(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        end
        _t1798 = _t1797(msg)
        fields1272 = _t1798
        unwrapped_fields1273 = fields1272
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1274 = unwrapped_fields1273[1]
        write(pp, format_string_value(field1274))
        newline(pp)
        field1275 = unwrapped_fields1273[2]
        pretty_relation_id(pp, field1275)
        newline(pp)
        write(pp, "[")
        field1276 = unwrapped_fields1273[3]
        for (i1799, elem1277) in enumerate(field1276)
            i1278 = i1799 - 1
            if (i1278 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1277)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1282 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1282)
        write(pp, flat1282)
        return nothing
    else
        function _t1800(_dollar_dollar)
            return _dollar_dollar
        end
        _t1801 = _t1800(msg)
        fields1280 = _t1801
        unwrapped_fields1281 = fields1280
        write(pp, "(")
        write(pp, "asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(unwrapped_fields1281))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1285 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1285)
        write(pp, flat1285)
        return nothing
    else
        function _t1802(_dollar_dollar)
            return _dollar_dollar.fragment_id
        end
        _t1803 = _t1802(msg)
        fields1283 = _t1803
        unwrapped_fields1284 = fields1283
        write(pp, "(")
        write(pp, "undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1284)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1290 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1290)
        write(pp, flat1290)
        return nothing
    else
        function _t1804(_dollar_dollar)
            return _dollar_dollar.relations
        end
        _t1805 = _t1804(msg)
        fields1286 = _t1805
        unwrapped_fields1287 = fields1286
        write(pp, "(")
        write(pp, "context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1287)
            newline(pp)
            for (i1806, elem1288) in enumerate(unwrapped_fields1287)
                i1289 = i1806 - 1
                if (i1289 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1288)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1295 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1295)
        write(pp, flat1295)
        return nothing
    else
        function _t1807(_dollar_dollar)
            return _dollar_dollar
        end
        _t1808 = _t1807(msg)
        fields1291 = _t1808
        unwrapped_fields1292 = fields1291
        write(pp, "(")
        write(pp, "reads")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1292)
            newline(pp)
            for (i1809, elem1293) in enumerate(unwrapped_fields1292)
                i1294 = i1809 - 1
                if (i1294 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1293)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1306 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1306)
        write(pp, flat1306)
        return nothing
    else
        function _t1810(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("demand"))
                _t1811 = _get_oneof_field(_dollar_dollar, :demand)
            else
                _t1811 = nothing
            end
            return _t1811
        end
        _t1812 = _t1810(msg)
        deconstruct_result1304 = _t1812
        if !isnothing(deconstruct_result1304)
            unwrapped1305 = deconstruct_result1304
            pretty_demand(pp, unwrapped1305)
        else
            function _t1813(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("output"))
                    _t1814 = _get_oneof_field(_dollar_dollar, :output)
                else
                    _t1814 = nothing
                end
                return _t1814
            end
            _t1815 = _t1813(msg)
            deconstruct_result1302 = _t1815
            if !isnothing(deconstruct_result1302)
                unwrapped1303 = deconstruct_result1302
                pretty_output(pp, unwrapped1303)
            else
                function _t1816(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                        _t1817 = _get_oneof_field(_dollar_dollar, :what_if)
                    else
                        _t1817 = nothing
                    end
                    return _t1817
                end
                _t1818 = _t1816(msg)
                deconstruct_result1300 = _t1818
                if !isnothing(deconstruct_result1300)
                    unwrapped1301 = deconstruct_result1300
                    pretty_what_if(pp, unwrapped1301)
                else
                    function _t1819(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("abort"))
                            _t1820 = _get_oneof_field(_dollar_dollar, :abort)
                        else
                            _t1820 = nothing
                        end
                        return _t1820
                    end
                    _t1821 = _t1819(msg)
                    deconstruct_result1298 = _t1821
                    if !isnothing(deconstruct_result1298)
                        unwrapped1299 = deconstruct_result1298
                        pretty_abort(pp, unwrapped1299)
                    else
                        function _t1822(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("#export"))
                                _t1823 = _get_oneof_field(_dollar_dollar, :var"#export")
                            else
                                _t1823 = nothing
                            end
                            return _t1823
                        end
                        _t1824 = _t1822(msg)
                        deconstruct_result1296 = _t1824
                        if !isnothing(deconstruct_result1296)
                            unwrapped1297 = deconstruct_result1296
                            pretty_export(pp, unwrapped1297)
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
    flat1309 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1309)
        write(pp, flat1309)
        return nothing
    else
        function _t1825(_dollar_dollar)
            return _dollar_dollar.relation_id
        end
        _t1826 = _t1825(msg)
        fields1307 = _t1826
        unwrapped_fields1308 = fields1307
        write(pp, "(")
        write(pp, "demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1308)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1314 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1314)
        write(pp, flat1314)
        return nothing
    else
        function _t1827(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        end
        _t1828 = _t1827(msg)
        fields1310 = _t1828
        unwrapped_fields1311 = fields1310
        write(pp, "(")
        write(pp, "output")
        indent_sexp!(pp)
        newline(pp)
        field1312 = unwrapped_fields1311[1]
        pretty_name(pp, field1312)
        newline(pp)
        field1313 = unwrapped_fields1311[2]
        pretty_relation_id(pp, field1313)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1319 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1319)
        write(pp, flat1319)
        return nothing
    else
        function _t1829(_dollar_dollar)
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        end
        _t1830 = _t1829(msg)
        fields1315 = _t1830
        unwrapped_fields1316 = fields1315
        write(pp, "(")
        write(pp, "what_if")
        indent_sexp!(pp)
        newline(pp)
        field1317 = unwrapped_fields1316[1]
        pretty_name(pp, field1317)
        newline(pp)
        field1318 = unwrapped_fields1316[2]
        pretty_epoch(pp, field1318)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1325 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1325)
        write(pp, flat1325)
        return nothing
    else
        function _t1831(_dollar_dollar)
            if _dollar_dollar.name != "abort"
                _t1832 = _dollar_dollar.name
            else
                _t1832 = nothing
            end
            return (_t1832, _dollar_dollar.relation_id,)
        end
        _t1833 = _t1831(msg)
        fields1320 = _t1833
        unwrapped_fields1321 = fields1320
        write(pp, "(")
        write(pp, "abort")
        indent_sexp!(pp)
        field1322 = unwrapped_fields1321[1]
        if !isnothing(field1322)
            newline(pp)
            opt_val1323 = field1322
            pretty_name(pp, opt_val1323)
        end
        newline(pp)
        field1324 = unwrapped_fields1321[2]
        pretty_relation_id(pp, field1324)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1328 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1328)
        write(pp, flat1328)
        return nothing
    else
        function _t1834(_dollar_dollar)
            return _get_oneof_field(_dollar_dollar, :csv_config)
        end
        _t1835 = _t1834(msg)
        fields1326 = _t1835
        unwrapped_fields1327 = fields1326
        write(pp, "(")
        write(pp, "export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1327)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1334 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1334)
        write(pp, flat1334)
        return nothing
    else
        function _t1836(_dollar_dollar)
            _t1837 = deconstruct_export_csv_config(pp, _dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1837,)
        end
        _t1838 = _t1836(msg)
        fields1329 = _t1838
        unwrapped_fields1330 = fields1329
        write(pp, "(")
        write(pp, "export_csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1331 = unwrapped_fields1330[1]
        pretty_export_csv_path(pp, field1331)
        newline(pp)
        field1332 = unwrapped_fields1330[2]
        pretty_export_csv_columns(pp, field1332)
        newline(pp)
        field1333 = unwrapped_fields1330[3]
        pretty_config_dict(pp, field1333)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1337 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1337)
        write(pp, flat1337)
        return nothing
    else
        function _t1839(_dollar_dollar)
            return _dollar_dollar
        end
        _t1840 = _t1839(msg)
        fields1335 = _t1840
        unwrapped_fields1336 = fields1335
        write(pp, "(")
        write(pp, "path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string_value(unwrapped_fields1336))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1342 = try_flat(pp, msg, pretty_export_csv_columns)
    if !isnothing(flat1342)
        write(pp, flat1342)
        return nothing
    else
        function _t1841(_dollar_dollar)
            return _dollar_dollar
        end
        _t1842 = _t1841(msg)
        fields1338 = _t1842
        unwrapped_fields1339 = fields1338
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1339)
            newline(pp)
            for (i1843, elem1340) in enumerate(unwrapped_fields1339)
                i1341 = i1843 - 1
                if (i1341 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1340)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_column(pp::PrettyPrinter, msg::Proto.ExportCSVColumn)
    flat1347 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1347)
        write(pp, flat1347)
        return nothing
    else
        function _t1844(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        end
        _t1845 = _t1844(msg)
        fields1343 = _t1845
        unwrapped_fields1344 = fields1343
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1345 = unwrapped_fields1344[1]
        write(pp, format_string_value(field1345))
        newline(pp)
        field1346 = unwrapped_fields1344[2]
        pretty_relation_id(pp, field1346)
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
