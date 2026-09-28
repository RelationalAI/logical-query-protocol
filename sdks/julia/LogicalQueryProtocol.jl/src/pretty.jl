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

function deconstruct_load_errors_optional(pp::PrettyPrinter, msg::Proto.TargetRelations)::Union{Nothing, Proto.RelationId}
    if _has_proto_field(msg, Symbol("load_errors"))
        return msg.load_errors
    else
        _t1918 = nothing
    end
    return nothing
end

function deconstruct_csv_data_columns_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Vector{Proto.GNFColumn}}
    if _has_proto_field(msg, Symbol("relations"))
        return nothing
    else
        _t1919 = nothing
    end
    return msg.columns
end

function deconstruct_csv_data_relations_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Proto.TargetRelations}
    if _has_proto_field(msg, Symbol("relations"))
        return msg.relations
    else
        _t1920 = nothing
    end
    return nothing
end

function deconstruct_export_csv_output_location(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Tuple{String, String}
    return (msg.path, msg.transaction_output_name,)
end

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1921 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1921
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1922 = Proto.Value(value=OneOf(:int_value, v))
    return _t1922
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1923 = Proto.Value(value=OneOf(:float_value, v))
    return _t1923
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1924 = Proto.Value(value=OneOf(:string_value, v))
    return _t1924
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1925 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1925
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1926 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1926
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1927 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1927,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1928 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1928,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1929 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1929,))
            end
        end
    end
    _t1930 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1930,))
    for pair in sort([(k, v) for (k, v) in msg.configuration_values])
        push!(result, pair)
    end
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1931 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1931,))
    _t1932 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1932,))
    if msg.new_line != ""
        _t1933 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1933,))
    end
    _t1934 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1934,))
    _t1935 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1935,))
    _t1936 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1936,))
    if msg.comment != ""
        _t1937 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1937,))
    end
    for missing_string in msg.missing_strings
        _t1938 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1938,))
    end
    _t1939 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1939,))
    _t1940 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1940,))
    _t1941 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1941,))
    if msg.partition_size_mb != 0
        _t1942 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1942,))
    end
    return sort(result)
end

function deconstruct_csv_storage_integration_optional(pp::PrettyPrinter, msg::Proto.CSVConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    if !_has_proto_field(msg, Symbol("storage_integration"))
        return nothing
    else
        _t1943 = nothing
    end
    si = msg.storage_integration
    result = Tuple{String, Proto.Value}[]
    if si.provider != ""
        _t1944 = _make_value_string(pp, si.provider)
        push!(result, ("provider", _t1944,))
    end
    if si.azure_sas_token != ""
        _t1945 = _make_value_string(pp, "***")
        push!(result, ("azure_sas_token", _t1945,))
    end
    if si.s3_region != ""
        _t1946 = _make_value_string(pp, si.s3_region)
        push!(result, ("s3_region", _t1946,))
    end
    if si.s3_access_key_id != ""
        _t1947 = _make_value_string(pp, "***")
        push!(result, ("s3_access_key_id", _t1947,))
    end
    if si.s3_secret_access_key != ""
        _t1948 = _make_value_string(pp, "***")
        push!(result, ("s3_secret_access_key", _t1948,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1949 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1949,))
    _t1950 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1950,))
    _t1951 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1951,))
    _t1952 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1952,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1953 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1953,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1954 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1954,))
        end
    end
    _t1955 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1955,))
    _t1956 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1956,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1957 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1957,))
    end
    if !isnothing(msg.compression)
        _t1958 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1958,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1959 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1959,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1960 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1960,))
    end
    if !isnothing(msg.syntax_delim)
        _t1961 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1961,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1962 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1962,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1963 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1963,))
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
        _t1964 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1965 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1966 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1967 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1967,))
    end
    if msg.target_file_size_bytes != 0
        _t1968 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1968,))
    end
    if msg.compression != ""
        _t1969 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1969,))
    end
    if length(result) == 0
        return nothing
    else
        _t1970 = nothing
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
        _t1971 = nothing
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
    flat868 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat868)
        write(pp, flat868)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1718 = _dollar_dollar.configure
        else
            _t1718 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1719 = _dollar_dollar.sync
        else
            _t1719 = nothing
        end
        fields859 = (_t1718, _t1719, _dollar_dollar.epochs,)
        unwrapped_fields860 = fields859
        write(pp, "(transaction")
        indent_sexp!(pp)
        field861 = unwrapped_fields860[1]
        if !isnothing(field861)
            newline(pp)
            opt_val862 = field861
            pretty_configure(pp, opt_val862)
        end
        field863 = unwrapped_fields860[2]
        if !isnothing(field863)
            newline(pp)
            opt_val864 = field863
            pretty_sync(pp, opt_val864)
        end
        field865 = unwrapped_fields860[3]
        if !isempty(field865)
            newline(pp)
            for (i1720, elem866) in enumerate(field865)
                i867 = i1720 - 1
                if (i867 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem866)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat871 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat871)
        write(pp, flat871)
        return nothing
    else
        _dollar_dollar = msg
        _t1721 = deconstruct_configure(pp, _dollar_dollar)
        fields869 = _t1721
        unwrapped_fields870 = fields869
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields870)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat875 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat875)
        write(pp, flat875)
        return nothing
    else
        fields872 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields872)
            newline(pp)
            for (i1722, elem873) in enumerate(fields872)
                i874 = i1722 - 1
                if (i874 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem873)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat880 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat880)
        write(pp, flat880)
        return nothing
    else
        _dollar_dollar = msg
        fields876 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields877 = fields876
        write(pp, ":")
        field878 = unwrapped_fields877[1]
        write(pp, field878)
        write(pp, " ")
        field879 = unwrapped_fields877[2]
        pretty_raw_value(pp, field879)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat906 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1723 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1723 = nothing
        end
        deconstruct_result904 = _t1723
        if !isnothing(deconstruct_result904)
            unwrapped905 = deconstruct_result904
            pretty_raw_date(pp, unwrapped905)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1724 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1724 = nothing
            end
            deconstruct_result902 = _t1724
            if !isnothing(deconstruct_result902)
                unwrapped903 = deconstruct_result902
                pretty_raw_datetime(pp, unwrapped903)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1725 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1725 = nothing
                end
                deconstruct_result900 = _t1725
                if !isnothing(deconstruct_result900)
                    unwrapped901 = deconstruct_result900
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped901))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1726 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1726 = nothing
                    end
                    deconstruct_result898 = _t1726
                    if !isnothing(deconstruct_result898)
                        unwrapped899 = deconstruct_result898
                        write(pp, (string(Int64(unwrapped899)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1727 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1727 = nothing
                        end
                        deconstruct_result896 = _t1727
                        if !isnothing(deconstruct_result896)
                            unwrapped897 = deconstruct_result896
                            write(pp, string(unwrapped897))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1728 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1728 = nothing
                            end
                            deconstruct_result894 = _t1728
                            if !isnothing(deconstruct_result894)
                                unwrapped895 = deconstruct_result894
                                write(pp, format_float32_literal(unwrapped895))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1729 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1729 = nothing
                                end
                                deconstruct_result892 = _t1729
                                if !isnothing(deconstruct_result892)
                                    unwrapped893 = deconstruct_result892
                                    write(pp, lowercase(string(unwrapped893)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1730 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1730 = nothing
                                    end
                                    deconstruct_result890 = _t1730
                                    if !isnothing(deconstruct_result890)
                                        unwrapped891 = deconstruct_result890
                                        write(pp, (string(Int64(unwrapped891)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1731 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1731 = nothing
                                        end
                                        deconstruct_result888 = _t1731
                                        if !isnothing(deconstruct_result888)
                                            unwrapped889 = deconstruct_result888
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped889))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1732 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1732 = nothing
                                            end
                                            deconstruct_result886 = _t1732
                                            if !isnothing(deconstruct_result886)
                                                unwrapped887 = deconstruct_result886
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped887))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1733 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1733 = nothing
                                                end
                                                deconstruct_result884 = _t1733
                                                if !isnothing(deconstruct_result884)
                                                    unwrapped885 = deconstruct_result884
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped885))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1734 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1734 = nothing
                                                    end
                                                    deconstruct_result882 = _t1734
                                                    if !isnothing(deconstruct_result882)
                                                        unwrapped883 = deconstruct_result882
                                                        pretty_boolean_value(pp, unwrapped883)
                                                    else
                                                        fields881 = msg
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
    flat912 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat912)
        write(pp, flat912)
        return nothing
    else
        _dollar_dollar = msg
        fields907 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields908 = fields907
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field909 = unwrapped_fields908[1]
        write(pp, string(field909))
        newline(pp)
        field910 = unwrapped_fields908[2]
        write(pp, string(field910))
        newline(pp)
        field911 = unwrapped_fields908[3]
        write(pp, string(field911))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat923 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat923)
        write(pp, flat923)
        return nothing
    else
        _dollar_dollar = msg
        fields913 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields914 = fields913
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field915 = unwrapped_fields914[1]
        write(pp, string(field915))
        newline(pp)
        field916 = unwrapped_fields914[2]
        write(pp, string(field916))
        newline(pp)
        field917 = unwrapped_fields914[3]
        write(pp, string(field917))
        newline(pp)
        field918 = unwrapped_fields914[4]
        write(pp, string(field918))
        newline(pp)
        field919 = unwrapped_fields914[5]
        write(pp, string(field919))
        newline(pp)
        field920 = unwrapped_fields914[6]
        write(pp, string(field920))
        field921 = unwrapped_fields914[7]
        if !isnothing(field921)
            newline(pp)
            opt_val922 = field921
            write(pp, string(opt_val922))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1735 = ()
    else
        _t1735 = nothing
    end
    deconstruct_result926 = _t1735
    if !isnothing(deconstruct_result926)
        unwrapped927 = deconstruct_result926
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1736 = ()
        else
            _t1736 = nothing
        end
        deconstruct_result924 = _t1736
        if !isnothing(deconstruct_result924)
            unwrapped925 = deconstruct_result924
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat932 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat932)
        write(pp, flat932)
        return nothing
    else
        _dollar_dollar = msg
        fields928 = _dollar_dollar.fragments
        unwrapped_fields929 = fields928
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields929)
            newline(pp)
            for (i1737, elem930) in enumerate(unwrapped_fields929)
                i931 = i1737 - 1
                if (i931 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem930)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat935 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat935)
        write(pp, flat935)
        return nothing
    else
        _dollar_dollar = msg
        fields933 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields934 = fields933
        write(pp, ":")
        write(pp, unwrapped_fields934)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat942 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat942)
        write(pp, flat942)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1738 = _dollar_dollar.writes
        else
            _t1738 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1739 = _dollar_dollar.reads
        else
            _t1739 = nothing
        end
        fields936 = (_t1738, _t1739,)
        unwrapped_fields937 = fields936
        write(pp, "(epoch")
        indent_sexp!(pp)
        field938 = unwrapped_fields937[1]
        if !isnothing(field938)
            newline(pp)
            opt_val939 = field938
            pretty_epoch_writes(pp, opt_val939)
        end
        field940 = unwrapped_fields937[2]
        if !isnothing(field940)
            newline(pp)
            opt_val941 = field940
            pretty_epoch_reads(pp, opt_val941)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat946 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        fields943 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields943)
            newline(pp)
            for (i1740, elem944) in enumerate(fields943)
                i945 = i1740 - 1
                if (i945 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem944)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat955 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat955)
        write(pp, flat955)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1741 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1741 = nothing
        end
        deconstruct_result953 = _t1741
        if !isnothing(deconstruct_result953)
            unwrapped954 = deconstruct_result953
            pretty_define(pp, unwrapped954)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1742 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1742 = nothing
            end
            deconstruct_result951 = _t1742
            if !isnothing(deconstruct_result951)
                unwrapped952 = deconstruct_result951
                pretty_undefine(pp, unwrapped952)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1743 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1743 = nothing
                end
                deconstruct_result949 = _t1743
                if !isnothing(deconstruct_result949)
                    unwrapped950 = deconstruct_result949
                    pretty_context(pp, unwrapped950)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1744 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1744 = nothing
                    end
                    deconstruct_result947 = _t1744
                    if !isnothing(deconstruct_result947)
                        unwrapped948 = deconstruct_result947
                        pretty_snapshot(pp, unwrapped948)
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
    flat958 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat958)
        write(pp, flat958)
        return nothing
    else
        _dollar_dollar = msg
        fields956 = _dollar_dollar.fragment
        unwrapped_fields957 = fields956
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields957)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat965 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat965)
        write(pp, flat965)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields959 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields960 = fields959
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field961 = unwrapped_fields960[1]
        pretty_new_fragment_id(pp, field961)
        field962 = unwrapped_fields960[2]
        if !isempty(field962)
            newline(pp)
            for (i1745, elem963) in enumerate(field962)
                i964 = i1745 - 1
                if (i964 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem963)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat967 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat967)
        write(pp, flat967)
        return nothing
    else
        fields966 = msg
        pretty_fragment_id(pp, fields966)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat976 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat976)
        write(pp, flat976)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1746 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1746 = nothing
        end
        deconstruct_result974 = _t1746
        if !isnothing(deconstruct_result974)
            unwrapped975 = deconstruct_result974
            pretty_def(pp, unwrapped975)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1747 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1747 = nothing
            end
            deconstruct_result972 = _t1747
            if !isnothing(deconstruct_result972)
                unwrapped973 = deconstruct_result972
                pretty_algorithm(pp, unwrapped973)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1748 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1748 = nothing
                end
                deconstruct_result970 = _t1748
                if !isnothing(deconstruct_result970)
                    unwrapped971 = deconstruct_result970
                    pretty_constraint(pp, unwrapped971)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1749 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1749 = nothing
                    end
                    deconstruct_result968 = _t1749
                    if !isnothing(deconstruct_result968)
                        unwrapped969 = deconstruct_result968
                        pretty_data(pp, unwrapped969)
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
    flat983 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat983)
        write(pp, flat983)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1750 = _dollar_dollar.attrs
        else
            _t1750 = nothing
        end
        fields977 = (_dollar_dollar.name, _dollar_dollar.body, _t1750,)
        unwrapped_fields978 = fields977
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field979 = unwrapped_fields978[1]
        pretty_relation_id(pp, field979)
        newline(pp)
        field980 = unwrapped_fields978[2]
        pretty_abstraction(pp, field980)
        field981 = unwrapped_fields978[3]
        if !isnothing(field981)
            newline(pp)
            opt_val982 = field981
            pretty_attrs(pp, opt_val982)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat988 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat988)
        write(pp, flat988)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1752 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1751 = _t1752
        else
            _t1751 = nothing
        end
        deconstruct_result986 = _t1751
        if !isnothing(deconstruct_result986)
            unwrapped987 = deconstruct_result986
            write(pp, ":")
            write(pp, unwrapped987)
        else
            _dollar_dollar = msg
            _t1753 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result984 = _t1753
            if !isnothing(deconstruct_result984)
                unwrapped985 = deconstruct_result984
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped985))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat993 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat993)
        write(pp, flat993)
        return nothing
    else
        _dollar_dollar = msg
        _t1754 = deconstruct_bindings(pp, _dollar_dollar)
        fields989 = (_t1754, _dollar_dollar.value,)
        unwrapped_fields990 = fields989
        write(pp, "(")
        indent!(pp)
        field991 = unwrapped_fields990[1]
        pretty_bindings(pp, field991)
        newline(pp)
        field992 = unwrapped_fields990[2]
        pretty_formula(pp, field992)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat1001 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat1001)
        write(pp, flat1001)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1755 = _dollar_dollar[2]
        else
            _t1755 = nothing
        end
        fields994 = (_dollar_dollar[1], _t1755,)
        unwrapped_fields995 = fields994
        write(pp, "[")
        indent!(pp)
        field996 = unwrapped_fields995[1]
        for (i1756, elem997) in enumerate(field996)
            i998 = i1756 - 1
            if (i998 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem997)
        end
        field999 = unwrapped_fields995[2]
        if !isnothing(field999)
            newline(pp)
            opt_val1000 = field999
            pretty_value_bindings(pp, opt_val1000)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat1006 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat1006)
        write(pp, flat1006)
        return nothing
    else
        _dollar_dollar = msg
        fields1002 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields1003 = fields1002
        field1004 = unwrapped_fields1003[1]
        write(pp, field1004)
        write(pp, "::")
        field1005 = unwrapped_fields1003[2]
        pretty_type(pp, field1005)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat1037 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat1037)
        write(pp, flat1037)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1757 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1757 = nothing
        end
        deconstruct_result1035 = _t1757
        if !isnothing(deconstruct_result1035)
            unwrapped1036 = deconstruct_result1035
            pretty_unspecified_type(pp, unwrapped1036)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1758 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1758 = nothing
            end
            deconstruct_result1033 = _t1758
            if !isnothing(deconstruct_result1033)
                unwrapped1034 = deconstruct_result1033
                pretty_string_type(pp, unwrapped1034)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1759 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1759 = nothing
                end
                deconstruct_result1031 = _t1759
                if !isnothing(deconstruct_result1031)
                    unwrapped1032 = deconstruct_result1031
                    pretty_int_type(pp, unwrapped1032)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1760 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1760 = nothing
                    end
                    deconstruct_result1029 = _t1760
                    if !isnothing(deconstruct_result1029)
                        unwrapped1030 = deconstruct_result1029
                        pretty_float_type(pp, unwrapped1030)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1761 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1761 = nothing
                        end
                        deconstruct_result1027 = _t1761
                        if !isnothing(deconstruct_result1027)
                            unwrapped1028 = deconstruct_result1027
                            pretty_uint128_type(pp, unwrapped1028)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1762 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1762 = nothing
                            end
                            deconstruct_result1025 = _t1762
                            if !isnothing(deconstruct_result1025)
                                unwrapped1026 = deconstruct_result1025
                                pretty_int128_type(pp, unwrapped1026)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1763 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1763 = nothing
                                end
                                deconstruct_result1023 = _t1763
                                if !isnothing(deconstruct_result1023)
                                    unwrapped1024 = deconstruct_result1023
                                    pretty_date_type(pp, unwrapped1024)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1764 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1764 = nothing
                                    end
                                    deconstruct_result1021 = _t1764
                                    if !isnothing(deconstruct_result1021)
                                        unwrapped1022 = deconstruct_result1021
                                        pretty_datetime_type(pp, unwrapped1022)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1765 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1765 = nothing
                                        end
                                        deconstruct_result1019 = _t1765
                                        if !isnothing(deconstruct_result1019)
                                            unwrapped1020 = deconstruct_result1019
                                            pretty_missing_type(pp, unwrapped1020)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1766 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1766 = nothing
                                            end
                                            deconstruct_result1017 = _t1766
                                            if !isnothing(deconstruct_result1017)
                                                unwrapped1018 = deconstruct_result1017
                                                pretty_decimal_type(pp, unwrapped1018)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1767 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1767 = nothing
                                                end
                                                deconstruct_result1015 = _t1767
                                                if !isnothing(deconstruct_result1015)
                                                    unwrapped1016 = deconstruct_result1015
                                                    pretty_boolean_type(pp, unwrapped1016)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1768 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1768 = nothing
                                                    end
                                                    deconstruct_result1013 = _t1768
                                                    if !isnothing(deconstruct_result1013)
                                                        unwrapped1014 = deconstruct_result1013
                                                        pretty_int32_type(pp, unwrapped1014)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1769 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1769 = nothing
                                                        end
                                                        deconstruct_result1011 = _t1769
                                                        if !isnothing(deconstruct_result1011)
                                                            unwrapped1012 = deconstruct_result1011
                                                            pretty_float32_type(pp, unwrapped1012)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1770 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1770 = nothing
                                                            end
                                                            deconstruct_result1009 = _t1770
                                                            if !isnothing(deconstruct_result1009)
                                                                unwrapped1010 = deconstruct_result1009
                                                                pretty_uint32_type(pp, unwrapped1010)
                                                            else
                                                                _dollar_dollar = msg
                                                                if _has_proto_field(_dollar_dollar, Symbol("fixed_type"))
                                                                    _t1771 = _get_oneof_field(_dollar_dollar, :fixed_type)
                                                                else
                                                                    _t1771 = nothing
                                                                end
                                                                deconstruct_result1007 = _t1771
                                                                if !isnothing(deconstruct_result1007)
                                                                    unwrapped1008 = deconstruct_result1007
                                                                    pretty_fixed_type(pp, unwrapped1008)
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
    end
    return nothing
end

function pretty_unspecified_type(pp::PrettyPrinter, msg::Proto.UnspecifiedType)
    fields1038 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields1039 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields1040 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields1041 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields1042 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields1043 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields1044 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields1045 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields1046 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat1051 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat1051)
        write(pp, flat1051)
        return nothing
    else
        _dollar_dollar = msg
        fields1047 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields1048 = fields1047
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field1049 = unwrapped_fields1048[1]
        write(pp, string(field1049))
        newline(pp)
        field1050 = unwrapped_fields1048[2]
        write(pp, string(field1050))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields1052 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields1053 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields1054 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields1055 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_fixed_type(pp::PrettyPrinter, msg::Proto.FixedType)
    flat1058 = try_flat(pp, msg, pretty_fixed_type)
    if !isnothing(flat1058)
        write(pp, flat1058)
        return nothing
    else
        _dollar_dollar = msg
        fields1056 = Int64(_dollar_dollar.length)
        unwrapped_fields1057 = fields1056
        write(pp, "(FIXED")
        indent_sexp!(pp)
        newline(pp)
        write(pp, string(unwrapped_fields1057))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1062 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1062)
        write(pp, flat1062)
        return nothing
    else
        fields1059 = msg
        write(pp, "|")
        if !isempty(fields1059)
            write(pp, " ")
            for (i1772, elem1060) in enumerate(fields1059)
                i1061 = i1772 - 1
                if (i1061 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1060)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1089 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1089)
        write(pp, flat1089)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1773 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1773 = nothing
        end
        deconstruct_result1087 = _t1773
        if !isnothing(deconstruct_result1087)
            unwrapped1088 = deconstruct_result1087
            pretty_true(pp, unwrapped1088)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1774 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1774 = nothing
            end
            deconstruct_result1085 = _t1774
            if !isnothing(deconstruct_result1085)
                unwrapped1086 = deconstruct_result1085
                pretty_false(pp, unwrapped1086)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1775 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1775 = nothing
                end
                deconstruct_result1083 = _t1775
                if !isnothing(deconstruct_result1083)
                    unwrapped1084 = deconstruct_result1083
                    pretty_exists(pp, unwrapped1084)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1776 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1776 = nothing
                    end
                    deconstruct_result1081 = _t1776
                    if !isnothing(deconstruct_result1081)
                        unwrapped1082 = deconstruct_result1081
                        pretty_reduce(pp, unwrapped1082)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1777 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1777 = nothing
                        end
                        deconstruct_result1079 = _t1777
                        if !isnothing(deconstruct_result1079)
                            unwrapped1080 = deconstruct_result1079
                            pretty_conjunction(pp, unwrapped1080)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1778 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1778 = nothing
                            end
                            deconstruct_result1077 = _t1778
                            if !isnothing(deconstruct_result1077)
                                unwrapped1078 = deconstruct_result1077
                                pretty_disjunction(pp, unwrapped1078)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1779 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1779 = nothing
                                end
                                deconstruct_result1075 = _t1779
                                if !isnothing(deconstruct_result1075)
                                    unwrapped1076 = deconstruct_result1075
                                    pretty_not(pp, unwrapped1076)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1780 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1780 = nothing
                                    end
                                    deconstruct_result1073 = _t1780
                                    if !isnothing(deconstruct_result1073)
                                        unwrapped1074 = deconstruct_result1073
                                        pretty_ffi(pp, unwrapped1074)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1781 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1781 = nothing
                                        end
                                        deconstruct_result1071 = _t1781
                                        if !isnothing(deconstruct_result1071)
                                            unwrapped1072 = deconstruct_result1071
                                            pretty_atom(pp, unwrapped1072)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1782 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1782 = nothing
                                            end
                                            deconstruct_result1069 = _t1782
                                            if !isnothing(deconstruct_result1069)
                                                unwrapped1070 = deconstruct_result1069
                                                pretty_pragma(pp, unwrapped1070)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1783 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1783 = nothing
                                                end
                                                deconstruct_result1067 = _t1783
                                                if !isnothing(deconstruct_result1067)
                                                    unwrapped1068 = deconstruct_result1067
                                                    pretty_primitive(pp, unwrapped1068)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1784 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1784 = nothing
                                                    end
                                                    deconstruct_result1065 = _t1784
                                                    if !isnothing(deconstruct_result1065)
                                                        unwrapped1066 = deconstruct_result1065
                                                        pretty_rel_atom(pp, unwrapped1066)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1785 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1785 = nothing
                                                        end
                                                        deconstruct_result1063 = _t1785
                                                        if !isnothing(deconstruct_result1063)
                                                            unwrapped1064 = deconstruct_result1063
                                                            pretty_cast(pp, unwrapped1064)
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
    fields1090 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1091 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1096 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        _dollar_dollar = msg
        _t1786 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1092 = (_t1786, _dollar_dollar.body.value,)
        unwrapped_fields1093 = fields1092
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1094 = unwrapped_fields1093[1]
        pretty_bindings(pp, field1094)
        newline(pp)
        field1095 = unwrapped_fields1093[2]
        pretty_formula(pp, field1095)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1102 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1102)
        write(pp, flat1102)
        return nothing
    else
        _dollar_dollar = msg
        fields1097 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1098 = fields1097
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1099 = unwrapped_fields1098[1]
        pretty_abstraction(pp, field1099)
        newline(pp)
        field1100 = unwrapped_fields1098[2]
        pretty_abstraction(pp, field1100)
        newline(pp)
        field1101 = unwrapped_fields1098[3]
        pretty_terms(pp, field1101)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1106 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1106)
        write(pp, flat1106)
        return nothing
    else
        fields1103 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1103)
            newline(pp)
            for (i1787, elem1104) in enumerate(fields1103)
                i1105 = i1787 - 1
                if (i1105 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1104)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1111 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1111)
        write(pp, flat1111)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1788 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1788 = nothing
        end
        deconstruct_result1109 = _t1788
        if !isnothing(deconstruct_result1109)
            unwrapped1110 = deconstruct_result1109
            pretty_var(pp, unwrapped1110)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1789 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1789 = nothing
            end
            deconstruct_result1107 = _t1789
            if !isnothing(deconstruct_result1107)
                unwrapped1108 = deconstruct_result1107
                pretty_value(pp, unwrapped1108)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1114 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1114)
        write(pp, flat1114)
        return nothing
    else
        _dollar_dollar = msg
        fields1112 = _dollar_dollar.name
        unwrapped_fields1113 = fields1112
        write(pp, unwrapped_fields1113)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1140 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1140)
        write(pp, flat1140)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1790 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1790 = nothing
        end
        deconstruct_result1138 = _t1790
        if !isnothing(deconstruct_result1138)
            unwrapped1139 = deconstruct_result1138
            pretty_date(pp, unwrapped1139)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1791 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1791 = nothing
            end
            deconstruct_result1136 = _t1791
            if !isnothing(deconstruct_result1136)
                unwrapped1137 = deconstruct_result1136
                pretty_datetime(pp, unwrapped1137)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1792 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1792 = nothing
                end
                deconstruct_result1134 = _t1792
                if !isnothing(deconstruct_result1134)
                    unwrapped1135 = deconstruct_result1134
                    write(pp, format_string(pp, unwrapped1135))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1793 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1793 = nothing
                    end
                    deconstruct_result1132 = _t1793
                    if !isnothing(deconstruct_result1132)
                        unwrapped1133 = deconstruct_result1132
                        write(pp, format_int32(pp, unwrapped1133))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1794 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1794 = nothing
                        end
                        deconstruct_result1130 = _t1794
                        if !isnothing(deconstruct_result1130)
                            unwrapped1131 = deconstruct_result1130
                            write(pp, format_int(pp, unwrapped1131))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1795 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1795 = nothing
                            end
                            deconstruct_result1128 = _t1795
                            if !isnothing(deconstruct_result1128)
                                unwrapped1129 = deconstruct_result1128
                                write(pp, format_float32(pp, unwrapped1129))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1796 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1796 = nothing
                                end
                                deconstruct_result1126 = _t1796
                                if !isnothing(deconstruct_result1126)
                                    unwrapped1127 = deconstruct_result1126
                                    write(pp, format_float(pp, unwrapped1127))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1797 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1797 = nothing
                                    end
                                    deconstruct_result1124 = _t1797
                                    if !isnothing(deconstruct_result1124)
                                        unwrapped1125 = deconstruct_result1124
                                        write(pp, format_uint32(pp, unwrapped1125))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1798 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1798 = nothing
                                        end
                                        deconstruct_result1122 = _t1798
                                        if !isnothing(deconstruct_result1122)
                                            unwrapped1123 = deconstruct_result1122
                                            write(pp, format_uint128(pp, unwrapped1123))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1799 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1799 = nothing
                                            end
                                            deconstruct_result1120 = _t1799
                                            if !isnothing(deconstruct_result1120)
                                                unwrapped1121 = deconstruct_result1120
                                                write(pp, format_int128(pp, unwrapped1121))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1800 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1800 = nothing
                                                end
                                                deconstruct_result1118 = _t1800
                                                if !isnothing(deconstruct_result1118)
                                                    unwrapped1119 = deconstruct_result1118
                                                    write(pp, format_decimal(pp, unwrapped1119))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1801 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1801 = nothing
                                                    end
                                                    deconstruct_result1116 = _t1801
                                                    if !isnothing(deconstruct_result1116)
                                                        unwrapped1117 = deconstruct_result1116
                                                        pretty_boolean_value(pp, unwrapped1117)
                                                    else
                                                        fields1115 = msg
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
    flat1146 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1146)
        write(pp, flat1146)
        return nothing
    else
        _dollar_dollar = msg
        fields1141 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1142 = fields1141
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1143 = unwrapped_fields1142[1]
        write(pp, format_int(pp, field1143))
        newline(pp)
        field1144 = unwrapped_fields1142[2]
        write(pp, format_int(pp, field1144))
        newline(pp)
        field1145 = unwrapped_fields1142[3]
        write(pp, format_int(pp, field1145))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1157 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1157)
        write(pp, flat1157)
        return nothing
    else
        _dollar_dollar = msg
        fields1147 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1148 = fields1147
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1149 = unwrapped_fields1148[1]
        write(pp, format_int(pp, field1149))
        newline(pp)
        field1150 = unwrapped_fields1148[2]
        write(pp, format_int(pp, field1150))
        newline(pp)
        field1151 = unwrapped_fields1148[3]
        write(pp, format_int(pp, field1151))
        newline(pp)
        field1152 = unwrapped_fields1148[4]
        write(pp, format_int(pp, field1152))
        newline(pp)
        field1153 = unwrapped_fields1148[5]
        write(pp, format_int(pp, field1153))
        newline(pp)
        field1154 = unwrapped_fields1148[6]
        write(pp, format_int(pp, field1154))
        field1155 = unwrapped_fields1148[7]
        if !isnothing(field1155)
            newline(pp)
            opt_val1156 = field1155
            write(pp, format_int(pp, opt_val1156))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1162 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1162)
        write(pp, flat1162)
        return nothing
    else
        _dollar_dollar = msg
        fields1158 = _dollar_dollar.args
        unwrapped_fields1159 = fields1158
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1159)
            newline(pp)
            for (i1802, elem1160) in enumerate(unwrapped_fields1159)
                i1161 = i1802 - 1
                if (i1161 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1160)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1167 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        _dollar_dollar = msg
        fields1163 = _dollar_dollar.args
        unwrapped_fields1164 = fields1163
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1164)
            newline(pp)
            for (i1803, elem1165) in enumerate(unwrapped_fields1164)
                i1166 = i1803 - 1
                if (i1166 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1165)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1170 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1170)
        write(pp, flat1170)
        return nothing
    else
        _dollar_dollar = msg
        fields1168 = _dollar_dollar.arg
        unwrapped_fields1169 = fields1168
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1169)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1176 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1176)
        write(pp, flat1176)
        return nothing
    else
        _dollar_dollar = msg
        fields1171 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1172 = fields1171
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1173 = unwrapped_fields1172[1]
        pretty_name(pp, field1173)
        newline(pp)
        field1174 = unwrapped_fields1172[2]
        pretty_ffi_args(pp, field1174)
        newline(pp)
        field1175 = unwrapped_fields1172[3]
        pretty_terms(pp, field1175)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1178 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1178)
        write(pp, flat1178)
        return nothing
    else
        fields1177 = msg
        write(pp, ":")
        write(pp, fields1177)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1182 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1182)
        write(pp, flat1182)
        return nothing
    else
        fields1179 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1179)
            newline(pp)
            for (i1804, elem1180) in enumerate(fields1179)
                i1181 = i1804 - 1
                if (i1181 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1180)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1189 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1189)
        write(pp, flat1189)
        return nothing
    else
        _dollar_dollar = msg
        fields1183 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1184 = fields1183
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1185 = unwrapped_fields1184[1]
        pretty_relation_id(pp, field1185)
        field1186 = unwrapped_fields1184[2]
        if !isempty(field1186)
            newline(pp)
            for (i1805, elem1187) in enumerate(field1186)
                i1188 = i1805 - 1
                if (i1188 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1187)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1196 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1196)
        write(pp, flat1196)
        return nothing
    else
        _dollar_dollar = msg
        fields1190 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1191 = fields1190
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1192 = unwrapped_fields1191[1]
        pretty_name(pp, field1192)
        field1193 = unwrapped_fields1191[2]
        if !isempty(field1193)
            newline(pp)
            for (i1806, elem1194) in enumerate(field1193)
                i1195 = i1806 - 1
                if (i1195 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1194)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1212 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1212)
        write(pp, flat1212)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1807 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1807 = nothing
        end
        guard_result1211 = _t1807
        if !isnothing(guard_result1211)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1808 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1808 = nothing
            end
            guard_result1210 = _t1808
            if !isnothing(guard_result1210)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1809 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1809 = nothing
                end
                guard_result1209 = _t1809
                if !isnothing(guard_result1209)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1810 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1810 = nothing
                    end
                    guard_result1208 = _t1810
                    if !isnothing(guard_result1208)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1811 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1811 = nothing
                        end
                        guard_result1207 = _t1811
                        if !isnothing(guard_result1207)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1812 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1812 = nothing
                            end
                            guard_result1206 = _t1812
                            if !isnothing(guard_result1206)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1813 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1813 = nothing
                                end
                                guard_result1205 = _t1813
                                if !isnothing(guard_result1205)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1814 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1814 = nothing
                                    end
                                    guard_result1204 = _t1814
                                    if !isnothing(guard_result1204)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1815 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1815 = nothing
                                        end
                                        guard_result1203 = _t1815
                                        if !isnothing(guard_result1203)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1197 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1198 = fields1197
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1199 = unwrapped_fields1198[1]
                                            pretty_name(pp, field1199)
                                            field1200 = unwrapped_fields1198[2]
                                            if !isempty(field1200)
                                                newline(pp)
                                                for (i1816, elem1201) in enumerate(field1200)
                                                    i1202 = i1816 - 1
                                                    if (i1202 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1201)
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
    flat1217 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1217)
        write(pp, flat1217)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1817 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1817 = nothing
        end
        fields1213 = _t1817
        unwrapped_fields1214 = fields1213
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1215 = unwrapped_fields1214[1]
        pretty_term(pp, field1215)
        newline(pp)
        field1216 = unwrapped_fields1214[2]
        pretty_term(pp, field1216)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1222 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1222)
        write(pp, flat1222)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1818 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1818 = nothing
        end
        fields1218 = _t1818
        unwrapped_fields1219 = fields1218
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1220 = unwrapped_fields1219[1]
        pretty_term(pp, field1220)
        newline(pp)
        field1221 = unwrapped_fields1219[2]
        pretty_term(pp, field1221)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1227 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1227)
        write(pp, flat1227)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1819 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1819 = nothing
        end
        fields1223 = _t1819
        unwrapped_fields1224 = fields1223
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1225 = unwrapped_fields1224[1]
        pretty_term(pp, field1225)
        newline(pp)
        field1226 = unwrapped_fields1224[2]
        pretty_term(pp, field1226)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1232 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1232)
        write(pp, flat1232)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1820 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1820 = nothing
        end
        fields1228 = _t1820
        unwrapped_fields1229 = fields1228
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1230 = unwrapped_fields1229[1]
        pretty_term(pp, field1230)
        newline(pp)
        field1231 = unwrapped_fields1229[2]
        pretty_term(pp, field1231)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1237 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1237)
        write(pp, flat1237)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1821 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1821 = nothing
        end
        fields1233 = _t1821
        unwrapped_fields1234 = fields1233
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1235 = unwrapped_fields1234[1]
        pretty_term(pp, field1235)
        newline(pp)
        field1236 = unwrapped_fields1234[2]
        pretty_term(pp, field1236)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1243 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1243)
        write(pp, flat1243)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1822 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1822 = nothing
        end
        fields1238 = _t1822
        unwrapped_fields1239 = fields1238
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1240 = unwrapped_fields1239[1]
        pretty_term(pp, field1240)
        newline(pp)
        field1241 = unwrapped_fields1239[2]
        pretty_term(pp, field1241)
        newline(pp)
        field1242 = unwrapped_fields1239[3]
        pretty_term(pp, field1242)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1249 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1249)
        write(pp, flat1249)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1823 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1823 = nothing
        end
        fields1244 = _t1823
        unwrapped_fields1245 = fields1244
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1246 = unwrapped_fields1245[1]
        pretty_term(pp, field1246)
        newline(pp)
        field1247 = unwrapped_fields1245[2]
        pretty_term(pp, field1247)
        newline(pp)
        field1248 = unwrapped_fields1245[3]
        pretty_term(pp, field1248)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1255 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1255)
        write(pp, flat1255)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1824 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1824 = nothing
        end
        fields1250 = _t1824
        unwrapped_fields1251 = fields1250
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1252 = unwrapped_fields1251[1]
        pretty_term(pp, field1252)
        newline(pp)
        field1253 = unwrapped_fields1251[2]
        pretty_term(pp, field1253)
        newline(pp)
        field1254 = unwrapped_fields1251[3]
        pretty_term(pp, field1254)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1261 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1261)
        write(pp, flat1261)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1825 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1825 = nothing
        end
        fields1256 = _t1825
        unwrapped_fields1257 = fields1256
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1258 = unwrapped_fields1257[1]
        pretty_term(pp, field1258)
        newline(pp)
        field1259 = unwrapped_fields1257[2]
        pretty_term(pp, field1259)
        newline(pp)
        field1260 = unwrapped_fields1257[3]
        pretty_term(pp, field1260)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1266 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1266)
        write(pp, flat1266)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1826 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1826 = nothing
        end
        deconstruct_result1264 = _t1826
        if !isnothing(deconstruct_result1264)
            unwrapped1265 = deconstruct_result1264
            pretty_specialized_value(pp, unwrapped1265)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1827 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1827 = nothing
            end
            deconstruct_result1262 = _t1827
            if !isnothing(deconstruct_result1262)
                unwrapped1263 = deconstruct_result1262
                pretty_term(pp, unwrapped1263)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1268 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1268)
        write(pp, flat1268)
        return nothing
    else
        fields1267 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1267)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1275 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1275)
        write(pp, flat1275)
        return nothing
    else
        _dollar_dollar = msg
        fields1269 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1270 = fields1269
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1271 = unwrapped_fields1270[1]
        pretty_name(pp, field1271)
        field1272 = unwrapped_fields1270[2]
        if !isempty(field1272)
            newline(pp)
            for (i1828, elem1273) in enumerate(field1272)
                i1274 = i1828 - 1
                if (i1274 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1273)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1280 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1280)
        write(pp, flat1280)
        return nothing
    else
        _dollar_dollar = msg
        fields1276 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1277 = fields1276
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1278 = unwrapped_fields1277[1]
        pretty_term(pp, field1278)
        newline(pp)
        field1279 = unwrapped_fields1277[2]
        pretty_term(pp, field1279)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1284 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1284)
        write(pp, flat1284)
        return nothing
    else
        fields1281 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1281)
            newline(pp)
            for (i1829, elem1282) in enumerate(fields1281)
                i1283 = i1829 - 1
                if (i1283 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1282)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1291 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1291)
        write(pp, flat1291)
        return nothing
    else
        _dollar_dollar = msg
        fields1285 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1286 = fields1285
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1287 = unwrapped_fields1286[1]
        pretty_name(pp, field1287)
        field1288 = unwrapped_fields1286[2]
        if !isempty(field1288)
            newline(pp)
            for (i1830, elem1289) in enumerate(field1288)
                i1290 = i1830 - 1
                if (i1290 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1289)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1300 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1300)
        write(pp, flat1300)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1831 = _dollar_dollar.attrs
        else
            _t1831 = nothing
        end
        fields1292 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1831,)
        unwrapped_fields1293 = fields1292
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1294 = unwrapped_fields1293[1]
        if !isempty(field1294)
            newline(pp)
            for (i1832, elem1295) in enumerate(field1294)
                i1296 = i1832 - 1
                if (i1296 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1295)
            end
        end
        newline(pp)
        field1297 = unwrapped_fields1293[2]
        pretty_script(pp, field1297)
        field1298 = unwrapped_fields1293[3]
        if !isnothing(field1298)
            newline(pp)
            opt_val1299 = field1298
            pretty_attrs(pp, opt_val1299)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1305 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1305)
        write(pp, flat1305)
        return nothing
    else
        _dollar_dollar = msg
        fields1301 = _dollar_dollar.constructs
        unwrapped_fields1302 = fields1301
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1302)
            newline(pp)
            for (i1833, elem1303) in enumerate(unwrapped_fields1302)
                i1304 = i1833 - 1
                if (i1304 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1303)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1310 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1310)
        write(pp, flat1310)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1834 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1834 = nothing
        end
        deconstruct_result1308 = _t1834
        if !isnothing(deconstruct_result1308)
            unwrapped1309 = deconstruct_result1308
            pretty_loop(pp, unwrapped1309)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1835 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1835 = nothing
            end
            deconstruct_result1306 = _t1835
            if !isnothing(deconstruct_result1306)
                unwrapped1307 = deconstruct_result1306
                pretty_instruction(pp, unwrapped1307)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1317 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1317)
        write(pp, flat1317)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1836 = _dollar_dollar.attrs
        else
            _t1836 = nothing
        end
        fields1311 = (_dollar_dollar.init, _dollar_dollar.body, _t1836,)
        unwrapped_fields1312 = fields1311
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1313 = unwrapped_fields1312[1]
        pretty_init(pp, field1313)
        newline(pp)
        field1314 = unwrapped_fields1312[2]
        pretty_script(pp, field1314)
        field1315 = unwrapped_fields1312[3]
        if !isnothing(field1315)
            newline(pp)
            opt_val1316 = field1315
            pretty_attrs(pp, opt_val1316)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1321 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1321)
        write(pp, flat1321)
        return nothing
    else
        fields1318 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1318)
            newline(pp)
            for (i1837, elem1319) in enumerate(fields1318)
                i1320 = i1837 - 1
                if (i1320 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1319)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1332 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1332)
        write(pp, flat1332)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1838 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1838 = nothing
        end
        deconstruct_result1330 = _t1838
        if !isnothing(deconstruct_result1330)
            unwrapped1331 = deconstruct_result1330
            pretty_assign(pp, unwrapped1331)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1839 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1839 = nothing
            end
            deconstruct_result1328 = _t1839
            if !isnothing(deconstruct_result1328)
                unwrapped1329 = deconstruct_result1328
                pretty_upsert(pp, unwrapped1329)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1840 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1840 = nothing
                end
                deconstruct_result1326 = _t1840
                if !isnothing(deconstruct_result1326)
                    unwrapped1327 = deconstruct_result1326
                    pretty_break(pp, unwrapped1327)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1841 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1841 = nothing
                    end
                    deconstruct_result1324 = _t1841
                    if !isnothing(deconstruct_result1324)
                        unwrapped1325 = deconstruct_result1324
                        pretty_monoid_def(pp, unwrapped1325)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1842 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1842 = nothing
                        end
                        deconstruct_result1322 = _t1842
                        if !isnothing(deconstruct_result1322)
                            unwrapped1323 = deconstruct_result1322
                            pretty_monus_def(pp, unwrapped1323)
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
    flat1339 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1339)
        write(pp, flat1339)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1843 = _dollar_dollar.attrs
        else
            _t1843 = nothing
        end
        fields1333 = (_dollar_dollar.name, _dollar_dollar.body, _t1843,)
        unwrapped_fields1334 = fields1333
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1335 = unwrapped_fields1334[1]
        pretty_relation_id(pp, field1335)
        newline(pp)
        field1336 = unwrapped_fields1334[2]
        pretty_abstraction(pp, field1336)
        field1337 = unwrapped_fields1334[3]
        if !isnothing(field1337)
            newline(pp)
            opt_val1338 = field1337
            pretty_attrs(pp, opt_val1338)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1346 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1346)
        write(pp, flat1346)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1844 = _dollar_dollar.attrs
        else
            _t1844 = nothing
        end
        fields1340 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1844,)
        unwrapped_fields1341 = fields1340
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1342 = unwrapped_fields1341[1]
        pretty_relation_id(pp, field1342)
        newline(pp)
        field1343 = unwrapped_fields1341[2]
        pretty_abstraction_with_arity(pp, field1343)
        field1344 = unwrapped_fields1341[3]
        if !isnothing(field1344)
            newline(pp)
            opt_val1345 = field1344
            pretty_attrs(pp, opt_val1345)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1351 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1351)
        write(pp, flat1351)
        return nothing
    else
        _dollar_dollar = msg
        _t1845 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1347 = (_t1845, _dollar_dollar[1].value,)
        unwrapped_fields1348 = fields1347
        write(pp, "(")
        indent!(pp)
        field1349 = unwrapped_fields1348[1]
        pretty_bindings(pp, field1349)
        newline(pp)
        field1350 = unwrapped_fields1348[2]
        pretty_formula(pp, field1350)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1358 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1358)
        write(pp, flat1358)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1846 = _dollar_dollar.attrs
        else
            _t1846 = nothing
        end
        fields1352 = (_dollar_dollar.name, _dollar_dollar.body, _t1846,)
        unwrapped_fields1353 = fields1352
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1354 = unwrapped_fields1353[1]
        pretty_relation_id(pp, field1354)
        newline(pp)
        field1355 = unwrapped_fields1353[2]
        pretty_abstraction(pp, field1355)
        field1356 = unwrapped_fields1353[3]
        if !isnothing(field1356)
            newline(pp)
            opt_val1357 = field1356
            pretty_attrs(pp, opt_val1357)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1366 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1366)
        write(pp, flat1366)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1847 = _dollar_dollar.attrs
        else
            _t1847 = nothing
        end
        fields1359 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1847,)
        unwrapped_fields1360 = fields1359
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1361 = unwrapped_fields1360[1]
        pretty_monoid(pp, field1361)
        newline(pp)
        field1362 = unwrapped_fields1360[2]
        pretty_relation_id(pp, field1362)
        newline(pp)
        field1363 = unwrapped_fields1360[3]
        pretty_abstraction_with_arity(pp, field1363)
        field1364 = unwrapped_fields1360[4]
        if !isnothing(field1364)
            newline(pp)
            opt_val1365 = field1364
            pretty_attrs(pp, opt_val1365)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1375 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1375)
        write(pp, flat1375)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1848 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1848 = nothing
        end
        deconstruct_result1373 = _t1848
        if !isnothing(deconstruct_result1373)
            unwrapped1374 = deconstruct_result1373
            pretty_or_monoid(pp, unwrapped1374)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1849 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1849 = nothing
            end
            deconstruct_result1371 = _t1849
            if !isnothing(deconstruct_result1371)
                unwrapped1372 = deconstruct_result1371
                pretty_min_monoid(pp, unwrapped1372)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1850 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1850 = nothing
                end
                deconstruct_result1369 = _t1850
                if !isnothing(deconstruct_result1369)
                    unwrapped1370 = deconstruct_result1369
                    pretty_max_monoid(pp, unwrapped1370)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1851 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1851 = nothing
                    end
                    deconstruct_result1367 = _t1851
                    if !isnothing(deconstruct_result1367)
                        unwrapped1368 = deconstruct_result1367
                        pretty_sum_monoid(pp, unwrapped1368)
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
    fields1376 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1379 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1379)
        write(pp, flat1379)
        return nothing
    else
        _dollar_dollar = msg
        fields1377 = _dollar_dollar.var"#type"
        unwrapped_fields1378 = fields1377
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1378)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1382 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1382)
        write(pp, flat1382)
        return nothing
    else
        _dollar_dollar = msg
        fields1380 = _dollar_dollar.var"#type"
        unwrapped_fields1381 = fields1380
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1381)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1385 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1385)
        write(pp, flat1385)
        return nothing
    else
        _dollar_dollar = msg
        fields1383 = _dollar_dollar.var"#type"
        unwrapped_fields1384 = fields1383
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1384)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1393 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1393)
        write(pp, flat1393)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1852 = _dollar_dollar.attrs
        else
            _t1852 = nothing
        end
        fields1386 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1852,)
        unwrapped_fields1387 = fields1386
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1388 = unwrapped_fields1387[1]
        pretty_monoid(pp, field1388)
        newline(pp)
        field1389 = unwrapped_fields1387[2]
        pretty_relation_id(pp, field1389)
        newline(pp)
        field1390 = unwrapped_fields1387[3]
        pretty_abstraction_with_arity(pp, field1390)
        field1391 = unwrapped_fields1387[4]
        if !isnothing(field1391)
            newline(pp)
            opt_val1392 = field1391
            pretty_attrs(pp, opt_val1392)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1400 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1400)
        write(pp, flat1400)
        return nothing
    else
        _dollar_dollar = msg
        fields1394 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1395 = fields1394
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1396 = unwrapped_fields1395[1]
        pretty_relation_id(pp, field1396)
        newline(pp)
        field1397 = unwrapped_fields1395[2]
        pretty_abstraction(pp, field1397)
        newline(pp)
        field1398 = unwrapped_fields1395[3]
        pretty_functional_dependency_keys(pp, field1398)
        newline(pp)
        field1399 = unwrapped_fields1395[4]
        pretty_functional_dependency_values(pp, field1399)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1404 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1404)
        write(pp, flat1404)
        return nothing
    else
        fields1401 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1401)
            newline(pp)
            for (i1853, elem1402) in enumerate(fields1401)
                i1403 = i1853 - 1
                if (i1403 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1402)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1408 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1408)
        write(pp, flat1408)
        return nothing
    else
        fields1405 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1405)
            newline(pp)
            for (i1854, elem1406) in enumerate(fields1405)
                i1407 = i1854 - 1
                if (i1407 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1406)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1417 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1417)
        write(pp, flat1417)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1855 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1855 = nothing
        end
        deconstruct_result1415 = _t1855
        if !isnothing(deconstruct_result1415)
            unwrapped1416 = deconstruct_result1415
            pretty_edb(pp, unwrapped1416)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1856 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1856 = nothing
            end
            deconstruct_result1413 = _t1856
            if !isnothing(deconstruct_result1413)
                unwrapped1414 = deconstruct_result1413
                pretty_betree_relation(pp, unwrapped1414)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1857 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1857 = nothing
                end
                deconstruct_result1411 = _t1857
                if !isnothing(deconstruct_result1411)
                    unwrapped1412 = deconstruct_result1411
                    pretty_csv_data(pp, unwrapped1412)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1858 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1858 = nothing
                    end
                    deconstruct_result1409 = _t1858
                    if !isnothing(deconstruct_result1409)
                        unwrapped1410 = deconstruct_result1409
                        pretty_iceberg_data(pp, unwrapped1410)
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
    flat1423 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1423)
        write(pp, flat1423)
        return nothing
    else
        _dollar_dollar = msg
        fields1418 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1419 = fields1418
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1420 = unwrapped_fields1419[1]
        pretty_relation_id(pp, field1420)
        newline(pp)
        field1421 = unwrapped_fields1419[2]
        pretty_edb_path(pp, field1421)
        newline(pp)
        field1422 = unwrapped_fields1419[3]
        pretty_edb_types(pp, field1422)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1427 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1427)
        write(pp, flat1427)
        return nothing
    else
        fields1424 = msg
        write(pp, "[")
        indent!(pp)
        for (i1859, elem1425) in enumerate(fields1424)
            i1426 = i1859 - 1
            if (i1426 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1425))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1431 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1431)
        write(pp, flat1431)
        return nothing
    else
        fields1428 = msg
        write(pp, "[")
        indent!(pp)
        for (i1860, elem1429) in enumerate(fields1428)
            i1430 = i1860 - 1
            if (i1430 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1429)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1436 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1436)
        write(pp, flat1436)
        return nothing
    else
        _dollar_dollar = msg
        fields1432 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1433 = fields1432
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1434 = unwrapped_fields1433[1]
        pretty_relation_id(pp, field1434)
        newline(pp)
        field1435 = unwrapped_fields1433[2]
        pretty_betree_info(pp, field1435)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1442 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1442)
        write(pp, flat1442)
        return nothing
    else
        _dollar_dollar = msg
        _t1861 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1437 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1861,)
        unwrapped_fields1438 = fields1437
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1439 = unwrapped_fields1438[1]
        pretty_betree_info_key_types(pp, field1439)
        newline(pp)
        field1440 = unwrapped_fields1438[2]
        pretty_betree_info_value_types(pp, field1440)
        newline(pp)
        field1441 = unwrapped_fields1438[3]
        pretty_config_dict(pp, field1441)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1446 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1446)
        write(pp, flat1446)
        return nothing
    else
        fields1443 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1443)
            newline(pp)
            for (i1862, elem1444) in enumerate(fields1443)
                i1445 = i1862 - 1
                if (i1445 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1444)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1450 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1450)
        write(pp, flat1450)
        return nothing
    else
        fields1447 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1447)
            newline(pp)
            for (i1863, elem1448) in enumerate(fields1447)
                i1449 = i1863 - 1
                if (i1449 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1448)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1460 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1460)
        write(pp, flat1460)
        return nothing
    else
        _dollar_dollar = msg
        _t1864 = deconstruct_csv_data_columns_optional(pp, _dollar_dollar)
        _t1865 = deconstruct_csv_data_relations_optional(pp, _dollar_dollar)
        fields1451 = (_dollar_dollar.locator, _dollar_dollar.config, _t1864, _t1865, _dollar_dollar.asof,)
        unwrapped_fields1452 = fields1451
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1453 = unwrapped_fields1452[1]
        pretty_csvlocator(pp, field1453)
        newline(pp)
        field1454 = unwrapped_fields1452[2]
        pretty_csv_config(pp, field1454)
        field1455 = unwrapped_fields1452[3]
        if !isnothing(field1455)
            newline(pp)
            opt_val1456 = field1455
            pretty_gnf_columns(pp, opt_val1456)
        end
        field1457 = unwrapped_fields1452[4]
        if !isnothing(field1457)
            newline(pp)
            opt_val1458 = field1457
            pretty_target_relations(pp, opt_val1458)
        end
        newline(pp)
        field1459 = unwrapped_fields1452[5]
        pretty_csv_asof(pp, field1459)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1467 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1467)
        write(pp, flat1467)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1866 = _dollar_dollar.paths
        else
            _t1866 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1867 = String(copy(_dollar_dollar.inline_data))
        else
            _t1867 = nothing
        end
        fields1461 = (_t1866, _t1867,)
        unwrapped_fields1462 = fields1461
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1463 = unwrapped_fields1462[1]
        if !isnothing(field1463)
            newline(pp)
            opt_val1464 = field1463
            pretty_csv_locator_paths(pp, opt_val1464)
        end
        field1465 = unwrapped_fields1462[2]
        if !isnothing(field1465)
            newline(pp)
            opt_val1466 = field1465
            pretty_csv_locator_inline_data(pp, opt_val1466)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1471 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1471)
        write(pp, flat1471)
        return nothing
    else
        fields1468 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1468)
            newline(pp)
            for (i1868, elem1469) in enumerate(fields1468)
                i1470 = i1868 - 1
                if (i1470 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1469))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1473 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1473)
        write(pp, flat1473)
        return nothing
    else
        fields1472 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1472))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1479 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1479)
        write(pp, flat1479)
        return nothing
    else
        _dollar_dollar = msg
        _t1869 = deconstruct_csv_config(pp, _dollar_dollar)
        _t1870 = deconstruct_csv_storage_integration_optional(pp, _dollar_dollar)
        fields1474 = (_t1869, _t1870,)
        unwrapped_fields1475 = fields1474
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1476 = unwrapped_fields1475[1]
        pretty_config_dict(pp, field1476)
        field1477 = unwrapped_fields1475[2]
        if !isnothing(field1477)
            newline(pp)
            opt_val1478 = field1477
            pretty__storage_integration(pp, opt_val1478)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty__storage_integration(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat1481 = try_flat(pp, msg, pretty__storage_integration)
    if !isnothing(flat1481)
        write(pp, flat1481)
        return nothing
    else
        fields1480 = msg
        write(pp, "(storage_integration")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, fields1480)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1485 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1485)
        write(pp, flat1485)
        return nothing
    else
        fields1482 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1482)
            newline(pp)
            for (i1871, elem1483) in enumerate(fields1482)
                i1484 = i1871 - 1
                if (i1484 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1483)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1494 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1494)
        write(pp, flat1494)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1872 = _dollar_dollar.target_id
        else
            _t1872 = nothing
        end
        fields1486 = (_dollar_dollar.column_path, _t1872, _dollar_dollar.types,)
        unwrapped_fields1487 = fields1486
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1488 = unwrapped_fields1487[1]
        pretty_gnf_column_path(pp, field1488)
        field1489 = unwrapped_fields1487[2]
        if !isnothing(field1489)
            newline(pp)
            opt_val1490 = field1489
            pretty_relation_id(pp, opt_val1490)
        end
        newline(pp)
        write(pp, "[")
        field1491 = unwrapped_fields1487[3]
        for (i1873, elem1492) in enumerate(field1491)
            i1493 = i1873 - 1
            if (i1493 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1492)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1501 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1501)
        write(pp, flat1501)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1874 = _dollar_dollar[1]
        else
            _t1874 = nothing
        end
        deconstruct_result1499 = _t1874
        if !isnothing(deconstruct_result1499)
            unwrapped1500 = deconstruct_result1499
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1500))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1875 = _dollar_dollar
            else
                _t1875 = nothing
            end
            deconstruct_result1495 = _t1875
            if !isnothing(deconstruct_result1495)
                unwrapped1496 = deconstruct_result1495
                write(pp, "[")
                indent!(pp)
                for (i1876, elem1497) in enumerate(unwrapped1496)
                    i1498 = i1876 - 1
                    if (i1498 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1497))
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
    flat1508 = try_flat(pp, msg, pretty_target_relations)
    if !isnothing(flat1508)
        write(pp, flat1508)
        return nothing
    else
        _dollar_dollar = msg
        _t1877 = deconstruct_relation_keys(pp, _dollar_dollar)
        _t1878 = deconstruct_load_errors_optional(pp, _dollar_dollar)
        fields1502 = (_t1877, _dollar_dollar, _t1878,)
        unwrapped_fields1503 = fields1502
        write(pp, "(relations")
        indent_sexp!(pp)
        newline(pp)
        field1504 = unwrapped_fields1503[1]
        pretty_relation_keys(pp, field1504)
        newline(pp)
        field1505 = unwrapped_fields1503[2]
        pretty_relation_body(pp, field1505)
        field1506 = unwrapped_fields1503[3]
        if !isnothing(field1506)
            newline(pp)
            opt_val1507 = field1506
            pretty_load_errors(pp, opt_val1507)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_keys(pp::PrettyPrinter, msg::Tuple{Vector{Proto.NamedColumn}, Bool})
    flat1515 = try_flat(pp, msg, pretty_relation_keys)
    if !isnothing(flat1515)
        write(pp, flat1515)
        return nothing
    else
        _dollar_dollar = msg
        if !_dollar_dollar[2]
            _t1879 = _dollar_dollar[1]
        else
            _t1879 = nothing
        end
        deconstruct_result1511 = _t1879
        if !isnothing(deconstruct_result1511)
            unwrapped1512 = deconstruct_result1511
            write(pp, "(keys")
            indent_sexp!(pp)
            if !isempty(unwrapped1512)
                newline(pp)
                for (i1880, elem1513) in enumerate(unwrapped1512)
                    i1514 = i1880 - 1
                    if (i1514 > 0)
                        newline(pp)
                    end
                    pretty_named_column(pp, elem1513)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _dollar_dollar[2]
                _t1881 = ()
            else
                _t1881 = nothing
            end
            deconstruct_result1509 = _t1881
            if !isnothing(deconstruct_result1509)
                unwrapped1510 = deconstruct_result1509
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
    flat1520 = try_flat(pp, msg, pretty_named_column)
    if !isnothing(flat1520)
        write(pp, flat1520)
        return nothing
    else
        _dollar_dollar = msg
        fields1516 = (_dollar_dollar.name, _dollar_dollar.var"#type",)
        unwrapped_fields1517 = fields1516
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1518 = unwrapped_fields1517[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1518))
        newline(pp)
        field1519 = unwrapped_fields1517[2]
        pretty_type(pp, field1519)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_body(pp::PrettyPrinter, msg::Proto.TargetRelations)
    flat1527 = try_flat(pp, msg, pretty_relation_body)
    if !isnothing(flat1527)
        write(pp, flat1527)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("plain"))
            _t1882 = _get_oneof_field(_dollar_dollar, :plain).targets
        else
            _t1882 = nothing
        end
        deconstruct_result1525 = _t1882
        if !isnothing(deconstruct_result1525)
            unwrapped1526 = deconstruct_result1525
            pretty_non_cdc_relations(pp, unwrapped1526)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("cdc"))
                _t1883 = (_get_oneof_field(_dollar_dollar, :cdc).inserts, _get_oneof_field(_dollar_dollar, :cdc).deletes,)
            else
                _t1883 = nothing
            end
            deconstruct_result1521 = _t1883
            if !isnothing(deconstruct_result1521)
                unwrapped1522 = deconstruct_result1521
                field1523 = unwrapped1522[1]
                pretty_cdc_inserts(pp, field1523)
                write(pp, " ")
                field1524 = unwrapped1522[2]
                pretty_cdc_deletes(pp, field1524)
            else
                throw(ParseError("No matching rule for relation_body"))
            end
        end
    end
    return nothing
end

function pretty_non_cdc_relations(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1531 = try_flat(pp, msg, pretty_non_cdc_relations)
    if !isnothing(flat1531)
        write(pp, flat1531)
        return nothing
    else
        fields1528 = msg
        for (i1884, elem1529) in enumerate(fields1528)
            i1530 = i1884 - 1
            if (i1530 > 0)
                newline(pp)
            end
            pretty_target_relation(pp, elem1529)
        end
    end
    return nothing
end

function pretty_target_relation(pp::PrettyPrinter, msg::Proto.TargetRelation)
    flat1538 = try_flat(pp, msg, pretty_target_relation)
    if !isnothing(flat1538)
        write(pp, flat1538)
        return nothing
    else
        _dollar_dollar = msg
        fields1532 = (_dollar_dollar.target_id, _dollar_dollar.values,)
        unwrapped_fields1533 = fields1532
        write(pp, "(relation")
        indent_sexp!(pp)
        newline(pp)
        field1534 = unwrapped_fields1533[1]
        pretty_relation_id(pp, field1534)
        field1535 = unwrapped_fields1533[2]
        if !isempty(field1535)
            newline(pp)
            for (i1885, elem1536) in enumerate(field1535)
                i1537 = i1885 - 1
                if (i1537 > 0)
                    newline(pp)
                end
                pretty_named_column(pp, elem1536)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_inserts(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1542 = try_flat(pp, msg, pretty_cdc_inserts)
    if !isnothing(flat1542)
        write(pp, flat1542)
        return nothing
    else
        fields1539 = msg
        write(pp, "(inserts")
        indent_sexp!(pp)
        if !isempty(fields1539)
            newline(pp)
            for (i1886, elem1540) in enumerate(fields1539)
                i1541 = i1886 - 1
                if (i1541 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1540)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_deletes(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1546 = try_flat(pp, msg, pretty_cdc_deletes)
    if !isnothing(flat1546)
        write(pp, flat1546)
        return nothing
    else
        fields1543 = msg
        write(pp, "(deletes")
        indent_sexp!(pp)
        if !isempty(fields1543)
            newline(pp)
            for (i1887, elem1544) in enumerate(fields1543)
                i1545 = i1887 - 1
                if (i1545 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1544)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_load_errors(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1548 = try_flat(pp, msg, pretty_load_errors)
    if !isnothing(flat1548)
        write(pp, flat1548)
        return nothing
    else
        fields1547 = msg
        write(pp, "(load_errors")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1547)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1550 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1550)
        write(pp, flat1550)
        return nothing
    else
        fields1549 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1549))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1561 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1561)
        write(pp, flat1561)
        return nothing
    else
        _dollar_dollar = msg
        _t1888 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1889 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1551 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1888, _t1889, _dollar_dollar.returns_delta,)
        unwrapped_fields1552 = fields1551
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1553 = unwrapped_fields1552[1]
        pretty_iceberg_locator(pp, field1553)
        newline(pp)
        field1554 = unwrapped_fields1552[2]
        pretty_iceberg_catalog_config(pp, field1554)
        newline(pp)
        field1555 = unwrapped_fields1552[3]
        pretty_gnf_columns(pp, field1555)
        field1556 = unwrapped_fields1552[4]
        if !isnothing(field1556)
            newline(pp)
            opt_val1557 = field1556
            pretty_iceberg_from_snapshot(pp, opt_val1557)
        end
        field1558 = unwrapped_fields1552[5]
        if !isnothing(field1558)
            newline(pp)
            opt_val1559 = field1558
            pretty_iceberg_to_snapshot(pp, opt_val1559)
        end
        newline(pp)
        field1560 = unwrapped_fields1552[6]
        pretty_boolean_value(pp, field1560)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1567 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1567)
        write(pp, flat1567)
        return nothing
    else
        _dollar_dollar = msg
        fields1562 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1563 = fields1562
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1564 = unwrapped_fields1563[1]
        pretty_iceberg_locator_table_name(pp, field1564)
        newline(pp)
        field1565 = unwrapped_fields1563[2]
        pretty_iceberg_locator_namespace(pp, field1565)
        newline(pp)
        field1566 = unwrapped_fields1563[3]
        pretty_iceberg_locator_warehouse(pp, field1566)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1569 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1569)
        write(pp, flat1569)
        return nothing
    else
        fields1568 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1568))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1573 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1573)
        write(pp, flat1573)
        return nothing
    else
        fields1570 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1570)
            newline(pp)
            for (i1890, elem1571) in enumerate(fields1570)
                i1572 = i1890 - 1
                if (i1572 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1571))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1575 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1575)
        write(pp, flat1575)
        return nothing
    else
        fields1574 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1574))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1583 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1583)
        write(pp, flat1583)
        return nothing
    else
        _dollar_dollar = msg
        _t1891 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1576 = (_dollar_dollar.catalog_uri, _t1891, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1577 = fields1576
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1578 = unwrapped_fields1577[1]
        pretty_iceberg_catalog_uri(pp, field1578)
        field1579 = unwrapped_fields1577[2]
        if !isnothing(field1579)
            newline(pp)
            opt_val1580 = field1579
            pretty_iceberg_catalog_config_scope(pp, opt_val1580)
        end
        newline(pp)
        field1581 = unwrapped_fields1577[3]
        pretty_iceberg_properties(pp, field1581)
        newline(pp)
        field1582 = unwrapped_fields1577[4]
        pretty_iceberg_auth_properties(pp, field1582)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1585 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1585)
        write(pp, flat1585)
        return nothing
    else
        fields1584 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1584))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1587 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1587)
        write(pp, flat1587)
        return nothing
    else
        fields1586 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1586))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1591 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1591)
        write(pp, flat1591)
        return nothing
    else
        fields1588 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1588)
            newline(pp)
            for (i1892, elem1589) in enumerate(fields1588)
                i1590 = i1892 - 1
                if (i1590 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1589)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1596 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1596)
        write(pp, flat1596)
        return nothing
    else
        _dollar_dollar = msg
        fields1592 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1593 = fields1592
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1594 = unwrapped_fields1593[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1594))
        newline(pp)
        field1595 = unwrapped_fields1593[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1595))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1600 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1600)
        write(pp, flat1600)
        return nothing
    else
        fields1597 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1597)
            newline(pp)
            for (i1893, elem1598) in enumerate(fields1597)
                i1599 = i1893 - 1
                if (i1599 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1598)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1605 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1605)
        write(pp, flat1605)
        return nothing
    else
        _dollar_dollar = msg
        _t1894 = mask_secret_value(pp, _dollar_dollar)
        fields1601 = (_dollar_dollar[1], _t1894,)
        unwrapped_fields1602 = fields1601
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1603 = unwrapped_fields1602[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1603))
        newline(pp)
        field1604 = unwrapped_fields1602[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1604))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1607 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1607)
        write(pp, flat1607)
        return nothing
    else
        fields1606 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1606))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1609 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1609)
        write(pp, flat1609)
        return nothing
    else
        fields1608 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1608))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1612 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1612)
        write(pp, flat1612)
        return nothing
    else
        _dollar_dollar = msg
        fields1610 = _dollar_dollar.fragment_id
        unwrapped_fields1611 = fields1610
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1611)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1617 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1617)
        write(pp, flat1617)
        return nothing
    else
        _dollar_dollar = msg
        fields1613 = _dollar_dollar.relations
        unwrapped_fields1614 = fields1613
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1614)
            newline(pp)
            for (i1895, elem1615) in enumerate(unwrapped_fields1614)
                i1616 = i1895 - 1
                if (i1616 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1615)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1624 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1624)
        write(pp, flat1624)
        return nothing
    else
        _dollar_dollar = msg
        fields1618 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1619 = fields1618
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1620 = unwrapped_fields1619[1]
        pretty_edb_path(pp, field1620)
        field1621 = unwrapped_fields1619[2]
        if !isempty(field1621)
            newline(pp)
            for (i1896, elem1622) in enumerate(field1621)
                i1623 = i1896 - 1
                if (i1623 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1622)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1629 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1629)
        write(pp, flat1629)
        return nothing
    else
        _dollar_dollar = msg
        fields1625 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1626 = fields1625
        field1627 = unwrapped_fields1626[1]
        pretty_edb_path(pp, field1627)
        write(pp, " ")
        field1628 = unwrapped_fields1626[2]
        pretty_relation_id(pp, field1628)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1633 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1633)
        write(pp, flat1633)
        return nothing
    else
        fields1630 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1630)
            newline(pp)
            for (i1897, elem1631) in enumerate(fields1630)
                i1632 = i1897 - 1
                if (i1632 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1631)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1644 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1644)
        write(pp, flat1644)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1898 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1898 = nothing
        end
        deconstruct_result1642 = _t1898
        if !isnothing(deconstruct_result1642)
            unwrapped1643 = deconstruct_result1642
            pretty_demand(pp, unwrapped1643)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1899 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1899 = nothing
            end
            deconstruct_result1640 = _t1899
            if !isnothing(deconstruct_result1640)
                unwrapped1641 = deconstruct_result1640
                pretty_output(pp, unwrapped1641)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1900 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1900 = nothing
                end
                deconstruct_result1638 = _t1900
                if !isnothing(deconstruct_result1638)
                    unwrapped1639 = deconstruct_result1638
                    pretty_what_if(pp, unwrapped1639)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1901 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1901 = nothing
                    end
                    deconstruct_result1636 = _t1901
                    if !isnothing(deconstruct_result1636)
                        unwrapped1637 = deconstruct_result1636
                        pretty_abort(pp, unwrapped1637)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1902 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1902 = nothing
                        end
                        deconstruct_result1634 = _t1902
                        if !isnothing(deconstruct_result1634)
                            unwrapped1635 = deconstruct_result1634
                            pretty_export(pp, unwrapped1635)
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
    flat1647 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1647)
        write(pp, flat1647)
        return nothing
    else
        _dollar_dollar = msg
        fields1645 = _dollar_dollar.relation_id
        unwrapped_fields1646 = fields1645
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1646)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1652 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1652)
        write(pp, flat1652)
        return nothing
    else
        _dollar_dollar = msg
        fields1648 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1649 = fields1648
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1650 = unwrapped_fields1649[1]
        pretty_name(pp, field1650)
        newline(pp)
        field1651 = unwrapped_fields1649[2]
        pretty_relation_id(pp, field1651)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1657 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1657)
        write(pp, flat1657)
        return nothing
    else
        _dollar_dollar = msg
        fields1653 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1654 = fields1653
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1655 = unwrapped_fields1654[1]
        pretty_name(pp, field1655)
        newline(pp)
        field1656 = unwrapped_fields1654[2]
        pretty_epoch(pp, field1656)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1663 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1663)
        write(pp, flat1663)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1903 = _dollar_dollar.name
        else
            _t1903 = nothing
        end
        fields1658 = (_t1903, _dollar_dollar.relation_id,)
        unwrapped_fields1659 = fields1658
        write(pp, "(abort")
        indent_sexp!(pp)
        field1660 = unwrapped_fields1659[1]
        if !isnothing(field1660)
            newline(pp)
            opt_val1661 = field1660
            pretty_name(pp, opt_val1661)
        end
        newline(pp)
        field1662 = unwrapped_fields1659[2]
        pretty_relation_id(pp, field1662)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1668 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1668)
        write(pp, flat1668)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1904 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1904 = nothing
        end
        deconstruct_result1666 = _t1904
        if !isnothing(deconstruct_result1666)
            unwrapped1667 = deconstruct_result1666
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1667)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1905 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1905 = nothing
            end
            deconstruct_result1664 = _t1905
            if !isnothing(deconstruct_result1664)
                unwrapped1665 = deconstruct_result1664
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1665)
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
    flat1679 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1679)
        write(pp, flat1679)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1907 = deconstruct_export_csv_output_location(pp, _dollar_dollar)
            _t1906 = (_t1907, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1906 = nothing
        end
        deconstruct_result1674 = _t1906
        if !isnothing(deconstruct_result1674)
            unwrapped1675 = deconstruct_result1674
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1676 = unwrapped1675[1]
            pretty_export_csv_output_location(pp, field1676)
            newline(pp)
            field1677 = unwrapped1675[2]
            pretty_export_csv_source(pp, field1677)
            newline(pp)
            field1678 = unwrapped1675[3]
            pretty_csv_config(pp, field1678)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1909 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1908 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1909,)
            else
                _t1908 = nothing
            end
            deconstruct_result1669 = _t1908
            if !isnothing(deconstruct_result1669)
                unwrapped1670 = deconstruct_result1669
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1671 = unwrapped1670[1]
                pretty_export_csv_path(pp, field1671)
                newline(pp)
                field1672 = unwrapped1670[2]
                pretty_export_csv_columns_list(pp, field1672)
                newline(pp)
                field1673 = unwrapped1670[3]
                pretty_config_dict(pp, field1673)
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
    flat1684 = try_flat(pp, msg, pretty_export_csv_output_location)
    if !isnothing(flat1684)
        write(pp, flat1684)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar[1] != ""
            _t1910 = _dollar_dollar[1]
        else
            _t1910 = nothing
        end
        deconstruct_result1682 = _t1910
        if !isnothing(deconstruct_result1682)
            unwrapped1683 = deconstruct_result1682
            write(pp, "(path")
            indent_sexp!(pp)
            newline(pp)
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1683))
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _dollar_dollar[2] != ""
                _t1911 = _dollar_dollar[2]
            else
                _t1911 = nothing
            end
            deconstruct_result1680 = _t1911
            if !isnothing(deconstruct_result1680)
                unwrapped1681 = deconstruct_result1680
                write(pp, "(transaction_output_name")
                indent_sexp!(pp)
                newline(pp)
                pretty_name(pp, unwrapped1681)
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
    flat1691 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1691)
        write(pp, flat1691)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1912 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1912 = nothing
        end
        deconstruct_result1687 = _t1912
        if !isnothing(deconstruct_result1687)
            unwrapped1688 = deconstruct_result1687
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1688)
                newline(pp)
                for (i1913, elem1689) in enumerate(unwrapped1688)
                    i1690 = i1913 - 1
                    if (i1690 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1689)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1914 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1914 = nothing
            end
            deconstruct_result1685 = _t1914
            if !isnothing(deconstruct_result1685)
                unwrapped1686 = deconstruct_result1685
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1686)
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
    flat1696 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1696)
        write(pp, flat1696)
        return nothing
    else
        _dollar_dollar = msg
        fields1692 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1693 = fields1692
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1694 = unwrapped_fields1693[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1694))
        newline(pp)
        field1695 = unwrapped_fields1693[2]
        pretty_relation_id(pp, field1695)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1698 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1698)
        write(pp, flat1698)
        return nothing
    else
        fields1697 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1697))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1702 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1702)
        write(pp, flat1702)
        return nothing
    else
        fields1699 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1699)
            newline(pp)
            for (i1915, elem1700) in enumerate(fields1699)
                i1701 = i1915 - 1
                if (i1701 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1700)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1711 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1711)
        write(pp, flat1711)
        return nothing
    else
        _dollar_dollar = msg
        _t1916 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1703 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1916,)
        unwrapped_fields1704 = fields1703
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1705 = unwrapped_fields1704[1]
        pretty_iceberg_locator(pp, field1705)
        newline(pp)
        field1706 = unwrapped_fields1704[2]
        pretty_iceberg_catalog_config(pp, field1706)
        newline(pp)
        field1707 = unwrapped_fields1704[3]
        pretty_export_iceberg_table_def(pp, field1707)
        newline(pp)
        field1708 = unwrapped_fields1704[4]
        pretty_iceberg_table_properties(pp, field1708)
        field1709 = unwrapped_fields1704[5]
        if !isnothing(field1709)
            newline(pp)
            opt_val1710 = field1709
            pretty_config_dict(pp, opt_val1710)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1713 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1713)
        write(pp, flat1713)
        return nothing
    else
        fields1712 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1712)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1717 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1717)
        write(pp, flat1717)
        return nothing
    else
        fields1714 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1714)
            newline(pp)
            for (i1917, elem1715) in enumerate(fields1714)
                i1716 = i1917 - 1
                if (i1716 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1715)
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
    for (i1972, _rid) in enumerate(msg.ids)
        _idx = i1972 - 1
        newline(pp)
        write(pp, "(")
        _t1973 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1973)
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
    for (i1974, _elem) in enumerate(msg.inserts)
        _idx = i1974 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":deletes (")
    for (i1975, _elem) in enumerate(msg.deletes)
        _idx = i1975 - 1
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
    for (i1976, _elem) in enumerate(msg.keys)
        _idx = i1976 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1977, _elem) in enumerate(msg.values)
        _idx = i1977 - 1
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
    for (i1978, _elem) in enumerate(msg.targets)
        _idx = i1978 - 1
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
    for (i1979, _elem) in enumerate(msg.columns)
        _idx = i1979 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FixedType) = pretty_fixed_type(pp, x)
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
