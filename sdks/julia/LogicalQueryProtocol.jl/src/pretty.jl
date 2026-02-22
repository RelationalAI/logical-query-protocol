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
    _t1721 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1721
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1722 = Proto.Value(value=OneOf(:int_value, v))
    return _t1722
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1723 = Proto.Value(value=OneOf(:float_value, v))
    return _t1723
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1724 = Proto.Value(value=OneOf(:string_value, v))
    return _t1724
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1725 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1725
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1726 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1726
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1727 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1727,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1728 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1728,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1729 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1729,))
            end
        end
    end
    _t1730 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1730,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1731 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1731,))
    _t1732 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1732,))
    if msg.new_line != ""
        _t1733 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1733,))
    end
    _t1734 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1734,))
    _t1735 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1735,))
    _t1736 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1736,))
    if msg.comment != ""
        _t1737 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1737,))
    end
    for missing_string in msg.missing_strings
        _t1738 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1738,))
    end
    _t1739 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1739,))
    _t1740 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1740,))
    _t1741 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1741,))
    if msg.partition_size_mb != 0
        _t1742 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1742,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1743 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1743,))
    _t1744 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1744,))
    _t1745 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1745,))
    _t1746 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1746,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1747 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1747,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1748 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1748,))
        end
    end
    _t1749 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1749,))
    _t1750 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1750,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1751 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1751,))
    end
    if !isnothing(msg.compression)
        _t1752 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1752,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1753 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1753,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1754 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1754,))
    end
    if !isnothing(msg.syntax_delim)
        _t1755 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1755,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1756 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1756,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1757 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1757,))
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
                    write(pp, format_string(pp, unwrapped677))
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
                        write(pp, format_int(pp, unwrapped675))
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
                            write(pp, format_float(pp, unwrapped673))
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
        write(pp, format_int(pp, field685))
        newline(pp)
        field686 = unwrapped_fields684[2]
        write(pp, format_int(pp, field686))
        newline(pp)
        field687 = unwrapped_fields684[3]
        write(pp, format_int(pp, field687))
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
        write(pp, format_int(pp, field691))
        newline(pp)
        field692 = unwrapped_fields690[2]
        write(pp, format_int(pp, field692))
        newline(pp)
        field693 = unwrapped_fields690[3]
        write(pp, format_int(pp, field693))
        newline(pp)
        field694 = unwrapped_fields690[4]
        write(pp, format_int(pp, field694))
        newline(pp)
        field695 = unwrapped_fields690[5]
        write(pp, format_int(pp, field695))
        newline(pp)
        field696 = unwrapped_fields690[6]
        write(pp, format_int(pp, field696))
        field697 = unwrapped_fields690[7]
        if !isnothing(field697)
            newline(pp)
            opt_val698 = field697
            write(pp, format_int(pp, opt_val698))
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
            if !isnothing(relation_id_to_string(pp, _dollar_dollar))
                _t1374 = deconstruct_relation_id_string(pp, _dollar_dollar)
                _t1373 = _t1374
            else
                _t1373 = nothing
            end
            return _t1373
        end
        _t1375 = _t1372(msg)
        deconstruct_result762 = _t1375
        if !isnothing(deconstruct_result762)
            unwrapped763 = deconstruct_result762
            write(pp, ":")
            write(pp, unwrapped763)
        else
            function _t1376(_dollar_dollar)
                _t1377 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
                return _t1377
            end
            _t1378 = _t1376(msg)
            deconstruct_result760 = _t1378
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
        function _t1379(_dollar_dollar)
            _t1380 = deconstruct_bindings(pp, _dollar_dollar)
            return (_t1380, _dollar_dollar.value,)
        end
        _t1381 = _t1379(msg)
        fields765 = _t1381
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
        function _t1382(_dollar_dollar)
            if !isempty(_dollar_dollar[2])
                _t1383 = _dollar_dollar[2]
            else
                _t1383 = nothing
            end
            return (_dollar_dollar[1], _t1383,)
        end
        _t1384 = _t1382(msg)
        fields770 = _t1384
        unwrapped_fields771 = fields770
        write(pp, "[")
        indent!(pp)
        field772 = unwrapped_fields771[1]
        for (i1385, elem773) in enumerate(field772)
            i774 = i1385 - 1
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
        function _t1386(_dollar_dollar)
            return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        end
        _t1387 = _t1386(msg)
        fields778 = _t1387
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
        function _t1388(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
                _t1389 = _get_oneof_field(_dollar_dollar, :unspecified_type)
            else
                _t1389 = nothing
            end
            return _t1389
        end
        _t1390 = _t1388(msg)
        deconstruct_result803 = _t1390
        if !isnothing(deconstruct_result803)
            unwrapped804 = deconstruct_result803
            pretty_unspecified_type(pp, unwrapped804)
        else
            function _t1391(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                    _t1392 = _get_oneof_field(_dollar_dollar, :string_type)
                else
                    _t1392 = nothing
                end
                return _t1392
            end
            _t1393 = _t1391(msg)
            deconstruct_result801 = _t1393
            if !isnothing(deconstruct_result801)
                unwrapped802 = deconstruct_result801
                pretty_string_type(pp, unwrapped802)
            else
                function _t1394(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                        _t1395 = _get_oneof_field(_dollar_dollar, :int_type)
                    else
                        _t1395 = nothing
                    end
                    return _t1395
                end
                _t1396 = _t1394(msg)
                deconstruct_result799 = _t1396
                if !isnothing(deconstruct_result799)
                    unwrapped800 = deconstruct_result799
                    pretty_int_type(pp, unwrapped800)
                else
                    function _t1397(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                            _t1398 = _get_oneof_field(_dollar_dollar, :float_type)
                        else
                            _t1398 = nothing
                        end
                        return _t1398
                    end
                    _t1399 = _t1397(msg)
                    deconstruct_result797 = _t1399
                    if !isnothing(deconstruct_result797)
                        unwrapped798 = deconstruct_result797
                        pretty_float_type(pp, unwrapped798)
                    else
                        function _t1400(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                                _t1401 = _get_oneof_field(_dollar_dollar, :uint128_type)
                            else
                                _t1401 = nothing
                            end
                            return _t1401
                        end
                        _t1402 = _t1400(msg)
                        deconstruct_result795 = _t1402
                        if !isnothing(deconstruct_result795)
                            unwrapped796 = deconstruct_result795
                            pretty_uint128_type(pp, unwrapped796)
                        else
                            function _t1403(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                    _t1404 = _get_oneof_field(_dollar_dollar, :int128_type)
                                else
                                    _t1404 = nothing
                                end
                                return _t1404
                            end
                            _t1405 = _t1403(msg)
                            deconstruct_result793 = _t1405
                            if !isnothing(deconstruct_result793)
                                unwrapped794 = deconstruct_result793
                                pretty_int128_type(pp, unwrapped794)
                            else
                                function _t1406(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                        _t1407 = _get_oneof_field(_dollar_dollar, :date_type)
                                    else
                                        _t1407 = nothing
                                    end
                                    return _t1407
                                end
                                _t1408 = _t1406(msg)
                                deconstruct_result791 = _t1408
                                if !isnothing(deconstruct_result791)
                                    unwrapped792 = deconstruct_result791
                                    pretty_date_type(pp, unwrapped792)
                                else
                                    function _t1409(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                            _t1410 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                        else
                                            _t1410 = nothing
                                        end
                                        return _t1410
                                    end
                                    _t1411 = _t1409(msg)
                                    deconstruct_result789 = _t1411
                                    if !isnothing(deconstruct_result789)
                                        unwrapped790 = deconstruct_result789
                                        pretty_datetime_type(pp, unwrapped790)
                                    else
                                        function _t1412(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                                _t1413 = _get_oneof_field(_dollar_dollar, :missing_type)
                                            else
                                                _t1413 = nothing
                                            end
                                            return _t1413
                                        end
                                        _t1414 = _t1412(msg)
                                        deconstruct_result787 = _t1414
                                        if !isnothing(deconstruct_result787)
                                            unwrapped788 = deconstruct_result787
                                            pretty_missing_type(pp, unwrapped788)
                                        else
                                            function _t1415(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                    _t1416 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                                else
                                                    _t1416 = nothing
                                                end
                                                return _t1416
                                            end
                                            _t1417 = _t1415(msg)
                                            deconstruct_result785 = _t1417
                                            if !isnothing(deconstruct_result785)
                                                unwrapped786 = deconstruct_result785
                                                pretty_decimal_type(pp, unwrapped786)
                                            else
                                                function _t1418(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                        _t1419 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                    else
                                                        _t1419 = nothing
                                                    end
                                                    return _t1419
                                                end
                                                _t1420 = _t1418(msg)
                                                deconstruct_result783 = _t1420
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
        function _t1421(_dollar_dollar)
            return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        end
        _t1422 = _t1421(msg)
        fields815 = _t1422
        unwrapped_fields816 = fields815
        write(pp, "(")
        write(pp, "DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field817 = unwrapped_fields816[1]
        write(pp, format_int(pp, field817))
        newline(pp)
        field818 = unwrapped_fields816[2]
        write(pp, format_int(pp, field818))
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
            for (i1423, elem822) in enumerate(fields821)
                i823 = i1423 - 1
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
        function _t1424(_dollar_dollar)
            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                _t1425 = _get_oneof_field(_dollar_dollar, :conjunction)
            else
                _t1425 = nothing
            end
            return _t1425
        end
        _t1426 = _t1424(msg)
        deconstruct_result849 = _t1426
        if !isnothing(deconstruct_result849)
            unwrapped850 = deconstruct_result849
            pretty_true(pp, unwrapped850)
        else
            function _t1427(_dollar_dollar)
                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                    _t1428 = _get_oneof_field(_dollar_dollar, :disjunction)
                else
                    _t1428 = nothing
                end
                return _t1428
            end
            _t1429 = _t1427(msg)
            deconstruct_result847 = _t1429
            if !isnothing(deconstruct_result847)
                unwrapped848 = deconstruct_result847
                pretty_false(pp, unwrapped848)
            else
                function _t1430(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("exists"))
                        _t1431 = _get_oneof_field(_dollar_dollar, :exists)
                    else
                        _t1431 = nothing
                    end
                    return _t1431
                end
                _t1432 = _t1430(msg)
                deconstruct_result845 = _t1432
                if !isnothing(deconstruct_result845)
                    unwrapped846 = deconstruct_result845
                    pretty_exists(pp, unwrapped846)
                else
                    function _t1433(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                            _t1434 = _get_oneof_field(_dollar_dollar, :reduce)
                        else
                            _t1434 = nothing
                        end
                        return _t1434
                    end
                    _t1435 = _t1433(msg)
                    deconstruct_result843 = _t1435
                    if !isnothing(deconstruct_result843)
                        unwrapped844 = deconstruct_result843
                        pretty_reduce(pp, unwrapped844)
                    else
                        function _t1436(_dollar_dollar)
                            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                                _t1437 = _get_oneof_field(_dollar_dollar, :conjunction)
                            else
                                _t1437 = nothing
                            end
                            return _t1437
                        end
                        _t1438 = _t1436(msg)
                        deconstruct_result841 = _t1438
                        if !isnothing(deconstruct_result841)
                            unwrapped842 = deconstruct_result841
                            pretty_conjunction(pp, unwrapped842)
                        else
                            function _t1439(_dollar_dollar)
                                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                    _t1440 = _get_oneof_field(_dollar_dollar, :disjunction)
                                else
                                    _t1440 = nothing
                                end
                                return _t1440
                            end
                            _t1441 = _t1439(msg)
                            deconstruct_result839 = _t1441
                            if !isnothing(deconstruct_result839)
                                unwrapped840 = deconstruct_result839
                                pretty_disjunction(pp, unwrapped840)
                            else
                                function _t1442(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("not"))
                                        _t1443 = _get_oneof_field(_dollar_dollar, :not)
                                    else
                                        _t1443 = nothing
                                    end
                                    return _t1443
                                end
                                _t1444 = _t1442(msg)
                                deconstruct_result837 = _t1444
                                if !isnothing(deconstruct_result837)
                                    unwrapped838 = deconstruct_result837
                                    pretty_not(pp, unwrapped838)
                                else
                                    function _t1445(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                            _t1446 = _get_oneof_field(_dollar_dollar, :ffi)
                                        else
                                            _t1446 = nothing
                                        end
                                        return _t1446
                                    end
                                    _t1447 = _t1445(msg)
                                    deconstruct_result835 = _t1447
                                    if !isnothing(deconstruct_result835)
                                        unwrapped836 = deconstruct_result835
                                        pretty_ffi(pp, unwrapped836)
                                    else
                                        function _t1448(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                                _t1449 = _get_oneof_field(_dollar_dollar, :atom)
                                            else
                                                _t1449 = nothing
                                            end
                                            return _t1449
                                        end
                                        _t1450 = _t1448(msg)
                                        deconstruct_result833 = _t1450
                                        if !isnothing(deconstruct_result833)
                                            unwrapped834 = deconstruct_result833
                                            pretty_atom(pp, unwrapped834)
                                        else
                                            function _t1451(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                    _t1452 = _get_oneof_field(_dollar_dollar, :pragma)
                                                else
                                                    _t1452 = nothing
                                                end
                                                return _t1452
                                            end
                                            _t1453 = _t1451(msg)
                                            deconstruct_result831 = _t1453
                                            if !isnothing(deconstruct_result831)
                                                unwrapped832 = deconstruct_result831
                                                pretty_pragma(pp, unwrapped832)
                                            else
                                                function _t1454(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                        _t1455 = _get_oneof_field(_dollar_dollar, :primitive)
                                                    else
                                                        _t1455 = nothing
                                                    end
                                                    return _t1455
                                                end
                                                _t1456 = _t1454(msg)
                                                deconstruct_result829 = _t1456
                                                if !isnothing(deconstruct_result829)
                                                    unwrapped830 = deconstruct_result829
                                                    pretty_primitive(pp, unwrapped830)
                                                else
                                                    function _t1457(_dollar_dollar)
                                                        if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                            _t1458 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                        else
                                                            _t1458 = nothing
                                                        end
                                                        return _t1458
                                                    end
                                                    _t1459 = _t1457(msg)
                                                    deconstruct_result827 = _t1459
                                                    if !isnothing(deconstruct_result827)
                                                        unwrapped828 = deconstruct_result827
                                                        pretty_rel_atom(pp, unwrapped828)
                                                    else
                                                        function _t1460(_dollar_dollar)
                                                            if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                                _t1461 = _get_oneof_field(_dollar_dollar, :cast)
                                                            else
                                                                _t1461 = nothing
                                                            end
                                                            return _t1461
                                                        end
                                                        _t1462 = _t1460(msg)
                                                        deconstruct_result825 = _t1462
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
        function _t1463(_dollar_dollar)
            _t1464 = deconstruct_bindings(pp, _dollar_dollar.body)
            return (_t1464, _dollar_dollar.body.value,)
        end
        _t1465 = _t1463(msg)
        fields854 = _t1465
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
        function _t1466(_dollar_dollar)
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        end
        _t1467 = _t1466(msg)
        fields859 = _t1467
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
            for (i1468, elem866) in enumerate(fields865)
                i867 = i1468 - 1
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
        function _t1469(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("var"))
                _t1470 = _get_oneof_field(_dollar_dollar, :var)
            else
                _t1470 = nothing
            end
            return _t1470
        end
        _t1471 = _t1469(msg)
        deconstruct_result871 = _t1471
        if !isnothing(deconstruct_result871)
            unwrapped872 = deconstruct_result871
            pretty_var(pp, unwrapped872)
        else
            function _t1472(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("constant"))
                    _t1473 = _get_oneof_field(_dollar_dollar, :constant)
                else
                    _t1473 = nothing
                end
                return _t1473
            end
            _t1474 = _t1472(msg)
            deconstruct_result869 = _t1474
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
        function _t1475(_dollar_dollar)
            return _dollar_dollar.name
        end
        _t1476 = _t1475(msg)
        fields874 = _t1476
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
        function _t1477(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1478 = _t1477(msg)
        fields879 = _t1478
        unwrapped_fields880 = fields879
        write(pp, "(")
        write(pp, "and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields880)
            newline(pp)
            for (i1479, elem881) in enumerate(unwrapped_fields880)
                i882 = i1479 - 1
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
        function _t1480(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1481 = _t1480(msg)
        fields884 = _t1481
        unwrapped_fields885 = fields884
        write(pp, "(")
        write(pp, "or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields885)
            newline(pp)
            for (i1482, elem886) in enumerate(unwrapped_fields885)
                i887 = i1482 - 1
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
        function _t1483(_dollar_dollar)
            return _dollar_dollar.arg
        end
        _t1484 = _t1483(msg)
        fields889 = _t1484
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
        function _t1485(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        end
        _t1486 = _t1485(msg)
        fields892 = _t1486
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
            for (i1487, elem901) in enumerate(fields900)
                i902 = i1487 - 1
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
        function _t1488(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1489 = _t1488(msg)
        fields904 = _t1489
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
            for (i1490, elem908) in enumerate(field907)
                i909 = i1490 - 1
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
        function _t1491(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1492 = _t1491(msg)
        fields911 = _t1492
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
            for (i1493, elem915) in enumerate(field914)
                i916 = i1493 - 1
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
        function _t1494(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1495 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1495 = nothing
            end
            return _t1495
        end
        _t1496 = _t1494(msg)
        guard_result932 = _t1496
        if !isnothing(guard_result932)
            pretty_eq(pp, msg)
        else
            function _t1497(_dollar_dollar)
                if _dollar_dollar.name == "rel_primitive_lt_monotype"
                    _t1498 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1498 = nothing
                end
                return _t1498
            end
            _t1499 = _t1497(msg)
            guard_result931 = _t1499
            if !isnothing(guard_result931)
                pretty_lt(pp, msg)
            else
                function _t1500(_dollar_dollar)
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                        _t1501 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1501 = nothing
                    end
                    return _t1501
                end
                _t1502 = _t1500(msg)
                guard_result930 = _t1502
                if !isnothing(guard_result930)
                    pretty_lt_eq(pp, msg)
                else
                    function _t1503(_dollar_dollar)
                        if _dollar_dollar.name == "rel_primitive_gt_monotype"
                            _t1504 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1504 = nothing
                        end
                        return _t1504
                    end
                    _t1505 = _t1503(msg)
                    guard_result929 = _t1505
                    if !isnothing(guard_result929)
                        pretty_gt(pp, msg)
                    else
                        function _t1506(_dollar_dollar)
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                                _t1507 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                            else
                                _t1507 = nothing
                            end
                            return _t1507
                        end
                        _t1508 = _t1506(msg)
                        guard_result928 = _t1508
                        if !isnothing(guard_result928)
                            pretty_gt_eq(pp, msg)
                        else
                            function _t1509(_dollar_dollar)
                                if _dollar_dollar.name == "rel_primitive_add_monotype"
                                    _t1510 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1510 = nothing
                                end
                                return _t1510
                            end
                            _t1511 = _t1509(msg)
                            guard_result927 = _t1511
                            if !isnothing(guard_result927)
                                pretty_add(pp, msg)
                            else
                                function _t1512(_dollar_dollar)
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                        _t1513 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1513 = nothing
                                    end
                                    return _t1513
                                end
                                _t1514 = _t1512(msg)
                                guard_result926 = _t1514
                                if !isnothing(guard_result926)
                                    pretty_minus(pp, msg)
                                else
                                    function _t1515(_dollar_dollar)
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                            _t1516 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1516 = nothing
                                        end
                                        return _t1516
                                    end
                                    _t1517 = _t1515(msg)
                                    guard_result925 = _t1517
                                    if !isnothing(guard_result925)
                                        pretty_multiply(pp, msg)
                                    else
                                        function _t1518(_dollar_dollar)
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                                _t1519 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                            else
                                                _t1519 = nothing
                                            end
                                            return _t1519
                                        end
                                        _t1520 = _t1518(msg)
                                        guard_result924 = _t1520
                                        if !isnothing(guard_result924)
                                            pretty_divide(pp, msg)
                                        else
                                            function _t1521(_dollar_dollar)
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            end
                                            _t1522 = _t1521(msg)
                                            fields918 = _t1522
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
                                                for (i1523, elem922) in enumerate(field921)
                                                    i923 = i1523 - 1
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
        function _t1524(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1525 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1525 = nothing
            end
            return _t1525
        end
        _t1526 = _t1524(msg)
        fields934 = _t1526
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
        function _t1527(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1528 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1528 = nothing
            end
            return _t1528
        end
        _t1529 = _t1527(msg)
        fields939 = _t1529
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
        function _t1530(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                _t1531 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1531 = nothing
            end
            return _t1531
        end
        _t1532 = _t1530(msg)
        fields944 = _t1532
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
        function _t1533(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_monotype"
                _t1534 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1534 = nothing
            end
            return _t1534
        end
        _t1535 = _t1533(msg)
        fields949 = _t1535
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
        function _t1536(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                _t1537 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1537 = nothing
            end
            return _t1537
        end
        _t1538 = _t1536(msg)
        fields954 = _t1538
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
        function _t1539(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_add_monotype"
                _t1540 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1540 = nothing
            end
            return _t1540
        end
        _t1541 = _t1539(msg)
        fields959 = _t1541
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
        function _t1542(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                _t1543 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1543 = nothing
            end
            return _t1543
        end
        _t1544 = _t1542(msg)
        fields965 = _t1544
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
        function _t1545(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                _t1546 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1546 = nothing
            end
            return _t1546
        end
        _t1547 = _t1545(msg)
        fields971 = _t1547
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
        function _t1548(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                _t1549 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1549 = nothing
            end
            return _t1549
        end
        _t1550 = _t1548(msg)
        fields977 = _t1550
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
        function _t1551(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
                _t1552 = _get_oneof_field(_dollar_dollar, :specialized_value)
            else
                _t1552 = nothing
            end
            return _t1552
        end
        _t1553 = _t1551(msg)
        deconstruct_result985 = _t1553
        if !isnothing(deconstruct_result985)
            unwrapped986 = deconstruct_result985
            pretty_specialized_value(pp, unwrapped986)
        else
            function _t1554(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("term"))
                    _t1555 = _get_oneof_field(_dollar_dollar, :term)
                else
                    _t1555 = nothing
                end
                return _t1555
            end
            _t1556 = _t1554(msg)
            deconstruct_result983 = _t1556
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
        function _t1557(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1558 = _t1557(msg)
        fields990 = _t1558
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
            for (i1559, elem994) in enumerate(field993)
                i995 = i1559 - 1
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
        function _t1560(_dollar_dollar)
            return (_dollar_dollar.input, _dollar_dollar.result,)
        end
        _t1561 = _t1560(msg)
        fields997 = _t1561
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
            for (i1562, elem1003) in enumerate(fields1002)
                i1004 = i1562 - 1
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
        function _t1563(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args,)
        end
        _t1564 = _t1563(msg)
        fields1006 = _t1564
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
            for (i1565, elem1010) in enumerate(field1009)
                i1011 = i1565 - 1
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
        function _t1566(_dollar_dollar)
            return (_dollar_dollar.var"#global", _dollar_dollar.body,)
        end
        _t1567 = _t1566(msg)
        fields1013 = _t1567
        unwrapped_fields1014 = fields1013
        write(pp, "(")
        write(pp, "algorithm")
        indent_sexp!(pp)
        field1015 = unwrapped_fields1014[1]
        if !isempty(field1015)
            newline(pp)
            for (i1568, elem1016) in enumerate(field1015)
                i1017 = i1568 - 1
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
        function _t1569(_dollar_dollar)
            return _dollar_dollar.constructs
        end
        _t1570 = _t1569(msg)
        fields1020 = _t1570
        unwrapped_fields1021 = fields1020
        write(pp, "(")
        write(pp, "script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1021)
            newline(pp)
            for (i1571, elem1022) in enumerate(unwrapped_fields1021)
                i1023 = i1571 - 1
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
        function _t1572(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("loop"))
                _t1573 = _get_oneof_field(_dollar_dollar, :loop)
            else
                _t1573 = nothing
            end
            return _t1573
        end
        _t1574 = _t1572(msg)
        deconstruct_result1027 = _t1574
        if !isnothing(deconstruct_result1027)
            unwrapped1028 = deconstruct_result1027
            pretty_loop(pp, unwrapped1028)
        else
            function _t1575(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                    _t1576 = _get_oneof_field(_dollar_dollar, :instruction)
                else
                    _t1576 = nothing
                end
                return _t1576
            end
            _t1577 = _t1575(msg)
            deconstruct_result1025 = _t1577
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
        function _t1578(_dollar_dollar)
            return (_dollar_dollar.init, _dollar_dollar.body,)
        end
        _t1579 = _t1578(msg)
        fields1030 = _t1579
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
            for (i1580, elem1036) in enumerate(fields1035)
                i1037 = i1580 - 1
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
        function _t1581(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("assign"))
                _t1582 = _get_oneof_field(_dollar_dollar, :assign)
            else
                _t1582 = nothing
            end
            return _t1582
        end
        _t1583 = _t1581(msg)
        deconstruct_result1047 = _t1583
        if !isnothing(deconstruct_result1047)
            unwrapped1048 = deconstruct_result1047
            pretty_assign(pp, unwrapped1048)
        else
            function _t1584(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                    _t1585 = _get_oneof_field(_dollar_dollar, :upsert)
                else
                    _t1585 = nothing
                end
                return _t1585
            end
            _t1586 = _t1584(msg)
            deconstruct_result1045 = _t1586
            if !isnothing(deconstruct_result1045)
                unwrapped1046 = deconstruct_result1045
                pretty_upsert(pp, unwrapped1046)
            else
                function _t1587(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("#break"))
                        _t1588 = _get_oneof_field(_dollar_dollar, :var"#break")
                    else
                        _t1588 = nothing
                    end
                    return _t1588
                end
                _t1589 = _t1587(msg)
                deconstruct_result1043 = _t1589
                if !isnothing(deconstruct_result1043)
                    unwrapped1044 = deconstruct_result1043
                    pretty_break(pp, unwrapped1044)
                else
                    function _t1590(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                            _t1591 = _get_oneof_field(_dollar_dollar, :monoid_def)
                        else
                            _t1591 = nothing
                        end
                        return _t1591
                    end
                    _t1592 = _t1590(msg)
                    deconstruct_result1041 = _t1592
                    if !isnothing(deconstruct_result1041)
                        unwrapped1042 = deconstruct_result1041
                        pretty_monoid_def(pp, unwrapped1042)
                    else
                        function _t1593(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                                _t1594 = _get_oneof_field(_dollar_dollar, :monus_def)
                            else
                                _t1594 = nothing
                            end
                            return _t1594
                        end
                        _t1595 = _t1593(msg)
                        deconstruct_result1039 = _t1595
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
        function _t1596(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1597 = _dollar_dollar.attrs
            else
                _t1597 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1597,)
        end
        _t1598 = _t1596(msg)
        fields1050 = _t1598
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
        function _t1599(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1600 = _dollar_dollar.attrs
            else
                _t1600 = nothing
            end
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1600,)
        end
        _t1601 = _t1599(msg)
        fields1057 = _t1601
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
        function _t1602(_dollar_dollar)
            _t1603 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
            return (_t1603, _dollar_dollar[1].value,)
        end
        _t1604 = _t1602(msg)
        fields1064 = _t1604
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
        function _t1605(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1606 = _dollar_dollar.attrs
            else
                _t1606 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1606,)
        end
        _t1607 = _t1605(msg)
        fields1069 = _t1607
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
        function _t1608(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1609 = _dollar_dollar.attrs
            else
                _t1609 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1609,)
        end
        _t1610 = _t1608(msg)
        fields1076 = _t1610
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
        function _t1611(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
                _t1612 = _get_oneof_field(_dollar_dollar, :or_monoid)
            else
                _t1612 = nothing
            end
            return _t1612
        end
        _t1613 = _t1611(msg)
        deconstruct_result1090 = _t1613
        if !isnothing(deconstruct_result1090)
            unwrapped1091 = deconstruct_result1090
            pretty_or_monoid(pp, unwrapped1091)
        else
            function _t1614(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                    _t1615 = _get_oneof_field(_dollar_dollar, :min_monoid)
                else
                    _t1615 = nothing
                end
                return _t1615
            end
            _t1616 = _t1614(msg)
            deconstruct_result1088 = _t1616
            if !isnothing(deconstruct_result1088)
                unwrapped1089 = deconstruct_result1088
                pretty_min_monoid(pp, unwrapped1089)
            else
                function _t1617(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                        _t1618 = _get_oneof_field(_dollar_dollar, :max_monoid)
                    else
                        _t1618 = nothing
                    end
                    return _t1618
                end
                _t1619 = _t1617(msg)
                deconstruct_result1086 = _t1619
                if !isnothing(deconstruct_result1086)
                    unwrapped1087 = deconstruct_result1086
                    pretty_max_monoid(pp, unwrapped1087)
                else
                    function _t1620(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                            _t1621 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                        else
                            _t1621 = nothing
                        end
                        return _t1621
                    end
                    _t1622 = _t1620(msg)
                    deconstruct_result1084 = _t1622
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
        function _t1623(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1624 = _t1623(msg)
        fields1094 = _t1624
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
        function _t1625(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1626 = _t1625(msg)
        fields1097 = _t1626
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
        function _t1627(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1628 = _t1627(msg)
        fields1100 = _t1628
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
        function _t1629(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1630 = _dollar_dollar.attrs
            else
                _t1630 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1630,)
        end
        _t1631 = _t1629(msg)
        fields1103 = _t1631
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
        function _t1632(_dollar_dollar)
            return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        end
        _t1633 = _t1632(msg)
        fields1111 = _t1633
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
            for (i1634, elem1119) in enumerate(fields1118)
                i1120 = i1634 - 1
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
            for (i1635, elem1123) in enumerate(fields1122)
                i1124 = i1635 - 1
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
        function _t1636(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("rel_edb"))
                _t1637 = _get_oneof_field(_dollar_dollar, :rel_edb)
            else
                _t1637 = nothing
            end
            return _t1637
        end
        _t1638 = _t1636(msg)
        deconstruct_result1130 = _t1638
        if !isnothing(deconstruct_result1130)
            unwrapped1131 = deconstruct_result1130
            pretty_rel_edb(pp, unwrapped1131)
        else
            function _t1639(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                    _t1640 = _get_oneof_field(_dollar_dollar, :betree_relation)
                else
                    _t1640 = nothing
                end
                return _t1640
            end
            _t1641 = _t1639(msg)
            deconstruct_result1128 = _t1641
            if !isnothing(deconstruct_result1128)
                unwrapped1129 = deconstruct_result1128
                pretty_betree_relation(pp, unwrapped1129)
            else
                function _t1642(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                        _t1643 = _get_oneof_field(_dollar_dollar, :csv_data)
                    else
                        _t1643 = nothing
                    end
                    return _t1643
                end
                _t1644 = _t1642(msg)
                deconstruct_result1126 = _t1644
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
        function _t1645(_dollar_dollar)
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        end
        _t1646 = _t1645(msg)
        fields1133 = _t1646
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
        for (i1647, elem1140) in enumerate(fields1139)
            i1141 = i1647 - 1
            if (i1141 > 0)
                newline(pp)
            end
            write(pp, format_string(pp, elem1140))
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
        for (i1648, elem1144) in enumerate(fields1143)
            i1145 = i1648 - 1
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
        function _t1649(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        end
        _t1650 = _t1649(msg)
        fields1147 = _t1650
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
        function _t1651(_dollar_dollar)
            _t1652 = deconstruct_betree_info_config(pp, _dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1652,)
        end
        _t1653 = _t1651(msg)
        fields1152 = _t1653
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
            for (i1654, elem1159) in enumerate(fields1158)
                i1160 = i1654 - 1
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
            for (i1655, elem1163) in enumerate(fields1162)
                i1164 = i1655 - 1
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
        function _t1656(_dollar_dollar)
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        end
        _t1657 = _t1656(msg)
        fields1166 = _t1657
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
        function _t1658(_dollar_dollar)
            if !isempty(_dollar_dollar.paths)
                _t1659 = _dollar_dollar.paths
            else
                _t1659 = nothing
            end
            if String(copy(_dollar_dollar.inline_data)) != ""
                _t1660 = String(copy(_dollar_dollar.inline_data))
            else
                _t1660 = nothing
            end
            return (_t1659, _t1660,)
        end
        _t1661 = _t1658(msg)
        fields1173 = _t1661
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
            for (i1662, elem1181) in enumerate(fields1180)
                i1182 = i1662 - 1
                if (i1182 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1181))
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
        write(pp, format_string(pp, fields1184))
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
        function _t1663(_dollar_dollar)
            _t1664 = deconstruct_csv_config(pp, _dollar_dollar)
            return _t1664
        end
        _t1665 = _t1663(msg)
        fields1186 = _t1665
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
            for (i1666, elem1190) in enumerate(fields1189)
                i1191 = i1666 - 1
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
        function _t1667(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        end
        _t1668 = _t1667(msg)
        fields1193 = _t1668
        unwrapped_fields1194 = fields1193
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1195 = unwrapped_fields1194[1]
        write(pp, format_string(pp, field1195))
        newline(pp)
        field1196 = unwrapped_fields1194[2]
        pretty_relation_id(pp, field1196)
        newline(pp)
        write(pp, "[")
        field1197 = unwrapped_fields1194[3]
        for (i1669, elem1198) in enumerate(field1197)
            i1199 = i1669 - 1
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
        write(pp, format_string(pp, fields1201))
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
        function _t1670(_dollar_dollar)
            return _dollar_dollar.fragment_id
        end
        _t1671 = _t1670(msg)
        fields1203 = _t1671
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
        function _t1672(_dollar_dollar)
            return _dollar_dollar.relations
        end
        _t1673 = _t1672(msg)
        fields1206 = _t1673
        unwrapped_fields1207 = fields1206
        write(pp, "(")
        write(pp, "context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1207)
            newline(pp)
            for (i1674, elem1208) in enumerate(unwrapped_fields1207)
                i1209 = i1674 - 1
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
        function _t1675(_dollar_dollar)
            return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        end
        _t1676 = _t1675(msg)
        fields1211 = _t1676
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
            for (i1677, elem1217) in enumerate(fields1216)
                i1218 = i1677 - 1
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
        function _t1678(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("demand"))
                _t1679 = _get_oneof_field(_dollar_dollar, :demand)
            else
                _t1679 = nothing
            end
            return _t1679
        end
        _t1680 = _t1678(msg)
        deconstruct_result1228 = _t1680
        if !isnothing(deconstruct_result1228)
            unwrapped1229 = deconstruct_result1228
            pretty_demand(pp, unwrapped1229)
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
            deconstruct_result1226 = _t1683
            if !isnothing(deconstruct_result1226)
                unwrapped1227 = deconstruct_result1226
                pretty_output(pp, unwrapped1227)
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
                deconstruct_result1224 = _t1686
                if !isnothing(deconstruct_result1224)
                    unwrapped1225 = deconstruct_result1224
                    pretty_what_if(pp, unwrapped1225)
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
                    deconstruct_result1222 = _t1689
                    if !isnothing(deconstruct_result1222)
                        unwrapped1223 = deconstruct_result1222
                        pretty_abort(pp, unwrapped1223)
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
                        deconstruct_result1220 = _t1692
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
        function _t1693(_dollar_dollar)
            return _dollar_dollar.relation_id
        end
        _t1694 = _t1693(msg)
        fields1231 = _t1694
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
        function _t1695(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        end
        _t1696 = _t1695(msg)
        fields1234 = _t1696
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
        function _t1697(_dollar_dollar)
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        end
        _t1698 = _t1697(msg)
        fields1239 = _t1698
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
        function _t1699(_dollar_dollar)
            if _dollar_dollar.name != "abort"
                _t1700 = _dollar_dollar.name
            else
                _t1700 = nothing
            end
            return (_t1700, _dollar_dollar.relation_id,)
        end
        _t1701 = _t1699(msg)
        fields1244 = _t1701
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
        function _t1702(_dollar_dollar)
            return _get_oneof_field(_dollar_dollar, :csv_config)
        end
        _t1703 = _t1702(msg)
        fields1250 = _t1703
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
        function _t1704(_dollar_dollar)
            if length(_dollar_dollar.data_columns) == 0
                _t1705 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else
                _t1705 = nothing
            end
            return _t1705
        end
        _t1706 = _t1704(msg)
        deconstruct_result1258 = _t1706
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
            function _t1707(_dollar_dollar)
                if length(_dollar_dollar.data_columns) != 0
                    _t1709 = deconstruct_export_csv_config(pp, _dollar_dollar)
                    _t1708 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1709,)
                else
                    _t1708 = nothing
                end
                return _t1708
            end
            _t1710 = _t1707(msg)
            deconstruct_result1253 = _t1710
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
        write(pp, format_string(pp, fields1264))
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
        function _t1711(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
                _t1712 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
            else
                _t1712 = nothing
            end
            return _t1712
        end
        _t1713 = _t1711(msg)
        deconstruct_result1268 = _t1713
        if !isnothing(deconstruct_result1268)
            unwrapped1269 = deconstruct_result1268
            write(pp, "(")
            write(pp, "gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1269)
                newline(pp)
                for (i1714, elem1270) in enumerate(unwrapped1269)
                    i1271 = i1714 - 1
                    if (i1271 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1270)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            function _t1715(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                    _t1716 = _get_oneof_field(_dollar_dollar, :table_def)
                else
                    _t1716 = nothing
                end
                return _t1716
            end
            _t1717 = _t1715(msg)
            deconstruct_result1266 = _t1717
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
        function _t1718(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        end
        _t1719 = _t1718(msg)
        fields1273 = _t1719
        unwrapped_fields1274 = fields1273
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1275 = unwrapped_fields1274[1]
        write(pp, format_string(pp, field1275))
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
            for (i1720, elem1279) in enumerate(fields1278)
                i1280 = i1720 - 1
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


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1759, _rid) in enumerate(msg.ids)
        _idx = i1759 - 1
        newline(pp)
        write(pp, "(")
        _t1760 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1760)
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
    for (i1761, _elem) in enumerate(msg.keys)
        _idx = i1761 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values ")
    write(pp, "(")
    for (i1762, _elem) in enumerate(msg.values)
        _idx = i1762 - 1
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

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Proto.ExportCSVColumns)
    write(pp, "(export_csv_columns")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":columns ")
    write(pp, "(")
    for (i1763, _elem) in enumerate(msg.columns)
        _idx = i1763 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.RelEDB) = pretty_rel_edb(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{String}) = pretty_rel_edb_path(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.var"#Type"}) = pretty_rel_edb_types(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeRelation) = pretty_betree_relation(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeInfo) = pretty_betree_info(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVData) = pretty_csv_data(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVLocator) = pretty_csvlocator(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVConfig) = pretty_csv_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.CSVColumn}) = pretty_csv_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVColumn) = pretty_csv_column(pp, x)
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportCSVSource) = pretty_export_csv_source(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportCSVColumn) = pretty_export_csv_column(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.ExportCSVColumn}) = pretty_export_csv_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DebugInfo) = pretty_debug_info(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeConfig) = pretty_be_tree_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeLocator) = pretty_be_tree_locator(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DecimalValue) = pretty_decimal_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FunctionalDependency) = pretty_functional_dependency(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Int128Value) = pretty_int128_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MissingValue) = pretty_missing_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.UInt128Value) = pretty_u_int128_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportCSVColumns) = pretty_export_csv_columns(pp, x)
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
