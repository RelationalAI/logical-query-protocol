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
    _t1741 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1741
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1742 = Proto.Value(value=OneOf(:int_value, v))
    return _t1742
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1743 = Proto.Value(value=OneOf(:float_value, v))
    return _t1743
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1744 = Proto.Value(value=OneOf(:string_value, v))
    return _t1744
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1745 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1745
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1746 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1746
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1747 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1747,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1748 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1748,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1749 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1749,))
            end
        end
    end
    _t1750 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1750,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1751 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1751,))
    _t1752 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1752,))
    if msg.new_line != ""
        _t1753 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1753,))
    end
    _t1754 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1754,))
    _t1755 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1755,))
    _t1756 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1756,))
    if msg.comment != ""
        _t1757 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1757,))
    end
    for missing_string in msg.missing_strings
        _t1758 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1758,))
    end
    _t1759 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1759,))
    _t1760 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1760,))
    _t1761 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1761,))
    if msg.partition_size_mb != 0
        _t1762 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1762,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1763 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1763,))
    _t1764 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1764,))
    _t1765 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1765,))
    _t1766 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1766,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1767 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1767,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1768 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1768,))
        end
    end
    _t1769 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1769,))
    _t1770 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1770,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1771 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1771,))
    end
    if !isnothing(msg.compression)
        _t1772 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1772,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1773 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1773,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1774 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1774,))
    end
    if !isnothing(msg.syntax_delim)
        _t1775 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1775,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1776 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1776,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1777 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1777,))
    end
    return sort(result)
end

function mask_secret_value(pp::PrettyPrinter, pair::Tuple{String, String})::String
    return "***"
end

function deconstruct_iceberg_catalog_config_scope_optional(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)::Union{Nothing, String}
    if msg.scope != ""
        return msg.scope
    else
        _t1778 = nothing
    end
    return nothing
end

function deconstruct_iceberg_locator_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergLocator)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1779 = nothing
    end
    return nothing
end

function deconstruct_iceberg_locator_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergLocator)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1780 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1781 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1781,))
    end
    if msg.target_file_size_bytes != 0
        _t1782 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1782,))
    end
    if msg.compression != ""
        _t1783 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1783,))
    end
    if length(result) == 0
        return nothing
    else
        _t1784 = nothing
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
        _t1785 = nothing
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
    flat789 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat789)
        write(pp, flat789)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1560 = _dollar_dollar.configure
        else
            _t1560 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1561 = _dollar_dollar.sync
        else
            _t1561 = nothing
        end
        fields780 = (_t1560, _t1561, _dollar_dollar.epochs,)
        unwrapped_fields781 = fields780
        write(pp, "(transaction")
        indent_sexp!(pp)
        field782 = unwrapped_fields781[1]
        if !isnothing(field782)
            newline(pp)
            opt_val783 = field782
            pretty_configure(pp, opt_val783)
        end
        field784 = unwrapped_fields781[2]
        if !isnothing(field784)
            newline(pp)
            opt_val785 = field784
            pretty_sync(pp, opt_val785)
        end
        field786 = unwrapped_fields781[3]
        if !isempty(field786)
            newline(pp)
            for (i1562, elem787) in enumerate(field786)
                i788 = i1562 - 1
                if (i788 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem787)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat792 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat792)
        write(pp, flat792)
        return nothing
    else
        _dollar_dollar = msg
        _t1563 = deconstruct_configure(pp, _dollar_dollar)
        fields790 = _t1563
        unwrapped_fields791 = fields790
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields791)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat796 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat796)
        write(pp, flat796)
        return nothing
    else
        fields793 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields793)
            newline(pp)
            for (i1564, elem794) in enumerate(fields793)
                i795 = i1564 - 1
                if (i795 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem794)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat801 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat801)
        write(pp, flat801)
        return nothing
    else
        _dollar_dollar = msg
        fields797 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields798 = fields797
        write(pp, ":")
        field799 = unwrapped_fields798[1]
        write(pp, field799)
        write(pp, " ")
        field800 = unwrapped_fields798[2]
        pretty_raw_value(pp, field800)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat827 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat827)
        write(pp, flat827)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1565 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1565 = nothing
        end
        deconstruct_result825 = _t1565
        if !isnothing(deconstruct_result825)
            unwrapped826 = deconstruct_result825
            pretty_raw_date(pp, unwrapped826)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1566 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1566 = nothing
            end
            deconstruct_result823 = _t1566
            if !isnothing(deconstruct_result823)
                unwrapped824 = deconstruct_result823
                pretty_raw_datetime(pp, unwrapped824)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1567 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1567 = nothing
                end
                deconstruct_result821 = _t1567
                if !isnothing(deconstruct_result821)
                    unwrapped822 = deconstruct_result821
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped822))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1568 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1568 = nothing
                    end
                    deconstruct_result819 = _t1568
                    if !isnothing(deconstruct_result819)
                        unwrapped820 = deconstruct_result819
                        write(pp, (string(Int64(unwrapped820)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1569 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1569 = nothing
                        end
                        deconstruct_result817 = _t1569
                        if !isnothing(deconstruct_result817)
                            unwrapped818 = deconstruct_result817
                            write(pp, string(unwrapped818))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1570 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1570 = nothing
                            end
                            deconstruct_result815 = _t1570
                            if !isnothing(deconstruct_result815)
                                unwrapped816 = deconstruct_result815
                                write(pp, format_float32_literal(unwrapped816))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1571 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1571 = nothing
                                end
                                deconstruct_result813 = _t1571
                                if !isnothing(deconstruct_result813)
                                    unwrapped814 = deconstruct_result813
                                    write(pp, lowercase(string(unwrapped814)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1572 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1572 = nothing
                                    end
                                    deconstruct_result811 = _t1572
                                    if !isnothing(deconstruct_result811)
                                        unwrapped812 = deconstruct_result811
                                        write(pp, (string(Int64(unwrapped812)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1573 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1573 = nothing
                                        end
                                        deconstruct_result809 = _t1573
                                        if !isnothing(deconstruct_result809)
                                            unwrapped810 = deconstruct_result809
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped810))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1574 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1574 = nothing
                                            end
                                            deconstruct_result807 = _t1574
                                            if !isnothing(deconstruct_result807)
                                                unwrapped808 = deconstruct_result807
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped808))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1575 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1575 = nothing
                                                end
                                                deconstruct_result805 = _t1575
                                                if !isnothing(deconstruct_result805)
                                                    unwrapped806 = deconstruct_result805
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped806))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1576 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1576 = nothing
                                                    end
                                                    deconstruct_result803 = _t1576
                                                    if !isnothing(deconstruct_result803)
                                                        unwrapped804 = deconstruct_result803
                                                        pretty_boolean_value(pp, unwrapped804)
                                                    else
                                                        fields802 = msg
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
    flat833 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat833)
        write(pp, flat833)
        return nothing
    else
        _dollar_dollar = msg
        fields828 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields829 = fields828
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field830 = unwrapped_fields829[1]
        write(pp, string(field830))
        newline(pp)
        field831 = unwrapped_fields829[2]
        write(pp, string(field831))
        newline(pp)
        field832 = unwrapped_fields829[3]
        write(pp, string(field832))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat844 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat844)
        write(pp, flat844)
        return nothing
    else
        _dollar_dollar = msg
        fields834 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields835 = fields834
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field836 = unwrapped_fields835[1]
        write(pp, string(field836))
        newline(pp)
        field837 = unwrapped_fields835[2]
        write(pp, string(field837))
        newline(pp)
        field838 = unwrapped_fields835[3]
        write(pp, string(field838))
        newline(pp)
        field839 = unwrapped_fields835[4]
        write(pp, string(field839))
        newline(pp)
        field840 = unwrapped_fields835[5]
        write(pp, string(field840))
        newline(pp)
        field841 = unwrapped_fields835[6]
        write(pp, string(field841))
        field842 = unwrapped_fields835[7]
        if !isnothing(field842)
            newline(pp)
            opt_val843 = field842
            write(pp, string(opt_val843))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1577 = ()
    else
        _t1577 = nothing
    end
    deconstruct_result847 = _t1577
    if !isnothing(deconstruct_result847)
        unwrapped848 = deconstruct_result847
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1578 = ()
        else
            _t1578 = nothing
        end
        deconstruct_result845 = _t1578
        if !isnothing(deconstruct_result845)
            unwrapped846 = deconstruct_result845
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat853 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat853)
        write(pp, flat853)
        return nothing
    else
        _dollar_dollar = msg
        fields849 = _dollar_dollar.fragments
        unwrapped_fields850 = fields849
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields850)
            newline(pp)
            for (i1579, elem851) in enumerate(unwrapped_fields850)
                i852 = i1579 - 1
                if (i852 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem851)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat856 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat856)
        write(pp, flat856)
        return nothing
    else
        _dollar_dollar = msg
        fields854 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields855 = fields854
        write(pp, ":")
        write(pp, unwrapped_fields855)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat863 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat863)
        write(pp, flat863)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1580 = _dollar_dollar.writes
        else
            _t1580 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1581 = _dollar_dollar.reads
        else
            _t1581 = nothing
        end
        fields857 = (_t1580, _t1581,)
        unwrapped_fields858 = fields857
        write(pp, "(epoch")
        indent_sexp!(pp)
        field859 = unwrapped_fields858[1]
        if !isnothing(field859)
            newline(pp)
            opt_val860 = field859
            pretty_epoch_writes(pp, opt_val860)
        end
        field861 = unwrapped_fields858[2]
        if !isnothing(field861)
            newline(pp)
            opt_val862 = field861
            pretty_epoch_reads(pp, opt_val862)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat867 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat867)
        write(pp, flat867)
        return nothing
    else
        fields864 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields864)
            newline(pp)
            for (i1582, elem865) in enumerate(fields864)
                i866 = i1582 - 1
                if (i866 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem865)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat876 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat876)
        write(pp, flat876)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1583 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1583 = nothing
        end
        deconstruct_result874 = _t1583
        if !isnothing(deconstruct_result874)
            unwrapped875 = deconstruct_result874
            pretty_define(pp, unwrapped875)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1584 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1584 = nothing
            end
            deconstruct_result872 = _t1584
            if !isnothing(deconstruct_result872)
                unwrapped873 = deconstruct_result872
                pretty_undefine(pp, unwrapped873)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1585 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1585 = nothing
                end
                deconstruct_result870 = _t1585
                if !isnothing(deconstruct_result870)
                    unwrapped871 = deconstruct_result870
                    pretty_context(pp, unwrapped871)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1586 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1586 = nothing
                    end
                    deconstruct_result868 = _t1586
                    if !isnothing(deconstruct_result868)
                        unwrapped869 = deconstruct_result868
                        pretty_snapshot(pp, unwrapped869)
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
    flat879 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat879)
        write(pp, flat879)
        return nothing
    else
        _dollar_dollar = msg
        fields877 = _dollar_dollar.fragment
        unwrapped_fields878 = fields877
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields878)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat886 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat886)
        write(pp, flat886)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields880 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields881 = fields880
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field882 = unwrapped_fields881[1]
        pretty_new_fragment_id(pp, field882)
        field883 = unwrapped_fields881[2]
        if !isempty(field883)
            newline(pp)
            for (i1587, elem884) in enumerate(field883)
                i885 = i1587 - 1
                if (i885 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem884)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat888 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat888)
        write(pp, flat888)
        return nothing
    else
        fields887 = msg
        pretty_fragment_id(pp, fields887)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat897 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat897)
        write(pp, flat897)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1588 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1588 = nothing
        end
        deconstruct_result895 = _t1588
        if !isnothing(deconstruct_result895)
            unwrapped896 = deconstruct_result895
            pretty_def(pp, unwrapped896)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1589 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1589 = nothing
            end
            deconstruct_result893 = _t1589
            if !isnothing(deconstruct_result893)
                unwrapped894 = deconstruct_result893
                pretty_algorithm(pp, unwrapped894)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1590 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1590 = nothing
                end
                deconstruct_result891 = _t1590
                if !isnothing(deconstruct_result891)
                    unwrapped892 = deconstruct_result891
                    pretty_constraint(pp, unwrapped892)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1591 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1591 = nothing
                    end
                    deconstruct_result889 = _t1591
                    if !isnothing(deconstruct_result889)
                        unwrapped890 = deconstruct_result889
                        pretty_data(pp, unwrapped890)
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
    flat904 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat904)
        write(pp, flat904)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1592 = _dollar_dollar.attrs
        else
            _t1592 = nothing
        end
        fields898 = (_dollar_dollar.name, _dollar_dollar.body, _t1592,)
        unwrapped_fields899 = fields898
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field900 = unwrapped_fields899[1]
        pretty_relation_id(pp, field900)
        newline(pp)
        field901 = unwrapped_fields899[2]
        pretty_abstraction(pp, field901)
        field902 = unwrapped_fields899[3]
        if !isnothing(field902)
            newline(pp)
            opt_val903 = field902
            pretty_attrs(pp, opt_val903)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat909 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat909)
        write(pp, flat909)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1594 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1593 = _t1594
        else
            _t1593 = nothing
        end
        deconstruct_result907 = _t1593
        if !isnothing(deconstruct_result907)
            unwrapped908 = deconstruct_result907
            write(pp, ":")
            write(pp, unwrapped908)
        else
            _dollar_dollar = msg
            _t1595 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result905 = _t1595
            if !isnothing(deconstruct_result905)
                unwrapped906 = deconstruct_result905
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped906))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat914 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat914)
        write(pp, flat914)
        return nothing
    else
        _dollar_dollar = msg
        _t1596 = deconstruct_bindings(pp, _dollar_dollar)
        fields910 = (_t1596, _dollar_dollar.value,)
        unwrapped_fields911 = fields910
        write(pp, "(")
        indent!(pp)
        field912 = unwrapped_fields911[1]
        pretty_bindings(pp, field912)
        newline(pp)
        field913 = unwrapped_fields911[2]
        pretty_formula(pp, field913)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat922 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat922)
        write(pp, flat922)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1597 = _dollar_dollar[2]
        else
            _t1597 = nothing
        end
        fields915 = (_dollar_dollar[1], _t1597,)
        unwrapped_fields916 = fields915
        write(pp, "[")
        indent!(pp)
        field917 = unwrapped_fields916[1]
        for (i1598, elem918) in enumerate(field917)
            i919 = i1598 - 1
            if (i919 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem918)
        end
        field920 = unwrapped_fields916[2]
        if !isnothing(field920)
            newline(pp)
            opt_val921 = field920
            pretty_value_bindings(pp, opt_val921)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat927 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat927)
        write(pp, flat927)
        return nothing
    else
        _dollar_dollar = msg
        fields923 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields924 = fields923
        field925 = unwrapped_fields924[1]
        write(pp, field925)
        write(pp, "::")
        field926 = unwrapped_fields924[2]
        pretty_type(pp, field926)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat956 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat956)
        write(pp, flat956)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1599 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1599 = nothing
        end
        deconstruct_result954 = _t1599
        if !isnothing(deconstruct_result954)
            unwrapped955 = deconstruct_result954
            pretty_unspecified_type(pp, unwrapped955)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1600 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1600 = nothing
            end
            deconstruct_result952 = _t1600
            if !isnothing(deconstruct_result952)
                unwrapped953 = deconstruct_result952
                pretty_string_type(pp, unwrapped953)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1601 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1601 = nothing
                end
                deconstruct_result950 = _t1601
                if !isnothing(deconstruct_result950)
                    unwrapped951 = deconstruct_result950
                    pretty_int_type(pp, unwrapped951)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1602 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1602 = nothing
                    end
                    deconstruct_result948 = _t1602
                    if !isnothing(deconstruct_result948)
                        unwrapped949 = deconstruct_result948
                        pretty_float_type(pp, unwrapped949)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1603 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1603 = nothing
                        end
                        deconstruct_result946 = _t1603
                        if !isnothing(deconstruct_result946)
                            unwrapped947 = deconstruct_result946
                            pretty_uint128_type(pp, unwrapped947)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1604 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1604 = nothing
                            end
                            deconstruct_result944 = _t1604
                            if !isnothing(deconstruct_result944)
                                unwrapped945 = deconstruct_result944
                                pretty_int128_type(pp, unwrapped945)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1605 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1605 = nothing
                                end
                                deconstruct_result942 = _t1605
                                if !isnothing(deconstruct_result942)
                                    unwrapped943 = deconstruct_result942
                                    pretty_date_type(pp, unwrapped943)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1606 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1606 = nothing
                                    end
                                    deconstruct_result940 = _t1606
                                    if !isnothing(deconstruct_result940)
                                        unwrapped941 = deconstruct_result940
                                        pretty_datetime_type(pp, unwrapped941)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1607 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1607 = nothing
                                        end
                                        deconstruct_result938 = _t1607
                                        if !isnothing(deconstruct_result938)
                                            unwrapped939 = deconstruct_result938
                                            pretty_missing_type(pp, unwrapped939)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1608 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1608 = nothing
                                            end
                                            deconstruct_result936 = _t1608
                                            if !isnothing(deconstruct_result936)
                                                unwrapped937 = deconstruct_result936
                                                pretty_decimal_type(pp, unwrapped937)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1609 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1609 = nothing
                                                end
                                                deconstruct_result934 = _t1609
                                                if !isnothing(deconstruct_result934)
                                                    unwrapped935 = deconstruct_result934
                                                    pretty_boolean_type(pp, unwrapped935)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1610 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1610 = nothing
                                                    end
                                                    deconstruct_result932 = _t1610
                                                    if !isnothing(deconstruct_result932)
                                                        unwrapped933 = deconstruct_result932
                                                        pretty_int32_type(pp, unwrapped933)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1611 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1611 = nothing
                                                        end
                                                        deconstruct_result930 = _t1611
                                                        if !isnothing(deconstruct_result930)
                                                            unwrapped931 = deconstruct_result930
                                                            pretty_float32_type(pp, unwrapped931)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1612 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1612 = nothing
                                                            end
                                                            deconstruct_result928 = _t1612
                                                            if !isnothing(deconstruct_result928)
                                                                unwrapped929 = deconstruct_result928
                                                                pretty_uint32_type(pp, unwrapped929)
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
    fields957 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields958 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields959 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields960 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields961 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields962 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields963 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields964 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields965 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat970 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat970)
        write(pp, flat970)
        return nothing
    else
        _dollar_dollar = msg
        fields966 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields967 = fields966
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field968 = unwrapped_fields967[1]
        write(pp, string(field968))
        newline(pp)
        field969 = unwrapped_fields967[2]
        write(pp, string(field969))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields971 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields972 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields973 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields974 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat978 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat978)
        write(pp, flat978)
        return nothing
    else
        fields975 = msg
        write(pp, "|")
        if !isempty(fields975)
            write(pp, " ")
            for (i1613, elem976) in enumerate(fields975)
                i977 = i1613 - 1
                if (i977 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem976)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1005 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1005)
        write(pp, flat1005)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1614 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1614 = nothing
        end
        deconstruct_result1003 = _t1614
        if !isnothing(deconstruct_result1003)
            unwrapped1004 = deconstruct_result1003
            pretty_true(pp, unwrapped1004)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1615 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1615 = nothing
            end
            deconstruct_result1001 = _t1615
            if !isnothing(deconstruct_result1001)
                unwrapped1002 = deconstruct_result1001
                pretty_false(pp, unwrapped1002)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1616 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1616 = nothing
                end
                deconstruct_result999 = _t1616
                if !isnothing(deconstruct_result999)
                    unwrapped1000 = deconstruct_result999
                    pretty_exists(pp, unwrapped1000)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1617 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1617 = nothing
                    end
                    deconstruct_result997 = _t1617
                    if !isnothing(deconstruct_result997)
                        unwrapped998 = deconstruct_result997
                        pretty_reduce(pp, unwrapped998)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1618 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1618 = nothing
                        end
                        deconstruct_result995 = _t1618
                        if !isnothing(deconstruct_result995)
                            unwrapped996 = deconstruct_result995
                            pretty_conjunction(pp, unwrapped996)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1619 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1619 = nothing
                            end
                            deconstruct_result993 = _t1619
                            if !isnothing(deconstruct_result993)
                                unwrapped994 = deconstruct_result993
                                pretty_disjunction(pp, unwrapped994)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1620 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1620 = nothing
                                end
                                deconstruct_result991 = _t1620
                                if !isnothing(deconstruct_result991)
                                    unwrapped992 = deconstruct_result991
                                    pretty_not(pp, unwrapped992)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1621 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1621 = nothing
                                    end
                                    deconstruct_result989 = _t1621
                                    if !isnothing(deconstruct_result989)
                                        unwrapped990 = deconstruct_result989
                                        pretty_ffi(pp, unwrapped990)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1622 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1622 = nothing
                                        end
                                        deconstruct_result987 = _t1622
                                        if !isnothing(deconstruct_result987)
                                            unwrapped988 = deconstruct_result987
                                            pretty_atom(pp, unwrapped988)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1623 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1623 = nothing
                                            end
                                            deconstruct_result985 = _t1623
                                            if !isnothing(deconstruct_result985)
                                                unwrapped986 = deconstruct_result985
                                                pretty_pragma(pp, unwrapped986)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1624 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1624 = nothing
                                                end
                                                deconstruct_result983 = _t1624
                                                if !isnothing(deconstruct_result983)
                                                    unwrapped984 = deconstruct_result983
                                                    pretty_primitive(pp, unwrapped984)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1625 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1625 = nothing
                                                    end
                                                    deconstruct_result981 = _t1625
                                                    if !isnothing(deconstruct_result981)
                                                        unwrapped982 = deconstruct_result981
                                                        pretty_rel_atom(pp, unwrapped982)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1626 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1626 = nothing
                                                        end
                                                        deconstruct_result979 = _t1626
                                                        if !isnothing(deconstruct_result979)
                                                            unwrapped980 = deconstruct_result979
                                                            pretty_cast(pp, unwrapped980)
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
    fields1006 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1007 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1012 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1012)
        write(pp, flat1012)
        return nothing
    else
        _dollar_dollar = msg
        _t1627 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1008 = (_t1627, _dollar_dollar.body.value,)
        unwrapped_fields1009 = fields1008
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1010 = unwrapped_fields1009[1]
        pretty_bindings(pp, field1010)
        newline(pp)
        field1011 = unwrapped_fields1009[2]
        pretty_formula(pp, field1011)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1018 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1018)
        write(pp, flat1018)
        return nothing
    else
        _dollar_dollar = msg
        fields1013 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1014 = fields1013
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1015 = unwrapped_fields1014[1]
        pretty_abstraction(pp, field1015)
        newline(pp)
        field1016 = unwrapped_fields1014[2]
        pretty_abstraction(pp, field1016)
        newline(pp)
        field1017 = unwrapped_fields1014[3]
        pretty_terms(pp, field1017)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1022 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1022)
        write(pp, flat1022)
        return nothing
    else
        fields1019 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1019)
            newline(pp)
            for (i1628, elem1020) in enumerate(fields1019)
                i1021 = i1628 - 1
                if (i1021 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1020)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1027 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1027)
        write(pp, flat1027)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1629 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1629 = nothing
        end
        deconstruct_result1025 = _t1629
        if !isnothing(deconstruct_result1025)
            unwrapped1026 = deconstruct_result1025
            pretty_var(pp, unwrapped1026)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1630 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1630 = nothing
            end
            deconstruct_result1023 = _t1630
            if !isnothing(deconstruct_result1023)
                unwrapped1024 = deconstruct_result1023
                pretty_value(pp, unwrapped1024)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1030 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1030)
        write(pp, flat1030)
        return nothing
    else
        _dollar_dollar = msg
        fields1028 = _dollar_dollar.name
        unwrapped_fields1029 = fields1028
        write(pp, unwrapped_fields1029)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1056 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1056)
        write(pp, flat1056)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1631 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1631 = nothing
        end
        deconstruct_result1054 = _t1631
        if !isnothing(deconstruct_result1054)
            unwrapped1055 = deconstruct_result1054
            pretty_date(pp, unwrapped1055)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1632 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1632 = nothing
            end
            deconstruct_result1052 = _t1632
            if !isnothing(deconstruct_result1052)
                unwrapped1053 = deconstruct_result1052
                pretty_datetime(pp, unwrapped1053)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1633 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1633 = nothing
                end
                deconstruct_result1050 = _t1633
                if !isnothing(deconstruct_result1050)
                    unwrapped1051 = deconstruct_result1050
                    write(pp, format_string(pp, unwrapped1051))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1634 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1634 = nothing
                    end
                    deconstruct_result1048 = _t1634
                    if !isnothing(deconstruct_result1048)
                        unwrapped1049 = deconstruct_result1048
                        write(pp, format_int32(pp, unwrapped1049))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1635 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1635 = nothing
                        end
                        deconstruct_result1046 = _t1635
                        if !isnothing(deconstruct_result1046)
                            unwrapped1047 = deconstruct_result1046
                            write(pp, format_int(pp, unwrapped1047))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1636 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1636 = nothing
                            end
                            deconstruct_result1044 = _t1636
                            if !isnothing(deconstruct_result1044)
                                unwrapped1045 = deconstruct_result1044
                                write(pp, format_float32(pp, unwrapped1045))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1637 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1637 = nothing
                                end
                                deconstruct_result1042 = _t1637
                                if !isnothing(deconstruct_result1042)
                                    unwrapped1043 = deconstruct_result1042
                                    write(pp, format_float(pp, unwrapped1043))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1638 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1638 = nothing
                                    end
                                    deconstruct_result1040 = _t1638
                                    if !isnothing(deconstruct_result1040)
                                        unwrapped1041 = deconstruct_result1040
                                        write(pp, format_uint32(pp, unwrapped1041))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1639 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1639 = nothing
                                        end
                                        deconstruct_result1038 = _t1639
                                        if !isnothing(deconstruct_result1038)
                                            unwrapped1039 = deconstruct_result1038
                                            write(pp, format_uint128(pp, unwrapped1039))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1640 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1640 = nothing
                                            end
                                            deconstruct_result1036 = _t1640
                                            if !isnothing(deconstruct_result1036)
                                                unwrapped1037 = deconstruct_result1036
                                                write(pp, format_int128(pp, unwrapped1037))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1641 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1641 = nothing
                                                end
                                                deconstruct_result1034 = _t1641
                                                if !isnothing(deconstruct_result1034)
                                                    unwrapped1035 = deconstruct_result1034
                                                    write(pp, format_decimal(pp, unwrapped1035))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1642 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1642 = nothing
                                                    end
                                                    deconstruct_result1032 = _t1642
                                                    if !isnothing(deconstruct_result1032)
                                                        unwrapped1033 = deconstruct_result1032
                                                        pretty_boolean_value(pp, unwrapped1033)
                                                    else
                                                        fields1031 = msg
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
    flat1062 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1062)
        write(pp, flat1062)
        return nothing
    else
        _dollar_dollar = msg
        fields1057 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1058 = fields1057
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1059 = unwrapped_fields1058[1]
        write(pp, format_int(pp, field1059))
        newline(pp)
        field1060 = unwrapped_fields1058[2]
        write(pp, format_int(pp, field1060))
        newline(pp)
        field1061 = unwrapped_fields1058[3]
        write(pp, format_int(pp, field1061))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1073 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1073)
        write(pp, flat1073)
        return nothing
    else
        _dollar_dollar = msg
        fields1063 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1064 = fields1063
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1065 = unwrapped_fields1064[1]
        write(pp, format_int(pp, field1065))
        newline(pp)
        field1066 = unwrapped_fields1064[2]
        write(pp, format_int(pp, field1066))
        newline(pp)
        field1067 = unwrapped_fields1064[3]
        write(pp, format_int(pp, field1067))
        newline(pp)
        field1068 = unwrapped_fields1064[4]
        write(pp, format_int(pp, field1068))
        newline(pp)
        field1069 = unwrapped_fields1064[5]
        write(pp, format_int(pp, field1069))
        newline(pp)
        field1070 = unwrapped_fields1064[6]
        write(pp, format_int(pp, field1070))
        field1071 = unwrapped_fields1064[7]
        if !isnothing(field1071)
            newline(pp)
            opt_val1072 = field1071
            write(pp, format_int(pp, opt_val1072))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1078 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1078)
        write(pp, flat1078)
        return nothing
    else
        _dollar_dollar = msg
        fields1074 = _dollar_dollar.args
        unwrapped_fields1075 = fields1074
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1075)
            newline(pp)
            for (i1643, elem1076) in enumerate(unwrapped_fields1075)
                i1077 = i1643 - 1
                if (i1077 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1076)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1083 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1083)
        write(pp, flat1083)
        return nothing
    else
        _dollar_dollar = msg
        fields1079 = _dollar_dollar.args
        unwrapped_fields1080 = fields1079
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1080)
            newline(pp)
            for (i1644, elem1081) in enumerate(unwrapped_fields1080)
                i1082 = i1644 - 1
                if (i1082 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1081)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1086 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1086)
        write(pp, flat1086)
        return nothing
    else
        _dollar_dollar = msg
        fields1084 = _dollar_dollar.arg
        unwrapped_fields1085 = fields1084
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1085)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1092 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        _dollar_dollar = msg
        fields1087 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1088 = fields1087
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1089 = unwrapped_fields1088[1]
        pretty_name(pp, field1089)
        newline(pp)
        field1090 = unwrapped_fields1088[2]
        pretty_ffi_args(pp, field1090)
        newline(pp)
        field1091 = unwrapped_fields1088[3]
        pretty_terms(pp, field1091)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1094 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1094)
        write(pp, flat1094)
        return nothing
    else
        fields1093 = msg
        write(pp, ":")
        write(pp, fields1093)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1098 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1098)
        write(pp, flat1098)
        return nothing
    else
        fields1095 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1095)
            newline(pp)
            for (i1645, elem1096) in enumerate(fields1095)
                i1097 = i1645 - 1
                if (i1097 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1096)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1105 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1105)
        write(pp, flat1105)
        return nothing
    else
        _dollar_dollar = msg
        fields1099 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1100 = fields1099
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1101 = unwrapped_fields1100[1]
        pretty_relation_id(pp, field1101)
        field1102 = unwrapped_fields1100[2]
        if !isempty(field1102)
            newline(pp)
            for (i1646, elem1103) in enumerate(field1102)
                i1104 = i1646 - 1
                if (i1104 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1103)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1112 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1112)
        write(pp, flat1112)
        return nothing
    else
        _dollar_dollar = msg
        fields1106 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1107 = fields1106
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1108 = unwrapped_fields1107[1]
        pretty_name(pp, field1108)
        field1109 = unwrapped_fields1107[2]
        if !isempty(field1109)
            newline(pp)
            for (i1647, elem1110) in enumerate(field1109)
                i1111 = i1647 - 1
                if (i1111 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1110)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1128 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1128)
        write(pp, flat1128)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1648 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1648 = nothing
        end
        guard_result1127 = _t1648
        if !isnothing(guard_result1127)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1649 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1649 = nothing
            end
            guard_result1126 = _t1649
            if !isnothing(guard_result1126)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1650 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1650 = nothing
                end
                guard_result1125 = _t1650
                if !isnothing(guard_result1125)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1651 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1651 = nothing
                    end
                    guard_result1124 = _t1651
                    if !isnothing(guard_result1124)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1652 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1652 = nothing
                        end
                        guard_result1123 = _t1652
                        if !isnothing(guard_result1123)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1653 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1653 = nothing
                            end
                            guard_result1122 = _t1653
                            if !isnothing(guard_result1122)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1654 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1654 = nothing
                                end
                                guard_result1121 = _t1654
                                if !isnothing(guard_result1121)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1655 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1655 = nothing
                                    end
                                    guard_result1120 = _t1655
                                    if !isnothing(guard_result1120)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1656 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1656 = nothing
                                        end
                                        guard_result1119 = _t1656
                                        if !isnothing(guard_result1119)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1113 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1114 = fields1113
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1115 = unwrapped_fields1114[1]
                                            pretty_name(pp, field1115)
                                            field1116 = unwrapped_fields1114[2]
                                            if !isempty(field1116)
                                                newline(pp)
                                                for (i1657, elem1117) in enumerate(field1116)
                                                    i1118 = i1657 - 1
                                                    if (i1118 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1117)
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
    flat1133 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1133)
        write(pp, flat1133)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1658 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1658 = nothing
        end
        fields1129 = _t1658
        unwrapped_fields1130 = fields1129
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1131 = unwrapped_fields1130[1]
        pretty_term(pp, field1131)
        newline(pp)
        field1132 = unwrapped_fields1130[2]
        pretty_term(pp, field1132)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1138 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1138)
        write(pp, flat1138)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1659 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1659 = nothing
        end
        fields1134 = _t1659
        unwrapped_fields1135 = fields1134
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1136 = unwrapped_fields1135[1]
        pretty_term(pp, field1136)
        newline(pp)
        field1137 = unwrapped_fields1135[2]
        pretty_term(pp, field1137)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1143 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1143)
        write(pp, flat1143)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1660 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1660 = nothing
        end
        fields1139 = _t1660
        unwrapped_fields1140 = fields1139
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1141 = unwrapped_fields1140[1]
        pretty_term(pp, field1141)
        newline(pp)
        field1142 = unwrapped_fields1140[2]
        pretty_term(pp, field1142)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1148 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1148)
        write(pp, flat1148)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1661 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1661 = nothing
        end
        fields1144 = _t1661
        unwrapped_fields1145 = fields1144
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1146 = unwrapped_fields1145[1]
        pretty_term(pp, field1146)
        newline(pp)
        field1147 = unwrapped_fields1145[2]
        pretty_term(pp, field1147)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1153 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1153)
        write(pp, flat1153)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1662 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1662 = nothing
        end
        fields1149 = _t1662
        unwrapped_fields1150 = fields1149
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1151 = unwrapped_fields1150[1]
        pretty_term(pp, field1151)
        newline(pp)
        field1152 = unwrapped_fields1150[2]
        pretty_term(pp, field1152)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1159 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1159)
        write(pp, flat1159)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1663 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1663 = nothing
        end
        fields1154 = _t1663
        unwrapped_fields1155 = fields1154
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1156 = unwrapped_fields1155[1]
        pretty_term(pp, field1156)
        newline(pp)
        field1157 = unwrapped_fields1155[2]
        pretty_term(pp, field1157)
        newline(pp)
        field1158 = unwrapped_fields1155[3]
        pretty_term(pp, field1158)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1165 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1165)
        write(pp, flat1165)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1664 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1664 = nothing
        end
        fields1160 = _t1664
        unwrapped_fields1161 = fields1160
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1162 = unwrapped_fields1161[1]
        pretty_term(pp, field1162)
        newline(pp)
        field1163 = unwrapped_fields1161[2]
        pretty_term(pp, field1163)
        newline(pp)
        field1164 = unwrapped_fields1161[3]
        pretty_term(pp, field1164)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1171 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1171)
        write(pp, flat1171)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1665 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1665 = nothing
        end
        fields1166 = _t1665
        unwrapped_fields1167 = fields1166
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1168 = unwrapped_fields1167[1]
        pretty_term(pp, field1168)
        newline(pp)
        field1169 = unwrapped_fields1167[2]
        pretty_term(pp, field1169)
        newline(pp)
        field1170 = unwrapped_fields1167[3]
        pretty_term(pp, field1170)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1177 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1177)
        write(pp, flat1177)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1666 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1666 = nothing
        end
        fields1172 = _t1666
        unwrapped_fields1173 = fields1172
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1174 = unwrapped_fields1173[1]
        pretty_term(pp, field1174)
        newline(pp)
        field1175 = unwrapped_fields1173[2]
        pretty_term(pp, field1175)
        newline(pp)
        field1176 = unwrapped_fields1173[3]
        pretty_term(pp, field1176)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1182 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1182)
        write(pp, flat1182)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1667 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1667 = nothing
        end
        deconstruct_result1180 = _t1667
        if !isnothing(deconstruct_result1180)
            unwrapped1181 = deconstruct_result1180
            pretty_specialized_value(pp, unwrapped1181)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1668 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1668 = nothing
            end
            deconstruct_result1178 = _t1668
            if !isnothing(deconstruct_result1178)
                unwrapped1179 = deconstruct_result1178
                pretty_term(pp, unwrapped1179)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1184 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1184)
        write(pp, flat1184)
        return nothing
    else
        fields1183 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1183)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1191 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1191)
        write(pp, flat1191)
        return nothing
    else
        _dollar_dollar = msg
        fields1185 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1186 = fields1185
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1187 = unwrapped_fields1186[1]
        pretty_name(pp, field1187)
        field1188 = unwrapped_fields1186[2]
        if !isempty(field1188)
            newline(pp)
            for (i1669, elem1189) in enumerate(field1188)
                i1190 = i1669 - 1
                if (i1190 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1189)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1196 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1196)
        write(pp, flat1196)
        return nothing
    else
        _dollar_dollar = msg
        fields1192 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1193 = fields1192
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1194 = unwrapped_fields1193[1]
        pretty_term(pp, field1194)
        newline(pp)
        field1195 = unwrapped_fields1193[2]
        pretty_term(pp, field1195)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1200 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1200)
        write(pp, flat1200)
        return nothing
    else
        fields1197 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1197)
            newline(pp)
            for (i1670, elem1198) in enumerate(fields1197)
                i1199 = i1670 - 1
                if (i1199 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1198)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1207 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1207)
        write(pp, flat1207)
        return nothing
    else
        _dollar_dollar = msg
        fields1201 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1202 = fields1201
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1203 = unwrapped_fields1202[1]
        pretty_name(pp, field1203)
        field1204 = unwrapped_fields1202[2]
        if !isempty(field1204)
            newline(pp)
            for (i1671, elem1205) in enumerate(field1204)
                i1206 = i1671 - 1
                if (i1206 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1205)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1214 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1214)
        write(pp, flat1214)
        return nothing
    else
        _dollar_dollar = msg
        fields1208 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1209 = fields1208
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1210 = unwrapped_fields1209[1]
        if !isempty(field1210)
            newline(pp)
            for (i1672, elem1211) in enumerate(field1210)
                i1212 = i1672 - 1
                if (i1212 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1211)
            end
        end
        newline(pp)
        field1213 = unwrapped_fields1209[2]
        pretty_script(pp, field1213)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1219 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1219)
        write(pp, flat1219)
        return nothing
    else
        _dollar_dollar = msg
        fields1215 = _dollar_dollar.constructs
        unwrapped_fields1216 = fields1215
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1216)
            newline(pp)
            for (i1673, elem1217) in enumerate(unwrapped_fields1216)
                i1218 = i1673 - 1
                if (i1218 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1217)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1224 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1224)
        write(pp, flat1224)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1674 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1674 = nothing
        end
        deconstruct_result1222 = _t1674
        if !isnothing(deconstruct_result1222)
            unwrapped1223 = deconstruct_result1222
            pretty_loop(pp, unwrapped1223)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1675 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1675 = nothing
            end
            deconstruct_result1220 = _t1675
            if !isnothing(deconstruct_result1220)
                unwrapped1221 = deconstruct_result1220
                pretty_instruction(pp, unwrapped1221)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1229 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1229)
        write(pp, flat1229)
        return nothing
    else
        _dollar_dollar = msg
        fields1225 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1226 = fields1225
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1227 = unwrapped_fields1226[1]
        pretty_init(pp, field1227)
        newline(pp)
        field1228 = unwrapped_fields1226[2]
        pretty_script(pp, field1228)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1233 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1233)
        write(pp, flat1233)
        return nothing
    else
        fields1230 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1230)
            newline(pp)
            for (i1676, elem1231) in enumerate(fields1230)
                i1232 = i1676 - 1
                if (i1232 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1231)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1244 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1244)
        write(pp, flat1244)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1677 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1677 = nothing
        end
        deconstruct_result1242 = _t1677
        if !isnothing(deconstruct_result1242)
            unwrapped1243 = deconstruct_result1242
            pretty_assign(pp, unwrapped1243)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1678 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1678 = nothing
            end
            deconstruct_result1240 = _t1678
            if !isnothing(deconstruct_result1240)
                unwrapped1241 = deconstruct_result1240
                pretty_upsert(pp, unwrapped1241)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1679 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1679 = nothing
                end
                deconstruct_result1238 = _t1679
                if !isnothing(deconstruct_result1238)
                    unwrapped1239 = deconstruct_result1238
                    pretty_break(pp, unwrapped1239)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1680 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1680 = nothing
                    end
                    deconstruct_result1236 = _t1680
                    if !isnothing(deconstruct_result1236)
                        unwrapped1237 = deconstruct_result1236
                        pretty_monoid_def(pp, unwrapped1237)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1681 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1681 = nothing
                        end
                        deconstruct_result1234 = _t1681
                        if !isnothing(deconstruct_result1234)
                            unwrapped1235 = deconstruct_result1234
                            pretty_monus_def(pp, unwrapped1235)
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
    flat1251 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1251)
        write(pp, flat1251)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1682 = _dollar_dollar.attrs
        else
            _t1682 = nothing
        end
        fields1245 = (_dollar_dollar.name, _dollar_dollar.body, _t1682,)
        unwrapped_fields1246 = fields1245
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1247 = unwrapped_fields1246[1]
        pretty_relation_id(pp, field1247)
        newline(pp)
        field1248 = unwrapped_fields1246[2]
        pretty_abstraction(pp, field1248)
        field1249 = unwrapped_fields1246[3]
        if !isnothing(field1249)
            newline(pp)
            opt_val1250 = field1249
            pretty_attrs(pp, opt_val1250)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1258 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1258)
        write(pp, flat1258)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1683 = _dollar_dollar.attrs
        else
            _t1683 = nothing
        end
        fields1252 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1683,)
        unwrapped_fields1253 = fields1252
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1254 = unwrapped_fields1253[1]
        pretty_relation_id(pp, field1254)
        newline(pp)
        field1255 = unwrapped_fields1253[2]
        pretty_abstraction_with_arity(pp, field1255)
        field1256 = unwrapped_fields1253[3]
        if !isnothing(field1256)
            newline(pp)
            opt_val1257 = field1256
            pretty_attrs(pp, opt_val1257)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1263 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1263)
        write(pp, flat1263)
        return nothing
    else
        _dollar_dollar = msg
        _t1684 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1259 = (_t1684, _dollar_dollar[1].value,)
        unwrapped_fields1260 = fields1259
        write(pp, "(")
        indent!(pp)
        field1261 = unwrapped_fields1260[1]
        pretty_bindings(pp, field1261)
        newline(pp)
        field1262 = unwrapped_fields1260[2]
        pretty_formula(pp, field1262)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1270 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1270)
        write(pp, flat1270)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1685 = _dollar_dollar.attrs
        else
            _t1685 = nothing
        end
        fields1264 = (_dollar_dollar.name, _dollar_dollar.body, _t1685,)
        unwrapped_fields1265 = fields1264
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1266 = unwrapped_fields1265[1]
        pretty_relation_id(pp, field1266)
        newline(pp)
        field1267 = unwrapped_fields1265[2]
        pretty_abstraction(pp, field1267)
        field1268 = unwrapped_fields1265[3]
        if !isnothing(field1268)
            newline(pp)
            opt_val1269 = field1268
            pretty_attrs(pp, opt_val1269)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1278 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1278)
        write(pp, flat1278)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1686 = _dollar_dollar.attrs
        else
            _t1686 = nothing
        end
        fields1271 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1686,)
        unwrapped_fields1272 = fields1271
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1273 = unwrapped_fields1272[1]
        pretty_monoid(pp, field1273)
        newline(pp)
        field1274 = unwrapped_fields1272[2]
        pretty_relation_id(pp, field1274)
        newline(pp)
        field1275 = unwrapped_fields1272[3]
        pretty_abstraction_with_arity(pp, field1275)
        field1276 = unwrapped_fields1272[4]
        if !isnothing(field1276)
            newline(pp)
            opt_val1277 = field1276
            pretty_attrs(pp, opt_val1277)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1287 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1287)
        write(pp, flat1287)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1687 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1687 = nothing
        end
        deconstruct_result1285 = _t1687
        if !isnothing(deconstruct_result1285)
            unwrapped1286 = deconstruct_result1285
            pretty_or_monoid(pp, unwrapped1286)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1688 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1688 = nothing
            end
            deconstruct_result1283 = _t1688
            if !isnothing(deconstruct_result1283)
                unwrapped1284 = deconstruct_result1283
                pretty_min_monoid(pp, unwrapped1284)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1689 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1689 = nothing
                end
                deconstruct_result1281 = _t1689
                if !isnothing(deconstruct_result1281)
                    unwrapped1282 = deconstruct_result1281
                    pretty_max_monoid(pp, unwrapped1282)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1690 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1690 = nothing
                    end
                    deconstruct_result1279 = _t1690
                    if !isnothing(deconstruct_result1279)
                        unwrapped1280 = deconstruct_result1279
                        pretty_sum_monoid(pp, unwrapped1280)
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
    fields1288 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1291 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1291)
        write(pp, flat1291)
        return nothing
    else
        _dollar_dollar = msg
        fields1289 = _dollar_dollar.var"#type"
        unwrapped_fields1290 = fields1289
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1290)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1294 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1294)
        write(pp, flat1294)
        return nothing
    else
        _dollar_dollar = msg
        fields1292 = _dollar_dollar.var"#type"
        unwrapped_fields1293 = fields1292
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1293)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1297 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1297)
        write(pp, flat1297)
        return nothing
    else
        _dollar_dollar = msg
        fields1295 = _dollar_dollar.var"#type"
        unwrapped_fields1296 = fields1295
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1296)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1305 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1305)
        write(pp, flat1305)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1691 = _dollar_dollar.attrs
        else
            _t1691 = nothing
        end
        fields1298 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1691,)
        unwrapped_fields1299 = fields1298
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1300 = unwrapped_fields1299[1]
        pretty_monoid(pp, field1300)
        newline(pp)
        field1301 = unwrapped_fields1299[2]
        pretty_relation_id(pp, field1301)
        newline(pp)
        field1302 = unwrapped_fields1299[3]
        pretty_abstraction_with_arity(pp, field1302)
        field1303 = unwrapped_fields1299[4]
        if !isnothing(field1303)
            newline(pp)
            opt_val1304 = field1303
            pretty_attrs(pp, opt_val1304)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1312 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1312)
        write(pp, flat1312)
        return nothing
    else
        _dollar_dollar = msg
        fields1306 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1307 = fields1306
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1308 = unwrapped_fields1307[1]
        pretty_relation_id(pp, field1308)
        newline(pp)
        field1309 = unwrapped_fields1307[2]
        pretty_abstraction(pp, field1309)
        newline(pp)
        field1310 = unwrapped_fields1307[3]
        pretty_functional_dependency_keys(pp, field1310)
        newline(pp)
        field1311 = unwrapped_fields1307[4]
        pretty_functional_dependency_values(pp, field1311)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1316 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1316)
        write(pp, flat1316)
        return nothing
    else
        fields1313 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1313)
            newline(pp)
            for (i1692, elem1314) in enumerate(fields1313)
                i1315 = i1692 - 1
                if (i1315 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1314)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1320 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1320)
        write(pp, flat1320)
        return nothing
    else
        fields1317 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1317)
            newline(pp)
            for (i1693, elem1318) in enumerate(fields1317)
                i1319 = i1693 - 1
                if (i1319 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1318)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1329 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1329)
        write(pp, flat1329)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1694 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1694 = nothing
        end
        deconstruct_result1327 = _t1694
        if !isnothing(deconstruct_result1327)
            unwrapped1328 = deconstruct_result1327
            pretty_edb(pp, unwrapped1328)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1695 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1695 = nothing
            end
            deconstruct_result1325 = _t1695
            if !isnothing(deconstruct_result1325)
                unwrapped1326 = deconstruct_result1325
                pretty_betree_relation(pp, unwrapped1326)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1696 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1696 = nothing
                end
                deconstruct_result1323 = _t1696
                if !isnothing(deconstruct_result1323)
                    unwrapped1324 = deconstruct_result1323
                    pretty_csv_data(pp, unwrapped1324)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1697 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1697 = nothing
                    end
                    deconstruct_result1321 = _t1697
                    if !isnothing(deconstruct_result1321)
                        unwrapped1322 = deconstruct_result1321
                        pretty_iceberg_data(pp, unwrapped1322)
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
    flat1335 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1335)
        write(pp, flat1335)
        return nothing
    else
        _dollar_dollar = msg
        fields1330 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1331 = fields1330
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1332 = unwrapped_fields1331[1]
        pretty_relation_id(pp, field1332)
        newline(pp)
        field1333 = unwrapped_fields1331[2]
        pretty_edb_path(pp, field1333)
        newline(pp)
        field1334 = unwrapped_fields1331[3]
        pretty_edb_types(pp, field1334)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1339 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1339)
        write(pp, flat1339)
        return nothing
    else
        fields1336 = msg
        write(pp, "[")
        indent!(pp)
        for (i1698, elem1337) in enumerate(fields1336)
            i1338 = i1698 - 1
            if (i1338 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1337))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1343 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1343)
        write(pp, flat1343)
        return nothing
    else
        fields1340 = msg
        write(pp, "[")
        indent!(pp)
        for (i1699, elem1341) in enumerate(fields1340)
            i1342 = i1699 - 1
            if (i1342 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1341)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1348 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1348)
        write(pp, flat1348)
        return nothing
    else
        _dollar_dollar = msg
        fields1344 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1345 = fields1344
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1346 = unwrapped_fields1345[1]
        pretty_relation_id(pp, field1346)
        newline(pp)
        field1347 = unwrapped_fields1345[2]
        pretty_betree_info(pp, field1347)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1354 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1354)
        write(pp, flat1354)
        return nothing
    else
        _dollar_dollar = msg
        _t1700 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1349 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1700,)
        unwrapped_fields1350 = fields1349
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1351 = unwrapped_fields1350[1]
        pretty_betree_info_key_types(pp, field1351)
        newline(pp)
        field1352 = unwrapped_fields1350[2]
        pretty_betree_info_value_types(pp, field1352)
        newline(pp)
        field1353 = unwrapped_fields1350[3]
        pretty_config_dict(pp, field1353)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1358 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1358)
        write(pp, flat1358)
        return nothing
    else
        fields1355 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1355)
            newline(pp)
            for (i1701, elem1356) in enumerate(fields1355)
                i1357 = i1701 - 1
                if (i1357 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1356)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1362 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1362)
        write(pp, flat1362)
        return nothing
    else
        fields1359 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1359)
            newline(pp)
            for (i1702, elem1360) in enumerate(fields1359)
                i1361 = i1702 - 1
                if (i1361 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1360)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1369 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1369)
        write(pp, flat1369)
        return nothing
    else
        _dollar_dollar = msg
        fields1363 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1364 = fields1363
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1365 = unwrapped_fields1364[1]
        pretty_csvlocator(pp, field1365)
        newline(pp)
        field1366 = unwrapped_fields1364[2]
        pretty_csv_config(pp, field1366)
        newline(pp)
        field1367 = unwrapped_fields1364[3]
        pretty_gnf_columns(pp, field1367)
        newline(pp)
        field1368 = unwrapped_fields1364[4]
        pretty_csv_asof(pp, field1368)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1376 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1703 = _dollar_dollar.paths
        else
            _t1703 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1704 = String(copy(_dollar_dollar.inline_data))
        else
            _t1704 = nothing
        end
        fields1370 = (_t1703, _t1704,)
        unwrapped_fields1371 = fields1370
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1372 = unwrapped_fields1371[1]
        if !isnothing(field1372)
            newline(pp)
            opt_val1373 = field1372
            pretty_csv_locator_paths(pp, opt_val1373)
        end
        field1374 = unwrapped_fields1371[2]
        if !isnothing(field1374)
            newline(pp)
            opt_val1375 = field1374
            pretty_csv_locator_inline_data(pp, opt_val1375)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1380 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1380)
        write(pp, flat1380)
        return nothing
    else
        fields1377 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1377)
            newline(pp)
            for (i1705, elem1378) in enumerate(fields1377)
                i1379 = i1705 - 1
                if (i1379 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1378))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1382 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1382)
        write(pp, flat1382)
        return nothing
    else
        fields1381 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1381))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1385 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1385)
        write(pp, flat1385)
        return nothing
    else
        _dollar_dollar = msg
        _t1706 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1383 = _t1706
        unwrapped_fields1384 = fields1383
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1384)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1389 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1389)
        write(pp, flat1389)
        return nothing
    else
        fields1386 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1386)
            newline(pp)
            for (i1707, elem1387) in enumerate(fields1386)
                i1388 = i1707 - 1
                if (i1388 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1387)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1398 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1398)
        write(pp, flat1398)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1708 = _dollar_dollar.target_id
        else
            _t1708 = nothing
        end
        fields1390 = (_dollar_dollar.column_path, _t1708, _dollar_dollar.types,)
        unwrapped_fields1391 = fields1390
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1392 = unwrapped_fields1391[1]
        pretty_gnf_column_path(pp, field1392)
        field1393 = unwrapped_fields1391[2]
        if !isnothing(field1393)
            newline(pp)
            opt_val1394 = field1393
            pretty_relation_id(pp, opt_val1394)
        end
        newline(pp)
        write(pp, "[")
        field1395 = unwrapped_fields1391[3]
        for (i1709, elem1396) in enumerate(field1395)
            i1397 = i1709 - 1
            if (i1397 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1396)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1405 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1405)
        write(pp, flat1405)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1710 = _dollar_dollar[1]
        else
            _t1710 = nothing
        end
        deconstruct_result1403 = _t1710
        if !isnothing(deconstruct_result1403)
            unwrapped1404 = deconstruct_result1403
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1404))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1711 = _dollar_dollar
            else
                _t1711 = nothing
            end
            deconstruct_result1399 = _t1711
            if !isnothing(deconstruct_result1399)
                unwrapped1400 = deconstruct_result1399
                write(pp, "[")
                indent!(pp)
                for (i1712, elem1401) in enumerate(unwrapped1400)
                    i1402 = i1712 - 1
                    if (i1402 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1401))
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
    flat1407 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1407)
        write(pp, flat1407)
        return nothing
    else
        fields1406 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1406))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1414 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1414)
        write(pp, flat1414)
        return nothing
    else
        _dollar_dollar = msg
        fields1408 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.returns_delta,)
        unwrapped_fields1409 = fields1408
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1410 = unwrapped_fields1409[1]
        pretty_iceberg_locator(pp, field1410)
        newline(pp)
        field1411 = unwrapped_fields1409[2]
        pretty_iceberg_catalog_config(pp, field1411)
        newline(pp)
        field1412 = unwrapped_fields1409[3]
        pretty_gnf_columns(pp, field1412)
        newline(pp)
        field1413 = unwrapped_fields1409[4]
        pretty_boolean_value(pp, field1413)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1426 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1426)
        write(pp, flat1426)
        return nothing
    else
        _dollar_dollar = msg
        _t1713 = deconstruct_iceberg_locator_from_snapshot_optional(pp, _dollar_dollar)
        _t1714 = deconstruct_iceberg_locator_to_snapshot_optional(pp, _dollar_dollar)
        fields1415 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse, _t1713, _t1714,)
        unwrapped_fields1416 = fields1415
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_name")
        newline(pp)
        field1417 = unwrapped_fields1416[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1417))
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "namespace")
        field1418 = unwrapped_fields1416[2]
        if !isempty(field1418)
            newline(pp)
            for (i1715, elem1419) in enumerate(field1418)
                i1420 = i1715 - 1
                if (i1420 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1419))
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "warehouse")
        newline(pp)
        field1421 = unwrapped_fields1416[3]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1421))
        dedent!(pp)
        write(pp, ")")
        field1422 = unwrapped_fields1416[4]
        if !isnothing(field1422)
            newline(pp)
            opt_val1423 = field1422
            pretty_iceberg_from_snapshot(pp, opt_val1423)
        end
        field1424 = unwrapped_fields1416[5]
        if !isnothing(field1424)
            newline(pp)
            opt_val1425 = field1424
            pretty_iceberg_to_snapshot(pp, opt_val1425)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1428 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1428)
        write(pp, flat1428)
        return nothing
    else
        fields1427 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1427))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1430 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1430)
        write(pp, flat1430)
        return nothing
    else
        fields1429 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1429))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1442 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1442)
        write(pp, flat1442)
        return nothing
    else
        _dollar_dollar = msg
        _t1716 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1431 = (_dollar_dollar.catalog_uri, _t1716, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1432 = fields1431
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "catalog_uri")
        newline(pp)
        field1433 = unwrapped_fields1432[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1433))
        dedent!(pp)
        write(pp, ")")
        field1434 = unwrapped_fields1432[2]
        if !isnothing(field1434)
            newline(pp)
            opt_val1435 = field1434
            pretty_iceberg_catalog_config_scope(pp, opt_val1435)
        end
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "properties")
        field1436 = unwrapped_fields1432[3]
        if !isempty(field1436)
            newline(pp)
            for (i1717, elem1437) in enumerate(field1436)
                i1438 = i1717 - 1
                if (i1438 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1437)
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "auth_properties")
        field1439 = unwrapped_fields1432[4]
        if !isempty(field1439)
            newline(pp)
            for (i1718, elem1440) in enumerate(field1439)
                i1441 = i1718 - 1
                if (i1441 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1440)
            end
        end
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1444 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1444)
        write(pp, flat1444)
        return nothing
    else
        fields1443 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1443))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1449 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1449)
        write(pp, flat1449)
        return nothing
    else
        _dollar_dollar = msg
        fields1445 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1446 = fields1445
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1447 = unwrapped_fields1446[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1447))
        newline(pp)
        field1448 = unwrapped_fields1446[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1448))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1454 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1454)
        write(pp, flat1454)
        return nothing
    else
        _dollar_dollar = msg
        _t1719 = mask_secret_value(pp, _dollar_dollar)
        fields1450 = (_dollar_dollar[1], _t1719,)
        unwrapped_fields1451 = fields1450
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1452 = unwrapped_fields1451[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1452))
        newline(pp)
        field1453 = unwrapped_fields1451[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1453))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1457 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1457)
        write(pp, flat1457)
        return nothing
    else
        _dollar_dollar = msg
        fields1455 = _dollar_dollar.fragment_id
        unwrapped_fields1456 = fields1455
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1456)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1462 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1462)
        write(pp, flat1462)
        return nothing
    else
        _dollar_dollar = msg
        fields1458 = _dollar_dollar.relations
        unwrapped_fields1459 = fields1458
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1459)
            newline(pp)
            for (i1720, elem1460) in enumerate(unwrapped_fields1459)
                i1461 = i1720 - 1
                if (i1461 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1460)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1467 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1467)
        write(pp, flat1467)
        return nothing
    else
        _dollar_dollar = msg
        fields1463 = _dollar_dollar.mappings
        unwrapped_fields1464 = fields1463
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1464)
            newline(pp)
            for (i1721, elem1465) in enumerate(unwrapped_fields1464)
                i1466 = i1721 - 1
                if (i1466 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1465)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1472 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1472)
        write(pp, flat1472)
        return nothing
    else
        _dollar_dollar = msg
        fields1468 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1469 = fields1468
        field1470 = unwrapped_fields1469[1]
        pretty_edb_path(pp, field1470)
        write(pp, " ")
        field1471 = unwrapped_fields1469[2]
        pretty_relation_id(pp, field1471)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1476 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1476)
        write(pp, flat1476)
        return nothing
    else
        fields1473 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1473)
            newline(pp)
            for (i1722, elem1474) in enumerate(fields1473)
                i1475 = i1722 - 1
                if (i1475 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1474)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1487 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1487)
        write(pp, flat1487)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1723 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1723 = nothing
        end
        deconstruct_result1485 = _t1723
        if !isnothing(deconstruct_result1485)
            unwrapped1486 = deconstruct_result1485
            pretty_demand(pp, unwrapped1486)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1724 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1724 = nothing
            end
            deconstruct_result1483 = _t1724
            if !isnothing(deconstruct_result1483)
                unwrapped1484 = deconstruct_result1483
                pretty_output(pp, unwrapped1484)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1725 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1725 = nothing
                end
                deconstruct_result1481 = _t1725
                if !isnothing(deconstruct_result1481)
                    unwrapped1482 = deconstruct_result1481
                    pretty_what_if(pp, unwrapped1482)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1726 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1726 = nothing
                    end
                    deconstruct_result1479 = _t1726
                    if !isnothing(deconstruct_result1479)
                        unwrapped1480 = deconstruct_result1479
                        pretty_abort(pp, unwrapped1480)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1727 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1727 = nothing
                        end
                        deconstruct_result1477 = _t1727
                        if !isnothing(deconstruct_result1477)
                            unwrapped1478 = deconstruct_result1477
                            pretty_export(pp, unwrapped1478)
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
    flat1490 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1490)
        write(pp, flat1490)
        return nothing
    else
        _dollar_dollar = msg
        fields1488 = _dollar_dollar.relation_id
        unwrapped_fields1489 = fields1488
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1489)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1495 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1495)
        write(pp, flat1495)
        return nothing
    else
        _dollar_dollar = msg
        fields1491 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1492 = fields1491
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1493 = unwrapped_fields1492[1]
        pretty_name(pp, field1493)
        newline(pp)
        field1494 = unwrapped_fields1492[2]
        pretty_relation_id(pp, field1494)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1500 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1500)
        write(pp, flat1500)
        return nothing
    else
        _dollar_dollar = msg
        fields1496 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1497 = fields1496
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1498 = unwrapped_fields1497[1]
        pretty_name(pp, field1498)
        newline(pp)
        field1499 = unwrapped_fields1497[2]
        pretty_epoch(pp, field1499)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1506 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1506)
        write(pp, flat1506)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1728 = _dollar_dollar.name
        else
            _t1728 = nothing
        end
        fields1501 = (_t1728, _dollar_dollar.relation_id,)
        unwrapped_fields1502 = fields1501
        write(pp, "(abort")
        indent_sexp!(pp)
        field1503 = unwrapped_fields1502[1]
        if !isnothing(field1503)
            newline(pp)
            opt_val1504 = field1503
            pretty_name(pp, opt_val1504)
        end
        newline(pp)
        field1505 = unwrapped_fields1502[2]
        pretty_relation_id(pp, field1505)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1511 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1511)
        write(pp, flat1511)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1729 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1729 = nothing
        end
        deconstruct_result1509 = _t1729
        if !isnothing(deconstruct_result1509)
            unwrapped1510 = deconstruct_result1509
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1510)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1730 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1730 = nothing
            end
            deconstruct_result1507 = _t1730
            if !isnothing(deconstruct_result1507)
                unwrapped1508 = deconstruct_result1507
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1508)
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
    flat1522 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1522)
        write(pp, flat1522)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1731 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1731 = nothing
        end
        deconstruct_result1517 = _t1731
        if !isnothing(deconstruct_result1517)
            unwrapped1518 = deconstruct_result1517
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1519 = unwrapped1518[1]
            pretty_export_csv_path(pp, field1519)
            newline(pp)
            field1520 = unwrapped1518[2]
            pretty_export_csv_source(pp, field1520)
            newline(pp)
            field1521 = unwrapped1518[3]
            pretty_csv_config(pp, field1521)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1733 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1732 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1733,)
            else
                _t1732 = nothing
            end
            deconstruct_result1512 = _t1732
            if !isnothing(deconstruct_result1512)
                unwrapped1513 = deconstruct_result1512
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1514 = unwrapped1513[1]
                pretty_export_csv_path(pp, field1514)
                newline(pp)
                field1515 = unwrapped1513[2]
                pretty_export_csv_columns_list(pp, field1515)
                newline(pp)
                field1516 = unwrapped1513[3]
                pretty_config_dict(pp, field1516)
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
    flat1524 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1524)
        write(pp, flat1524)
        return nothing
    else
        fields1523 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1523))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1531 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1531)
        write(pp, flat1531)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1734 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1734 = nothing
        end
        deconstruct_result1527 = _t1734
        if !isnothing(deconstruct_result1527)
            unwrapped1528 = deconstruct_result1527
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1528)
                newline(pp)
                for (i1735, elem1529) in enumerate(unwrapped1528)
                    i1530 = i1735 - 1
                    if (i1530 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1529)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1736 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1736 = nothing
            end
            deconstruct_result1525 = _t1736
            if !isnothing(deconstruct_result1525)
                unwrapped1526 = deconstruct_result1525
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1526)
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
    flat1536 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1536)
        write(pp, flat1536)
        return nothing
    else
        _dollar_dollar = msg
        fields1532 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1533 = fields1532
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1534 = unwrapped_fields1533[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1534))
        newline(pp)
        field1535 = unwrapped_fields1533[2]
        pretty_relation_id(pp, field1535)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1540 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1540)
        write(pp, flat1540)
        return nothing
    else
        fields1537 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1537)
            newline(pp)
            for (i1737, elem1538) in enumerate(fields1537)
                i1539 = i1737 - 1
                if (i1539 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1538)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1554 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1554)
        write(pp, flat1554)
        return nothing
    else
        _dollar_dollar = msg
        _t1738 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1541 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, _dollar_dollar.columns, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1738,)
        unwrapped_fields1542 = fields1541
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1543 = unwrapped_fields1542[1]
        pretty_iceberg_locator(pp, field1543)
        newline(pp)
        field1544 = unwrapped_fields1542[2]
        pretty_iceberg_catalog_config(pp, field1544)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_def")
        newline(pp)
        field1545 = unwrapped_fields1542[3]
        pretty_relation_id(pp, field1545)
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "columns")
        field1546 = unwrapped_fields1542[4]
        if !isempty(field1546)
            newline(pp)
            for (i1739, elem1547) in enumerate(field1546)
                i1548 = i1739 - 1
                if (i1548 > 0)
                    newline(pp)
                end
                pretty_export_gnf_column(pp, elem1547)
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_properties")
        field1549 = unwrapped_fields1542[5]
        if !isempty(field1549)
            newline(pp)
            for (i1740, elem1550) in enumerate(field1549)
                i1551 = i1740 - 1
                if (i1551 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1550)
            end
        end
        dedent!(pp)
        write(pp, ")")
        field1552 = unwrapped_fields1542[6]
        if !isnothing(field1552)
            newline(pp)
            opt_val1553 = field1552
            pretty_config_dict(pp, opt_val1553)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_gnf_column(pp::PrettyPrinter, msg::Proto.ExportGNFColumn)
    flat1559 = try_flat(pp, msg, pretty_export_gnf_column)
    if !isnothing(flat1559)
        write(pp, flat1559)
        return nothing
    else
        _dollar_dollar = msg
        fields1555 = (_dollar_dollar.name, _dollar_dollar.nullable,)
        unwrapped_fields1556 = fields1555
        write(pp, "(gnf_column")
        indent_sexp!(pp)
        newline(pp)
        field1557 = unwrapped_fields1556[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1557))
        newline(pp)
        field1558 = unwrapped_fields1556[2]
        pretty_boolean_value(pp, field1558)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1786, _rid) in enumerate(msg.ids)
        _idx = i1786 - 1
        newline(pp)
        write(pp, "(")
        _t1787 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1787)
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
    for (i1788, _elem) in enumerate(msg.keys)
        _idx = i1788 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1789, _elem) in enumerate(msg.values)
        _idx = i1789 - 1
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
    for (i1790, _elem) in enumerate(msg.columns)
        _idx = i1790 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.IcebergCatalogConfig) = pretty_iceberg_catalog_config(pp, x)
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportGNFColumn) = pretty_export_gnf_column(pp, x)
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
