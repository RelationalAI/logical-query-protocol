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
    _computing::Set{Tuple{UInt,UInt}}
    _memo::Dict{Tuple{UInt,UInt},String}
    _memo_refs::Vector{Any}
    print_symbolic_relation_ids::Bool
    debug_info::Dict{Tuple{UInt64,UInt64},String}
    constant_formatter::ConstantFormatter
end

function PrettyPrinter(; max_width::Int=92, print_symbolic_relation_ids::Bool=true, constant_formatter::ConstantFormatter=DEFAULT_CONSTANT_FORMATTER)
    return PrettyPrinter(
        IOBuffer(), [0], 0, true, "\n", max_width,
        Set{Tuple{UInt,UInt}}(), Dict{Tuple{UInt,UInt},String}(), Any[],
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
    memo_key = (objectid(msg), objectid(pretty_fn))
    if !haskey(pp._memo, memo_key) && !(memo_key in pp._computing)
        push!(pp._computing, memo_key)
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
            pp._memo[memo_key] = String(copy(pp.io.data[1:pp.io.size]))
            push!(pp._memo_refs, msg)
        finally
            pp.io = saved_io
            pp.separator = saved_sep
            pp.indent_stack = saved_indent
            pp.column = saved_col
            pp.at_line_start = saved_at_line_start
            delete!(pp._computing, memo_key)
        end
    end
    if haskey(pp._memo, memo_key)
        flat = pp._memo[memo_key]
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
    _t1770 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1770
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1771 = Proto.Value(value=OneOf(:int_value, v))
    return _t1771
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1772 = Proto.Value(value=OneOf(:float_value, v))
    return _t1772
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1773 = Proto.Value(value=OneOf(:string_value, v))
    return _t1773
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1774 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1774
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1775 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1775
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1776 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1776,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1777 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1777,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1778 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1778,))
            end
        end
    end
    _t1779 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1779,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1780 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1780,))
    _t1781 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1781,))
    if msg.new_line != ""
        _t1782 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1782,))
    end
    _t1783 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1783,))
    _t1784 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1784,))
    _t1785 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1785,))
    if msg.comment != ""
        _t1786 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1786,))
    end
    for missing_string in msg.missing_strings
        _t1787 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1787,))
    end
    _t1788 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1788,))
    _t1789 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1789,))
    _t1790 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1790,))
    if msg.partition_size_mb != 0
        _t1791 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1791,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1792 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1792,))
    _t1793 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1793,))
    _t1794 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1794,))
    _t1795 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1795,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1796 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1796,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1797 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1797,))
        end
    end
    _t1798 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1798,))
    _t1799 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1799,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1800 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1800,))
    end
    if !isnothing(msg.compression)
        _t1801 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1801,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1802 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1802,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1803 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1803,))
    end
    if !isnothing(msg.syntax_delim)
        _t1804 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1804,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1805 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1805,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1806 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1806,))
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
        _t1807 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1808 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1809 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1810 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1810,))
    end
    if msg.target_file_size_bytes != 0
        _t1811 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1811,))
    end
    if msg.compression != ""
        _t1812 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1812,))
    end
    if length(result) == 0
        return nothing
    else
        _t1813 = nothing
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
        _t1814 = nothing
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
    flat803 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat803)
        write(pp, flat803)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1588 = _dollar_dollar.configure
        else
            _t1588 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1589 = _dollar_dollar.sync
        else
            _t1589 = nothing
        end
        fields794 = (_t1588, _t1589, _dollar_dollar.epochs,)
        unwrapped_fields795 = fields794
        write(pp, "(transaction")
        indent_sexp!(pp)
        field796 = unwrapped_fields795[1]
        if !isnothing(field796)
            newline(pp)
            opt_val797 = field796
            pretty_configure(pp, opt_val797)
        end
        field798 = unwrapped_fields795[2]
        if !isnothing(field798)
            newline(pp)
            opt_val799 = field798
            pretty_sync(pp, opt_val799)
        end
        field800 = unwrapped_fields795[3]
        if !isempty(field800)
            newline(pp)
            for (i1590, elem801) in enumerate(field800)
                i802 = i1590 - 1
                if (i802 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem801)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat806 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat806)
        write(pp, flat806)
        return nothing
    else
        _dollar_dollar = msg
        _t1591 = deconstruct_configure(pp, _dollar_dollar)
        fields804 = _t1591
        unwrapped_fields805 = fields804
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields805)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat810 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat810)
        write(pp, flat810)
        return nothing
    else
        fields807 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields807)
            newline(pp)
            for (i1592, elem808) in enumerate(fields807)
                i809 = i1592 - 1
                if (i809 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem808)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat815 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat815)
        write(pp, flat815)
        return nothing
    else
        _dollar_dollar = msg
        fields811 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields812 = fields811
        write(pp, ":")
        field813 = unwrapped_fields812[1]
        write(pp, field813)
        write(pp, " ")
        field814 = unwrapped_fields812[2]
        pretty_raw_value(pp, field814)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat841 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat841)
        write(pp, flat841)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1593 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1593 = nothing
        end
        deconstruct_result839 = _t1593
        if !isnothing(deconstruct_result839)
            unwrapped840 = deconstruct_result839
            pretty_raw_date(pp, unwrapped840)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1594 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1594 = nothing
            end
            deconstruct_result837 = _t1594
            if !isnothing(deconstruct_result837)
                unwrapped838 = deconstruct_result837
                pretty_raw_datetime(pp, unwrapped838)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1595 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1595 = nothing
                end
                deconstruct_result835 = _t1595
                if !isnothing(deconstruct_result835)
                    unwrapped836 = deconstruct_result835
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped836))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1596 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1596 = nothing
                    end
                    deconstruct_result833 = _t1596
                    if !isnothing(deconstruct_result833)
                        unwrapped834 = deconstruct_result833
                        write(pp, (string(Int64(unwrapped834)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1597 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1597 = nothing
                        end
                        deconstruct_result831 = _t1597
                        if !isnothing(deconstruct_result831)
                            unwrapped832 = deconstruct_result831
                            write(pp, string(unwrapped832))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1598 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1598 = nothing
                            end
                            deconstruct_result829 = _t1598
                            if !isnothing(deconstruct_result829)
                                unwrapped830 = deconstruct_result829
                                write(pp, format_float32_literal(unwrapped830))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1599 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1599 = nothing
                                end
                                deconstruct_result827 = _t1599
                                if !isnothing(deconstruct_result827)
                                    unwrapped828 = deconstruct_result827
                                    write(pp, lowercase(string(unwrapped828)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1600 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1600 = nothing
                                    end
                                    deconstruct_result825 = _t1600
                                    if !isnothing(deconstruct_result825)
                                        unwrapped826 = deconstruct_result825
                                        write(pp, (string(Int64(unwrapped826)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1601 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1601 = nothing
                                        end
                                        deconstruct_result823 = _t1601
                                        if !isnothing(deconstruct_result823)
                                            unwrapped824 = deconstruct_result823
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped824))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1602 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1602 = nothing
                                            end
                                            deconstruct_result821 = _t1602
                                            if !isnothing(deconstruct_result821)
                                                unwrapped822 = deconstruct_result821
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped822))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1603 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1603 = nothing
                                                end
                                                deconstruct_result819 = _t1603
                                                if !isnothing(deconstruct_result819)
                                                    unwrapped820 = deconstruct_result819
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped820))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1604 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1604 = nothing
                                                    end
                                                    deconstruct_result817 = _t1604
                                                    if !isnothing(deconstruct_result817)
                                                        unwrapped818 = deconstruct_result817
                                                        pretty_boolean_value(pp, unwrapped818)
                                                    else
                                                        fields816 = msg
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
    flat847 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat847)
        write(pp, flat847)
        return nothing
    else
        _dollar_dollar = msg
        fields842 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields843 = fields842
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field844 = unwrapped_fields843[1]
        write(pp, string(field844))
        newline(pp)
        field845 = unwrapped_fields843[2]
        write(pp, string(field845))
        newline(pp)
        field846 = unwrapped_fields843[3]
        write(pp, string(field846))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat858 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat858)
        write(pp, flat858)
        return nothing
    else
        _dollar_dollar = msg
        fields848 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields849 = fields848
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field850 = unwrapped_fields849[1]
        write(pp, string(field850))
        newline(pp)
        field851 = unwrapped_fields849[2]
        write(pp, string(field851))
        newline(pp)
        field852 = unwrapped_fields849[3]
        write(pp, string(field852))
        newline(pp)
        field853 = unwrapped_fields849[4]
        write(pp, string(field853))
        newline(pp)
        field854 = unwrapped_fields849[5]
        write(pp, string(field854))
        newline(pp)
        field855 = unwrapped_fields849[6]
        write(pp, string(field855))
        field856 = unwrapped_fields849[7]
        if !isnothing(field856)
            newline(pp)
            opt_val857 = field856
            write(pp, string(opt_val857))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1605 = ()
    else
        _t1605 = nothing
    end
    deconstruct_result861 = _t1605
    if !isnothing(deconstruct_result861)
        unwrapped862 = deconstruct_result861
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1606 = ()
        else
            _t1606 = nothing
        end
        deconstruct_result859 = _t1606
        if !isnothing(deconstruct_result859)
            unwrapped860 = deconstruct_result859
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat867 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat867)
        write(pp, flat867)
        return nothing
    else
        _dollar_dollar = msg
        fields863 = _dollar_dollar.fragments
        unwrapped_fields864 = fields863
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields864)
            newline(pp)
            for (i1607, elem865) in enumerate(unwrapped_fields864)
                i866 = i1607 - 1
                if (i866 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem865)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat870 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat870)
        write(pp, flat870)
        return nothing
    else
        _dollar_dollar = msg
        fields868 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields869 = fields868
        write(pp, ":")
        write(pp, unwrapped_fields869)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat877 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat877)
        write(pp, flat877)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1608 = _dollar_dollar.writes
        else
            _t1608 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1609 = _dollar_dollar.reads
        else
            _t1609 = nothing
        end
        fields871 = (_t1608, _t1609,)
        unwrapped_fields872 = fields871
        write(pp, "(epoch")
        indent_sexp!(pp)
        field873 = unwrapped_fields872[1]
        if !isnothing(field873)
            newline(pp)
            opt_val874 = field873
            pretty_epoch_writes(pp, opt_val874)
        end
        field875 = unwrapped_fields872[2]
        if !isnothing(field875)
            newline(pp)
            opt_val876 = field875
            pretty_epoch_reads(pp, opt_val876)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat881 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat881)
        write(pp, flat881)
        return nothing
    else
        fields878 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields878)
            newline(pp)
            for (i1610, elem879) in enumerate(fields878)
                i880 = i1610 - 1
                if (i880 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem879)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat890 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat890)
        write(pp, flat890)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1611 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1611 = nothing
        end
        deconstruct_result888 = _t1611
        if !isnothing(deconstruct_result888)
            unwrapped889 = deconstruct_result888
            pretty_define(pp, unwrapped889)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1612 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1612 = nothing
            end
            deconstruct_result886 = _t1612
            if !isnothing(deconstruct_result886)
                unwrapped887 = deconstruct_result886
                pretty_undefine(pp, unwrapped887)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1613 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1613 = nothing
                end
                deconstruct_result884 = _t1613
                if !isnothing(deconstruct_result884)
                    unwrapped885 = deconstruct_result884
                    pretty_context(pp, unwrapped885)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1614 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1614 = nothing
                    end
                    deconstruct_result882 = _t1614
                    if !isnothing(deconstruct_result882)
                        unwrapped883 = deconstruct_result882
                        pretty_snapshot(pp, unwrapped883)
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
    flat893 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat893)
        write(pp, flat893)
        return nothing
    else
        _dollar_dollar = msg
        fields891 = _dollar_dollar.fragment
        unwrapped_fields892 = fields891
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields892)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat900 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat900)
        write(pp, flat900)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields894 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields895 = fields894
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field896 = unwrapped_fields895[1]
        pretty_new_fragment_id(pp, field896)
        field897 = unwrapped_fields895[2]
        if !isempty(field897)
            newline(pp)
            for (i1615, elem898) in enumerate(field897)
                i899 = i1615 - 1
                if (i899 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem898)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat902 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat902)
        write(pp, flat902)
        return nothing
    else
        fields901 = msg
        pretty_fragment_id(pp, fields901)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat911 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat911)
        write(pp, flat911)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1616 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1616 = nothing
        end
        deconstruct_result909 = _t1616
        if !isnothing(deconstruct_result909)
            unwrapped910 = deconstruct_result909
            pretty_def(pp, unwrapped910)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1617 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1617 = nothing
            end
            deconstruct_result907 = _t1617
            if !isnothing(deconstruct_result907)
                unwrapped908 = deconstruct_result907
                pretty_algorithm(pp, unwrapped908)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1618 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1618 = nothing
                end
                deconstruct_result905 = _t1618
                if !isnothing(deconstruct_result905)
                    unwrapped906 = deconstruct_result905
                    pretty_constraint(pp, unwrapped906)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1619 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1619 = nothing
                    end
                    deconstruct_result903 = _t1619
                    if !isnothing(deconstruct_result903)
                        unwrapped904 = deconstruct_result903
                        pretty_data(pp, unwrapped904)
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
    flat918 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat918)
        write(pp, flat918)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1620 = _dollar_dollar.attrs
        else
            _t1620 = nothing
        end
        fields912 = (_dollar_dollar.name, _dollar_dollar.body, _t1620,)
        unwrapped_fields913 = fields912
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field914 = unwrapped_fields913[1]
        pretty_relation_id(pp, field914)
        newline(pp)
        field915 = unwrapped_fields913[2]
        pretty_abstraction(pp, field915)
        field916 = unwrapped_fields913[3]
        if !isnothing(field916)
            newline(pp)
            opt_val917 = field916
            pretty_attrs(pp, opt_val917)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat923 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat923)
        write(pp, flat923)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1622 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1621 = _t1622
        else
            _t1621 = nothing
        end
        deconstruct_result921 = _t1621
        if !isnothing(deconstruct_result921)
            unwrapped922 = deconstruct_result921
            write(pp, ":")
            write(pp, unwrapped922)
        else
            _dollar_dollar = msg
            _t1623 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result919 = _t1623
            if !isnothing(deconstruct_result919)
                unwrapped920 = deconstruct_result919
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped920))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat928 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat928)
        write(pp, flat928)
        return nothing
    else
        _dollar_dollar = msg
        _t1624 = deconstruct_bindings(pp, _dollar_dollar)
        fields924 = (_t1624, _dollar_dollar.value,)
        unwrapped_fields925 = fields924
        write(pp, "(")
        indent!(pp)
        field926 = unwrapped_fields925[1]
        pretty_bindings(pp, field926)
        newline(pp)
        field927 = unwrapped_fields925[2]
        pretty_formula(pp, field927)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat936 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat936)
        write(pp, flat936)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1625 = _dollar_dollar[2]
        else
            _t1625 = nothing
        end
        fields929 = (_dollar_dollar[1], _t1625,)
        unwrapped_fields930 = fields929
        write(pp, "[")
        indent!(pp)
        field931 = unwrapped_fields930[1]
        for (i1626, elem932) in enumerate(field931)
            i933 = i1626 - 1
            if (i933 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem932)
        end
        field934 = unwrapped_fields930[2]
        if !isnothing(field934)
            newline(pp)
            opt_val935 = field934
            pretty_value_bindings(pp, opt_val935)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat941 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat941)
        write(pp, flat941)
        return nothing
    else
        _dollar_dollar = msg
        fields937 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields938 = fields937
        field939 = unwrapped_fields938[1]
        write(pp, field939)
        write(pp, "::")
        field940 = unwrapped_fields938[2]
        pretty_type(pp, field940)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat970 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat970)
        write(pp, flat970)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1627 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1627 = nothing
        end
        deconstruct_result968 = _t1627
        if !isnothing(deconstruct_result968)
            unwrapped969 = deconstruct_result968
            pretty_unspecified_type(pp, unwrapped969)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1628 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1628 = nothing
            end
            deconstruct_result966 = _t1628
            if !isnothing(deconstruct_result966)
                unwrapped967 = deconstruct_result966
                pretty_string_type(pp, unwrapped967)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1629 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1629 = nothing
                end
                deconstruct_result964 = _t1629
                if !isnothing(deconstruct_result964)
                    unwrapped965 = deconstruct_result964
                    pretty_int_type(pp, unwrapped965)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1630 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1630 = nothing
                    end
                    deconstruct_result962 = _t1630
                    if !isnothing(deconstruct_result962)
                        unwrapped963 = deconstruct_result962
                        pretty_float_type(pp, unwrapped963)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1631 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1631 = nothing
                        end
                        deconstruct_result960 = _t1631
                        if !isnothing(deconstruct_result960)
                            unwrapped961 = deconstruct_result960
                            pretty_uint128_type(pp, unwrapped961)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1632 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1632 = nothing
                            end
                            deconstruct_result958 = _t1632
                            if !isnothing(deconstruct_result958)
                                unwrapped959 = deconstruct_result958
                                pretty_int128_type(pp, unwrapped959)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1633 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1633 = nothing
                                end
                                deconstruct_result956 = _t1633
                                if !isnothing(deconstruct_result956)
                                    unwrapped957 = deconstruct_result956
                                    pretty_date_type(pp, unwrapped957)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1634 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1634 = nothing
                                    end
                                    deconstruct_result954 = _t1634
                                    if !isnothing(deconstruct_result954)
                                        unwrapped955 = deconstruct_result954
                                        pretty_datetime_type(pp, unwrapped955)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1635 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1635 = nothing
                                        end
                                        deconstruct_result952 = _t1635
                                        if !isnothing(deconstruct_result952)
                                            unwrapped953 = deconstruct_result952
                                            pretty_missing_type(pp, unwrapped953)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1636 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1636 = nothing
                                            end
                                            deconstruct_result950 = _t1636
                                            if !isnothing(deconstruct_result950)
                                                unwrapped951 = deconstruct_result950
                                                pretty_decimal_type(pp, unwrapped951)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1637 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1637 = nothing
                                                end
                                                deconstruct_result948 = _t1637
                                                if !isnothing(deconstruct_result948)
                                                    unwrapped949 = deconstruct_result948
                                                    pretty_boolean_type(pp, unwrapped949)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1638 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1638 = nothing
                                                    end
                                                    deconstruct_result946 = _t1638
                                                    if !isnothing(deconstruct_result946)
                                                        unwrapped947 = deconstruct_result946
                                                        pretty_int32_type(pp, unwrapped947)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1639 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1639 = nothing
                                                        end
                                                        deconstruct_result944 = _t1639
                                                        if !isnothing(deconstruct_result944)
                                                            unwrapped945 = deconstruct_result944
                                                            pretty_float32_type(pp, unwrapped945)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1640 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1640 = nothing
                                                            end
                                                            deconstruct_result942 = _t1640
                                                            if !isnothing(deconstruct_result942)
                                                                unwrapped943 = deconstruct_result942
                                                                pretty_uint32_type(pp, unwrapped943)
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
    fields971 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields972 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields973 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields974 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields975 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields976 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields977 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields978 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields979 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat984 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat984)
        write(pp, flat984)
        return nothing
    else
        _dollar_dollar = msg
        fields980 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields981 = fields980
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field982 = unwrapped_fields981[1]
        write(pp, string(field982))
        newline(pp)
        field983 = unwrapped_fields981[2]
        write(pp, string(field983))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields985 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields986 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields987 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields988 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat992 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat992)
        write(pp, flat992)
        return nothing
    else
        fields989 = msg
        write(pp, "|")
        if !isempty(fields989)
            write(pp, " ")
            for (i1641, elem990) in enumerate(fields989)
                i991 = i1641 - 1
                if (i991 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem990)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1019 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1019)
        write(pp, flat1019)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1642 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1642 = nothing
        end
        deconstruct_result1017 = _t1642
        if !isnothing(deconstruct_result1017)
            unwrapped1018 = deconstruct_result1017
            pretty_true(pp, unwrapped1018)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1643 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1643 = nothing
            end
            deconstruct_result1015 = _t1643
            if !isnothing(deconstruct_result1015)
                unwrapped1016 = deconstruct_result1015
                pretty_false(pp, unwrapped1016)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1644 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1644 = nothing
                end
                deconstruct_result1013 = _t1644
                if !isnothing(deconstruct_result1013)
                    unwrapped1014 = deconstruct_result1013
                    pretty_exists(pp, unwrapped1014)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1645 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1645 = nothing
                    end
                    deconstruct_result1011 = _t1645
                    if !isnothing(deconstruct_result1011)
                        unwrapped1012 = deconstruct_result1011
                        pretty_reduce(pp, unwrapped1012)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1646 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1646 = nothing
                        end
                        deconstruct_result1009 = _t1646
                        if !isnothing(deconstruct_result1009)
                            unwrapped1010 = deconstruct_result1009
                            pretty_conjunction(pp, unwrapped1010)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1647 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1647 = nothing
                            end
                            deconstruct_result1007 = _t1647
                            if !isnothing(deconstruct_result1007)
                                unwrapped1008 = deconstruct_result1007
                                pretty_disjunction(pp, unwrapped1008)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1648 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1648 = nothing
                                end
                                deconstruct_result1005 = _t1648
                                if !isnothing(deconstruct_result1005)
                                    unwrapped1006 = deconstruct_result1005
                                    pretty_not(pp, unwrapped1006)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1649 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1649 = nothing
                                    end
                                    deconstruct_result1003 = _t1649
                                    if !isnothing(deconstruct_result1003)
                                        unwrapped1004 = deconstruct_result1003
                                        pretty_ffi(pp, unwrapped1004)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1650 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1650 = nothing
                                        end
                                        deconstruct_result1001 = _t1650
                                        if !isnothing(deconstruct_result1001)
                                            unwrapped1002 = deconstruct_result1001
                                            pretty_atom(pp, unwrapped1002)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1651 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1651 = nothing
                                            end
                                            deconstruct_result999 = _t1651
                                            if !isnothing(deconstruct_result999)
                                                unwrapped1000 = deconstruct_result999
                                                pretty_pragma(pp, unwrapped1000)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1652 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1652 = nothing
                                                end
                                                deconstruct_result997 = _t1652
                                                if !isnothing(deconstruct_result997)
                                                    unwrapped998 = deconstruct_result997
                                                    pretty_primitive(pp, unwrapped998)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1653 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1653 = nothing
                                                    end
                                                    deconstruct_result995 = _t1653
                                                    if !isnothing(deconstruct_result995)
                                                        unwrapped996 = deconstruct_result995
                                                        pretty_rel_atom(pp, unwrapped996)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1654 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1654 = nothing
                                                        end
                                                        deconstruct_result993 = _t1654
                                                        if !isnothing(deconstruct_result993)
                                                            unwrapped994 = deconstruct_result993
                                                            pretty_cast(pp, unwrapped994)
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
    fields1020 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1021 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1026 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1026)
        write(pp, flat1026)
        return nothing
    else
        _dollar_dollar = msg
        _t1655 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1022 = (_t1655, _dollar_dollar.body.value,)
        unwrapped_fields1023 = fields1022
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1024 = unwrapped_fields1023[1]
        pretty_bindings(pp, field1024)
        newline(pp)
        field1025 = unwrapped_fields1023[2]
        pretty_formula(pp, field1025)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1032 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1032)
        write(pp, flat1032)
        return nothing
    else
        _dollar_dollar = msg
        fields1027 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1028 = fields1027
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1029 = unwrapped_fields1028[1]
        pretty_abstraction(pp, field1029)
        newline(pp)
        field1030 = unwrapped_fields1028[2]
        pretty_abstraction(pp, field1030)
        newline(pp)
        field1031 = unwrapped_fields1028[3]
        pretty_terms(pp, field1031)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1036 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1036)
        write(pp, flat1036)
        return nothing
    else
        fields1033 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1033)
            newline(pp)
            for (i1656, elem1034) in enumerate(fields1033)
                i1035 = i1656 - 1
                if (i1035 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1034)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1041 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1041)
        write(pp, flat1041)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1657 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1657 = nothing
        end
        deconstruct_result1039 = _t1657
        if !isnothing(deconstruct_result1039)
            unwrapped1040 = deconstruct_result1039
            pretty_var(pp, unwrapped1040)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1658 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1658 = nothing
            end
            deconstruct_result1037 = _t1658
            if !isnothing(deconstruct_result1037)
                unwrapped1038 = deconstruct_result1037
                pretty_value(pp, unwrapped1038)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1044 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1044)
        write(pp, flat1044)
        return nothing
    else
        _dollar_dollar = msg
        fields1042 = _dollar_dollar.name
        unwrapped_fields1043 = fields1042
        write(pp, unwrapped_fields1043)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1070 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1070)
        write(pp, flat1070)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1659 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1659 = nothing
        end
        deconstruct_result1068 = _t1659
        if !isnothing(deconstruct_result1068)
            unwrapped1069 = deconstruct_result1068
            pretty_date(pp, unwrapped1069)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1660 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1660 = nothing
            end
            deconstruct_result1066 = _t1660
            if !isnothing(deconstruct_result1066)
                unwrapped1067 = deconstruct_result1066
                pretty_datetime(pp, unwrapped1067)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1661 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1661 = nothing
                end
                deconstruct_result1064 = _t1661
                if !isnothing(deconstruct_result1064)
                    unwrapped1065 = deconstruct_result1064
                    write(pp, format_string(pp, unwrapped1065))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1662 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1662 = nothing
                    end
                    deconstruct_result1062 = _t1662
                    if !isnothing(deconstruct_result1062)
                        unwrapped1063 = deconstruct_result1062
                        write(pp, format_int32(pp, unwrapped1063))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1663 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1663 = nothing
                        end
                        deconstruct_result1060 = _t1663
                        if !isnothing(deconstruct_result1060)
                            unwrapped1061 = deconstruct_result1060
                            write(pp, format_int(pp, unwrapped1061))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1664 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1664 = nothing
                            end
                            deconstruct_result1058 = _t1664
                            if !isnothing(deconstruct_result1058)
                                unwrapped1059 = deconstruct_result1058
                                write(pp, format_float32(pp, unwrapped1059))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1665 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1665 = nothing
                                end
                                deconstruct_result1056 = _t1665
                                if !isnothing(deconstruct_result1056)
                                    unwrapped1057 = deconstruct_result1056
                                    write(pp, format_float(pp, unwrapped1057))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1666 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1666 = nothing
                                    end
                                    deconstruct_result1054 = _t1666
                                    if !isnothing(deconstruct_result1054)
                                        unwrapped1055 = deconstruct_result1054
                                        write(pp, format_uint32(pp, unwrapped1055))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1667 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1667 = nothing
                                        end
                                        deconstruct_result1052 = _t1667
                                        if !isnothing(deconstruct_result1052)
                                            unwrapped1053 = deconstruct_result1052
                                            write(pp, format_uint128(pp, unwrapped1053))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1668 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1668 = nothing
                                            end
                                            deconstruct_result1050 = _t1668
                                            if !isnothing(deconstruct_result1050)
                                                unwrapped1051 = deconstruct_result1050
                                                write(pp, format_int128(pp, unwrapped1051))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1669 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1669 = nothing
                                                end
                                                deconstruct_result1048 = _t1669
                                                if !isnothing(deconstruct_result1048)
                                                    unwrapped1049 = deconstruct_result1048
                                                    write(pp, format_decimal(pp, unwrapped1049))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1670 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1670 = nothing
                                                    end
                                                    deconstruct_result1046 = _t1670
                                                    if !isnothing(deconstruct_result1046)
                                                        unwrapped1047 = deconstruct_result1046
                                                        pretty_boolean_value(pp, unwrapped1047)
                                                    else
                                                        fields1045 = msg
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
    flat1076 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1076)
        write(pp, flat1076)
        return nothing
    else
        _dollar_dollar = msg
        fields1071 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1072 = fields1071
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1073 = unwrapped_fields1072[1]
        write(pp, format_int(pp, field1073))
        newline(pp)
        field1074 = unwrapped_fields1072[2]
        write(pp, format_int(pp, field1074))
        newline(pp)
        field1075 = unwrapped_fields1072[3]
        write(pp, format_int(pp, field1075))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1087 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1087)
        write(pp, flat1087)
        return nothing
    else
        _dollar_dollar = msg
        fields1077 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1078 = fields1077
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1079 = unwrapped_fields1078[1]
        write(pp, format_int(pp, field1079))
        newline(pp)
        field1080 = unwrapped_fields1078[2]
        write(pp, format_int(pp, field1080))
        newline(pp)
        field1081 = unwrapped_fields1078[3]
        write(pp, format_int(pp, field1081))
        newline(pp)
        field1082 = unwrapped_fields1078[4]
        write(pp, format_int(pp, field1082))
        newline(pp)
        field1083 = unwrapped_fields1078[5]
        write(pp, format_int(pp, field1083))
        newline(pp)
        field1084 = unwrapped_fields1078[6]
        write(pp, format_int(pp, field1084))
        field1085 = unwrapped_fields1078[7]
        if !isnothing(field1085)
            newline(pp)
            opt_val1086 = field1085
            write(pp, format_int(pp, opt_val1086))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1092 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        _dollar_dollar = msg
        fields1088 = _dollar_dollar.args
        unwrapped_fields1089 = fields1088
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1089)
            newline(pp)
            for (i1671, elem1090) in enumerate(unwrapped_fields1089)
                i1091 = i1671 - 1
                if (i1091 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1090)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1097 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1097)
        write(pp, flat1097)
        return nothing
    else
        _dollar_dollar = msg
        fields1093 = _dollar_dollar.args
        unwrapped_fields1094 = fields1093
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1094)
            newline(pp)
            for (i1672, elem1095) in enumerate(unwrapped_fields1094)
                i1096 = i1672 - 1
                if (i1096 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1095)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1100 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1100)
        write(pp, flat1100)
        return nothing
    else
        _dollar_dollar = msg
        fields1098 = _dollar_dollar.arg
        unwrapped_fields1099 = fields1098
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1099)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1106 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1106)
        write(pp, flat1106)
        return nothing
    else
        _dollar_dollar = msg
        fields1101 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1102 = fields1101
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1103 = unwrapped_fields1102[1]
        pretty_name(pp, field1103)
        newline(pp)
        field1104 = unwrapped_fields1102[2]
        pretty_ffi_args(pp, field1104)
        newline(pp)
        field1105 = unwrapped_fields1102[3]
        pretty_terms(pp, field1105)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1108 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1108)
        write(pp, flat1108)
        return nothing
    else
        fields1107 = msg
        write(pp, ":")
        write(pp, fields1107)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1112 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1112)
        write(pp, flat1112)
        return nothing
    else
        fields1109 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1109)
            newline(pp)
            for (i1673, elem1110) in enumerate(fields1109)
                i1111 = i1673 - 1
                if (i1111 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1110)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1119 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1119)
        write(pp, flat1119)
        return nothing
    else
        _dollar_dollar = msg
        fields1113 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1114 = fields1113
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1115 = unwrapped_fields1114[1]
        pretty_relation_id(pp, field1115)
        field1116 = unwrapped_fields1114[2]
        if !isempty(field1116)
            newline(pp)
            for (i1674, elem1117) in enumerate(field1116)
                i1118 = i1674 - 1
                if (i1118 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1117)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1126 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1126)
        write(pp, flat1126)
        return nothing
    else
        _dollar_dollar = msg
        fields1120 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1121 = fields1120
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1122 = unwrapped_fields1121[1]
        pretty_name(pp, field1122)
        field1123 = unwrapped_fields1121[2]
        if !isempty(field1123)
            newline(pp)
            for (i1675, elem1124) in enumerate(field1123)
                i1125 = i1675 - 1
                if (i1125 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1124)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1142 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1142)
        write(pp, flat1142)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1676 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1676 = nothing
        end
        guard_result1141 = _t1676
        if !isnothing(guard_result1141)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1677 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1677 = nothing
            end
            guard_result1140 = _t1677
            if !isnothing(guard_result1140)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1678 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1678 = nothing
                end
                guard_result1139 = _t1678
                if !isnothing(guard_result1139)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1679 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1679 = nothing
                    end
                    guard_result1138 = _t1679
                    if !isnothing(guard_result1138)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1680 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1680 = nothing
                        end
                        guard_result1137 = _t1680
                        if !isnothing(guard_result1137)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1681 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1681 = nothing
                            end
                            guard_result1136 = _t1681
                            if !isnothing(guard_result1136)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1682 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1682 = nothing
                                end
                                guard_result1135 = _t1682
                                if !isnothing(guard_result1135)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1683 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1683 = nothing
                                    end
                                    guard_result1134 = _t1683
                                    if !isnothing(guard_result1134)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1684 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1684 = nothing
                                        end
                                        guard_result1133 = _t1684
                                        if !isnothing(guard_result1133)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1127 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1128 = fields1127
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1129 = unwrapped_fields1128[1]
                                            pretty_name(pp, field1129)
                                            field1130 = unwrapped_fields1128[2]
                                            if !isempty(field1130)
                                                newline(pp)
                                                for (i1685, elem1131) in enumerate(field1130)
                                                    i1132 = i1685 - 1
                                                    if (i1132 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1131)
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
    flat1147 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1147)
        write(pp, flat1147)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1686 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1686 = nothing
        end
        fields1143 = _t1686
        unwrapped_fields1144 = fields1143
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1145 = unwrapped_fields1144[1]
        pretty_term(pp, field1145)
        newline(pp)
        field1146 = unwrapped_fields1144[2]
        pretty_term(pp, field1146)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1152 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1152)
        write(pp, flat1152)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1687 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1687 = nothing
        end
        fields1148 = _t1687
        unwrapped_fields1149 = fields1148
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1150 = unwrapped_fields1149[1]
        pretty_term(pp, field1150)
        newline(pp)
        field1151 = unwrapped_fields1149[2]
        pretty_term(pp, field1151)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1157 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1157)
        write(pp, flat1157)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1688 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1688 = nothing
        end
        fields1153 = _t1688
        unwrapped_fields1154 = fields1153
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1155 = unwrapped_fields1154[1]
        pretty_term(pp, field1155)
        newline(pp)
        field1156 = unwrapped_fields1154[2]
        pretty_term(pp, field1156)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1162 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1162)
        write(pp, flat1162)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1689 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1689 = nothing
        end
        fields1158 = _t1689
        unwrapped_fields1159 = fields1158
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1160 = unwrapped_fields1159[1]
        pretty_term(pp, field1160)
        newline(pp)
        field1161 = unwrapped_fields1159[2]
        pretty_term(pp, field1161)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1167 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1690 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1690 = nothing
        end
        fields1163 = _t1690
        unwrapped_fields1164 = fields1163
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1165 = unwrapped_fields1164[1]
        pretty_term(pp, field1165)
        newline(pp)
        field1166 = unwrapped_fields1164[2]
        pretty_term(pp, field1166)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1173 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1173)
        write(pp, flat1173)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1691 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1691 = nothing
        end
        fields1168 = _t1691
        unwrapped_fields1169 = fields1168
        write(pp, "(+")
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

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1179 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1692 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1692 = nothing
        end
        fields1174 = _t1692
        unwrapped_fields1175 = fields1174
        write(pp, "(-")
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

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1185 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1185)
        write(pp, flat1185)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1693 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1693 = nothing
        end
        fields1180 = _t1693
        unwrapped_fields1181 = fields1180
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1182 = unwrapped_fields1181[1]
        pretty_term(pp, field1182)
        newline(pp)
        field1183 = unwrapped_fields1181[2]
        pretty_term(pp, field1183)
        newline(pp)
        field1184 = unwrapped_fields1181[3]
        pretty_term(pp, field1184)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1191 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1191)
        write(pp, flat1191)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1694 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1694 = nothing
        end
        fields1186 = _t1694
        unwrapped_fields1187 = fields1186
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1188 = unwrapped_fields1187[1]
        pretty_term(pp, field1188)
        newline(pp)
        field1189 = unwrapped_fields1187[2]
        pretty_term(pp, field1189)
        newline(pp)
        field1190 = unwrapped_fields1187[3]
        pretty_term(pp, field1190)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1196 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1196)
        write(pp, flat1196)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1695 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1695 = nothing
        end
        deconstruct_result1194 = _t1695
        if !isnothing(deconstruct_result1194)
            unwrapped1195 = deconstruct_result1194
            pretty_specialized_value(pp, unwrapped1195)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1696 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1696 = nothing
            end
            deconstruct_result1192 = _t1696
            if !isnothing(deconstruct_result1192)
                unwrapped1193 = deconstruct_result1192
                pretty_term(pp, unwrapped1193)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1198 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1198)
        write(pp, flat1198)
        return nothing
    else
        fields1197 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1197)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1205 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1205)
        write(pp, flat1205)
        return nothing
    else
        _dollar_dollar = msg
        fields1199 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1200 = fields1199
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1201 = unwrapped_fields1200[1]
        pretty_name(pp, field1201)
        field1202 = unwrapped_fields1200[2]
        if !isempty(field1202)
            newline(pp)
            for (i1697, elem1203) in enumerate(field1202)
                i1204 = i1697 - 1
                if (i1204 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1203)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1210 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1210)
        write(pp, flat1210)
        return nothing
    else
        _dollar_dollar = msg
        fields1206 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1207 = fields1206
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1208 = unwrapped_fields1207[1]
        pretty_term(pp, field1208)
        newline(pp)
        field1209 = unwrapped_fields1207[2]
        pretty_term(pp, field1209)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1214 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1214)
        write(pp, flat1214)
        return nothing
    else
        fields1211 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1211)
            newline(pp)
            for (i1698, elem1212) in enumerate(fields1211)
                i1213 = i1698 - 1
                if (i1213 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1212)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1221 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1221)
        write(pp, flat1221)
        return nothing
    else
        _dollar_dollar = msg
        fields1215 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1216 = fields1215
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1217 = unwrapped_fields1216[1]
        pretty_name(pp, field1217)
        field1218 = unwrapped_fields1216[2]
        if !isempty(field1218)
            newline(pp)
            for (i1699, elem1219) in enumerate(field1218)
                i1220 = i1699 - 1
                if (i1220 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1219)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1230 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1230)
        write(pp, flat1230)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1700 = _dollar_dollar.attrs
        else
            _t1700 = nothing
        end
        fields1222 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1700,)
        unwrapped_fields1223 = fields1222
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1224 = unwrapped_fields1223[1]
        if !isempty(field1224)
            newline(pp)
            for (i1701, elem1225) in enumerate(field1224)
                i1226 = i1701 - 1
                if (i1226 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1225)
            end
        end
        newline(pp)
        field1227 = unwrapped_fields1223[2]
        pretty_script(pp, field1227)
        field1228 = unwrapped_fields1223[3]
        if !isnothing(field1228)
            newline(pp)
            opt_val1229 = field1228
            pretty_attrs(pp, opt_val1229)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1235 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1235)
        write(pp, flat1235)
        return nothing
    else
        _dollar_dollar = msg
        fields1231 = _dollar_dollar.constructs
        unwrapped_fields1232 = fields1231
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1232)
            newline(pp)
            for (i1702, elem1233) in enumerate(unwrapped_fields1232)
                i1234 = i1702 - 1
                if (i1234 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1233)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1240 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1240)
        write(pp, flat1240)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1703 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1703 = nothing
        end
        deconstruct_result1238 = _t1703
        if !isnothing(deconstruct_result1238)
            unwrapped1239 = deconstruct_result1238
            pretty_loop(pp, unwrapped1239)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1704 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1704 = nothing
            end
            deconstruct_result1236 = _t1704
            if !isnothing(deconstruct_result1236)
                unwrapped1237 = deconstruct_result1236
                pretty_instruction(pp, unwrapped1237)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1247 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1247)
        write(pp, flat1247)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1705 = _dollar_dollar.attrs
        else
            _t1705 = nothing
        end
        fields1241 = (_dollar_dollar.init, _dollar_dollar.body, _t1705,)
        unwrapped_fields1242 = fields1241
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1243 = unwrapped_fields1242[1]
        pretty_init(pp, field1243)
        newline(pp)
        field1244 = unwrapped_fields1242[2]
        pretty_script(pp, field1244)
        field1245 = unwrapped_fields1242[3]
        if !isnothing(field1245)
            newline(pp)
            opt_val1246 = field1245
            pretty_attrs(pp, opt_val1246)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1251 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1251)
        write(pp, flat1251)
        return nothing
    else
        fields1248 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1248)
            newline(pp)
            for (i1706, elem1249) in enumerate(fields1248)
                i1250 = i1706 - 1
                if (i1250 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1249)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1262 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1262)
        write(pp, flat1262)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1707 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1707 = nothing
        end
        deconstruct_result1260 = _t1707
        if !isnothing(deconstruct_result1260)
            unwrapped1261 = deconstruct_result1260
            pretty_assign(pp, unwrapped1261)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1708 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1708 = nothing
            end
            deconstruct_result1258 = _t1708
            if !isnothing(deconstruct_result1258)
                unwrapped1259 = deconstruct_result1258
                pretty_upsert(pp, unwrapped1259)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1709 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1709 = nothing
                end
                deconstruct_result1256 = _t1709
                if !isnothing(deconstruct_result1256)
                    unwrapped1257 = deconstruct_result1256
                    pretty_break(pp, unwrapped1257)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1710 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1710 = nothing
                    end
                    deconstruct_result1254 = _t1710
                    if !isnothing(deconstruct_result1254)
                        unwrapped1255 = deconstruct_result1254
                        pretty_monoid_def(pp, unwrapped1255)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1711 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1711 = nothing
                        end
                        deconstruct_result1252 = _t1711
                        if !isnothing(deconstruct_result1252)
                            unwrapped1253 = deconstruct_result1252
                            pretty_monus_def(pp, unwrapped1253)
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
    flat1269 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1269)
        write(pp, flat1269)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1712 = _dollar_dollar.attrs
        else
            _t1712 = nothing
        end
        fields1263 = (_dollar_dollar.name, _dollar_dollar.body, _t1712,)
        unwrapped_fields1264 = fields1263
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1265 = unwrapped_fields1264[1]
        pretty_relation_id(pp, field1265)
        newline(pp)
        field1266 = unwrapped_fields1264[2]
        pretty_abstraction(pp, field1266)
        field1267 = unwrapped_fields1264[3]
        if !isnothing(field1267)
            newline(pp)
            opt_val1268 = field1267
            pretty_attrs(pp, opt_val1268)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1276 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1276)
        write(pp, flat1276)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1713 = _dollar_dollar.attrs
        else
            _t1713 = nothing
        end
        fields1270 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1713,)
        unwrapped_fields1271 = fields1270
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1272 = unwrapped_fields1271[1]
        pretty_relation_id(pp, field1272)
        newline(pp)
        field1273 = unwrapped_fields1271[2]
        pretty_abstraction_with_arity(pp, field1273)
        field1274 = unwrapped_fields1271[3]
        if !isnothing(field1274)
            newline(pp)
            opt_val1275 = field1274
            pretty_attrs(pp, opt_val1275)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1281 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1281)
        write(pp, flat1281)
        return nothing
    else
        _dollar_dollar = msg
        _t1714 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1277 = (_t1714, _dollar_dollar[1].value,)
        unwrapped_fields1278 = fields1277
        write(pp, "(")
        indent!(pp)
        field1279 = unwrapped_fields1278[1]
        pretty_bindings(pp, field1279)
        newline(pp)
        field1280 = unwrapped_fields1278[2]
        pretty_formula(pp, field1280)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1288 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1288)
        write(pp, flat1288)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1715 = _dollar_dollar.attrs
        else
            _t1715 = nothing
        end
        fields1282 = (_dollar_dollar.name, _dollar_dollar.body, _t1715,)
        unwrapped_fields1283 = fields1282
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1284 = unwrapped_fields1283[1]
        pretty_relation_id(pp, field1284)
        newline(pp)
        field1285 = unwrapped_fields1283[2]
        pretty_abstraction(pp, field1285)
        field1286 = unwrapped_fields1283[3]
        if !isnothing(field1286)
            newline(pp)
            opt_val1287 = field1286
            pretty_attrs(pp, opt_val1287)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1296 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1296)
        write(pp, flat1296)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1716 = _dollar_dollar.attrs
        else
            _t1716 = nothing
        end
        fields1289 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1716,)
        unwrapped_fields1290 = fields1289
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1291 = unwrapped_fields1290[1]
        pretty_monoid(pp, field1291)
        newline(pp)
        field1292 = unwrapped_fields1290[2]
        pretty_relation_id(pp, field1292)
        newline(pp)
        field1293 = unwrapped_fields1290[3]
        pretty_abstraction_with_arity(pp, field1293)
        field1294 = unwrapped_fields1290[4]
        if !isnothing(field1294)
            newline(pp)
            opt_val1295 = field1294
            pretty_attrs(pp, opt_val1295)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1305 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1305)
        write(pp, flat1305)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1717 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1717 = nothing
        end
        deconstruct_result1303 = _t1717
        if !isnothing(deconstruct_result1303)
            unwrapped1304 = deconstruct_result1303
            pretty_or_monoid(pp, unwrapped1304)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1718 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1718 = nothing
            end
            deconstruct_result1301 = _t1718
            if !isnothing(deconstruct_result1301)
                unwrapped1302 = deconstruct_result1301
                pretty_min_monoid(pp, unwrapped1302)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1719 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1719 = nothing
                end
                deconstruct_result1299 = _t1719
                if !isnothing(deconstruct_result1299)
                    unwrapped1300 = deconstruct_result1299
                    pretty_max_monoid(pp, unwrapped1300)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1720 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1720 = nothing
                    end
                    deconstruct_result1297 = _t1720
                    if !isnothing(deconstruct_result1297)
                        unwrapped1298 = deconstruct_result1297
                        pretty_sum_monoid(pp, unwrapped1298)
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
    fields1306 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1309 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1309)
        write(pp, flat1309)
        return nothing
    else
        _dollar_dollar = msg
        fields1307 = _dollar_dollar.var"#type"
        unwrapped_fields1308 = fields1307
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1308)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1312 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1312)
        write(pp, flat1312)
        return nothing
    else
        _dollar_dollar = msg
        fields1310 = _dollar_dollar.var"#type"
        unwrapped_fields1311 = fields1310
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1311)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1315 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1315)
        write(pp, flat1315)
        return nothing
    else
        _dollar_dollar = msg
        fields1313 = _dollar_dollar.var"#type"
        unwrapped_fields1314 = fields1313
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1314)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1323 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1323)
        write(pp, flat1323)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1721 = _dollar_dollar.attrs
        else
            _t1721 = nothing
        end
        fields1316 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1721,)
        unwrapped_fields1317 = fields1316
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1318 = unwrapped_fields1317[1]
        pretty_monoid(pp, field1318)
        newline(pp)
        field1319 = unwrapped_fields1317[2]
        pretty_relation_id(pp, field1319)
        newline(pp)
        field1320 = unwrapped_fields1317[3]
        pretty_abstraction_with_arity(pp, field1320)
        field1321 = unwrapped_fields1317[4]
        if !isnothing(field1321)
            newline(pp)
            opt_val1322 = field1321
            pretty_attrs(pp, opt_val1322)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1330 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1330)
        write(pp, flat1330)
        return nothing
    else
        _dollar_dollar = msg
        fields1324 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1325 = fields1324
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1326 = unwrapped_fields1325[1]
        pretty_relation_id(pp, field1326)
        newline(pp)
        field1327 = unwrapped_fields1325[2]
        pretty_abstraction(pp, field1327)
        newline(pp)
        field1328 = unwrapped_fields1325[3]
        pretty_functional_dependency_keys(pp, field1328)
        newline(pp)
        field1329 = unwrapped_fields1325[4]
        pretty_functional_dependency_values(pp, field1329)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1334 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1334)
        write(pp, flat1334)
        return nothing
    else
        fields1331 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1331)
            newline(pp)
            for (i1722, elem1332) in enumerate(fields1331)
                i1333 = i1722 - 1
                if (i1333 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1332)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1338 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1338)
        write(pp, flat1338)
        return nothing
    else
        fields1335 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1335)
            newline(pp)
            for (i1723, elem1336) in enumerate(fields1335)
                i1337 = i1723 - 1
                if (i1337 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1336)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1347 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1347)
        write(pp, flat1347)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1724 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1724 = nothing
        end
        deconstruct_result1345 = _t1724
        if !isnothing(deconstruct_result1345)
            unwrapped1346 = deconstruct_result1345
            pretty_edb(pp, unwrapped1346)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1725 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1725 = nothing
            end
            deconstruct_result1343 = _t1725
            if !isnothing(deconstruct_result1343)
                unwrapped1344 = deconstruct_result1343
                pretty_betree_relation(pp, unwrapped1344)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1726 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1726 = nothing
                end
                deconstruct_result1341 = _t1726
                if !isnothing(deconstruct_result1341)
                    unwrapped1342 = deconstruct_result1341
                    pretty_csv_data(pp, unwrapped1342)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1727 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1727 = nothing
                    end
                    deconstruct_result1339 = _t1727
                    if !isnothing(deconstruct_result1339)
                        unwrapped1340 = deconstruct_result1339
                        pretty_iceberg_data(pp, unwrapped1340)
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
    flat1353 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1353)
        write(pp, flat1353)
        return nothing
    else
        _dollar_dollar = msg
        fields1348 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1349 = fields1348
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1350 = unwrapped_fields1349[1]
        pretty_relation_id(pp, field1350)
        newline(pp)
        field1351 = unwrapped_fields1349[2]
        pretty_edb_path(pp, field1351)
        newline(pp)
        field1352 = unwrapped_fields1349[3]
        pretty_edb_types(pp, field1352)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1357 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1357)
        write(pp, flat1357)
        return nothing
    else
        fields1354 = msg
        write(pp, "[")
        indent!(pp)
        for (i1728, elem1355) in enumerate(fields1354)
            i1356 = i1728 - 1
            if (i1356 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1355))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1361 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1361)
        write(pp, flat1361)
        return nothing
    else
        fields1358 = msg
        write(pp, "[")
        indent!(pp)
        for (i1729, elem1359) in enumerate(fields1358)
            i1360 = i1729 - 1
            if (i1360 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1359)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1366 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1366)
        write(pp, flat1366)
        return nothing
    else
        _dollar_dollar = msg
        fields1362 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1363 = fields1362
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1364 = unwrapped_fields1363[1]
        pretty_relation_id(pp, field1364)
        newline(pp)
        field1365 = unwrapped_fields1363[2]
        pretty_betree_info(pp, field1365)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1372 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1372)
        write(pp, flat1372)
        return nothing
    else
        _dollar_dollar = msg
        _t1730 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1367 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1730,)
        unwrapped_fields1368 = fields1367
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1369 = unwrapped_fields1368[1]
        pretty_betree_info_key_types(pp, field1369)
        newline(pp)
        field1370 = unwrapped_fields1368[2]
        pretty_betree_info_value_types(pp, field1370)
        newline(pp)
        field1371 = unwrapped_fields1368[3]
        pretty_config_dict(pp, field1371)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1376 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        fields1373 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1373)
            newline(pp)
            for (i1731, elem1374) in enumerate(fields1373)
                i1375 = i1731 - 1
                if (i1375 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1374)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1380 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1380)
        write(pp, flat1380)
        return nothing
    else
        fields1377 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1377)
            newline(pp)
            for (i1732, elem1378) in enumerate(fields1377)
                i1379 = i1732 - 1
                if (i1379 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1378)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1387 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1387)
        write(pp, flat1387)
        return nothing
    else
        _dollar_dollar = msg
        fields1381 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1382 = fields1381
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1383 = unwrapped_fields1382[1]
        pretty_csvlocator(pp, field1383)
        newline(pp)
        field1384 = unwrapped_fields1382[2]
        pretty_csv_config(pp, field1384)
        newline(pp)
        field1385 = unwrapped_fields1382[3]
        pretty_gnf_columns(pp, field1385)
        newline(pp)
        field1386 = unwrapped_fields1382[4]
        pretty_csv_asof(pp, field1386)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1394 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1394)
        write(pp, flat1394)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1733 = _dollar_dollar.paths
        else
            _t1733 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1734 = String(copy(_dollar_dollar.inline_data))
        else
            _t1734 = nothing
        end
        fields1388 = (_t1733, _t1734,)
        unwrapped_fields1389 = fields1388
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1390 = unwrapped_fields1389[1]
        if !isnothing(field1390)
            newline(pp)
            opt_val1391 = field1390
            pretty_csv_locator_paths(pp, opt_val1391)
        end
        field1392 = unwrapped_fields1389[2]
        if !isnothing(field1392)
            newline(pp)
            opt_val1393 = field1392
            pretty_csv_locator_inline_data(pp, opt_val1393)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1398 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1398)
        write(pp, flat1398)
        return nothing
    else
        fields1395 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1395)
            newline(pp)
            for (i1735, elem1396) in enumerate(fields1395)
                i1397 = i1735 - 1
                if (i1397 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1396))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1400 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1400)
        write(pp, flat1400)
        return nothing
    else
        fields1399 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1399))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1403 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1403)
        write(pp, flat1403)
        return nothing
    else
        _dollar_dollar = msg
        _t1736 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1401 = _t1736
        unwrapped_fields1402 = fields1401
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1402)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1407 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1407)
        write(pp, flat1407)
        return nothing
    else
        fields1404 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1404)
            newline(pp)
            for (i1737, elem1405) in enumerate(fields1404)
                i1406 = i1737 - 1
                if (i1406 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1405)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1416 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1416)
        write(pp, flat1416)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1738 = _dollar_dollar.target_id
        else
            _t1738 = nothing
        end
        fields1408 = (_dollar_dollar.column_path, _t1738, _dollar_dollar.types,)
        unwrapped_fields1409 = fields1408
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1410 = unwrapped_fields1409[1]
        pretty_gnf_column_path(pp, field1410)
        field1411 = unwrapped_fields1409[2]
        if !isnothing(field1411)
            newline(pp)
            opt_val1412 = field1411
            pretty_relation_id(pp, opt_val1412)
        end
        newline(pp)
        write(pp, "[")
        field1413 = unwrapped_fields1409[3]
        for (i1739, elem1414) in enumerate(field1413)
            i1415 = i1739 - 1
            if (i1415 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1414)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1423 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1423)
        write(pp, flat1423)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1740 = _dollar_dollar[1]
        else
            _t1740 = nothing
        end
        deconstruct_result1421 = _t1740
        if !isnothing(deconstruct_result1421)
            unwrapped1422 = deconstruct_result1421
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1422))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1741 = _dollar_dollar
            else
                _t1741 = nothing
            end
            deconstruct_result1417 = _t1741
            if !isnothing(deconstruct_result1417)
                unwrapped1418 = deconstruct_result1417
                write(pp, "[")
                indent!(pp)
                for (i1742, elem1419) in enumerate(unwrapped1418)
                    i1420 = i1742 - 1
                    if (i1420 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1419))
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
    flat1425 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1425)
        write(pp, flat1425)
        return nothing
    else
        fields1424 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1424))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1436 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1436)
        write(pp, flat1436)
        return nothing
    else
        _dollar_dollar = msg
        _t1743 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1744 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1426 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1743, _t1744, _dollar_dollar.returns_delta,)
        unwrapped_fields1427 = fields1426
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1428 = unwrapped_fields1427[1]
        pretty_iceberg_locator(pp, field1428)
        newline(pp)
        field1429 = unwrapped_fields1427[2]
        pretty_iceberg_catalog_config(pp, field1429)
        newline(pp)
        field1430 = unwrapped_fields1427[3]
        pretty_gnf_columns(pp, field1430)
        field1431 = unwrapped_fields1427[4]
        if !isnothing(field1431)
            newline(pp)
            opt_val1432 = field1431
            pretty_iceberg_from_snapshot(pp, opt_val1432)
        end
        field1433 = unwrapped_fields1427[5]
        if !isnothing(field1433)
            newline(pp)
            opt_val1434 = field1433
            pretty_iceberg_to_snapshot(pp, opt_val1434)
        end
        newline(pp)
        field1435 = unwrapped_fields1427[6]
        pretty_boolean_value(pp, field1435)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1442 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1442)
        write(pp, flat1442)
        return nothing
    else
        _dollar_dollar = msg
        fields1437 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1438 = fields1437
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1439 = unwrapped_fields1438[1]
        pretty_iceberg_locator_table_name(pp, field1439)
        newline(pp)
        field1440 = unwrapped_fields1438[2]
        pretty_iceberg_locator_namespace(pp, field1440)
        newline(pp)
        field1441 = unwrapped_fields1438[3]
        pretty_iceberg_locator_warehouse(pp, field1441)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1444 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1444)
        write(pp, flat1444)
        return nothing
    else
        fields1443 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1443))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1448 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1448)
        write(pp, flat1448)
        return nothing
    else
        fields1445 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1445)
            newline(pp)
            for (i1745, elem1446) in enumerate(fields1445)
                i1447 = i1745 - 1
                if (i1447 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1446))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1450 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1450)
        write(pp, flat1450)
        return nothing
    else
        fields1449 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1449))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1458 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1458)
        write(pp, flat1458)
        return nothing
    else
        _dollar_dollar = msg
        _t1746 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1451 = (_dollar_dollar.catalog_uri, _t1746, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1452 = fields1451
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1453 = unwrapped_fields1452[1]
        pretty_iceberg_catalog_uri(pp, field1453)
        field1454 = unwrapped_fields1452[2]
        if !isnothing(field1454)
            newline(pp)
            opt_val1455 = field1454
            pretty_iceberg_catalog_config_scope(pp, opt_val1455)
        end
        newline(pp)
        field1456 = unwrapped_fields1452[3]
        pretty_iceberg_properties(pp, field1456)
        newline(pp)
        field1457 = unwrapped_fields1452[4]
        pretty_iceberg_auth_properties(pp, field1457)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1460 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1460)
        write(pp, flat1460)
        return nothing
    else
        fields1459 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1459))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1462 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1462)
        write(pp, flat1462)
        return nothing
    else
        fields1461 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1461))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1466 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1466)
        write(pp, flat1466)
        return nothing
    else
        fields1463 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1463)
            newline(pp)
            for (i1747, elem1464) in enumerate(fields1463)
                i1465 = i1747 - 1
                if (i1465 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1464)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1471 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1471)
        write(pp, flat1471)
        return nothing
    else
        _dollar_dollar = msg
        fields1467 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1468 = fields1467
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1469 = unwrapped_fields1468[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1469))
        newline(pp)
        field1470 = unwrapped_fields1468[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1470))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1475 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1475)
        write(pp, flat1475)
        return nothing
    else
        fields1472 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1472)
            newline(pp)
            for (i1748, elem1473) in enumerate(fields1472)
                i1474 = i1748 - 1
                if (i1474 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1473)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1480 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1480)
        write(pp, flat1480)
        return nothing
    else
        _dollar_dollar = msg
        _t1749 = mask_secret_value(pp, _dollar_dollar)
        fields1476 = (_dollar_dollar[1], _t1749,)
        unwrapped_fields1477 = fields1476
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1478 = unwrapped_fields1477[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1478))
        newline(pp)
        field1479 = unwrapped_fields1477[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1479))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1482 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1482)
        write(pp, flat1482)
        return nothing
    else
        fields1481 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1481))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1484 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1484)
        write(pp, flat1484)
        return nothing
    else
        fields1483 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1483))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1487 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1487)
        write(pp, flat1487)
        return nothing
    else
        _dollar_dollar = msg
        fields1485 = _dollar_dollar.fragment_id
        unwrapped_fields1486 = fields1485
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1486)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1492 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1492)
        write(pp, flat1492)
        return nothing
    else
        _dollar_dollar = msg
        fields1488 = _dollar_dollar.relations
        unwrapped_fields1489 = fields1488
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1489)
            newline(pp)
            for (i1750, elem1490) in enumerate(unwrapped_fields1489)
                i1491 = i1750 - 1
                if (i1491 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1490)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1499 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1499)
        write(pp, flat1499)
        return nothing
    else
        _dollar_dollar = msg
        fields1493 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1494 = fields1493
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1495 = unwrapped_fields1494[1]
        pretty_edb_path(pp, field1495)
        field1496 = unwrapped_fields1494[2]
        if !isempty(field1496)
            newline(pp)
            for (i1751, elem1497) in enumerate(field1496)
                i1498 = i1751 - 1
                if (i1498 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1497)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1504 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1504)
        write(pp, flat1504)
        return nothing
    else
        _dollar_dollar = msg
        fields1500 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1501 = fields1500
        field1502 = unwrapped_fields1501[1]
        pretty_edb_path(pp, field1502)
        write(pp, " ")
        field1503 = unwrapped_fields1501[2]
        pretty_relation_id(pp, field1503)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1508 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1508)
        write(pp, flat1508)
        return nothing
    else
        fields1505 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1505)
            newline(pp)
            for (i1752, elem1506) in enumerate(fields1505)
                i1507 = i1752 - 1
                if (i1507 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1506)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1519 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1519)
        write(pp, flat1519)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1753 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1753 = nothing
        end
        deconstruct_result1517 = _t1753
        if !isnothing(deconstruct_result1517)
            unwrapped1518 = deconstruct_result1517
            pretty_demand(pp, unwrapped1518)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1754 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1754 = nothing
            end
            deconstruct_result1515 = _t1754
            if !isnothing(deconstruct_result1515)
                unwrapped1516 = deconstruct_result1515
                pretty_output(pp, unwrapped1516)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1755 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1755 = nothing
                end
                deconstruct_result1513 = _t1755
                if !isnothing(deconstruct_result1513)
                    unwrapped1514 = deconstruct_result1513
                    pretty_what_if(pp, unwrapped1514)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1756 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1756 = nothing
                    end
                    deconstruct_result1511 = _t1756
                    if !isnothing(deconstruct_result1511)
                        unwrapped1512 = deconstruct_result1511
                        pretty_abort(pp, unwrapped1512)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1757 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1757 = nothing
                        end
                        deconstruct_result1509 = _t1757
                        if !isnothing(deconstruct_result1509)
                            unwrapped1510 = deconstruct_result1509
                            pretty_export(pp, unwrapped1510)
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
    flat1522 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1522)
        write(pp, flat1522)
        return nothing
    else
        _dollar_dollar = msg
        fields1520 = _dollar_dollar.relation_id
        unwrapped_fields1521 = fields1520
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1521)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1527 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1527)
        write(pp, flat1527)
        return nothing
    else
        _dollar_dollar = msg
        fields1523 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1524 = fields1523
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1525 = unwrapped_fields1524[1]
        pretty_name(pp, field1525)
        newline(pp)
        field1526 = unwrapped_fields1524[2]
        pretty_relation_id(pp, field1526)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1532 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1532)
        write(pp, flat1532)
        return nothing
    else
        _dollar_dollar = msg
        fields1528 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1529 = fields1528
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1530 = unwrapped_fields1529[1]
        pretty_name(pp, field1530)
        newline(pp)
        field1531 = unwrapped_fields1529[2]
        pretty_epoch(pp, field1531)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1538 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1538)
        write(pp, flat1538)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1758 = _dollar_dollar.name
        else
            _t1758 = nothing
        end
        fields1533 = (_t1758, _dollar_dollar.relation_id,)
        unwrapped_fields1534 = fields1533
        write(pp, "(abort")
        indent_sexp!(pp)
        field1535 = unwrapped_fields1534[1]
        if !isnothing(field1535)
            newline(pp)
            opt_val1536 = field1535
            pretty_name(pp, opt_val1536)
        end
        newline(pp)
        field1537 = unwrapped_fields1534[2]
        pretty_relation_id(pp, field1537)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1543 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1543)
        write(pp, flat1543)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1759 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1759 = nothing
        end
        deconstruct_result1541 = _t1759
        if !isnothing(deconstruct_result1541)
            unwrapped1542 = deconstruct_result1541
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1542)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1760 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1760 = nothing
            end
            deconstruct_result1539 = _t1760
            if !isnothing(deconstruct_result1539)
                unwrapped1540 = deconstruct_result1539
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1540)
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
    flat1554 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1554)
        write(pp, flat1554)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1761 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1761 = nothing
        end
        deconstruct_result1549 = _t1761
        if !isnothing(deconstruct_result1549)
            unwrapped1550 = deconstruct_result1549
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1551 = unwrapped1550[1]
            pretty_export_csv_path(pp, field1551)
            newline(pp)
            field1552 = unwrapped1550[2]
            pretty_export_csv_source(pp, field1552)
            newline(pp)
            field1553 = unwrapped1550[3]
            pretty_csv_config(pp, field1553)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1763 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1762 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1763,)
            else
                _t1762 = nothing
            end
            deconstruct_result1544 = _t1762
            if !isnothing(deconstruct_result1544)
                unwrapped1545 = deconstruct_result1544
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1546 = unwrapped1545[1]
                pretty_export_csv_path(pp, field1546)
                newline(pp)
                field1547 = unwrapped1545[2]
                pretty_export_csv_columns_list(pp, field1547)
                newline(pp)
                field1548 = unwrapped1545[3]
                pretty_config_dict(pp, field1548)
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
    flat1556 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1556)
        write(pp, flat1556)
        return nothing
    else
        fields1555 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1555))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1563 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1563)
        write(pp, flat1563)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1764 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1764 = nothing
        end
        deconstruct_result1559 = _t1764
        if !isnothing(deconstruct_result1559)
            unwrapped1560 = deconstruct_result1559
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1560)
                newline(pp)
                for (i1765, elem1561) in enumerate(unwrapped1560)
                    i1562 = i1765 - 1
                    if (i1562 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1561)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1766 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1766 = nothing
            end
            deconstruct_result1557 = _t1766
            if !isnothing(deconstruct_result1557)
                unwrapped1558 = deconstruct_result1557
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1558)
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
    flat1568 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1568)
        write(pp, flat1568)
        return nothing
    else
        _dollar_dollar = msg
        fields1564 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1565 = fields1564
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1566 = unwrapped_fields1565[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1566))
        newline(pp)
        field1567 = unwrapped_fields1565[2]
        pretty_relation_id(pp, field1567)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1572 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1572)
        write(pp, flat1572)
        return nothing
    else
        fields1569 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1569)
            newline(pp)
            for (i1767, elem1570) in enumerate(fields1569)
                i1571 = i1767 - 1
                if (i1571 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1570)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1581 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1581)
        write(pp, flat1581)
        return nothing
    else
        _dollar_dollar = msg
        _t1768 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1573 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1768,)
        unwrapped_fields1574 = fields1573
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1575 = unwrapped_fields1574[1]
        pretty_iceberg_locator(pp, field1575)
        newline(pp)
        field1576 = unwrapped_fields1574[2]
        pretty_iceberg_catalog_config(pp, field1576)
        newline(pp)
        field1577 = unwrapped_fields1574[3]
        pretty_export_iceberg_table_def(pp, field1577)
        newline(pp)
        field1578 = unwrapped_fields1574[4]
        pretty_iceberg_table_properties(pp, field1578)
        field1579 = unwrapped_fields1574[5]
        if !isnothing(field1579)
            newline(pp)
            opt_val1580 = field1579
            pretty_config_dict(pp, opt_val1580)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1583 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1583)
        write(pp, flat1583)
        return nothing
    else
        fields1582 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1582)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1587 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1587)
        write(pp, flat1587)
        return nothing
    else
        fields1584 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1584)
            newline(pp)
            for (i1769, elem1585) in enumerate(fields1584)
                i1586 = i1769 - 1
                if (i1586 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1585)
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
    for (i1815, _rid) in enumerate(msg.ids)
        _idx = i1815 - 1
        newline(pp)
        write(pp, "(")
        _t1816 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1816)
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
    for (i1817, _elem) in enumerate(msg.keys)
        _idx = i1817 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1818, _elem) in enumerate(msg.values)
        _idx = i1818 - 1
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
    for (i1819, _elem) in enumerate(msg.columns)
        _idx = i1819 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Tuple{String, String}}) = pretty_iceberg_properties(pp, x)
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
