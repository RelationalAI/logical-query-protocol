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

function deconstruct_relation_keys(pp::PrettyPrinter, msg::Proto.TargetRelations)::Tuple{Vector{Proto.NamedColumn}, Bool}
    return (msg.keys, msg.synthetic_key,)
end

function deconstruct_csv_data_columns_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Vector{Proto.GNFColumn}}
    if _has_proto_field(msg, Symbol("relations"))
        return nothing
    else
        _t1898 = nothing
    end
    return msg.columns
end

function deconstruct_csv_data_relations_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Proto.TargetRelations}
    if _has_proto_field(msg, Symbol("relations"))
        return msg.relations
    else
        _t1899 = nothing
    end
    return nothing
end

function deconstruct_export_csv_output_location(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Tuple{String, String}
    return (msg.path, msg.transaction_output_name,)
end

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1900 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1900
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1901 = Proto.Value(value=OneOf(:int_value, v))
    return _t1901
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1902 = Proto.Value(value=OneOf(:float_value, v))
    return _t1902
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1903 = Proto.Value(value=OneOf(:string_value, v))
    return _t1903
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1904 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1904
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1905 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1905
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1906 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1906,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1907 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1907,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1908 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1908,))
            end
        end
    end
    _t1909 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1909,))
    for pair in sort([(k, v) for (k, v) in msg.configuration_values])
        push!(result, pair)
    end
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1910 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1910,))
    _t1911 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1911,))
    if msg.new_line != ""
        _t1912 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1912,))
    end
    _t1913 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1913,))
    _t1914 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1914,))
    _t1915 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1915,))
    if msg.comment != ""
        _t1916 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1916,))
    end
    for missing_string in msg.missing_strings
        _t1917 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1917,))
    end
    _t1918 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1918,))
    _t1919 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1919,))
    _t1920 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1920,))
    if msg.partition_size_mb != 0
        _t1921 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1921,))
    end
    return sort(result)
end

function deconstruct_csv_storage_integration_optional(pp::PrettyPrinter, msg::Proto.CSVConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    if !_has_proto_field(msg, Symbol("storage_integration"))
        return nothing
    else
        _t1922 = nothing
    end
    si = msg.storage_integration
    result = Tuple{String, Proto.Value}[]
    if si.provider != ""
        _t1923 = _make_value_string(pp, si.provider)
        push!(result, ("provider", _t1923,))
    end
    if si.azure_sas_token != ""
        _t1924 = _make_value_string(pp, "***")
        push!(result, ("azure_sas_token", _t1924,))
    end
    if si.s3_region != ""
        _t1925 = _make_value_string(pp, si.s3_region)
        push!(result, ("s3_region", _t1925,))
    end
    if si.s3_access_key_id != ""
        _t1926 = _make_value_string(pp, "***")
        push!(result, ("s3_access_key_id", _t1926,))
    end
    if si.s3_secret_access_key != ""
        _t1927 = _make_value_string(pp, "***")
        push!(result, ("s3_secret_access_key", _t1927,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1928 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1928,))
    _t1929 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1929,))
    _t1930 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1930,))
    _t1931 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1931,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1932 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1932,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1933 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1933,))
        end
    end
    _t1934 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1934,))
    _t1935 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1935,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1936 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1936,))
    end
    if !isnothing(msg.compression)
        _t1937 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1937,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1938 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1938,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1939 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1939,))
    end
    if !isnothing(msg.syntax_delim)
        _t1940 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1940,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1941 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1941,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1942 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1942,))
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
        _t1943 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1944 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1945 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1946 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1946,))
    end
    if msg.target_file_size_bytes != 0
        _t1947 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1947,))
    end
    if msg.compression != ""
        _t1948 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1948,))
    end
    if length(result) == 0
        return nothing
    else
        _t1949 = nothing
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
        _t1950 = nothing
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
    flat859 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat859)
        write(pp, flat859)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1700 = _dollar_dollar.configure
        else
            _t1700 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1701 = _dollar_dollar.sync
        else
            _t1701 = nothing
        end
        fields850 = (_t1700, _t1701, _dollar_dollar.epochs,)
        unwrapped_fields851 = fields850
        write(pp, "(transaction")
        indent_sexp!(pp)
        field852 = unwrapped_fields851[1]
        if !isnothing(field852)
            newline(pp)
            opt_val853 = field852
            pretty_configure(pp, opt_val853)
        end
        field854 = unwrapped_fields851[2]
        if !isnothing(field854)
            newline(pp)
            opt_val855 = field854
            pretty_sync(pp, opt_val855)
        end
        field856 = unwrapped_fields851[3]
        if !isempty(field856)
            newline(pp)
            for (i1702, elem857) in enumerate(field856)
                i858 = i1702 - 1
                if (i858 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem857)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat862 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat862)
        write(pp, flat862)
        return nothing
    else
        _dollar_dollar = msg
        _t1703 = deconstruct_configure(pp, _dollar_dollar)
        fields860 = _t1703
        unwrapped_fields861 = fields860
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields861)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat866 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat866)
        write(pp, flat866)
        return nothing
    else
        fields863 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields863)
            newline(pp)
            for (i1704, elem864) in enumerate(fields863)
                i865 = i1704 - 1
                if (i865 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem864)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat871 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat871)
        write(pp, flat871)
        return nothing
    else
        _dollar_dollar = msg
        fields867 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields868 = fields867
        write(pp, ":")
        field869 = unwrapped_fields868[1]
        write(pp, field869)
        write(pp, " ")
        field870 = unwrapped_fields868[2]
        pretty_raw_value(pp, field870)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat897 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat897)
        write(pp, flat897)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1705 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1705 = nothing
        end
        deconstruct_result895 = _t1705
        if !isnothing(deconstruct_result895)
            unwrapped896 = deconstruct_result895
            pretty_raw_date(pp, unwrapped896)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1706 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1706 = nothing
            end
            deconstruct_result893 = _t1706
            if !isnothing(deconstruct_result893)
                unwrapped894 = deconstruct_result893
                pretty_raw_datetime(pp, unwrapped894)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1707 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1707 = nothing
                end
                deconstruct_result891 = _t1707
                if !isnothing(deconstruct_result891)
                    unwrapped892 = deconstruct_result891
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped892))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1708 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1708 = nothing
                    end
                    deconstruct_result889 = _t1708
                    if !isnothing(deconstruct_result889)
                        unwrapped890 = deconstruct_result889
                        write(pp, (string(Int64(unwrapped890)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1709 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1709 = nothing
                        end
                        deconstruct_result887 = _t1709
                        if !isnothing(deconstruct_result887)
                            unwrapped888 = deconstruct_result887
                            write(pp, string(unwrapped888))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1710 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1710 = nothing
                            end
                            deconstruct_result885 = _t1710
                            if !isnothing(deconstruct_result885)
                                unwrapped886 = deconstruct_result885
                                write(pp, format_float32_literal(unwrapped886))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1711 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1711 = nothing
                                end
                                deconstruct_result883 = _t1711
                                if !isnothing(deconstruct_result883)
                                    unwrapped884 = deconstruct_result883
                                    write(pp, lowercase(string(unwrapped884)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1712 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1712 = nothing
                                    end
                                    deconstruct_result881 = _t1712
                                    if !isnothing(deconstruct_result881)
                                        unwrapped882 = deconstruct_result881
                                        write(pp, (string(Int64(unwrapped882)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1713 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1713 = nothing
                                        end
                                        deconstruct_result879 = _t1713
                                        if !isnothing(deconstruct_result879)
                                            unwrapped880 = deconstruct_result879
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped880))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1714 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1714 = nothing
                                            end
                                            deconstruct_result877 = _t1714
                                            if !isnothing(deconstruct_result877)
                                                unwrapped878 = deconstruct_result877
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped878))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1715 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1715 = nothing
                                                end
                                                deconstruct_result875 = _t1715
                                                if !isnothing(deconstruct_result875)
                                                    unwrapped876 = deconstruct_result875
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped876))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1716 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1716 = nothing
                                                    end
                                                    deconstruct_result873 = _t1716
                                                    if !isnothing(deconstruct_result873)
                                                        unwrapped874 = deconstruct_result873
                                                        pretty_boolean_value(pp, unwrapped874)
                                                    else
                                                        fields872 = msg
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
    flat903 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat903)
        write(pp, flat903)
        return nothing
    else
        _dollar_dollar = msg
        fields898 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields899 = fields898
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field900 = unwrapped_fields899[1]
        write(pp, string(field900))
        newline(pp)
        field901 = unwrapped_fields899[2]
        write(pp, string(field901))
        newline(pp)
        field902 = unwrapped_fields899[3]
        write(pp, string(field902))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat914 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat914)
        write(pp, flat914)
        return nothing
    else
        _dollar_dollar = msg
        fields904 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields905 = fields904
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field906 = unwrapped_fields905[1]
        write(pp, string(field906))
        newline(pp)
        field907 = unwrapped_fields905[2]
        write(pp, string(field907))
        newline(pp)
        field908 = unwrapped_fields905[3]
        write(pp, string(field908))
        newline(pp)
        field909 = unwrapped_fields905[4]
        write(pp, string(field909))
        newline(pp)
        field910 = unwrapped_fields905[5]
        write(pp, string(field910))
        newline(pp)
        field911 = unwrapped_fields905[6]
        write(pp, string(field911))
        field912 = unwrapped_fields905[7]
        if !isnothing(field912)
            newline(pp)
            opt_val913 = field912
            write(pp, string(opt_val913))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1717 = ()
    else
        _t1717 = nothing
    end
    deconstruct_result917 = _t1717
    if !isnothing(deconstruct_result917)
        unwrapped918 = deconstruct_result917
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1718 = ()
        else
            _t1718 = nothing
        end
        deconstruct_result915 = _t1718
        if !isnothing(deconstruct_result915)
            unwrapped916 = deconstruct_result915
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat923 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat923)
        write(pp, flat923)
        return nothing
    else
        _dollar_dollar = msg
        fields919 = _dollar_dollar.fragments
        unwrapped_fields920 = fields919
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields920)
            newline(pp)
            for (i1719, elem921) in enumerate(unwrapped_fields920)
                i922 = i1719 - 1
                if (i922 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem921)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat926 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat926)
        write(pp, flat926)
        return nothing
    else
        _dollar_dollar = msg
        fields924 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields925 = fields924
        write(pp, ":")
        write(pp, unwrapped_fields925)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat933 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat933)
        write(pp, flat933)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1720 = _dollar_dollar.writes
        else
            _t1720 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1721 = _dollar_dollar.reads
        else
            _t1721 = nothing
        end
        fields927 = (_t1720, _t1721,)
        unwrapped_fields928 = fields927
        write(pp, "(epoch")
        indent_sexp!(pp)
        field929 = unwrapped_fields928[1]
        if !isnothing(field929)
            newline(pp)
            opt_val930 = field929
            pretty_epoch_writes(pp, opt_val930)
        end
        field931 = unwrapped_fields928[2]
        if !isnothing(field931)
            newline(pp)
            opt_val932 = field931
            pretty_epoch_reads(pp, opt_val932)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat937 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat937)
        write(pp, flat937)
        return nothing
    else
        fields934 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields934)
            newline(pp)
            for (i1722, elem935) in enumerate(fields934)
                i936 = i1722 - 1
                if (i936 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem935)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat946 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1723 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1723 = nothing
        end
        deconstruct_result944 = _t1723
        if !isnothing(deconstruct_result944)
            unwrapped945 = deconstruct_result944
            pretty_define(pp, unwrapped945)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1724 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1724 = nothing
            end
            deconstruct_result942 = _t1724
            if !isnothing(deconstruct_result942)
                unwrapped943 = deconstruct_result942
                pretty_undefine(pp, unwrapped943)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1725 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1725 = nothing
                end
                deconstruct_result940 = _t1725
                if !isnothing(deconstruct_result940)
                    unwrapped941 = deconstruct_result940
                    pretty_context(pp, unwrapped941)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1726 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1726 = nothing
                    end
                    deconstruct_result938 = _t1726
                    if !isnothing(deconstruct_result938)
                        unwrapped939 = deconstruct_result938
                        pretty_snapshot(pp, unwrapped939)
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
    flat949 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat949)
        write(pp, flat949)
        return nothing
    else
        _dollar_dollar = msg
        fields947 = _dollar_dollar.fragment
        unwrapped_fields948 = fields947
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields948)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat956 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat956)
        write(pp, flat956)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields950 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields951 = fields950
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field952 = unwrapped_fields951[1]
        pretty_new_fragment_id(pp, field952)
        field953 = unwrapped_fields951[2]
        if !isempty(field953)
            newline(pp)
            for (i1727, elem954) in enumerate(field953)
                i955 = i1727 - 1
                if (i955 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem954)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat958 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat958)
        write(pp, flat958)
        return nothing
    else
        fields957 = msg
        pretty_fragment_id(pp, fields957)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat967 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat967)
        write(pp, flat967)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1728 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1728 = nothing
        end
        deconstruct_result965 = _t1728
        if !isnothing(deconstruct_result965)
            unwrapped966 = deconstruct_result965
            pretty_def(pp, unwrapped966)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1729 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1729 = nothing
            end
            deconstruct_result963 = _t1729
            if !isnothing(deconstruct_result963)
                unwrapped964 = deconstruct_result963
                pretty_algorithm(pp, unwrapped964)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1730 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1730 = nothing
                end
                deconstruct_result961 = _t1730
                if !isnothing(deconstruct_result961)
                    unwrapped962 = deconstruct_result961
                    pretty_constraint(pp, unwrapped962)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1731 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1731 = nothing
                    end
                    deconstruct_result959 = _t1731
                    if !isnothing(deconstruct_result959)
                        unwrapped960 = deconstruct_result959
                        pretty_data(pp, unwrapped960)
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
    flat974 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat974)
        write(pp, flat974)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1732 = _dollar_dollar.attrs
        else
            _t1732 = nothing
        end
        fields968 = (_dollar_dollar.name, _dollar_dollar.body, _t1732,)
        unwrapped_fields969 = fields968
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field970 = unwrapped_fields969[1]
        pretty_relation_id(pp, field970)
        newline(pp)
        field971 = unwrapped_fields969[2]
        pretty_abstraction(pp, field971)
        field972 = unwrapped_fields969[3]
        if !isnothing(field972)
            newline(pp)
            opt_val973 = field972
            pretty_attrs(pp, opt_val973)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat979 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat979)
        write(pp, flat979)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1734 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1733 = _t1734
        else
            _t1733 = nothing
        end
        deconstruct_result977 = _t1733
        if !isnothing(deconstruct_result977)
            unwrapped978 = deconstruct_result977
            write(pp, ":")
            write(pp, unwrapped978)
        else
            _dollar_dollar = msg
            _t1735 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result975 = _t1735
            if !isnothing(deconstruct_result975)
                unwrapped976 = deconstruct_result975
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped976))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat984 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat984)
        write(pp, flat984)
        return nothing
    else
        _dollar_dollar = msg
        _t1736 = deconstruct_bindings(pp, _dollar_dollar)
        fields980 = (_t1736, _dollar_dollar.value,)
        unwrapped_fields981 = fields980
        write(pp, "(")
        indent!(pp)
        field982 = unwrapped_fields981[1]
        pretty_bindings(pp, field982)
        newline(pp)
        field983 = unwrapped_fields981[2]
        pretty_formula(pp, field983)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat992 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat992)
        write(pp, flat992)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1737 = _dollar_dollar[2]
        else
            _t1737 = nothing
        end
        fields985 = (_dollar_dollar[1], _t1737,)
        unwrapped_fields986 = fields985
        write(pp, "[")
        indent!(pp)
        field987 = unwrapped_fields986[1]
        for (i1738, elem988) in enumerate(field987)
            i989 = i1738 - 1
            if (i989 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem988)
        end
        field990 = unwrapped_fields986[2]
        if !isnothing(field990)
            newline(pp)
            opt_val991 = field990
            pretty_value_bindings(pp, opt_val991)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat997 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat997)
        write(pp, flat997)
        return nothing
    else
        _dollar_dollar = msg
        fields993 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields994 = fields993
        field995 = unwrapped_fields994[1]
        write(pp, field995)
        write(pp, "::")
        field996 = unwrapped_fields994[2]
        pretty_type(pp, field996)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat1026 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat1026)
        write(pp, flat1026)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1739 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1739 = nothing
        end
        deconstruct_result1024 = _t1739
        if !isnothing(deconstruct_result1024)
            unwrapped1025 = deconstruct_result1024
            pretty_unspecified_type(pp, unwrapped1025)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1740 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1740 = nothing
            end
            deconstruct_result1022 = _t1740
            if !isnothing(deconstruct_result1022)
                unwrapped1023 = deconstruct_result1022
                pretty_string_type(pp, unwrapped1023)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1741 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1741 = nothing
                end
                deconstruct_result1020 = _t1741
                if !isnothing(deconstruct_result1020)
                    unwrapped1021 = deconstruct_result1020
                    pretty_int_type(pp, unwrapped1021)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1742 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1742 = nothing
                    end
                    deconstruct_result1018 = _t1742
                    if !isnothing(deconstruct_result1018)
                        unwrapped1019 = deconstruct_result1018
                        pretty_float_type(pp, unwrapped1019)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1743 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1743 = nothing
                        end
                        deconstruct_result1016 = _t1743
                        if !isnothing(deconstruct_result1016)
                            unwrapped1017 = deconstruct_result1016
                            pretty_uint128_type(pp, unwrapped1017)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1744 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1744 = nothing
                            end
                            deconstruct_result1014 = _t1744
                            if !isnothing(deconstruct_result1014)
                                unwrapped1015 = deconstruct_result1014
                                pretty_int128_type(pp, unwrapped1015)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1745 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1745 = nothing
                                end
                                deconstruct_result1012 = _t1745
                                if !isnothing(deconstruct_result1012)
                                    unwrapped1013 = deconstruct_result1012
                                    pretty_date_type(pp, unwrapped1013)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1746 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1746 = nothing
                                    end
                                    deconstruct_result1010 = _t1746
                                    if !isnothing(deconstruct_result1010)
                                        unwrapped1011 = deconstruct_result1010
                                        pretty_datetime_type(pp, unwrapped1011)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1747 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1747 = nothing
                                        end
                                        deconstruct_result1008 = _t1747
                                        if !isnothing(deconstruct_result1008)
                                            unwrapped1009 = deconstruct_result1008
                                            pretty_missing_type(pp, unwrapped1009)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1748 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1748 = nothing
                                            end
                                            deconstruct_result1006 = _t1748
                                            if !isnothing(deconstruct_result1006)
                                                unwrapped1007 = deconstruct_result1006
                                                pretty_decimal_type(pp, unwrapped1007)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1749 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1749 = nothing
                                                end
                                                deconstruct_result1004 = _t1749
                                                if !isnothing(deconstruct_result1004)
                                                    unwrapped1005 = deconstruct_result1004
                                                    pretty_boolean_type(pp, unwrapped1005)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1750 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1750 = nothing
                                                    end
                                                    deconstruct_result1002 = _t1750
                                                    if !isnothing(deconstruct_result1002)
                                                        unwrapped1003 = deconstruct_result1002
                                                        pretty_int32_type(pp, unwrapped1003)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1751 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1751 = nothing
                                                        end
                                                        deconstruct_result1000 = _t1751
                                                        if !isnothing(deconstruct_result1000)
                                                            unwrapped1001 = deconstruct_result1000
                                                            pretty_float32_type(pp, unwrapped1001)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1752 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1752 = nothing
                                                            end
                                                            deconstruct_result998 = _t1752
                                                            if !isnothing(deconstruct_result998)
                                                                unwrapped999 = deconstruct_result998
                                                                pretty_uint32_type(pp, unwrapped999)
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
    fields1027 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields1028 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields1029 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields1030 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields1031 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields1032 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields1033 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields1034 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields1035 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat1040 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat1040)
        write(pp, flat1040)
        return nothing
    else
        _dollar_dollar = msg
        fields1036 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields1037 = fields1036
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field1038 = unwrapped_fields1037[1]
        write(pp, string(field1038))
        newline(pp)
        field1039 = unwrapped_fields1037[2]
        write(pp, string(field1039))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields1041 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields1042 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields1043 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields1044 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1048 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1048)
        write(pp, flat1048)
        return nothing
    else
        fields1045 = msg
        write(pp, "|")
        if !isempty(fields1045)
            write(pp, " ")
            for (i1753, elem1046) in enumerate(fields1045)
                i1047 = i1753 - 1
                if (i1047 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1046)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1075 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1075)
        write(pp, flat1075)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1754 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1754 = nothing
        end
        deconstruct_result1073 = _t1754
        if !isnothing(deconstruct_result1073)
            unwrapped1074 = deconstruct_result1073
            pretty_true(pp, unwrapped1074)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1755 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1755 = nothing
            end
            deconstruct_result1071 = _t1755
            if !isnothing(deconstruct_result1071)
                unwrapped1072 = deconstruct_result1071
                pretty_false(pp, unwrapped1072)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1756 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1756 = nothing
                end
                deconstruct_result1069 = _t1756
                if !isnothing(deconstruct_result1069)
                    unwrapped1070 = deconstruct_result1069
                    pretty_exists(pp, unwrapped1070)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1757 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1757 = nothing
                    end
                    deconstruct_result1067 = _t1757
                    if !isnothing(deconstruct_result1067)
                        unwrapped1068 = deconstruct_result1067
                        pretty_reduce(pp, unwrapped1068)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1758 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1758 = nothing
                        end
                        deconstruct_result1065 = _t1758
                        if !isnothing(deconstruct_result1065)
                            unwrapped1066 = deconstruct_result1065
                            pretty_conjunction(pp, unwrapped1066)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1759 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1759 = nothing
                            end
                            deconstruct_result1063 = _t1759
                            if !isnothing(deconstruct_result1063)
                                unwrapped1064 = deconstruct_result1063
                                pretty_disjunction(pp, unwrapped1064)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1760 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1760 = nothing
                                end
                                deconstruct_result1061 = _t1760
                                if !isnothing(deconstruct_result1061)
                                    unwrapped1062 = deconstruct_result1061
                                    pretty_not(pp, unwrapped1062)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1761 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1761 = nothing
                                    end
                                    deconstruct_result1059 = _t1761
                                    if !isnothing(deconstruct_result1059)
                                        unwrapped1060 = deconstruct_result1059
                                        pretty_ffi(pp, unwrapped1060)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1762 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1762 = nothing
                                        end
                                        deconstruct_result1057 = _t1762
                                        if !isnothing(deconstruct_result1057)
                                            unwrapped1058 = deconstruct_result1057
                                            pretty_atom(pp, unwrapped1058)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1763 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1763 = nothing
                                            end
                                            deconstruct_result1055 = _t1763
                                            if !isnothing(deconstruct_result1055)
                                                unwrapped1056 = deconstruct_result1055
                                                pretty_pragma(pp, unwrapped1056)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1764 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1764 = nothing
                                                end
                                                deconstruct_result1053 = _t1764
                                                if !isnothing(deconstruct_result1053)
                                                    unwrapped1054 = deconstruct_result1053
                                                    pretty_primitive(pp, unwrapped1054)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1765 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1765 = nothing
                                                    end
                                                    deconstruct_result1051 = _t1765
                                                    if !isnothing(deconstruct_result1051)
                                                        unwrapped1052 = deconstruct_result1051
                                                        pretty_rel_atom(pp, unwrapped1052)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1766 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1766 = nothing
                                                        end
                                                        deconstruct_result1049 = _t1766
                                                        if !isnothing(deconstruct_result1049)
                                                            unwrapped1050 = deconstruct_result1049
                                                            pretty_cast(pp, unwrapped1050)
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
    fields1076 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1077 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1082 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1082)
        write(pp, flat1082)
        return nothing
    else
        _dollar_dollar = msg
        _t1767 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1078 = (_t1767, _dollar_dollar.body.value,)
        unwrapped_fields1079 = fields1078
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1080 = unwrapped_fields1079[1]
        pretty_bindings(pp, field1080)
        newline(pp)
        field1081 = unwrapped_fields1079[2]
        pretty_formula(pp, field1081)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1088 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1088)
        write(pp, flat1088)
        return nothing
    else
        _dollar_dollar = msg
        fields1083 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1084 = fields1083
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1085 = unwrapped_fields1084[1]
        pretty_abstraction(pp, field1085)
        newline(pp)
        field1086 = unwrapped_fields1084[2]
        pretty_abstraction(pp, field1086)
        newline(pp)
        field1087 = unwrapped_fields1084[3]
        pretty_terms(pp, field1087)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1092 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        fields1089 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1089)
            newline(pp)
            for (i1768, elem1090) in enumerate(fields1089)
                i1091 = i1768 - 1
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

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1097 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1097)
        write(pp, flat1097)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1769 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1769 = nothing
        end
        deconstruct_result1095 = _t1769
        if !isnothing(deconstruct_result1095)
            unwrapped1096 = deconstruct_result1095
            pretty_var(pp, unwrapped1096)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1770 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1770 = nothing
            end
            deconstruct_result1093 = _t1770
            if !isnothing(deconstruct_result1093)
                unwrapped1094 = deconstruct_result1093
                pretty_value(pp, unwrapped1094)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1100 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1100)
        write(pp, flat1100)
        return nothing
    else
        _dollar_dollar = msg
        fields1098 = _dollar_dollar.name
        unwrapped_fields1099 = fields1098
        write(pp, unwrapped_fields1099)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1126 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1126)
        write(pp, flat1126)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1771 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1771 = nothing
        end
        deconstruct_result1124 = _t1771
        if !isnothing(deconstruct_result1124)
            unwrapped1125 = deconstruct_result1124
            pretty_date(pp, unwrapped1125)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1772 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1772 = nothing
            end
            deconstruct_result1122 = _t1772
            if !isnothing(deconstruct_result1122)
                unwrapped1123 = deconstruct_result1122
                pretty_datetime(pp, unwrapped1123)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1773 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1773 = nothing
                end
                deconstruct_result1120 = _t1773
                if !isnothing(deconstruct_result1120)
                    unwrapped1121 = deconstruct_result1120
                    write(pp, format_string(pp, unwrapped1121))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1774 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1774 = nothing
                    end
                    deconstruct_result1118 = _t1774
                    if !isnothing(deconstruct_result1118)
                        unwrapped1119 = deconstruct_result1118
                        write(pp, format_int32(pp, unwrapped1119))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1775 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1775 = nothing
                        end
                        deconstruct_result1116 = _t1775
                        if !isnothing(deconstruct_result1116)
                            unwrapped1117 = deconstruct_result1116
                            write(pp, format_int(pp, unwrapped1117))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1776 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1776 = nothing
                            end
                            deconstruct_result1114 = _t1776
                            if !isnothing(deconstruct_result1114)
                                unwrapped1115 = deconstruct_result1114
                                write(pp, format_float32(pp, unwrapped1115))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1777 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1777 = nothing
                                end
                                deconstruct_result1112 = _t1777
                                if !isnothing(deconstruct_result1112)
                                    unwrapped1113 = deconstruct_result1112
                                    write(pp, format_float(pp, unwrapped1113))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1778 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1778 = nothing
                                    end
                                    deconstruct_result1110 = _t1778
                                    if !isnothing(deconstruct_result1110)
                                        unwrapped1111 = deconstruct_result1110
                                        write(pp, format_uint32(pp, unwrapped1111))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1779 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1779 = nothing
                                        end
                                        deconstruct_result1108 = _t1779
                                        if !isnothing(deconstruct_result1108)
                                            unwrapped1109 = deconstruct_result1108
                                            write(pp, format_uint128(pp, unwrapped1109))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1780 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1780 = nothing
                                            end
                                            deconstruct_result1106 = _t1780
                                            if !isnothing(deconstruct_result1106)
                                                unwrapped1107 = deconstruct_result1106
                                                write(pp, format_int128(pp, unwrapped1107))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1781 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1781 = nothing
                                                end
                                                deconstruct_result1104 = _t1781
                                                if !isnothing(deconstruct_result1104)
                                                    unwrapped1105 = deconstruct_result1104
                                                    write(pp, format_decimal(pp, unwrapped1105))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1782 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1782 = nothing
                                                    end
                                                    deconstruct_result1102 = _t1782
                                                    if !isnothing(deconstruct_result1102)
                                                        unwrapped1103 = deconstruct_result1102
                                                        pretty_boolean_value(pp, unwrapped1103)
                                                    else
                                                        fields1101 = msg
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
    flat1132 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1132)
        write(pp, flat1132)
        return nothing
    else
        _dollar_dollar = msg
        fields1127 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1128 = fields1127
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1129 = unwrapped_fields1128[1]
        write(pp, format_int(pp, field1129))
        newline(pp)
        field1130 = unwrapped_fields1128[2]
        write(pp, format_int(pp, field1130))
        newline(pp)
        field1131 = unwrapped_fields1128[3]
        write(pp, format_int(pp, field1131))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1143 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1143)
        write(pp, flat1143)
        return nothing
    else
        _dollar_dollar = msg
        fields1133 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1134 = fields1133
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1135 = unwrapped_fields1134[1]
        write(pp, format_int(pp, field1135))
        newline(pp)
        field1136 = unwrapped_fields1134[2]
        write(pp, format_int(pp, field1136))
        newline(pp)
        field1137 = unwrapped_fields1134[3]
        write(pp, format_int(pp, field1137))
        newline(pp)
        field1138 = unwrapped_fields1134[4]
        write(pp, format_int(pp, field1138))
        newline(pp)
        field1139 = unwrapped_fields1134[5]
        write(pp, format_int(pp, field1139))
        newline(pp)
        field1140 = unwrapped_fields1134[6]
        write(pp, format_int(pp, field1140))
        field1141 = unwrapped_fields1134[7]
        if !isnothing(field1141)
            newline(pp)
            opt_val1142 = field1141
            write(pp, format_int(pp, opt_val1142))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1148 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1148)
        write(pp, flat1148)
        return nothing
    else
        _dollar_dollar = msg
        fields1144 = _dollar_dollar.args
        unwrapped_fields1145 = fields1144
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1145)
            newline(pp)
            for (i1783, elem1146) in enumerate(unwrapped_fields1145)
                i1147 = i1783 - 1
                if (i1147 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1146)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1153 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1153)
        write(pp, flat1153)
        return nothing
    else
        _dollar_dollar = msg
        fields1149 = _dollar_dollar.args
        unwrapped_fields1150 = fields1149
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1150)
            newline(pp)
            for (i1784, elem1151) in enumerate(unwrapped_fields1150)
                i1152 = i1784 - 1
                if (i1152 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1151)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1156 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1156)
        write(pp, flat1156)
        return nothing
    else
        _dollar_dollar = msg
        fields1154 = _dollar_dollar.arg
        unwrapped_fields1155 = fields1154
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1155)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1162 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1162)
        write(pp, flat1162)
        return nothing
    else
        _dollar_dollar = msg
        fields1157 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1158 = fields1157
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1159 = unwrapped_fields1158[1]
        pretty_name(pp, field1159)
        newline(pp)
        field1160 = unwrapped_fields1158[2]
        pretty_ffi_args(pp, field1160)
        newline(pp)
        field1161 = unwrapped_fields1158[3]
        pretty_terms(pp, field1161)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1164 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1164)
        write(pp, flat1164)
        return nothing
    else
        fields1163 = msg
        write(pp, ":")
        write(pp, fields1163)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1168 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1168)
        write(pp, flat1168)
        return nothing
    else
        fields1165 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1165)
            newline(pp)
            for (i1785, elem1166) in enumerate(fields1165)
                i1167 = i1785 - 1
                if (i1167 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1166)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1175 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1175)
        write(pp, flat1175)
        return nothing
    else
        _dollar_dollar = msg
        fields1169 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1170 = fields1169
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1171 = unwrapped_fields1170[1]
        pretty_relation_id(pp, field1171)
        field1172 = unwrapped_fields1170[2]
        if !isempty(field1172)
            newline(pp)
            for (i1786, elem1173) in enumerate(field1172)
                i1174 = i1786 - 1
                if (i1174 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1173)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1182 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1182)
        write(pp, flat1182)
        return nothing
    else
        _dollar_dollar = msg
        fields1176 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1177 = fields1176
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1178 = unwrapped_fields1177[1]
        pretty_name(pp, field1178)
        field1179 = unwrapped_fields1177[2]
        if !isempty(field1179)
            newline(pp)
            for (i1787, elem1180) in enumerate(field1179)
                i1181 = i1787 - 1
                if (i1181 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1180)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1198 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1198)
        write(pp, flat1198)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1788 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1788 = nothing
        end
        guard_result1197 = _t1788
        if !isnothing(guard_result1197)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1789 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1789 = nothing
            end
            guard_result1196 = _t1789
            if !isnothing(guard_result1196)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1790 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1790 = nothing
                end
                guard_result1195 = _t1790
                if !isnothing(guard_result1195)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1791 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1791 = nothing
                    end
                    guard_result1194 = _t1791
                    if !isnothing(guard_result1194)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1792 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1792 = nothing
                        end
                        guard_result1193 = _t1792
                        if !isnothing(guard_result1193)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1793 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1793 = nothing
                            end
                            guard_result1192 = _t1793
                            if !isnothing(guard_result1192)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1794 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1794 = nothing
                                end
                                guard_result1191 = _t1794
                                if !isnothing(guard_result1191)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1795 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1795 = nothing
                                    end
                                    guard_result1190 = _t1795
                                    if !isnothing(guard_result1190)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1796 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1796 = nothing
                                        end
                                        guard_result1189 = _t1796
                                        if !isnothing(guard_result1189)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1183 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1184 = fields1183
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1185 = unwrapped_fields1184[1]
                                            pretty_name(pp, field1185)
                                            field1186 = unwrapped_fields1184[2]
                                            if !isempty(field1186)
                                                newline(pp)
                                                for (i1797, elem1187) in enumerate(field1186)
                                                    i1188 = i1797 - 1
                                                    if (i1188 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1187)
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
    flat1203 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1203)
        write(pp, flat1203)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1798 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1798 = nothing
        end
        fields1199 = _t1798
        unwrapped_fields1200 = fields1199
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1201 = unwrapped_fields1200[1]
        pretty_term(pp, field1201)
        newline(pp)
        field1202 = unwrapped_fields1200[2]
        pretty_term(pp, field1202)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1208 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1208)
        write(pp, flat1208)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1799 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1799 = nothing
        end
        fields1204 = _t1799
        unwrapped_fields1205 = fields1204
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1206 = unwrapped_fields1205[1]
        pretty_term(pp, field1206)
        newline(pp)
        field1207 = unwrapped_fields1205[2]
        pretty_term(pp, field1207)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1213 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1213)
        write(pp, flat1213)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1800 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1800 = nothing
        end
        fields1209 = _t1800
        unwrapped_fields1210 = fields1209
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1211 = unwrapped_fields1210[1]
        pretty_term(pp, field1211)
        newline(pp)
        field1212 = unwrapped_fields1210[2]
        pretty_term(pp, field1212)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1218 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1218)
        write(pp, flat1218)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1801 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1801 = nothing
        end
        fields1214 = _t1801
        unwrapped_fields1215 = fields1214
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1216 = unwrapped_fields1215[1]
        pretty_term(pp, field1216)
        newline(pp)
        field1217 = unwrapped_fields1215[2]
        pretty_term(pp, field1217)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1223 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1223)
        write(pp, flat1223)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1802 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1802 = nothing
        end
        fields1219 = _t1802
        unwrapped_fields1220 = fields1219
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1221 = unwrapped_fields1220[1]
        pretty_term(pp, field1221)
        newline(pp)
        field1222 = unwrapped_fields1220[2]
        pretty_term(pp, field1222)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1229 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1229)
        write(pp, flat1229)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1803 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1803 = nothing
        end
        fields1224 = _t1803
        unwrapped_fields1225 = fields1224
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1226 = unwrapped_fields1225[1]
        pretty_term(pp, field1226)
        newline(pp)
        field1227 = unwrapped_fields1225[2]
        pretty_term(pp, field1227)
        newline(pp)
        field1228 = unwrapped_fields1225[3]
        pretty_term(pp, field1228)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1235 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1235)
        write(pp, flat1235)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1804 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1804 = nothing
        end
        fields1230 = _t1804
        unwrapped_fields1231 = fields1230
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1232 = unwrapped_fields1231[1]
        pretty_term(pp, field1232)
        newline(pp)
        field1233 = unwrapped_fields1231[2]
        pretty_term(pp, field1233)
        newline(pp)
        field1234 = unwrapped_fields1231[3]
        pretty_term(pp, field1234)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1241 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1241)
        write(pp, flat1241)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1805 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1805 = nothing
        end
        fields1236 = _t1805
        unwrapped_fields1237 = fields1236
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1238 = unwrapped_fields1237[1]
        pretty_term(pp, field1238)
        newline(pp)
        field1239 = unwrapped_fields1237[2]
        pretty_term(pp, field1239)
        newline(pp)
        field1240 = unwrapped_fields1237[3]
        pretty_term(pp, field1240)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1247 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1247)
        write(pp, flat1247)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1806 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1806 = nothing
        end
        fields1242 = _t1806
        unwrapped_fields1243 = fields1242
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1244 = unwrapped_fields1243[1]
        pretty_term(pp, field1244)
        newline(pp)
        field1245 = unwrapped_fields1243[2]
        pretty_term(pp, field1245)
        newline(pp)
        field1246 = unwrapped_fields1243[3]
        pretty_term(pp, field1246)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1252 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1252)
        write(pp, flat1252)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1807 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1807 = nothing
        end
        deconstruct_result1250 = _t1807
        if !isnothing(deconstruct_result1250)
            unwrapped1251 = deconstruct_result1250
            pretty_specialized_value(pp, unwrapped1251)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1808 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1808 = nothing
            end
            deconstruct_result1248 = _t1808
            if !isnothing(deconstruct_result1248)
                unwrapped1249 = deconstruct_result1248
                pretty_term(pp, unwrapped1249)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1254 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1254)
        write(pp, flat1254)
        return nothing
    else
        fields1253 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1253)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1261 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1261)
        write(pp, flat1261)
        return nothing
    else
        _dollar_dollar = msg
        fields1255 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1256 = fields1255
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1257 = unwrapped_fields1256[1]
        pretty_name(pp, field1257)
        field1258 = unwrapped_fields1256[2]
        if !isempty(field1258)
            newline(pp)
            for (i1809, elem1259) in enumerate(field1258)
                i1260 = i1809 - 1
                if (i1260 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1259)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1266 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1266)
        write(pp, flat1266)
        return nothing
    else
        _dollar_dollar = msg
        fields1262 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1263 = fields1262
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1264 = unwrapped_fields1263[1]
        pretty_term(pp, field1264)
        newline(pp)
        field1265 = unwrapped_fields1263[2]
        pretty_term(pp, field1265)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1270 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1270)
        write(pp, flat1270)
        return nothing
    else
        fields1267 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1267)
            newline(pp)
            for (i1810, elem1268) in enumerate(fields1267)
                i1269 = i1810 - 1
                if (i1269 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1268)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1277 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1277)
        write(pp, flat1277)
        return nothing
    else
        _dollar_dollar = msg
        fields1271 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1272 = fields1271
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1273 = unwrapped_fields1272[1]
        pretty_name(pp, field1273)
        field1274 = unwrapped_fields1272[2]
        if !isempty(field1274)
            newline(pp)
            for (i1811, elem1275) in enumerate(field1274)
                i1276 = i1811 - 1
                if (i1276 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1275)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1286 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1286)
        write(pp, flat1286)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1812 = _dollar_dollar.attrs
        else
            _t1812 = nothing
        end
        fields1278 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1812,)
        unwrapped_fields1279 = fields1278
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1280 = unwrapped_fields1279[1]
        if !isempty(field1280)
            newline(pp)
            for (i1813, elem1281) in enumerate(field1280)
                i1282 = i1813 - 1
                if (i1282 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1281)
            end
        end
        newline(pp)
        field1283 = unwrapped_fields1279[2]
        pretty_script(pp, field1283)
        field1284 = unwrapped_fields1279[3]
        if !isnothing(field1284)
            newline(pp)
            opt_val1285 = field1284
            pretty_attrs(pp, opt_val1285)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1291 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1291)
        write(pp, flat1291)
        return nothing
    else
        _dollar_dollar = msg
        fields1287 = _dollar_dollar.constructs
        unwrapped_fields1288 = fields1287
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1288)
            newline(pp)
            for (i1814, elem1289) in enumerate(unwrapped_fields1288)
                i1290 = i1814 - 1
                if (i1290 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1289)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1296 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1296)
        write(pp, flat1296)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1815 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1815 = nothing
        end
        deconstruct_result1294 = _t1815
        if !isnothing(deconstruct_result1294)
            unwrapped1295 = deconstruct_result1294
            pretty_loop(pp, unwrapped1295)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1816 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1816 = nothing
            end
            deconstruct_result1292 = _t1816
            if !isnothing(deconstruct_result1292)
                unwrapped1293 = deconstruct_result1292
                pretty_instruction(pp, unwrapped1293)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1303 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1303)
        write(pp, flat1303)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1817 = _dollar_dollar.attrs
        else
            _t1817 = nothing
        end
        fields1297 = (_dollar_dollar.init, _dollar_dollar.body, _t1817,)
        unwrapped_fields1298 = fields1297
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1299 = unwrapped_fields1298[1]
        pretty_init(pp, field1299)
        newline(pp)
        field1300 = unwrapped_fields1298[2]
        pretty_script(pp, field1300)
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

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1307 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1307)
        write(pp, flat1307)
        return nothing
    else
        fields1304 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1304)
            newline(pp)
            for (i1818, elem1305) in enumerate(fields1304)
                i1306 = i1818 - 1
                if (i1306 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1305)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1318 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1318)
        write(pp, flat1318)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1819 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1819 = nothing
        end
        deconstruct_result1316 = _t1819
        if !isnothing(deconstruct_result1316)
            unwrapped1317 = deconstruct_result1316
            pretty_assign(pp, unwrapped1317)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1820 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1820 = nothing
            end
            deconstruct_result1314 = _t1820
            if !isnothing(deconstruct_result1314)
                unwrapped1315 = deconstruct_result1314
                pretty_upsert(pp, unwrapped1315)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1821 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1821 = nothing
                end
                deconstruct_result1312 = _t1821
                if !isnothing(deconstruct_result1312)
                    unwrapped1313 = deconstruct_result1312
                    pretty_break(pp, unwrapped1313)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1822 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1822 = nothing
                    end
                    deconstruct_result1310 = _t1822
                    if !isnothing(deconstruct_result1310)
                        unwrapped1311 = deconstruct_result1310
                        pretty_monoid_def(pp, unwrapped1311)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1823 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1823 = nothing
                        end
                        deconstruct_result1308 = _t1823
                        if !isnothing(deconstruct_result1308)
                            unwrapped1309 = deconstruct_result1308
                            pretty_monus_def(pp, unwrapped1309)
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
    flat1325 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1325)
        write(pp, flat1325)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1824 = _dollar_dollar.attrs
        else
            _t1824 = nothing
        end
        fields1319 = (_dollar_dollar.name, _dollar_dollar.body, _t1824,)
        unwrapped_fields1320 = fields1319
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1321 = unwrapped_fields1320[1]
        pretty_relation_id(pp, field1321)
        newline(pp)
        field1322 = unwrapped_fields1320[2]
        pretty_abstraction(pp, field1322)
        field1323 = unwrapped_fields1320[3]
        if !isnothing(field1323)
            newline(pp)
            opt_val1324 = field1323
            pretty_attrs(pp, opt_val1324)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1332 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1332)
        write(pp, flat1332)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1825 = _dollar_dollar.attrs
        else
            _t1825 = nothing
        end
        fields1326 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1825,)
        unwrapped_fields1327 = fields1326
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1328 = unwrapped_fields1327[1]
        pretty_relation_id(pp, field1328)
        newline(pp)
        field1329 = unwrapped_fields1327[2]
        pretty_abstraction_with_arity(pp, field1329)
        field1330 = unwrapped_fields1327[3]
        if !isnothing(field1330)
            newline(pp)
            opt_val1331 = field1330
            pretty_attrs(pp, opt_val1331)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1337 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1337)
        write(pp, flat1337)
        return nothing
    else
        _dollar_dollar = msg
        _t1826 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1333 = (_t1826, _dollar_dollar[1].value,)
        unwrapped_fields1334 = fields1333
        write(pp, "(")
        indent!(pp)
        field1335 = unwrapped_fields1334[1]
        pretty_bindings(pp, field1335)
        newline(pp)
        field1336 = unwrapped_fields1334[2]
        pretty_formula(pp, field1336)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1344 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1344)
        write(pp, flat1344)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1827 = _dollar_dollar.attrs
        else
            _t1827 = nothing
        end
        fields1338 = (_dollar_dollar.name, _dollar_dollar.body, _t1827,)
        unwrapped_fields1339 = fields1338
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1340 = unwrapped_fields1339[1]
        pretty_relation_id(pp, field1340)
        newline(pp)
        field1341 = unwrapped_fields1339[2]
        pretty_abstraction(pp, field1341)
        field1342 = unwrapped_fields1339[3]
        if !isnothing(field1342)
            newline(pp)
            opt_val1343 = field1342
            pretty_attrs(pp, opt_val1343)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1352 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1352)
        write(pp, flat1352)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1828 = _dollar_dollar.attrs
        else
            _t1828 = nothing
        end
        fields1345 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1828,)
        unwrapped_fields1346 = fields1345
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1347 = unwrapped_fields1346[1]
        pretty_monoid(pp, field1347)
        newline(pp)
        field1348 = unwrapped_fields1346[2]
        pretty_relation_id(pp, field1348)
        newline(pp)
        field1349 = unwrapped_fields1346[3]
        pretty_abstraction_with_arity(pp, field1349)
        field1350 = unwrapped_fields1346[4]
        if !isnothing(field1350)
            newline(pp)
            opt_val1351 = field1350
            pretty_attrs(pp, opt_val1351)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1361 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1361)
        write(pp, flat1361)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1829 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1829 = nothing
        end
        deconstruct_result1359 = _t1829
        if !isnothing(deconstruct_result1359)
            unwrapped1360 = deconstruct_result1359
            pretty_or_monoid(pp, unwrapped1360)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1830 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1830 = nothing
            end
            deconstruct_result1357 = _t1830
            if !isnothing(deconstruct_result1357)
                unwrapped1358 = deconstruct_result1357
                pretty_min_monoid(pp, unwrapped1358)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1831 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1831 = nothing
                end
                deconstruct_result1355 = _t1831
                if !isnothing(deconstruct_result1355)
                    unwrapped1356 = deconstruct_result1355
                    pretty_max_monoid(pp, unwrapped1356)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1832 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1832 = nothing
                    end
                    deconstruct_result1353 = _t1832
                    if !isnothing(deconstruct_result1353)
                        unwrapped1354 = deconstruct_result1353
                        pretty_sum_monoid(pp, unwrapped1354)
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
    fields1362 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1365 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1365)
        write(pp, flat1365)
        return nothing
    else
        _dollar_dollar = msg
        fields1363 = _dollar_dollar.var"#type"
        unwrapped_fields1364 = fields1363
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1364)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1368 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1368)
        write(pp, flat1368)
        return nothing
    else
        _dollar_dollar = msg
        fields1366 = _dollar_dollar.var"#type"
        unwrapped_fields1367 = fields1366
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1367)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1371 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1371)
        write(pp, flat1371)
        return nothing
    else
        _dollar_dollar = msg
        fields1369 = _dollar_dollar.var"#type"
        unwrapped_fields1370 = fields1369
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1370)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1379 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1379)
        write(pp, flat1379)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1833 = _dollar_dollar.attrs
        else
            _t1833 = nothing
        end
        fields1372 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1833,)
        unwrapped_fields1373 = fields1372
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1374 = unwrapped_fields1373[1]
        pretty_monoid(pp, field1374)
        newline(pp)
        field1375 = unwrapped_fields1373[2]
        pretty_relation_id(pp, field1375)
        newline(pp)
        field1376 = unwrapped_fields1373[3]
        pretty_abstraction_with_arity(pp, field1376)
        field1377 = unwrapped_fields1373[4]
        if !isnothing(field1377)
            newline(pp)
            opt_val1378 = field1377
            pretty_attrs(pp, opt_val1378)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1386 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1386)
        write(pp, flat1386)
        return nothing
    else
        _dollar_dollar = msg
        fields1380 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1381 = fields1380
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1382 = unwrapped_fields1381[1]
        pretty_relation_id(pp, field1382)
        newline(pp)
        field1383 = unwrapped_fields1381[2]
        pretty_abstraction(pp, field1383)
        newline(pp)
        field1384 = unwrapped_fields1381[3]
        pretty_functional_dependency_keys(pp, field1384)
        newline(pp)
        field1385 = unwrapped_fields1381[4]
        pretty_functional_dependency_values(pp, field1385)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1390 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1390)
        write(pp, flat1390)
        return nothing
    else
        fields1387 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1387)
            newline(pp)
            for (i1834, elem1388) in enumerate(fields1387)
                i1389 = i1834 - 1
                if (i1389 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1388)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1394 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1394)
        write(pp, flat1394)
        return nothing
    else
        fields1391 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1391)
            newline(pp)
            for (i1835, elem1392) in enumerate(fields1391)
                i1393 = i1835 - 1
                if (i1393 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1392)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1403 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1403)
        write(pp, flat1403)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1836 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1836 = nothing
        end
        deconstruct_result1401 = _t1836
        if !isnothing(deconstruct_result1401)
            unwrapped1402 = deconstruct_result1401
            pretty_edb(pp, unwrapped1402)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1837 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1837 = nothing
            end
            deconstruct_result1399 = _t1837
            if !isnothing(deconstruct_result1399)
                unwrapped1400 = deconstruct_result1399
                pretty_betree_relation(pp, unwrapped1400)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1838 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1838 = nothing
                end
                deconstruct_result1397 = _t1838
                if !isnothing(deconstruct_result1397)
                    unwrapped1398 = deconstruct_result1397
                    pretty_csv_data(pp, unwrapped1398)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1839 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1839 = nothing
                    end
                    deconstruct_result1395 = _t1839
                    if !isnothing(deconstruct_result1395)
                        unwrapped1396 = deconstruct_result1395
                        pretty_iceberg_data(pp, unwrapped1396)
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
    flat1409 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1409)
        write(pp, flat1409)
        return nothing
    else
        _dollar_dollar = msg
        fields1404 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1405 = fields1404
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1406 = unwrapped_fields1405[1]
        pretty_relation_id(pp, field1406)
        newline(pp)
        field1407 = unwrapped_fields1405[2]
        pretty_edb_path(pp, field1407)
        newline(pp)
        field1408 = unwrapped_fields1405[3]
        pretty_edb_types(pp, field1408)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1413 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1413)
        write(pp, flat1413)
        return nothing
    else
        fields1410 = msg
        write(pp, "[")
        indent!(pp)
        for (i1840, elem1411) in enumerate(fields1410)
            i1412 = i1840 - 1
            if (i1412 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1411))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1417 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1417)
        write(pp, flat1417)
        return nothing
    else
        fields1414 = msg
        write(pp, "[")
        indent!(pp)
        for (i1841, elem1415) in enumerate(fields1414)
            i1416 = i1841 - 1
            if (i1416 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1415)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1422 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1422)
        write(pp, flat1422)
        return nothing
    else
        _dollar_dollar = msg
        fields1418 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1419 = fields1418
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1420 = unwrapped_fields1419[1]
        pretty_relation_id(pp, field1420)
        newline(pp)
        field1421 = unwrapped_fields1419[2]
        pretty_betree_info(pp, field1421)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1428 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1428)
        write(pp, flat1428)
        return nothing
    else
        _dollar_dollar = msg
        _t1842 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1423 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1842,)
        unwrapped_fields1424 = fields1423
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1425 = unwrapped_fields1424[1]
        pretty_betree_info_key_types(pp, field1425)
        newline(pp)
        field1426 = unwrapped_fields1424[2]
        pretty_betree_info_value_types(pp, field1426)
        newline(pp)
        field1427 = unwrapped_fields1424[3]
        pretty_config_dict(pp, field1427)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1432 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1432)
        write(pp, flat1432)
        return nothing
    else
        fields1429 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1429)
            newline(pp)
            for (i1843, elem1430) in enumerate(fields1429)
                i1431 = i1843 - 1
                if (i1431 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1430)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1436 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1436)
        write(pp, flat1436)
        return nothing
    else
        fields1433 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1433)
            newline(pp)
            for (i1844, elem1434) in enumerate(fields1433)
                i1435 = i1844 - 1
                if (i1435 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1434)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1446 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1446)
        write(pp, flat1446)
        return nothing
    else
        _dollar_dollar = msg
        _t1845 = deconstruct_csv_data_columns_optional(pp, _dollar_dollar)
        _t1846 = deconstruct_csv_data_relations_optional(pp, _dollar_dollar)
        fields1437 = (_dollar_dollar.locator, _dollar_dollar.config, _t1845, _t1846, _dollar_dollar.asof,)
        unwrapped_fields1438 = fields1437
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1439 = unwrapped_fields1438[1]
        pretty_csvlocator(pp, field1439)
        newline(pp)
        field1440 = unwrapped_fields1438[2]
        pretty_csv_config(pp, field1440)
        field1441 = unwrapped_fields1438[3]
        if !isnothing(field1441)
            newline(pp)
            opt_val1442 = field1441
            pretty_gnf_columns(pp, opt_val1442)
        end
        field1443 = unwrapped_fields1438[4]
        if !isnothing(field1443)
            newline(pp)
            opt_val1444 = field1443
            pretty_target_relations(pp, opt_val1444)
        end
        newline(pp)
        field1445 = unwrapped_fields1438[5]
        pretty_csv_asof(pp, field1445)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1453 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1453)
        write(pp, flat1453)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1847 = _dollar_dollar.paths
        else
            _t1847 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1848 = String(copy(_dollar_dollar.inline_data))
        else
            _t1848 = nothing
        end
        fields1447 = (_t1847, _t1848,)
        unwrapped_fields1448 = fields1447
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1449 = unwrapped_fields1448[1]
        if !isnothing(field1449)
            newline(pp)
            opt_val1450 = field1449
            pretty_csv_locator_paths(pp, opt_val1450)
        end
        field1451 = unwrapped_fields1448[2]
        if !isnothing(field1451)
            newline(pp)
            opt_val1452 = field1451
            pretty_csv_locator_inline_data(pp, opt_val1452)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1457 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1457)
        write(pp, flat1457)
        return nothing
    else
        fields1454 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1454)
            newline(pp)
            for (i1849, elem1455) in enumerate(fields1454)
                i1456 = i1849 - 1
                if (i1456 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1455))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1459 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1459)
        write(pp, flat1459)
        return nothing
    else
        fields1458 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1458))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1465 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1465)
        write(pp, flat1465)
        return nothing
    else
        _dollar_dollar = msg
        _t1850 = deconstruct_csv_config(pp, _dollar_dollar)
        _t1851 = deconstruct_csv_storage_integration_optional(pp, _dollar_dollar)
        fields1460 = (_t1850, _t1851,)
        unwrapped_fields1461 = fields1460
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1462 = unwrapped_fields1461[1]
        pretty_config_dict(pp, field1462)
        field1463 = unwrapped_fields1461[2]
        if !isnothing(field1463)
            newline(pp)
            opt_val1464 = field1463
            pretty__storage_integration(pp, opt_val1464)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty__storage_integration(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat1467 = try_flat(pp, msg, pretty__storage_integration)
    if !isnothing(flat1467)
        write(pp, flat1467)
        return nothing
    else
        fields1466 = msg
        write(pp, "(storage_integration")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, fields1466)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1471 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1471)
        write(pp, flat1471)
        return nothing
    else
        fields1468 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1468)
            newline(pp)
            for (i1852, elem1469) in enumerate(fields1468)
                i1470 = i1852 - 1
                if (i1470 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1469)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1480 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1480)
        write(pp, flat1480)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1853 = _dollar_dollar.target_id
        else
            _t1853 = nothing
        end
        fields1472 = (_dollar_dollar.column_path, _t1853, _dollar_dollar.types,)
        unwrapped_fields1473 = fields1472
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1474 = unwrapped_fields1473[1]
        pretty_gnf_column_path(pp, field1474)
        field1475 = unwrapped_fields1473[2]
        if !isnothing(field1475)
            newline(pp)
            opt_val1476 = field1475
            pretty_relation_id(pp, opt_val1476)
        end
        newline(pp)
        write(pp, "[")
        field1477 = unwrapped_fields1473[3]
        for (i1854, elem1478) in enumerate(field1477)
            i1479 = i1854 - 1
            if (i1479 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1478)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1487 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1487)
        write(pp, flat1487)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1855 = _dollar_dollar[1]
        else
            _t1855 = nothing
        end
        deconstruct_result1485 = _t1855
        if !isnothing(deconstruct_result1485)
            unwrapped1486 = deconstruct_result1485
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1486))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1856 = _dollar_dollar
            else
                _t1856 = nothing
            end
            deconstruct_result1481 = _t1856
            if !isnothing(deconstruct_result1481)
                unwrapped1482 = deconstruct_result1481
                write(pp, "[")
                indent!(pp)
                for (i1857, elem1483) in enumerate(unwrapped1482)
                    i1484 = i1857 - 1
                    if (i1484 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1483))
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

function pretty_target_relations(pp::PrettyPrinter, msg::Proto.TargetRelations)
    flat1492 = try_flat(pp, msg, pretty_target_relations)
    if !isnothing(flat1492)
        write(pp, flat1492)
        return nothing
    else
        _dollar_dollar = msg
        _t1858 = deconstruct_relation_keys(pp, _dollar_dollar)
        fields1488 = (_t1858, _dollar_dollar,)
        unwrapped_fields1489 = fields1488
        write(pp, "(relations")
        indent_sexp!(pp)
        newline(pp)
        field1490 = unwrapped_fields1489[1]
        pretty_relation_keys(pp, field1490)
        newline(pp)
        field1491 = unwrapped_fields1489[2]
        pretty_relation_body(pp, field1491)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_keys(pp::PrettyPrinter, msg::Tuple{Vector{Proto.NamedColumn}, Bool})
    flat1499 = try_flat(pp, msg, pretty_relation_keys)
    if !isnothing(flat1499)
        write(pp, flat1499)
        return nothing
    else
        _dollar_dollar = msg
        if !_dollar_dollar[2]
            _t1859 = _dollar_dollar[1]
        else
            _t1859 = nothing
        end
        deconstruct_result1495 = _t1859
        if !isnothing(deconstruct_result1495)
            unwrapped1496 = deconstruct_result1495
            write(pp, "(keys")
            indent_sexp!(pp)
            if !isempty(unwrapped1496)
                newline(pp)
                for (i1860, elem1497) in enumerate(unwrapped1496)
                    i1498 = i1860 - 1
                    if (i1498 > 0)
                        newline(pp)
                    end
                    pretty_named_column(pp, elem1497)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _dollar_dollar[2]
                _t1861 = ()
            else
                _t1861 = nothing
            end
            deconstruct_result1493 = _t1861
            if !isnothing(deconstruct_result1493)
                unwrapped1494 = deconstruct_result1493
                write(pp, "(keys")
                newline(pp)
                write(pp, "synthetic)")
            else
                throw(ParseError("No matching rule for relation_keys"))
            end
        end
    end
    return nothing
end

function pretty_named_column(pp::PrettyPrinter, msg::Proto.NamedColumn)
    flat1504 = try_flat(pp, msg, pretty_named_column)
    if !isnothing(flat1504)
        write(pp, flat1504)
        return nothing
    else
        _dollar_dollar = msg
        fields1500 = (_dollar_dollar.name, _dollar_dollar.var"#type",)
        unwrapped_fields1501 = fields1500
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1502 = unwrapped_fields1501[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1502))
        newline(pp)
        field1503 = unwrapped_fields1501[2]
        pretty_type(pp, field1503)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_body(pp::PrettyPrinter, msg::Proto.TargetRelations)
    flat1511 = try_flat(pp, msg, pretty_relation_body)
    if !isnothing(flat1511)
        write(pp, flat1511)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("plain"))
            _t1862 = _get_oneof_field(_dollar_dollar, :plain).targets
        else
            _t1862 = nothing
        end
        deconstruct_result1509 = _t1862
        if !isnothing(deconstruct_result1509)
            unwrapped1510 = deconstruct_result1509
            pretty_non_cdc_relations(pp, unwrapped1510)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("cdc"))
                _t1863 = (_get_oneof_field(_dollar_dollar, :cdc).inserts, _get_oneof_field(_dollar_dollar, :cdc).deletes,)
            else
                _t1863 = nothing
            end
            deconstruct_result1505 = _t1863
            if !isnothing(deconstruct_result1505)
                unwrapped1506 = deconstruct_result1505
                field1507 = unwrapped1506[1]
                pretty_cdc_inserts(pp, field1507)
                write(pp, " ")
                field1508 = unwrapped1506[2]
                pretty_cdc_deletes(pp, field1508)
            else
                throw(ParseError("No matching rule for relation_body"))
            end
        end
    end
    return nothing
end

function pretty_non_cdc_relations(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1515 = try_flat(pp, msg, pretty_non_cdc_relations)
    if !isnothing(flat1515)
        write(pp, flat1515)
        return nothing
    else
        fields1512 = msg
        for (i1864, elem1513) in enumerate(fields1512)
            i1514 = i1864 - 1
            if (i1514 > 0)
                newline(pp)
            end
            pretty_target_relation(pp, elem1513)
        end
    end
    return nothing
end

function pretty_target_relation(pp::PrettyPrinter, msg::Proto.TargetRelation)
    flat1522 = try_flat(pp, msg, pretty_target_relation)
    if !isnothing(flat1522)
        write(pp, flat1522)
        return nothing
    else
        _dollar_dollar = msg
        fields1516 = (_dollar_dollar.target_id, _dollar_dollar.values,)
        unwrapped_fields1517 = fields1516
        write(pp, "(relation")
        indent_sexp!(pp)
        newline(pp)
        field1518 = unwrapped_fields1517[1]
        pretty_relation_id(pp, field1518)
        field1519 = unwrapped_fields1517[2]
        if !isempty(field1519)
            newline(pp)
            for (i1865, elem1520) in enumerate(field1519)
                i1521 = i1865 - 1
                if (i1521 > 0)
                    newline(pp)
                end
                pretty_named_column(pp, elem1520)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_inserts(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1526 = try_flat(pp, msg, pretty_cdc_inserts)
    if !isnothing(flat1526)
        write(pp, flat1526)
        return nothing
    else
        fields1523 = msg
        write(pp, "(inserts")
        indent_sexp!(pp)
        if !isempty(fields1523)
            newline(pp)
            for (i1866, elem1524) in enumerate(fields1523)
                i1525 = i1866 - 1
                if (i1525 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1524)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_deletes(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1530 = try_flat(pp, msg, pretty_cdc_deletes)
    if !isnothing(flat1530)
        write(pp, flat1530)
        return nothing
    else
        fields1527 = msg
        write(pp, "(deletes")
        indent_sexp!(pp)
        if !isempty(fields1527)
            newline(pp)
            for (i1867, elem1528) in enumerate(fields1527)
                i1529 = i1867 - 1
                if (i1529 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1528)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1532 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1532)
        write(pp, flat1532)
        return nothing
    else
        fields1531 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1531))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1543 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1543)
        write(pp, flat1543)
        return nothing
    else
        _dollar_dollar = msg
        _t1868 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1869 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1533 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1868, _t1869, _dollar_dollar.returns_delta,)
        unwrapped_fields1534 = fields1533
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1535 = unwrapped_fields1534[1]
        pretty_iceberg_locator(pp, field1535)
        newline(pp)
        field1536 = unwrapped_fields1534[2]
        pretty_iceberg_catalog_config(pp, field1536)
        newline(pp)
        field1537 = unwrapped_fields1534[3]
        pretty_gnf_columns(pp, field1537)
        field1538 = unwrapped_fields1534[4]
        if !isnothing(field1538)
            newline(pp)
            opt_val1539 = field1538
            pretty_iceberg_from_snapshot(pp, opt_val1539)
        end
        field1540 = unwrapped_fields1534[5]
        if !isnothing(field1540)
            newline(pp)
            opt_val1541 = field1540
            pretty_iceberg_to_snapshot(pp, opt_val1541)
        end
        newline(pp)
        field1542 = unwrapped_fields1534[6]
        pretty_boolean_value(pp, field1542)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1549 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1549)
        write(pp, flat1549)
        return nothing
    else
        _dollar_dollar = msg
        fields1544 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1545 = fields1544
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1546 = unwrapped_fields1545[1]
        pretty_iceberg_locator_table_name(pp, field1546)
        newline(pp)
        field1547 = unwrapped_fields1545[2]
        pretty_iceberg_locator_namespace(pp, field1547)
        newline(pp)
        field1548 = unwrapped_fields1545[3]
        pretty_iceberg_locator_warehouse(pp, field1548)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1551 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1551)
        write(pp, flat1551)
        return nothing
    else
        fields1550 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1550))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1555 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1555)
        write(pp, flat1555)
        return nothing
    else
        fields1552 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1552)
            newline(pp)
            for (i1870, elem1553) in enumerate(fields1552)
                i1554 = i1870 - 1
                if (i1554 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1553))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1557 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1557)
        write(pp, flat1557)
        return nothing
    else
        fields1556 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1556))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1565 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1565)
        write(pp, flat1565)
        return nothing
    else
        _dollar_dollar = msg
        _t1871 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1558 = (_dollar_dollar.catalog_uri, _t1871, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1559 = fields1558
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1560 = unwrapped_fields1559[1]
        pretty_iceberg_catalog_uri(pp, field1560)
        field1561 = unwrapped_fields1559[2]
        if !isnothing(field1561)
            newline(pp)
            opt_val1562 = field1561
            pretty_iceberg_catalog_config_scope(pp, opt_val1562)
        end
        newline(pp)
        field1563 = unwrapped_fields1559[3]
        pretty_iceberg_properties(pp, field1563)
        newline(pp)
        field1564 = unwrapped_fields1559[4]
        pretty_iceberg_auth_properties(pp, field1564)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1567 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1567)
        write(pp, flat1567)
        return nothing
    else
        fields1566 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1566))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1569 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1569)
        write(pp, flat1569)
        return nothing
    else
        fields1568 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1568))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1573 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1573)
        write(pp, flat1573)
        return nothing
    else
        fields1570 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1570)
            newline(pp)
            for (i1872, elem1571) in enumerate(fields1570)
                i1572 = i1872 - 1
                if (i1572 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1571)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1578 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1578)
        write(pp, flat1578)
        return nothing
    else
        _dollar_dollar = msg
        fields1574 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1575 = fields1574
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1576 = unwrapped_fields1575[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1576))
        newline(pp)
        field1577 = unwrapped_fields1575[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1577))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1582 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1582)
        write(pp, flat1582)
        return nothing
    else
        fields1579 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1579)
            newline(pp)
            for (i1873, elem1580) in enumerate(fields1579)
                i1581 = i1873 - 1
                if (i1581 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1580)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1587 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1587)
        write(pp, flat1587)
        return nothing
    else
        _dollar_dollar = msg
        _t1874 = mask_secret_value(pp, _dollar_dollar)
        fields1583 = (_dollar_dollar[1], _t1874,)
        unwrapped_fields1584 = fields1583
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1585 = unwrapped_fields1584[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1585))
        newline(pp)
        field1586 = unwrapped_fields1584[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1586))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1589 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1589)
        write(pp, flat1589)
        return nothing
    else
        fields1588 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1588))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1591 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1591)
        write(pp, flat1591)
        return nothing
    else
        fields1590 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1590))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1594 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1594)
        write(pp, flat1594)
        return nothing
    else
        _dollar_dollar = msg
        fields1592 = _dollar_dollar.fragment_id
        unwrapped_fields1593 = fields1592
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1593)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1599 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1599)
        write(pp, flat1599)
        return nothing
    else
        _dollar_dollar = msg
        fields1595 = _dollar_dollar.relations
        unwrapped_fields1596 = fields1595
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1596)
            newline(pp)
            for (i1875, elem1597) in enumerate(unwrapped_fields1596)
                i1598 = i1875 - 1
                if (i1598 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1597)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1606 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1606)
        write(pp, flat1606)
        return nothing
    else
        _dollar_dollar = msg
        fields1600 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1601 = fields1600
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1602 = unwrapped_fields1601[1]
        pretty_edb_path(pp, field1602)
        field1603 = unwrapped_fields1601[2]
        if !isempty(field1603)
            newline(pp)
            for (i1876, elem1604) in enumerate(field1603)
                i1605 = i1876 - 1
                if (i1605 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1604)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1611 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1611)
        write(pp, flat1611)
        return nothing
    else
        _dollar_dollar = msg
        fields1607 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1608 = fields1607
        field1609 = unwrapped_fields1608[1]
        pretty_edb_path(pp, field1609)
        write(pp, " ")
        field1610 = unwrapped_fields1608[2]
        pretty_relation_id(pp, field1610)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1615 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1615)
        write(pp, flat1615)
        return nothing
    else
        fields1612 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1612)
            newline(pp)
            for (i1877, elem1613) in enumerate(fields1612)
                i1614 = i1877 - 1
                if (i1614 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1613)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1626 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1626)
        write(pp, flat1626)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1878 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1878 = nothing
        end
        deconstruct_result1624 = _t1878
        if !isnothing(deconstruct_result1624)
            unwrapped1625 = deconstruct_result1624
            pretty_demand(pp, unwrapped1625)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1879 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1879 = nothing
            end
            deconstruct_result1622 = _t1879
            if !isnothing(deconstruct_result1622)
                unwrapped1623 = deconstruct_result1622
                pretty_output(pp, unwrapped1623)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1880 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1880 = nothing
                end
                deconstruct_result1620 = _t1880
                if !isnothing(deconstruct_result1620)
                    unwrapped1621 = deconstruct_result1620
                    pretty_what_if(pp, unwrapped1621)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1881 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1881 = nothing
                    end
                    deconstruct_result1618 = _t1881
                    if !isnothing(deconstruct_result1618)
                        unwrapped1619 = deconstruct_result1618
                        pretty_abort(pp, unwrapped1619)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1882 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1882 = nothing
                        end
                        deconstruct_result1616 = _t1882
                        if !isnothing(deconstruct_result1616)
                            unwrapped1617 = deconstruct_result1616
                            pretty_export(pp, unwrapped1617)
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
    flat1629 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1629)
        write(pp, flat1629)
        return nothing
    else
        _dollar_dollar = msg
        fields1627 = _dollar_dollar.relation_id
        unwrapped_fields1628 = fields1627
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1628)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1634 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1634)
        write(pp, flat1634)
        return nothing
    else
        _dollar_dollar = msg
        fields1630 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1631 = fields1630
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1632 = unwrapped_fields1631[1]
        pretty_name(pp, field1632)
        newline(pp)
        field1633 = unwrapped_fields1631[2]
        pretty_relation_id(pp, field1633)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1639 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1639)
        write(pp, flat1639)
        return nothing
    else
        _dollar_dollar = msg
        fields1635 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1636 = fields1635
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1637 = unwrapped_fields1636[1]
        pretty_name(pp, field1637)
        newline(pp)
        field1638 = unwrapped_fields1636[2]
        pretty_epoch(pp, field1638)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1645 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1645)
        write(pp, flat1645)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1883 = _dollar_dollar.name
        else
            _t1883 = nothing
        end
        fields1640 = (_t1883, _dollar_dollar.relation_id,)
        unwrapped_fields1641 = fields1640
        write(pp, "(abort")
        indent_sexp!(pp)
        field1642 = unwrapped_fields1641[1]
        if !isnothing(field1642)
            newline(pp)
            opt_val1643 = field1642
            pretty_name(pp, opt_val1643)
        end
        newline(pp)
        field1644 = unwrapped_fields1641[2]
        pretty_relation_id(pp, field1644)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1650 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1650)
        write(pp, flat1650)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1884 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1884 = nothing
        end
        deconstruct_result1648 = _t1884
        if !isnothing(deconstruct_result1648)
            unwrapped1649 = deconstruct_result1648
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1649)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1885 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1885 = nothing
            end
            deconstruct_result1646 = _t1885
            if !isnothing(deconstruct_result1646)
                unwrapped1647 = deconstruct_result1646
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1647)
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
    flat1661 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1661)
        write(pp, flat1661)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1887 = deconstruct_export_csv_output_location(pp, _dollar_dollar)
            _t1886 = (_t1887, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1886 = nothing
        end
        deconstruct_result1656 = _t1886
        if !isnothing(deconstruct_result1656)
            unwrapped1657 = deconstruct_result1656
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1658 = unwrapped1657[1]
            pretty_export_csv_output_location(pp, field1658)
            newline(pp)
            field1659 = unwrapped1657[2]
            pretty_export_csv_source(pp, field1659)
            newline(pp)
            field1660 = unwrapped1657[3]
            pretty_csv_config(pp, field1660)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1889 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1888 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1889,)
            else
                _t1888 = nothing
            end
            deconstruct_result1651 = _t1888
            if !isnothing(deconstruct_result1651)
                unwrapped1652 = deconstruct_result1651
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1653 = unwrapped1652[1]
                pretty_export_csv_path(pp, field1653)
                newline(pp)
                field1654 = unwrapped1652[2]
                pretty_export_csv_columns_list(pp, field1654)
                newline(pp)
                field1655 = unwrapped1652[3]
                pretty_config_dict(pp, field1655)
                dedent!(pp)
                write(pp, ")")
            else
                throw(ParseError("No matching rule for export_csv_config"))
            end
        end
    end
    return nothing
end

function pretty_export_csv_output_location(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1666 = try_flat(pp, msg, pretty_export_csv_output_location)
    if !isnothing(flat1666)
        write(pp, flat1666)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar[1] != ""
            _t1890 = _dollar_dollar[1]
        else
            _t1890 = nothing
        end
        deconstruct_result1664 = _t1890
        if !isnothing(deconstruct_result1664)
            unwrapped1665 = deconstruct_result1664
            write(pp, "(path")
            indent_sexp!(pp)
            newline(pp)
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1665))
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _dollar_dollar[2] != ""
                _t1891 = _dollar_dollar[2]
            else
                _t1891 = nothing
            end
            deconstruct_result1662 = _t1891
            if !isnothing(deconstruct_result1662)
                unwrapped1663 = deconstruct_result1662
                write(pp, "(transaction_output_name")
                indent_sexp!(pp)
                newline(pp)
                pretty_name(pp, unwrapped1663)
                dedent!(pp)
                write(pp, ")")
            else
                throw(ParseError("No matching rule for export_csv_output_location"))
            end
        end
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1673 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1673)
        write(pp, flat1673)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1892 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1892 = nothing
        end
        deconstruct_result1669 = _t1892
        if !isnothing(deconstruct_result1669)
            unwrapped1670 = deconstruct_result1669
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1670)
                newline(pp)
                for (i1893, elem1671) in enumerate(unwrapped1670)
                    i1672 = i1893 - 1
                    if (i1672 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1671)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1894 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1894 = nothing
            end
            deconstruct_result1667 = _t1894
            if !isnothing(deconstruct_result1667)
                unwrapped1668 = deconstruct_result1667
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1668)
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
    flat1678 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1678)
        write(pp, flat1678)
        return nothing
    else
        _dollar_dollar = msg
        fields1674 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1675 = fields1674
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1676 = unwrapped_fields1675[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1676))
        newline(pp)
        field1677 = unwrapped_fields1675[2]
        pretty_relation_id(pp, field1677)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1680 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1680)
        write(pp, flat1680)
        return nothing
    else
        fields1679 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1679))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1684 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1684)
        write(pp, flat1684)
        return nothing
    else
        fields1681 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1681)
            newline(pp)
            for (i1895, elem1682) in enumerate(fields1681)
                i1683 = i1895 - 1
                if (i1683 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1682)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1693 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1693)
        write(pp, flat1693)
        return nothing
    else
        _dollar_dollar = msg
        _t1896 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1685 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1896,)
        unwrapped_fields1686 = fields1685
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1687 = unwrapped_fields1686[1]
        pretty_iceberg_locator(pp, field1687)
        newline(pp)
        field1688 = unwrapped_fields1686[2]
        pretty_iceberg_catalog_config(pp, field1688)
        newline(pp)
        field1689 = unwrapped_fields1686[3]
        pretty_export_iceberg_table_def(pp, field1689)
        newline(pp)
        field1690 = unwrapped_fields1686[4]
        pretty_iceberg_table_properties(pp, field1690)
        field1691 = unwrapped_fields1686[5]
        if !isnothing(field1691)
            newline(pp)
            opt_val1692 = field1691
            pretty_config_dict(pp, opt_val1692)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1695 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1695)
        write(pp, flat1695)
        return nothing
    else
        fields1694 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1694)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1699 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1699)
        write(pp, flat1699)
        return nothing
    else
        fields1696 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1696)
            newline(pp)
            for (i1897, elem1697) in enumerate(fields1696)
                i1698 = i1897 - 1
                if (i1698 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1697)
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
    for (i1951, _rid) in enumerate(msg.ids)
        _idx = i1951 - 1
        newline(pp)
        write(pp, "(")
        _t1952 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1952)
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

function pretty_cdc_targets(pp::PrettyPrinter, msg::Proto.CDCTargets)
    write(pp, "(cdc_targets")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":inserts (")
    for (i1953, _elem) in enumerate(msg.inserts)
        _idx = i1953 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":deletes (")
    for (i1954, _elem) in enumerate(msg.deletes)
        _idx = i1954 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, "))")
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
    for (i1955, _elem) in enumerate(msg.keys)
        _idx = i1955 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1956, _elem) in enumerate(msg.values)
        _idx = i1956 - 1
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

function pretty_plain_targets(pp::PrettyPrinter, msg::Proto.PlainTargets)
    write(pp, "(plain_targets")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":targets (")
    for (i1957, _elem) in enumerate(msg.targets)
        _idx = i1957 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, "))")
    dedent!(pp)
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
    for (i1958, _elem) in enumerate(msg.columns)
        _idx = i1958 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.TargetRelations) = pretty_target_relations(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Tuple{Vector{Proto.NamedColumn}, Bool}) = pretty_relation_keys(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.NamedColumn) = pretty_named_column(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.TargetRelation}) = pretty_non_cdc_relations(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.TargetRelation) = pretty_target_relation(pp, x)
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CDCTargets) = pretty_cdc_targets(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DecimalValue) = pretty_decimal_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FunctionalDependency) = pretty_functional_dependency(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Int128Value) = pretty_int128_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MissingValue) = pretty_missing_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.PlainTargets) = pretty_plain_targets(pp, x)
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
