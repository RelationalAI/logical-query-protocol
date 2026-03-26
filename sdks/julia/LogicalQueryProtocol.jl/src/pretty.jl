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

"""
    format_int32(formatter::ConstantFormatter, pp::PrettyPrinter, v::Int32)::String

Format an Int32 value as a string with the `i32` suffix.

Override this function for custom ConstantFormatter subtypes to customize Int32 formatting.
"""
format_int32(formatter::DefaultConstantFormatter, pp::PrettyPrinter, v::Int32)::String = string(Int64(v)) * "i32"

"""
    format_float32(formatter::ConstantFormatter, pp::PrettyPrinter, v::Float32)::String

Format a Float32 value as a string with the `f32` suffix.

Override this function for custom ConstantFormatter subtypes to customize Float32 formatting.
"""
format_float32(formatter::DefaultConstantFormatter, pp::PrettyPrinter, v::Float32)::String = format_float32_literal(v)

"""
    format_uint32(formatter::ConstantFormatter, pp::PrettyPrinter, v::UInt32)::String

Format a UInt32 value as a string with the `u32` suffix.

Override this function for custom ConstantFormatter subtypes to customize UInt32 formatting.
"""
format_uint32(formatter::DefaultConstantFormatter, pp::PrettyPrinter, v::UInt32)::String = string(Int64(v)) * "u32"

# Fallback methods for custom formatters that don't override all types
# These delegate to the default formatter
format_decimal(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.DecimalValue)::String = format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, msg)
format_int128(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.Int128Value)::String = format_int128(DEFAULT_CONSTANT_FORMATTER, pp, msg)
format_uint128(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.UInt128Value)::String = format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, msg)
format_int(formatter::ConstantFormatter, pp::PrettyPrinter, v::Int64)::String = format_int(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_float(formatter::ConstantFormatter, pp::PrettyPrinter, v::Float64)::String = format_float(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_string(formatter::ConstantFormatter, pp::PrettyPrinter, s::AbstractString)::String = format_string(DEFAULT_CONSTANT_FORMATTER, pp, s)
format_bool(formatter::ConstantFormatter, pp::PrettyPrinter, v::Bool)::String = format_bool(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_int32(formatter::ConstantFormatter, pp::PrettyPrinter, v::Int32)::String = format_int32(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_uint32(formatter::ConstantFormatter, pp::PrettyPrinter, v::UInt32)::String = format_uint32(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_float32(formatter::ConstantFormatter, pp::PrettyPrinter, v::Float32)::String = format_float32(DEFAULT_CONSTANT_FORMATTER, pp, v)

# Convenience methods that use pp.constant_formatter
format_decimal(pp::PrettyPrinter, msg::Proto.DecimalValue)::String = format_decimal(pp.constant_formatter, pp, msg)
format_int128(pp::PrettyPrinter, msg::Proto.Int128Value)::String = format_int128(pp.constant_formatter, pp, msg)
format_uint128(pp::PrettyPrinter, msg::Proto.UInt128Value)::String = format_uint128(pp.constant_formatter, pp, msg)
format_int(pp::PrettyPrinter, v::Int64)::String = format_int(pp.constant_formatter, pp, v)
format_float(pp::PrettyPrinter, v::Float64)::String = format_float(pp.constant_formatter, pp, v)
format_string(pp::PrettyPrinter, s::AbstractString)::String = format_string(pp.constant_formatter, pp, s)
format_bool(pp::PrettyPrinter, v::Bool)::String = format_bool(pp.constant_formatter, pp, v)
format_int32(pp::PrettyPrinter, v::Int32)::String = format_int32(pp.constant_formatter, pp, v)
format_uint32(pp::PrettyPrinter, v::UInt32)::String = format_uint32(pp.constant_formatter, pp, v)
format_float32(pp::PrettyPrinter, v::Float32)::String = format_float32(pp.constant_formatter, pp, v)

function format_float32_literal(v::Float32)::String
    isinf(v) && return "inf32"
    isnan(v) && return "nan32"
    return lowercase(string(v)) * "f32"
end

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
    _t1712 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1712
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1713 = Proto.Value(value=OneOf(:int_value, v))
    return _t1713
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1714 = Proto.Value(value=OneOf(:float_value, v))
    return _t1714
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1715 = Proto.Value(value=OneOf(:string_value, v))
    return _t1715
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1716 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1716
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1717 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1717
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1718 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1718,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1719 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1719,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1720 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1720,))
            end
        end
    end
    _t1721 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1721,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1722 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1722,))
    _t1723 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1723,))
    if msg.new_line != ""
        _t1724 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1724,))
    end
    _t1725 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1725,))
    _t1726 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1726,))
    _t1727 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1727,))
    if msg.comment != ""
        _t1728 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1728,))
    end
    for missing_string in msg.missing_strings
        _t1729 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1729,))
    end
    _t1730 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1730,))
    _t1731 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1731,))
    _t1732 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1732,))
    if msg.partition_size_mb != 0
        _t1733 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1733,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1734 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1734,))
    _t1735 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1735,))
    _t1736 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1736,))
    _t1737 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1737,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1738 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1738,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1739 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1739,))
        end
    end
    _t1740 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1740,))
    _t1741 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1741,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1742 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1742,))
    end
    if !isnothing(msg.compression)
        _t1743 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1743,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1744 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1744,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1745 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1745,))
    end
    if !isnothing(msg.syntax_delim)
        _t1746 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1746,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1747 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1747,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1748 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1748,))
    end
    return sort(result)
end

function deconstruct_iceberg_config_scope_optional(pp::PrettyPrinter, msg::Proto.IcebergConfig)::Union{Nothing, String}
    if _has_proto_field(msg, Symbol("scope"))
        return msg.scope
    else
        _t1749 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if _has_proto_field(msg, Symbol("to_snapshot"))
        return msg.to_snapshot
    else
        _t1750 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1751 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1751,))
    end
    if msg.target_file_size_bytes != 0
        _t1752 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1752,))
    end
    if msg.compression != ""
        _t1753 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1753,))
    end
    if length(result) == 0
        return nothing
    else
        _t1754 = nothing
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
        _t1755 = nothing
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
    flat776 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat776)
        write(pp, flat776)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1534 = _dollar_dollar.configure
        else
            _t1534 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1535 = _dollar_dollar.sync
        else
            _t1535 = nothing
        end
        fields767 = (_t1534, _t1535, _dollar_dollar.epochs,)
        unwrapped_fields768 = fields767
        write(pp, "(transaction")
        indent_sexp!(pp)
        field769 = unwrapped_fields768[1]
        if !isnothing(field769)
            newline(pp)
            opt_val770 = field769
            pretty_configure(pp, opt_val770)
        end
        field771 = unwrapped_fields768[2]
        if !isnothing(field771)
            newline(pp)
            opt_val772 = field771
            pretty_sync(pp, opt_val772)
        end
        field773 = unwrapped_fields768[3]
        if !isempty(field773)
            newline(pp)
            for (i1536, elem774) in enumerate(field773)
                i775 = i1536 - 1
                if (i775 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem774)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat779 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat779)
        write(pp, flat779)
        return nothing
    else
        _dollar_dollar = msg
        _t1537 = deconstruct_configure(pp, _dollar_dollar)
        fields777 = _t1537
        unwrapped_fields778 = fields777
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields778)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat783 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat783)
        write(pp, flat783)
        return nothing
    else
        fields780 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields780)
            newline(pp)
            for (i1538, elem781) in enumerate(fields780)
                i782 = i1538 - 1
                if (i782 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem781)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat788 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat788)
        write(pp, flat788)
        return nothing
    else
        _dollar_dollar = msg
        fields784 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields785 = fields784
        write(pp, ":")
        field786 = unwrapped_fields785[1]
        write(pp, field786)
        write(pp, " ")
        field787 = unwrapped_fields785[2]
        pretty_raw_value(pp, field787)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat814 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat814)
        write(pp, flat814)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1539 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1539 = nothing
        end
        deconstruct_result812 = _t1539
        if !isnothing(deconstruct_result812)
            unwrapped813 = deconstruct_result812
            pretty_raw_date(pp, unwrapped813)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1540 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1540 = nothing
            end
            deconstruct_result810 = _t1540
            if !isnothing(deconstruct_result810)
                unwrapped811 = deconstruct_result810
                pretty_raw_datetime(pp, unwrapped811)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1541 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1541 = nothing
                end
                deconstruct_result808 = _t1541
                if !isnothing(deconstruct_result808)
                    unwrapped809 = deconstruct_result808
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped809))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1542 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1542 = nothing
                    end
                    deconstruct_result806 = _t1542
                    if !isnothing(deconstruct_result806)
                        unwrapped807 = deconstruct_result806
                        write(pp, (string(Int64(unwrapped807)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1543 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1543 = nothing
                        end
                        deconstruct_result804 = _t1543
                        if !isnothing(deconstruct_result804)
                            unwrapped805 = deconstruct_result804
                            write(pp, string(unwrapped805))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1544 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1544 = nothing
                            end
                            deconstruct_result802 = _t1544
                            if !isnothing(deconstruct_result802)
                                unwrapped803 = deconstruct_result802
                                write(pp, format_float32_literal(unwrapped803))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1545 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1545 = nothing
                                end
                                deconstruct_result800 = _t1545
                                if !isnothing(deconstruct_result800)
                                    unwrapped801 = deconstruct_result800
                                    write(pp, lowercase(string(unwrapped801)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1546 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1546 = nothing
                                    end
                                    deconstruct_result798 = _t1546
                                    if !isnothing(deconstruct_result798)
                                        unwrapped799 = deconstruct_result798
                                        write(pp, (string(Int64(unwrapped799)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1547 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1547 = nothing
                                        end
                                        deconstruct_result796 = _t1547
                                        if !isnothing(deconstruct_result796)
                                            unwrapped797 = deconstruct_result796
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped797))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1548 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1548 = nothing
                                            end
                                            deconstruct_result794 = _t1548
                                            if !isnothing(deconstruct_result794)
                                                unwrapped795 = deconstruct_result794
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped795))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1549 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1549 = nothing
                                                end
                                                deconstruct_result792 = _t1549
                                                if !isnothing(deconstruct_result792)
                                                    unwrapped793 = deconstruct_result792
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped793))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1550 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1550 = nothing
                                                    end
                                                    deconstruct_result790 = _t1550
                                                    if !isnothing(deconstruct_result790)
                                                        unwrapped791 = deconstruct_result790
                                                        pretty_boolean_value(pp, unwrapped791)
                                                    else
                                                        fields789 = msg
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
            end
        end
    end
    return nothing
end

function pretty_raw_date(pp::PrettyPrinter, msg::Proto.DateValue)
    flat820 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat820)
        write(pp, flat820)
        return nothing
    else
        _dollar_dollar = msg
        fields815 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields816 = fields815
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field817 = unwrapped_fields816[1]
        write(pp, string(field817))
        newline(pp)
        field818 = unwrapped_fields816[2]
        write(pp, string(field818))
        newline(pp)
        field819 = unwrapped_fields816[3]
        write(pp, string(field819))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat831 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat831)
        write(pp, flat831)
        return nothing
    else
        _dollar_dollar = msg
        fields821 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields822 = fields821
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field823 = unwrapped_fields822[1]
        write(pp, string(field823))
        newline(pp)
        field824 = unwrapped_fields822[2]
        write(pp, string(field824))
        newline(pp)
        field825 = unwrapped_fields822[3]
        write(pp, string(field825))
        newline(pp)
        field826 = unwrapped_fields822[4]
        write(pp, string(field826))
        newline(pp)
        field827 = unwrapped_fields822[5]
        write(pp, string(field827))
        newline(pp)
        field828 = unwrapped_fields822[6]
        write(pp, string(field828))
        field829 = unwrapped_fields822[7]
        if !isnothing(field829)
            newline(pp)
            opt_val830 = field829
            write(pp, string(opt_val830))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1551 = ()
    else
        _t1551 = nothing
    end
    deconstruct_result834 = _t1551
    if !isnothing(deconstruct_result834)
        unwrapped835 = deconstruct_result834
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1552 = ()
        else
            _t1552 = nothing
        end
        deconstruct_result832 = _t1552
        if !isnothing(deconstruct_result832)
            unwrapped833 = deconstruct_result832
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat840 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat840)
        write(pp, flat840)
        return nothing
    else
        _dollar_dollar = msg
        fields836 = _dollar_dollar.fragments
        unwrapped_fields837 = fields836
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields837)
            newline(pp)
            for (i1553, elem838) in enumerate(unwrapped_fields837)
                i839 = i1553 - 1
                if (i839 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem838)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat843 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat843)
        write(pp, flat843)
        return nothing
    else
        _dollar_dollar = msg
        fields841 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields842 = fields841
        write(pp, ":")
        write(pp, unwrapped_fields842)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat850 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat850)
        write(pp, flat850)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1554 = _dollar_dollar.writes
        else
            _t1554 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1555 = _dollar_dollar.reads
        else
            _t1555 = nothing
        end
        fields844 = (_t1554, _t1555,)
        unwrapped_fields845 = fields844
        write(pp, "(epoch")
        indent_sexp!(pp)
        field846 = unwrapped_fields845[1]
        if !isnothing(field846)
            newline(pp)
            opt_val847 = field846
            pretty_epoch_writes(pp, opt_val847)
        end
        field848 = unwrapped_fields845[2]
        if !isnothing(field848)
            newline(pp)
            opt_val849 = field848
            pretty_epoch_reads(pp, opt_val849)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat854 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat854)
        write(pp, flat854)
        return nothing
    else
        fields851 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields851)
            newline(pp)
            for (i1556, elem852) in enumerate(fields851)
                i853 = i1556 - 1
                if (i853 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem852)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat863 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat863)
        write(pp, flat863)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1557 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1557 = nothing
        end
        deconstruct_result861 = _t1557
        if !isnothing(deconstruct_result861)
            unwrapped862 = deconstruct_result861
            pretty_define(pp, unwrapped862)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1558 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1558 = nothing
            end
            deconstruct_result859 = _t1558
            if !isnothing(deconstruct_result859)
                unwrapped860 = deconstruct_result859
                pretty_undefine(pp, unwrapped860)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1559 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1559 = nothing
                end
                deconstruct_result857 = _t1559
                if !isnothing(deconstruct_result857)
                    unwrapped858 = deconstruct_result857
                    pretty_context(pp, unwrapped858)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1560 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1560 = nothing
                    end
                    deconstruct_result855 = _t1560
                    if !isnothing(deconstruct_result855)
                        unwrapped856 = deconstruct_result855
                        pretty_snapshot(pp, unwrapped856)
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
    flat866 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat866)
        write(pp, flat866)
        return nothing
    else
        _dollar_dollar = msg
        fields864 = _dollar_dollar.fragment
        unwrapped_fields865 = fields864
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields865)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat873 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat873)
        write(pp, flat873)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields867 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields868 = fields867
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field869 = unwrapped_fields868[1]
        pretty_new_fragment_id(pp, field869)
        field870 = unwrapped_fields868[2]
        if !isempty(field870)
            newline(pp)
            for (i1561, elem871) in enumerate(field870)
                i872 = i1561 - 1
                if (i872 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem871)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat875 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat875)
        write(pp, flat875)
        return nothing
    else
        fields874 = msg
        pretty_fragment_id(pp, fields874)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat884 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat884)
        write(pp, flat884)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1562 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1562 = nothing
        end
        deconstruct_result882 = _t1562
        if !isnothing(deconstruct_result882)
            unwrapped883 = deconstruct_result882
            pretty_def(pp, unwrapped883)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1563 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1563 = nothing
            end
            deconstruct_result880 = _t1563
            if !isnothing(deconstruct_result880)
                unwrapped881 = deconstruct_result880
                pretty_algorithm(pp, unwrapped881)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1564 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1564 = nothing
                end
                deconstruct_result878 = _t1564
                if !isnothing(deconstruct_result878)
                    unwrapped879 = deconstruct_result878
                    pretty_constraint(pp, unwrapped879)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1565 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1565 = nothing
                    end
                    deconstruct_result876 = _t1565
                    if !isnothing(deconstruct_result876)
                        unwrapped877 = deconstruct_result876
                        pretty_data(pp, unwrapped877)
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
    flat891 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat891)
        write(pp, flat891)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1566 = _dollar_dollar.attrs
        else
            _t1566 = nothing
        end
        fields885 = (_dollar_dollar.name, _dollar_dollar.body, _t1566,)
        unwrapped_fields886 = fields885
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field887 = unwrapped_fields886[1]
        pretty_relation_id(pp, field887)
        newline(pp)
        field888 = unwrapped_fields886[2]
        pretty_abstraction(pp, field888)
        field889 = unwrapped_fields886[3]
        if !isnothing(field889)
            newline(pp)
            opt_val890 = field889
            pretty_attrs(pp, opt_val890)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat896 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat896)
        write(pp, flat896)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1568 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1567 = _t1568
        else
            _t1567 = nothing
        end
        deconstruct_result894 = _t1567
        if !isnothing(deconstruct_result894)
            unwrapped895 = deconstruct_result894
            write(pp, ":")
            write(pp, unwrapped895)
        else
            _dollar_dollar = msg
            _t1569 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result892 = _t1569
            if !isnothing(deconstruct_result892)
                unwrapped893 = deconstruct_result892
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped893))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat901 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat901)
        write(pp, flat901)
        return nothing
    else
        _dollar_dollar = msg
        _t1570 = deconstruct_bindings(pp, _dollar_dollar)
        fields897 = (_t1570, _dollar_dollar.value,)
        unwrapped_fields898 = fields897
        write(pp, "(")
        indent!(pp)
        field899 = unwrapped_fields898[1]
        pretty_bindings(pp, field899)
        newline(pp)
        field900 = unwrapped_fields898[2]
        pretty_formula(pp, field900)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat909 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat909)
        write(pp, flat909)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1571 = _dollar_dollar[2]
        else
            _t1571 = nothing
        end
        fields902 = (_dollar_dollar[1], _t1571,)
        unwrapped_fields903 = fields902
        write(pp, "[")
        indent!(pp)
        field904 = unwrapped_fields903[1]
        for (i1572, elem905) in enumerate(field904)
            i906 = i1572 - 1
            if (i906 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem905)
        end
        field907 = unwrapped_fields903[2]
        if !isnothing(field907)
            newline(pp)
            opt_val908 = field907
            pretty_value_bindings(pp, opt_val908)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat914 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat914)
        write(pp, flat914)
        return nothing
    else
        _dollar_dollar = msg
        fields910 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields911 = fields910
        field912 = unwrapped_fields911[1]
        write(pp, field912)
        write(pp, "::")
        field913 = unwrapped_fields911[2]
        pretty_type(pp, field913)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat943 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat943)
        write(pp, flat943)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1573 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1573 = nothing
        end
        deconstruct_result941 = _t1573
        if !isnothing(deconstruct_result941)
            unwrapped942 = deconstruct_result941
            pretty_unspecified_type(pp, unwrapped942)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1574 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1574 = nothing
            end
            deconstruct_result939 = _t1574
            if !isnothing(deconstruct_result939)
                unwrapped940 = deconstruct_result939
                pretty_string_type(pp, unwrapped940)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1575 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1575 = nothing
                end
                deconstruct_result937 = _t1575
                if !isnothing(deconstruct_result937)
                    unwrapped938 = deconstruct_result937
                    pretty_int_type(pp, unwrapped938)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1576 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1576 = nothing
                    end
                    deconstruct_result935 = _t1576
                    if !isnothing(deconstruct_result935)
                        unwrapped936 = deconstruct_result935
                        pretty_float_type(pp, unwrapped936)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1577 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1577 = nothing
                        end
                        deconstruct_result933 = _t1577
                        if !isnothing(deconstruct_result933)
                            unwrapped934 = deconstruct_result933
                            pretty_uint128_type(pp, unwrapped934)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1578 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1578 = nothing
                            end
                            deconstruct_result931 = _t1578
                            if !isnothing(deconstruct_result931)
                                unwrapped932 = deconstruct_result931
                                pretty_int128_type(pp, unwrapped932)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1579 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1579 = nothing
                                end
                                deconstruct_result929 = _t1579
                                if !isnothing(deconstruct_result929)
                                    unwrapped930 = deconstruct_result929
                                    pretty_date_type(pp, unwrapped930)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1580 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1580 = nothing
                                    end
                                    deconstruct_result927 = _t1580
                                    if !isnothing(deconstruct_result927)
                                        unwrapped928 = deconstruct_result927
                                        pretty_datetime_type(pp, unwrapped928)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1581 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1581 = nothing
                                        end
                                        deconstruct_result925 = _t1581
                                        if !isnothing(deconstruct_result925)
                                            unwrapped926 = deconstruct_result925
                                            pretty_missing_type(pp, unwrapped926)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1582 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1582 = nothing
                                            end
                                            deconstruct_result923 = _t1582
                                            if !isnothing(deconstruct_result923)
                                                unwrapped924 = deconstruct_result923
                                                pretty_decimal_type(pp, unwrapped924)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1583 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1583 = nothing
                                                end
                                                deconstruct_result921 = _t1583
                                                if !isnothing(deconstruct_result921)
                                                    unwrapped922 = deconstruct_result921
                                                    pretty_boolean_type(pp, unwrapped922)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1584 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1584 = nothing
                                                    end
                                                    deconstruct_result919 = _t1584
                                                    if !isnothing(deconstruct_result919)
                                                        unwrapped920 = deconstruct_result919
                                                        pretty_int32_type(pp, unwrapped920)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1585 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1585 = nothing
                                                        end
                                                        deconstruct_result917 = _t1585
                                                        if !isnothing(deconstruct_result917)
                                                            unwrapped918 = deconstruct_result917
                                                            pretty_float32_type(pp, unwrapped918)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1586 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1586 = nothing
                                                            end
                                                            deconstruct_result915 = _t1586
                                                            if !isnothing(deconstruct_result915)
                                                                unwrapped916 = deconstruct_result915
                                                                pretty_uint32_type(pp, unwrapped916)
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
            end
        end
    end
    return nothing
end

function pretty_unspecified_type(pp::PrettyPrinter, msg::Proto.UnspecifiedType)
    fields944 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields945 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields946 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields947 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields948 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields949 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields950 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields951 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields952 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat957 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat957)
        write(pp, flat957)
        return nothing
    else
        _dollar_dollar = msg
        fields953 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields954 = fields953
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field955 = unwrapped_fields954[1]
        write(pp, string(field955))
        newline(pp)
        field956 = unwrapped_fields954[2]
        write(pp, string(field956))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields958 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields959 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields960 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields961 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat965 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat965)
        write(pp, flat965)
        return nothing
    else
        fields962 = msg
        write(pp, "|")
        if !isempty(fields962)
            write(pp, " ")
            for (i1587, elem963) in enumerate(fields962)
                i964 = i1587 - 1
                if (i964 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem963)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat992 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat992)
        write(pp, flat992)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1588 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1588 = nothing
        end
        deconstruct_result990 = _t1588
        if !isnothing(deconstruct_result990)
            unwrapped991 = deconstruct_result990
            pretty_true(pp, unwrapped991)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1589 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1589 = nothing
            end
            deconstruct_result988 = _t1589
            if !isnothing(deconstruct_result988)
                unwrapped989 = deconstruct_result988
                pretty_false(pp, unwrapped989)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1590 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1590 = nothing
                end
                deconstruct_result986 = _t1590
                if !isnothing(deconstruct_result986)
                    unwrapped987 = deconstruct_result986
                    pretty_exists(pp, unwrapped987)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1591 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1591 = nothing
                    end
                    deconstruct_result984 = _t1591
                    if !isnothing(deconstruct_result984)
                        unwrapped985 = deconstruct_result984
                        pretty_reduce(pp, unwrapped985)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1592 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1592 = nothing
                        end
                        deconstruct_result982 = _t1592
                        if !isnothing(deconstruct_result982)
                            unwrapped983 = deconstruct_result982
                            pretty_conjunction(pp, unwrapped983)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1593 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1593 = nothing
                            end
                            deconstruct_result980 = _t1593
                            if !isnothing(deconstruct_result980)
                                unwrapped981 = deconstruct_result980
                                pretty_disjunction(pp, unwrapped981)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1594 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1594 = nothing
                                end
                                deconstruct_result978 = _t1594
                                if !isnothing(deconstruct_result978)
                                    unwrapped979 = deconstruct_result978
                                    pretty_not(pp, unwrapped979)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1595 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1595 = nothing
                                    end
                                    deconstruct_result976 = _t1595
                                    if !isnothing(deconstruct_result976)
                                        unwrapped977 = deconstruct_result976
                                        pretty_ffi(pp, unwrapped977)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1596 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1596 = nothing
                                        end
                                        deconstruct_result974 = _t1596
                                        if !isnothing(deconstruct_result974)
                                            unwrapped975 = deconstruct_result974
                                            pretty_atom(pp, unwrapped975)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1597 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1597 = nothing
                                            end
                                            deconstruct_result972 = _t1597
                                            if !isnothing(deconstruct_result972)
                                                unwrapped973 = deconstruct_result972
                                                pretty_pragma(pp, unwrapped973)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1598 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1598 = nothing
                                                end
                                                deconstruct_result970 = _t1598
                                                if !isnothing(deconstruct_result970)
                                                    unwrapped971 = deconstruct_result970
                                                    pretty_primitive(pp, unwrapped971)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1599 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1599 = nothing
                                                    end
                                                    deconstruct_result968 = _t1599
                                                    if !isnothing(deconstruct_result968)
                                                        unwrapped969 = deconstruct_result968
                                                        pretty_rel_atom(pp, unwrapped969)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1600 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1600 = nothing
                                                        end
                                                        deconstruct_result966 = _t1600
                                                        if !isnothing(deconstruct_result966)
                                                            unwrapped967 = deconstruct_result966
                                                            pretty_cast(pp, unwrapped967)
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
    fields993 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields994 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat999 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat999)
        write(pp, flat999)
        return nothing
    else
        _dollar_dollar = msg
        _t1601 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields995 = (_t1601, _dollar_dollar.body.value,)
        unwrapped_fields996 = fields995
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field997 = unwrapped_fields996[1]
        pretty_bindings(pp, field997)
        newline(pp)
        field998 = unwrapped_fields996[2]
        pretty_formula(pp, field998)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1005 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1005)
        write(pp, flat1005)
        return nothing
    else
        _dollar_dollar = msg
        fields1000 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1001 = fields1000
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1002 = unwrapped_fields1001[1]
        pretty_abstraction(pp, field1002)
        newline(pp)
        field1003 = unwrapped_fields1001[2]
        pretty_abstraction(pp, field1003)
        newline(pp)
        field1004 = unwrapped_fields1001[3]
        pretty_terms(pp, field1004)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1009 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1009)
        write(pp, flat1009)
        return nothing
    else
        fields1006 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1006)
            newline(pp)
            for (i1602, elem1007) in enumerate(fields1006)
                i1008 = i1602 - 1
                if (i1008 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1007)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1014 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1014)
        write(pp, flat1014)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1603 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1603 = nothing
        end
        deconstruct_result1012 = _t1603
        if !isnothing(deconstruct_result1012)
            unwrapped1013 = deconstruct_result1012
            pretty_var(pp, unwrapped1013)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1604 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1604 = nothing
            end
            deconstruct_result1010 = _t1604
            if !isnothing(deconstruct_result1010)
                unwrapped1011 = deconstruct_result1010
                pretty_value(pp, unwrapped1011)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1017 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1017)
        write(pp, flat1017)
        return nothing
    else
        _dollar_dollar = msg
        fields1015 = _dollar_dollar.name
        unwrapped_fields1016 = fields1015
        write(pp, unwrapped_fields1016)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1043 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1043)
        write(pp, flat1043)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1605 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1605 = nothing
        end
        deconstruct_result1041 = _t1605
        if !isnothing(deconstruct_result1041)
            unwrapped1042 = deconstruct_result1041
            pretty_date(pp, unwrapped1042)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1606 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1606 = nothing
            end
            deconstruct_result1039 = _t1606
            if !isnothing(deconstruct_result1039)
                unwrapped1040 = deconstruct_result1039
                pretty_datetime(pp, unwrapped1040)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1607 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1607 = nothing
                end
                deconstruct_result1037 = _t1607
                if !isnothing(deconstruct_result1037)
                    unwrapped1038 = deconstruct_result1037
                    write(pp, format_string(pp, unwrapped1038))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1608 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1608 = nothing
                    end
                    deconstruct_result1035 = _t1608
                    if !isnothing(deconstruct_result1035)
                        unwrapped1036 = deconstruct_result1035
                        write(pp, format_int32(pp, unwrapped1036))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1609 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1609 = nothing
                        end
                        deconstruct_result1033 = _t1609
                        if !isnothing(deconstruct_result1033)
                            unwrapped1034 = deconstruct_result1033
                            write(pp, format_int(pp, unwrapped1034))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1610 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1610 = nothing
                            end
                            deconstruct_result1031 = _t1610
                            if !isnothing(deconstruct_result1031)
                                unwrapped1032 = deconstruct_result1031
                                write(pp, format_float32(pp, unwrapped1032))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1611 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1611 = nothing
                                end
                                deconstruct_result1029 = _t1611
                                if !isnothing(deconstruct_result1029)
                                    unwrapped1030 = deconstruct_result1029
                                    write(pp, format_float(pp, unwrapped1030))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1612 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1612 = nothing
                                    end
                                    deconstruct_result1027 = _t1612
                                    if !isnothing(deconstruct_result1027)
                                        unwrapped1028 = deconstruct_result1027
                                        write(pp, format_uint32(pp, unwrapped1028))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1613 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1613 = nothing
                                        end
                                        deconstruct_result1025 = _t1613
                                        if !isnothing(deconstruct_result1025)
                                            unwrapped1026 = deconstruct_result1025
                                            write(pp, format_uint128(pp, unwrapped1026))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1614 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1614 = nothing
                                            end
                                            deconstruct_result1023 = _t1614
                                            if !isnothing(deconstruct_result1023)
                                                unwrapped1024 = deconstruct_result1023
                                                write(pp, format_int128(pp, unwrapped1024))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1615 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1615 = nothing
                                                end
                                                deconstruct_result1021 = _t1615
                                                if !isnothing(deconstruct_result1021)
                                                    unwrapped1022 = deconstruct_result1021
                                                    write(pp, format_decimal(pp, unwrapped1022))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1616 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1616 = nothing
                                                    end
                                                    deconstruct_result1019 = _t1616
                                                    if !isnothing(deconstruct_result1019)
                                                        unwrapped1020 = deconstruct_result1019
                                                        pretty_boolean_value(pp, unwrapped1020)
                                                    else
                                                        fields1018 = msg
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
            end
        end
    end
    return nothing
end

function pretty_date(pp::PrettyPrinter, msg::Proto.DateValue)
    flat1049 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1049)
        write(pp, flat1049)
        return nothing
    else
        _dollar_dollar = msg
        fields1044 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1045 = fields1044
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1046 = unwrapped_fields1045[1]
        write(pp, format_int(pp, field1046))
        newline(pp)
        field1047 = unwrapped_fields1045[2]
        write(pp, format_int(pp, field1047))
        newline(pp)
        field1048 = unwrapped_fields1045[3]
        write(pp, format_int(pp, field1048))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1060 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1060)
        write(pp, flat1060)
        return nothing
    else
        _dollar_dollar = msg
        fields1050 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1051 = fields1050
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1052 = unwrapped_fields1051[1]
        write(pp, format_int(pp, field1052))
        newline(pp)
        field1053 = unwrapped_fields1051[2]
        write(pp, format_int(pp, field1053))
        newline(pp)
        field1054 = unwrapped_fields1051[3]
        write(pp, format_int(pp, field1054))
        newline(pp)
        field1055 = unwrapped_fields1051[4]
        write(pp, format_int(pp, field1055))
        newline(pp)
        field1056 = unwrapped_fields1051[5]
        write(pp, format_int(pp, field1056))
        newline(pp)
        field1057 = unwrapped_fields1051[6]
        write(pp, format_int(pp, field1057))
        field1058 = unwrapped_fields1051[7]
        if !isnothing(field1058)
            newline(pp)
            opt_val1059 = field1058
            write(pp, format_int(pp, opt_val1059))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1065 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1065)
        write(pp, flat1065)
        return nothing
    else
        _dollar_dollar = msg
        fields1061 = _dollar_dollar.args
        unwrapped_fields1062 = fields1061
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1062)
            newline(pp)
            for (i1617, elem1063) in enumerate(unwrapped_fields1062)
                i1064 = i1617 - 1
                if (i1064 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1063)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1070 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1070)
        write(pp, flat1070)
        return nothing
    else
        _dollar_dollar = msg
        fields1066 = _dollar_dollar.args
        unwrapped_fields1067 = fields1066
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1067)
            newline(pp)
            for (i1618, elem1068) in enumerate(unwrapped_fields1067)
                i1069 = i1618 - 1
                if (i1069 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1068)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1073 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1073)
        write(pp, flat1073)
        return nothing
    else
        _dollar_dollar = msg
        fields1071 = _dollar_dollar.arg
        unwrapped_fields1072 = fields1071
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1072)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1079 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1079)
        write(pp, flat1079)
        return nothing
    else
        _dollar_dollar = msg
        fields1074 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1075 = fields1074
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1076 = unwrapped_fields1075[1]
        pretty_name(pp, field1076)
        newline(pp)
        field1077 = unwrapped_fields1075[2]
        pretty_ffi_args(pp, field1077)
        newline(pp)
        field1078 = unwrapped_fields1075[3]
        pretty_terms(pp, field1078)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1081 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1081)
        write(pp, flat1081)
        return nothing
    else
        fields1080 = msg
        write(pp, ":")
        write(pp, fields1080)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1085 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1085)
        write(pp, flat1085)
        return nothing
    else
        fields1082 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1082)
            newline(pp)
            for (i1619, elem1083) in enumerate(fields1082)
                i1084 = i1619 - 1
                if (i1084 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1083)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1092 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        _dollar_dollar = msg
        fields1086 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1087 = fields1086
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1088 = unwrapped_fields1087[1]
        pretty_relation_id(pp, field1088)
        field1089 = unwrapped_fields1087[2]
        if !isempty(field1089)
            newline(pp)
            for (i1620, elem1090) in enumerate(field1089)
                i1091 = i1620 - 1
                if (i1091 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1090)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1099 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1099)
        write(pp, flat1099)
        return nothing
    else
        _dollar_dollar = msg
        fields1093 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1094 = fields1093
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1095 = unwrapped_fields1094[1]
        pretty_name(pp, field1095)
        field1096 = unwrapped_fields1094[2]
        if !isempty(field1096)
            newline(pp)
            for (i1621, elem1097) in enumerate(field1096)
                i1098 = i1621 - 1
                if (i1098 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1097)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1115 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1115)
        write(pp, flat1115)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1622 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1622 = nothing
        end
        guard_result1114 = _t1622
        if !isnothing(guard_result1114)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1623 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1623 = nothing
            end
            guard_result1113 = _t1623
            if !isnothing(guard_result1113)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1624 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1624 = nothing
                end
                guard_result1112 = _t1624
                if !isnothing(guard_result1112)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1625 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1625 = nothing
                    end
                    guard_result1111 = _t1625
                    if !isnothing(guard_result1111)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1626 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1626 = nothing
                        end
                        guard_result1110 = _t1626
                        if !isnothing(guard_result1110)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1627 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1627 = nothing
                            end
                            guard_result1109 = _t1627
                            if !isnothing(guard_result1109)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1628 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1628 = nothing
                                end
                                guard_result1108 = _t1628
                                if !isnothing(guard_result1108)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1629 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1629 = nothing
                                    end
                                    guard_result1107 = _t1629
                                    if !isnothing(guard_result1107)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1630 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1630 = nothing
                                        end
                                        guard_result1106 = _t1630
                                        if !isnothing(guard_result1106)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1100 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1101 = fields1100
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1102 = unwrapped_fields1101[1]
                                            pretty_name(pp, field1102)
                                            field1103 = unwrapped_fields1101[2]
                                            if !isempty(field1103)
                                                newline(pp)
                                                for (i1631, elem1104) in enumerate(field1103)
                                                    i1105 = i1631 - 1
                                                    if (i1105 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1104)
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
    flat1120 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1120)
        write(pp, flat1120)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1632 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1632 = nothing
        end
        fields1116 = _t1632
        unwrapped_fields1117 = fields1116
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1118 = unwrapped_fields1117[1]
        pretty_term(pp, field1118)
        newline(pp)
        field1119 = unwrapped_fields1117[2]
        pretty_term(pp, field1119)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1125 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1125)
        write(pp, flat1125)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1633 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1633 = nothing
        end
        fields1121 = _t1633
        unwrapped_fields1122 = fields1121
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1123 = unwrapped_fields1122[1]
        pretty_term(pp, field1123)
        newline(pp)
        field1124 = unwrapped_fields1122[2]
        pretty_term(pp, field1124)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1130 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1130)
        write(pp, flat1130)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1634 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1634 = nothing
        end
        fields1126 = _t1634
        unwrapped_fields1127 = fields1126
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1128 = unwrapped_fields1127[1]
        pretty_term(pp, field1128)
        newline(pp)
        field1129 = unwrapped_fields1127[2]
        pretty_term(pp, field1129)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1135 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1135)
        write(pp, flat1135)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1635 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1635 = nothing
        end
        fields1131 = _t1635
        unwrapped_fields1132 = fields1131
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1133 = unwrapped_fields1132[1]
        pretty_term(pp, field1133)
        newline(pp)
        field1134 = unwrapped_fields1132[2]
        pretty_term(pp, field1134)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1140 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1140)
        write(pp, flat1140)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1636 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1636 = nothing
        end
        fields1136 = _t1636
        unwrapped_fields1137 = fields1136
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1138 = unwrapped_fields1137[1]
        pretty_term(pp, field1138)
        newline(pp)
        field1139 = unwrapped_fields1137[2]
        pretty_term(pp, field1139)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1146 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1146)
        write(pp, flat1146)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1637 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1637 = nothing
        end
        fields1141 = _t1637
        unwrapped_fields1142 = fields1141
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1143 = unwrapped_fields1142[1]
        pretty_term(pp, field1143)
        newline(pp)
        field1144 = unwrapped_fields1142[2]
        pretty_term(pp, field1144)
        newline(pp)
        field1145 = unwrapped_fields1142[3]
        pretty_term(pp, field1145)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1152 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1152)
        write(pp, flat1152)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1638 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1638 = nothing
        end
        fields1147 = _t1638
        unwrapped_fields1148 = fields1147
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1149 = unwrapped_fields1148[1]
        pretty_term(pp, field1149)
        newline(pp)
        field1150 = unwrapped_fields1148[2]
        pretty_term(pp, field1150)
        newline(pp)
        field1151 = unwrapped_fields1148[3]
        pretty_term(pp, field1151)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1158 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1158)
        write(pp, flat1158)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1639 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1639 = nothing
        end
        fields1153 = _t1639
        unwrapped_fields1154 = fields1153
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1155 = unwrapped_fields1154[1]
        pretty_term(pp, field1155)
        newline(pp)
        field1156 = unwrapped_fields1154[2]
        pretty_term(pp, field1156)
        newline(pp)
        field1157 = unwrapped_fields1154[3]
        pretty_term(pp, field1157)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1164 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1164)
        write(pp, flat1164)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1640 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1640 = nothing
        end
        fields1159 = _t1640
        unwrapped_fields1160 = fields1159
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1161 = unwrapped_fields1160[1]
        pretty_term(pp, field1161)
        newline(pp)
        field1162 = unwrapped_fields1160[2]
        pretty_term(pp, field1162)
        newline(pp)
        field1163 = unwrapped_fields1160[3]
        pretty_term(pp, field1163)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1169 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1169)
        write(pp, flat1169)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1641 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1641 = nothing
        end
        deconstruct_result1167 = _t1641
        if !isnothing(deconstruct_result1167)
            unwrapped1168 = deconstruct_result1167
            pretty_specialized_value(pp, unwrapped1168)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1642 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1642 = nothing
            end
            deconstruct_result1165 = _t1642
            if !isnothing(deconstruct_result1165)
                unwrapped1166 = deconstruct_result1165
                pretty_term(pp, unwrapped1166)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1171 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1171)
        write(pp, flat1171)
        return nothing
    else
        fields1170 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1170)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1178 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1178)
        write(pp, flat1178)
        return nothing
    else
        _dollar_dollar = msg
        fields1172 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1173 = fields1172
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1174 = unwrapped_fields1173[1]
        pretty_name(pp, field1174)
        field1175 = unwrapped_fields1173[2]
        if !isempty(field1175)
            newline(pp)
            for (i1643, elem1176) in enumerate(field1175)
                i1177 = i1643 - 1
                if (i1177 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1176)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1183 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1183)
        write(pp, flat1183)
        return nothing
    else
        _dollar_dollar = msg
        fields1179 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1180 = fields1179
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1181 = unwrapped_fields1180[1]
        pretty_term(pp, field1181)
        newline(pp)
        field1182 = unwrapped_fields1180[2]
        pretty_term(pp, field1182)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1187 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1187)
        write(pp, flat1187)
        return nothing
    else
        fields1184 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1184)
            newline(pp)
            for (i1644, elem1185) in enumerate(fields1184)
                i1186 = i1644 - 1
                if (i1186 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1185)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1194 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1194)
        write(pp, flat1194)
        return nothing
    else
        _dollar_dollar = msg
        fields1188 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1189 = fields1188
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1190 = unwrapped_fields1189[1]
        pretty_name(pp, field1190)
        field1191 = unwrapped_fields1189[2]
        if !isempty(field1191)
            newline(pp)
            for (i1645, elem1192) in enumerate(field1191)
                i1193 = i1645 - 1
                if (i1193 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1192)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1201 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1201)
        write(pp, flat1201)
        return nothing
    else
        _dollar_dollar = msg
        fields1195 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1196 = fields1195
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1197 = unwrapped_fields1196[1]
        if !isempty(field1197)
            newline(pp)
            for (i1646, elem1198) in enumerate(field1197)
                i1199 = i1646 - 1
                if (i1199 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1198)
            end
        end
        newline(pp)
        field1200 = unwrapped_fields1196[2]
        pretty_script(pp, field1200)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1206 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1206)
        write(pp, flat1206)
        return nothing
    else
        _dollar_dollar = msg
        fields1202 = _dollar_dollar.constructs
        unwrapped_fields1203 = fields1202
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1203)
            newline(pp)
            for (i1647, elem1204) in enumerate(unwrapped_fields1203)
                i1205 = i1647 - 1
                if (i1205 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1204)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1211 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1211)
        write(pp, flat1211)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1648 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1648 = nothing
        end
        deconstruct_result1209 = _t1648
        if !isnothing(deconstruct_result1209)
            unwrapped1210 = deconstruct_result1209
            pretty_loop(pp, unwrapped1210)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1649 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1649 = nothing
            end
            deconstruct_result1207 = _t1649
            if !isnothing(deconstruct_result1207)
                unwrapped1208 = deconstruct_result1207
                pretty_instruction(pp, unwrapped1208)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1216 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1216)
        write(pp, flat1216)
        return nothing
    else
        _dollar_dollar = msg
        fields1212 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1213 = fields1212
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1214 = unwrapped_fields1213[1]
        pretty_init(pp, field1214)
        newline(pp)
        field1215 = unwrapped_fields1213[2]
        pretty_script(pp, field1215)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1220 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        fields1217 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1217)
            newline(pp)
            for (i1650, elem1218) in enumerate(fields1217)
                i1219 = i1650 - 1
                if (i1219 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1218)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1231 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1231)
        write(pp, flat1231)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1651 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1651 = nothing
        end
        deconstruct_result1229 = _t1651
        if !isnothing(deconstruct_result1229)
            unwrapped1230 = deconstruct_result1229
            pretty_assign(pp, unwrapped1230)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1652 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1652 = nothing
            end
            deconstruct_result1227 = _t1652
            if !isnothing(deconstruct_result1227)
                unwrapped1228 = deconstruct_result1227
                pretty_upsert(pp, unwrapped1228)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1653 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1653 = nothing
                end
                deconstruct_result1225 = _t1653
                if !isnothing(deconstruct_result1225)
                    unwrapped1226 = deconstruct_result1225
                    pretty_break(pp, unwrapped1226)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1654 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1654 = nothing
                    end
                    deconstruct_result1223 = _t1654
                    if !isnothing(deconstruct_result1223)
                        unwrapped1224 = deconstruct_result1223
                        pretty_monoid_def(pp, unwrapped1224)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1655 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1655 = nothing
                        end
                        deconstruct_result1221 = _t1655
                        if !isnothing(deconstruct_result1221)
                            unwrapped1222 = deconstruct_result1221
                            pretty_monus_def(pp, unwrapped1222)
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
    flat1238 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1238)
        write(pp, flat1238)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1656 = _dollar_dollar.attrs
        else
            _t1656 = nothing
        end
        fields1232 = (_dollar_dollar.name, _dollar_dollar.body, _t1656,)
        unwrapped_fields1233 = fields1232
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1234 = unwrapped_fields1233[1]
        pretty_relation_id(pp, field1234)
        newline(pp)
        field1235 = unwrapped_fields1233[2]
        pretty_abstraction(pp, field1235)
        field1236 = unwrapped_fields1233[3]
        if !isnothing(field1236)
            newline(pp)
            opt_val1237 = field1236
            pretty_attrs(pp, opt_val1237)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1245 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1245)
        write(pp, flat1245)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1657 = _dollar_dollar.attrs
        else
            _t1657 = nothing
        end
        fields1239 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1657,)
        unwrapped_fields1240 = fields1239
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1241 = unwrapped_fields1240[1]
        pretty_relation_id(pp, field1241)
        newline(pp)
        field1242 = unwrapped_fields1240[2]
        pretty_abstraction_with_arity(pp, field1242)
        field1243 = unwrapped_fields1240[3]
        if !isnothing(field1243)
            newline(pp)
            opt_val1244 = field1243
            pretty_attrs(pp, opt_val1244)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1250 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1250)
        write(pp, flat1250)
        return nothing
    else
        _dollar_dollar = msg
        _t1658 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1246 = (_t1658, _dollar_dollar[1].value,)
        unwrapped_fields1247 = fields1246
        write(pp, "(")
        indent!(pp)
        field1248 = unwrapped_fields1247[1]
        pretty_bindings(pp, field1248)
        newline(pp)
        field1249 = unwrapped_fields1247[2]
        pretty_formula(pp, field1249)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1257 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1257)
        write(pp, flat1257)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1659 = _dollar_dollar.attrs
        else
            _t1659 = nothing
        end
        fields1251 = (_dollar_dollar.name, _dollar_dollar.body, _t1659,)
        unwrapped_fields1252 = fields1251
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1253 = unwrapped_fields1252[1]
        pretty_relation_id(pp, field1253)
        newline(pp)
        field1254 = unwrapped_fields1252[2]
        pretty_abstraction(pp, field1254)
        field1255 = unwrapped_fields1252[3]
        if !isnothing(field1255)
            newline(pp)
            opt_val1256 = field1255
            pretty_attrs(pp, opt_val1256)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1265 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1265)
        write(pp, flat1265)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1660 = _dollar_dollar.attrs
        else
            _t1660 = nothing
        end
        fields1258 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1660,)
        unwrapped_fields1259 = fields1258
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1260 = unwrapped_fields1259[1]
        pretty_monoid(pp, field1260)
        newline(pp)
        field1261 = unwrapped_fields1259[2]
        pretty_relation_id(pp, field1261)
        newline(pp)
        field1262 = unwrapped_fields1259[3]
        pretty_abstraction_with_arity(pp, field1262)
        field1263 = unwrapped_fields1259[4]
        if !isnothing(field1263)
            newline(pp)
            opt_val1264 = field1263
            pretty_attrs(pp, opt_val1264)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1274 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1274)
        write(pp, flat1274)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1661 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1661 = nothing
        end
        deconstruct_result1272 = _t1661
        if !isnothing(deconstruct_result1272)
            unwrapped1273 = deconstruct_result1272
            pretty_or_monoid(pp, unwrapped1273)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1662 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1662 = nothing
            end
            deconstruct_result1270 = _t1662
            if !isnothing(deconstruct_result1270)
                unwrapped1271 = deconstruct_result1270
                pretty_min_monoid(pp, unwrapped1271)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1663 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1663 = nothing
                end
                deconstruct_result1268 = _t1663
                if !isnothing(deconstruct_result1268)
                    unwrapped1269 = deconstruct_result1268
                    pretty_max_monoid(pp, unwrapped1269)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1664 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1664 = nothing
                    end
                    deconstruct_result1266 = _t1664
                    if !isnothing(deconstruct_result1266)
                        unwrapped1267 = deconstruct_result1266
                        pretty_sum_monoid(pp, unwrapped1267)
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
    fields1275 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1278 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1278)
        write(pp, flat1278)
        return nothing
    else
        _dollar_dollar = msg
        fields1276 = _dollar_dollar.var"#type"
        unwrapped_fields1277 = fields1276
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1277)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1281 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1281)
        write(pp, flat1281)
        return nothing
    else
        _dollar_dollar = msg
        fields1279 = _dollar_dollar.var"#type"
        unwrapped_fields1280 = fields1279
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1280)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1284 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1284)
        write(pp, flat1284)
        return nothing
    else
        _dollar_dollar = msg
        fields1282 = _dollar_dollar.var"#type"
        unwrapped_fields1283 = fields1282
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1283)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1292 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1292)
        write(pp, flat1292)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1665 = _dollar_dollar.attrs
        else
            _t1665 = nothing
        end
        fields1285 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1665,)
        unwrapped_fields1286 = fields1285
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1287 = unwrapped_fields1286[1]
        pretty_monoid(pp, field1287)
        newline(pp)
        field1288 = unwrapped_fields1286[2]
        pretty_relation_id(pp, field1288)
        newline(pp)
        field1289 = unwrapped_fields1286[3]
        pretty_abstraction_with_arity(pp, field1289)
        field1290 = unwrapped_fields1286[4]
        if !isnothing(field1290)
            newline(pp)
            opt_val1291 = field1290
            pretty_attrs(pp, opt_val1291)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1299 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1299)
        write(pp, flat1299)
        return nothing
    else
        _dollar_dollar = msg
        fields1293 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1294 = fields1293
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1295 = unwrapped_fields1294[1]
        pretty_relation_id(pp, field1295)
        newline(pp)
        field1296 = unwrapped_fields1294[2]
        pretty_abstraction(pp, field1296)
        newline(pp)
        field1297 = unwrapped_fields1294[3]
        pretty_functional_dependency_keys(pp, field1297)
        newline(pp)
        field1298 = unwrapped_fields1294[4]
        pretty_functional_dependency_values(pp, field1298)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1303 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1303)
        write(pp, flat1303)
        return nothing
    else
        fields1300 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1300)
            newline(pp)
            for (i1666, elem1301) in enumerate(fields1300)
                i1302 = i1666 - 1
                if (i1302 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1301)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1307 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1307)
        write(pp, flat1307)
        return nothing
    else
        fields1304 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1304)
            newline(pp)
            for (i1667, elem1305) in enumerate(fields1304)
                i1306 = i1667 - 1
                if (i1306 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1305)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1316 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1316)
        write(pp, flat1316)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1668 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1668 = nothing
        end
        deconstruct_result1314 = _t1668
        if !isnothing(deconstruct_result1314)
            unwrapped1315 = deconstruct_result1314
            pretty_edb(pp, unwrapped1315)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1669 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1669 = nothing
            end
            deconstruct_result1312 = _t1669
            if !isnothing(deconstruct_result1312)
                unwrapped1313 = deconstruct_result1312
                pretty_betree_relation(pp, unwrapped1313)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1670 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1670 = nothing
                end
                deconstruct_result1310 = _t1670
                if !isnothing(deconstruct_result1310)
                    unwrapped1311 = deconstruct_result1310
                    pretty_csv_data(pp, unwrapped1311)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1671 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1671 = nothing
                    end
                    deconstruct_result1308 = _t1671
                    if !isnothing(deconstruct_result1308)
                        unwrapped1309 = deconstruct_result1308
                        pretty_iceberg_data(pp, unwrapped1309)
                    else
                        throw(ParseError("No matching rule for data"))
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_edb(pp::PrettyPrinter, msg::Proto.EDB)
    flat1322 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1322)
        write(pp, flat1322)
        return nothing
    else
        _dollar_dollar = msg
        fields1317 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1318 = fields1317
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1319 = unwrapped_fields1318[1]
        pretty_relation_id(pp, field1319)
        newline(pp)
        field1320 = unwrapped_fields1318[2]
        pretty_edb_path(pp, field1320)
        newline(pp)
        field1321 = unwrapped_fields1318[3]
        pretty_edb_types(pp, field1321)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1326 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1326)
        write(pp, flat1326)
        return nothing
    else
        fields1323 = msg
        write(pp, "[")
        indent!(pp)
        for (i1672, elem1324) in enumerate(fields1323)
            i1325 = i1672 - 1
            if (i1325 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1324))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1330 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1330)
        write(pp, flat1330)
        return nothing
    else
        fields1327 = msg
        write(pp, "[")
        indent!(pp)
        for (i1673, elem1328) in enumerate(fields1327)
            i1329 = i1673 - 1
            if (i1329 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1328)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1335 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1335)
        write(pp, flat1335)
        return nothing
    else
        _dollar_dollar = msg
        fields1331 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1332 = fields1331
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1333 = unwrapped_fields1332[1]
        pretty_relation_id(pp, field1333)
        newline(pp)
        field1334 = unwrapped_fields1332[2]
        pretty_betree_info(pp, field1334)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1341 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1341)
        write(pp, flat1341)
        return nothing
    else
        _dollar_dollar = msg
        _t1674 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1336 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1674,)
        unwrapped_fields1337 = fields1336
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1338 = unwrapped_fields1337[1]
        pretty_betree_info_key_types(pp, field1338)
        newline(pp)
        field1339 = unwrapped_fields1337[2]
        pretty_betree_info_value_types(pp, field1339)
        newline(pp)
        field1340 = unwrapped_fields1337[3]
        pretty_config_dict(pp, field1340)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1345 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1345)
        write(pp, flat1345)
        return nothing
    else
        fields1342 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1342)
            newline(pp)
            for (i1675, elem1343) in enumerate(fields1342)
                i1344 = i1675 - 1
                if (i1344 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1343)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1349 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1349)
        write(pp, flat1349)
        return nothing
    else
        fields1346 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1346)
            newline(pp)
            for (i1676, elem1347) in enumerate(fields1346)
                i1348 = i1676 - 1
                if (i1348 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1347)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1356 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1356)
        write(pp, flat1356)
        return nothing
    else
        _dollar_dollar = msg
        fields1350 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1351 = fields1350
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1352 = unwrapped_fields1351[1]
        pretty_csvlocator(pp, field1352)
        newline(pp)
        field1353 = unwrapped_fields1351[2]
        pretty_csv_config(pp, field1353)
        newline(pp)
        field1354 = unwrapped_fields1351[3]
        pretty_gnf_columns(pp, field1354)
        newline(pp)
        field1355 = unwrapped_fields1351[4]
        pretty_csv_asof(pp, field1355)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1363 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1363)
        write(pp, flat1363)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1677 = _dollar_dollar.paths
        else
            _t1677 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1678 = String(copy(_dollar_dollar.inline_data))
        else
            _t1678 = nothing
        end
        fields1357 = (_t1677, _t1678,)
        unwrapped_fields1358 = fields1357
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1359 = unwrapped_fields1358[1]
        if !isnothing(field1359)
            newline(pp)
            opt_val1360 = field1359
            pretty_csv_locator_paths(pp, opt_val1360)
        end
        field1361 = unwrapped_fields1358[2]
        if !isnothing(field1361)
            newline(pp)
            opt_val1362 = field1361
            pretty_csv_locator_inline_data(pp, opt_val1362)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1367 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1367)
        write(pp, flat1367)
        return nothing
    else
        fields1364 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1364)
            newline(pp)
            for (i1679, elem1365) in enumerate(fields1364)
                i1366 = i1679 - 1
                if (i1366 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1365))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1369 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1369)
        write(pp, flat1369)
        return nothing
    else
        fields1368 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1368))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1372 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1372)
        write(pp, flat1372)
        return nothing
    else
        _dollar_dollar = msg
        _t1680 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1370 = _t1680
        unwrapped_fields1371 = fields1370
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1371)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1376 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        fields1373 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1373)
            newline(pp)
            for (i1681, elem1374) in enumerate(fields1373)
                i1375 = i1681 - 1
                if (i1375 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1374)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1385 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1385)
        write(pp, flat1385)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1682 = _dollar_dollar.target_id
        else
            _t1682 = nothing
        end
        fields1377 = (_dollar_dollar.column_path, _t1682, _dollar_dollar.types,)
        unwrapped_fields1378 = fields1377
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1379 = unwrapped_fields1378[1]
        pretty_gnf_column_path(pp, field1379)
        field1380 = unwrapped_fields1378[2]
        if !isnothing(field1380)
            newline(pp)
            opt_val1381 = field1380
            pretty_relation_id(pp, opt_val1381)
        end
        newline(pp)
        write(pp, "[")
        field1382 = unwrapped_fields1378[3]
        for (i1683, elem1383) in enumerate(field1382)
            i1384 = i1683 - 1
            if (i1384 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1383)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1392 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1392)
        write(pp, flat1392)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1684 = _dollar_dollar[1]
        else
            _t1684 = nothing
        end
        deconstruct_result1390 = _t1684
        if !isnothing(deconstruct_result1390)
            unwrapped1391 = deconstruct_result1390
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1391))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1685 = _dollar_dollar
            else
                _t1685 = nothing
            end
            deconstruct_result1386 = _t1685
            if !isnothing(deconstruct_result1386)
                unwrapped1387 = deconstruct_result1386
                write(pp, "[")
                indent!(pp)
                for (i1686, elem1388) in enumerate(unwrapped1387)
                    i1389 = i1686 - 1
                    if (i1389 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1388))
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
    flat1394 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1394)
        write(pp, flat1394)
        return nothing
    else
        fields1393 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1393))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1402 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1402)
        write(pp, flat1402)
        return nothing
    else
        _dollar_dollar = msg
        _t1687 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1395 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1687,)
        unwrapped_fields1396 = fields1395
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1397 = unwrapped_fields1396[1]
        pretty_iceberg_locator(pp, field1397)
        newline(pp)
        field1398 = unwrapped_fields1396[2]
        pretty_iceberg_config(pp, field1398)
        newline(pp)
        field1399 = unwrapped_fields1396[3]
        pretty_gnf_columns(pp, field1399)
        field1400 = unwrapped_fields1396[4]
        if !isnothing(field1400)
            newline(pp)
            opt_val1401 = field1400
            pretty_iceberg_to_snapshot(pp, opt_val1401)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1410 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1410)
        write(pp, flat1410)
        return nothing
    else
        _dollar_dollar = msg
        fields1403 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1404 = fields1403
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_name")
        newline(pp)
        field1405 = unwrapped_fields1404[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1405))
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "namespace")
        field1406 = unwrapped_fields1404[2]
        if !isempty(field1406)
            newline(pp)
            for (i1688, elem1407) in enumerate(field1406)
                i1408 = i1688 - 1
                if (i1408 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1407))
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "warehouse")
        newline(pp)
        field1409 = unwrapped_fields1404[3]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1409))
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_config(pp::PrettyPrinter, msg::Proto.IcebergConfig)
    flat1422 = try_flat(pp, msg, pretty_iceberg_config)
    if !isnothing(flat1422)
        write(pp, flat1422)
        return nothing
    else
        _dollar_dollar = msg
        _t1689 = deconstruct_iceberg_config_scope_optional(pp, _dollar_dollar)
        fields1411 = (_dollar_dollar.catalog_uri, _t1689, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1412 = fields1411
        write(pp, "(iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "catalog_uri")
        newline(pp)
        field1413 = unwrapped_fields1412[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1413))
        dedent!(pp)
        write(pp, ")")
        field1414 = unwrapped_fields1412[2]
        if !isnothing(field1414)
            newline(pp)
            opt_val1415 = field1414
            pretty_iceberg_config_scope(pp, opt_val1415)
        end
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "properties")
        field1416 = unwrapped_fields1412[3]
        if !isempty(field1416)
            newline(pp)
            for (i1690, elem1417) in enumerate(field1416)
                i1418 = i1690 - 1
                if (i1418 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1417)
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "auth_properties")
        field1419 = unwrapped_fields1412[4]
        if !isempty(field1419)
            newline(pp)
            for (i1691, elem1420) in enumerate(field1419)
                i1421 = i1691 - 1
                if (i1421 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1420)
            end
        end
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_config_scope(pp::PrettyPrinter, msg::String)
    flat1424 = try_flat(pp, msg, pretty_iceberg_config_scope)
    if !isnothing(flat1424)
        write(pp, flat1424)
        return nothing
    else
        fields1423 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1423))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1429 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1429)
        write(pp, flat1429)
        return nothing
    else
        _dollar_dollar = msg
        fields1425 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1426 = fields1425
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1427 = unwrapped_fields1426[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1427))
        newline(pp)
        field1428 = unwrapped_fields1426[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1428))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1431 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1431)
        write(pp, flat1431)
        return nothing
    else
        fields1430 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1430))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1434 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1434)
        write(pp, flat1434)
        return nothing
    else
        _dollar_dollar = msg
        fields1432 = _dollar_dollar.fragment_id
        unwrapped_fields1433 = fields1432
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1433)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1439 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1439)
        write(pp, flat1439)
        return nothing
    else
        _dollar_dollar = msg
        fields1435 = _dollar_dollar.relations
        unwrapped_fields1436 = fields1435
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1436)
            newline(pp)
            for (i1692, elem1437) in enumerate(unwrapped_fields1436)
                i1438 = i1692 - 1
                if (i1438 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1437)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1444 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1444)
        write(pp, flat1444)
        return nothing
    else
        _dollar_dollar = msg
        fields1440 = _dollar_dollar.mappings
        unwrapped_fields1441 = fields1440
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1441)
            newline(pp)
            for (i1693, elem1442) in enumerate(unwrapped_fields1441)
                i1443 = i1693 - 1
                if (i1443 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1442)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1449 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1449)
        write(pp, flat1449)
        return nothing
    else
        _dollar_dollar = msg
        fields1445 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1446 = fields1445
        field1447 = unwrapped_fields1446[1]
        pretty_edb_path(pp, field1447)
        write(pp, " ")
        field1448 = unwrapped_fields1446[2]
        pretty_relation_id(pp, field1448)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1453 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1453)
        write(pp, flat1453)
        return nothing
    else
        fields1450 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1450)
            newline(pp)
            for (i1694, elem1451) in enumerate(fields1450)
                i1452 = i1694 - 1
                if (i1452 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1451)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1464 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1464)
        write(pp, flat1464)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1695 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1695 = nothing
        end
        deconstruct_result1462 = _t1695
        if !isnothing(deconstruct_result1462)
            unwrapped1463 = deconstruct_result1462
            pretty_demand(pp, unwrapped1463)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1696 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1696 = nothing
            end
            deconstruct_result1460 = _t1696
            if !isnothing(deconstruct_result1460)
                unwrapped1461 = deconstruct_result1460
                pretty_output(pp, unwrapped1461)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1697 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1697 = nothing
                end
                deconstruct_result1458 = _t1697
                if !isnothing(deconstruct_result1458)
                    unwrapped1459 = deconstruct_result1458
                    pretty_what_if(pp, unwrapped1459)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1698 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1698 = nothing
                    end
                    deconstruct_result1456 = _t1698
                    if !isnothing(deconstruct_result1456)
                        unwrapped1457 = deconstruct_result1456
                        pretty_abort(pp, unwrapped1457)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1699 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1699 = nothing
                        end
                        deconstruct_result1454 = _t1699
                        if !isnothing(deconstruct_result1454)
                            unwrapped1455 = deconstruct_result1454
                            pretty_export(pp, unwrapped1455)
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
    flat1467 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1467)
        write(pp, flat1467)
        return nothing
    else
        _dollar_dollar = msg
        fields1465 = _dollar_dollar.relation_id
        unwrapped_fields1466 = fields1465
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1466)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1472 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1472)
        write(pp, flat1472)
        return nothing
    else
        _dollar_dollar = msg
        fields1468 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1469 = fields1468
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1470 = unwrapped_fields1469[1]
        pretty_name(pp, field1470)
        newline(pp)
        field1471 = unwrapped_fields1469[2]
        pretty_relation_id(pp, field1471)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1477 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1477)
        write(pp, flat1477)
        return nothing
    else
        _dollar_dollar = msg
        fields1473 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1474 = fields1473
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1475 = unwrapped_fields1474[1]
        pretty_name(pp, field1475)
        newline(pp)
        field1476 = unwrapped_fields1474[2]
        pretty_epoch(pp, field1476)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1483 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1483)
        write(pp, flat1483)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1700 = _dollar_dollar.name
        else
            _t1700 = nothing
        end
        fields1478 = (_t1700, _dollar_dollar.relation_id,)
        unwrapped_fields1479 = fields1478
        write(pp, "(abort")
        indent_sexp!(pp)
        field1480 = unwrapped_fields1479[1]
        if !isnothing(field1480)
            newline(pp)
            opt_val1481 = field1480
            pretty_name(pp, opt_val1481)
        end
        newline(pp)
        field1482 = unwrapped_fields1479[2]
        pretty_relation_id(pp, field1482)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1488 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1488)
        write(pp, flat1488)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1701 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1701 = nothing
        end
        deconstruct_result1486 = _t1701
        if !isnothing(deconstruct_result1486)
            unwrapped1487 = deconstruct_result1486
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1487)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1702 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1702 = nothing
            end
            deconstruct_result1484 = _t1702
            if !isnothing(deconstruct_result1484)
                unwrapped1485 = deconstruct_result1484
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1485)
                dedent!(pp)
                write(pp, ")")
            else
                throw(ParseError("No matching rule for export"))
            end
        end
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1499 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1499)
        write(pp, flat1499)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1703 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1703 = nothing
        end
        deconstruct_result1494 = _t1703
        if !isnothing(deconstruct_result1494)
            unwrapped1495 = deconstruct_result1494
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1496 = unwrapped1495[1]
            pretty_export_csv_path(pp, field1496)
            newline(pp)
            field1497 = unwrapped1495[2]
            pretty_export_csv_source(pp, field1497)
            newline(pp)
            field1498 = unwrapped1495[3]
            pretty_csv_config(pp, field1498)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1705 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1704 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1705,)
            else
                _t1704 = nothing
            end
            deconstruct_result1489 = _t1704
            if !isnothing(deconstruct_result1489)
                unwrapped1490 = deconstruct_result1489
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1491 = unwrapped1490[1]
                pretty_export_csv_path(pp, field1491)
                newline(pp)
                field1492 = unwrapped1490[2]
                pretty_export_csv_columns_list(pp, field1492)
                newline(pp)
                field1493 = unwrapped1490[3]
                pretty_config_dict(pp, field1493)
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
    flat1501 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1501)
        write(pp, flat1501)
        return nothing
    else
        fields1500 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1500))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1508 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1508)
        write(pp, flat1508)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1706 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1706 = nothing
        end
        deconstruct_result1504 = _t1706
        if !isnothing(deconstruct_result1504)
            unwrapped1505 = deconstruct_result1504
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1505)
                newline(pp)
                for (i1707, elem1506) in enumerate(unwrapped1505)
                    i1507 = i1707 - 1
                    if (i1507 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1506)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1708 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1708 = nothing
            end
            deconstruct_result1502 = _t1708
            if !isnothing(deconstruct_result1502)
                unwrapped1503 = deconstruct_result1502
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1503)
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
    flat1513 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1513)
        write(pp, flat1513)
        return nothing
    else
        _dollar_dollar = msg
        fields1509 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1510 = fields1509
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1511 = unwrapped_fields1510[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1511))
        newline(pp)
        field1512 = unwrapped_fields1510[2]
        pretty_relation_id(pp, field1512)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1517 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1517)
        write(pp, flat1517)
        return nothing
    else
        fields1514 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1514)
            newline(pp)
            for (i1709, elem1515) in enumerate(fields1514)
                i1516 = i1709 - 1
                if (i1516 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1515)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1527 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1527)
        write(pp, flat1527)
        return nothing
    else
        _dollar_dollar = msg
        _t1710 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1518 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1710,)
        unwrapped_fields1519 = fields1518
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1520 = unwrapped_fields1519[1]
        pretty_iceberg_locator(pp, field1520)
        newline(pp)
        field1521 = unwrapped_fields1519[2]
        pretty_iceberg_config(pp, field1521)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "columns")
        field1522 = unwrapped_fields1519[3]
        if !isempty(field1522)
            newline(pp)
            for (i1711, elem1523) in enumerate(field1522)
                i1524 = i1711 - 1
                if (i1524 > 0)
                    newline(pp)
                end
                pretty_iceberg_export_column(pp, elem1523)
            end
        end
        dedent!(pp)
        write(pp, ")")
        field1525 = unwrapped_fields1519[4]
        if !isnothing(field1525)
            newline(pp)
            opt_val1526 = field1525
            pretty_config_dict(pp, opt_val1526)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_export_column(pp::PrettyPrinter, msg::Proto.IcebergExportColumn)
    flat1533 = try_flat(pp, msg, pretty_iceberg_export_column)
    if !isnothing(flat1533)
        write(pp, flat1533)
        return nothing
    else
        _dollar_dollar = msg
        fields1528 = (_dollar_dollar.name, _dollar_dollar.var"#type", _dollar_dollar.nullable,)
        unwrapped_fields1529 = fields1528
        write(pp, "(iceberg_column")
        indent_sexp!(pp)
        newline(pp)
        field1530 = unwrapped_fields1529[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1530))
        newline(pp)
        field1531 = unwrapped_fields1529[2]
        pretty_type(pp, field1531)
        newline(pp)
        field1532 = unwrapped_fields1529[3]
        pretty_boolean_value(pp, field1532)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1756, _rid) in enumerate(msg.ids)
        _idx = i1756 - 1
        newline(pp)
        write(pp, "(")
        _t1757 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1757)
        write(pp, " ")
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, msg.orig_names[_idx + 1]))
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
    write(pp, lowercase(string(msg.epsilon)))
    newline(pp)
    write(pp, ":max_pivots ")
    write(pp, string(msg.max_pivots))
    newline(pp)
    write(pp, ":max_deltas ")
    write(pp, string(msg.max_deltas))
    newline(pp)
    write(pp, ":max_leaf ")
    write(pp, string(msg.max_leaf))
    write(pp, ")")
    dedent!(pp)
    return nothing
end

function pretty_be_tree_locator(pp::PrettyPrinter, msg::Proto.BeTreeLocator)
    write(pp, "(be_tree_locator")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":element_count ")
    write(pp, string(msg.element_count))
    newline(pp)
    write(pp, ":tree_height ")
    write(pp, string(msg.tree_height))
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
    write(pp, ":keys (")
    for (i1758, _elem) in enumerate(msg.keys)
        _idx = i1758 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1759, _elem) in enumerate(msg.values)
        _idx = i1759 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, "))")
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
    write(pp, ":columns (")
    for (i1760, _elem) in enumerate(msg.columns)
        _idx = i1760 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, "))")
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DateValue) = pretty_raw_date(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DateTimeValue) = pretty_raw_datetime(pp, x)
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Int32Type) = pretty_int32_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Float32Type) = pretty_float32_type(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.UInt32Type) = pretty_uint32_type(pp, x)
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.IcebergData) = pretty_iceberg_data(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.IcebergLocator) = pretty_iceberg_locator(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.IcebergConfig) = pretty_iceberg_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Tuple{String, String}) = pretty_iceberg_property_entry(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Undefine) = pretty_undefine(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Context) = pretty_context(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Snapshot) = pretty_snapshot(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.SnapshotMapping) = pretty_snapshot_mapping(pp, x)
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
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.ExportCSVColumn}) = pretty_export_csv_columns_list(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportIcebergConfig) = pretty_export_iceberg_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.IcebergExportColumn) = pretty_iceberg_export_column(pp, x)
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
export format_decimal, format_int128, format_uint128, format_int, format_float, format_string, format_bool, format_int32, format_uint32, format_float32
# Export legacy format functions for backward compatibility
export format_float64, format_string_value
# Export pretty printing API
export pprint, pretty, pretty_debug
export PrettyPrinter
# Export internal helpers for testing
export indent_level, indent!, try_flat

end # module Pretty
