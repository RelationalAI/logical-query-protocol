"""
    Pretty

Auto-generated pretty printer module.

Generated from protobuf specifications.
# Do not modify this file! If you need to modify the pretty printer, edit the generator code
in `meta/` or edit the protobuf specification in `proto/v1`.

Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer julia
"""
module Pretty

using ProtoBuf: OneOf

# Import protobuf modules and helpers from parent
using ..relationalai: relationalai
using ..relationalai.lqp.v1
using ..LogicalQueryProtocol: LQPSyntax, LQPFragmentId, _has_proto_field, _get_oneof_field
using ..Parser: ParseError
const Proto = relationalai.lqp.v1

"""
    ConstantFormatter

Abstract type for customizing how constants are formatted in the pretty printer.

Users can define subtypes of `ConstantFormatter` and override format functions
(like `format_decimal`, `format_int128`, `format_uint128`) to customize how
constants are displayed.

See `DefaultConstantFormatter` for the default implementation.
"""
abstract type ConstantFormatter end

"""
    DefaultConstantFormatter <: ConstantFormatter

Default constant formatter that produces standard formatting for all constants.
"""
struct DefaultConstantFormatter <: ConstantFormatter end

"""
    DEFAULT_CONSTANT_FORMATTER

Singleton instance of DefaultConstantFormatter.
"""
const DEFAULT_CONSTANT_FORMATTER = DefaultConstantFormatter()

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
    print_symbolic_relation_ids::Bool
    debug_info::Dict{Tuple{UInt64,UInt64},String}
    constant_formatter::ConstantFormatter
end

function PrettyPrinter(; max_width::Int=92, print_symbolic_relation_ids::Bool=true, constant_formatter::ConstantFormatter=DEFAULT_CONSTANT_FORMATTER)
    return PrettyPrinter(
        IOBuffer(), [0], 0, true, "\n", max_width,
        Set{UInt}(), Dict{UInt,String}(), Any[],
        print_symbolic_relation_ids,
        Dict{Tuple{UInt64,UInt64},String}(),
        constant_formatter,
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

"""
    format_decimal(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.DecimalValue)::String

Format a DecimalValue as a string.

Override this function for custom ConstantFormatter subtypes to customize decimal formatting.
"""
function format_decimal(formatter::DefaultConstantFormatter, pp::PrettyPrinter, msg::Proto.DecimalValue)::String
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

"""
    format_int128(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.Int128Value)::String

Format an Int128Value as a string.

Override this function for custom ConstantFormatter subtypes to customize int128 formatting.
"""
function format_int128(formatter::DefaultConstantFormatter, pp::PrettyPrinter, msg::Proto.Int128Value)::String
    value = Int128(msg.high) << 64 | Int128(msg.low)
    if msg.high & (UInt64(1) << 63) != 0
        value -= Int128(1) << 128
    end
    return string(value) * "i128"
end

"""
    format_uint128(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.UInt128Value)::String

Format a UInt128Value as a string.

Override this function for custom ConstantFormatter subtypes to customize uint128 formatting.
"""
function format_uint128(formatter::DefaultConstantFormatter, pp::PrettyPrinter, msg::Proto.UInt128Value)::String
    value = UInt128(msg.high) << 64 | UInt128(msg.low)
    return "0x" * string(value, base=16)
end

"""
    format_int(formatter::ConstantFormatter, pp::PrettyPrinter, v::Int64)::String

Format an integer value as a string.

Override this function for custom ConstantFormatter subtypes to customize integer formatting.
"""
format_int(formatter::DefaultConstantFormatter, pp::PrettyPrinter, v::Int64)::String = string(v)

"""
    format_float(formatter::ConstantFormatter, pp::PrettyPrinter, v::Float64)::String

Format a Float64 value as a string.

Override this function for custom ConstantFormatter subtypes to customize float formatting.
"""
format_float(formatter::DefaultConstantFormatter, pp::PrettyPrinter, v::Float64)::String = lowercase(string(v))

"""
    format_string(formatter::ConstantFormatter, pp::PrettyPrinter, s::AbstractString)::String

Format a string value with proper escaping.

Override this function for custom ConstantFormatter subtypes to customize string formatting.
"""
function format_string(formatter::DefaultConstantFormatter, pp::PrettyPrinter, s::AbstractString)::String
    escaped = replace(s, "\\" => "\\\\")
    escaped = replace(escaped, "\"" => "\\\"")
    escaped = replace(escaped, "\n" => "\\n")
    escaped = replace(escaped, "\r" => "\\r")
    escaped = replace(escaped, "\t" => "\\t")
    return "\"" * escaped * "\""
end

"""
    format_bool(formatter::ConstantFormatter, pp::PrettyPrinter, v::Bool)::String

Format a boolean value as a string.

Override this function for custom ConstantFormatter subtypes to customize boolean formatting.
"""
format_bool(formatter::DefaultConstantFormatter, pp::PrettyPrinter, v::Bool)::String = v ? "true" : "false"

# Fallback methods for custom formatters that don't override all types
# These delegate to the default formatter
format_decimal(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.DecimalValue)::String = format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, msg)
format_int128(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.Int128Value)::String = format_int128(DEFAULT_CONSTANT_FORMATTER, pp, msg)
format_uint128(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.UInt128Value)::String = format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, msg)
format_int(formatter::ConstantFormatter, pp::PrettyPrinter, v::Int64)::String = format_int(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_float(formatter::ConstantFormatter, pp::PrettyPrinter, v::Float64)::String = format_float(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_string(formatter::ConstantFormatter, pp::PrettyPrinter, s::AbstractString)::String = format_string(DEFAULT_CONSTANT_FORMATTER, pp, s)
format_bool(formatter::ConstantFormatter, pp::PrettyPrinter, v::Bool)::String = format_bool(DEFAULT_CONSTANT_FORMATTER, pp, v)

# Backward compatibility: convenience methods that use pp.constant_formatter
format_decimal(pp::PrettyPrinter, msg::Proto.DecimalValue)::String = format_decimal(pp.constant_formatter, pp, msg)
format_int128(pp::PrettyPrinter, msg::Proto.Int128Value)::String = format_int128(pp.constant_formatter, pp, msg)
format_uint128(pp::PrettyPrinter, msg::Proto.UInt128Value)::String = format_uint128(pp.constant_formatter, pp, msg)
format_int(pp::PrettyPrinter, v::Int64)::String = format_int(pp.constant_formatter, pp, v)
format_float(pp::PrettyPrinter, v::Float64)::String = format_float(pp.constant_formatter, pp, v)
format_string(pp::PrettyPrinter, s::AbstractString)::String = format_string(pp.constant_formatter, pp, s)
format_bool(pp::PrettyPrinter, v::Bool)::String = format_bool(pp.constant_formatter, pp, v)

# Legacy function names for backward compatibility
format_float64(v::Float64)::String = lowercase(string(v))
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

function relation_id_to_string(pp::PrettyPrinter, msg::Proto.RelationId)::Union{String,Nothing}
    !pp.print_symbolic_relation_ids && return nothing
    return get(pp.debug_info, (msg.id_low, msg.id_high), nothing)
end

function relation_id_to_uint128(pp::PrettyPrinter, msg::Proto.RelationId)
    return Proto.UInt128Value(msg.id_low, msg.id_high)
end

function write_debug_info(pp::PrettyPrinter)::Nothing
    isempty(pp.debug_info) && return nothing
    Base.write(pp.io, "\n;; Debug information\n")
    Base.write(pp.io, ";; -----------------------\n")
    Base.write(pp.io, ";; Original names\n")
    for ((id_low, id_high), name) in sort(collect(pp.debug_info); by=x -> x[2])
        value = UInt128(id_high) << 64 | UInt128(id_low)
        Base.write(pp.io, ";; \t ID `0x" * string(value, base=16) * "` -> `" * name * "`\n")
    end
    return nothing
end

# --- Helper functions ---

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1710 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1710
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1711 = Proto.Value(value=OneOf(:int_value, v))
    return _t1711
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1712 = Proto.Value(value=OneOf(:float_value, v))
    return _t1712
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1713 = Proto.Value(value=OneOf(:string_value, v))
    return _t1713
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1714 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1714
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1715 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1715
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1716 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1716,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1717 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1717,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1718 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1718,))
            end
        end
    end
    _t1719 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1719,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1720 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1720,))
    _t1721 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1721,))
    if msg.new_line != ""
        _t1722 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1722,))
    end
    _t1723 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1723,))
    _t1724 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1724,))
    _t1725 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1725,))
    if msg.comment != ""
        _t1726 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1726,))
    end
    for missing_string in msg.missing_strings
        _t1727 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1727,))
    end
    _t1728 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1728,))
    _t1729 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1729,))
    _t1730 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1730,))
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1731 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1731,))
    _t1732 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1732,))
    _t1733 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1733,))
    _t1734 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1734,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1735 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1735,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1736 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1736,))
        end
    end
    _t1737 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1737,))
    _t1738 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1738,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1739 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1739,))
    end
    if !isnothing(msg.compression)
        _t1740 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1740,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1741 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1741,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1742 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1742,))
    end
    if !isnothing(msg.syntax_delim)
        _t1743 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1743,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1744 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1744,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1745 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1745,))
    end
    return sort(result)
end

function deconstruct_relation_id_string(pp::PrettyPrinter, msg::Proto.RelationId)::String
    name = relation_id_to_string(pp, msg)
    return name
end

function deconstruct_relation_id_uint128(pp::PrettyPrinter, msg::Proto.RelationId)::Union{Nothing, Proto.UInt128Value}
    name = relation_id_to_string(pp, msg)
    if isnothing(name)
        return relation_id_to_uint128(pp, msg)
    else
        _t1746 = nothing
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
    flat646 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat646)
        write(pp, flat646)
        return nothing
    else
        function _t1274(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("configure"))
                _t1275 = _dollar_dollar.configure
            else
                _t1275 = nothing
            end
            if _has_proto_field(_dollar_dollar, Symbol("sync"))
                _t1276 = _dollar_dollar.sync
            else
                _t1276 = nothing
            end
            return (_t1275, _t1276, _dollar_dollar.epochs,)
        end
        _t1277 = _t1274(msg)
        fields637 = _t1277
        unwrapped_fields638 = fields637
        write(pp, "(")
        write(pp, "transaction")
        indent_sexp!(pp)
        field639 = unwrapped_fields638[1]
        if !isnothing(field639)
            newline(pp)
            opt_val640 = field639
            pretty_configure(pp, opt_val640)
        end
        field641 = unwrapped_fields638[2]
        if !isnothing(field641)
            newline(pp)
            opt_val642 = field641
            pretty_sync(pp, opt_val642)
        end
        field643 = unwrapped_fields638[3]
        if !isempty(field643)
            newline(pp)
            for (i1278, elem644) in enumerate(field643)
                i645 = i1278 - 1
                if (i645 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem644)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat649 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat649)
        write(pp, flat649)
        return nothing
    else
        function _t1279(_dollar_dollar)
            _t1280 = deconstruct_configure(pp, _dollar_dollar)
            return _t1280
        end
        _t1281 = _t1279(msg)
        fields647 = _t1281
        unwrapped_fields648 = fields647
        write(pp, "(")
        write(pp, "configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields648)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat653 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat653)
        write(pp, flat653)
        return nothing
    else
        fields650 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields650)
            newline(pp)
            for (i1282, elem651) in enumerate(fields650)
                i652 = i1282 - 1
                if (i652 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem651)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat658 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat658)
        write(pp, flat658)
        return nothing
    else
        function _t1283(_dollar_dollar)
            return (_dollar_dollar[1], _dollar_dollar[2],)
        end
        _t1284 = _t1283(msg)
        fields654 = _t1284
        unwrapped_fields655 = fields654
        write(pp, ":")
        field656 = unwrapped_fields655[1]
        write(pp, field656)
        write(pp, " ")
        field657 = unwrapped_fields655[2]
        pretty_value(pp, field657)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat678 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat678)
        write(pp, flat678)
        return nothing
    else
        function _t1285(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("date_value"))
                _t1286 = _get_oneof_field(_dollar_dollar, :date_value)
            else
                _t1286 = nothing
            end
            return _t1286
        end
        _t1287 = _t1285(msg)
        deconstruct_result676 = _t1287
        if !isnothing(deconstruct_result676)
            unwrapped677 = deconstruct_result676
            pretty_date(pp, unwrapped677)
        else
            function _t1288(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                    _t1289 = _get_oneof_field(_dollar_dollar, :datetime_value)
                else
                    _t1289 = nothing
                end
                return _t1289
            end
            _t1290 = _t1288(msg)
            deconstruct_result674 = _t1290
            if !isnothing(deconstruct_result674)
                unwrapped675 = deconstruct_result674
                pretty_datetime(pp, unwrapped675)
            else
                function _t1291(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                        _t1292 = _get_oneof_field(_dollar_dollar, :string_value)
                    else
                        _t1292 = nothing
                    end
                    return _t1292
                end
                _t1293 = _t1291(msg)
                deconstruct_result672 = _t1293
                if !isnothing(deconstruct_result672)
                    unwrapped673 = deconstruct_result672
                    write(pp, format_string(pp, unwrapped673))
                else
                    function _t1294(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1295 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1295 = nothing
                        end
                        return _t1295
                    end
                    _t1296 = _t1294(msg)
                    deconstruct_result670 = _t1296
                    if !isnothing(deconstruct_result670)
                        unwrapped671 = deconstruct_result670
                        write(pp, format_int(pp, unwrapped671))
                    else
                        function _t1297(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                _t1298 = _get_oneof_field(_dollar_dollar, :float_value)
                            else
                                _t1298 = nothing
                            end
                            return _t1298
                        end
                        _t1299 = _t1297(msg)
                        deconstruct_result668 = _t1299
                        if !isnothing(deconstruct_result668)
                            unwrapped669 = deconstruct_result668
                            write(pp, format_float(pp, unwrapped669))
                        else
                            function _t1300(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                    _t1301 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                else
                                    _t1301 = nothing
                                end
                                return _t1301
                            end
                            _t1302 = _t1300(msg)
                            deconstruct_result666 = _t1302
                            if !isnothing(deconstruct_result666)
                                unwrapped667 = deconstruct_result666
                                write(pp, format_uint128(pp, unwrapped667))
                            else
                                function _t1303(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                        _t1304 = _get_oneof_field(_dollar_dollar, :int128_value)
                                    else
                                        _t1304 = nothing
                                    end
                                    return _t1304
                                end
                                _t1305 = _t1303(msg)
                                deconstruct_result664 = _t1305
                                if !isnothing(deconstruct_result664)
                                    unwrapped665 = deconstruct_result664
                                    write(pp, format_int128(pp, unwrapped665))
                                else
                                    function _t1306(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                            _t1307 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                        else
                                            _t1307 = nothing
                                        end
                                        return _t1307
                                    end
                                    _t1308 = _t1306(msg)
                                    deconstruct_result662 = _t1308
                                    if !isnothing(deconstruct_result662)
                                        unwrapped663 = deconstruct_result662
                                        write(pp, format_decimal(pp, unwrapped663))
                                    else
                                        function _t1309(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                _t1310 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                            else
                                                _t1310 = nothing
                                            end
                                            return _t1310
                                        end
                                        _t1311 = _t1309(msg)
                                        deconstruct_result660 = _t1311
                                        if !isnothing(deconstruct_result660)
                                            unwrapped661 = deconstruct_result660
                                            pretty_boolean_value(pp, unwrapped661)
                                        else
                                            fields659 = msg
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
    flat684 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat684)
        write(pp, flat684)
        return nothing
    else
        function _t1312(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        end
        _t1313 = _t1312(msg)
        fields679 = _t1313
        unwrapped_fields680 = fields679
        write(pp, "(")
        write(pp, "date")
        indent_sexp!(pp)
        newline(pp)
        field681 = unwrapped_fields680[1]
        write(pp, format_int(pp, field681))
        newline(pp)
        field682 = unwrapped_fields680[2]
        write(pp, format_int(pp, field682))
        newline(pp)
        field683 = unwrapped_fields680[3]
        write(pp, format_int(pp, field683))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat695 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat695)
        write(pp, flat695)
        return nothing
    else
        function _t1314(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        end
        _t1315 = _t1314(msg)
        fields685 = _t1315
        unwrapped_fields686 = fields685
        write(pp, "(")
        write(pp, "datetime")
        indent_sexp!(pp)
        newline(pp)
        field687 = unwrapped_fields686[1]
        write(pp, format_int(pp, field687))
        newline(pp)
        field688 = unwrapped_fields686[2]
        write(pp, format_int(pp, field688))
        newline(pp)
        field689 = unwrapped_fields686[3]
        write(pp, format_int(pp, field689))
        newline(pp)
        field690 = unwrapped_fields686[4]
        write(pp, format_int(pp, field690))
        newline(pp)
        field691 = unwrapped_fields686[5]
        write(pp, format_int(pp, field691))
        newline(pp)
        field692 = unwrapped_fields686[6]
        write(pp, format_int(pp, field692))
        field693 = unwrapped_fields686[7]
        if !isnothing(field693)
            newline(pp)
            opt_val694 = field693
            write(pp, format_int(pp, opt_val694))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    function _t1316(_dollar_dollar)
        if _dollar_dollar
            _t1317 = ()
        else
            _t1317 = nothing
        end
        return _t1317
    end
    _t1318 = _t1316(msg)
    deconstruct_result698 = _t1318
    if !isnothing(deconstruct_result698)
        unwrapped699 = deconstruct_result698
        write(pp, "true")
    else
        function _t1319(_dollar_dollar)
            if !_dollar_dollar
                _t1320 = ()
            else
                _t1320 = nothing
            end
            return _t1320
        end
        _t1321 = _t1319(msg)
        deconstruct_result696 = _t1321
        if !isnothing(deconstruct_result696)
            unwrapped697 = deconstruct_result696
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat704 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat704)
        write(pp, flat704)
        return nothing
    else
        function _t1322(_dollar_dollar)
            return _dollar_dollar.fragments
        end
        _t1323 = _t1322(msg)
        fields700 = _t1323
        unwrapped_fields701 = fields700
        write(pp, "(")
        write(pp, "sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields701)
            newline(pp)
            for (i1324, elem702) in enumerate(unwrapped_fields701)
                i703 = i1324 - 1
                if (i703 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem702)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat707 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat707)
        write(pp, flat707)
        return nothing
    else
        function _t1325(_dollar_dollar)
            return fragment_id_to_string(pp, _dollar_dollar)
        end
        _t1326 = _t1325(msg)
        fields705 = _t1326
        unwrapped_fields706 = fields705
        write(pp, ":")
        write(pp, unwrapped_fields706)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat714 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat714)
        write(pp, flat714)
        return nothing
    else
        function _t1327(_dollar_dollar)
            if !isempty(_dollar_dollar.writes)
                _t1328 = _dollar_dollar.writes
            else
                _t1328 = nothing
            end
            if !isempty(_dollar_dollar.reads)
                _t1329 = _dollar_dollar.reads
            else
                _t1329 = nothing
            end
            return (_t1328, _t1329,)
        end
        _t1330 = _t1327(msg)
        fields708 = _t1330
        unwrapped_fields709 = fields708
        write(pp, "(")
        write(pp, "epoch")
        indent_sexp!(pp)
        field710 = unwrapped_fields709[1]
        if !isnothing(field710)
            newline(pp)
            opt_val711 = field710
            pretty_epoch_writes(pp, opt_val711)
        end
        field712 = unwrapped_fields709[2]
        if !isnothing(field712)
            newline(pp)
            opt_val713 = field712
            pretty_epoch_reads(pp, opt_val713)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat718 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat718)
        write(pp, flat718)
        return nothing
    else
        fields715 = msg
        write(pp, "(")
        write(pp, "writes")
        indent_sexp!(pp)
        if !isempty(fields715)
            newline(pp)
            for (i1331, elem716) in enumerate(fields715)
                i717 = i1331 - 1
                if (i717 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem716)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat727 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat727)
        write(pp, flat727)
        return nothing
    else
        function _t1332(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("define"))
                _t1333 = _get_oneof_field(_dollar_dollar, :define)
            else
                _t1333 = nothing
            end
            return _t1333
        end
        _t1334 = _t1332(msg)
        deconstruct_result725 = _t1334
        if !isnothing(deconstruct_result725)
            unwrapped726 = deconstruct_result725
            pretty_define(pp, unwrapped726)
        else
            function _t1335(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                    _t1336 = _get_oneof_field(_dollar_dollar, :undefine)
                else
                    _t1336 = nothing
                end
                return _t1336
            end
            _t1337 = _t1335(msg)
            deconstruct_result723 = _t1337
            if !isnothing(deconstruct_result723)
                unwrapped724 = deconstruct_result723
                pretty_undefine(pp, unwrapped724)
            else
                function _t1338(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("context"))
                        _t1339 = _get_oneof_field(_dollar_dollar, :context)
                    else
                        _t1339 = nothing
                    end
                    return _t1339
                end
                _t1340 = _t1338(msg)
                deconstruct_result721 = _t1340
                if !isnothing(deconstruct_result721)
                    unwrapped722 = deconstruct_result721
                    pretty_context(pp, unwrapped722)
                else
                    function _t1341(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                            _t1342 = _get_oneof_field(_dollar_dollar, :snapshot)
                        else
                            _t1342 = nothing
                        end
                        return _t1342
                    end
                    _t1343 = _t1341(msg)
                    deconstruct_result719 = _t1343
                    if !isnothing(deconstruct_result719)
                        unwrapped720 = deconstruct_result719
                        pretty_snapshot(pp, unwrapped720)
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
    flat730 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat730)
        write(pp, flat730)
        return nothing
    else
        function _t1344(_dollar_dollar)
            return _dollar_dollar.fragment
        end
        _t1345 = _t1344(msg)
        fields728 = _t1345
        unwrapped_fields729 = fields728
        write(pp, "(")
        write(pp, "define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields729)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat737 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat737)
        write(pp, flat737)
        return nothing
    else
        function _t1346(_dollar_dollar)
            start_pretty_fragment(pp, _dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        end
        _t1347 = _t1346(msg)
        fields731 = _t1347
        unwrapped_fields732 = fields731
        write(pp, "(")
        write(pp, "fragment")
        indent_sexp!(pp)
        newline(pp)
        field733 = unwrapped_fields732[1]
        pretty_new_fragment_id(pp, field733)
        field734 = unwrapped_fields732[2]
        if !isempty(field734)
            newline(pp)
            for (i1348, elem735) in enumerate(field734)
                i736 = i1348 - 1
                if (i736 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem735)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat739 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat739)
        write(pp, flat739)
        return nothing
    else
        fields738 = msg
        pretty_fragment_id(pp, fields738)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat748 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat748)
        write(pp, flat748)
        return nothing
    else
        function _t1349(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("def"))
                _t1350 = _get_oneof_field(_dollar_dollar, :def)
            else
                _t1350 = nothing
            end
            return _t1350
        end
        _t1351 = _t1349(msg)
        deconstruct_result746 = _t1351
        if !isnothing(deconstruct_result746)
            unwrapped747 = deconstruct_result746
            pretty_def(pp, unwrapped747)
        else
            function _t1352(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                    _t1353 = _get_oneof_field(_dollar_dollar, :algorithm)
                else
                    _t1353 = nothing
                end
                return _t1353
            end
            _t1354 = _t1352(msg)
            deconstruct_result744 = _t1354
            if !isnothing(deconstruct_result744)
                unwrapped745 = deconstruct_result744
                pretty_algorithm(pp, unwrapped745)
            else
                function _t1355(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                        _t1356 = _get_oneof_field(_dollar_dollar, :constraint)
                    else
                        _t1356 = nothing
                    end
                    return _t1356
                end
                _t1357 = _t1355(msg)
                deconstruct_result742 = _t1357
                if !isnothing(deconstruct_result742)
                    unwrapped743 = deconstruct_result742
                    pretty_constraint(pp, unwrapped743)
                else
                    function _t1358(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("data"))
                            _t1359 = _get_oneof_field(_dollar_dollar, :data)
                        else
                            _t1359 = nothing
                        end
                        return _t1359
                    end
                    _t1360 = _t1358(msg)
                    deconstruct_result740 = _t1360
                    if !isnothing(deconstruct_result740)
                        unwrapped741 = deconstruct_result740
                        pretty_data(pp, unwrapped741)
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
    flat755 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat755)
        write(pp, flat755)
        return nothing
    else
        function _t1361(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1362 = _dollar_dollar.attrs
            else
                _t1362 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1362,)
        end
        _t1363 = _t1361(msg)
        fields749 = _t1363
        unwrapped_fields750 = fields749
        write(pp, "(")
        write(pp, "def")
        indent_sexp!(pp)
        newline(pp)
        field751 = unwrapped_fields750[1]
        pretty_relation_id(pp, field751)
        newline(pp)
        field752 = unwrapped_fields750[2]
        pretty_abstraction(pp, field752)
        field753 = unwrapped_fields750[3]
        if !isnothing(field753)
            newline(pp)
            opt_val754 = field753
            pretty_attrs(pp, opt_val754)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat760 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat760)
        write(pp, flat760)
        return nothing
    else
        function _t1364(_dollar_dollar)
            if !isnothing(relation_id_to_string(pp, _dollar_dollar))
                _t1366 = deconstruct_relation_id_string(pp, _dollar_dollar)
                _t1365 = _t1366
            else
                _t1365 = nothing
            end
            return _t1365
        end
        _t1367 = _t1364(msg)
        deconstruct_result758 = _t1367
        if !isnothing(deconstruct_result758)
            unwrapped759 = deconstruct_result758
            write(pp, ":")
            write(pp, unwrapped759)
        else
            function _t1368(_dollar_dollar)
                _t1369 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
                return _t1369
            end
            _t1370 = _t1368(msg)
            deconstruct_result756 = _t1370
            if !isnothing(deconstruct_result756)
                unwrapped757 = deconstruct_result756
                write(pp, format_uint128(pp, unwrapped757))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat765 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat765)
        write(pp, flat765)
        return nothing
    else
        function _t1371(_dollar_dollar)
            _t1372 = deconstruct_bindings(pp, _dollar_dollar)
            return (_t1372, _dollar_dollar.value,)
        end
        _t1373 = _t1371(msg)
        fields761 = _t1373
        unwrapped_fields762 = fields761
        write(pp, "(")
        indent!(pp)
        field763 = unwrapped_fields762[1]
        pretty_bindings(pp, field763)
        newline(pp)
        field764 = unwrapped_fields762[2]
        pretty_formula(pp, field764)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat773 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat773)
        write(pp, flat773)
        return nothing
    else
        function _t1374(_dollar_dollar)
            if !isempty(_dollar_dollar[2])
                _t1375 = _dollar_dollar[2]
            else
                _t1375 = nothing
            end
            return (_dollar_dollar[1], _t1375,)
        end
        _t1376 = _t1374(msg)
        fields766 = _t1376
        unwrapped_fields767 = fields766
        write(pp, "[")
        indent!(pp)
        field768 = unwrapped_fields767[1]
        for (i1377, elem769) in enumerate(field768)
            i770 = i1377 - 1
            if (i770 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem769)
        end
        field771 = unwrapped_fields767[2]
        if !isnothing(field771)
            newline(pp)
            opt_val772 = field771
            pretty_value_bindings(pp, opt_val772)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat778 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat778)
        write(pp, flat778)
        return nothing
    else
        function _t1378(_dollar_dollar)
            return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        end
        _t1379 = _t1378(msg)
        fields774 = _t1379
        unwrapped_fields775 = fields774
        field776 = unwrapped_fields775[1]
        write(pp, field776)
        write(pp, "::")
        field777 = unwrapped_fields775[2]
        pretty_type(pp, field777)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat801 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat801)
        write(pp, flat801)
        return nothing
    else
        function _t1380(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
                _t1381 = _get_oneof_field(_dollar_dollar, :unspecified_type)
            else
                _t1381 = nothing
            end
            return _t1381
        end
        _t1382 = _t1380(msg)
        deconstruct_result799 = _t1382
        if !isnothing(deconstruct_result799)
            unwrapped800 = deconstruct_result799
            pretty_unspecified_type(pp, unwrapped800)
        else
            function _t1383(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                    _t1384 = _get_oneof_field(_dollar_dollar, :string_type)
                else
                    _t1384 = nothing
                end
                return _t1384
            end
            _t1385 = _t1383(msg)
            deconstruct_result797 = _t1385
            if !isnothing(deconstruct_result797)
                unwrapped798 = deconstruct_result797
                pretty_string_type(pp, unwrapped798)
            else
                function _t1386(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                        _t1387 = _get_oneof_field(_dollar_dollar, :int_type)
                    else
                        _t1387 = nothing
                    end
                    return _t1387
                end
                _t1388 = _t1386(msg)
                deconstruct_result795 = _t1388
                if !isnothing(deconstruct_result795)
                    unwrapped796 = deconstruct_result795
                    pretty_int_type(pp, unwrapped796)
                else
                    function _t1389(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                            _t1390 = _get_oneof_field(_dollar_dollar, :float_type)
                        else
                            _t1390 = nothing
                        end
                        return _t1390
                    end
                    _t1391 = _t1389(msg)
                    deconstruct_result793 = _t1391
                    if !isnothing(deconstruct_result793)
                        unwrapped794 = deconstruct_result793
                        pretty_float_type(pp, unwrapped794)
                    else
                        function _t1392(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                                _t1393 = _get_oneof_field(_dollar_dollar, :uint128_type)
                            else
                                _t1393 = nothing
                            end
                            return _t1393
                        end
                        _t1394 = _t1392(msg)
                        deconstruct_result791 = _t1394
                        if !isnothing(deconstruct_result791)
                            unwrapped792 = deconstruct_result791
                            pretty_uint128_type(pp, unwrapped792)
                        else
                            function _t1395(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                    _t1396 = _get_oneof_field(_dollar_dollar, :int128_type)
                                else
                                    _t1396 = nothing
                                end
                                return _t1396
                            end
                            _t1397 = _t1395(msg)
                            deconstruct_result789 = _t1397
                            if !isnothing(deconstruct_result789)
                                unwrapped790 = deconstruct_result789
                                pretty_int128_type(pp, unwrapped790)
                            else
                                function _t1398(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                        _t1399 = _get_oneof_field(_dollar_dollar, :date_type)
                                    else
                                        _t1399 = nothing
                                    end
                                    return _t1399
                                end
                                _t1400 = _t1398(msg)
                                deconstruct_result787 = _t1400
                                if !isnothing(deconstruct_result787)
                                    unwrapped788 = deconstruct_result787
                                    pretty_date_type(pp, unwrapped788)
                                else
                                    function _t1401(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                            _t1402 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                        else
                                            _t1402 = nothing
                                        end
                                        return _t1402
                                    end
                                    _t1403 = _t1401(msg)
                                    deconstruct_result785 = _t1403
                                    if !isnothing(deconstruct_result785)
                                        unwrapped786 = deconstruct_result785
                                        pretty_datetime_type(pp, unwrapped786)
                                    else
                                        function _t1404(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                                _t1405 = _get_oneof_field(_dollar_dollar, :missing_type)
                                            else
                                                _t1405 = nothing
                                            end
                                            return _t1405
                                        end
                                        _t1406 = _t1404(msg)
                                        deconstruct_result783 = _t1406
                                        if !isnothing(deconstruct_result783)
                                            unwrapped784 = deconstruct_result783
                                            pretty_missing_type(pp, unwrapped784)
                                        else
                                            function _t1407(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                    _t1408 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                                else
                                                    _t1408 = nothing
                                                end
                                                return _t1408
                                            end
                                            _t1409 = _t1407(msg)
                                            deconstruct_result781 = _t1409
                                            if !isnothing(deconstruct_result781)
                                                unwrapped782 = deconstruct_result781
                                                pretty_decimal_type(pp, unwrapped782)
                                            else
                                                function _t1410(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                        _t1411 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                    else
                                                        _t1411 = nothing
                                                    end
                                                    return _t1411
                                                end
                                                _t1412 = _t1410(msg)
                                                deconstruct_result779 = _t1412
                                                if !isnothing(deconstruct_result779)
                                                    unwrapped780 = deconstruct_result779
                                                    pretty_boolean_type(pp, unwrapped780)
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
    fields802 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields803 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields804 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields805 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields806 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields807 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields808 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields809 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields810 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat815 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat815)
        write(pp, flat815)
        return nothing
    else
        function _t1413(_dollar_dollar)
            return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        end
        _t1414 = _t1413(msg)
        fields811 = _t1414
        unwrapped_fields812 = fields811
        write(pp, "(")
        write(pp, "DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field813 = unwrapped_fields812[1]
        write(pp, format_int(pp, field813))
        newline(pp)
        field814 = unwrapped_fields812[2]
        write(pp, format_int(pp, field814))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields816 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat820 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat820)
        write(pp, flat820)
        return nothing
    else
        fields817 = msg
        write(pp, "|")
        if !isempty(fields817)
            write(pp, " ")
            for (i1415, elem818) in enumerate(fields817)
                i819 = i1415 - 1
                if (i819 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem818)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat847 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat847)
        write(pp, flat847)
        return nothing
    else
        function _t1416(_dollar_dollar)
            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                _t1417 = _get_oneof_field(_dollar_dollar, :conjunction)
            else
                _t1417 = nothing
            end
            return _t1417
        end
        _t1418 = _t1416(msg)
        deconstruct_result845 = _t1418
        if !isnothing(deconstruct_result845)
            unwrapped846 = deconstruct_result845
            pretty_true(pp, unwrapped846)
        else
            function _t1419(_dollar_dollar)
                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                    _t1420 = _get_oneof_field(_dollar_dollar, :disjunction)
                else
                    _t1420 = nothing
                end
                return _t1420
            end
            _t1421 = _t1419(msg)
            deconstruct_result843 = _t1421
            if !isnothing(deconstruct_result843)
                unwrapped844 = deconstruct_result843
                pretty_false(pp, unwrapped844)
            else
                function _t1422(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("exists"))
                        _t1423 = _get_oneof_field(_dollar_dollar, :exists)
                    else
                        _t1423 = nothing
                    end
                    return _t1423
                end
                _t1424 = _t1422(msg)
                deconstruct_result841 = _t1424
                if !isnothing(deconstruct_result841)
                    unwrapped842 = deconstruct_result841
                    pretty_exists(pp, unwrapped842)
                else
                    function _t1425(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                            _t1426 = _get_oneof_field(_dollar_dollar, :reduce)
                        else
                            _t1426 = nothing
                        end
                        return _t1426
                    end
                    _t1427 = _t1425(msg)
                    deconstruct_result839 = _t1427
                    if !isnothing(deconstruct_result839)
                        unwrapped840 = deconstruct_result839
                        pretty_reduce(pp, unwrapped840)
                    else
                        function _t1428(_dollar_dollar)
                            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                                _t1429 = _get_oneof_field(_dollar_dollar, :conjunction)
                            else
                                _t1429 = nothing
                            end
                            return _t1429
                        end
                        _t1430 = _t1428(msg)
                        deconstruct_result837 = _t1430
                        if !isnothing(deconstruct_result837)
                            unwrapped838 = deconstruct_result837
                            pretty_conjunction(pp, unwrapped838)
                        else
                            function _t1431(_dollar_dollar)
                                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                    _t1432 = _get_oneof_field(_dollar_dollar, :disjunction)
                                else
                                    _t1432 = nothing
                                end
                                return _t1432
                            end
                            _t1433 = _t1431(msg)
                            deconstruct_result835 = _t1433
                            if !isnothing(deconstruct_result835)
                                unwrapped836 = deconstruct_result835
                                pretty_disjunction(pp, unwrapped836)
                            else
                                function _t1434(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("not"))
                                        _t1435 = _get_oneof_field(_dollar_dollar, :not)
                                    else
                                        _t1435 = nothing
                                    end
                                    return _t1435
                                end
                                _t1436 = _t1434(msg)
                                deconstruct_result833 = _t1436
                                if !isnothing(deconstruct_result833)
                                    unwrapped834 = deconstruct_result833
                                    pretty_not(pp, unwrapped834)
                                else
                                    function _t1437(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                            _t1438 = _get_oneof_field(_dollar_dollar, :ffi)
                                        else
                                            _t1438 = nothing
                                        end
                                        return _t1438
                                    end
                                    _t1439 = _t1437(msg)
                                    deconstruct_result831 = _t1439
                                    if !isnothing(deconstruct_result831)
                                        unwrapped832 = deconstruct_result831
                                        pretty_ffi(pp, unwrapped832)
                                    else
                                        function _t1440(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                                _t1441 = _get_oneof_field(_dollar_dollar, :atom)
                                            else
                                                _t1441 = nothing
                                            end
                                            return _t1441
                                        end
                                        _t1442 = _t1440(msg)
                                        deconstruct_result829 = _t1442
                                        if !isnothing(deconstruct_result829)
                                            unwrapped830 = deconstruct_result829
                                            pretty_atom(pp, unwrapped830)
                                        else
                                            function _t1443(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                    _t1444 = _get_oneof_field(_dollar_dollar, :pragma)
                                                else
                                                    _t1444 = nothing
                                                end
                                                return _t1444
                                            end
                                            _t1445 = _t1443(msg)
                                            deconstruct_result827 = _t1445
                                            if !isnothing(deconstruct_result827)
                                                unwrapped828 = deconstruct_result827
                                                pretty_pragma(pp, unwrapped828)
                                            else
                                                function _t1446(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                        _t1447 = _get_oneof_field(_dollar_dollar, :primitive)
                                                    else
                                                        _t1447 = nothing
                                                    end
                                                    return _t1447
                                                end
                                                _t1448 = _t1446(msg)
                                                deconstruct_result825 = _t1448
                                                if !isnothing(deconstruct_result825)
                                                    unwrapped826 = deconstruct_result825
                                                    pretty_primitive(pp, unwrapped826)
                                                else
                                                    function _t1449(_dollar_dollar)
                                                        if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                            _t1450 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                        else
                                                            _t1450 = nothing
                                                        end
                                                        return _t1450
                                                    end
                                                    _t1451 = _t1449(msg)
                                                    deconstruct_result823 = _t1451
                                                    if !isnothing(deconstruct_result823)
                                                        unwrapped824 = deconstruct_result823
                                                        pretty_rel_atom(pp, unwrapped824)
                                                    else
                                                        function _t1452(_dollar_dollar)
                                                            if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                                _t1453 = _get_oneof_field(_dollar_dollar, :cast)
                                                            else
                                                                _t1453 = nothing
                                                            end
                                                            return _t1453
                                                        end
                                                        _t1454 = _t1452(msg)
                                                        deconstruct_result821 = _t1454
                                                        if !isnothing(deconstruct_result821)
                                                            unwrapped822 = deconstruct_result821
                                                            pretty_cast(pp, unwrapped822)
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
    fields848 = msg
    write(pp, "(")
    write(pp, "true")
    write(pp, ")")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields849 = msg
    write(pp, "(")
    write(pp, "false")
    write(pp, ")")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat854 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat854)
        write(pp, flat854)
        return nothing
    else
        function _t1455(_dollar_dollar)
            _t1456 = deconstruct_bindings(pp, _dollar_dollar.body)
            return (_t1456, _dollar_dollar.body.value,)
        end
        _t1457 = _t1455(msg)
        fields850 = _t1457
        unwrapped_fields851 = fields850
        write(pp, "(")
        write(pp, "exists")
        indent_sexp!(pp)
        newline(pp)
        field852 = unwrapped_fields851[1]
        pretty_bindings(pp, field852)
        newline(pp)
        field853 = unwrapped_fields851[2]
        pretty_formula(pp, field853)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat860 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat860)
        write(pp, flat860)
        return nothing
    else
        function _t1458(_dollar_dollar)
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        end
        _t1459 = _t1458(msg)
        fields855 = _t1459
        unwrapped_fields856 = fields855
        write(pp, "(")
        write(pp, "reduce")
        indent_sexp!(pp)
        newline(pp)
        field857 = unwrapped_fields856[1]
        pretty_abstraction(pp, field857)
        newline(pp)
        field858 = unwrapped_fields856[2]
        pretty_abstraction(pp, field858)
        newline(pp)
        field859 = unwrapped_fields856[3]
        pretty_terms(pp, field859)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat864 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat864)
        write(pp, flat864)
        return nothing
    else
        fields861 = msg
        write(pp, "(")
        write(pp, "terms")
        indent_sexp!(pp)
        if !isempty(fields861)
            newline(pp)
            for (i1460, elem862) in enumerate(fields861)
                i863 = i1460 - 1
                if (i863 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem862)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat869 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat869)
        write(pp, flat869)
        return nothing
    else
        function _t1461(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("var"))
                _t1462 = _get_oneof_field(_dollar_dollar, :var)
            else
                _t1462 = nothing
            end
            return _t1462
        end
        _t1463 = _t1461(msg)
        deconstruct_result867 = _t1463
        if !isnothing(deconstruct_result867)
            unwrapped868 = deconstruct_result867
            pretty_var(pp, unwrapped868)
        else
            function _t1464(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("constant"))
                    _t1465 = _get_oneof_field(_dollar_dollar, :constant)
                else
                    _t1465 = nothing
                end
                return _t1465
            end
            _t1466 = _t1464(msg)
            deconstruct_result865 = _t1466
            if !isnothing(deconstruct_result865)
                unwrapped866 = deconstruct_result865
                pretty_constant(pp, unwrapped866)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat872 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat872)
        write(pp, flat872)
        return nothing
    else
        function _t1467(_dollar_dollar)
            return _dollar_dollar.name
        end
        _t1468 = _t1467(msg)
        fields870 = _t1468
        unwrapped_fields871 = fields870
        write(pp, unwrapped_fields871)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat874 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat874)
        write(pp, flat874)
        return nothing
    else
        fields873 = msg
        pretty_value(pp, fields873)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat879 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat879)
        write(pp, flat879)
        return nothing
    else
        function _t1469(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1470 = _t1469(msg)
        fields875 = _t1470
        unwrapped_fields876 = fields875
        write(pp, "(")
        write(pp, "and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields876)
            newline(pp)
            for (i1471, elem877) in enumerate(unwrapped_fields876)
                i878 = i1471 - 1
                if (i878 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem877)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat884 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat884)
        write(pp, flat884)
        return nothing
    else
        function _t1472(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1473 = _t1472(msg)
        fields880 = _t1473
        unwrapped_fields881 = fields880
        write(pp, "(")
        write(pp, "or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields881)
            newline(pp)
            for (i1474, elem882) in enumerate(unwrapped_fields881)
                i883 = i1474 - 1
                if (i883 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem882)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat887 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat887)
        write(pp, flat887)
        return nothing
    else
        function _t1475(_dollar_dollar)
            return _dollar_dollar.arg
        end
        _t1476 = _t1475(msg)
        fields885 = _t1476
        unwrapped_fields886 = fields885
        write(pp, "(")
        write(pp, "not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields886)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat893 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat893)
        write(pp, flat893)
        return nothing
    else
        function _t1477(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        end
        _t1478 = _t1477(msg)
        fields888 = _t1478
        unwrapped_fields889 = fields888
        write(pp, "(")
        write(pp, "ffi")
        indent_sexp!(pp)
        newline(pp)
        field890 = unwrapped_fields889[1]
        pretty_name(pp, field890)
        newline(pp)
        field891 = unwrapped_fields889[2]
        pretty_ffi_args(pp, field891)
        newline(pp)
        field892 = unwrapped_fields889[3]
        pretty_terms(pp, field892)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat895 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat895)
        write(pp, flat895)
        return nothing
    else
        fields894 = msg
        write(pp, ":")
        write(pp, fields894)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat899 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat899)
        write(pp, flat899)
        return nothing
    else
        fields896 = msg
        write(pp, "(")
        write(pp, "args")
        indent_sexp!(pp)
        if !isempty(fields896)
            newline(pp)
            for (i1479, elem897) in enumerate(fields896)
                i898 = i1479 - 1
                if (i898 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem897)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat906 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        function _t1480(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1481 = _t1480(msg)
        fields900 = _t1481
        unwrapped_fields901 = fields900
        write(pp, "(")
        write(pp, "atom")
        indent_sexp!(pp)
        newline(pp)
        field902 = unwrapped_fields901[1]
        pretty_relation_id(pp, field902)
        field903 = unwrapped_fields901[2]
        if !isempty(field903)
            newline(pp)
            for (i1482, elem904) in enumerate(field903)
                i905 = i1482 - 1
                if (i905 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem904)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat913 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat913)
        write(pp, flat913)
        return nothing
    else
        function _t1483(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1484 = _t1483(msg)
        fields907 = _t1484
        unwrapped_fields908 = fields907
        write(pp, "(")
        write(pp, "pragma")
        indent_sexp!(pp)
        newline(pp)
        field909 = unwrapped_fields908[1]
        pretty_name(pp, field909)
        field910 = unwrapped_fields908[2]
        if !isempty(field910)
            newline(pp)
            for (i1485, elem911) in enumerate(field910)
                i912 = i1485 - 1
                if (i912 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem911)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat929 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat929)
        write(pp, flat929)
        return nothing
    else
        function _t1486(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1487 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1487 = nothing
            end
            return _t1487
        end
        _t1488 = _t1486(msg)
        guard_result928 = _t1488
        if !isnothing(guard_result928)
            pretty_eq(pp, msg)
        else
            function _t1489(_dollar_dollar)
                if _dollar_dollar.name == "rel_primitive_lt_monotype"
                    _t1490 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1490 = nothing
                end
                return _t1490
            end
            _t1491 = _t1489(msg)
            guard_result927 = _t1491
            if !isnothing(guard_result927)
                pretty_lt(pp, msg)
            else
                function _t1492(_dollar_dollar)
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                        _t1493 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1493 = nothing
                    end
                    return _t1493
                end
                _t1494 = _t1492(msg)
                guard_result926 = _t1494
                if !isnothing(guard_result926)
                    pretty_lt_eq(pp, msg)
                else
                    function _t1495(_dollar_dollar)
                        if _dollar_dollar.name == "rel_primitive_gt_monotype"
                            _t1496 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1496 = nothing
                        end
                        return _t1496
                    end
                    _t1497 = _t1495(msg)
                    guard_result925 = _t1497
                    if !isnothing(guard_result925)
                        pretty_gt(pp, msg)
                    else
                        function _t1498(_dollar_dollar)
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                                _t1499 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                            else
                                _t1499 = nothing
                            end
                            return _t1499
                        end
                        _t1500 = _t1498(msg)
                        guard_result924 = _t1500
                        if !isnothing(guard_result924)
                            pretty_gt_eq(pp, msg)
                        else
                            function _t1501(_dollar_dollar)
                                if _dollar_dollar.name == "rel_primitive_add_monotype"
                                    _t1502 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1502 = nothing
                                end
                                return _t1502
                            end
                            _t1503 = _t1501(msg)
                            guard_result923 = _t1503
                            if !isnothing(guard_result923)
                                pretty_add(pp, msg)
                            else
                                function _t1504(_dollar_dollar)
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                        _t1505 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1505 = nothing
                                    end
                                    return _t1505
                                end
                                _t1506 = _t1504(msg)
                                guard_result922 = _t1506
                                if !isnothing(guard_result922)
                                    pretty_minus(pp, msg)
                                else
                                    function _t1507(_dollar_dollar)
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                            _t1508 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1508 = nothing
                                        end
                                        return _t1508
                                    end
                                    _t1509 = _t1507(msg)
                                    guard_result921 = _t1509
                                    if !isnothing(guard_result921)
                                        pretty_multiply(pp, msg)
                                    else
                                        function _t1510(_dollar_dollar)
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                                _t1511 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                            else
                                                _t1511 = nothing
                                            end
                                            return _t1511
                                        end
                                        _t1512 = _t1510(msg)
                                        guard_result920 = _t1512
                                        if !isnothing(guard_result920)
                                            pretty_divide(pp, msg)
                                        else
                                            function _t1513(_dollar_dollar)
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            end
                                            _t1514 = _t1513(msg)
                                            fields914 = _t1514
                                            unwrapped_fields915 = fields914
                                            write(pp, "(")
                                            write(pp, "primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field916 = unwrapped_fields915[1]
                                            pretty_name(pp, field916)
                                            field917 = unwrapped_fields915[2]
                                            if !isempty(field917)
                                                newline(pp)
                                                for (i1515, elem918) in enumerate(field917)
                                                    i919 = i1515 - 1
                                                    if (i919 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem918)
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
    flat934 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat934)
        write(pp, flat934)
        return nothing
    else
        function _t1516(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1517 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1517 = nothing
            end
            return _t1517
        end
        _t1518 = _t1516(msg)
        fields930 = _t1518
        unwrapped_fields931 = fields930
        write(pp, "(")
        write(pp, "=")
        indent_sexp!(pp)
        newline(pp)
        field932 = unwrapped_fields931[1]
        pretty_term(pp, field932)
        newline(pp)
        field933 = unwrapped_fields931[2]
        pretty_term(pp, field933)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat939 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat939)
        write(pp, flat939)
        return nothing
    else
        function _t1519(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1520 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1520 = nothing
            end
            return _t1520
        end
        _t1521 = _t1519(msg)
        fields935 = _t1521
        unwrapped_fields936 = fields935
        write(pp, "(")
        write(pp, "<")
        indent_sexp!(pp)
        newline(pp)
        field937 = unwrapped_fields936[1]
        pretty_term(pp, field937)
        newline(pp)
        field938 = unwrapped_fields936[2]
        pretty_term(pp, field938)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat944 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat944)
        write(pp, flat944)
        return nothing
    else
        function _t1522(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                _t1523 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1523 = nothing
            end
            return _t1523
        end
        _t1524 = _t1522(msg)
        fields940 = _t1524
        unwrapped_fields941 = fields940
        write(pp, "(")
        write(pp, "<=")
        indent_sexp!(pp)
        newline(pp)
        field942 = unwrapped_fields941[1]
        pretty_term(pp, field942)
        newline(pp)
        field943 = unwrapped_fields941[2]
        pretty_term(pp, field943)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat949 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat949)
        write(pp, flat949)
        return nothing
    else
        function _t1525(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_monotype"
                _t1526 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1526 = nothing
            end
            return _t1526
        end
        _t1527 = _t1525(msg)
        fields945 = _t1527
        unwrapped_fields946 = fields945
        write(pp, "(")
        write(pp, ">")
        indent_sexp!(pp)
        newline(pp)
        field947 = unwrapped_fields946[1]
        pretty_term(pp, field947)
        newline(pp)
        field948 = unwrapped_fields946[2]
        pretty_term(pp, field948)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat954 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat954)
        write(pp, flat954)
        return nothing
    else
        function _t1528(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                _t1529 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1529 = nothing
            end
            return _t1529
        end
        _t1530 = _t1528(msg)
        fields950 = _t1530
        unwrapped_fields951 = fields950
        write(pp, "(")
        write(pp, ">=")
        indent_sexp!(pp)
        newline(pp)
        field952 = unwrapped_fields951[1]
        pretty_term(pp, field952)
        newline(pp)
        field953 = unwrapped_fields951[2]
        pretty_term(pp, field953)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat960 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat960)
        write(pp, flat960)
        return nothing
    else
        function _t1531(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_add_monotype"
                _t1532 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1532 = nothing
            end
            return _t1532
        end
        _t1533 = _t1531(msg)
        fields955 = _t1533
        unwrapped_fields956 = fields955
        write(pp, "(")
        write(pp, "+")
        indent_sexp!(pp)
        newline(pp)
        field957 = unwrapped_fields956[1]
        pretty_term(pp, field957)
        newline(pp)
        field958 = unwrapped_fields956[2]
        pretty_term(pp, field958)
        newline(pp)
        field959 = unwrapped_fields956[3]
        pretty_term(pp, field959)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat966 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat966)
        write(pp, flat966)
        return nothing
    else
        function _t1534(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                _t1535 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1535 = nothing
            end
            return _t1535
        end
        _t1536 = _t1534(msg)
        fields961 = _t1536
        unwrapped_fields962 = fields961
        write(pp, "(")
        write(pp, "-")
        indent_sexp!(pp)
        newline(pp)
        field963 = unwrapped_fields962[1]
        pretty_term(pp, field963)
        newline(pp)
        field964 = unwrapped_fields962[2]
        pretty_term(pp, field964)
        newline(pp)
        field965 = unwrapped_fields962[3]
        pretty_term(pp, field965)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat972 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat972)
        write(pp, flat972)
        return nothing
    else
        function _t1537(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                _t1538 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1538 = nothing
            end
            return _t1538
        end
        _t1539 = _t1537(msg)
        fields967 = _t1539
        unwrapped_fields968 = fields967
        write(pp, "(")
        write(pp, "*")
        indent_sexp!(pp)
        newline(pp)
        field969 = unwrapped_fields968[1]
        pretty_term(pp, field969)
        newline(pp)
        field970 = unwrapped_fields968[2]
        pretty_term(pp, field970)
        newline(pp)
        field971 = unwrapped_fields968[3]
        pretty_term(pp, field971)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat978 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat978)
        write(pp, flat978)
        return nothing
    else
        function _t1540(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                _t1541 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1541 = nothing
            end
            return _t1541
        end
        _t1542 = _t1540(msg)
        fields973 = _t1542
        unwrapped_fields974 = fields973
        write(pp, "(")
        write(pp, "/")
        indent_sexp!(pp)
        newline(pp)
        field975 = unwrapped_fields974[1]
        pretty_term(pp, field975)
        newline(pp)
        field976 = unwrapped_fields974[2]
        pretty_term(pp, field976)
        newline(pp)
        field977 = unwrapped_fields974[3]
        pretty_term(pp, field977)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat983 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat983)
        write(pp, flat983)
        return nothing
    else
        function _t1543(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
                _t1544 = _get_oneof_field(_dollar_dollar, :specialized_value)
            else
                _t1544 = nothing
            end
            return _t1544
        end
        _t1545 = _t1543(msg)
        deconstruct_result981 = _t1545
        if !isnothing(deconstruct_result981)
            unwrapped982 = deconstruct_result981
            pretty_specialized_value(pp, unwrapped982)
        else
            function _t1546(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("term"))
                    _t1547 = _get_oneof_field(_dollar_dollar, :term)
                else
                    _t1547 = nothing
                end
                return _t1547
            end
            _t1548 = _t1546(msg)
            deconstruct_result979 = _t1548
            if !isnothing(deconstruct_result979)
                unwrapped980 = deconstruct_result979
                pretty_term(pp, unwrapped980)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat985 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat985)
        write(pp, flat985)
        return nothing
    else
        fields984 = msg
        write(pp, "#")
        pretty_value(pp, fields984)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat992 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat992)
        write(pp, flat992)
        return nothing
    else
        function _t1549(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1550 = _t1549(msg)
        fields986 = _t1550
        unwrapped_fields987 = fields986
        write(pp, "(")
        write(pp, "relatom")
        indent_sexp!(pp)
        newline(pp)
        field988 = unwrapped_fields987[1]
        pretty_name(pp, field988)
        field989 = unwrapped_fields987[2]
        if !isempty(field989)
            newline(pp)
            for (i1551, elem990) in enumerate(field989)
                i991 = i1551 - 1
                if (i991 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem990)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat997 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat997)
        write(pp, flat997)
        return nothing
    else
        function _t1552(_dollar_dollar)
            return (_dollar_dollar.input, _dollar_dollar.result,)
        end
        _t1553 = _t1552(msg)
        fields993 = _t1553
        unwrapped_fields994 = fields993
        write(pp, "(")
        write(pp, "cast")
        indent_sexp!(pp)
        newline(pp)
        field995 = unwrapped_fields994[1]
        pretty_term(pp, field995)
        newline(pp)
        field996 = unwrapped_fields994[2]
        pretty_term(pp, field996)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1001 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1001)
        write(pp, flat1001)
        return nothing
    else
        fields998 = msg
        write(pp, "(")
        write(pp, "attrs")
        indent_sexp!(pp)
        if !isempty(fields998)
            newline(pp)
            for (i1554, elem999) in enumerate(fields998)
                i1000 = i1554 - 1
                if (i1000 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem999)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1008 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1008)
        write(pp, flat1008)
        return nothing
    else
        function _t1555(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args,)
        end
        _t1556 = _t1555(msg)
        fields1002 = _t1556
        unwrapped_fields1003 = fields1002
        write(pp, "(")
        write(pp, "attribute")
        indent_sexp!(pp)
        newline(pp)
        field1004 = unwrapped_fields1003[1]
        pretty_name(pp, field1004)
        field1005 = unwrapped_fields1003[2]
        if !isempty(field1005)
            newline(pp)
            for (i1557, elem1006) in enumerate(field1005)
                i1007 = i1557 - 1
                if (i1007 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem1006)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1015 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1015)
        write(pp, flat1015)
        return nothing
    else
        function _t1558(_dollar_dollar)
            return (_dollar_dollar.var"#global", _dollar_dollar.body,)
        end
        _t1559 = _t1558(msg)
        fields1009 = _t1559
        unwrapped_fields1010 = fields1009
        write(pp, "(")
        write(pp, "algorithm")
        indent_sexp!(pp)
        field1011 = unwrapped_fields1010[1]
        if !isempty(field1011)
            newline(pp)
            for (i1560, elem1012) in enumerate(field1011)
                i1013 = i1560 - 1
                if (i1013 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1012)
            end
        end
        newline(pp)
        field1014 = unwrapped_fields1010[2]
        pretty_script(pp, field1014)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1020 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1020)
        write(pp, flat1020)
        return nothing
    else
        function _t1561(_dollar_dollar)
            return _dollar_dollar.constructs
        end
        _t1562 = _t1561(msg)
        fields1016 = _t1562
        unwrapped_fields1017 = fields1016
        write(pp, "(")
        write(pp, "script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1017)
            newline(pp)
            for (i1563, elem1018) in enumerate(unwrapped_fields1017)
                i1019 = i1563 - 1
                if (i1019 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1018)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1025 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1025)
        write(pp, flat1025)
        return nothing
    else
        function _t1564(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("loop"))
                _t1565 = _get_oneof_field(_dollar_dollar, :loop)
            else
                _t1565 = nothing
            end
            return _t1565
        end
        _t1566 = _t1564(msg)
        deconstruct_result1023 = _t1566
        if !isnothing(deconstruct_result1023)
            unwrapped1024 = deconstruct_result1023
            pretty_loop(pp, unwrapped1024)
        else
            function _t1567(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                    _t1568 = _get_oneof_field(_dollar_dollar, :instruction)
                else
                    _t1568 = nothing
                end
                return _t1568
            end
            _t1569 = _t1567(msg)
            deconstruct_result1021 = _t1569
            if !isnothing(deconstruct_result1021)
                unwrapped1022 = deconstruct_result1021
                pretty_instruction(pp, unwrapped1022)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1030 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1030)
        write(pp, flat1030)
        return nothing
    else
        function _t1570(_dollar_dollar)
            return (_dollar_dollar.init, _dollar_dollar.body,)
        end
        _t1571 = _t1570(msg)
        fields1026 = _t1571
        unwrapped_fields1027 = fields1026
        write(pp, "(")
        write(pp, "loop")
        indent_sexp!(pp)
        newline(pp)
        field1028 = unwrapped_fields1027[1]
        pretty_init(pp, field1028)
        newline(pp)
        field1029 = unwrapped_fields1027[2]
        pretty_script(pp, field1029)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1034 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1034)
        write(pp, flat1034)
        return nothing
    else
        fields1031 = msg
        write(pp, "(")
        write(pp, "init")
        indent_sexp!(pp)
        if !isempty(fields1031)
            newline(pp)
            for (i1572, elem1032) in enumerate(fields1031)
                i1033 = i1572 - 1
                if (i1033 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1032)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1045 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1045)
        write(pp, flat1045)
        return nothing
    else
        function _t1573(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("assign"))
                _t1574 = _get_oneof_field(_dollar_dollar, :assign)
            else
                _t1574 = nothing
            end
            return _t1574
        end
        _t1575 = _t1573(msg)
        deconstruct_result1043 = _t1575
        if !isnothing(deconstruct_result1043)
            unwrapped1044 = deconstruct_result1043
            pretty_assign(pp, unwrapped1044)
        else
            function _t1576(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                    _t1577 = _get_oneof_field(_dollar_dollar, :upsert)
                else
                    _t1577 = nothing
                end
                return _t1577
            end
            _t1578 = _t1576(msg)
            deconstruct_result1041 = _t1578
            if !isnothing(deconstruct_result1041)
                unwrapped1042 = deconstruct_result1041
                pretty_upsert(pp, unwrapped1042)
            else
                function _t1579(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("#break"))
                        _t1580 = _get_oneof_field(_dollar_dollar, :var"#break")
                    else
                        _t1580 = nothing
                    end
                    return _t1580
                end
                _t1581 = _t1579(msg)
                deconstruct_result1039 = _t1581
                if !isnothing(deconstruct_result1039)
                    unwrapped1040 = deconstruct_result1039
                    pretty_break(pp, unwrapped1040)
                else
                    function _t1582(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                            _t1583 = _get_oneof_field(_dollar_dollar, :monoid_def)
                        else
                            _t1583 = nothing
                        end
                        return _t1583
                    end
                    _t1584 = _t1582(msg)
                    deconstruct_result1037 = _t1584
                    if !isnothing(deconstruct_result1037)
                        unwrapped1038 = deconstruct_result1037
                        pretty_monoid_def(pp, unwrapped1038)
                    else
                        function _t1585(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                                _t1586 = _get_oneof_field(_dollar_dollar, :monus_def)
                            else
                                _t1586 = nothing
                            end
                            return _t1586
                        end
                        _t1587 = _t1585(msg)
                        deconstruct_result1035 = _t1587
                        if !isnothing(deconstruct_result1035)
                            unwrapped1036 = deconstruct_result1035
                            pretty_monus_def(pp, unwrapped1036)
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
    flat1052 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1052)
        write(pp, flat1052)
        return nothing
    else
        function _t1588(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1589 = _dollar_dollar.attrs
            else
                _t1589 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1589,)
        end
        _t1590 = _t1588(msg)
        fields1046 = _t1590
        unwrapped_fields1047 = fields1046
        write(pp, "(")
        write(pp, "assign")
        indent_sexp!(pp)
        newline(pp)
        field1048 = unwrapped_fields1047[1]
        pretty_relation_id(pp, field1048)
        newline(pp)
        field1049 = unwrapped_fields1047[2]
        pretty_abstraction(pp, field1049)
        field1050 = unwrapped_fields1047[3]
        if !isnothing(field1050)
            newline(pp)
            opt_val1051 = field1050
            pretty_attrs(pp, opt_val1051)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1059 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1059)
        write(pp, flat1059)
        return nothing
    else
        function _t1591(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1592 = _dollar_dollar.attrs
            else
                _t1592 = nothing
            end
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1592,)
        end
        _t1593 = _t1591(msg)
        fields1053 = _t1593
        unwrapped_fields1054 = fields1053
        write(pp, "(")
        write(pp, "upsert")
        indent_sexp!(pp)
        newline(pp)
        field1055 = unwrapped_fields1054[1]
        pretty_relation_id(pp, field1055)
        newline(pp)
        field1056 = unwrapped_fields1054[2]
        pretty_abstraction_with_arity(pp, field1056)
        field1057 = unwrapped_fields1054[3]
        if !isnothing(field1057)
            newline(pp)
            opt_val1058 = field1057
            pretty_attrs(pp, opt_val1058)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1064 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1064)
        write(pp, flat1064)
        return nothing
    else
        function _t1594(_dollar_dollar)
            _t1595 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
            return (_t1595, _dollar_dollar[1].value,)
        end
        _t1596 = _t1594(msg)
        fields1060 = _t1596
        unwrapped_fields1061 = fields1060
        write(pp, "(")
        indent!(pp)
        field1062 = unwrapped_fields1061[1]
        pretty_bindings(pp, field1062)
        newline(pp)
        field1063 = unwrapped_fields1061[2]
        pretty_formula(pp, field1063)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1071 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1071)
        write(pp, flat1071)
        return nothing
    else
        function _t1597(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1598 = _dollar_dollar.attrs
            else
                _t1598 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1598,)
        end
        _t1599 = _t1597(msg)
        fields1065 = _t1599
        unwrapped_fields1066 = fields1065
        write(pp, "(")
        write(pp, "break")
        indent_sexp!(pp)
        newline(pp)
        field1067 = unwrapped_fields1066[1]
        pretty_relation_id(pp, field1067)
        newline(pp)
        field1068 = unwrapped_fields1066[2]
        pretty_abstraction(pp, field1068)
        field1069 = unwrapped_fields1066[3]
        if !isnothing(field1069)
            newline(pp)
            opt_val1070 = field1069
            pretty_attrs(pp, opt_val1070)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1079 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1079)
        write(pp, flat1079)
        return nothing
    else
        function _t1600(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1601 = _dollar_dollar.attrs
            else
                _t1601 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1601,)
        end
        _t1602 = _t1600(msg)
        fields1072 = _t1602
        unwrapped_fields1073 = fields1072
        write(pp, "(")
        write(pp, "monoid")
        indent_sexp!(pp)
        newline(pp)
        field1074 = unwrapped_fields1073[1]
        pretty_monoid(pp, field1074)
        newline(pp)
        field1075 = unwrapped_fields1073[2]
        pretty_relation_id(pp, field1075)
        newline(pp)
        field1076 = unwrapped_fields1073[3]
        pretty_abstraction_with_arity(pp, field1076)
        field1077 = unwrapped_fields1073[4]
        if !isnothing(field1077)
            newline(pp)
            opt_val1078 = field1077
            pretty_attrs(pp, opt_val1078)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1088 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1088)
        write(pp, flat1088)
        return nothing
    else
        function _t1603(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
                _t1604 = _get_oneof_field(_dollar_dollar, :or_monoid)
            else
                _t1604 = nothing
            end
            return _t1604
        end
        _t1605 = _t1603(msg)
        deconstruct_result1086 = _t1605
        if !isnothing(deconstruct_result1086)
            unwrapped1087 = deconstruct_result1086
            pretty_or_monoid(pp, unwrapped1087)
        else
            function _t1606(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                    _t1607 = _get_oneof_field(_dollar_dollar, :min_monoid)
                else
                    _t1607 = nothing
                end
                return _t1607
            end
            _t1608 = _t1606(msg)
            deconstruct_result1084 = _t1608
            if !isnothing(deconstruct_result1084)
                unwrapped1085 = deconstruct_result1084
                pretty_min_monoid(pp, unwrapped1085)
            else
                function _t1609(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                        _t1610 = _get_oneof_field(_dollar_dollar, :max_monoid)
                    else
                        _t1610 = nothing
                    end
                    return _t1610
                end
                _t1611 = _t1609(msg)
                deconstruct_result1082 = _t1611
                if !isnothing(deconstruct_result1082)
                    unwrapped1083 = deconstruct_result1082
                    pretty_max_monoid(pp, unwrapped1083)
                else
                    function _t1612(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                            _t1613 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                        else
                            _t1613 = nothing
                        end
                        return _t1613
                    end
                    _t1614 = _t1612(msg)
                    deconstruct_result1080 = _t1614
                    if !isnothing(deconstruct_result1080)
                        unwrapped1081 = deconstruct_result1080
                        pretty_sum_monoid(pp, unwrapped1081)
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
    fields1089 = msg
    write(pp, "(")
    write(pp, "or")
    write(pp, ")")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1092 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        function _t1615(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1616 = _t1615(msg)
        fields1090 = _t1616
        unwrapped_fields1091 = fields1090
        write(pp, "(")
        write(pp, "min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1091)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1095 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1095)
        write(pp, flat1095)
        return nothing
    else
        function _t1617(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1618 = _t1617(msg)
        fields1093 = _t1618
        unwrapped_fields1094 = fields1093
        write(pp, "(")
        write(pp, "max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1094)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1098 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1098)
        write(pp, flat1098)
        return nothing
    else
        function _t1619(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1620 = _t1619(msg)
        fields1096 = _t1620
        unwrapped_fields1097 = fields1096
        write(pp, "(")
        write(pp, "sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1097)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1106 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1106)
        write(pp, flat1106)
        return nothing
    else
        function _t1621(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1622 = _dollar_dollar.attrs
            else
                _t1622 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1622,)
        end
        _t1623 = _t1621(msg)
        fields1099 = _t1623
        unwrapped_fields1100 = fields1099
        write(pp, "(")
        write(pp, "monus")
        indent_sexp!(pp)
        newline(pp)
        field1101 = unwrapped_fields1100[1]
        pretty_monoid(pp, field1101)
        newline(pp)
        field1102 = unwrapped_fields1100[2]
        pretty_relation_id(pp, field1102)
        newline(pp)
        field1103 = unwrapped_fields1100[3]
        pretty_abstraction_with_arity(pp, field1103)
        field1104 = unwrapped_fields1100[4]
        if !isnothing(field1104)
            newline(pp)
            opt_val1105 = field1104
            pretty_attrs(pp, opt_val1105)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1113 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1113)
        write(pp, flat1113)
        return nothing
    else
        function _t1624(_dollar_dollar)
            return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        end
        _t1625 = _t1624(msg)
        fields1107 = _t1625
        unwrapped_fields1108 = fields1107
        write(pp, "(")
        write(pp, "functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1109 = unwrapped_fields1108[1]
        pretty_relation_id(pp, field1109)
        newline(pp)
        field1110 = unwrapped_fields1108[2]
        pretty_abstraction(pp, field1110)
        newline(pp)
        field1111 = unwrapped_fields1108[3]
        pretty_functional_dependency_keys(pp, field1111)
        newline(pp)
        field1112 = unwrapped_fields1108[4]
        pretty_functional_dependency_values(pp, field1112)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1117 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1117)
        write(pp, flat1117)
        return nothing
    else
        fields1114 = msg
        write(pp, "(")
        write(pp, "keys")
        indent_sexp!(pp)
        if !isempty(fields1114)
            newline(pp)
            for (i1626, elem1115) in enumerate(fields1114)
                i1116 = i1626 - 1
                if (i1116 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1115)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1121 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1121)
        write(pp, flat1121)
        return nothing
    else
        fields1118 = msg
        write(pp, "(")
        write(pp, "values")
        indent_sexp!(pp)
        if !isempty(fields1118)
            newline(pp)
            for (i1627, elem1119) in enumerate(fields1118)
                i1120 = i1627 - 1
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

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1128 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1128)
        write(pp, flat1128)
        return nothing
    else
        function _t1628(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("edb"))
                _t1629 = _get_oneof_field(_dollar_dollar, :edb)
            else
                _t1629 = nothing
            end
            return _t1629
        end
        _t1630 = _t1628(msg)
        deconstruct_result1126 = _t1630
        if !isnothing(deconstruct_result1126)
            unwrapped1127 = deconstruct_result1126
            pretty_edb(pp, unwrapped1127)
        else
            function _t1631(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                    _t1632 = _get_oneof_field(_dollar_dollar, :betree_relation)
                else
                    _t1632 = nothing
                end
                return _t1632
            end
            _t1633 = _t1631(msg)
            deconstruct_result1124 = _t1633
            if !isnothing(deconstruct_result1124)
                unwrapped1125 = deconstruct_result1124
                pretty_betree_relation(pp, unwrapped1125)
            else
                function _t1634(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                        _t1635 = _get_oneof_field(_dollar_dollar, :csv_data)
                    else
                        _t1635 = nothing
                    end
                    return _t1635
                end
                _t1636 = _t1634(msg)
                deconstruct_result1122 = _t1636
                if !isnothing(deconstruct_result1122)
                    unwrapped1123 = deconstruct_result1122
                    pretty_csv_data(pp, unwrapped1123)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_edb(pp::PrettyPrinter, msg::Proto.EDB)
    flat1134 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1134)
        write(pp, flat1134)
        return nothing
    else
        function _t1637(_dollar_dollar)
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        end
        _t1638 = _t1637(msg)
        fields1129 = _t1638
        unwrapped_fields1130 = fields1129
        write(pp, "(")
        write(pp, "edb")
        indent_sexp!(pp)
        newline(pp)
        field1131 = unwrapped_fields1130[1]
        pretty_relation_id(pp, field1131)
        newline(pp)
        field1132 = unwrapped_fields1130[2]
        pretty_edb_path(pp, field1132)
        newline(pp)
        field1133 = unwrapped_fields1130[3]
        pretty_edb_types(pp, field1133)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1138 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1138)
        write(pp, flat1138)
        return nothing
    else
        fields1135 = msg
        write(pp, "[")
        indent!(pp)
        for (i1639, elem1136) in enumerate(fields1135)
            i1137 = i1639 - 1
            if (i1137 > 0)
                newline(pp)
            end
            write(pp, format_string(pp, elem1136))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1142 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1142)
        write(pp, flat1142)
        return nothing
    else
        fields1139 = msg
        write(pp, "[")
        indent!(pp)
        for (i1640, elem1140) in enumerate(fields1139)
            i1141 = i1640 - 1
            if (i1141 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1140)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1147 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1147)
        write(pp, flat1147)
        return nothing
    else
        function _t1641(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        end
        _t1642 = _t1641(msg)
        fields1143 = _t1642
        unwrapped_fields1144 = fields1143
        write(pp, "(")
        write(pp, "betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1145 = unwrapped_fields1144[1]
        pretty_relation_id(pp, field1145)
        newline(pp)
        field1146 = unwrapped_fields1144[2]
        pretty_betree_info(pp, field1146)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1153 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1153)
        write(pp, flat1153)
        return nothing
    else
        function _t1643(_dollar_dollar)
            _t1644 = deconstruct_betree_info_config(pp, _dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1644,)
        end
        _t1645 = _t1643(msg)
        fields1148 = _t1645
        unwrapped_fields1149 = fields1148
        write(pp, "(")
        write(pp, "betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1150 = unwrapped_fields1149[1]
        pretty_betree_info_key_types(pp, field1150)
        newline(pp)
        field1151 = unwrapped_fields1149[2]
        pretty_betree_info_value_types(pp, field1151)
        newline(pp)
        field1152 = unwrapped_fields1149[3]
        pretty_config_dict(pp, field1152)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1157 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1157)
        write(pp, flat1157)
        return nothing
    else
        fields1154 = msg
        write(pp, "(")
        write(pp, "key_types")
        indent_sexp!(pp)
        if !isempty(fields1154)
            newline(pp)
            for (i1646, elem1155) in enumerate(fields1154)
                i1156 = i1646 - 1
                if (i1156 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1155)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1161 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1161)
        write(pp, flat1161)
        return nothing
    else
        fields1158 = msg
        write(pp, "(")
        write(pp, "value_types")
        indent_sexp!(pp)
        if !isempty(fields1158)
            newline(pp)
            for (i1647, elem1159) in enumerate(fields1158)
                i1160 = i1647 - 1
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

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1168 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1168)
        write(pp, flat1168)
        return nothing
    else
        function _t1648(_dollar_dollar)
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        end
        _t1649 = _t1648(msg)
        fields1162 = _t1649
        unwrapped_fields1163 = fields1162
        write(pp, "(")
        write(pp, "csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1164 = unwrapped_fields1163[1]
        pretty_csvlocator(pp, field1164)
        newline(pp)
        field1165 = unwrapped_fields1163[2]
        pretty_csv_config(pp, field1165)
        newline(pp)
        field1166 = unwrapped_fields1163[3]
        pretty_gnf_columns(pp, field1166)
        newline(pp)
        field1167 = unwrapped_fields1163[4]
        pretty_csv_asof(pp, field1167)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1175 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1175)
        write(pp, flat1175)
        return nothing
    else
        function _t1650(_dollar_dollar)
            if !isempty(_dollar_dollar.paths)
                _t1651 = _dollar_dollar.paths
            else
                _t1651 = nothing
            end
            if String(copy(_dollar_dollar.inline_data)) != ""
                _t1652 = String(copy(_dollar_dollar.inline_data))
            else
                _t1652 = nothing
            end
            return (_t1651, _t1652,)
        end
        _t1653 = _t1650(msg)
        fields1169 = _t1653
        unwrapped_fields1170 = fields1169
        write(pp, "(")
        write(pp, "csv_locator")
        indent_sexp!(pp)
        field1171 = unwrapped_fields1170[1]
        if !isnothing(field1171)
            newline(pp)
            opt_val1172 = field1171
            pretty_csv_locator_paths(pp, opt_val1172)
        end
        field1173 = unwrapped_fields1170[2]
        if !isnothing(field1173)
            newline(pp)
            opt_val1174 = field1173
            pretty_csv_locator_inline_data(pp, opt_val1174)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1179 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        fields1176 = msg
        write(pp, "(")
        write(pp, "paths")
        indent_sexp!(pp)
        if !isempty(fields1176)
            newline(pp)
            for (i1654, elem1177) in enumerate(fields1176)
                i1178 = i1654 - 1
                if (i1178 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1177))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1181 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1181)
        write(pp, flat1181)
        return nothing
    else
        fields1180 = msg
        write(pp, "(")
        write(pp, "inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1180))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1184 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1184)
        write(pp, flat1184)
        return nothing
    else
        function _t1655(_dollar_dollar)
            _t1656 = deconstruct_csv_config(pp, _dollar_dollar)
            return _t1656
        end
        _t1657 = _t1655(msg)
        fields1182 = _t1657
        unwrapped_fields1183 = fields1182
        write(pp, "(")
        write(pp, "csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1183)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1188 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1188)
        write(pp, flat1188)
        return nothing
    else
        fields1185 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1185)
            newline(pp)
            for (i1658, elem1186) in enumerate(fields1185)
                i1187 = i1658 - 1
                if (i1187 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1186)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1197 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1197)
        write(pp, flat1197)
        return nothing
    else
        function _t1659(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("target_id"))
                _t1660 = _dollar_dollar.target_id
            else
                _t1660 = nothing
            end
            return (_dollar_dollar.column_path, _t1660, _dollar_dollar.types,)
        end
        _t1661 = _t1659(msg)
        fields1189 = _t1661
        unwrapped_fields1190 = fields1189
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1191 = unwrapped_fields1190[1]
        pretty_gnf_column_path(pp, field1191)
        field1192 = unwrapped_fields1190[2]
        if !isnothing(field1192)
            newline(pp)
            opt_val1193 = field1192
            pretty_relation_id(pp, opt_val1193)
        end
        newline(pp)
        write(pp, "[")
        field1194 = unwrapped_fields1190[3]
        for (i1662, elem1195) in enumerate(field1194)
            i1196 = i1662 - 1
            if (i1196 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1195)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1204 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1204)
        write(pp, flat1204)
        return nothing
    else
        function _t1663(_dollar_dollar)
            if length(_dollar_dollar) == 1
                _t1664 = _dollar_dollar[1]
            else
                _t1664 = nothing
            end
            return _t1664
        end
        _t1665 = _t1663(msg)
        deconstruct_result1202 = _t1665
        if !isnothing(deconstruct_result1202)
            unwrapped1203 = deconstruct_result1202
            write(pp, format_string(pp, unwrapped1203))
        else
            function _t1666(_dollar_dollar)
                if length(_dollar_dollar) != 1
                    _t1667 = _dollar_dollar
                else
                    _t1667 = nothing
                end
                return _t1667
            end
            _t1668 = _t1666(msg)
            deconstruct_result1198 = _t1668
            if !isnothing(deconstruct_result1198)
                unwrapped1199 = deconstruct_result1198
                write(pp, "[")
                indent!(pp)
                for (i1669, elem1200) in enumerate(unwrapped1199)
                    i1201 = i1669 - 1
                    if (i1201 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(pp, elem1200))
                end
                dedent!(pp)
                write(pp, "]")
            else
                throw(ParseError("No matching rule for gnf_column_path"))
            end
        end
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1206 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1206)
        write(pp, flat1206)
        return nothing
    else
        fields1205 = msg
        write(pp, "(")
        write(pp, "asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1205))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1209 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1209)
        write(pp, flat1209)
        return nothing
    else
        function _t1670(_dollar_dollar)
            return _dollar_dollar.fragment_id
        end
        _t1671 = _t1670(msg)
        fields1207 = _t1671
        unwrapped_fields1208 = fields1207
        write(pp, "(")
        write(pp, "undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1208)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1214 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1214)
        write(pp, flat1214)
        return nothing
    else
        function _t1672(_dollar_dollar)
            return _dollar_dollar.relations
        end
        _t1673 = _t1672(msg)
        fields1210 = _t1673
        unwrapped_fields1211 = fields1210
        write(pp, "(")
        write(pp, "context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1211)
            newline(pp)
            for (i1674, elem1212) in enumerate(unwrapped_fields1211)
                i1213 = i1674 - 1
                if (i1213 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1212)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1219 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1219)
        write(pp, flat1219)
        return nothing
    else
        function _t1675(_dollar_dollar)
            return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        end
        _t1676 = _t1675(msg)
        fields1215 = _t1676
        unwrapped_fields1216 = fields1215
        write(pp, "(")
        write(pp, "snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1217 = unwrapped_fields1216[1]
        pretty_edb_path(pp, field1217)
        newline(pp)
        field1218 = unwrapped_fields1216[2]
        pretty_relation_id(pp, field1218)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1223 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1223)
        write(pp, flat1223)
        return nothing
    else
        fields1220 = msg
        write(pp, "(")
        write(pp, "reads")
        indent_sexp!(pp)
        if !isempty(fields1220)
            newline(pp)
            for (i1677, elem1221) in enumerate(fields1220)
                i1222 = i1677 - 1
                if (i1222 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1221)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1234 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1234)
        write(pp, flat1234)
        return nothing
    else
        function _t1678(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("demand"))
                _t1679 = _get_oneof_field(_dollar_dollar, :demand)
            else
                _t1679 = nothing
            end
            return _t1679
        end
        _t1680 = _t1678(msg)
        deconstruct_result1232 = _t1680
        if !isnothing(deconstruct_result1232)
            unwrapped1233 = deconstruct_result1232
            pretty_demand(pp, unwrapped1233)
        else
            function _t1681(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("output"))
                    _t1682 = _get_oneof_field(_dollar_dollar, :output)
                else
                    _t1682 = nothing
                end
                return _t1682
            end
            _t1683 = _t1681(msg)
            deconstruct_result1230 = _t1683
            if !isnothing(deconstruct_result1230)
                unwrapped1231 = deconstruct_result1230
                pretty_output(pp, unwrapped1231)
            else
                function _t1684(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                        _t1685 = _get_oneof_field(_dollar_dollar, :what_if)
                    else
                        _t1685 = nothing
                    end
                    return _t1685
                end
                _t1686 = _t1684(msg)
                deconstruct_result1228 = _t1686
                if !isnothing(deconstruct_result1228)
                    unwrapped1229 = deconstruct_result1228
                    pretty_what_if(pp, unwrapped1229)
                else
                    function _t1687(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("abort"))
                            _t1688 = _get_oneof_field(_dollar_dollar, :abort)
                        else
                            _t1688 = nothing
                        end
                        return _t1688
                    end
                    _t1689 = _t1687(msg)
                    deconstruct_result1226 = _t1689
                    if !isnothing(deconstruct_result1226)
                        unwrapped1227 = deconstruct_result1226
                        pretty_abort(pp, unwrapped1227)
                    else
                        function _t1690(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("#export"))
                                _t1691 = _get_oneof_field(_dollar_dollar, :var"#export")
                            else
                                _t1691 = nothing
                            end
                            return _t1691
                        end
                        _t1692 = _t1690(msg)
                        deconstruct_result1224 = _t1692
                        if !isnothing(deconstruct_result1224)
                            unwrapped1225 = deconstruct_result1224
                            pretty_export(pp, unwrapped1225)
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
    flat1237 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1237)
        write(pp, flat1237)
        return nothing
    else
        function _t1693(_dollar_dollar)
            return _dollar_dollar.relation_id
        end
        _t1694 = _t1693(msg)
        fields1235 = _t1694
        unwrapped_fields1236 = fields1235
        write(pp, "(")
        write(pp, "demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1236)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1242 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1242)
        write(pp, flat1242)
        return nothing
    else
        function _t1695(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        end
        _t1696 = _t1695(msg)
        fields1238 = _t1696
        unwrapped_fields1239 = fields1238
        write(pp, "(")
        write(pp, "output")
        indent_sexp!(pp)
        newline(pp)
        field1240 = unwrapped_fields1239[1]
        pretty_name(pp, field1240)
        newline(pp)
        field1241 = unwrapped_fields1239[2]
        pretty_relation_id(pp, field1241)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1247 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1247)
        write(pp, flat1247)
        return nothing
    else
        function _t1697(_dollar_dollar)
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        end
        _t1698 = _t1697(msg)
        fields1243 = _t1698
        unwrapped_fields1244 = fields1243
        write(pp, "(")
        write(pp, "what_if")
        indent_sexp!(pp)
        newline(pp)
        field1245 = unwrapped_fields1244[1]
        pretty_name(pp, field1245)
        newline(pp)
        field1246 = unwrapped_fields1244[2]
        pretty_epoch(pp, field1246)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1253 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        function _t1699(_dollar_dollar)
            if _dollar_dollar.name != "abort"
                _t1700 = _dollar_dollar.name
            else
                _t1700 = nothing
            end
            return (_t1700, _dollar_dollar.relation_id,)
        end
        _t1701 = _t1699(msg)
        fields1248 = _t1701
        unwrapped_fields1249 = fields1248
        write(pp, "(")
        write(pp, "abort")
        indent_sexp!(pp)
        field1250 = unwrapped_fields1249[1]
        if !isnothing(field1250)
            newline(pp)
            opt_val1251 = field1250
            pretty_name(pp, opt_val1251)
        end
        newline(pp)
        field1252 = unwrapped_fields1249[2]
        pretty_relation_id(pp, field1252)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1256 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1256)
        write(pp, flat1256)
        return nothing
    else
        function _t1702(_dollar_dollar)
            return _get_oneof_field(_dollar_dollar, :csv_config)
        end
        _t1703 = _t1702(msg)
        fields1254 = _t1703
        unwrapped_fields1255 = fields1254
        write(pp, "(")
        write(pp, "export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1255)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1262 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1262)
        write(pp, flat1262)
        return nothing
    else
        function _t1704(_dollar_dollar)
            _t1705 = deconstruct_export_csv_config(pp, _dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1705,)
        end
        _t1706 = _t1704(msg)
        fields1257 = _t1706
        unwrapped_fields1258 = fields1257
        write(pp, "(")
        write(pp, "export_csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1259 = unwrapped_fields1258[1]
        pretty_export_csv_path(pp, field1259)
        newline(pp)
        field1260 = unwrapped_fields1258[2]
        pretty_export_csv_columns(pp, field1260)
        newline(pp)
        field1261 = unwrapped_fields1258[3]
        pretty_config_dict(pp, field1261)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1264 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1264)
        write(pp, flat1264)
        return nothing
    else
        fields1263 = msg
        write(pp, "(")
        write(pp, "path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1263))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1268 = try_flat(pp, msg, pretty_export_csv_columns)
    if !isnothing(flat1268)
        write(pp, flat1268)
        return nothing
    else
        fields1265 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1265)
            newline(pp)
            for (i1707, elem1266) in enumerate(fields1265)
                i1267 = i1707 - 1
                if (i1267 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1266)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_column(pp::PrettyPrinter, msg::Proto.ExportCSVColumn)
    flat1273 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1273)
        write(pp, flat1273)
        return nothing
    else
        function _t1708(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        end
        _t1709 = _t1708(msg)
        fields1269 = _t1709
        unwrapped_fields1270 = fields1269
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1271 = unwrapped_fields1270[1]
        write(pp, format_string(pp, field1271))
        newline(pp)
        field1272 = unwrapped_fields1270[2]
        pretty_relation_id(pp, field1272)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1747, _rid) in enumerate(msg.ids)
        _idx = i1747 - 1
        newline(pp)
        write(pp, "(")
        _t1748 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1748)
        write(pp, " ")
        write(pp, format_string(pp, msg.orig_names[_idx + 1]))
        write(pp, ")")
    end
    write(pp, ")")
    dedent!(pp)
    return nothing
end

function pretty_be_tree_config(pp::PrettyPrinter, msg::Proto.BeTreeConfig)
    write(pp, "(be_tree_config")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":epsilon ")
    write(pp, format_float(pp, msg.epsilon))
    newline(pp)
    write(pp, ":max_pivots ")
    write(pp, format_int(pp, msg.max_pivots))
    newline(pp)
    write(pp, ":max_deltas ")
    write(pp, format_int(pp, msg.max_deltas))
    newline(pp)
    write(pp, ":max_leaf ")
    write(pp, format_int(pp, msg.max_leaf))
    write(pp, ")")
    dedent!(pp)
    return nothing
end

function pretty_be_tree_locator(pp::PrettyPrinter, msg::Proto.BeTreeLocator)
    write(pp, "(be_tree_locator")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":element_count ")
    write(pp, format_int(pp, msg.element_count))
    newline(pp)
    write(pp, ":tree_height ")
    write(pp, format_int(pp, msg.tree_height))
    newline(pp)
    write(pp, ":location ")
    if _has_proto_field(msg, Symbol("root_pageid"))
        write(pp, "(:root_pageid ")
        _pprint_dispatch(pp, _get_oneof_field(msg, :root_pageid))
        write(pp, ")")
    else
        if _has_proto_field(msg, Symbol("inline_data"))
            write(pp, "(:inline_data ")
            write(pp, "0x" * bytes2hex(_get_oneof_field(msg, :inline_data)))
            write(pp, ")")
        else
            write(pp, "nothing")
        end
    end
    write(pp, ")")
    dedent!(pp)
    return nothing
end

function pretty_decimal_value(pp::PrettyPrinter, msg::Proto.DecimalValue)
    write(pp, format_decimal(pp, msg))
    return nothing
end

function pretty_functional_dependency(pp::PrettyPrinter, msg::Proto.FunctionalDependency)
    write(pp, "(functional_dependency")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":guard ")
    _pprint_dispatch(pp, msg.guard)
    newline(pp)
    write(pp, ":keys ")
    write(pp, "(")
    for (i1749, _elem) in enumerate(msg.keys)
        _idx = i1749 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values ")
    write(pp, "(")
    for (i1750, _elem) in enumerate(msg.values)
        _idx = i1750 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    write(pp, ")")
    dedent!(pp)
    return nothing
end

function pretty_int128_value(pp::PrettyPrinter, msg::Proto.Int128Value)
    write(pp, format_int128(pp, msg))
    return nothing
end

function pretty_missing_value(pp::PrettyPrinter, msg::Proto.MissingValue)
    write(pp, "missing")
    return nothing
end

function pretty_u_int128_value(pp::PrettyPrinter, msg::Proto.UInt128Value)
    write(pp, format_uint128(pp, msg))
    return nothing
end

function pretty_ivm_config(pp::PrettyPrinter, msg::Proto.IVMConfig)
    write(pp, "(ivm_config")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":level ")
    _pprint_dispatch(pp, msg.level)
    write(pp, ")")
    dedent!(pp)
    return nothing
end

function pretty_maintenance_level(pp::PrettyPrinter, x::Proto.MaintenanceLevel.T)
    if x == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_UNSPECIFIED
        write(pp, "unspecified")
    else
        if x == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
            write(pp, "off")
        else
            if x == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
                write(pp, "auto")
            else
                if x == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
                    write(pp, "all")
                end
            end
        end
    end
    return nothing
end

# --- pprint dispatch (generated) ---
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Transaction) = pretty_transaction(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Configure) = pretty_configure(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Tuple{String, Proto.Value}}) = pretty_config_dict(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Tuple{String, Proto.Value}) = pretty_config_key_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Value) = pretty_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DateValue) = pretty_date(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DateTimeValue) = pretty_datetime(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Bool) = pretty_boolean_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Sync) = pretty_sync(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FragmentId) = pretty_fragment_id(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Epoch) = pretty_epoch(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.Write}) = pretty_epoch_writes(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Write) = pretty_write(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Define) = pretty_define(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Fragment) = pretty_fragment(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Declaration) = pretty_declaration(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Def) = pretty_def(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.RelationId) = pretty_relation_id(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Abstraction) = pretty_abstraction(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}) = pretty_bindings(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Binding) = pretty_binding(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.var"#Type") = pretty_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.UnspecifiedType) = pretty_unspecified_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.StringType) = pretty_string_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.IntType) = pretty_int_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FloatType) = pretty_float_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.UInt128Type) = pretty_uint128_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Int128Type) = pretty_int128_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DateType) = pretty_date_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DateTimeType) = pretty_datetime_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MissingType) = pretty_missing_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DecimalType) = pretty_decimal_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BooleanType) = pretty_boolean_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.Binding}) = pretty_value_bindings(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Formula) = pretty_formula(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Conjunction) = pretty_conjunction(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Disjunction) = pretty_disjunction(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Exists) = pretty_exists(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Reduce) = pretty_reduce(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.Term}) = pretty_terms(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Term) = pretty_term(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Var) = pretty_var(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Not) = pretty_not(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FFI) = pretty_ffi(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::String) = pretty_name(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.Abstraction}) = pretty_ffi_args(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Atom) = pretty_atom(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Pragma) = pretty_pragma(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Primitive) = pretty_primitive(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.RelTerm) = pretty_rel_term(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.RelAtom) = pretty_rel_atom(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Cast) = pretty_cast(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.Attribute}) = pretty_attrs(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Attribute) = pretty_attribute(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Algorithm) = pretty_algorithm(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Script) = pretty_script(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Construct) = pretty_construct(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Loop) = pretty_loop(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.Instruction}) = pretty_init(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Instruction) = pretty_instruction(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Assign) = pretty_assign(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Upsert) = pretty_upsert(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Tuple{Proto.Abstraction, Int64}) = pretty_abstraction_with_arity(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Break) = pretty_break(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MonoidDef) = pretty_monoid_def(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Monoid) = pretty_monoid(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.OrMonoid) = pretty_or_monoid(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MinMonoid) = pretty_min_monoid(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MaxMonoid) = pretty_max_monoid(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.SumMonoid) = pretty_sum_monoid(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MonusDef) = pretty_monus_def(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Constraint) = pretty_constraint(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.Var}) = pretty_functional_dependency_keys(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Data) = pretty_data(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.EDB) = pretty_edb(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{String}) = pretty_edb_path(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.var"#Type"}) = pretty_edb_types(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeRelation) = pretty_betree_relation(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeInfo) = pretty_betree_info(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVData) = pretty_csv_data(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVLocator) = pretty_csvlocator(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVConfig) = pretty_csv_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.GNFColumn}) = pretty_gnf_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.GNFColumn) = pretty_gnf_column(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Undefine) = pretty_undefine(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Context) = pretty_context(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Snapshot) = pretty_snapshot(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.Read}) = pretty_epoch_reads(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Read) = pretty_read(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Demand) = pretty_demand(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Output) = pretty_output(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.WhatIf) = pretty_what_if(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Abort) = pretty_abort(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Export) = pretty_export(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportCSVConfig) = pretty_export_csv_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.ExportCSVColumn}) = pretty_export_csv_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportCSVColumn) = pretty_export_csv_column(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DebugInfo) = pretty_debug_info(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeConfig) = pretty_be_tree_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeLocator) = pretty_be_tree_locator(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DecimalValue) = pretty_decimal_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FunctionalDependency) = pretty_functional_dependency(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Int128Value) = pretty_int128_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MissingValue) = pretty_missing_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.UInt128Value) = pretty_u_int128_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.IVMConfig) = pretty_ivm_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MaintenanceLevel.T) = pretty_maintenance_level(pp, x)

# --- pprint API ---

struct LQPSyntaxWithDebug{T<:LQPSyntax}
    syntax::T
    debug_info::Proto.DebugInfo
end

function pprint(io::IO, x::LQPSyntax; max_width::Int=92, constant_formatter::ConstantFormatter=DEFAULT_CONSTANT_FORMATTER)
    pp = PrettyPrinter(max_width=max_width, constant_formatter=constant_formatter)
    _pprint_dispatch(pp, x)
    newline(pp)
    print(io, get_output(pp))
    return nothing
end

function pprint(io::IO, x::LQPSyntaxWithDebug; max_width::Int=92, constant_formatter::ConstantFormatter=DEFAULT_CONSTANT_FORMATTER)
    pp = PrettyPrinter(max_width=max_width, print_symbolic_relation_ids=false, constant_formatter=constant_formatter)
    di = x.debug_info
    for (rid, name) in zip(di.ids, di.orig_names)
        pp.debug_info[(rid.id_low, rid.id_high)] = name
    end
    _pprint_dispatch(pp, x.syntax)
    newline(pp)
    write_debug_info(pp)
    print(io, get_output(pp))
    return nothing
end

function pprint(io::IO, x::LQPFragmentId)
    print(io, String(copy(x.id)))
    return nothing
end

pprint(x; max_width::Int=92, constant_formatter::ConstantFormatter=DEFAULT_CONSTANT_FORMATTER) = pprint(stdout, x; max_width=max_width, constant_formatter=constant_formatter)

function pretty(msg::Proto.Transaction; max_width::Int=92, constant_formatter::ConstantFormatter=DEFAULT_CONSTANT_FORMATTER)::String
    pp = PrettyPrinter(max_width=max_width, constant_formatter=constant_formatter)
    pretty_transaction(pp, msg)
    newline(pp)
    return get_output(pp)
end

function pretty_debug(msg::Proto.Transaction; max_width::Int=92, constant_formatter::ConstantFormatter=DEFAULT_CONSTANT_FORMATTER)::String
    pp = PrettyPrinter(max_width=max_width, print_symbolic_relation_ids=false, constant_formatter=constant_formatter)
    pretty_transaction(pp, msg)
    newline(pp)
    write_debug_info(pp)
    return get_output(pp)
end

# Export ConstantFormatter types for user customization
export ConstantFormatter, DefaultConstantFormatter, DEFAULT_CONSTANT_FORMATTER
# Export format functions for users to extend
export format_decimal, format_int128, format_uint128, format_int, format_float, format_string, format_bool
# Export legacy format functions for backward compatibility
export format_float64, format_string_value
# Export pretty printing API
export pprint, pretty, pretty_debug
export PrettyPrinter
# Export internal helpers for testing
export indent_level, indent!, try_flat

end # module Pretty
