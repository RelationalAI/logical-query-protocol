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
    _t1803 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1803
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1804 = Proto.Value(value=OneOf(:int_value, v))
    return _t1804
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1805 = Proto.Value(value=OneOf(:float_value, v))
    return _t1805
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1806 = Proto.Value(value=OneOf(:string_value, v))
    return _t1806
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1807 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1807
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1808 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1808
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1809 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1809,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1810 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1810,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1811 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1811,))
            end
        end
    end
    _t1812 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1812,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1813 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1813,))
    _t1814 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1814,))
    if msg.new_line != ""
        _t1815 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1815,))
    end
    _t1816 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1816,))
    _t1817 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1817,))
    _t1818 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1818,))
    if msg.comment != ""
        _t1819 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1819,))
    end
    for missing_string in msg.missing_strings
        _t1820 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1820,))
    end
    _t1821 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1821,))
    _t1822 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1822,))
    _t1823 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1823,))
    if msg.partition_size_mb != 0
        _t1824 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1824,))
    end
    return sort(result)
end

function deconstruct_csv_storage_integration_optional(pp::PrettyPrinter, msg::Proto.CSVConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    if !_has_proto_field(msg, Symbol("storage_integration"))
        return nothing
    else
        _t1825 = nothing
    end
    si = msg.storage_integration
    result = Tuple{String, Proto.Value}[]
    if si.provider != ""
        _t1826 = _make_value_string(pp, si.provider)
        push!(result, ("provider", _t1826,))
    end
    if si.azure_sas_token != ""
        _t1827 = _make_value_string(pp, "***")
        push!(result, ("azure_sas_token", _t1827,))
    end
    if si.s3_region != ""
        _t1828 = _make_value_string(pp, si.s3_region)
        push!(result, ("s3_region", _t1828,))
    end
    if si.s3_access_key_id != ""
        _t1829 = _make_value_string(pp, "***")
        push!(result, ("s3_access_key_id", _t1829,))
    end
    if si.s3_secret_access_key != ""
        _t1830 = _make_value_string(pp, "***")
        push!(result, ("s3_secret_access_key", _t1830,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1831 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1831,))
    _t1832 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1832,))
    _t1833 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1833,))
    _t1834 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1834,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1835 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1835,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1836 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1836,))
        end
    end
    _t1837 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1837,))
    _t1838 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1838,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1839 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1839,))
    end
    if !isnothing(msg.compression)
        _t1840 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1840,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1841 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1841,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1842 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1842,))
    end
    if !isnothing(msg.syntax_delim)
        _t1843 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1843,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1844 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1844,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1845 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1845,))
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
        _t1846 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1847 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1848 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1849 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1849,))
    end
    if msg.target_file_size_bytes != 0
        _t1850 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1850,))
    end
    if msg.compression != ""
        _t1851 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1851,))
    end
    if length(result) == 0
        return nothing
    else
        _t1852 = nothing
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
        _t1853 = nothing
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
    flat818 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat818)
        write(pp, flat818)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1618 = _dollar_dollar.configure
        else
            _t1618 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1619 = _dollar_dollar.sync
        else
            _t1619 = nothing
        end
        fields809 = (_t1618, _t1619, _dollar_dollar.epochs,)
        unwrapped_fields810 = fields809
        write(pp, "(transaction")
        indent_sexp!(pp)
        field811 = unwrapped_fields810[1]
        if !isnothing(field811)
            newline(pp)
            opt_val812 = field811
            pretty_configure(pp, opt_val812)
        end
        field813 = unwrapped_fields810[2]
        if !isnothing(field813)
            newline(pp)
            opt_val814 = field813
            pretty_sync(pp, opt_val814)
        end
        field815 = unwrapped_fields810[3]
        if !isempty(field815)
            newline(pp)
            for (i1620, elem816) in enumerate(field815)
                i817 = i1620 - 1
                if (i817 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem816)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat821 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat821)
        write(pp, flat821)
        return nothing
    else
        _dollar_dollar = msg
        _t1621 = deconstruct_configure(pp, _dollar_dollar)
        fields819 = _t1621
        unwrapped_fields820 = fields819
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields820)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat825 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat825)
        write(pp, flat825)
        return nothing
    else
        fields822 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields822)
            newline(pp)
            for (i1622, elem823) in enumerate(fields822)
                i824 = i1622 - 1
                if (i824 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem823)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat830 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat830)
        write(pp, flat830)
        return nothing
    else
        _dollar_dollar = msg
        fields826 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields827 = fields826
        write(pp, ":")
        field828 = unwrapped_fields827[1]
        write(pp, field828)
        write(pp, " ")
        field829 = unwrapped_fields827[2]
        pretty_raw_value(pp, field829)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat856 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat856)
        write(pp, flat856)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1623 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1623 = nothing
        end
        deconstruct_result854 = _t1623
        if !isnothing(deconstruct_result854)
            unwrapped855 = deconstruct_result854
            pretty_raw_date(pp, unwrapped855)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1624 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1624 = nothing
            end
            deconstruct_result852 = _t1624
            if !isnothing(deconstruct_result852)
                unwrapped853 = deconstruct_result852
                pretty_raw_datetime(pp, unwrapped853)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1625 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1625 = nothing
                end
                deconstruct_result850 = _t1625
                if !isnothing(deconstruct_result850)
                    unwrapped851 = deconstruct_result850
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped851))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1626 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1626 = nothing
                    end
                    deconstruct_result848 = _t1626
                    if !isnothing(deconstruct_result848)
                        unwrapped849 = deconstruct_result848
                        write(pp, (string(Int64(unwrapped849)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1627 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1627 = nothing
                        end
                        deconstruct_result846 = _t1627
                        if !isnothing(deconstruct_result846)
                            unwrapped847 = deconstruct_result846
                            write(pp, string(unwrapped847))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1628 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1628 = nothing
                            end
                            deconstruct_result844 = _t1628
                            if !isnothing(deconstruct_result844)
                                unwrapped845 = deconstruct_result844
                                write(pp, format_float32_literal(unwrapped845))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1629 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1629 = nothing
                                end
                                deconstruct_result842 = _t1629
                                if !isnothing(deconstruct_result842)
                                    unwrapped843 = deconstruct_result842
                                    write(pp, lowercase(string(unwrapped843)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1630 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1630 = nothing
                                    end
                                    deconstruct_result840 = _t1630
                                    if !isnothing(deconstruct_result840)
                                        unwrapped841 = deconstruct_result840
                                        write(pp, (string(Int64(unwrapped841)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1631 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1631 = nothing
                                        end
                                        deconstruct_result838 = _t1631
                                        if !isnothing(deconstruct_result838)
                                            unwrapped839 = deconstruct_result838
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped839))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1632 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1632 = nothing
                                            end
                                            deconstruct_result836 = _t1632
                                            if !isnothing(deconstruct_result836)
                                                unwrapped837 = deconstruct_result836
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped837))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1633 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1633 = nothing
                                                end
                                                deconstruct_result834 = _t1633
                                                if !isnothing(deconstruct_result834)
                                                    unwrapped835 = deconstruct_result834
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped835))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1634 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1634 = nothing
                                                    end
                                                    deconstruct_result832 = _t1634
                                                    if !isnothing(deconstruct_result832)
                                                        unwrapped833 = deconstruct_result832
                                                        pretty_boolean_value(pp, unwrapped833)
                                                    else
                                                        fields831 = msg
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
    flat862 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat862)
        write(pp, flat862)
        return nothing
    else
        _dollar_dollar = msg
        fields857 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields858 = fields857
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field859 = unwrapped_fields858[1]
        write(pp, string(field859))
        newline(pp)
        field860 = unwrapped_fields858[2]
        write(pp, string(field860))
        newline(pp)
        field861 = unwrapped_fields858[3]
        write(pp, string(field861))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat873 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat873)
        write(pp, flat873)
        return nothing
    else
        _dollar_dollar = msg
        fields863 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields864 = fields863
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field865 = unwrapped_fields864[1]
        write(pp, string(field865))
        newline(pp)
        field866 = unwrapped_fields864[2]
        write(pp, string(field866))
        newline(pp)
        field867 = unwrapped_fields864[3]
        write(pp, string(field867))
        newline(pp)
        field868 = unwrapped_fields864[4]
        write(pp, string(field868))
        newline(pp)
        field869 = unwrapped_fields864[5]
        write(pp, string(field869))
        newline(pp)
        field870 = unwrapped_fields864[6]
        write(pp, string(field870))
        field871 = unwrapped_fields864[7]
        if !isnothing(field871)
            newline(pp)
            opt_val872 = field871
            write(pp, string(opt_val872))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1635 = ()
    else
        _t1635 = nothing
    end
    deconstruct_result876 = _t1635
    if !isnothing(deconstruct_result876)
        unwrapped877 = deconstruct_result876
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1636 = ()
        else
            _t1636 = nothing
        end
        deconstruct_result874 = _t1636
        if !isnothing(deconstruct_result874)
            unwrapped875 = deconstruct_result874
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat882 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat882)
        write(pp, flat882)
        return nothing
    else
        _dollar_dollar = msg
        fields878 = _dollar_dollar.fragments
        unwrapped_fields879 = fields878
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields879)
            newline(pp)
            for (i1637, elem880) in enumerate(unwrapped_fields879)
                i881 = i1637 - 1
                if (i881 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem880)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat885 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat885)
        write(pp, flat885)
        return nothing
    else
        _dollar_dollar = msg
        fields883 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields884 = fields883
        write(pp, ":")
        write(pp, unwrapped_fields884)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat892 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat892)
        write(pp, flat892)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1638 = _dollar_dollar.writes
        else
            _t1638 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1639 = _dollar_dollar.reads
        else
            _t1639 = nothing
        end
        fields886 = (_t1638, _t1639,)
        unwrapped_fields887 = fields886
        write(pp, "(epoch")
        indent_sexp!(pp)
        field888 = unwrapped_fields887[1]
        if !isnothing(field888)
            newline(pp)
            opt_val889 = field888
            pretty_epoch_writes(pp, opt_val889)
        end
        field890 = unwrapped_fields887[2]
        if !isnothing(field890)
            newline(pp)
            opt_val891 = field890
            pretty_epoch_reads(pp, opt_val891)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat896 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat896)
        write(pp, flat896)
        return nothing
    else
        fields893 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields893)
            newline(pp)
            for (i1640, elem894) in enumerate(fields893)
                i895 = i1640 - 1
                if (i895 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem894)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat905 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat905)
        write(pp, flat905)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1641 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1641 = nothing
        end
        deconstruct_result903 = _t1641
        if !isnothing(deconstruct_result903)
            unwrapped904 = deconstruct_result903
            pretty_define(pp, unwrapped904)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1642 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1642 = nothing
            end
            deconstruct_result901 = _t1642
            if !isnothing(deconstruct_result901)
                unwrapped902 = deconstruct_result901
                pretty_undefine(pp, unwrapped902)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1643 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1643 = nothing
                end
                deconstruct_result899 = _t1643
                if !isnothing(deconstruct_result899)
                    unwrapped900 = deconstruct_result899
                    pretty_context(pp, unwrapped900)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1644 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1644 = nothing
                    end
                    deconstruct_result897 = _t1644
                    if !isnothing(deconstruct_result897)
                        unwrapped898 = deconstruct_result897
                        pretty_snapshot(pp, unwrapped898)
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
    flat908 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat908)
        write(pp, flat908)
        return nothing
    else
        _dollar_dollar = msg
        fields906 = _dollar_dollar.fragment
        unwrapped_fields907 = fields906
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields907)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat915 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat915)
        write(pp, flat915)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields909 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields910 = fields909
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field911 = unwrapped_fields910[1]
        pretty_new_fragment_id(pp, field911)
        field912 = unwrapped_fields910[2]
        if !isempty(field912)
            newline(pp)
            for (i1645, elem913) in enumerate(field912)
                i914 = i1645 - 1
                if (i914 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem913)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat917 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat917)
        write(pp, flat917)
        return nothing
    else
        fields916 = msg
        pretty_fragment_id(pp, fields916)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat926 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat926)
        write(pp, flat926)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1646 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1646 = nothing
        end
        deconstruct_result924 = _t1646
        if !isnothing(deconstruct_result924)
            unwrapped925 = deconstruct_result924
            pretty_def(pp, unwrapped925)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1647 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1647 = nothing
            end
            deconstruct_result922 = _t1647
            if !isnothing(deconstruct_result922)
                unwrapped923 = deconstruct_result922
                pretty_algorithm(pp, unwrapped923)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1648 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1648 = nothing
                end
                deconstruct_result920 = _t1648
                if !isnothing(deconstruct_result920)
                    unwrapped921 = deconstruct_result920
                    pretty_constraint(pp, unwrapped921)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1649 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1649 = nothing
                    end
                    deconstruct_result918 = _t1649
                    if !isnothing(deconstruct_result918)
                        unwrapped919 = deconstruct_result918
                        pretty_data(pp, unwrapped919)
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
    flat933 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat933)
        write(pp, flat933)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1650 = _dollar_dollar.attrs
        else
            _t1650 = nothing
        end
        fields927 = (_dollar_dollar.name, _dollar_dollar.body, _t1650,)
        unwrapped_fields928 = fields927
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field929 = unwrapped_fields928[1]
        pretty_relation_id(pp, field929)
        newline(pp)
        field930 = unwrapped_fields928[2]
        pretty_abstraction(pp, field930)
        field931 = unwrapped_fields928[3]
        if !isnothing(field931)
            newline(pp)
            opt_val932 = field931
            pretty_attrs(pp, opt_val932)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat938 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat938)
        write(pp, flat938)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1652 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1651 = _t1652
        else
            _t1651 = nothing
        end
        deconstruct_result936 = _t1651
        if !isnothing(deconstruct_result936)
            unwrapped937 = deconstruct_result936
            write(pp, ":")
            write(pp, unwrapped937)
        else
            _dollar_dollar = msg
            _t1653 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result934 = _t1653
            if !isnothing(deconstruct_result934)
                unwrapped935 = deconstruct_result934
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped935))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat943 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat943)
        write(pp, flat943)
        return nothing
    else
        _dollar_dollar = msg
        _t1654 = deconstruct_bindings(pp, _dollar_dollar)
        fields939 = (_t1654, _dollar_dollar.value,)
        unwrapped_fields940 = fields939
        write(pp, "(")
        indent!(pp)
        field941 = unwrapped_fields940[1]
        pretty_bindings(pp, field941)
        newline(pp)
        field942 = unwrapped_fields940[2]
        pretty_formula(pp, field942)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat951 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat951)
        write(pp, flat951)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1655 = _dollar_dollar[2]
        else
            _t1655 = nothing
        end
        fields944 = (_dollar_dollar[1], _t1655,)
        unwrapped_fields945 = fields944
        write(pp, "[")
        indent!(pp)
        field946 = unwrapped_fields945[1]
        for (i1656, elem947) in enumerate(field946)
            i948 = i1656 - 1
            if (i948 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem947)
        end
        field949 = unwrapped_fields945[2]
        if !isnothing(field949)
            newline(pp)
            opt_val950 = field949
            pretty_value_bindings(pp, opt_val950)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat956 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat956)
        write(pp, flat956)
        return nothing
    else
        _dollar_dollar = msg
        fields952 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields953 = fields952
        field954 = unwrapped_fields953[1]
        write(pp, field954)
        write(pp, "::")
        field955 = unwrapped_fields953[2]
        pretty_type(pp, field955)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat985 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat985)
        write(pp, flat985)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1657 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1657 = nothing
        end
        deconstruct_result983 = _t1657
        if !isnothing(deconstruct_result983)
            unwrapped984 = deconstruct_result983
            pretty_unspecified_type(pp, unwrapped984)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1658 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1658 = nothing
            end
            deconstruct_result981 = _t1658
            if !isnothing(deconstruct_result981)
                unwrapped982 = deconstruct_result981
                pretty_string_type(pp, unwrapped982)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1659 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1659 = nothing
                end
                deconstruct_result979 = _t1659
                if !isnothing(deconstruct_result979)
                    unwrapped980 = deconstruct_result979
                    pretty_int_type(pp, unwrapped980)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1660 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1660 = nothing
                    end
                    deconstruct_result977 = _t1660
                    if !isnothing(deconstruct_result977)
                        unwrapped978 = deconstruct_result977
                        pretty_float_type(pp, unwrapped978)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1661 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1661 = nothing
                        end
                        deconstruct_result975 = _t1661
                        if !isnothing(deconstruct_result975)
                            unwrapped976 = deconstruct_result975
                            pretty_uint128_type(pp, unwrapped976)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1662 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1662 = nothing
                            end
                            deconstruct_result973 = _t1662
                            if !isnothing(deconstruct_result973)
                                unwrapped974 = deconstruct_result973
                                pretty_int128_type(pp, unwrapped974)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1663 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1663 = nothing
                                end
                                deconstruct_result971 = _t1663
                                if !isnothing(deconstruct_result971)
                                    unwrapped972 = deconstruct_result971
                                    pretty_date_type(pp, unwrapped972)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1664 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1664 = nothing
                                    end
                                    deconstruct_result969 = _t1664
                                    if !isnothing(deconstruct_result969)
                                        unwrapped970 = deconstruct_result969
                                        pretty_datetime_type(pp, unwrapped970)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1665 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1665 = nothing
                                        end
                                        deconstruct_result967 = _t1665
                                        if !isnothing(deconstruct_result967)
                                            unwrapped968 = deconstruct_result967
                                            pretty_missing_type(pp, unwrapped968)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1666 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1666 = nothing
                                            end
                                            deconstruct_result965 = _t1666
                                            if !isnothing(deconstruct_result965)
                                                unwrapped966 = deconstruct_result965
                                                pretty_decimal_type(pp, unwrapped966)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1667 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1667 = nothing
                                                end
                                                deconstruct_result963 = _t1667
                                                if !isnothing(deconstruct_result963)
                                                    unwrapped964 = deconstruct_result963
                                                    pretty_boolean_type(pp, unwrapped964)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1668 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1668 = nothing
                                                    end
                                                    deconstruct_result961 = _t1668
                                                    if !isnothing(deconstruct_result961)
                                                        unwrapped962 = deconstruct_result961
                                                        pretty_int32_type(pp, unwrapped962)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1669 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1669 = nothing
                                                        end
                                                        deconstruct_result959 = _t1669
                                                        if !isnothing(deconstruct_result959)
                                                            unwrapped960 = deconstruct_result959
                                                            pretty_float32_type(pp, unwrapped960)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1670 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1670 = nothing
                                                            end
                                                            deconstruct_result957 = _t1670
                                                            if !isnothing(deconstruct_result957)
                                                                unwrapped958 = deconstruct_result957
                                                                pretty_uint32_type(pp, unwrapped958)
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
    fields986 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields987 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields988 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields989 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields990 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields991 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields992 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields993 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields994 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat999 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat999)
        write(pp, flat999)
        return nothing
    else
        _dollar_dollar = msg
        fields995 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields996 = fields995
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field997 = unwrapped_fields996[1]
        write(pp, string(field997))
        newline(pp)
        field998 = unwrapped_fields996[2]
        write(pp, string(field998))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields1000 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields1001 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields1002 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields1003 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1007 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1007)
        write(pp, flat1007)
        return nothing
    else
        fields1004 = msg
        write(pp, "|")
        if !isempty(fields1004)
            write(pp, " ")
            for (i1671, elem1005) in enumerate(fields1004)
                i1006 = i1671 - 1
                if (i1006 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1005)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1034 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1034)
        write(pp, flat1034)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1672 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1672 = nothing
        end
        deconstruct_result1032 = _t1672
        if !isnothing(deconstruct_result1032)
            unwrapped1033 = deconstruct_result1032
            pretty_true(pp, unwrapped1033)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1673 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1673 = nothing
            end
            deconstruct_result1030 = _t1673
            if !isnothing(deconstruct_result1030)
                unwrapped1031 = deconstruct_result1030
                pretty_false(pp, unwrapped1031)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1674 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1674 = nothing
                end
                deconstruct_result1028 = _t1674
                if !isnothing(deconstruct_result1028)
                    unwrapped1029 = deconstruct_result1028
                    pretty_exists(pp, unwrapped1029)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1675 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1675 = nothing
                    end
                    deconstruct_result1026 = _t1675
                    if !isnothing(deconstruct_result1026)
                        unwrapped1027 = deconstruct_result1026
                        pretty_reduce(pp, unwrapped1027)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1676 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1676 = nothing
                        end
                        deconstruct_result1024 = _t1676
                        if !isnothing(deconstruct_result1024)
                            unwrapped1025 = deconstruct_result1024
                            pretty_conjunction(pp, unwrapped1025)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1677 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1677 = nothing
                            end
                            deconstruct_result1022 = _t1677
                            if !isnothing(deconstruct_result1022)
                                unwrapped1023 = deconstruct_result1022
                                pretty_disjunction(pp, unwrapped1023)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1678 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1678 = nothing
                                end
                                deconstruct_result1020 = _t1678
                                if !isnothing(deconstruct_result1020)
                                    unwrapped1021 = deconstruct_result1020
                                    pretty_not(pp, unwrapped1021)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1679 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1679 = nothing
                                    end
                                    deconstruct_result1018 = _t1679
                                    if !isnothing(deconstruct_result1018)
                                        unwrapped1019 = deconstruct_result1018
                                        pretty_ffi(pp, unwrapped1019)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1680 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1680 = nothing
                                        end
                                        deconstruct_result1016 = _t1680
                                        if !isnothing(deconstruct_result1016)
                                            unwrapped1017 = deconstruct_result1016
                                            pretty_atom(pp, unwrapped1017)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1681 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1681 = nothing
                                            end
                                            deconstruct_result1014 = _t1681
                                            if !isnothing(deconstruct_result1014)
                                                unwrapped1015 = deconstruct_result1014
                                                pretty_pragma(pp, unwrapped1015)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1682 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1682 = nothing
                                                end
                                                deconstruct_result1012 = _t1682
                                                if !isnothing(deconstruct_result1012)
                                                    unwrapped1013 = deconstruct_result1012
                                                    pretty_primitive(pp, unwrapped1013)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1683 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1683 = nothing
                                                    end
                                                    deconstruct_result1010 = _t1683
                                                    if !isnothing(deconstruct_result1010)
                                                        unwrapped1011 = deconstruct_result1010
                                                        pretty_rel_atom(pp, unwrapped1011)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1684 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1684 = nothing
                                                        end
                                                        deconstruct_result1008 = _t1684
                                                        if !isnothing(deconstruct_result1008)
                                                            unwrapped1009 = deconstruct_result1008
                                                            pretty_cast(pp, unwrapped1009)
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
    fields1035 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1036 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1041 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1041)
        write(pp, flat1041)
        return nothing
    else
        _dollar_dollar = msg
        _t1685 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1037 = (_t1685, _dollar_dollar.body.value,)
        unwrapped_fields1038 = fields1037
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1039 = unwrapped_fields1038[1]
        pretty_bindings(pp, field1039)
        newline(pp)
        field1040 = unwrapped_fields1038[2]
        pretty_formula(pp, field1040)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1047 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1047)
        write(pp, flat1047)
        return nothing
    else
        _dollar_dollar = msg
        fields1042 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1043 = fields1042
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1044 = unwrapped_fields1043[1]
        pretty_abstraction(pp, field1044)
        newline(pp)
        field1045 = unwrapped_fields1043[2]
        pretty_abstraction(pp, field1045)
        newline(pp)
        field1046 = unwrapped_fields1043[3]
        pretty_terms(pp, field1046)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1051 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1051)
        write(pp, flat1051)
        return nothing
    else
        fields1048 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1048)
            newline(pp)
            for (i1686, elem1049) in enumerate(fields1048)
                i1050 = i1686 - 1
                if (i1050 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1049)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1056 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1056)
        write(pp, flat1056)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1687 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1687 = nothing
        end
        deconstruct_result1054 = _t1687
        if !isnothing(deconstruct_result1054)
            unwrapped1055 = deconstruct_result1054
            pretty_var(pp, unwrapped1055)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1688 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1688 = nothing
            end
            deconstruct_result1052 = _t1688
            if !isnothing(deconstruct_result1052)
                unwrapped1053 = deconstruct_result1052
                pretty_value(pp, unwrapped1053)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1059 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1059)
        write(pp, flat1059)
        return nothing
    else
        _dollar_dollar = msg
        fields1057 = _dollar_dollar.name
        unwrapped_fields1058 = fields1057
        write(pp, unwrapped_fields1058)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1085 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1085)
        write(pp, flat1085)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1689 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1689 = nothing
        end
        deconstruct_result1083 = _t1689
        if !isnothing(deconstruct_result1083)
            unwrapped1084 = deconstruct_result1083
            pretty_date(pp, unwrapped1084)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1690 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1690 = nothing
            end
            deconstruct_result1081 = _t1690
            if !isnothing(deconstruct_result1081)
                unwrapped1082 = deconstruct_result1081
                pretty_datetime(pp, unwrapped1082)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1691 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1691 = nothing
                end
                deconstruct_result1079 = _t1691
                if !isnothing(deconstruct_result1079)
                    unwrapped1080 = deconstruct_result1079
                    write(pp, format_string(pp, unwrapped1080))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1692 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1692 = nothing
                    end
                    deconstruct_result1077 = _t1692
                    if !isnothing(deconstruct_result1077)
                        unwrapped1078 = deconstruct_result1077
                        write(pp, format_int32(pp, unwrapped1078))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1693 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1693 = nothing
                        end
                        deconstruct_result1075 = _t1693
                        if !isnothing(deconstruct_result1075)
                            unwrapped1076 = deconstruct_result1075
                            write(pp, format_int(pp, unwrapped1076))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1694 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1694 = nothing
                            end
                            deconstruct_result1073 = _t1694
                            if !isnothing(deconstruct_result1073)
                                unwrapped1074 = deconstruct_result1073
                                write(pp, format_float32(pp, unwrapped1074))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1695 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1695 = nothing
                                end
                                deconstruct_result1071 = _t1695
                                if !isnothing(deconstruct_result1071)
                                    unwrapped1072 = deconstruct_result1071
                                    write(pp, format_float(pp, unwrapped1072))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1696 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1696 = nothing
                                    end
                                    deconstruct_result1069 = _t1696
                                    if !isnothing(deconstruct_result1069)
                                        unwrapped1070 = deconstruct_result1069
                                        write(pp, format_uint32(pp, unwrapped1070))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1697 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1697 = nothing
                                        end
                                        deconstruct_result1067 = _t1697
                                        if !isnothing(deconstruct_result1067)
                                            unwrapped1068 = deconstruct_result1067
                                            write(pp, format_uint128(pp, unwrapped1068))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1698 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1698 = nothing
                                            end
                                            deconstruct_result1065 = _t1698
                                            if !isnothing(deconstruct_result1065)
                                                unwrapped1066 = deconstruct_result1065
                                                write(pp, format_int128(pp, unwrapped1066))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1699 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1699 = nothing
                                                end
                                                deconstruct_result1063 = _t1699
                                                if !isnothing(deconstruct_result1063)
                                                    unwrapped1064 = deconstruct_result1063
                                                    write(pp, format_decimal(pp, unwrapped1064))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1700 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1700 = nothing
                                                    end
                                                    deconstruct_result1061 = _t1700
                                                    if !isnothing(deconstruct_result1061)
                                                        unwrapped1062 = deconstruct_result1061
                                                        pretty_boolean_value(pp, unwrapped1062)
                                                    else
                                                        fields1060 = msg
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
    flat1091 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1091)
        write(pp, flat1091)
        return nothing
    else
        _dollar_dollar = msg
        fields1086 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1087 = fields1086
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1088 = unwrapped_fields1087[1]
        write(pp, format_int(pp, field1088))
        newline(pp)
        field1089 = unwrapped_fields1087[2]
        write(pp, format_int(pp, field1089))
        newline(pp)
        field1090 = unwrapped_fields1087[3]
        write(pp, format_int(pp, field1090))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1102 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1102)
        write(pp, flat1102)
        return nothing
    else
        _dollar_dollar = msg
        fields1092 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1093 = fields1092
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1094 = unwrapped_fields1093[1]
        write(pp, format_int(pp, field1094))
        newline(pp)
        field1095 = unwrapped_fields1093[2]
        write(pp, format_int(pp, field1095))
        newline(pp)
        field1096 = unwrapped_fields1093[3]
        write(pp, format_int(pp, field1096))
        newline(pp)
        field1097 = unwrapped_fields1093[4]
        write(pp, format_int(pp, field1097))
        newline(pp)
        field1098 = unwrapped_fields1093[5]
        write(pp, format_int(pp, field1098))
        newline(pp)
        field1099 = unwrapped_fields1093[6]
        write(pp, format_int(pp, field1099))
        field1100 = unwrapped_fields1093[7]
        if !isnothing(field1100)
            newline(pp)
            opt_val1101 = field1100
            write(pp, format_int(pp, opt_val1101))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1107 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1107)
        write(pp, flat1107)
        return nothing
    else
        _dollar_dollar = msg
        fields1103 = _dollar_dollar.args
        unwrapped_fields1104 = fields1103
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1104)
            newline(pp)
            for (i1701, elem1105) in enumerate(unwrapped_fields1104)
                i1106 = i1701 - 1
                if (i1106 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1105)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1112 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1112)
        write(pp, flat1112)
        return nothing
    else
        _dollar_dollar = msg
        fields1108 = _dollar_dollar.args
        unwrapped_fields1109 = fields1108
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1109)
            newline(pp)
            for (i1702, elem1110) in enumerate(unwrapped_fields1109)
                i1111 = i1702 - 1
                if (i1111 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1110)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1115 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1115)
        write(pp, flat1115)
        return nothing
    else
        _dollar_dollar = msg
        fields1113 = _dollar_dollar.arg
        unwrapped_fields1114 = fields1113
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1114)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1121 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1121)
        write(pp, flat1121)
        return nothing
    else
        _dollar_dollar = msg
        fields1116 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1117 = fields1116
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1118 = unwrapped_fields1117[1]
        pretty_name(pp, field1118)
        newline(pp)
        field1119 = unwrapped_fields1117[2]
        pretty_ffi_args(pp, field1119)
        newline(pp)
        field1120 = unwrapped_fields1117[3]
        pretty_terms(pp, field1120)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1123 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1123)
        write(pp, flat1123)
        return nothing
    else
        fields1122 = msg
        write(pp, ":")
        write(pp, fields1122)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1127 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1127)
        write(pp, flat1127)
        return nothing
    else
        fields1124 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1124)
            newline(pp)
            for (i1703, elem1125) in enumerate(fields1124)
                i1126 = i1703 - 1
                if (i1126 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1125)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1134 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1134)
        write(pp, flat1134)
        return nothing
    else
        _dollar_dollar = msg
        fields1128 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1129 = fields1128
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1130 = unwrapped_fields1129[1]
        pretty_relation_id(pp, field1130)
        field1131 = unwrapped_fields1129[2]
        if !isempty(field1131)
            newline(pp)
            for (i1704, elem1132) in enumerate(field1131)
                i1133 = i1704 - 1
                if (i1133 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1132)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1141 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1141)
        write(pp, flat1141)
        return nothing
    else
        _dollar_dollar = msg
        fields1135 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1136 = fields1135
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1137 = unwrapped_fields1136[1]
        pretty_name(pp, field1137)
        field1138 = unwrapped_fields1136[2]
        if !isempty(field1138)
            newline(pp)
            for (i1705, elem1139) in enumerate(field1138)
                i1140 = i1705 - 1
                if (i1140 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1139)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1157 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1157)
        write(pp, flat1157)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1706 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1706 = nothing
        end
        guard_result1156 = _t1706
        if !isnothing(guard_result1156)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1707 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1707 = nothing
            end
            guard_result1155 = _t1707
            if !isnothing(guard_result1155)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1708 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1708 = nothing
                end
                guard_result1154 = _t1708
                if !isnothing(guard_result1154)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1709 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1709 = nothing
                    end
                    guard_result1153 = _t1709
                    if !isnothing(guard_result1153)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1710 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1710 = nothing
                        end
                        guard_result1152 = _t1710
                        if !isnothing(guard_result1152)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1711 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1711 = nothing
                            end
                            guard_result1151 = _t1711
                            if !isnothing(guard_result1151)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1712 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1712 = nothing
                                end
                                guard_result1150 = _t1712
                                if !isnothing(guard_result1150)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1713 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1713 = nothing
                                    end
                                    guard_result1149 = _t1713
                                    if !isnothing(guard_result1149)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1714 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1714 = nothing
                                        end
                                        guard_result1148 = _t1714
                                        if !isnothing(guard_result1148)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1142 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1143 = fields1142
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1144 = unwrapped_fields1143[1]
                                            pretty_name(pp, field1144)
                                            field1145 = unwrapped_fields1143[2]
                                            if !isempty(field1145)
                                                newline(pp)
                                                for (i1715, elem1146) in enumerate(field1145)
                                                    i1147 = i1715 - 1
                                                    if (i1147 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1146)
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
    flat1162 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1162)
        write(pp, flat1162)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1716 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1716 = nothing
        end
        fields1158 = _t1716
        unwrapped_fields1159 = fields1158
        write(pp, "(=")
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

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1167 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1717 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1717 = nothing
        end
        fields1163 = _t1717
        unwrapped_fields1164 = fields1163
        write(pp, "(<")
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

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1172 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1172)
        write(pp, flat1172)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1718 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1718 = nothing
        end
        fields1168 = _t1718
        unwrapped_fields1169 = fields1168
        write(pp, "(<=")
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

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1177 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1177)
        write(pp, flat1177)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1719 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1719 = nothing
        end
        fields1173 = _t1719
        unwrapped_fields1174 = fields1173
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1175 = unwrapped_fields1174[1]
        pretty_term(pp, field1175)
        newline(pp)
        field1176 = unwrapped_fields1174[2]
        pretty_term(pp, field1176)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1182 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1182)
        write(pp, flat1182)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1720 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1720 = nothing
        end
        fields1178 = _t1720
        unwrapped_fields1179 = fields1178
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1180 = unwrapped_fields1179[1]
        pretty_term(pp, field1180)
        newline(pp)
        field1181 = unwrapped_fields1179[2]
        pretty_term(pp, field1181)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1188 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1188)
        write(pp, flat1188)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1721 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1721 = nothing
        end
        fields1183 = _t1721
        unwrapped_fields1184 = fields1183
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1185 = unwrapped_fields1184[1]
        pretty_term(pp, field1185)
        newline(pp)
        field1186 = unwrapped_fields1184[2]
        pretty_term(pp, field1186)
        newline(pp)
        field1187 = unwrapped_fields1184[3]
        pretty_term(pp, field1187)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1194 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1194)
        write(pp, flat1194)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1722 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1722 = nothing
        end
        fields1189 = _t1722
        unwrapped_fields1190 = fields1189
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1191 = unwrapped_fields1190[1]
        pretty_term(pp, field1191)
        newline(pp)
        field1192 = unwrapped_fields1190[2]
        pretty_term(pp, field1192)
        newline(pp)
        field1193 = unwrapped_fields1190[3]
        pretty_term(pp, field1193)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1200 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1200)
        write(pp, flat1200)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1723 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1723 = nothing
        end
        fields1195 = _t1723
        unwrapped_fields1196 = fields1195
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1197 = unwrapped_fields1196[1]
        pretty_term(pp, field1197)
        newline(pp)
        field1198 = unwrapped_fields1196[2]
        pretty_term(pp, field1198)
        newline(pp)
        field1199 = unwrapped_fields1196[3]
        pretty_term(pp, field1199)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1206 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1206)
        write(pp, flat1206)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1724 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1724 = nothing
        end
        fields1201 = _t1724
        unwrapped_fields1202 = fields1201
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1203 = unwrapped_fields1202[1]
        pretty_term(pp, field1203)
        newline(pp)
        field1204 = unwrapped_fields1202[2]
        pretty_term(pp, field1204)
        newline(pp)
        field1205 = unwrapped_fields1202[3]
        pretty_term(pp, field1205)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1211 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1211)
        write(pp, flat1211)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1725 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1725 = nothing
        end
        deconstruct_result1209 = _t1725
        if !isnothing(deconstruct_result1209)
            unwrapped1210 = deconstruct_result1209
            pretty_specialized_value(pp, unwrapped1210)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1726 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1726 = nothing
            end
            deconstruct_result1207 = _t1726
            if !isnothing(deconstruct_result1207)
                unwrapped1208 = deconstruct_result1207
                pretty_term(pp, unwrapped1208)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1213 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1213)
        write(pp, flat1213)
        return nothing
    else
        fields1212 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1212)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1220 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        _dollar_dollar = msg
        fields1214 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1215 = fields1214
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1216 = unwrapped_fields1215[1]
        pretty_name(pp, field1216)
        field1217 = unwrapped_fields1215[2]
        if !isempty(field1217)
            newline(pp)
            for (i1727, elem1218) in enumerate(field1217)
                i1219 = i1727 - 1
                if (i1219 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1218)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1225 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1225)
        write(pp, flat1225)
        return nothing
    else
        _dollar_dollar = msg
        fields1221 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1222 = fields1221
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1223 = unwrapped_fields1222[1]
        pretty_term(pp, field1223)
        newline(pp)
        field1224 = unwrapped_fields1222[2]
        pretty_term(pp, field1224)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1229 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1229)
        write(pp, flat1229)
        return nothing
    else
        fields1226 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1226)
            newline(pp)
            for (i1728, elem1227) in enumerate(fields1226)
                i1228 = i1728 - 1
                if (i1228 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1227)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1236 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1236)
        write(pp, flat1236)
        return nothing
    else
        _dollar_dollar = msg
        fields1230 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1231 = fields1230
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1232 = unwrapped_fields1231[1]
        pretty_name(pp, field1232)
        field1233 = unwrapped_fields1231[2]
        if !isempty(field1233)
            newline(pp)
            for (i1729, elem1234) in enumerate(field1233)
                i1235 = i1729 - 1
                if (i1235 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1234)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1245 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1245)
        write(pp, flat1245)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1730 = _dollar_dollar.attrs
        else
            _t1730 = nothing
        end
        fields1237 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1730,)
        unwrapped_fields1238 = fields1237
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1239 = unwrapped_fields1238[1]
        if !isempty(field1239)
            newline(pp)
            for (i1731, elem1240) in enumerate(field1239)
                i1241 = i1731 - 1
                if (i1241 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1240)
            end
        end
        newline(pp)
        field1242 = unwrapped_fields1238[2]
        pretty_script(pp, field1242)
        field1243 = unwrapped_fields1238[3]
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

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1250 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1250)
        write(pp, flat1250)
        return nothing
    else
        _dollar_dollar = msg
        fields1246 = _dollar_dollar.constructs
        unwrapped_fields1247 = fields1246
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1247)
            newline(pp)
            for (i1732, elem1248) in enumerate(unwrapped_fields1247)
                i1249 = i1732 - 1
                if (i1249 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1248)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1255 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1255)
        write(pp, flat1255)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1733 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1733 = nothing
        end
        deconstruct_result1253 = _t1733
        if !isnothing(deconstruct_result1253)
            unwrapped1254 = deconstruct_result1253
            pretty_loop(pp, unwrapped1254)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1734 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1734 = nothing
            end
            deconstruct_result1251 = _t1734
            if !isnothing(deconstruct_result1251)
                unwrapped1252 = deconstruct_result1251
                pretty_instruction(pp, unwrapped1252)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1262 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1262)
        write(pp, flat1262)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1735 = _dollar_dollar.attrs
        else
            _t1735 = nothing
        end
        fields1256 = (_dollar_dollar.init, _dollar_dollar.body, _t1735,)
        unwrapped_fields1257 = fields1256
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1258 = unwrapped_fields1257[1]
        pretty_init(pp, field1258)
        newline(pp)
        field1259 = unwrapped_fields1257[2]
        pretty_script(pp, field1259)
        field1260 = unwrapped_fields1257[3]
        if !isnothing(field1260)
            newline(pp)
            opt_val1261 = field1260
            pretty_attrs(pp, opt_val1261)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1266 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1266)
        write(pp, flat1266)
        return nothing
    else
        fields1263 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1263)
            newline(pp)
            for (i1736, elem1264) in enumerate(fields1263)
                i1265 = i1736 - 1
                if (i1265 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1264)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1277 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1277)
        write(pp, flat1277)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1737 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1737 = nothing
        end
        deconstruct_result1275 = _t1737
        if !isnothing(deconstruct_result1275)
            unwrapped1276 = deconstruct_result1275
            pretty_assign(pp, unwrapped1276)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1738 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1738 = nothing
            end
            deconstruct_result1273 = _t1738
            if !isnothing(deconstruct_result1273)
                unwrapped1274 = deconstruct_result1273
                pretty_upsert(pp, unwrapped1274)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1739 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1739 = nothing
                end
                deconstruct_result1271 = _t1739
                if !isnothing(deconstruct_result1271)
                    unwrapped1272 = deconstruct_result1271
                    pretty_break(pp, unwrapped1272)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1740 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1740 = nothing
                    end
                    deconstruct_result1269 = _t1740
                    if !isnothing(deconstruct_result1269)
                        unwrapped1270 = deconstruct_result1269
                        pretty_monoid_def(pp, unwrapped1270)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1741 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1741 = nothing
                        end
                        deconstruct_result1267 = _t1741
                        if !isnothing(deconstruct_result1267)
                            unwrapped1268 = deconstruct_result1267
                            pretty_monus_def(pp, unwrapped1268)
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
    flat1284 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1284)
        write(pp, flat1284)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1742 = _dollar_dollar.attrs
        else
            _t1742 = nothing
        end
        fields1278 = (_dollar_dollar.name, _dollar_dollar.body, _t1742,)
        unwrapped_fields1279 = fields1278
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1280 = unwrapped_fields1279[1]
        pretty_relation_id(pp, field1280)
        newline(pp)
        field1281 = unwrapped_fields1279[2]
        pretty_abstraction(pp, field1281)
        field1282 = unwrapped_fields1279[3]
        if !isnothing(field1282)
            newline(pp)
            opt_val1283 = field1282
            pretty_attrs(pp, opt_val1283)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1291 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1291)
        write(pp, flat1291)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1743 = _dollar_dollar.attrs
        else
            _t1743 = nothing
        end
        fields1285 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1743,)
        unwrapped_fields1286 = fields1285
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1287 = unwrapped_fields1286[1]
        pretty_relation_id(pp, field1287)
        newline(pp)
        field1288 = unwrapped_fields1286[2]
        pretty_abstraction_with_arity(pp, field1288)
        field1289 = unwrapped_fields1286[3]
        if !isnothing(field1289)
            newline(pp)
            opt_val1290 = field1289
            pretty_attrs(pp, opt_val1290)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1296 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1296)
        write(pp, flat1296)
        return nothing
    else
        _dollar_dollar = msg
        _t1744 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1292 = (_t1744, _dollar_dollar[1].value,)
        unwrapped_fields1293 = fields1292
        write(pp, "(")
        indent!(pp)
        field1294 = unwrapped_fields1293[1]
        pretty_bindings(pp, field1294)
        newline(pp)
        field1295 = unwrapped_fields1293[2]
        pretty_formula(pp, field1295)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1303 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1303)
        write(pp, flat1303)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1745 = _dollar_dollar.attrs
        else
            _t1745 = nothing
        end
        fields1297 = (_dollar_dollar.name, _dollar_dollar.body, _t1745,)
        unwrapped_fields1298 = fields1297
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1299 = unwrapped_fields1298[1]
        pretty_relation_id(pp, field1299)
        newline(pp)
        field1300 = unwrapped_fields1298[2]
        pretty_abstraction(pp, field1300)
        field1301 = unwrapped_fields1298[3]
        if !isnothing(field1301)
            newline(pp)
            opt_val1302 = field1301
            pretty_attrs(pp, opt_val1302)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1311 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1311)
        write(pp, flat1311)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1746 = _dollar_dollar.attrs
        else
            _t1746 = nothing
        end
        fields1304 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1746,)
        unwrapped_fields1305 = fields1304
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1306 = unwrapped_fields1305[1]
        pretty_monoid(pp, field1306)
        newline(pp)
        field1307 = unwrapped_fields1305[2]
        pretty_relation_id(pp, field1307)
        newline(pp)
        field1308 = unwrapped_fields1305[3]
        pretty_abstraction_with_arity(pp, field1308)
        field1309 = unwrapped_fields1305[4]
        if !isnothing(field1309)
            newline(pp)
            opt_val1310 = field1309
            pretty_attrs(pp, opt_val1310)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1320 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1320)
        write(pp, flat1320)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1747 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1747 = nothing
        end
        deconstruct_result1318 = _t1747
        if !isnothing(deconstruct_result1318)
            unwrapped1319 = deconstruct_result1318
            pretty_or_monoid(pp, unwrapped1319)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1748 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1748 = nothing
            end
            deconstruct_result1316 = _t1748
            if !isnothing(deconstruct_result1316)
                unwrapped1317 = deconstruct_result1316
                pretty_min_monoid(pp, unwrapped1317)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1749 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1749 = nothing
                end
                deconstruct_result1314 = _t1749
                if !isnothing(deconstruct_result1314)
                    unwrapped1315 = deconstruct_result1314
                    pretty_max_monoid(pp, unwrapped1315)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1750 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1750 = nothing
                    end
                    deconstruct_result1312 = _t1750
                    if !isnothing(deconstruct_result1312)
                        unwrapped1313 = deconstruct_result1312
                        pretty_sum_monoid(pp, unwrapped1313)
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
    fields1321 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1324 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1324)
        write(pp, flat1324)
        return nothing
    else
        _dollar_dollar = msg
        fields1322 = _dollar_dollar.var"#type"
        unwrapped_fields1323 = fields1322
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1323)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1327 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1327)
        write(pp, flat1327)
        return nothing
    else
        _dollar_dollar = msg
        fields1325 = _dollar_dollar.var"#type"
        unwrapped_fields1326 = fields1325
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1326)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1330 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1330)
        write(pp, flat1330)
        return nothing
    else
        _dollar_dollar = msg
        fields1328 = _dollar_dollar.var"#type"
        unwrapped_fields1329 = fields1328
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1329)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1338 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1338)
        write(pp, flat1338)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1751 = _dollar_dollar.attrs
        else
            _t1751 = nothing
        end
        fields1331 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1751,)
        unwrapped_fields1332 = fields1331
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1333 = unwrapped_fields1332[1]
        pretty_monoid(pp, field1333)
        newline(pp)
        field1334 = unwrapped_fields1332[2]
        pretty_relation_id(pp, field1334)
        newline(pp)
        field1335 = unwrapped_fields1332[3]
        pretty_abstraction_with_arity(pp, field1335)
        field1336 = unwrapped_fields1332[4]
        if !isnothing(field1336)
            newline(pp)
            opt_val1337 = field1336
            pretty_attrs(pp, opt_val1337)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1345 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1345)
        write(pp, flat1345)
        return nothing
    else
        _dollar_dollar = msg
        fields1339 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1340 = fields1339
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1341 = unwrapped_fields1340[1]
        pretty_relation_id(pp, field1341)
        newline(pp)
        field1342 = unwrapped_fields1340[2]
        pretty_abstraction(pp, field1342)
        newline(pp)
        field1343 = unwrapped_fields1340[3]
        pretty_functional_dependency_keys(pp, field1343)
        newline(pp)
        field1344 = unwrapped_fields1340[4]
        pretty_functional_dependency_values(pp, field1344)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1349 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1349)
        write(pp, flat1349)
        return nothing
    else
        fields1346 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1346)
            newline(pp)
            for (i1752, elem1347) in enumerate(fields1346)
                i1348 = i1752 - 1
                if (i1348 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1347)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1353 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1353)
        write(pp, flat1353)
        return nothing
    else
        fields1350 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1350)
            newline(pp)
            for (i1753, elem1351) in enumerate(fields1350)
                i1352 = i1753 - 1
                if (i1352 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1351)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1362 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1362)
        write(pp, flat1362)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1754 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1754 = nothing
        end
        deconstruct_result1360 = _t1754
        if !isnothing(deconstruct_result1360)
            unwrapped1361 = deconstruct_result1360
            pretty_edb(pp, unwrapped1361)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1755 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1755 = nothing
            end
            deconstruct_result1358 = _t1755
            if !isnothing(deconstruct_result1358)
                unwrapped1359 = deconstruct_result1358
                pretty_betree_relation(pp, unwrapped1359)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1756 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1756 = nothing
                end
                deconstruct_result1356 = _t1756
                if !isnothing(deconstruct_result1356)
                    unwrapped1357 = deconstruct_result1356
                    pretty_csv_data(pp, unwrapped1357)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1757 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1757 = nothing
                    end
                    deconstruct_result1354 = _t1757
                    if !isnothing(deconstruct_result1354)
                        unwrapped1355 = deconstruct_result1354
                        pretty_iceberg_data(pp, unwrapped1355)
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
    flat1368 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1368)
        write(pp, flat1368)
        return nothing
    else
        _dollar_dollar = msg
        fields1363 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1364 = fields1363
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1365 = unwrapped_fields1364[1]
        pretty_relation_id(pp, field1365)
        newline(pp)
        field1366 = unwrapped_fields1364[2]
        pretty_edb_path(pp, field1366)
        newline(pp)
        field1367 = unwrapped_fields1364[3]
        pretty_edb_types(pp, field1367)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1372 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1372)
        write(pp, flat1372)
        return nothing
    else
        fields1369 = msg
        write(pp, "[")
        indent!(pp)
        for (i1758, elem1370) in enumerate(fields1369)
            i1371 = i1758 - 1
            if (i1371 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1370))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1376 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        fields1373 = msg
        write(pp, "[")
        indent!(pp)
        for (i1759, elem1374) in enumerate(fields1373)
            i1375 = i1759 - 1
            if (i1375 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1374)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1381 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1381)
        write(pp, flat1381)
        return nothing
    else
        _dollar_dollar = msg
        fields1377 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1378 = fields1377
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1379 = unwrapped_fields1378[1]
        pretty_relation_id(pp, field1379)
        newline(pp)
        field1380 = unwrapped_fields1378[2]
        pretty_betree_info(pp, field1380)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1387 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1387)
        write(pp, flat1387)
        return nothing
    else
        _dollar_dollar = msg
        _t1760 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1382 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1760,)
        unwrapped_fields1383 = fields1382
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1384 = unwrapped_fields1383[1]
        pretty_betree_info_key_types(pp, field1384)
        newline(pp)
        field1385 = unwrapped_fields1383[2]
        pretty_betree_info_value_types(pp, field1385)
        newline(pp)
        field1386 = unwrapped_fields1383[3]
        pretty_config_dict(pp, field1386)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1391 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1391)
        write(pp, flat1391)
        return nothing
    else
        fields1388 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1388)
            newline(pp)
            for (i1761, elem1389) in enumerate(fields1388)
                i1390 = i1761 - 1
                if (i1390 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1389)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1395 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1395)
        write(pp, flat1395)
        return nothing
    else
        fields1392 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1392)
            newline(pp)
            for (i1762, elem1393) in enumerate(fields1392)
                i1394 = i1762 - 1
                if (i1394 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1393)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1402 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1402)
        write(pp, flat1402)
        return nothing
    else
        _dollar_dollar = msg
        fields1396 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1397 = fields1396
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1398 = unwrapped_fields1397[1]
        pretty_csvlocator(pp, field1398)
        newline(pp)
        field1399 = unwrapped_fields1397[2]
        pretty_csv_config(pp, field1399)
        newline(pp)
        field1400 = unwrapped_fields1397[3]
        pretty_gnf_columns(pp, field1400)
        newline(pp)
        field1401 = unwrapped_fields1397[4]
        pretty_csv_asof(pp, field1401)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1409 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1409)
        write(pp, flat1409)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1763 = _dollar_dollar.paths
        else
            _t1763 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1764 = String(copy(_dollar_dollar.inline_data))
        else
            _t1764 = nothing
        end
        fields1403 = (_t1763, _t1764,)
        unwrapped_fields1404 = fields1403
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1405 = unwrapped_fields1404[1]
        if !isnothing(field1405)
            newline(pp)
            opt_val1406 = field1405
            pretty_csv_locator_paths(pp, opt_val1406)
        end
        field1407 = unwrapped_fields1404[2]
        if !isnothing(field1407)
            newline(pp)
            opt_val1408 = field1407
            pretty_csv_locator_inline_data(pp, opt_val1408)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1413 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1413)
        write(pp, flat1413)
        return nothing
    else
        fields1410 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1410)
            newline(pp)
            for (i1765, elem1411) in enumerate(fields1410)
                i1412 = i1765 - 1
                if (i1412 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1411))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1415 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1415)
        write(pp, flat1415)
        return nothing
    else
        fields1414 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1414))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1421 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1421)
        write(pp, flat1421)
        return nothing
    else
        _dollar_dollar = msg
        _t1766 = deconstruct_csv_config(pp, _dollar_dollar)
        _t1767 = deconstruct_csv_storage_integration_optional(pp, _dollar_dollar)
        fields1416 = (_t1766, _t1767,)
        unwrapped_fields1417 = fields1416
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1418 = unwrapped_fields1417[1]
        pretty_config_dict(pp, field1418)
        field1419 = unwrapped_fields1417[2]
        if !isnothing(field1419)
            newline(pp)
            opt_val1420 = field1419
            pretty__storage_integration(pp, opt_val1420)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty__storage_integration(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat1423 = try_flat(pp, msg, pretty__storage_integration)
    if !isnothing(flat1423)
        write(pp, flat1423)
        return nothing
    else
        fields1422 = msg
        write(pp, "(storage_integration")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, fields1422)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1427 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1427)
        write(pp, flat1427)
        return nothing
    else
        fields1424 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1424)
            newline(pp)
            for (i1768, elem1425) in enumerate(fields1424)
                i1426 = i1768 - 1
                if (i1426 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1425)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1436 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1436)
        write(pp, flat1436)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1769 = _dollar_dollar.target_id
        else
            _t1769 = nothing
        end
        fields1428 = (_dollar_dollar.column_path, _t1769, _dollar_dollar.types,)
        unwrapped_fields1429 = fields1428
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1430 = unwrapped_fields1429[1]
        pretty_gnf_column_path(pp, field1430)
        field1431 = unwrapped_fields1429[2]
        if !isnothing(field1431)
            newline(pp)
            opt_val1432 = field1431
            pretty_relation_id(pp, opt_val1432)
        end
        newline(pp)
        write(pp, "[")
        field1433 = unwrapped_fields1429[3]
        for (i1770, elem1434) in enumerate(field1433)
            i1435 = i1770 - 1
            if (i1435 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1434)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1443 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1443)
        write(pp, flat1443)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1771 = _dollar_dollar[1]
        else
            _t1771 = nothing
        end
        deconstruct_result1441 = _t1771
        if !isnothing(deconstruct_result1441)
            unwrapped1442 = deconstruct_result1441
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1442))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1772 = _dollar_dollar
            else
                _t1772 = nothing
            end
            deconstruct_result1437 = _t1772
            if !isnothing(deconstruct_result1437)
                unwrapped1438 = deconstruct_result1437
                write(pp, "[")
                indent!(pp)
                for (i1773, elem1439) in enumerate(unwrapped1438)
                    i1440 = i1773 - 1
                    if (i1440 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1439))
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
    flat1445 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1445)
        write(pp, flat1445)
        return nothing
    else
        fields1444 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1444))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1456 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1456)
        write(pp, flat1456)
        return nothing
    else
        _dollar_dollar = msg
        _t1774 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1775 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1446 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1774, _t1775, _dollar_dollar.returns_delta,)
        unwrapped_fields1447 = fields1446
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1448 = unwrapped_fields1447[1]
        pretty_iceberg_locator(pp, field1448)
        newline(pp)
        field1449 = unwrapped_fields1447[2]
        pretty_iceberg_catalog_config(pp, field1449)
        newline(pp)
        field1450 = unwrapped_fields1447[3]
        pretty_gnf_columns(pp, field1450)
        field1451 = unwrapped_fields1447[4]
        if !isnothing(field1451)
            newline(pp)
            opt_val1452 = field1451
            pretty_iceberg_from_snapshot(pp, opt_val1452)
        end
        field1453 = unwrapped_fields1447[5]
        if !isnothing(field1453)
            newline(pp)
            opt_val1454 = field1453
            pretty_iceberg_to_snapshot(pp, opt_val1454)
        end
        newline(pp)
        field1455 = unwrapped_fields1447[6]
        pretty_boolean_value(pp, field1455)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1462 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1462)
        write(pp, flat1462)
        return nothing
    else
        _dollar_dollar = msg
        fields1457 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1458 = fields1457
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1459 = unwrapped_fields1458[1]
        pretty_iceberg_locator_table_name(pp, field1459)
        newline(pp)
        field1460 = unwrapped_fields1458[2]
        pretty_iceberg_locator_namespace(pp, field1460)
        newline(pp)
        field1461 = unwrapped_fields1458[3]
        pretty_iceberg_locator_warehouse(pp, field1461)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1464 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1464)
        write(pp, flat1464)
        return nothing
    else
        fields1463 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1463))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1468 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1468)
        write(pp, flat1468)
        return nothing
    else
        fields1465 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1465)
            newline(pp)
            for (i1776, elem1466) in enumerate(fields1465)
                i1467 = i1776 - 1
                if (i1467 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1466))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1470 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1470)
        write(pp, flat1470)
        return nothing
    else
        fields1469 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1469))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1478 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1478)
        write(pp, flat1478)
        return nothing
    else
        _dollar_dollar = msg
        _t1777 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1471 = (_dollar_dollar.catalog_uri, _t1777, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1472 = fields1471
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1473 = unwrapped_fields1472[1]
        pretty_iceberg_catalog_uri(pp, field1473)
        field1474 = unwrapped_fields1472[2]
        if !isnothing(field1474)
            newline(pp)
            opt_val1475 = field1474
            pretty_iceberg_catalog_config_scope(pp, opt_val1475)
        end
        newline(pp)
        field1476 = unwrapped_fields1472[3]
        pretty_iceberg_properties(pp, field1476)
        newline(pp)
        field1477 = unwrapped_fields1472[4]
        pretty_iceberg_auth_properties(pp, field1477)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1480 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1480)
        write(pp, flat1480)
        return nothing
    else
        fields1479 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1479))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1482 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1482)
        write(pp, flat1482)
        return nothing
    else
        fields1481 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1481))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1486 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1486)
        write(pp, flat1486)
        return nothing
    else
        fields1483 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1483)
            newline(pp)
            for (i1778, elem1484) in enumerate(fields1483)
                i1485 = i1778 - 1
                if (i1485 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1484)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1491 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1491)
        write(pp, flat1491)
        return nothing
    else
        _dollar_dollar = msg
        fields1487 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1488 = fields1487
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1489 = unwrapped_fields1488[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1489))
        newline(pp)
        field1490 = unwrapped_fields1488[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1490))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1495 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1495)
        write(pp, flat1495)
        return nothing
    else
        fields1492 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1492)
            newline(pp)
            for (i1779, elem1493) in enumerate(fields1492)
                i1494 = i1779 - 1
                if (i1494 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1493)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1500 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1500)
        write(pp, flat1500)
        return nothing
    else
        _dollar_dollar = msg
        _t1780 = mask_secret_value(pp, _dollar_dollar)
        fields1496 = (_dollar_dollar[1], _t1780,)
        unwrapped_fields1497 = fields1496
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1498 = unwrapped_fields1497[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1498))
        newline(pp)
        field1499 = unwrapped_fields1497[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1499))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1502 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1502)
        write(pp, flat1502)
        return nothing
    else
        fields1501 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1501))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1504 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1504)
        write(pp, flat1504)
        return nothing
    else
        fields1503 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1503))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1507 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1507)
        write(pp, flat1507)
        return nothing
    else
        _dollar_dollar = msg
        fields1505 = _dollar_dollar.fragment_id
        unwrapped_fields1506 = fields1505
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1506)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1512 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1512)
        write(pp, flat1512)
        return nothing
    else
        _dollar_dollar = msg
        fields1508 = _dollar_dollar.relations
        unwrapped_fields1509 = fields1508
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1509)
            newline(pp)
            for (i1781, elem1510) in enumerate(unwrapped_fields1509)
                i1511 = i1781 - 1
                if (i1511 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1510)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1519 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1519)
        write(pp, flat1519)
        return nothing
    else
        _dollar_dollar = msg
        fields1513 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1514 = fields1513
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1515 = unwrapped_fields1514[1]
        pretty_edb_path(pp, field1515)
        field1516 = unwrapped_fields1514[2]
        if !isempty(field1516)
            newline(pp)
            for (i1782, elem1517) in enumerate(field1516)
                i1518 = i1782 - 1
                if (i1518 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1517)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1524 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1524)
        write(pp, flat1524)
        return nothing
    else
        _dollar_dollar = msg
        fields1520 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1521 = fields1520
        field1522 = unwrapped_fields1521[1]
        pretty_edb_path(pp, field1522)
        write(pp, " ")
        field1523 = unwrapped_fields1521[2]
        pretty_relation_id(pp, field1523)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1528 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1528)
        write(pp, flat1528)
        return nothing
    else
        fields1525 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1525)
            newline(pp)
            for (i1783, elem1526) in enumerate(fields1525)
                i1527 = i1783 - 1
                if (i1527 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1526)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1541 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1541)
        write(pp, flat1541)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1784 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1784 = nothing
        end
        deconstruct_result1539 = _t1784
        if !isnothing(deconstruct_result1539)
            unwrapped1540 = deconstruct_result1539
            pretty_demand(pp, unwrapped1540)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1785 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1785 = nothing
            end
            deconstruct_result1537 = _t1785
            if !isnothing(deconstruct_result1537)
                unwrapped1538 = deconstruct_result1537
                pretty_output(pp, unwrapped1538)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1786 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1786 = nothing
                end
                deconstruct_result1535 = _t1786
                if !isnothing(deconstruct_result1535)
                    unwrapped1536 = deconstruct_result1535
                    pretty_what_if(pp, unwrapped1536)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1787 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1787 = nothing
                    end
                    deconstruct_result1533 = _t1787
                    if !isnothing(deconstruct_result1533)
                        unwrapped1534 = deconstruct_result1533
                        pretty_abort(pp, unwrapped1534)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1788 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1788 = nothing
                        end
                        deconstruct_result1531 = _t1788
                        if !isnothing(deconstruct_result1531)
                            unwrapped1532 = deconstruct_result1531
                            pretty_export(pp, unwrapped1532)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("export_output"))
                                _t1789 = _get_oneof_field(_dollar_dollar, :export_output)
                            else
                                _t1789 = nothing
                            end
                            deconstruct_result1529 = _t1789
                            if !isnothing(deconstruct_result1529)
                                unwrapped1530 = deconstruct_result1529
                                pretty_export_output(pp, unwrapped1530)
                            else
                                throw(ParseError("No matching rule for read"))
                            end
                        end
                    end
                end
            end
        end
    end
    return nothing
end

function pretty_demand(pp::PrettyPrinter, msg::Proto.Demand)
    flat1544 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1544)
        write(pp, flat1544)
        return nothing
    else
        _dollar_dollar = msg
        fields1542 = _dollar_dollar.relation_id
        unwrapped_fields1543 = fields1542
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1543)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1549 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1549)
        write(pp, flat1549)
        return nothing
    else
        _dollar_dollar = msg
        fields1545 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1546 = fields1545
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1547 = unwrapped_fields1546[1]
        pretty_name(pp, field1547)
        newline(pp)
        field1548 = unwrapped_fields1546[2]
        pretty_relation_id(pp, field1548)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1554 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1554)
        write(pp, flat1554)
        return nothing
    else
        _dollar_dollar = msg
        fields1550 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1551 = fields1550
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1552 = unwrapped_fields1551[1]
        pretty_name(pp, field1552)
        newline(pp)
        field1553 = unwrapped_fields1551[2]
        pretty_epoch(pp, field1553)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1560 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1560)
        write(pp, flat1560)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1790 = _dollar_dollar.name
        else
            _t1790 = nothing
        end
        fields1555 = (_t1790, _dollar_dollar.relation_id,)
        unwrapped_fields1556 = fields1555
        write(pp, "(abort")
        indent_sexp!(pp)
        field1557 = unwrapped_fields1556[1]
        if !isnothing(field1557)
            newline(pp)
            opt_val1558 = field1557
            pretty_name(pp, opt_val1558)
        end
        newline(pp)
        field1559 = unwrapped_fields1556[2]
        pretty_relation_id(pp, field1559)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1565 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1565)
        write(pp, flat1565)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1791 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1791 = nothing
        end
        deconstruct_result1563 = _t1791
        if !isnothing(deconstruct_result1563)
            unwrapped1564 = deconstruct_result1563
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1564)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1792 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1792 = nothing
            end
            deconstruct_result1561 = _t1792
            if !isnothing(deconstruct_result1561)
                unwrapped1562 = deconstruct_result1561
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1562)
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
    flat1576 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1576)
        write(pp, flat1576)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1793 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1793 = nothing
        end
        deconstruct_result1571 = _t1793
        if !isnothing(deconstruct_result1571)
            unwrapped1572 = deconstruct_result1571
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1573 = unwrapped1572[1]
            pretty_export_csv_path(pp, field1573)
            newline(pp)
            field1574 = unwrapped1572[2]
            pretty_export_csv_source(pp, field1574)
            newline(pp)
            field1575 = unwrapped1572[3]
            pretty_csv_config(pp, field1575)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1795 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1794 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1795,)
            else
                _t1794 = nothing
            end
            deconstruct_result1566 = _t1794
            if !isnothing(deconstruct_result1566)
                unwrapped1567 = deconstruct_result1566
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1568 = unwrapped1567[1]
                pretty_export_csv_path(pp, field1568)
                newline(pp)
                field1569 = unwrapped1567[2]
                pretty_export_csv_columns_list(pp, field1569)
                newline(pp)
                field1570 = unwrapped1567[3]
                pretty_config_dict(pp, field1570)
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
    flat1578 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1578)
        write(pp, flat1578)
        return nothing
    else
        fields1577 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1577))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1585 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1585)
        write(pp, flat1585)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1796 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1796 = nothing
        end
        deconstruct_result1581 = _t1796
        if !isnothing(deconstruct_result1581)
            unwrapped1582 = deconstruct_result1581
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1582)
                newline(pp)
                for (i1797, elem1583) in enumerate(unwrapped1582)
                    i1584 = i1797 - 1
                    if (i1584 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1583)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1798 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1798 = nothing
            end
            deconstruct_result1579 = _t1798
            if !isnothing(deconstruct_result1579)
                unwrapped1580 = deconstruct_result1579
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1580)
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
    flat1590 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1590)
        write(pp, flat1590)
        return nothing
    else
        _dollar_dollar = msg
        fields1586 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1587 = fields1586
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1588 = unwrapped_fields1587[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1588))
        newline(pp)
        field1589 = unwrapped_fields1587[2]
        pretty_relation_id(pp, field1589)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1594 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1594)
        write(pp, flat1594)
        return nothing
    else
        fields1591 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1591)
            newline(pp)
            for (i1799, elem1592) in enumerate(fields1591)
                i1593 = i1799 - 1
                if (i1593 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1592)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1603 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1603)
        write(pp, flat1603)
        return nothing
    else
        _dollar_dollar = msg
        _t1800 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1595 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1800,)
        unwrapped_fields1596 = fields1595
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1597 = unwrapped_fields1596[1]
        pretty_iceberg_locator(pp, field1597)
        newline(pp)
        field1598 = unwrapped_fields1596[2]
        pretty_iceberg_catalog_config(pp, field1598)
        newline(pp)
        field1599 = unwrapped_fields1596[3]
        pretty_export_iceberg_table_def(pp, field1599)
        newline(pp)
        field1600 = unwrapped_fields1596[4]
        pretty_iceberg_table_properties(pp, field1600)
        field1601 = unwrapped_fields1596[5]
        if !isnothing(field1601)
            newline(pp)
            opt_val1602 = field1601
            pretty_config_dict(pp, opt_val1602)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1605 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1605)
        write(pp, flat1605)
        return nothing
    else
        fields1604 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1604)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1609 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1609)
        write(pp, flat1609)
        return nothing
    else
        fields1606 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1606)
            newline(pp)
            for (i1801, elem1607) in enumerate(fields1606)
                i1608 = i1801 - 1
                if (i1608 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1607)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_output(pp::PrettyPrinter, msg::Proto.ExportOutput)
    flat1612 = try_flat(pp, msg, pretty_export_output)
    if !isnothing(flat1612)
        write(pp, flat1612)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv"))
            _t1802 = _get_oneof_field(_dollar_dollar, :csv)
        else
            _t1802 = nothing
        end
        fields1610 = _t1802
        unwrapped_fields1611 = fields1610
        write(pp, "(export_output")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_output(pp, unwrapped_fields1611)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_output(pp::PrettyPrinter, msg::Proto.ExportCSVOutput)
    flat1617 = try_flat(pp, msg, pretty_export_csv_output)
    if !isnothing(flat1617)
        write(pp, flat1617)
        return nothing
    else
        _dollar_dollar = msg
        fields1613 = (_dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        unwrapped_fields1614 = fields1613
        write(pp, "(csv")
        indent_sexp!(pp)
        newline(pp)
        field1615 = unwrapped_fields1614[1]
        pretty_export_csv_source(pp, field1615)
        newline(pp)
        field1616 = unwrapped_fields1614[2]
        pretty_csv_config(pp, field1616)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1854, _rid) in enumerate(msg.ids)
        _idx = i1854 - 1
        newline(pp)
        write(pp, "(")
        _t1855 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1855)
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
    for (i1856, _elem) in enumerate(msg.keys)
        _idx = i1856 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1857, _elem) in enumerate(msg.values)
        _idx = i1857 - 1
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

function pretty_storage_integration(pp::PrettyPrinter, msg::Proto.StorageIntegration)
    write(pp, "(storage_integration")
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

function pretty_u_int128_value(pp::PrettyPrinter, msg::Proto.UInt128Value)
    write(pp, format_uint128(pp, msg))
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Proto.ExportCSVColumns)
    write(pp, "(export_csv_columns")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":columns (")
    for (i1858, _elem) in enumerate(msg.columns)
        _idx = i1858 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportOutput) = pretty_export_output(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportCSVOutput) = pretty_export_csv_output(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DebugInfo) = pretty_debug_info(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeConfig) = pretty_be_tree_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeLocator) = pretty_be_tree_locator(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DecimalValue) = pretty_decimal_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FunctionalDependency) = pretty_functional_dependency(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Int128Value) = pretty_int128_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MissingValue) = pretty_missing_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.StorageIntegration) = pretty_storage_integration(pp, x)
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
