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
    _t1746 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1746
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1747 = Proto.Value(value=OneOf(:int_value, v))
    return _t1747
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1748 = Proto.Value(value=OneOf(:float_value, v))
    return _t1748
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1749 = Proto.Value(value=OneOf(:string_value, v))
    return _t1749
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1750 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1750
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1751 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1751
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1752 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1752,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1753 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1753,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1754 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1754,))
            end
        end
    end
    _t1755 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1755,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1756 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1756,))
    _t1757 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1757,))
    if msg.new_line != ""
        _t1758 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1758,))
    end
    _t1759 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1759,))
    _t1760 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1760,))
    _t1761 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1761,))
    if msg.comment != ""
        _t1762 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1762,))
    end
    for missing_string in msg.missing_strings
        _t1763 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1763,))
    end
    _t1764 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1764,))
    _t1765 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1765,))
    _t1766 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1766,))
    if msg.partition_size_mb != 0
        _t1767 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1767,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1768 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1768,))
    _t1769 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1769,))
    _t1770 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1770,))
    _t1771 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1771,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1772 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1772,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1773 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1773,))
        end
    end
    _t1774 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1774,))
    _t1775 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1775,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1776 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1776,))
    end
    if !isnothing(msg.compression)
        _t1777 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1777,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1778 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1778,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1779 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1779,))
    end
    if !isnothing(msg.syntax_delim)
        _t1780 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1780,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1781 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1781,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1782 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1782,))
    end
    return sort(result)
end

function deconstruct_iceberg_catalog_config_scope_optional(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)::Union{Nothing, String}
    if msg.scope != ""
        return msg.scope
    else
        _t1783 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1784 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1785 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1785,))
    end
    if msg.target_file_size_bytes != 0
        _t1786 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1786,))
    end
    if msg.compression != ""
        _t1787 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1787,))
    end
    if length(result) == 0
        return nothing
    else
        _t1788 = nothing
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
        _t1789 = nothing
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
    flat791 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat791)
        write(pp, flat791)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1564 = _dollar_dollar.configure
        else
            _t1564 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1565 = _dollar_dollar.sync
        else
            _t1565 = nothing
        end
        fields782 = (_t1564, _t1565, _dollar_dollar.epochs,)
        unwrapped_fields783 = fields782
        write(pp, "(transaction")
        indent_sexp!(pp)
        field784 = unwrapped_fields783[1]
        if !isnothing(field784)
            newline(pp)
            opt_val785 = field784
            pretty_configure(pp, opt_val785)
        end
        field786 = unwrapped_fields783[2]
        if !isnothing(field786)
            newline(pp)
            opt_val787 = field786
            pretty_sync(pp, opt_val787)
        end
        field788 = unwrapped_fields783[3]
        if !isempty(field788)
            newline(pp)
            for (i1566, elem789) in enumerate(field788)
                i790 = i1566 - 1
                if (i790 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem789)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat794 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat794)
        write(pp, flat794)
        return nothing
    else
        _dollar_dollar = msg
        _t1567 = deconstruct_configure(pp, _dollar_dollar)
        fields792 = _t1567
        unwrapped_fields793 = fields792
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields793)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat798 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat798)
        write(pp, flat798)
        return nothing
    else
        fields795 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields795)
            newline(pp)
            for (i1568, elem796) in enumerate(fields795)
                i797 = i1568 - 1
                if (i797 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem796)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat803 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat803)
        write(pp, flat803)
        return nothing
    else
        _dollar_dollar = msg
        fields799 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields800 = fields799
        write(pp, ":")
        field801 = unwrapped_fields800[1]
        write(pp, field801)
        write(pp, " ")
        field802 = unwrapped_fields800[2]
        pretty_raw_value(pp, field802)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat829 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat829)
        write(pp, flat829)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1569 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1569 = nothing
        end
        deconstruct_result827 = _t1569
        if !isnothing(deconstruct_result827)
            unwrapped828 = deconstruct_result827
            pretty_raw_date(pp, unwrapped828)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1570 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1570 = nothing
            end
            deconstruct_result825 = _t1570
            if !isnothing(deconstruct_result825)
                unwrapped826 = deconstruct_result825
                pretty_raw_datetime(pp, unwrapped826)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1571 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1571 = nothing
                end
                deconstruct_result823 = _t1571
                if !isnothing(deconstruct_result823)
                    unwrapped824 = deconstruct_result823
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped824))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1572 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1572 = nothing
                    end
                    deconstruct_result821 = _t1572
                    if !isnothing(deconstruct_result821)
                        unwrapped822 = deconstruct_result821
                        write(pp, (string(Int64(unwrapped822)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1573 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1573 = nothing
                        end
                        deconstruct_result819 = _t1573
                        if !isnothing(deconstruct_result819)
                            unwrapped820 = deconstruct_result819
                            write(pp, string(unwrapped820))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1574 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1574 = nothing
                            end
                            deconstruct_result817 = _t1574
                            if !isnothing(deconstruct_result817)
                                unwrapped818 = deconstruct_result817
                                write(pp, format_float32_literal(unwrapped818))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1575 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1575 = nothing
                                end
                                deconstruct_result815 = _t1575
                                if !isnothing(deconstruct_result815)
                                    unwrapped816 = deconstruct_result815
                                    write(pp, lowercase(string(unwrapped816)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1576 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1576 = nothing
                                    end
                                    deconstruct_result813 = _t1576
                                    if !isnothing(deconstruct_result813)
                                        unwrapped814 = deconstruct_result813
                                        write(pp, (string(Int64(unwrapped814)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1577 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1577 = nothing
                                        end
                                        deconstruct_result811 = _t1577
                                        if !isnothing(deconstruct_result811)
                                            unwrapped812 = deconstruct_result811
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped812))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1578 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1578 = nothing
                                            end
                                            deconstruct_result809 = _t1578
                                            if !isnothing(deconstruct_result809)
                                                unwrapped810 = deconstruct_result809
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped810))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1579 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1579 = nothing
                                                end
                                                deconstruct_result807 = _t1579
                                                if !isnothing(deconstruct_result807)
                                                    unwrapped808 = deconstruct_result807
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped808))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1580 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1580 = nothing
                                                    end
                                                    deconstruct_result805 = _t1580
                                                    if !isnothing(deconstruct_result805)
                                                        unwrapped806 = deconstruct_result805
                                                        pretty_boolean_value(pp, unwrapped806)
                                                    else
                                                        fields804 = msg
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
    flat835 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat835)
        write(pp, flat835)
        return nothing
    else
        _dollar_dollar = msg
        fields830 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields831 = fields830
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field832 = unwrapped_fields831[1]
        write(pp, string(field832))
        newline(pp)
        field833 = unwrapped_fields831[2]
        write(pp, string(field833))
        newline(pp)
        field834 = unwrapped_fields831[3]
        write(pp, string(field834))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat846 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat846)
        write(pp, flat846)
        return nothing
    else
        _dollar_dollar = msg
        fields836 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields837 = fields836
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field838 = unwrapped_fields837[1]
        write(pp, string(field838))
        newline(pp)
        field839 = unwrapped_fields837[2]
        write(pp, string(field839))
        newline(pp)
        field840 = unwrapped_fields837[3]
        write(pp, string(field840))
        newline(pp)
        field841 = unwrapped_fields837[4]
        write(pp, string(field841))
        newline(pp)
        field842 = unwrapped_fields837[5]
        write(pp, string(field842))
        newline(pp)
        field843 = unwrapped_fields837[6]
        write(pp, string(field843))
        field844 = unwrapped_fields837[7]
        if !isnothing(field844)
            newline(pp)
            opt_val845 = field844
            write(pp, string(opt_val845))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1581 = ()
    else
        _t1581 = nothing
    end
    deconstruct_result849 = _t1581
    if !isnothing(deconstruct_result849)
        unwrapped850 = deconstruct_result849
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1582 = ()
        else
            _t1582 = nothing
        end
        deconstruct_result847 = _t1582
        if !isnothing(deconstruct_result847)
            unwrapped848 = deconstruct_result847
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat855 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat855)
        write(pp, flat855)
        return nothing
    else
        _dollar_dollar = msg
        fields851 = _dollar_dollar.fragments
        unwrapped_fields852 = fields851
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields852)
            newline(pp)
            for (i1583, elem853) in enumerate(unwrapped_fields852)
                i854 = i1583 - 1
                if (i854 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem853)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat858 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat858)
        write(pp, flat858)
        return nothing
    else
        _dollar_dollar = msg
        fields856 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields857 = fields856
        write(pp, ":")
        write(pp, unwrapped_fields857)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat865 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat865)
        write(pp, flat865)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1584 = _dollar_dollar.writes
        else
            _t1584 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1585 = _dollar_dollar.reads
        else
            _t1585 = nothing
        end
        fields859 = (_t1584, _t1585,)
        unwrapped_fields860 = fields859
        write(pp, "(epoch")
        indent_sexp!(pp)
        field861 = unwrapped_fields860[1]
        if !isnothing(field861)
            newline(pp)
            opt_val862 = field861
            pretty_epoch_writes(pp, opt_val862)
        end
        field863 = unwrapped_fields860[2]
        if !isnothing(field863)
            newline(pp)
            opt_val864 = field863
            pretty_epoch_reads(pp, opt_val864)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat869 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat869)
        write(pp, flat869)
        return nothing
    else
        fields866 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields866)
            newline(pp)
            for (i1586, elem867) in enumerate(fields866)
                i868 = i1586 - 1
                if (i868 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem867)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat878 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat878)
        write(pp, flat878)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1587 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1587 = nothing
        end
        deconstruct_result876 = _t1587
        if !isnothing(deconstruct_result876)
            unwrapped877 = deconstruct_result876
            pretty_define(pp, unwrapped877)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1588 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1588 = nothing
            end
            deconstruct_result874 = _t1588
            if !isnothing(deconstruct_result874)
                unwrapped875 = deconstruct_result874
                pretty_undefine(pp, unwrapped875)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1589 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1589 = nothing
                end
                deconstruct_result872 = _t1589
                if !isnothing(deconstruct_result872)
                    unwrapped873 = deconstruct_result872
                    pretty_context(pp, unwrapped873)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1590 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1590 = nothing
                    end
                    deconstruct_result870 = _t1590
                    if !isnothing(deconstruct_result870)
                        unwrapped871 = deconstruct_result870
                        pretty_snapshot(pp, unwrapped871)
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
    flat881 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat881)
        write(pp, flat881)
        return nothing
    else
        _dollar_dollar = msg
        fields879 = _dollar_dollar.fragment
        unwrapped_fields880 = fields879
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields880)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat888 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat888)
        write(pp, flat888)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields882 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields883 = fields882
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field884 = unwrapped_fields883[1]
        pretty_new_fragment_id(pp, field884)
        field885 = unwrapped_fields883[2]
        if !isempty(field885)
            newline(pp)
            for (i1591, elem886) in enumerate(field885)
                i887 = i1591 - 1
                if (i887 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem886)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat890 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat890)
        write(pp, flat890)
        return nothing
    else
        fields889 = msg
        pretty_fragment_id(pp, fields889)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat899 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat899)
        write(pp, flat899)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1592 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1592 = nothing
        end
        deconstruct_result897 = _t1592
        if !isnothing(deconstruct_result897)
            unwrapped898 = deconstruct_result897
            pretty_def(pp, unwrapped898)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1593 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1593 = nothing
            end
            deconstruct_result895 = _t1593
            if !isnothing(deconstruct_result895)
                unwrapped896 = deconstruct_result895
                pretty_algorithm(pp, unwrapped896)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1594 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1594 = nothing
                end
                deconstruct_result893 = _t1594
                if !isnothing(deconstruct_result893)
                    unwrapped894 = deconstruct_result893
                    pretty_constraint(pp, unwrapped894)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1595 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1595 = nothing
                    end
                    deconstruct_result891 = _t1595
                    if !isnothing(deconstruct_result891)
                        unwrapped892 = deconstruct_result891
                        pretty_data(pp, unwrapped892)
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
    flat906 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1596 = _dollar_dollar.attrs
        else
            _t1596 = nothing
        end
        fields900 = (_dollar_dollar.name, _dollar_dollar.body, _t1596,)
        unwrapped_fields901 = fields900
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field902 = unwrapped_fields901[1]
        pretty_relation_id(pp, field902)
        newline(pp)
        field903 = unwrapped_fields901[2]
        pretty_abstraction(pp, field903)
        field904 = unwrapped_fields901[3]
        if !isnothing(field904)
            newline(pp)
            opt_val905 = field904
            pretty_attrs(pp, opt_val905)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat911 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat911)
        write(pp, flat911)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1598 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1597 = _t1598
        else
            _t1597 = nothing
        end
        deconstruct_result909 = _t1597
        if !isnothing(deconstruct_result909)
            unwrapped910 = deconstruct_result909
            write(pp, ":")
            write(pp, unwrapped910)
        else
            _dollar_dollar = msg
            _t1599 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result907 = _t1599
            if !isnothing(deconstruct_result907)
                unwrapped908 = deconstruct_result907
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped908))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat916 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat916)
        write(pp, flat916)
        return nothing
    else
        _dollar_dollar = msg
        _t1600 = deconstruct_bindings(pp, _dollar_dollar)
        fields912 = (_t1600, _dollar_dollar.value,)
        unwrapped_fields913 = fields912
        write(pp, "(")
        indent!(pp)
        field914 = unwrapped_fields913[1]
        pretty_bindings(pp, field914)
        newline(pp)
        field915 = unwrapped_fields913[2]
        pretty_formula(pp, field915)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat924 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat924)
        write(pp, flat924)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1601 = _dollar_dollar[2]
        else
            _t1601 = nothing
        end
        fields917 = (_dollar_dollar[1], _t1601,)
        unwrapped_fields918 = fields917
        write(pp, "[")
        indent!(pp)
        field919 = unwrapped_fields918[1]
        for (i1602, elem920) in enumerate(field919)
            i921 = i1602 - 1
            if (i921 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem920)
        end
        field922 = unwrapped_fields918[2]
        if !isnothing(field922)
            newline(pp)
            opt_val923 = field922
            pretty_value_bindings(pp, opt_val923)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat929 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat929)
        write(pp, flat929)
        return nothing
    else
        _dollar_dollar = msg
        fields925 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields926 = fields925
        field927 = unwrapped_fields926[1]
        write(pp, field927)
        write(pp, "::")
        field928 = unwrapped_fields926[2]
        pretty_type(pp, field928)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat958 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat958)
        write(pp, flat958)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1603 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1603 = nothing
        end
        deconstruct_result956 = _t1603
        if !isnothing(deconstruct_result956)
            unwrapped957 = deconstruct_result956
            pretty_unspecified_type(pp, unwrapped957)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1604 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1604 = nothing
            end
            deconstruct_result954 = _t1604
            if !isnothing(deconstruct_result954)
                unwrapped955 = deconstruct_result954
                pretty_string_type(pp, unwrapped955)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1605 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1605 = nothing
                end
                deconstruct_result952 = _t1605
                if !isnothing(deconstruct_result952)
                    unwrapped953 = deconstruct_result952
                    pretty_int_type(pp, unwrapped953)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1606 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1606 = nothing
                    end
                    deconstruct_result950 = _t1606
                    if !isnothing(deconstruct_result950)
                        unwrapped951 = deconstruct_result950
                        pretty_float_type(pp, unwrapped951)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1607 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1607 = nothing
                        end
                        deconstruct_result948 = _t1607
                        if !isnothing(deconstruct_result948)
                            unwrapped949 = deconstruct_result948
                            pretty_uint128_type(pp, unwrapped949)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1608 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1608 = nothing
                            end
                            deconstruct_result946 = _t1608
                            if !isnothing(deconstruct_result946)
                                unwrapped947 = deconstruct_result946
                                pretty_int128_type(pp, unwrapped947)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1609 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1609 = nothing
                                end
                                deconstruct_result944 = _t1609
                                if !isnothing(deconstruct_result944)
                                    unwrapped945 = deconstruct_result944
                                    pretty_date_type(pp, unwrapped945)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1610 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1610 = nothing
                                    end
                                    deconstruct_result942 = _t1610
                                    if !isnothing(deconstruct_result942)
                                        unwrapped943 = deconstruct_result942
                                        pretty_datetime_type(pp, unwrapped943)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1611 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1611 = nothing
                                        end
                                        deconstruct_result940 = _t1611
                                        if !isnothing(deconstruct_result940)
                                            unwrapped941 = deconstruct_result940
                                            pretty_missing_type(pp, unwrapped941)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1612 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1612 = nothing
                                            end
                                            deconstruct_result938 = _t1612
                                            if !isnothing(deconstruct_result938)
                                                unwrapped939 = deconstruct_result938
                                                pretty_decimal_type(pp, unwrapped939)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1613 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1613 = nothing
                                                end
                                                deconstruct_result936 = _t1613
                                                if !isnothing(deconstruct_result936)
                                                    unwrapped937 = deconstruct_result936
                                                    pretty_boolean_type(pp, unwrapped937)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1614 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1614 = nothing
                                                    end
                                                    deconstruct_result934 = _t1614
                                                    if !isnothing(deconstruct_result934)
                                                        unwrapped935 = deconstruct_result934
                                                        pretty_int32_type(pp, unwrapped935)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1615 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1615 = nothing
                                                        end
                                                        deconstruct_result932 = _t1615
                                                        if !isnothing(deconstruct_result932)
                                                            unwrapped933 = deconstruct_result932
                                                            pretty_float32_type(pp, unwrapped933)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1616 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1616 = nothing
                                                            end
                                                            deconstruct_result930 = _t1616
                                                            if !isnothing(deconstruct_result930)
                                                                unwrapped931 = deconstruct_result930
                                                                pretty_uint32_type(pp, unwrapped931)
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
    fields959 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields960 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields961 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields962 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields963 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields964 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields965 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields966 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields967 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat972 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat972)
        write(pp, flat972)
        return nothing
    else
        _dollar_dollar = msg
        fields968 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields969 = fields968
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field970 = unwrapped_fields969[1]
        write(pp, string(field970))
        newline(pp)
        field971 = unwrapped_fields969[2]
        write(pp, string(field971))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields973 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields974 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields975 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields976 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat980 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat980)
        write(pp, flat980)
        return nothing
    else
        fields977 = msg
        write(pp, "|")
        if !isempty(fields977)
            write(pp, " ")
            for (i1617, elem978) in enumerate(fields977)
                i979 = i1617 - 1
                if (i979 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem978)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1007 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1007)
        write(pp, flat1007)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1618 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1618 = nothing
        end
        deconstruct_result1005 = _t1618
        if !isnothing(deconstruct_result1005)
            unwrapped1006 = deconstruct_result1005
            pretty_true(pp, unwrapped1006)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1619 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1619 = nothing
            end
            deconstruct_result1003 = _t1619
            if !isnothing(deconstruct_result1003)
                unwrapped1004 = deconstruct_result1003
                pretty_false(pp, unwrapped1004)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1620 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1620 = nothing
                end
                deconstruct_result1001 = _t1620
                if !isnothing(deconstruct_result1001)
                    unwrapped1002 = deconstruct_result1001
                    pretty_exists(pp, unwrapped1002)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1621 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1621 = nothing
                    end
                    deconstruct_result999 = _t1621
                    if !isnothing(deconstruct_result999)
                        unwrapped1000 = deconstruct_result999
                        pretty_reduce(pp, unwrapped1000)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1622 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1622 = nothing
                        end
                        deconstruct_result997 = _t1622
                        if !isnothing(deconstruct_result997)
                            unwrapped998 = deconstruct_result997
                            pretty_conjunction(pp, unwrapped998)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1623 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1623 = nothing
                            end
                            deconstruct_result995 = _t1623
                            if !isnothing(deconstruct_result995)
                                unwrapped996 = deconstruct_result995
                                pretty_disjunction(pp, unwrapped996)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1624 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1624 = nothing
                                end
                                deconstruct_result993 = _t1624
                                if !isnothing(deconstruct_result993)
                                    unwrapped994 = deconstruct_result993
                                    pretty_not(pp, unwrapped994)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1625 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1625 = nothing
                                    end
                                    deconstruct_result991 = _t1625
                                    if !isnothing(deconstruct_result991)
                                        unwrapped992 = deconstruct_result991
                                        pretty_ffi(pp, unwrapped992)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1626 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1626 = nothing
                                        end
                                        deconstruct_result989 = _t1626
                                        if !isnothing(deconstruct_result989)
                                            unwrapped990 = deconstruct_result989
                                            pretty_atom(pp, unwrapped990)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1627 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1627 = nothing
                                            end
                                            deconstruct_result987 = _t1627
                                            if !isnothing(deconstruct_result987)
                                                unwrapped988 = deconstruct_result987
                                                pretty_pragma(pp, unwrapped988)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1628 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1628 = nothing
                                                end
                                                deconstruct_result985 = _t1628
                                                if !isnothing(deconstruct_result985)
                                                    unwrapped986 = deconstruct_result985
                                                    pretty_primitive(pp, unwrapped986)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1629 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1629 = nothing
                                                    end
                                                    deconstruct_result983 = _t1629
                                                    if !isnothing(deconstruct_result983)
                                                        unwrapped984 = deconstruct_result983
                                                        pretty_rel_atom(pp, unwrapped984)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1630 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1630 = nothing
                                                        end
                                                        deconstruct_result981 = _t1630
                                                        if !isnothing(deconstruct_result981)
                                                            unwrapped982 = deconstruct_result981
                                                            pretty_cast(pp, unwrapped982)
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
    fields1008 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1009 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1014 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1014)
        write(pp, flat1014)
        return nothing
    else
        _dollar_dollar = msg
        _t1631 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1010 = (_t1631, _dollar_dollar.body.value,)
        unwrapped_fields1011 = fields1010
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1012 = unwrapped_fields1011[1]
        pretty_bindings(pp, field1012)
        newline(pp)
        field1013 = unwrapped_fields1011[2]
        pretty_formula(pp, field1013)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1020 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1020)
        write(pp, flat1020)
        return nothing
    else
        _dollar_dollar = msg
        fields1015 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1016 = fields1015
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1017 = unwrapped_fields1016[1]
        pretty_abstraction(pp, field1017)
        newline(pp)
        field1018 = unwrapped_fields1016[2]
        pretty_abstraction(pp, field1018)
        newline(pp)
        field1019 = unwrapped_fields1016[3]
        pretty_terms(pp, field1019)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1024 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1024)
        write(pp, flat1024)
        return nothing
    else
        fields1021 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1021)
            newline(pp)
            for (i1632, elem1022) in enumerate(fields1021)
                i1023 = i1632 - 1
                if (i1023 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1022)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1029 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1029)
        write(pp, flat1029)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1633 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1633 = nothing
        end
        deconstruct_result1027 = _t1633
        if !isnothing(deconstruct_result1027)
            unwrapped1028 = deconstruct_result1027
            pretty_var(pp, unwrapped1028)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1634 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1634 = nothing
            end
            deconstruct_result1025 = _t1634
            if !isnothing(deconstruct_result1025)
                unwrapped1026 = deconstruct_result1025
                pretty_value(pp, unwrapped1026)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1032 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1032)
        write(pp, flat1032)
        return nothing
    else
        _dollar_dollar = msg
        fields1030 = _dollar_dollar.name
        unwrapped_fields1031 = fields1030
        write(pp, unwrapped_fields1031)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1058 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1058)
        write(pp, flat1058)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1635 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1635 = nothing
        end
        deconstruct_result1056 = _t1635
        if !isnothing(deconstruct_result1056)
            unwrapped1057 = deconstruct_result1056
            pretty_date(pp, unwrapped1057)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1636 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1636 = nothing
            end
            deconstruct_result1054 = _t1636
            if !isnothing(deconstruct_result1054)
                unwrapped1055 = deconstruct_result1054
                pretty_datetime(pp, unwrapped1055)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1637 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1637 = nothing
                end
                deconstruct_result1052 = _t1637
                if !isnothing(deconstruct_result1052)
                    unwrapped1053 = deconstruct_result1052
                    write(pp, format_string(pp, unwrapped1053))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1638 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1638 = nothing
                    end
                    deconstruct_result1050 = _t1638
                    if !isnothing(deconstruct_result1050)
                        unwrapped1051 = deconstruct_result1050
                        write(pp, format_int32(pp, unwrapped1051))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1639 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1639 = nothing
                        end
                        deconstruct_result1048 = _t1639
                        if !isnothing(deconstruct_result1048)
                            unwrapped1049 = deconstruct_result1048
                            write(pp, format_int(pp, unwrapped1049))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1640 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1640 = nothing
                            end
                            deconstruct_result1046 = _t1640
                            if !isnothing(deconstruct_result1046)
                                unwrapped1047 = deconstruct_result1046
                                write(pp, format_float32(pp, unwrapped1047))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1641 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1641 = nothing
                                end
                                deconstruct_result1044 = _t1641
                                if !isnothing(deconstruct_result1044)
                                    unwrapped1045 = deconstruct_result1044
                                    write(pp, format_float(pp, unwrapped1045))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1642 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1642 = nothing
                                    end
                                    deconstruct_result1042 = _t1642
                                    if !isnothing(deconstruct_result1042)
                                        unwrapped1043 = deconstruct_result1042
                                        write(pp, format_uint32(pp, unwrapped1043))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1643 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1643 = nothing
                                        end
                                        deconstruct_result1040 = _t1643
                                        if !isnothing(deconstruct_result1040)
                                            unwrapped1041 = deconstruct_result1040
                                            write(pp, format_uint128(pp, unwrapped1041))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1644 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1644 = nothing
                                            end
                                            deconstruct_result1038 = _t1644
                                            if !isnothing(deconstruct_result1038)
                                                unwrapped1039 = deconstruct_result1038
                                                write(pp, format_int128(pp, unwrapped1039))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1645 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1645 = nothing
                                                end
                                                deconstruct_result1036 = _t1645
                                                if !isnothing(deconstruct_result1036)
                                                    unwrapped1037 = deconstruct_result1036
                                                    write(pp, format_decimal(pp, unwrapped1037))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1646 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1646 = nothing
                                                    end
                                                    deconstruct_result1034 = _t1646
                                                    if !isnothing(deconstruct_result1034)
                                                        unwrapped1035 = deconstruct_result1034
                                                        pretty_boolean_value(pp, unwrapped1035)
                                                    else
                                                        fields1033 = msg
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
    flat1064 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1064)
        write(pp, flat1064)
        return nothing
    else
        _dollar_dollar = msg
        fields1059 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1060 = fields1059
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1061 = unwrapped_fields1060[1]
        write(pp, format_int(pp, field1061))
        newline(pp)
        field1062 = unwrapped_fields1060[2]
        write(pp, format_int(pp, field1062))
        newline(pp)
        field1063 = unwrapped_fields1060[3]
        write(pp, format_int(pp, field1063))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1075 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1075)
        write(pp, flat1075)
        return nothing
    else
        _dollar_dollar = msg
        fields1065 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1066 = fields1065
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1067 = unwrapped_fields1066[1]
        write(pp, format_int(pp, field1067))
        newline(pp)
        field1068 = unwrapped_fields1066[2]
        write(pp, format_int(pp, field1068))
        newline(pp)
        field1069 = unwrapped_fields1066[3]
        write(pp, format_int(pp, field1069))
        newline(pp)
        field1070 = unwrapped_fields1066[4]
        write(pp, format_int(pp, field1070))
        newline(pp)
        field1071 = unwrapped_fields1066[5]
        write(pp, format_int(pp, field1071))
        newline(pp)
        field1072 = unwrapped_fields1066[6]
        write(pp, format_int(pp, field1072))
        field1073 = unwrapped_fields1066[7]
        if !isnothing(field1073)
            newline(pp)
            opt_val1074 = field1073
            write(pp, format_int(pp, opt_val1074))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1080 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1080)
        write(pp, flat1080)
        return nothing
    else
        _dollar_dollar = msg
        fields1076 = _dollar_dollar.args
        unwrapped_fields1077 = fields1076
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1077)
            newline(pp)
            for (i1647, elem1078) in enumerate(unwrapped_fields1077)
                i1079 = i1647 - 1
                if (i1079 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1078)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1085 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1085)
        write(pp, flat1085)
        return nothing
    else
        _dollar_dollar = msg
        fields1081 = _dollar_dollar.args
        unwrapped_fields1082 = fields1081
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1082)
            newline(pp)
            for (i1648, elem1083) in enumerate(unwrapped_fields1082)
                i1084 = i1648 - 1
                if (i1084 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1083)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1088 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1088)
        write(pp, flat1088)
        return nothing
    else
        _dollar_dollar = msg
        fields1086 = _dollar_dollar.arg
        unwrapped_fields1087 = fields1086
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1087)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1094 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1094)
        write(pp, flat1094)
        return nothing
    else
        _dollar_dollar = msg
        fields1089 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1090 = fields1089
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1091 = unwrapped_fields1090[1]
        pretty_name(pp, field1091)
        newline(pp)
        field1092 = unwrapped_fields1090[2]
        pretty_ffi_args(pp, field1092)
        newline(pp)
        field1093 = unwrapped_fields1090[3]
        pretty_terms(pp, field1093)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1096 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        fields1095 = msg
        write(pp, ":")
        write(pp, fields1095)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1100 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1100)
        write(pp, flat1100)
        return nothing
    else
        fields1097 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1097)
            newline(pp)
            for (i1649, elem1098) in enumerate(fields1097)
                i1099 = i1649 - 1
                if (i1099 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1098)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1107 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1107)
        write(pp, flat1107)
        return nothing
    else
        _dollar_dollar = msg
        fields1101 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1102 = fields1101
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1103 = unwrapped_fields1102[1]
        pretty_relation_id(pp, field1103)
        field1104 = unwrapped_fields1102[2]
        if !isempty(field1104)
            newline(pp)
            for (i1650, elem1105) in enumerate(field1104)
                i1106 = i1650 - 1
                if (i1106 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1105)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1114 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1114)
        write(pp, flat1114)
        return nothing
    else
        _dollar_dollar = msg
        fields1108 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1109 = fields1108
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1110 = unwrapped_fields1109[1]
        pretty_name(pp, field1110)
        field1111 = unwrapped_fields1109[2]
        if !isempty(field1111)
            newline(pp)
            for (i1651, elem1112) in enumerate(field1111)
                i1113 = i1651 - 1
                if (i1113 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1112)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1130 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1130)
        write(pp, flat1130)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1652 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1652 = nothing
        end
        guard_result1129 = _t1652
        if !isnothing(guard_result1129)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1653 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1653 = nothing
            end
            guard_result1128 = _t1653
            if !isnothing(guard_result1128)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1654 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1654 = nothing
                end
                guard_result1127 = _t1654
                if !isnothing(guard_result1127)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1655 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1655 = nothing
                    end
                    guard_result1126 = _t1655
                    if !isnothing(guard_result1126)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1656 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1656 = nothing
                        end
                        guard_result1125 = _t1656
                        if !isnothing(guard_result1125)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1657 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1657 = nothing
                            end
                            guard_result1124 = _t1657
                            if !isnothing(guard_result1124)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1658 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1658 = nothing
                                end
                                guard_result1123 = _t1658
                                if !isnothing(guard_result1123)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1659 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1659 = nothing
                                    end
                                    guard_result1122 = _t1659
                                    if !isnothing(guard_result1122)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1660 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1660 = nothing
                                        end
                                        guard_result1121 = _t1660
                                        if !isnothing(guard_result1121)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1115 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1116 = fields1115
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1117 = unwrapped_fields1116[1]
                                            pretty_name(pp, field1117)
                                            field1118 = unwrapped_fields1116[2]
                                            if !isempty(field1118)
                                                newline(pp)
                                                for (i1661, elem1119) in enumerate(field1118)
                                                    i1120 = i1661 - 1
                                                    if (i1120 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1119)
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
    flat1135 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1135)
        write(pp, flat1135)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1662 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1662 = nothing
        end
        fields1131 = _t1662
        unwrapped_fields1132 = fields1131
        write(pp, "(=")
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

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1140 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1140)
        write(pp, flat1140)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1663 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1663 = nothing
        end
        fields1136 = _t1663
        unwrapped_fields1137 = fields1136
        write(pp, "(<")
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

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1145 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1145)
        write(pp, flat1145)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1664 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1664 = nothing
        end
        fields1141 = _t1664
        unwrapped_fields1142 = fields1141
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1143 = unwrapped_fields1142[1]
        pretty_term(pp, field1143)
        newline(pp)
        field1144 = unwrapped_fields1142[2]
        pretty_term(pp, field1144)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1150 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1150)
        write(pp, flat1150)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1665 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1665 = nothing
        end
        fields1146 = _t1665
        unwrapped_fields1147 = fields1146
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1148 = unwrapped_fields1147[1]
        pretty_term(pp, field1148)
        newline(pp)
        field1149 = unwrapped_fields1147[2]
        pretty_term(pp, field1149)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1155 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1155)
        write(pp, flat1155)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1666 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1666 = nothing
        end
        fields1151 = _t1666
        unwrapped_fields1152 = fields1151
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1153 = unwrapped_fields1152[1]
        pretty_term(pp, field1153)
        newline(pp)
        field1154 = unwrapped_fields1152[2]
        pretty_term(pp, field1154)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1161 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1161)
        write(pp, flat1161)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1667 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1667 = nothing
        end
        fields1156 = _t1667
        unwrapped_fields1157 = fields1156
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1158 = unwrapped_fields1157[1]
        pretty_term(pp, field1158)
        newline(pp)
        field1159 = unwrapped_fields1157[2]
        pretty_term(pp, field1159)
        newline(pp)
        field1160 = unwrapped_fields1157[3]
        pretty_term(pp, field1160)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1167 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1668 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1668 = nothing
        end
        fields1162 = _t1668
        unwrapped_fields1163 = fields1162
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1164 = unwrapped_fields1163[1]
        pretty_term(pp, field1164)
        newline(pp)
        field1165 = unwrapped_fields1163[2]
        pretty_term(pp, field1165)
        newline(pp)
        field1166 = unwrapped_fields1163[3]
        pretty_term(pp, field1166)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1173 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1173)
        write(pp, flat1173)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1669 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1669 = nothing
        end
        fields1168 = _t1669
        unwrapped_fields1169 = fields1168
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1170 = unwrapped_fields1169[1]
        pretty_term(pp, field1170)
        newline(pp)
        field1171 = unwrapped_fields1169[2]
        pretty_term(pp, field1171)
        newline(pp)
        field1172 = unwrapped_fields1169[3]
        pretty_term(pp, field1172)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1179 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1670 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1670 = nothing
        end
        fields1174 = _t1670
        unwrapped_fields1175 = fields1174
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1176 = unwrapped_fields1175[1]
        pretty_term(pp, field1176)
        newline(pp)
        field1177 = unwrapped_fields1175[2]
        pretty_term(pp, field1177)
        newline(pp)
        field1178 = unwrapped_fields1175[3]
        pretty_term(pp, field1178)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1184 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1184)
        write(pp, flat1184)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1671 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1671 = nothing
        end
        deconstruct_result1182 = _t1671
        if !isnothing(deconstruct_result1182)
            unwrapped1183 = deconstruct_result1182
            pretty_specialized_value(pp, unwrapped1183)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1672 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1672 = nothing
            end
            deconstruct_result1180 = _t1672
            if !isnothing(deconstruct_result1180)
                unwrapped1181 = deconstruct_result1180
                pretty_term(pp, unwrapped1181)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1186 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1186)
        write(pp, flat1186)
        return nothing
    else
        fields1185 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1185)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1193 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1193)
        write(pp, flat1193)
        return nothing
    else
        _dollar_dollar = msg
        fields1187 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1188 = fields1187
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1189 = unwrapped_fields1188[1]
        pretty_name(pp, field1189)
        field1190 = unwrapped_fields1188[2]
        if !isempty(field1190)
            newline(pp)
            for (i1673, elem1191) in enumerate(field1190)
                i1192 = i1673 - 1
                if (i1192 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1191)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1198 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1198)
        write(pp, flat1198)
        return nothing
    else
        _dollar_dollar = msg
        fields1194 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1195 = fields1194
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1196 = unwrapped_fields1195[1]
        pretty_term(pp, field1196)
        newline(pp)
        field1197 = unwrapped_fields1195[2]
        pretty_term(pp, field1197)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1202 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1202)
        write(pp, flat1202)
        return nothing
    else
        fields1199 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1199)
            newline(pp)
            for (i1674, elem1200) in enumerate(fields1199)
                i1201 = i1674 - 1
                if (i1201 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1200)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1209 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1209)
        write(pp, flat1209)
        return nothing
    else
        _dollar_dollar = msg
        fields1203 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1204 = fields1203
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1205 = unwrapped_fields1204[1]
        pretty_name(pp, field1205)
        field1206 = unwrapped_fields1204[2]
        if !isempty(field1206)
            newline(pp)
            for (i1675, elem1207) in enumerate(field1206)
                i1208 = i1675 - 1
                if (i1208 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1207)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1216 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1216)
        write(pp, flat1216)
        return nothing
    else
        _dollar_dollar = msg
        fields1210 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1211 = fields1210
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1212 = unwrapped_fields1211[1]
        if !isempty(field1212)
            newline(pp)
            for (i1676, elem1213) in enumerate(field1212)
                i1214 = i1676 - 1
                if (i1214 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1213)
            end
        end
        newline(pp)
        field1215 = unwrapped_fields1211[2]
        pretty_script(pp, field1215)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1221 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1221)
        write(pp, flat1221)
        return nothing
    else
        _dollar_dollar = msg
        fields1217 = _dollar_dollar.constructs
        unwrapped_fields1218 = fields1217
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1218)
            newline(pp)
            for (i1677, elem1219) in enumerate(unwrapped_fields1218)
                i1220 = i1677 - 1
                if (i1220 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1219)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1226 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1226)
        write(pp, flat1226)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1678 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1678 = nothing
        end
        deconstruct_result1224 = _t1678
        if !isnothing(deconstruct_result1224)
            unwrapped1225 = deconstruct_result1224
            pretty_loop(pp, unwrapped1225)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1679 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1679 = nothing
            end
            deconstruct_result1222 = _t1679
            if !isnothing(deconstruct_result1222)
                unwrapped1223 = deconstruct_result1222
                pretty_instruction(pp, unwrapped1223)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1231 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1231)
        write(pp, flat1231)
        return nothing
    else
        _dollar_dollar = msg
        fields1227 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1228 = fields1227
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1229 = unwrapped_fields1228[1]
        pretty_init(pp, field1229)
        newline(pp)
        field1230 = unwrapped_fields1228[2]
        pretty_script(pp, field1230)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1235 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1235)
        write(pp, flat1235)
        return nothing
    else
        fields1232 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1232)
            newline(pp)
            for (i1680, elem1233) in enumerate(fields1232)
                i1234 = i1680 - 1
                if (i1234 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1233)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1246 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1246)
        write(pp, flat1246)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1681 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1681 = nothing
        end
        deconstruct_result1244 = _t1681
        if !isnothing(deconstruct_result1244)
            unwrapped1245 = deconstruct_result1244
            pretty_assign(pp, unwrapped1245)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1682 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1682 = nothing
            end
            deconstruct_result1242 = _t1682
            if !isnothing(deconstruct_result1242)
                unwrapped1243 = deconstruct_result1242
                pretty_upsert(pp, unwrapped1243)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1683 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1683 = nothing
                end
                deconstruct_result1240 = _t1683
                if !isnothing(deconstruct_result1240)
                    unwrapped1241 = deconstruct_result1240
                    pretty_break(pp, unwrapped1241)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1684 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1684 = nothing
                    end
                    deconstruct_result1238 = _t1684
                    if !isnothing(deconstruct_result1238)
                        unwrapped1239 = deconstruct_result1238
                        pretty_monoid_def(pp, unwrapped1239)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1685 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1685 = nothing
                        end
                        deconstruct_result1236 = _t1685
                        if !isnothing(deconstruct_result1236)
                            unwrapped1237 = deconstruct_result1236
                            pretty_monus_def(pp, unwrapped1237)
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
    flat1253 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1686 = _dollar_dollar.attrs
        else
            _t1686 = nothing
        end
        fields1247 = (_dollar_dollar.name, _dollar_dollar.body, _t1686,)
        unwrapped_fields1248 = fields1247
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1249 = unwrapped_fields1248[1]
        pretty_relation_id(pp, field1249)
        newline(pp)
        field1250 = unwrapped_fields1248[2]
        pretty_abstraction(pp, field1250)
        field1251 = unwrapped_fields1248[3]
        if !isnothing(field1251)
            newline(pp)
            opt_val1252 = field1251
            pretty_attrs(pp, opt_val1252)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1260 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1260)
        write(pp, flat1260)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1687 = _dollar_dollar.attrs
        else
            _t1687 = nothing
        end
        fields1254 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1687,)
        unwrapped_fields1255 = fields1254
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1256 = unwrapped_fields1255[1]
        pretty_relation_id(pp, field1256)
        newline(pp)
        field1257 = unwrapped_fields1255[2]
        pretty_abstraction_with_arity(pp, field1257)
        field1258 = unwrapped_fields1255[3]
        if !isnothing(field1258)
            newline(pp)
            opt_val1259 = field1258
            pretty_attrs(pp, opt_val1259)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1265 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1265)
        write(pp, flat1265)
        return nothing
    else
        _dollar_dollar = msg
        _t1688 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1261 = (_t1688, _dollar_dollar[1].value,)
        unwrapped_fields1262 = fields1261
        write(pp, "(")
        indent!(pp)
        field1263 = unwrapped_fields1262[1]
        pretty_bindings(pp, field1263)
        newline(pp)
        field1264 = unwrapped_fields1262[2]
        pretty_formula(pp, field1264)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1272 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1272)
        write(pp, flat1272)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1689 = _dollar_dollar.attrs
        else
            _t1689 = nothing
        end
        fields1266 = (_dollar_dollar.name, _dollar_dollar.body, _t1689,)
        unwrapped_fields1267 = fields1266
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1268 = unwrapped_fields1267[1]
        pretty_relation_id(pp, field1268)
        newline(pp)
        field1269 = unwrapped_fields1267[2]
        pretty_abstraction(pp, field1269)
        field1270 = unwrapped_fields1267[3]
        if !isnothing(field1270)
            newline(pp)
            opt_val1271 = field1270
            pretty_attrs(pp, opt_val1271)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1280 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1280)
        write(pp, flat1280)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1690 = _dollar_dollar.attrs
        else
            _t1690 = nothing
        end
        fields1273 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1690,)
        unwrapped_fields1274 = fields1273
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1275 = unwrapped_fields1274[1]
        pretty_monoid(pp, field1275)
        newline(pp)
        field1276 = unwrapped_fields1274[2]
        pretty_relation_id(pp, field1276)
        newline(pp)
        field1277 = unwrapped_fields1274[3]
        pretty_abstraction_with_arity(pp, field1277)
        field1278 = unwrapped_fields1274[4]
        if !isnothing(field1278)
            newline(pp)
            opt_val1279 = field1278
            pretty_attrs(pp, opt_val1279)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1289 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1289)
        write(pp, flat1289)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1691 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1691 = nothing
        end
        deconstruct_result1287 = _t1691
        if !isnothing(deconstruct_result1287)
            unwrapped1288 = deconstruct_result1287
            pretty_or_monoid(pp, unwrapped1288)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1692 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1692 = nothing
            end
            deconstruct_result1285 = _t1692
            if !isnothing(deconstruct_result1285)
                unwrapped1286 = deconstruct_result1285
                pretty_min_monoid(pp, unwrapped1286)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1693 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1693 = nothing
                end
                deconstruct_result1283 = _t1693
                if !isnothing(deconstruct_result1283)
                    unwrapped1284 = deconstruct_result1283
                    pretty_max_monoid(pp, unwrapped1284)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1694 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1694 = nothing
                    end
                    deconstruct_result1281 = _t1694
                    if !isnothing(deconstruct_result1281)
                        unwrapped1282 = deconstruct_result1281
                        pretty_sum_monoid(pp, unwrapped1282)
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
    fields1290 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1293 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1293)
        write(pp, flat1293)
        return nothing
    else
        _dollar_dollar = msg
        fields1291 = _dollar_dollar.var"#type"
        unwrapped_fields1292 = fields1291
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1292)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1296 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1296)
        write(pp, flat1296)
        return nothing
    else
        _dollar_dollar = msg
        fields1294 = _dollar_dollar.var"#type"
        unwrapped_fields1295 = fields1294
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1295)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1299 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1299)
        write(pp, flat1299)
        return nothing
    else
        _dollar_dollar = msg
        fields1297 = _dollar_dollar.var"#type"
        unwrapped_fields1298 = fields1297
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1298)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1307 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1307)
        write(pp, flat1307)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1695 = _dollar_dollar.attrs
        else
            _t1695 = nothing
        end
        fields1300 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1695,)
        unwrapped_fields1301 = fields1300
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1302 = unwrapped_fields1301[1]
        pretty_monoid(pp, field1302)
        newline(pp)
        field1303 = unwrapped_fields1301[2]
        pretty_relation_id(pp, field1303)
        newline(pp)
        field1304 = unwrapped_fields1301[3]
        pretty_abstraction_with_arity(pp, field1304)
        field1305 = unwrapped_fields1301[4]
        if !isnothing(field1305)
            newline(pp)
            opt_val1306 = field1305
            pretty_attrs(pp, opt_val1306)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1314 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1314)
        write(pp, flat1314)
        return nothing
    else
        _dollar_dollar = msg
        fields1308 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1309 = fields1308
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1310 = unwrapped_fields1309[1]
        pretty_relation_id(pp, field1310)
        newline(pp)
        field1311 = unwrapped_fields1309[2]
        pretty_abstraction(pp, field1311)
        newline(pp)
        field1312 = unwrapped_fields1309[3]
        pretty_functional_dependency_keys(pp, field1312)
        newline(pp)
        field1313 = unwrapped_fields1309[4]
        pretty_functional_dependency_values(pp, field1313)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1318 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1318)
        write(pp, flat1318)
        return nothing
    else
        fields1315 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1315)
            newline(pp)
            for (i1696, elem1316) in enumerate(fields1315)
                i1317 = i1696 - 1
                if (i1317 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1316)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1322 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1322)
        write(pp, flat1322)
        return nothing
    else
        fields1319 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1319)
            newline(pp)
            for (i1697, elem1320) in enumerate(fields1319)
                i1321 = i1697 - 1
                if (i1321 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1320)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1331 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1331)
        write(pp, flat1331)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1698 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1698 = nothing
        end
        deconstruct_result1329 = _t1698
        if !isnothing(deconstruct_result1329)
            unwrapped1330 = deconstruct_result1329
            pretty_edb(pp, unwrapped1330)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1699 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1699 = nothing
            end
            deconstruct_result1327 = _t1699
            if !isnothing(deconstruct_result1327)
                unwrapped1328 = deconstruct_result1327
                pretty_betree_relation(pp, unwrapped1328)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1700 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1700 = nothing
                end
                deconstruct_result1325 = _t1700
                if !isnothing(deconstruct_result1325)
                    unwrapped1326 = deconstruct_result1325
                    pretty_csv_data(pp, unwrapped1326)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1701 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1701 = nothing
                    end
                    deconstruct_result1323 = _t1701
                    if !isnothing(deconstruct_result1323)
                        unwrapped1324 = deconstruct_result1323
                        pretty_iceberg_data(pp, unwrapped1324)
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
    flat1337 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1337)
        write(pp, flat1337)
        return nothing
    else
        _dollar_dollar = msg
        fields1332 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1333 = fields1332
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1334 = unwrapped_fields1333[1]
        pretty_relation_id(pp, field1334)
        newline(pp)
        field1335 = unwrapped_fields1333[2]
        pretty_edb_path(pp, field1335)
        newline(pp)
        field1336 = unwrapped_fields1333[3]
        pretty_edb_types(pp, field1336)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1341 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1341)
        write(pp, flat1341)
        return nothing
    else
        fields1338 = msg
        write(pp, "[")
        indent!(pp)
        for (i1702, elem1339) in enumerate(fields1338)
            i1340 = i1702 - 1
            if (i1340 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1339))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1345 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1345)
        write(pp, flat1345)
        return nothing
    else
        fields1342 = msg
        write(pp, "[")
        indent!(pp)
        for (i1703, elem1343) in enumerate(fields1342)
            i1344 = i1703 - 1
            if (i1344 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1343)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1350 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1350)
        write(pp, flat1350)
        return nothing
    else
        _dollar_dollar = msg
        fields1346 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1347 = fields1346
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1348 = unwrapped_fields1347[1]
        pretty_relation_id(pp, field1348)
        newline(pp)
        field1349 = unwrapped_fields1347[2]
        pretty_betree_info(pp, field1349)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1356 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1356)
        write(pp, flat1356)
        return nothing
    else
        _dollar_dollar = msg
        _t1704 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1351 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1704,)
        unwrapped_fields1352 = fields1351
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1353 = unwrapped_fields1352[1]
        pretty_betree_info_key_types(pp, field1353)
        newline(pp)
        field1354 = unwrapped_fields1352[2]
        pretty_betree_info_value_types(pp, field1354)
        newline(pp)
        field1355 = unwrapped_fields1352[3]
        pretty_config_dict(pp, field1355)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1360 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1360)
        write(pp, flat1360)
        return nothing
    else
        fields1357 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1357)
            newline(pp)
            for (i1705, elem1358) in enumerate(fields1357)
                i1359 = i1705 - 1
                if (i1359 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1358)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1364 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1364)
        write(pp, flat1364)
        return nothing
    else
        fields1361 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1361)
            newline(pp)
            for (i1706, elem1362) in enumerate(fields1361)
                i1363 = i1706 - 1
                if (i1363 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1362)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1371 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1371)
        write(pp, flat1371)
        return nothing
    else
        _dollar_dollar = msg
        fields1365 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1366 = fields1365
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1367 = unwrapped_fields1366[1]
        pretty_csvlocator(pp, field1367)
        newline(pp)
        field1368 = unwrapped_fields1366[2]
        pretty_csv_config(pp, field1368)
        newline(pp)
        field1369 = unwrapped_fields1366[3]
        pretty_gnf_columns(pp, field1369)
        newline(pp)
        field1370 = unwrapped_fields1366[4]
        pretty_csv_asof(pp, field1370)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1378 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1378)
        write(pp, flat1378)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1707 = _dollar_dollar.paths
        else
            _t1707 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1708 = String(copy(_dollar_dollar.inline_data))
        else
            _t1708 = nothing
        end
        fields1372 = (_t1707, _t1708,)
        unwrapped_fields1373 = fields1372
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1374 = unwrapped_fields1373[1]
        if !isnothing(field1374)
            newline(pp)
            opt_val1375 = field1374
            pretty_csv_locator_paths(pp, opt_val1375)
        end
        field1376 = unwrapped_fields1373[2]
        if !isnothing(field1376)
            newline(pp)
            opt_val1377 = field1376
            pretty_csv_locator_inline_data(pp, opt_val1377)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1382 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1382)
        write(pp, flat1382)
        return nothing
    else
        fields1379 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1379)
            newline(pp)
            for (i1709, elem1380) in enumerate(fields1379)
                i1381 = i1709 - 1
                if (i1381 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1380))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1384 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1384)
        write(pp, flat1384)
        return nothing
    else
        fields1383 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1383))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1387 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1387)
        write(pp, flat1387)
        return nothing
    else
        _dollar_dollar = msg
        _t1710 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1385 = _t1710
        unwrapped_fields1386 = fields1385
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1386)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1391 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1391)
        write(pp, flat1391)
        return nothing
    else
        fields1388 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1388)
            newline(pp)
            for (i1711, elem1389) in enumerate(fields1388)
                i1390 = i1711 - 1
                if (i1390 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1389)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1400 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1400)
        write(pp, flat1400)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1712 = _dollar_dollar.target_id
        else
            _t1712 = nothing
        end
        fields1392 = (_dollar_dollar.column_path, _t1712, _dollar_dollar.types,)
        unwrapped_fields1393 = fields1392
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1394 = unwrapped_fields1393[1]
        pretty_gnf_column_path(pp, field1394)
        field1395 = unwrapped_fields1393[2]
        if !isnothing(field1395)
            newline(pp)
            opt_val1396 = field1395
            pretty_relation_id(pp, opt_val1396)
        end
        newline(pp)
        write(pp, "[")
        field1397 = unwrapped_fields1393[3]
        for (i1713, elem1398) in enumerate(field1397)
            i1399 = i1713 - 1
            if (i1399 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1398)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1407 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1407)
        write(pp, flat1407)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1714 = _dollar_dollar[1]
        else
            _t1714 = nothing
        end
        deconstruct_result1405 = _t1714
        if !isnothing(deconstruct_result1405)
            unwrapped1406 = deconstruct_result1405
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1406))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1715 = _dollar_dollar
            else
                _t1715 = nothing
            end
            deconstruct_result1401 = _t1715
            if !isnothing(deconstruct_result1401)
                unwrapped1402 = deconstruct_result1401
                write(pp, "[")
                indent!(pp)
                for (i1716, elem1403) in enumerate(unwrapped1402)
                    i1404 = i1716 - 1
                    if (i1404 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1403))
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
    flat1409 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1409)
        write(pp, flat1409)
        return nothing
    else
        fields1408 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1408))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1417 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1417)
        write(pp, flat1417)
        return nothing
    else
        _dollar_dollar = msg
        _t1717 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1410 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1717,)
        unwrapped_fields1411 = fields1410
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1412 = unwrapped_fields1411[1]
        pretty_iceberg_locator(pp, field1412)
        newline(pp)
        field1413 = unwrapped_fields1411[2]
        pretty_iceberg_catalog_config(pp, field1413)
        newline(pp)
        field1414 = unwrapped_fields1411[3]
        pretty_gnf_columns(pp, field1414)
        field1415 = unwrapped_fields1411[4]
        if !isnothing(field1415)
            newline(pp)
            opt_val1416 = field1415
            pretty_iceberg_to_snapshot(pp, opt_val1416)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1425 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1425)
        write(pp, flat1425)
        return nothing
    else
        _dollar_dollar = msg
        fields1418 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1419 = fields1418
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_name")
        newline(pp)
        field1420 = unwrapped_fields1419[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1420))
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "namespace")
        field1421 = unwrapped_fields1419[2]
        if !isempty(field1421)
            newline(pp)
            for (i1718, elem1422) in enumerate(field1421)
                i1423 = i1718 - 1
                if (i1423 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1422))
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "warehouse")
        newline(pp)
        field1424 = unwrapped_fields1419[3]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1424))
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1437 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1437)
        write(pp, flat1437)
        return nothing
    else
        _dollar_dollar = msg
        _t1719 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1426 = (_dollar_dollar.catalog_uri, _t1719, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1427 = fields1426
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "catalog_uri")
        newline(pp)
        field1428 = unwrapped_fields1427[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1428))
        dedent!(pp)
        write(pp, ")")
        field1429 = unwrapped_fields1427[2]
        if !isnothing(field1429)
            newline(pp)
            opt_val1430 = field1429
            pretty_iceberg_catalog_config_scope(pp, opt_val1430)
        end
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "properties")
        field1431 = unwrapped_fields1427[3]
        if !isempty(field1431)
            newline(pp)
            for (i1720, elem1432) in enumerate(field1431)
                i1433 = i1720 - 1
                if (i1433 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1432)
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "auth_properties")
        field1434 = unwrapped_fields1427[4]
        if !isempty(field1434)
            newline(pp)
            for (i1721, elem1435) in enumerate(field1434)
                i1436 = i1721 - 1
                if (i1436 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1435)
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
    flat1439 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1439)
        write(pp, flat1439)
        return nothing
    else
        fields1438 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1438))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1444 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1444)
        write(pp, flat1444)
        return nothing
    else
        _dollar_dollar = msg
        fields1440 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1441 = fields1440
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1442 = unwrapped_fields1441[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1442))
        newline(pp)
        field1443 = unwrapped_fields1441[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1443))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1446 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1446)
        write(pp, flat1446)
        return nothing
    else
        fields1445 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1445))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1449 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1449)
        write(pp, flat1449)
        return nothing
    else
        _dollar_dollar = msg
        fields1447 = _dollar_dollar.fragment_id
        unwrapped_fields1448 = fields1447
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1448)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1454 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1454)
        write(pp, flat1454)
        return nothing
    else
        _dollar_dollar = msg
        fields1450 = _dollar_dollar.relations
        unwrapped_fields1451 = fields1450
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1451)
            newline(pp)
            for (i1722, elem1452) in enumerate(unwrapped_fields1451)
                i1453 = i1722 - 1
                if (i1453 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1452)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1459 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1459)
        write(pp, flat1459)
        return nothing
    else
        _dollar_dollar = msg
        fields1455 = _dollar_dollar.mappings
        unwrapped_fields1456 = fields1455
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1456)
            newline(pp)
            for (i1723, elem1457) in enumerate(unwrapped_fields1456)
                i1458 = i1723 - 1
                if (i1458 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1457)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1464 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1464)
        write(pp, flat1464)
        return nothing
    else
        _dollar_dollar = msg
        fields1460 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1461 = fields1460
        field1462 = unwrapped_fields1461[1]
        pretty_edb_path(pp, field1462)
        write(pp, " ")
        field1463 = unwrapped_fields1461[2]
        pretty_relation_id(pp, field1463)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1468 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1468)
        write(pp, flat1468)
        return nothing
    else
        fields1465 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1465)
            newline(pp)
            for (i1724, elem1466) in enumerate(fields1465)
                i1467 = i1724 - 1
                if (i1467 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1466)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1479 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1479)
        write(pp, flat1479)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1725 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1725 = nothing
        end
        deconstruct_result1477 = _t1725
        if !isnothing(deconstruct_result1477)
            unwrapped1478 = deconstruct_result1477
            pretty_demand(pp, unwrapped1478)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1726 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1726 = nothing
            end
            deconstruct_result1475 = _t1726
            if !isnothing(deconstruct_result1475)
                unwrapped1476 = deconstruct_result1475
                pretty_output(pp, unwrapped1476)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1727 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1727 = nothing
                end
                deconstruct_result1473 = _t1727
                if !isnothing(deconstruct_result1473)
                    unwrapped1474 = deconstruct_result1473
                    pretty_what_if(pp, unwrapped1474)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1728 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1728 = nothing
                    end
                    deconstruct_result1471 = _t1728
                    if !isnothing(deconstruct_result1471)
                        unwrapped1472 = deconstruct_result1471
                        pretty_abort(pp, unwrapped1472)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1729 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1729 = nothing
                        end
                        deconstruct_result1469 = _t1729
                        if !isnothing(deconstruct_result1469)
                            unwrapped1470 = deconstruct_result1469
                            pretty_export(pp, unwrapped1470)
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
    flat1482 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1482)
        write(pp, flat1482)
        return nothing
    else
        _dollar_dollar = msg
        fields1480 = _dollar_dollar.relation_id
        unwrapped_fields1481 = fields1480
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1481)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1487 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1487)
        write(pp, flat1487)
        return nothing
    else
        _dollar_dollar = msg
        fields1483 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1484 = fields1483
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1485 = unwrapped_fields1484[1]
        pretty_name(pp, field1485)
        newline(pp)
        field1486 = unwrapped_fields1484[2]
        pretty_relation_id(pp, field1486)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1492 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1492)
        write(pp, flat1492)
        return nothing
    else
        _dollar_dollar = msg
        fields1488 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1489 = fields1488
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1490 = unwrapped_fields1489[1]
        pretty_name(pp, field1490)
        newline(pp)
        field1491 = unwrapped_fields1489[2]
        pretty_epoch(pp, field1491)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1498 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1498)
        write(pp, flat1498)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1730 = _dollar_dollar.name
        else
            _t1730 = nothing
        end
        fields1493 = (_t1730, _dollar_dollar.relation_id,)
        unwrapped_fields1494 = fields1493
        write(pp, "(abort")
        indent_sexp!(pp)
        field1495 = unwrapped_fields1494[1]
        if !isnothing(field1495)
            newline(pp)
            opt_val1496 = field1495
            pretty_name(pp, opt_val1496)
        end
        newline(pp)
        field1497 = unwrapped_fields1494[2]
        pretty_relation_id(pp, field1497)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1503 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1503)
        write(pp, flat1503)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1731 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1731 = nothing
        end
        deconstruct_result1501 = _t1731
        if !isnothing(deconstruct_result1501)
            unwrapped1502 = deconstruct_result1501
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1502)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1732 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1732 = nothing
            end
            deconstruct_result1499 = _t1732
            if !isnothing(deconstruct_result1499)
                unwrapped1500 = deconstruct_result1499
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1500)
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
    flat1514 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1514)
        write(pp, flat1514)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1733 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1733 = nothing
        end
        deconstruct_result1509 = _t1733
        if !isnothing(deconstruct_result1509)
            unwrapped1510 = deconstruct_result1509
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1511 = unwrapped1510[1]
            pretty_export_csv_path(pp, field1511)
            newline(pp)
            field1512 = unwrapped1510[2]
            pretty_export_csv_source(pp, field1512)
            newline(pp)
            field1513 = unwrapped1510[3]
            pretty_csv_config(pp, field1513)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1735 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1734 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1735,)
            else
                _t1734 = nothing
            end
            deconstruct_result1504 = _t1734
            if !isnothing(deconstruct_result1504)
                unwrapped1505 = deconstruct_result1504
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1506 = unwrapped1505[1]
                pretty_export_csv_path(pp, field1506)
                newline(pp)
                field1507 = unwrapped1505[2]
                pretty_export_csv_columns_list(pp, field1507)
                newline(pp)
                field1508 = unwrapped1505[3]
                pretty_config_dict(pp, field1508)
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
    flat1516 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1516)
        write(pp, flat1516)
        return nothing
    else
        fields1515 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1515))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1523 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1523)
        write(pp, flat1523)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1736 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1736 = nothing
        end
        deconstruct_result1519 = _t1736
        if !isnothing(deconstruct_result1519)
            unwrapped1520 = deconstruct_result1519
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1520)
                newline(pp)
                for (i1737, elem1521) in enumerate(unwrapped1520)
                    i1522 = i1737 - 1
                    if (i1522 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1521)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1738 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1738 = nothing
            end
            deconstruct_result1517 = _t1738
            if !isnothing(deconstruct_result1517)
                unwrapped1518 = deconstruct_result1517
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1518)
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
    flat1528 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1528)
        write(pp, flat1528)
        return nothing
    else
        _dollar_dollar = msg
        fields1524 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1525 = fields1524
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1526 = unwrapped_fields1525[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1526))
        newline(pp)
        field1527 = unwrapped_fields1525[2]
        pretty_relation_id(pp, field1527)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1532 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1532)
        write(pp, flat1532)
        return nothing
    else
        fields1529 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1529)
            newline(pp)
            for (i1739, elem1530) in enumerate(fields1529)
                i1531 = i1739 - 1
                if (i1531 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1530)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1543 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1543)
        write(pp, flat1543)
        return nothing
    else
        _dollar_dollar = msg
        _t1740 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1533 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1740,)
        unwrapped_fields1534 = fields1533
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1535 = unwrapped_fields1534[1]
        pretty_iceberg_locator(pp, field1535)
        newline(pp)
        field1536 = unwrapped_fields1534[2]
        pretty_iceberg_catalog_config(pp, field1536)
        newline(pp)
        field1537 = unwrapped_fields1534[3]
        pretty_export_iceberg_columns(pp, field1537)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_properties")
        field1538 = unwrapped_fields1534[4]
        if !isempty(field1538)
            newline(pp)
            for (i1741, elem1539) in enumerate(field1538)
                i1540 = i1741 - 1
                if (i1540 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1539)
            end
        end
        dedent!(pp)
        write(pp, ")")
        field1541 = unwrapped_fields1534[5]
        if !isnothing(field1541)
            newline(pp)
            opt_val1542 = field1541
            pretty_config_dict(pp, opt_val1542)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_columns(pp::PrettyPrinter, msg::Proto.ExportIcebergColumns)
    flat1550 = try_flat(pp, msg, pretty_export_iceberg_columns)
    if !isnothing(flat1550)
        write(pp, flat1550)
        return nothing
    else
        _dollar_dollar = msg
        fields1544 = (_dollar_dollar, _dollar_dollar.target_columns,)
        unwrapped_fields1545 = fields1544
        write(pp, "(columns")
        indent_sexp!(pp)
        newline(pp)
        field1546 = unwrapped_fields1545[1]
        pretty_export_iceberg_column_source(pp, field1546)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "target_columns")
        field1547 = unwrapped_fields1545[2]
        if !isempty(field1547)
            newline(pp)
            for (i1742, elem1548) in enumerate(field1547)
                i1549 = i1742 - 1
                if (i1549 > 0)
                    newline(pp)
                end
                pretty_export_iceberg_column(pp, elem1548)
            end
        end
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_column_source(pp::PrettyPrinter, msg::Proto.ExportIcebergColumns)
    flat1557 = try_flat(pp, msg, pretty_export_iceberg_column_source)
    if !isnothing(flat1557)
        write(pp, flat1557)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("source_gnf_defs"))
            _t1743 = _get_oneof_field(_dollar_dollar, :source_gnf_defs).defs
        else
            _t1743 = nothing
        end
        deconstruct_result1553 = _t1743
        if !isnothing(deconstruct_result1553)
            unwrapped1554 = deconstruct_result1553
            write(pp, "(source_gnf_defs")
            indent_sexp!(pp)
            if !isempty(unwrapped1554)
                newline(pp)
                for (i1744, elem1555) in enumerate(unwrapped1554)
                    i1556 = i1744 - 1
                    if (i1556 > 0)
                        newline(pp)
                    end
                    pretty_relation_id(pp, elem1555)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("source_table_def"))
                _t1745 = _get_oneof_field(_dollar_dollar, :source_table_def)
            else
                _t1745 = nothing
            end
            deconstruct_result1551 = _t1745
            if !isnothing(deconstruct_result1551)
                unwrapped1552 = deconstruct_result1551
                write(pp, "(source_table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1552)
                dedent!(pp)
                write(pp, ")")
            else
                throw(ParseError("No matching rule for export_iceberg_column_source"))
            end
        end
    end
    return nothing
end

function pretty_export_iceberg_column(pp::PrettyPrinter, msg::Proto.ExportIcebergColumn)
    flat1563 = try_flat(pp, msg, pretty_export_iceberg_column)
    if !isnothing(flat1563)
        write(pp, flat1563)
        return nothing
    else
        _dollar_dollar = msg
        fields1558 = (_dollar_dollar.name, _dollar_dollar.var"#type", _dollar_dollar.nullable,)
        unwrapped_fields1559 = fields1558
        write(pp, "(iceberg_column")
        indent_sexp!(pp)
        newline(pp)
        field1560 = unwrapped_fields1559[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1560))
        newline(pp)
        field1561 = unwrapped_fields1559[2]
        pretty_type(pp, field1561)
        newline(pp)
        field1562 = unwrapped_fields1559[3]
        pretty_boolean_value(pp, field1562)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1790, _rid) in enumerate(msg.ids)
        _idx = i1790 - 1
        newline(pp)
        write(pp, "(")
        _t1791 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1791)
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
    for (i1792, _elem) in enumerate(msg.keys)
        _idx = i1792 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1793, _elem) in enumerate(msg.values)
        _idx = i1793 - 1
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
    for (i1794, _elem) in enumerate(msg.columns)
        _idx = i1794 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, "))")
    dedent!(pp)
    return nothing
end

function pretty_export_iceberg_gnf_defs(pp::PrettyPrinter, msg::Proto.ExportIcebergGnfDefs)
    write(pp, "(export_iceberg_gnf_defs")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":defs (")
    for (i1795, _elem) in enumerate(msg.defs)
        _idx = i1795 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportIcebergColumns) = pretty_export_iceberg_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportIcebergColumn) = pretty_export_iceberg_column(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DebugInfo) = pretty_debug_info(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeConfig) = pretty_be_tree_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeLocator) = pretty_be_tree_locator(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DecimalValue) = pretty_decimal_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FunctionalDependency) = pretty_functional_dependency(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Int128Value) = pretty_int128_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MissingValue) = pretty_missing_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.UInt128Value) = pretty_u_int128_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportCSVColumns) = pretty_export_csv_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportIcebergGnfDefs) = pretty_export_iceberg_gnf_defs(pp, x)
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
