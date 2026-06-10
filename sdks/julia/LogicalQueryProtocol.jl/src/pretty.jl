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
    _t1781 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1781
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1782 = Proto.Value(value=OneOf(:int_value, v))
    return _t1782
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1783 = Proto.Value(value=OneOf(:float_value, v))
    return _t1783
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1784 = Proto.Value(value=OneOf(:string_value, v))
    return _t1784
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1785 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1785
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1786 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1786
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1787 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1787,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1788 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1788,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1789 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1789,))
            end
        end
    end
    _t1790 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1790,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1791 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1791,))
    _t1792 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1792,))
    if msg.new_line != ""
        _t1793 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1793,))
    end
    _t1794 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1794,))
    _t1795 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1795,))
    _t1796 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1796,))
    if msg.comment != ""
        _t1797 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1797,))
    end
    for missing_string in msg.missing_strings
        _t1798 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1798,))
    end
    _t1799 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1799,))
    _t1800 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1800,))
    _t1801 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1801,))
    if msg.partition_size_mb != 0
        _t1802 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1802,))
    end
    return sort(result)
end

function deconstruct_csv_storage_integration_optional(pp::PrettyPrinter, msg::Proto.CSVConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    if !_has_proto_field(msg, Symbol("storage_integration"))
        return nothing
    else
        _t1803 = nothing
    end
    si = msg.storage_integration
    result = Tuple{String, Proto.Value}[]
    if si.provider != ""
        _t1804 = _make_value_string(pp, si.provider)
        push!(result, ("provider", _t1804,))
    end
    if si.azure_sas_token != ""
        _t1805 = _make_value_string(pp, "***")
        push!(result, ("azure_sas_token", _t1805,))
    end
    if si.s3_region != ""
        _t1806 = _make_value_string(pp, si.s3_region)
        push!(result, ("s3_region", _t1806,))
    end
    if si.s3_access_key_id != ""
        _t1807 = _make_value_string(pp, "***")
        push!(result, ("s3_access_key_id", _t1807,))
    end
    if si.s3_secret_access_key != ""
        _t1808 = _make_value_string(pp, "***")
        push!(result, ("s3_secret_access_key", _t1808,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1809 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1809,))
    _t1810 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1810,))
    _t1811 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1811,))
    _t1812 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1812,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1813 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1813,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1814 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1814,))
        end
    end
    _t1815 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1815,))
    _t1816 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1816,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1817 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1817,))
    end
    if !isnothing(msg.compression)
        _t1818 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1818,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1819 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1819,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1820 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1820,))
    end
    if !isnothing(msg.syntax_delim)
        _t1821 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1821,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1822 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1822,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1823 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1823,))
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
        _t1824 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1825 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1826 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1827 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1827,))
    end
    if msg.target_file_size_bytes != 0
        _t1828 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1828,))
    end
    if msg.compression != ""
        _t1829 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1829,))
    end
    if length(result) == 0
        return nothing
    else
        _t1830 = nothing
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
        _t1831 = nothing
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
    flat808 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat808)
        write(pp, flat808)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1598 = _dollar_dollar.configure
        else
            _t1598 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1599 = _dollar_dollar.sync
        else
            _t1599 = nothing
        end
        fields799 = (_t1598, _t1599, _dollar_dollar.epochs,)
        unwrapped_fields800 = fields799
        write(pp, "(transaction")
        indent_sexp!(pp)
        field801 = unwrapped_fields800[1]
        if !isnothing(field801)
            newline(pp)
            opt_val802 = field801
            pretty_configure(pp, opt_val802)
        end
        field803 = unwrapped_fields800[2]
        if !isnothing(field803)
            newline(pp)
            opt_val804 = field803
            pretty_sync(pp, opt_val804)
        end
        field805 = unwrapped_fields800[3]
        if !isempty(field805)
            newline(pp)
            for (i1600, elem806) in enumerate(field805)
                i807 = i1600 - 1
                if (i807 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem806)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat811 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat811)
        write(pp, flat811)
        return nothing
    else
        _dollar_dollar = msg
        _t1601 = deconstruct_configure(pp, _dollar_dollar)
        fields809 = _t1601
        unwrapped_fields810 = fields809
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields810)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat815 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat815)
        write(pp, flat815)
        return nothing
    else
        fields812 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields812)
            newline(pp)
            for (i1602, elem813) in enumerate(fields812)
                i814 = i1602 - 1
                if (i814 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem813)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat820 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat820)
        write(pp, flat820)
        return nothing
    else
        _dollar_dollar = msg
        fields816 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields817 = fields816
        write(pp, ":")
        field818 = unwrapped_fields817[1]
        write(pp, field818)
        write(pp, " ")
        field819 = unwrapped_fields817[2]
        pretty_raw_value(pp, field819)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat846 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat846)
        write(pp, flat846)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1603 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1603 = nothing
        end
        deconstruct_result844 = _t1603
        if !isnothing(deconstruct_result844)
            unwrapped845 = deconstruct_result844
            pretty_raw_date(pp, unwrapped845)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1604 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1604 = nothing
            end
            deconstruct_result842 = _t1604
            if !isnothing(deconstruct_result842)
                unwrapped843 = deconstruct_result842
                pretty_raw_datetime(pp, unwrapped843)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1605 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1605 = nothing
                end
                deconstruct_result840 = _t1605
                if !isnothing(deconstruct_result840)
                    unwrapped841 = deconstruct_result840
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped841))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1606 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1606 = nothing
                    end
                    deconstruct_result838 = _t1606
                    if !isnothing(deconstruct_result838)
                        unwrapped839 = deconstruct_result838
                        write(pp, (string(Int64(unwrapped839)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1607 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1607 = nothing
                        end
                        deconstruct_result836 = _t1607
                        if !isnothing(deconstruct_result836)
                            unwrapped837 = deconstruct_result836
                            write(pp, string(unwrapped837))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1608 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1608 = nothing
                            end
                            deconstruct_result834 = _t1608
                            if !isnothing(deconstruct_result834)
                                unwrapped835 = deconstruct_result834
                                write(pp, format_float32_literal(unwrapped835))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1609 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1609 = nothing
                                end
                                deconstruct_result832 = _t1609
                                if !isnothing(deconstruct_result832)
                                    unwrapped833 = deconstruct_result832
                                    write(pp, lowercase(string(unwrapped833)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1610 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1610 = nothing
                                    end
                                    deconstruct_result830 = _t1610
                                    if !isnothing(deconstruct_result830)
                                        unwrapped831 = deconstruct_result830
                                        write(pp, (string(Int64(unwrapped831)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1611 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1611 = nothing
                                        end
                                        deconstruct_result828 = _t1611
                                        if !isnothing(deconstruct_result828)
                                            unwrapped829 = deconstruct_result828
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped829))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1612 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1612 = nothing
                                            end
                                            deconstruct_result826 = _t1612
                                            if !isnothing(deconstruct_result826)
                                                unwrapped827 = deconstruct_result826
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped827))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1613 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1613 = nothing
                                                end
                                                deconstruct_result824 = _t1613
                                                if !isnothing(deconstruct_result824)
                                                    unwrapped825 = deconstruct_result824
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped825))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1614 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1614 = nothing
                                                    end
                                                    deconstruct_result822 = _t1614
                                                    if !isnothing(deconstruct_result822)
                                                        unwrapped823 = deconstruct_result822
                                                        pretty_boolean_value(pp, unwrapped823)
                                                    else
                                                        fields821 = msg
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
    flat852 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat852)
        write(pp, flat852)
        return nothing
    else
        _dollar_dollar = msg
        fields847 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields848 = fields847
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field849 = unwrapped_fields848[1]
        write(pp, string(field849))
        newline(pp)
        field850 = unwrapped_fields848[2]
        write(pp, string(field850))
        newline(pp)
        field851 = unwrapped_fields848[3]
        write(pp, string(field851))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat863 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat863)
        write(pp, flat863)
        return nothing
    else
        _dollar_dollar = msg
        fields853 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields854 = fields853
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field855 = unwrapped_fields854[1]
        write(pp, string(field855))
        newline(pp)
        field856 = unwrapped_fields854[2]
        write(pp, string(field856))
        newline(pp)
        field857 = unwrapped_fields854[3]
        write(pp, string(field857))
        newline(pp)
        field858 = unwrapped_fields854[4]
        write(pp, string(field858))
        newline(pp)
        field859 = unwrapped_fields854[5]
        write(pp, string(field859))
        newline(pp)
        field860 = unwrapped_fields854[6]
        write(pp, string(field860))
        field861 = unwrapped_fields854[7]
        if !isnothing(field861)
            newline(pp)
            opt_val862 = field861
            write(pp, string(opt_val862))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1615 = ()
    else
        _t1615 = nothing
    end
    deconstruct_result866 = _t1615
    if !isnothing(deconstruct_result866)
        unwrapped867 = deconstruct_result866
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1616 = ()
        else
            _t1616 = nothing
        end
        deconstruct_result864 = _t1616
        if !isnothing(deconstruct_result864)
            unwrapped865 = deconstruct_result864
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat872 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat872)
        write(pp, flat872)
        return nothing
    else
        _dollar_dollar = msg
        fields868 = _dollar_dollar.fragments
        unwrapped_fields869 = fields868
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields869)
            newline(pp)
            for (i1617, elem870) in enumerate(unwrapped_fields869)
                i871 = i1617 - 1
                if (i871 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem870)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat875 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat875)
        write(pp, flat875)
        return nothing
    else
        _dollar_dollar = msg
        fields873 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields874 = fields873
        write(pp, ":")
        write(pp, unwrapped_fields874)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat882 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat882)
        write(pp, flat882)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1618 = _dollar_dollar.writes
        else
            _t1618 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1619 = _dollar_dollar.reads
        else
            _t1619 = nothing
        end
        fields876 = (_t1618, _t1619,)
        unwrapped_fields877 = fields876
        write(pp, "(epoch")
        indent_sexp!(pp)
        field878 = unwrapped_fields877[1]
        if !isnothing(field878)
            newline(pp)
            opt_val879 = field878
            pretty_epoch_writes(pp, opt_val879)
        end
        field880 = unwrapped_fields877[2]
        if !isnothing(field880)
            newline(pp)
            opt_val881 = field880
            pretty_epoch_reads(pp, opt_val881)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat886 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat886)
        write(pp, flat886)
        return nothing
    else
        fields883 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields883)
            newline(pp)
            for (i1620, elem884) in enumerate(fields883)
                i885 = i1620 - 1
                if (i885 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem884)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat895 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat895)
        write(pp, flat895)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1621 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1621 = nothing
        end
        deconstruct_result893 = _t1621
        if !isnothing(deconstruct_result893)
            unwrapped894 = deconstruct_result893
            pretty_define(pp, unwrapped894)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1622 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1622 = nothing
            end
            deconstruct_result891 = _t1622
            if !isnothing(deconstruct_result891)
                unwrapped892 = deconstruct_result891
                pretty_undefine(pp, unwrapped892)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1623 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1623 = nothing
                end
                deconstruct_result889 = _t1623
                if !isnothing(deconstruct_result889)
                    unwrapped890 = deconstruct_result889
                    pretty_context(pp, unwrapped890)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1624 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1624 = nothing
                    end
                    deconstruct_result887 = _t1624
                    if !isnothing(deconstruct_result887)
                        unwrapped888 = deconstruct_result887
                        pretty_snapshot(pp, unwrapped888)
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
    flat898 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat898)
        write(pp, flat898)
        return nothing
    else
        _dollar_dollar = msg
        fields896 = _dollar_dollar.fragment
        unwrapped_fields897 = fields896
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields897)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat905 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat905)
        write(pp, flat905)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields899 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields900 = fields899
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field901 = unwrapped_fields900[1]
        pretty_new_fragment_id(pp, field901)
        field902 = unwrapped_fields900[2]
        if !isempty(field902)
            newline(pp)
            for (i1625, elem903) in enumerate(field902)
                i904 = i1625 - 1
                if (i904 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem903)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat907 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat907)
        write(pp, flat907)
        return nothing
    else
        fields906 = msg
        pretty_fragment_id(pp, fields906)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat916 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat916)
        write(pp, flat916)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1626 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1626 = nothing
        end
        deconstruct_result914 = _t1626
        if !isnothing(deconstruct_result914)
            unwrapped915 = deconstruct_result914
            pretty_def(pp, unwrapped915)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1627 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1627 = nothing
            end
            deconstruct_result912 = _t1627
            if !isnothing(deconstruct_result912)
                unwrapped913 = deconstruct_result912
                pretty_algorithm(pp, unwrapped913)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1628 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1628 = nothing
                end
                deconstruct_result910 = _t1628
                if !isnothing(deconstruct_result910)
                    unwrapped911 = deconstruct_result910
                    pretty_constraint(pp, unwrapped911)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1629 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1629 = nothing
                    end
                    deconstruct_result908 = _t1629
                    if !isnothing(deconstruct_result908)
                        unwrapped909 = deconstruct_result908
                        pretty_data(pp, unwrapped909)
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
    flat923 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat923)
        write(pp, flat923)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1630 = _dollar_dollar.attrs
        else
            _t1630 = nothing
        end
        fields917 = (_dollar_dollar.name, _dollar_dollar.body, _t1630,)
        unwrapped_fields918 = fields917
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field919 = unwrapped_fields918[1]
        pretty_relation_id(pp, field919)
        newline(pp)
        field920 = unwrapped_fields918[2]
        pretty_abstraction(pp, field920)
        field921 = unwrapped_fields918[3]
        if !isnothing(field921)
            newline(pp)
            opt_val922 = field921
            pretty_attrs(pp, opt_val922)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat928 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat928)
        write(pp, flat928)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1632 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1631 = _t1632
        else
            _t1631 = nothing
        end
        deconstruct_result926 = _t1631
        if !isnothing(deconstruct_result926)
            unwrapped927 = deconstruct_result926
            write(pp, ":")
            write(pp, unwrapped927)
        else
            _dollar_dollar = msg
            _t1633 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result924 = _t1633
            if !isnothing(deconstruct_result924)
                unwrapped925 = deconstruct_result924
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped925))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat933 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat933)
        write(pp, flat933)
        return nothing
    else
        _dollar_dollar = msg
        _t1634 = deconstruct_bindings(pp, _dollar_dollar)
        fields929 = (_t1634, _dollar_dollar.value,)
        unwrapped_fields930 = fields929
        write(pp, "(")
        indent!(pp)
        field931 = unwrapped_fields930[1]
        pretty_bindings(pp, field931)
        newline(pp)
        field932 = unwrapped_fields930[2]
        pretty_formula(pp, field932)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat941 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat941)
        write(pp, flat941)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1635 = _dollar_dollar[2]
        else
            _t1635 = nothing
        end
        fields934 = (_dollar_dollar[1], _t1635,)
        unwrapped_fields935 = fields934
        write(pp, "[")
        indent!(pp)
        field936 = unwrapped_fields935[1]
        for (i1636, elem937) in enumerate(field936)
            i938 = i1636 - 1
            if (i938 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem937)
        end
        field939 = unwrapped_fields935[2]
        if !isnothing(field939)
            newline(pp)
            opt_val940 = field939
            pretty_value_bindings(pp, opt_val940)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat946 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        _dollar_dollar = msg
        fields942 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields943 = fields942
        field944 = unwrapped_fields943[1]
        write(pp, field944)
        write(pp, "::")
        field945 = unwrapped_fields943[2]
        pretty_type(pp, field945)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat975 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat975)
        write(pp, flat975)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1637 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1637 = nothing
        end
        deconstruct_result973 = _t1637
        if !isnothing(deconstruct_result973)
            unwrapped974 = deconstruct_result973
            pretty_unspecified_type(pp, unwrapped974)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1638 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1638 = nothing
            end
            deconstruct_result971 = _t1638
            if !isnothing(deconstruct_result971)
                unwrapped972 = deconstruct_result971
                pretty_string_type(pp, unwrapped972)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1639 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1639 = nothing
                end
                deconstruct_result969 = _t1639
                if !isnothing(deconstruct_result969)
                    unwrapped970 = deconstruct_result969
                    pretty_int_type(pp, unwrapped970)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1640 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1640 = nothing
                    end
                    deconstruct_result967 = _t1640
                    if !isnothing(deconstruct_result967)
                        unwrapped968 = deconstruct_result967
                        pretty_float_type(pp, unwrapped968)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1641 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1641 = nothing
                        end
                        deconstruct_result965 = _t1641
                        if !isnothing(deconstruct_result965)
                            unwrapped966 = deconstruct_result965
                            pretty_uint128_type(pp, unwrapped966)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1642 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1642 = nothing
                            end
                            deconstruct_result963 = _t1642
                            if !isnothing(deconstruct_result963)
                                unwrapped964 = deconstruct_result963
                                pretty_int128_type(pp, unwrapped964)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1643 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1643 = nothing
                                end
                                deconstruct_result961 = _t1643
                                if !isnothing(deconstruct_result961)
                                    unwrapped962 = deconstruct_result961
                                    pretty_date_type(pp, unwrapped962)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1644 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1644 = nothing
                                    end
                                    deconstruct_result959 = _t1644
                                    if !isnothing(deconstruct_result959)
                                        unwrapped960 = deconstruct_result959
                                        pretty_datetime_type(pp, unwrapped960)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1645 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1645 = nothing
                                        end
                                        deconstruct_result957 = _t1645
                                        if !isnothing(deconstruct_result957)
                                            unwrapped958 = deconstruct_result957
                                            pretty_missing_type(pp, unwrapped958)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1646 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1646 = nothing
                                            end
                                            deconstruct_result955 = _t1646
                                            if !isnothing(deconstruct_result955)
                                                unwrapped956 = deconstruct_result955
                                                pretty_decimal_type(pp, unwrapped956)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1647 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1647 = nothing
                                                end
                                                deconstruct_result953 = _t1647
                                                if !isnothing(deconstruct_result953)
                                                    unwrapped954 = deconstruct_result953
                                                    pretty_boolean_type(pp, unwrapped954)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1648 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1648 = nothing
                                                    end
                                                    deconstruct_result951 = _t1648
                                                    if !isnothing(deconstruct_result951)
                                                        unwrapped952 = deconstruct_result951
                                                        pretty_int32_type(pp, unwrapped952)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1649 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1649 = nothing
                                                        end
                                                        deconstruct_result949 = _t1649
                                                        if !isnothing(deconstruct_result949)
                                                            unwrapped950 = deconstruct_result949
                                                            pretty_float32_type(pp, unwrapped950)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1650 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1650 = nothing
                                                            end
                                                            deconstruct_result947 = _t1650
                                                            if !isnothing(deconstruct_result947)
                                                                unwrapped948 = deconstruct_result947
                                                                pretty_uint32_type(pp, unwrapped948)
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
    fields976 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields977 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields978 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields979 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields980 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields981 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields982 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields983 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields984 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat989 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat989)
        write(pp, flat989)
        return nothing
    else
        _dollar_dollar = msg
        fields985 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields986 = fields985
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field987 = unwrapped_fields986[1]
        write(pp, string(field987))
        newline(pp)
        field988 = unwrapped_fields986[2]
        write(pp, string(field988))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields990 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields991 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields992 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields993 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat997 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat997)
        write(pp, flat997)
        return nothing
    else
        fields994 = msg
        write(pp, "|")
        if !isempty(fields994)
            write(pp, " ")
            for (i1651, elem995) in enumerate(fields994)
                i996 = i1651 - 1
                if (i996 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem995)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1024 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1024)
        write(pp, flat1024)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1652 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1652 = nothing
        end
        deconstruct_result1022 = _t1652
        if !isnothing(deconstruct_result1022)
            unwrapped1023 = deconstruct_result1022
            pretty_true(pp, unwrapped1023)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1653 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1653 = nothing
            end
            deconstruct_result1020 = _t1653
            if !isnothing(deconstruct_result1020)
                unwrapped1021 = deconstruct_result1020
                pretty_false(pp, unwrapped1021)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1654 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1654 = nothing
                end
                deconstruct_result1018 = _t1654
                if !isnothing(deconstruct_result1018)
                    unwrapped1019 = deconstruct_result1018
                    pretty_exists(pp, unwrapped1019)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1655 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1655 = nothing
                    end
                    deconstruct_result1016 = _t1655
                    if !isnothing(deconstruct_result1016)
                        unwrapped1017 = deconstruct_result1016
                        pretty_reduce(pp, unwrapped1017)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1656 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1656 = nothing
                        end
                        deconstruct_result1014 = _t1656
                        if !isnothing(deconstruct_result1014)
                            unwrapped1015 = deconstruct_result1014
                            pretty_conjunction(pp, unwrapped1015)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1657 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1657 = nothing
                            end
                            deconstruct_result1012 = _t1657
                            if !isnothing(deconstruct_result1012)
                                unwrapped1013 = deconstruct_result1012
                                pretty_disjunction(pp, unwrapped1013)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1658 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1658 = nothing
                                end
                                deconstruct_result1010 = _t1658
                                if !isnothing(deconstruct_result1010)
                                    unwrapped1011 = deconstruct_result1010
                                    pretty_not(pp, unwrapped1011)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1659 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1659 = nothing
                                    end
                                    deconstruct_result1008 = _t1659
                                    if !isnothing(deconstruct_result1008)
                                        unwrapped1009 = deconstruct_result1008
                                        pretty_ffi(pp, unwrapped1009)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1660 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1660 = nothing
                                        end
                                        deconstruct_result1006 = _t1660
                                        if !isnothing(deconstruct_result1006)
                                            unwrapped1007 = deconstruct_result1006
                                            pretty_atom(pp, unwrapped1007)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1661 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1661 = nothing
                                            end
                                            deconstruct_result1004 = _t1661
                                            if !isnothing(deconstruct_result1004)
                                                unwrapped1005 = deconstruct_result1004
                                                pretty_pragma(pp, unwrapped1005)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1662 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1662 = nothing
                                                end
                                                deconstruct_result1002 = _t1662
                                                if !isnothing(deconstruct_result1002)
                                                    unwrapped1003 = deconstruct_result1002
                                                    pretty_primitive(pp, unwrapped1003)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1663 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1663 = nothing
                                                    end
                                                    deconstruct_result1000 = _t1663
                                                    if !isnothing(deconstruct_result1000)
                                                        unwrapped1001 = deconstruct_result1000
                                                        pretty_rel_atom(pp, unwrapped1001)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1664 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1664 = nothing
                                                        end
                                                        deconstruct_result998 = _t1664
                                                        if !isnothing(deconstruct_result998)
                                                            unwrapped999 = deconstruct_result998
                                                            pretty_cast(pp, unwrapped999)
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
    fields1025 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1026 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1031 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1031)
        write(pp, flat1031)
        return nothing
    else
        _dollar_dollar = msg
        _t1665 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1027 = (_t1665, _dollar_dollar.body.value,)
        unwrapped_fields1028 = fields1027
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1029 = unwrapped_fields1028[1]
        pretty_bindings(pp, field1029)
        newline(pp)
        field1030 = unwrapped_fields1028[2]
        pretty_formula(pp, field1030)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1037 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1037)
        write(pp, flat1037)
        return nothing
    else
        _dollar_dollar = msg
        fields1032 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1033 = fields1032
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1034 = unwrapped_fields1033[1]
        pretty_abstraction(pp, field1034)
        newline(pp)
        field1035 = unwrapped_fields1033[2]
        pretty_abstraction(pp, field1035)
        newline(pp)
        field1036 = unwrapped_fields1033[3]
        pretty_terms(pp, field1036)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1041 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1041)
        write(pp, flat1041)
        return nothing
    else
        fields1038 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1038)
            newline(pp)
            for (i1666, elem1039) in enumerate(fields1038)
                i1040 = i1666 - 1
                if (i1040 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1039)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1046 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1046)
        write(pp, flat1046)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1667 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1667 = nothing
        end
        deconstruct_result1044 = _t1667
        if !isnothing(deconstruct_result1044)
            unwrapped1045 = deconstruct_result1044
            pretty_var(pp, unwrapped1045)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1668 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1668 = nothing
            end
            deconstruct_result1042 = _t1668
            if !isnothing(deconstruct_result1042)
                unwrapped1043 = deconstruct_result1042
                pretty_value(pp, unwrapped1043)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1049 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1049)
        write(pp, flat1049)
        return nothing
    else
        _dollar_dollar = msg
        fields1047 = _dollar_dollar.name
        unwrapped_fields1048 = fields1047
        write(pp, unwrapped_fields1048)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1075 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1075)
        write(pp, flat1075)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1669 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1669 = nothing
        end
        deconstruct_result1073 = _t1669
        if !isnothing(deconstruct_result1073)
            unwrapped1074 = deconstruct_result1073
            pretty_date(pp, unwrapped1074)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1670 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1670 = nothing
            end
            deconstruct_result1071 = _t1670
            if !isnothing(deconstruct_result1071)
                unwrapped1072 = deconstruct_result1071
                pretty_datetime(pp, unwrapped1072)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1671 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1671 = nothing
                end
                deconstruct_result1069 = _t1671
                if !isnothing(deconstruct_result1069)
                    unwrapped1070 = deconstruct_result1069
                    write(pp, format_string(pp, unwrapped1070))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1672 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1672 = nothing
                    end
                    deconstruct_result1067 = _t1672
                    if !isnothing(deconstruct_result1067)
                        unwrapped1068 = deconstruct_result1067
                        write(pp, format_int32(pp, unwrapped1068))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1673 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1673 = nothing
                        end
                        deconstruct_result1065 = _t1673
                        if !isnothing(deconstruct_result1065)
                            unwrapped1066 = deconstruct_result1065
                            write(pp, format_int(pp, unwrapped1066))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1674 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1674 = nothing
                            end
                            deconstruct_result1063 = _t1674
                            if !isnothing(deconstruct_result1063)
                                unwrapped1064 = deconstruct_result1063
                                write(pp, format_float32(pp, unwrapped1064))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1675 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1675 = nothing
                                end
                                deconstruct_result1061 = _t1675
                                if !isnothing(deconstruct_result1061)
                                    unwrapped1062 = deconstruct_result1061
                                    write(pp, format_float(pp, unwrapped1062))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1676 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1676 = nothing
                                    end
                                    deconstruct_result1059 = _t1676
                                    if !isnothing(deconstruct_result1059)
                                        unwrapped1060 = deconstruct_result1059
                                        write(pp, format_uint32(pp, unwrapped1060))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1677 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1677 = nothing
                                        end
                                        deconstruct_result1057 = _t1677
                                        if !isnothing(deconstruct_result1057)
                                            unwrapped1058 = deconstruct_result1057
                                            write(pp, format_uint128(pp, unwrapped1058))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1678 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1678 = nothing
                                            end
                                            deconstruct_result1055 = _t1678
                                            if !isnothing(deconstruct_result1055)
                                                unwrapped1056 = deconstruct_result1055
                                                write(pp, format_int128(pp, unwrapped1056))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1679 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1679 = nothing
                                                end
                                                deconstruct_result1053 = _t1679
                                                if !isnothing(deconstruct_result1053)
                                                    unwrapped1054 = deconstruct_result1053
                                                    write(pp, format_decimal(pp, unwrapped1054))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1680 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1680 = nothing
                                                    end
                                                    deconstruct_result1051 = _t1680
                                                    if !isnothing(deconstruct_result1051)
                                                        unwrapped1052 = deconstruct_result1051
                                                        pretty_boolean_value(pp, unwrapped1052)
                                                    else
                                                        fields1050 = msg
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
    flat1081 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1081)
        write(pp, flat1081)
        return nothing
    else
        _dollar_dollar = msg
        fields1076 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1077 = fields1076
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1078 = unwrapped_fields1077[1]
        write(pp, format_int(pp, field1078))
        newline(pp)
        field1079 = unwrapped_fields1077[2]
        write(pp, format_int(pp, field1079))
        newline(pp)
        field1080 = unwrapped_fields1077[3]
        write(pp, format_int(pp, field1080))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1092 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        _dollar_dollar = msg
        fields1082 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1083 = fields1082
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1084 = unwrapped_fields1083[1]
        write(pp, format_int(pp, field1084))
        newline(pp)
        field1085 = unwrapped_fields1083[2]
        write(pp, format_int(pp, field1085))
        newline(pp)
        field1086 = unwrapped_fields1083[3]
        write(pp, format_int(pp, field1086))
        newline(pp)
        field1087 = unwrapped_fields1083[4]
        write(pp, format_int(pp, field1087))
        newline(pp)
        field1088 = unwrapped_fields1083[5]
        write(pp, format_int(pp, field1088))
        newline(pp)
        field1089 = unwrapped_fields1083[6]
        write(pp, format_int(pp, field1089))
        field1090 = unwrapped_fields1083[7]
        if !isnothing(field1090)
            newline(pp)
            opt_val1091 = field1090
            write(pp, format_int(pp, opt_val1091))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1097 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1097)
        write(pp, flat1097)
        return nothing
    else
        _dollar_dollar = msg
        fields1093 = _dollar_dollar.args
        unwrapped_fields1094 = fields1093
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1094)
            newline(pp)
            for (i1681, elem1095) in enumerate(unwrapped_fields1094)
                i1096 = i1681 - 1
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

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1102 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1102)
        write(pp, flat1102)
        return nothing
    else
        _dollar_dollar = msg
        fields1098 = _dollar_dollar.args
        unwrapped_fields1099 = fields1098
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1099)
            newline(pp)
            for (i1682, elem1100) in enumerate(unwrapped_fields1099)
                i1101 = i1682 - 1
                if (i1101 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1100)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1105 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1105)
        write(pp, flat1105)
        return nothing
    else
        _dollar_dollar = msg
        fields1103 = _dollar_dollar.arg
        unwrapped_fields1104 = fields1103
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1104)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1111 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1111)
        write(pp, flat1111)
        return nothing
    else
        _dollar_dollar = msg
        fields1106 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1107 = fields1106
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1108 = unwrapped_fields1107[1]
        pretty_name(pp, field1108)
        newline(pp)
        field1109 = unwrapped_fields1107[2]
        pretty_ffi_args(pp, field1109)
        newline(pp)
        field1110 = unwrapped_fields1107[3]
        pretty_terms(pp, field1110)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1113 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1113)
        write(pp, flat1113)
        return nothing
    else
        fields1112 = msg
        write(pp, ":")
        write(pp, fields1112)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1117 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1117)
        write(pp, flat1117)
        return nothing
    else
        fields1114 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1114)
            newline(pp)
            for (i1683, elem1115) in enumerate(fields1114)
                i1116 = i1683 - 1
                if (i1116 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1115)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1124 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1124)
        write(pp, flat1124)
        return nothing
    else
        _dollar_dollar = msg
        fields1118 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1119 = fields1118
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1120 = unwrapped_fields1119[1]
        pretty_relation_id(pp, field1120)
        field1121 = unwrapped_fields1119[2]
        if !isempty(field1121)
            newline(pp)
            for (i1684, elem1122) in enumerate(field1121)
                i1123 = i1684 - 1
                if (i1123 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1122)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1131 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1131)
        write(pp, flat1131)
        return nothing
    else
        _dollar_dollar = msg
        fields1125 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1126 = fields1125
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1127 = unwrapped_fields1126[1]
        pretty_name(pp, field1127)
        field1128 = unwrapped_fields1126[2]
        if !isempty(field1128)
            newline(pp)
            for (i1685, elem1129) in enumerate(field1128)
                i1130 = i1685 - 1
                if (i1130 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1129)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1147 = try_flat(pp, msg, pretty_primitive)
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
        guard_result1146 = _t1686
        if !isnothing(guard_result1146)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1687 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1687 = nothing
            end
            guard_result1145 = _t1687
            if !isnothing(guard_result1145)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1688 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1688 = nothing
                end
                guard_result1144 = _t1688
                if !isnothing(guard_result1144)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1689 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1689 = nothing
                    end
                    guard_result1143 = _t1689
                    if !isnothing(guard_result1143)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1690 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1690 = nothing
                        end
                        guard_result1142 = _t1690
                        if !isnothing(guard_result1142)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1691 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1691 = nothing
                            end
                            guard_result1141 = _t1691
                            if !isnothing(guard_result1141)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1692 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1692 = nothing
                                end
                                guard_result1140 = _t1692
                                if !isnothing(guard_result1140)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1693 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1693 = nothing
                                    end
                                    guard_result1139 = _t1693
                                    if !isnothing(guard_result1139)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1694 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1694 = nothing
                                        end
                                        guard_result1138 = _t1694
                                        if !isnothing(guard_result1138)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1132 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1133 = fields1132
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1134 = unwrapped_fields1133[1]
                                            pretty_name(pp, field1134)
                                            field1135 = unwrapped_fields1133[2]
                                            if !isempty(field1135)
                                                newline(pp)
                                                for (i1695, elem1136) in enumerate(field1135)
                                                    i1137 = i1695 - 1
                                                    if (i1137 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1136)
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
    flat1152 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1152)
        write(pp, flat1152)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1696 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1696 = nothing
        end
        fields1148 = _t1696
        unwrapped_fields1149 = fields1148
        write(pp, "(=")
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

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1157 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1157)
        write(pp, flat1157)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1697 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1697 = nothing
        end
        fields1153 = _t1697
        unwrapped_fields1154 = fields1153
        write(pp, "(<")
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

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1162 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1162)
        write(pp, flat1162)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1698 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1698 = nothing
        end
        fields1158 = _t1698
        unwrapped_fields1159 = fields1158
        write(pp, "(<=")
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

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1167 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1699 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1699 = nothing
        end
        fields1163 = _t1699
        unwrapped_fields1164 = fields1163
        write(pp, "(>")
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

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1172 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1172)
        write(pp, flat1172)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1700 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1700 = nothing
        end
        fields1168 = _t1700
        unwrapped_fields1169 = fields1168
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1170 = unwrapped_fields1169[1]
        pretty_term(pp, field1170)
        newline(pp)
        field1171 = unwrapped_fields1169[2]
        pretty_term(pp, field1171)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1178 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1178)
        write(pp, flat1178)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1701 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1701 = nothing
        end
        fields1173 = _t1701
        unwrapped_fields1174 = fields1173
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1175 = unwrapped_fields1174[1]
        pretty_term(pp, field1175)
        newline(pp)
        field1176 = unwrapped_fields1174[2]
        pretty_term(pp, field1176)
        newline(pp)
        field1177 = unwrapped_fields1174[3]
        pretty_term(pp, field1177)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1184 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1184)
        write(pp, flat1184)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1702 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1702 = nothing
        end
        fields1179 = _t1702
        unwrapped_fields1180 = fields1179
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1181 = unwrapped_fields1180[1]
        pretty_term(pp, field1181)
        newline(pp)
        field1182 = unwrapped_fields1180[2]
        pretty_term(pp, field1182)
        newline(pp)
        field1183 = unwrapped_fields1180[3]
        pretty_term(pp, field1183)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1190 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1190)
        write(pp, flat1190)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1703 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1703 = nothing
        end
        fields1185 = _t1703
        unwrapped_fields1186 = fields1185
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1187 = unwrapped_fields1186[1]
        pretty_term(pp, field1187)
        newline(pp)
        field1188 = unwrapped_fields1186[2]
        pretty_term(pp, field1188)
        newline(pp)
        field1189 = unwrapped_fields1186[3]
        pretty_term(pp, field1189)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1196 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1196)
        write(pp, flat1196)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1704 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1704 = nothing
        end
        fields1191 = _t1704
        unwrapped_fields1192 = fields1191
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1193 = unwrapped_fields1192[1]
        pretty_term(pp, field1193)
        newline(pp)
        field1194 = unwrapped_fields1192[2]
        pretty_term(pp, field1194)
        newline(pp)
        field1195 = unwrapped_fields1192[3]
        pretty_term(pp, field1195)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1201 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1201)
        write(pp, flat1201)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1705 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1705 = nothing
        end
        deconstruct_result1199 = _t1705
        if !isnothing(deconstruct_result1199)
            unwrapped1200 = deconstruct_result1199
            pretty_specialized_value(pp, unwrapped1200)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1706 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1706 = nothing
            end
            deconstruct_result1197 = _t1706
            if !isnothing(deconstruct_result1197)
                unwrapped1198 = deconstruct_result1197
                pretty_term(pp, unwrapped1198)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1203 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1203)
        write(pp, flat1203)
        return nothing
    else
        fields1202 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1202)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1210 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1210)
        write(pp, flat1210)
        return nothing
    else
        _dollar_dollar = msg
        fields1204 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1205 = fields1204
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1206 = unwrapped_fields1205[1]
        pretty_name(pp, field1206)
        field1207 = unwrapped_fields1205[2]
        if !isempty(field1207)
            newline(pp)
            for (i1707, elem1208) in enumerate(field1207)
                i1209 = i1707 - 1
                if (i1209 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1208)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1215 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        _dollar_dollar = msg
        fields1211 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1212 = fields1211
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1213 = unwrapped_fields1212[1]
        pretty_term(pp, field1213)
        newline(pp)
        field1214 = unwrapped_fields1212[2]
        pretty_term(pp, field1214)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1219 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1219)
        write(pp, flat1219)
        return nothing
    else
        fields1216 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1216)
            newline(pp)
            for (i1708, elem1217) in enumerate(fields1216)
                i1218 = i1708 - 1
                if (i1218 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1217)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1226 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1226)
        write(pp, flat1226)
        return nothing
    else
        _dollar_dollar = msg
        fields1220 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1221 = fields1220
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1222 = unwrapped_fields1221[1]
        pretty_name(pp, field1222)
        field1223 = unwrapped_fields1221[2]
        if !isempty(field1223)
            newline(pp)
            for (i1709, elem1224) in enumerate(field1223)
                i1225 = i1709 - 1
                if (i1225 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1224)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1235 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1235)
        write(pp, flat1235)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1710 = _dollar_dollar.attrs
        else
            _t1710 = nothing
        end
        fields1227 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1710,)
        unwrapped_fields1228 = fields1227
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1229 = unwrapped_fields1228[1]
        if !isempty(field1229)
            newline(pp)
            for (i1711, elem1230) in enumerate(field1229)
                i1231 = i1711 - 1
                if (i1231 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1230)
            end
        end
        newline(pp)
        field1232 = unwrapped_fields1228[2]
        pretty_script(pp, field1232)
        field1233 = unwrapped_fields1228[3]
        if !isnothing(field1233)
            newline(pp)
            opt_val1234 = field1233
            pretty_attrs(pp, opt_val1234)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1240 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1240)
        write(pp, flat1240)
        return nothing
    else
        _dollar_dollar = msg
        fields1236 = _dollar_dollar.constructs
        unwrapped_fields1237 = fields1236
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1237)
            newline(pp)
            for (i1712, elem1238) in enumerate(unwrapped_fields1237)
                i1239 = i1712 - 1
                if (i1239 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1238)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1245 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1245)
        write(pp, flat1245)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1713 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1713 = nothing
        end
        deconstruct_result1243 = _t1713
        if !isnothing(deconstruct_result1243)
            unwrapped1244 = deconstruct_result1243
            pretty_loop(pp, unwrapped1244)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1714 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1714 = nothing
            end
            deconstruct_result1241 = _t1714
            if !isnothing(deconstruct_result1241)
                unwrapped1242 = deconstruct_result1241
                pretty_instruction(pp, unwrapped1242)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1252 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1252)
        write(pp, flat1252)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1715 = _dollar_dollar.attrs
        else
            _t1715 = nothing
        end
        fields1246 = (_dollar_dollar.init, _dollar_dollar.body, _t1715,)
        unwrapped_fields1247 = fields1246
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1248 = unwrapped_fields1247[1]
        pretty_init(pp, field1248)
        newline(pp)
        field1249 = unwrapped_fields1247[2]
        pretty_script(pp, field1249)
        field1250 = unwrapped_fields1247[3]
        if !isnothing(field1250)
            newline(pp)
            opt_val1251 = field1250
            pretty_attrs(pp, opt_val1251)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1256 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1256)
        write(pp, flat1256)
        return nothing
    else
        fields1253 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1253)
            newline(pp)
            for (i1716, elem1254) in enumerate(fields1253)
                i1255 = i1716 - 1
                if (i1255 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1254)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1267 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1267)
        write(pp, flat1267)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1717 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1717 = nothing
        end
        deconstruct_result1265 = _t1717
        if !isnothing(deconstruct_result1265)
            unwrapped1266 = deconstruct_result1265
            pretty_assign(pp, unwrapped1266)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1718 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1718 = nothing
            end
            deconstruct_result1263 = _t1718
            if !isnothing(deconstruct_result1263)
                unwrapped1264 = deconstruct_result1263
                pretty_upsert(pp, unwrapped1264)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1719 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1719 = nothing
                end
                deconstruct_result1261 = _t1719
                if !isnothing(deconstruct_result1261)
                    unwrapped1262 = deconstruct_result1261
                    pretty_break(pp, unwrapped1262)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1720 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1720 = nothing
                    end
                    deconstruct_result1259 = _t1720
                    if !isnothing(deconstruct_result1259)
                        unwrapped1260 = deconstruct_result1259
                        pretty_monoid_def(pp, unwrapped1260)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1721 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1721 = nothing
                        end
                        deconstruct_result1257 = _t1721
                        if !isnothing(deconstruct_result1257)
                            unwrapped1258 = deconstruct_result1257
                            pretty_monus_def(pp, unwrapped1258)
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
    flat1274 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1274)
        write(pp, flat1274)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1722 = _dollar_dollar.attrs
        else
            _t1722 = nothing
        end
        fields1268 = (_dollar_dollar.name, _dollar_dollar.body, _t1722,)
        unwrapped_fields1269 = fields1268
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1270 = unwrapped_fields1269[1]
        pretty_relation_id(pp, field1270)
        newline(pp)
        field1271 = unwrapped_fields1269[2]
        pretty_abstraction(pp, field1271)
        field1272 = unwrapped_fields1269[3]
        if !isnothing(field1272)
            newline(pp)
            opt_val1273 = field1272
            pretty_attrs(pp, opt_val1273)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1281 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1281)
        write(pp, flat1281)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1723 = _dollar_dollar.attrs
        else
            _t1723 = nothing
        end
        fields1275 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1723,)
        unwrapped_fields1276 = fields1275
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1277 = unwrapped_fields1276[1]
        pretty_relation_id(pp, field1277)
        newline(pp)
        field1278 = unwrapped_fields1276[2]
        pretty_abstraction_with_arity(pp, field1278)
        field1279 = unwrapped_fields1276[3]
        if !isnothing(field1279)
            newline(pp)
            opt_val1280 = field1279
            pretty_attrs(pp, opt_val1280)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1286 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1286)
        write(pp, flat1286)
        return nothing
    else
        _dollar_dollar = msg
        _t1724 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1282 = (_t1724, _dollar_dollar[1].value,)
        unwrapped_fields1283 = fields1282
        write(pp, "(")
        indent!(pp)
        field1284 = unwrapped_fields1283[1]
        pretty_bindings(pp, field1284)
        newline(pp)
        field1285 = unwrapped_fields1283[2]
        pretty_formula(pp, field1285)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1293 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1293)
        write(pp, flat1293)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1725 = _dollar_dollar.attrs
        else
            _t1725 = nothing
        end
        fields1287 = (_dollar_dollar.name, _dollar_dollar.body, _t1725,)
        unwrapped_fields1288 = fields1287
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1289 = unwrapped_fields1288[1]
        pretty_relation_id(pp, field1289)
        newline(pp)
        field1290 = unwrapped_fields1288[2]
        pretty_abstraction(pp, field1290)
        field1291 = unwrapped_fields1288[3]
        if !isnothing(field1291)
            newline(pp)
            opt_val1292 = field1291
            pretty_attrs(pp, opt_val1292)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1301 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1301)
        write(pp, flat1301)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1726 = _dollar_dollar.attrs
        else
            _t1726 = nothing
        end
        fields1294 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1726,)
        unwrapped_fields1295 = fields1294
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1296 = unwrapped_fields1295[1]
        pretty_monoid(pp, field1296)
        newline(pp)
        field1297 = unwrapped_fields1295[2]
        pretty_relation_id(pp, field1297)
        newline(pp)
        field1298 = unwrapped_fields1295[3]
        pretty_abstraction_with_arity(pp, field1298)
        field1299 = unwrapped_fields1295[4]
        if !isnothing(field1299)
            newline(pp)
            opt_val1300 = field1299
            pretty_attrs(pp, opt_val1300)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1310 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1310)
        write(pp, flat1310)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1727 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1727 = nothing
        end
        deconstruct_result1308 = _t1727
        if !isnothing(deconstruct_result1308)
            unwrapped1309 = deconstruct_result1308
            pretty_or_monoid(pp, unwrapped1309)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1728 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1728 = nothing
            end
            deconstruct_result1306 = _t1728
            if !isnothing(deconstruct_result1306)
                unwrapped1307 = deconstruct_result1306
                pretty_min_monoid(pp, unwrapped1307)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1729 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1729 = nothing
                end
                deconstruct_result1304 = _t1729
                if !isnothing(deconstruct_result1304)
                    unwrapped1305 = deconstruct_result1304
                    pretty_max_monoid(pp, unwrapped1305)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1730 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1730 = nothing
                    end
                    deconstruct_result1302 = _t1730
                    if !isnothing(deconstruct_result1302)
                        unwrapped1303 = deconstruct_result1302
                        pretty_sum_monoid(pp, unwrapped1303)
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
    fields1311 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1314 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1314)
        write(pp, flat1314)
        return nothing
    else
        _dollar_dollar = msg
        fields1312 = _dollar_dollar.var"#type"
        unwrapped_fields1313 = fields1312
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1313)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1317 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1317)
        write(pp, flat1317)
        return nothing
    else
        _dollar_dollar = msg
        fields1315 = _dollar_dollar.var"#type"
        unwrapped_fields1316 = fields1315
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1316)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1320 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1320)
        write(pp, flat1320)
        return nothing
    else
        _dollar_dollar = msg
        fields1318 = _dollar_dollar.var"#type"
        unwrapped_fields1319 = fields1318
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1319)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1328 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1328)
        write(pp, flat1328)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1731 = _dollar_dollar.attrs
        else
            _t1731 = nothing
        end
        fields1321 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1731,)
        unwrapped_fields1322 = fields1321
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1323 = unwrapped_fields1322[1]
        pretty_monoid(pp, field1323)
        newline(pp)
        field1324 = unwrapped_fields1322[2]
        pretty_relation_id(pp, field1324)
        newline(pp)
        field1325 = unwrapped_fields1322[3]
        pretty_abstraction_with_arity(pp, field1325)
        field1326 = unwrapped_fields1322[4]
        if !isnothing(field1326)
            newline(pp)
            opt_val1327 = field1326
            pretty_attrs(pp, opt_val1327)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1335 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1335)
        write(pp, flat1335)
        return nothing
    else
        _dollar_dollar = msg
        fields1329 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1330 = fields1329
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1331 = unwrapped_fields1330[1]
        pretty_relation_id(pp, field1331)
        newline(pp)
        field1332 = unwrapped_fields1330[2]
        pretty_abstraction(pp, field1332)
        newline(pp)
        field1333 = unwrapped_fields1330[3]
        pretty_functional_dependency_keys(pp, field1333)
        newline(pp)
        field1334 = unwrapped_fields1330[4]
        pretty_functional_dependency_values(pp, field1334)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1339 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1339)
        write(pp, flat1339)
        return nothing
    else
        fields1336 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1336)
            newline(pp)
            for (i1732, elem1337) in enumerate(fields1336)
                i1338 = i1732 - 1
                if (i1338 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1337)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1343 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1343)
        write(pp, flat1343)
        return nothing
    else
        fields1340 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1340)
            newline(pp)
            for (i1733, elem1341) in enumerate(fields1340)
                i1342 = i1733 - 1
                if (i1342 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1341)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1352 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1352)
        write(pp, flat1352)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1734 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1734 = nothing
        end
        deconstruct_result1350 = _t1734
        if !isnothing(deconstruct_result1350)
            unwrapped1351 = deconstruct_result1350
            pretty_edb(pp, unwrapped1351)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1735 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1735 = nothing
            end
            deconstruct_result1348 = _t1735
            if !isnothing(deconstruct_result1348)
                unwrapped1349 = deconstruct_result1348
                pretty_betree_relation(pp, unwrapped1349)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1736 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1736 = nothing
                end
                deconstruct_result1346 = _t1736
                if !isnothing(deconstruct_result1346)
                    unwrapped1347 = deconstruct_result1346
                    pretty_csv_data(pp, unwrapped1347)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1737 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1737 = nothing
                    end
                    deconstruct_result1344 = _t1737
                    if !isnothing(deconstruct_result1344)
                        unwrapped1345 = deconstruct_result1344
                        pretty_iceberg_data(pp, unwrapped1345)
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
    flat1358 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1358)
        write(pp, flat1358)
        return nothing
    else
        _dollar_dollar = msg
        fields1353 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1354 = fields1353
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1355 = unwrapped_fields1354[1]
        pretty_relation_id(pp, field1355)
        newline(pp)
        field1356 = unwrapped_fields1354[2]
        pretty_edb_path(pp, field1356)
        newline(pp)
        field1357 = unwrapped_fields1354[3]
        pretty_edb_types(pp, field1357)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1362 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1362)
        write(pp, flat1362)
        return nothing
    else
        fields1359 = msg
        write(pp, "[")
        indent!(pp)
        for (i1738, elem1360) in enumerate(fields1359)
            i1361 = i1738 - 1
            if (i1361 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1360))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1366 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1366)
        write(pp, flat1366)
        return nothing
    else
        fields1363 = msg
        write(pp, "[")
        indent!(pp)
        for (i1739, elem1364) in enumerate(fields1363)
            i1365 = i1739 - 1
            if (i1365 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1364)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1371 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1371)
        write(pp, flat1371)
        return nothing
    else
        _dollar_dollar = msg
        fields1367 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1368 = fields1367
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1369 = unwrapped_fields1368[1]
        pretty_relation_id(pp, field1369)
        newline(pp)
        field1370 = unwrapped_fields1368[2]
        pretty_betree_info(pp, field1370)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1377 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1377)
        write(pp, flat1377)
        return nothing
    else
        _dollar_dollar = msg
        _t1740 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1372 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1740,)
        unwrapped_fields1373 = fields1372
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1374 = unwrapped_fields1373[1]
        pretty_betree_info_key_types(pp, field1374)
        newline(pp)
        field1375 = unwrapped_fields1373[2]
        pretty_betree_info_value_types(pp, field1375)
        newline(pp)
        field1376 = unwrapped_fields1373[3]
        pretty_config_dict(pp, field1376)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1381 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1381)
        write(pp, flat1381)
        return nothing
    else
        fields1378 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1378)
            newline(pp)
            for (i1741, elem1379) in enumerate(fields1378)
                i1380 = i1741 - 1
                if (i1380 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1379)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1385 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1385)
        write(pp, flat1385)
        return nothing
    else
        fields1382 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1382)
            newline(pp)
            for (i1742, elem1383) in enumerate(fields1382)
                i1384 = i1742 - 1
                if (i1384 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1383)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1392 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1392)
        write(pp, flat1392)
        return nothing
    else
        _dollar_dollar = msg
        fields1386 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1387 = fields1386
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1388 = unwrapped_fields1387[1]
        pretty_csvlocator(pp, field1388)
        newline(pp)
        field1389 = unwrapped_fields1387[2]
        pretty_csv_config(pp, field1389)
        newline(pp)
        field1390 = unwrapped_fields1387[3]
        pretty_gnf_columns(pp, field1390)
        newline(pp)
        field1391 = unwrapped_fields1387[4]
        pretty_csv_asof(pp, field1391)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1399 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1399)
        write(pp, flat1399)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1743 = _dollar_dollar.paths
        else
            _t1743 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1744 = String(copy(_dollar_dollar.inline_data))
        else
            _t1744 = nothing
        end
        fields1393 = (_t1743, _t1744,)
        unwrapped_fields1394 = fields1393
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1395 = unwrapped_fields1394[1]
        if !isnothing(field1395)
            newline(pp)
            opt_val1396 = field1395
            pretty_csv_locator_paths(pp, opt_val1396)
        end
        field1397 = unwrapped_fields1394[2]
        if !isnothing(field1397)
            newline(pp)
            opt_val1398 = field1397
            pretty_csv_locator_inline_data(pp, opt_val1398)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1403 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1403)
        write(pp, flat1403)
        return nothing
    else
        fields1400 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1400)
            newline(pp)
            for (i1745, elem1401) in enumerate(fields1400)
                i1402 = i1745 - 1
                if (i1402 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1401))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1405 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1405)
        write(pp, flat1405)
        return nothing
    else
        fields1404 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1404))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1411 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1411)
        write(pp, flat1411)
        return nothing
    else
        _dollar_dollar = msg
        _t1746 = deconstruct_csv_config(pp, _dollar_dollar)
        _t1747 = deconstruct_csv_storage_integration_optional(pp, _dollar_dollar)
        fields1406 = (_t1746, _t1747,)
        unwrapped_fields1407 = fields1406
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1408 = unwrapped_fields1407[1]
        pretty_config_dict(pp, field1408)
        field1409 = unwrapped_fields1407[2]
        if !isnothing(field1409)
            newline(pp)
            opt_val1410 = field1409
            pretty_storage_integration(pp, opt_val1410)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_storage_integration(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat1413 = try_flat(pp, msg, pretty_storage_integration)
    if !isnothing(flat1413)
        write(pp, flat1413)
        return nothing
    else
        fields1412 = msg
        write(pp, "(storage_integration")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, fields1412)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1417 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1417)
        write(pp, flat1417)
        return nothing
    else
        fields1414 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1414)
            newline(pp)
            for (i1748, elem1415) in enumerate(fields1414)
                i1416 = i1748 - 1
                if (i1416 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1415)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1426 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1426)
        write(pp, flat1426)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1749 = _dollar_dollar.target_id
        else
            _t1749 = nothing
        end
        fields1418 = (_dollar_dollar.column_path, _t1749, _dollar_dollar.types,)
        unwrapped_fields1419 = fields1418
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1420 = unwrapped_fields1419[1]
        pretty_gnf_column_path(pp, field1420)
        field1421 = unwrapped_fields1419[2]
        if !isnothing(field1421)
            newline(pp)
            opt_val1422 = field1421
            pretty_relation_id(pp, opt_val1422)
        end
        newline(pp)
        write(pp, "[")
        field1423 = unwrapped_fields1419[3]
        for (i1750, elem1424) in enumerate(field1423)
            i1425 = i1750 - 1
            if (i1425 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1424)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1433 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1433)
        write(pp, flat1433)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1751 = _dollar_dollar[1]
        else
            _t1751 = nothing
        end
        deconstruct_result1431 = _t1751
        if !isnothing(deconstruct_result1431)
            unwrapped1432 = deconstruct_result1431
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1432))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1752 = _dollar_dollar
            else
                _t1752 = nothing
            end
            deconstruct_result1427 = _t1752
            if !isnothing(deconstruct_result1427)
                unwrapped1428 = deconstruct_result1427
                write(pp, "[")
                indent!(pp)
                for (i1753, elem1429) in enumerate(unwrapped1428)
                    i1430 = i1753 - 1
                    if (i1430 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1429))
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
    flat1435 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1435)
        write(pp, flat1435)
        return nothing
    else
        fields1434 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1434))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1446 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1446)
        write(pp, flat1446)
        return nothing
    else
        _dollar_dollar = msg
        _t1754 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1755 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1436 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1754, _t1755, _dollar_dollar.returns_delta,)
        unwrapped_fields1437 = fields1436
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1438 = unwrapped_fields1437[1]
        pretty_iceberg_locator(pp, field1438)
        newline(pp)
        field1439 = unwrapped_fields1437[2]
        pretty_iceberg_catalog_config(pp, field1439)
        newline(pp)
        field1440 = unwrapped_fields1437[3]
        pretty_gnf_columns(pp, field1440)
        field1441 = unwrapped_fields1437[4]
        if !isnothing(field1441)
            newline(pp)
            opt_val1442 = field1441
            pretty_iceberg_from_snapshot(pp, opt_val1442)
        end
        field1443 = unwrapped_fields1437[5]
        if !isnothing(field1443)
            newline(pp)
            opt_val1444 = field1443
            pretty_iceberg_to_snapshot(pp, opt_val1444)
        end
        newline(pp)
        field1445 = unwrapped_fields1437[6]
        pretty_boolean_value(pp, field1445)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1452 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1452)
        write(pp, flat1452)
        return nothing
    else
        _dollar_dollar = msg
        fields1447 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1448 = fields1447
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1449 = unwrapped_fields1448[1]
        pretty_iceberg_locator_table_name(pp, field1449)
        newline(pp)
        field1450 = unwrapped_fields1448[2]
        pretty_iceberg_locator_namespace(pp, field1450)
        newline(pp)
        field1451 = unwrapped_fields1448[3]
        pretty_iceberg_locator_warehouse(pp, field1451)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1454 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1454)
        write(pp, flat1454)
        return nothing
    else
        fields1453 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1453))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1458 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1458)
        write(pp, flat1458)
        return nothing
    else
        fields1455 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1455)
            newline(pp)
            for (i1756, elem1456) in enumerate(fields1455)
                i1457 = i1756 - 1
                if (i1457 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1456))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1460 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1460)
        write(pp, flat1460)
        return nothing
    else
        fields1459 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1459))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1468 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1468)
        write(pp, flat1468)
        return nothing
    else
        _dollar_dollar = msg
        _t1757 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1461 = (_dollar_dollar.catalog_uri, _t1757, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1462 = fields1461
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1463 = unwrapped_fields1462[1]
        pretty_iceberg_catalog_uri(pp, field1463)
        field1464 = unwrapped_fields1462[2]
        if !isnothing(field1464)
            newline(pp)
            opt_val1465 = field1464
            pretty_iceberg_catalog_config_scope(pp, opt_val1465)
        end
        newline(pp)
        field1466 = unwrapped_fields1462[3]
        pretty_iceberg_properties(pp, field1466)
        newline(pp)
        field1467 = unwrapped_fields1462[4]
        pretty_iceberg_auth_properties(pp, field1467)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1470 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1470)
        write(pp, flat1470)
        return nothing
    else
        fields1469 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1469))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1472 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1472)
        write(pp, flat1472)
        return nothing
    else
        fields1471 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1471))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1476 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1476)
        write(pp, flat1476)
        return nothing
    else
        fields1473 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1473)
            newline(pp)
            for (i1758, elem1474) in enumerate(fields1473)
                i1475 = i1758 - 1
                if (i1475 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1474)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1481 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1481)
        write(pp, flat1481)
        return nothing
    else
        _dollar_dollar = msg
        fields1477 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1478 = fields1477
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1479 = unwrapped_fields1478[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1479))
        newline(pp)
        field1480 = unwrapped_fields1478[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1480))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1485 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1485)
        write(pp, flat1485)
        return nothing
    else
        fields1482 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1482)
            newline(pp)
            for (i1759, elem1483) in enumerate(fields1482)
                i1484 = i1759 - 1
                if (i1484 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1483)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1490 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1490)
        write(pp, flat1490)
        return nothing
    else
        _dollar_dollar = msg
        _t1760 = mask_secret_value(pp, _dollar_dollar)
        fields1486 = (_dollar_dollar[1], _t1760,)
        unwrapped_fields1487 = fields1486
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1488 = unwrapped_fields1487[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1488))
        newline(pp)
        field1489 = unwrapped_fields1487[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1489))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1492 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1492)
        write(pp, flat1492)
        return nothing
    else
        fields1491 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1491))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1494 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1494)
        write(pp, flat1494)
        return nothing
    else
        fields1493 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1493))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1497 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1497)
        write(pp, flat1497)
        return nothing
    else
        _dollar_dollar = msg
        fields1495 = _dollar_dollar.fragment_id
        unwrapped_fields1496 = fields1495
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1496)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1502 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1502)
        write(pp, flat1502)
        return nothing
    else
        _dollar_dollar = msg
        fields1498 = _dollar_dollar.relations
        unwrapped_fields1499 = fields1498
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1499)
            newline(pp)
            for (i1761, elem1500) in enumerate(unwrapped_fields1499)
                i1501 = i1761 - 1
                if (i1501 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1500)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1509 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1509)
        write(pp, flat1509)
        return nothing
    else
        _dollar_dollar = msg
        fields1503 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1504 = fields1503
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1505 = unwrapped_fields1504[1]
        pretty_edb_path(pp, field1505)
        field1506 = unwrapped_fields1504[2]
        if !isempty(field1506)
            newline(pp)
            for (i1762, elem1507) in enumerate(field1506)
                i1508 = i1762 - 1
                if (i1508 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1507)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1514 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1514)
        write(pp, flat1514)
        return nothing
    else
        _dollar_dollar = msg
        fields1510 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1511 = fields1510
        field1512 = unwrapped_fields1511[1]
        pretty_edb_path(pp, field1512)
        write(pp, " ")
        field1513 = unwrapped_fields1511[2]
        pretty_relation_id(pp, field1513)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1518 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1518)
        write(pp, flat1518)
        return nothing
    else
        fields1515 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1515)
            newline(pp)
            for (i1763, elem1516) in enumerate(fields1515)
                i1517 = i1763 - 1
                if (i1517 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1516)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1529 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1529)
        write(pp, flat1529)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1764 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1764 = nothing
        end
        deconstruct_result1527 = _t1764
        if !isnothing(deconstruct_result1527)
            unwrapped1528 = deconstruct_result1527
            pretty_demand(pp, unwrapped1528)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1765 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1765 = nothing
            end
            deconstruct_result1525 = _t1765
            if !isnothing(deconstruct_result1525)
                unwrapped1526 = deconstruct_result1525
                pretty_output(pp, unwrapped1526)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1766 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1766 = nothing
                end
                deconstruct_result1523 = _t1766
                if !isnothing(deconstruct_result1523)
                    unwrapped1524 = deconstruct_result1523
                    pretty_what_if(pp, unwrapped1524)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1767 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1767 = nothing
                    end
                    deconstruct_result1521 = _t1767
                    if !isnothing(deconstruct_result1521)
                        unwrapped1522 = deconstruct_result1521
                        pretty_abort(pp, unwrapped1522)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1768 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1768 = nothing
                        end
                        deconstruct_result1519 = _t1768
                        if !isnothing(deconstruct_result1519)
                            unwrapped1520 = deconstruct_result1519
                            pretty_export(pp, unwrapped1520)
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
    flat1532 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1532)
        write(pp, flat1532)
        return nothing
    else
        _dollar_dollar = msg
        fields1530 = _dollar_dollar.relation_id
        unwrapped_fields1531 = fields1530
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1531)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1537 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1537)
        write(pp, flat1537)
        return nothing
    else
        _dollar_dollar = msg
        fields1533 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1534 = fields1533
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1535 = unwrapped_fields1534[1]
        pretty_name(pp, field1535)
        newline(pp)
        field1536 = unwrapped_fields1534[2]
        pretty_relation_id(pp, field1536)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1542 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1542)
        write(pp, flat1542)
        return nothing
    else
        _dollar_dollar = msg
        fields1538 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1539 = fields1538
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1540 = unwrapped_fields1539[1]
        pretty_name(pp, field1540)
        newline(pp)
        field1541 = unwrapped_fields1539[2]
        pretty_epoch(pp, field1541)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1548 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1548)
        write(pp, flat1548)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1769 = _dollar_dollar.name
        else
            _t1769 = nothing
        end
        fields1543 = (_t1769, _dollar_dollar.relation_id,)
        unwrapped_fields1544 = fields1543
        write(pp, "(abort")
        indent_sexp!(pp)
        field1545 = unwrapped_fields1544[1]
        if !isnothing(field1545)
            newline(pp)
            opt_val1546 = field1545
            pretty_name(pp, opt_val1546)
        end
        newline(pp)
        field1547 = unwrapped_fields1544[2]
        pretty_relation_id(pp, field1547)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1553 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1553)
        write(pp, flat1553)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1770 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1770 = nothing
        end
        deconstruct_result1551 = _t1770
        if !isnothing(deconstruct_result1551)
            unwrapped1552 = deconstruct_result1551
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1552)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1771 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1771 = nothing
            end
            deconstruct_result1549 = _t1771
            if !isnothing(deconstruct_result1549)
                unwrapped1550 = deconstruct_result1549
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1550)
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
    flat1564 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1564)
        write(pp, flat1564)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1772 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1772 = nothing
        end
        deconstruct_result1559 = _t1772
        if !isnothing(deconstruct_result1559)
            unwrapped1560 = deconstruct_result1559
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1561 = unwrapped1560[1]
            pretty_export_csv_path(pp, field1561)
            newline(pp)
            field1562 = unwrapped1560[2]
            pretty_export_csv_source(pp, field1562)
            newline(pp)
            field1563 = unwrapped1560[3]
            pretty_csv_config(pp, field1563)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1774 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1773 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1774,)
            else
                _t1773 = nothing
            end
            deconstruct_result1554 = _t1773
            if !isnothing(deconstruct_result1554)
                unwrapped1555 = deconstruct_result1554
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1556 = unwrapped1555[1]
                pretty_export_csv_path(pp, field1556)
                newline(pp)
                field1557 = unwrapped1555[2]
                pretty_export_csv_columns_list(pp, field1557)
                newline(pp)
                field1558 = unwrapped1555[3]
                pretty_config_dict(pp, field1558)
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
    flat1566 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1566)
        write(pp, flat1566)
        return nothing
    else
        fields1565 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1565))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1573 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1573)
        write(pp, flat1573)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1775 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1775 = nothing
        end
        deconstruct_result1569 = _t1775
        if !isnothing(deconstruct_result1569)
            unwrapped1570 = deconstruct_result1569
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1570)
                newline(pp)
                for (i1776, elem1571) in enumerate(unwrapped1570)
                    i1572 = i1776 - 1
                    if (i1572 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1571)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1777 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1777 = nothing
            end
            deconstruct_result1567 = _t1777
            if !isnothing(deconstruct_result1567)
                unwrapped1568 = deconstruct_result1567
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1568)
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
    flat1578 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1578)
        write(pp, flat1578)
        return nothing
    else
        _dollar_dollar = msg
        fields1574 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1575 = fields1574
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1576 = unwrapped_fields1575[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1576))
        newline(pp)
        field1577 = unwrapped_fields1575[2]
        pretty_relation_id(pp, field1577)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1582 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1582)
        write(pp, flat1582)
        return nothing
    else
        fields1579 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1579)
            newline(pp)
            for (i1778, elem1580) in enumerate(fields1579)
                i1581 = i1778 - 1
                if (i1581 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1580)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1591 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1591)
        write(pp, flat1591)
        return nothing
    else
        _dollar_dollar = msg
        _t1779 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1583 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1779,)
        unwrapped_fields1584 = fields1583
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1585 = unwrapped_fields1584[1]
        pretty_iceberg_locator(pp, field1585)
        newline(pp)
        field1586 = unwrapped_fields1584[2]
        pretty_iceberg_catalog_config(pp, field1586)
        newline(pp)
        field1587 = unwrapped_fields1584[3]
        pretty_export_iceberg_table_def(pp, field1587)
        newline(pp)
        field1588 = unwrapped_fields1584[4]
        pretty_iceberg_table_properties(pp, field1588)
        field1589 = unwrapped_fields1584[5]
        if !isnothing(field1589)
            newline(pp)
            opt_val1590 = field1589
            pretty_config_dict(pp, opt_val1590)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1593 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1593)
        write(pp, flat1593)
        return nothing
    else
        fields1592 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1592)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1597 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1597)
        write(pp, flat1597)
        return nothing
    else
        fields1594 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1594)
            newline(pp)
            for (i1780, elem1595) in enumerate(fields1594)
                i1596 = i1780 - 1
                if (i1596 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1595)
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
    for (i1832, _rid) in enumerate(msg.ids)
        _idx = i1832 - 1
        newline(pp)
        write(pp, "(")
        _t1833 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1833)
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

function pretty_csv_storage_integration(pp::PrettyPrinter, msg::Proto.CSVStorageIntegration)
    write(pp, "(csv_storage_integration")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":provider ")
    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, msg.provider))
    newline(pp)
    write(pp, ":azure_sas_token ")
    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, msg.azure_sas_token))
    newline(pp)
    write(pp, ":s3_region ")
    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, msg.s3_region))
    newline(pp)
    write(pp, ":s3_access_key_id ")
    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, msg.s3_access_key_id))
    newline(pp)
    write(pp, ":s3_secret_access_key ")
    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, msg.s3_secret_access_key))
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
    for (i1834, _elem) in enumerate(msg.keys)
        _idx = i1834 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1835, _elem) in enumerate(msg.values)
        _idx = i1835 - 1
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
    for (i1836, _elem) in enumerate(msg.columns)
        _idx = i1836 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVStorageIntegration) = pretty_csv_storage_integration(pp, x)
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
