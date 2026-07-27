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
        _t1907 = nothing
    end
    return nothing
end

function deconstruct_csv_data_columns_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Vector{Proto.GNFColumn}}
    if _has_proto_field(msg, Symbol("relations"))
        return nothing
    else
        _t1908 = nothing
    end
    return msg.columns
end

function deconstruct_csv_data_relations_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Proto.TargetRelations}
    if _has_proto_field(msg, Symbol("relations"))
        return msg.relations
    else
        _t1909 = nothing
    end
    return nothing
end

function deconstruct_export_csv_output_location(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Tuple{String, String}
    return (msg.path, msg.transaction_output_name,)
end

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1910 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1910
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1911 = Proto.Value(value=OneOf(:int_value, v))
    return _t1911
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1912 = Proto.Value(value=OneOf(:float_value, v))
    return _t1912
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1913 = Proto.Value(value=OneOf(:string_value, v))
    return _t1913
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1914 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1914
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1915 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1915
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1916 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1916,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1917 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1917,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1918 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1918,))
            end
        end
    end
    _t1919 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1919,))
    for pair in sort([(k, v) for (k, v) in msg.configuration_values])
        push!(result, pair)
    end
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1920 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1920,))
    _t1921 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1921,))
    if msg.new_line != ""
        _t1922 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1922,))
    end
    _t1923 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1923,))
    _t1924 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1924,))
    _t1925 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1925,))
    if msg.comment != ""
        _t1926 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1926,))
    end
    for missing_string in msg.missing_strings
        _t1927 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1927,))
    end
    _t1928 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1928,))
    _t1929 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1929,))
    _t1930 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1930,))
    if msg.partition_size_mb != 0
        _t1931 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1931,))
    end
    return sort(result)
end

function deconstruct_csv_storage_integration_optional(pp::PrettyPrinter, msg::Proto.CSVConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    if !_has_proto_field(msg, Symbol("storage_integration"))
        return nothing
    else
        _t1932 = nothing
    end
    si = msg.storage_integration
    result = Tuple{String, Proto.Value}[]
    if si.provider != ""
        _t1933 = _make_value_string(pp, si.provider)
        push!(result, ("provider", _t1933,))
    end
    if si.azure_sas_token != ""
        _t1934 = _make_value_string(pp, "***")
        push!(result, ("azure_sas_token", _t1934,))
    end
    if si.s3_region != ""
        _t1935 = _make_value_string(pp, si.s3_region)
        push!(result, ("s3_region", _t1935,))
    end
    if si.s3_access_key_id != ""
        _t1936 = _make_value_string(pp, "***")
        push!(result, ("s3_access_key_id", _t1936,))
    end
    if si.s3_secret_access_key != ""
        _t1937 = _make_value_string(pp, "***")
        push!(result, ("s3_secret_access_key", _t1937,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1938 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1938,))
    _t1939 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1939,))
    _t1940 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1940,))
    _t1941 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1941,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1942 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1942,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1943 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1943,))
        end
    end
    _t1944 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1944,))
    _t1945 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1945,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1946 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1946,))
    end
    if !isnothing(msg.compression)
        _t1947 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1947,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1948 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1948,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1949 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1949,))
    end
    if !isnothing(msg.syntax_delim)
        _t1950 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1950,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1951 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1951,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1952 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1952,))
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
        _t1953 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1954 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1955 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1956 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1956,))
    end
    if msg.target_file_size_bytes != 0
        _t1957 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1957,))
    end
    if msg.compression != ""
        _t1958 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1958,))
    end
    if length(result) == 0
        return nothing
    else
        _t1959 = nothing
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
        _t1960 = nothing
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
    flat863 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat863)
        write(pp, flat863)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1708 = _dollar_dollar.configure
        else
            _t1708 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1709 = _dollar_dollar.sync
        else
            _t1709 = nothing
        end
        fields854 = (_t1708, _t1709, _dollar_dollar.epochs,)
        unwrapped_fields855 = fields854
        write(pp, "(transaction")
        indent_sexp!(pp)
        field856 = unwrapped_fields855[1]
        if !isnothing(field856)
            newline(pp)
            opt_val857 = field856
            pretty_configure(pp, opt_val857)
        end
        field858 = unwrapped_fields855[2]
        if !isnothing(field858)
            newline(pp)
            opt_val859 = field858
            pretty_sync(pp, opt_val859)
        end
        field860 = unwrapped_fields855[3]
        if !isempty(field860)
            newline(pp)
            for (i1710, elem861) in enumerate(field860)
                i862 = i1710 - 1
                if (i862 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem861)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat866 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat866)
        write(pp, flat866)
        return nothing
    else
        _dollar_dollar = msg
        _t1711 = deconstruct_configure(pp, _dollar_dollar)
        fields864 = _t1711
        unwrapped_fields865 = fields864
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields865)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat870 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat870)
        write(pp, flat870)
        return nothing
    else
        fields867 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields867)
            newline(pp)
            for (i1712, elem868) in enumerate(fields867)
                i869 = i1712 - 1
                if (i869 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem868)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat875 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat875)
        write(pp, flat875)
        return nothing
    else
        _dollar_dollar = msg
        fields871 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields872 = fields871
        write(pp, ":")
        field873 = unwrapped_fields872[1]
        write(pp, field873)
        write(pp, " ")
        field874 = unwrapped_fields872[2]
        pretty_raw_value(pp, field874)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat901 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat901)
        write(pp, flat901)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1713 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1713 = nothing
        end
        deconstruct_result899 = _t1713
        if !isnothing(deconstruct_result899)
            unwrapped900 = deconstruct_result899
            pretty_raw_date(pp, unwrapped900)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1714 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1714 = nothing
            end
            deconstruct_result897 = _t1714
            if !isnothing(deconstruct_result897)
                unwrapped898 = deconstruct_result897
                pretty_raw_datetime(pp, unwrapped898)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1715 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1715 = nothing
                end
                deconstruct_result895 = _t1715
                if !isnothing(deconstruct_result895)
                    unwrapped896 = deconstruct_result895
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped896))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1716 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1716 = nothing
                    end
                    deconstruct_result893 = _t1716
                    if !isnothing(deconstruct_result893)
                        unwrapped894 = deconstruct_result893
                        write(pp, (string(Int64(unwrapped894)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1717 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1717 = nothing
                        end
                        deconstruct_result891 = _t1717
                        if !isnothing(deconstruct_result891)
                            unwrapped892 = deconstruct_result891
                            write(pp, string(unwrapped892))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1718 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1718 = nothing
                            end
                            deconstruct_result889 = _t1718
                            if !isnothing(deconstruct_result889)
                                unwrapped890 = deconstruct_result889
                                write(pp, format_float32_literal(unwrapped890))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1719 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1719 = nothing
                                end
                                deconstruct_result887 = _t1719
                                if !isnothing(deconstruct_result887)
                                    unwrapped888 = deconstruct_result887
                                    write(pp, lowercase(string(unwrapped888)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1720 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1720 = nothing
                                    end
                                    deconstruct_result885 = _t1720
                                    if !isnothing(deconstruct_result885)
                                        unwrapped886 = deconstruct_result885
                                        write(pp, (string(Int64(unwrapped886)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1721 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1721 = nothing
                                        end
                                        deconstruct_result883 = _t1721
                                        if !isnothing(deconstruct_result883)
                                            unwrapped884 = deconstruct_result883
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped884))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1722 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1722 = nothing
                                            end
                                            deconstruct_result881 = _t1722
                                            if !isnothing(deconstruct_result881)
                                                unwrapped882 = deconstruct_result881
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped882))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1723 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1723 = nothing
                                                end
                                                deconstruct_result879 = _t1723
                                                if !isnothing(deconstruct_result879)
                                                    unwrapped880 = deconstruct_result879
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped880))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1724 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1724 = nothing
                                                    end
                                                    deconstruct_result877 = _t1724
                                                    if !isnothing(deconstruct_result877)
                                                        unwrapped878 = deconstruct_result877
                                                        pretty_boolean_value(pp, unwrapped878)
                                                    else
                                                        fields876 = msg
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
    flat907 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat907)
        write(pp, flat907)
        return nothing
    else
        _dollar_dollar = msg
        fields902 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields903 = fields902
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field904 = unwrapped_fields903[1]
        write(pp, string(field904))
        newline(pp)
        field905 = unwrapped_fields903[2]
        write(pp, string(field905))
        newline(pp)
        field906 = unwrapped_fields903[3]
        write(pp, string(field906))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat918 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat918)
        write(pp, flat918)
        return nothing
    else
        _dollar_dollar = msg
        fields908 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields909 = fields908
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field910 = unwrapped_fields909[1]
        write(pp, string(field910))
        newline(pp)
        field911 = unwrapped_fields909[2]
        write(pp, string(field911))
        newline(pp)
        field912 = unwrapped_fields909[3]
        write(pp, string(field912))
        newline(pp)
        field913 = unwrapped_fields909[4]
        write(pp, string(field913))
        newline(pp)
        field914 = unwrapped_fields909[5]
        write(pp, string(field914))
        newline(pp)
        field915 = unwrapped_fields909[6]
        write(pp, string(field915))
        field916 = unwrapped_fields909[7]
        if !isnothing(field916)
            newline(pp)
            opt_val917 = field916
            write(pp, string(opt_val917))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1725 = ()
    else
        _t1725 = nothing
    end
    deconstruct_result921 = _t1725
    if !isnothing(deconstruct_result921)
        unwrapped922 = deconstruct_result921
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1726 = ()
        else
            _t1726 = nothing
        end
        deconstruct_result919 = _t1726
        if !isnothing(deconstruct_result919)
            unwrapped920 = deconstruct_result919
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat927 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat927)
        write(pp, flat927)
        return nothing
    else
        _dollar_dollar = msg
        fields923 = _dollar_dollar.fragments
        unwrapped_fields924 = fields923
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields924)
            newline(pp)
            for (i1727, elem925) in enumerate(unwrapped_fields924)
                i926 = i1727 - 1
                if (i926 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem925)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat930 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat930)
        write(pp, flat930)
        return nothing
    else
        _dollar_dollar = msg
        fields928 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields929 = fields928
        write(pp, ":")
        write(pp, unwrapped_fields929)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat937 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat937)
        write(pp, flat937)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1728 = _dollar_dollar.writes
        else
            _t1728 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1729 = _dollar_dollar.reads
        else
            _t1729 = nothing
        end
        fields931 = (_t1728, _t1729,)
        unwrapped_fields932 = fields931
        write(pp, "(epoch")
        indent_sexp!(pp)
        field933 = unwrapped_fields932[1]
        if !isnothing(field933)
            newline(pp)
            opt_val934 = field933
            pretty_epoch_writes(pp, opt_val934)
        end
        field935 = unwrapped_fields932[2]
        if !isnothing(field935)
            newline(pp)
            opt_val936 = field935
            pretty_epoch_reads(pp, opt_val936)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat941 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat941)
        write(pp, flat941)
        return nothing
    else
        fields938 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields938)
            newline(pp)
            for (i1730, elem939) in enumerate(fields938)
                i940 = i1730 - 1
                if (i940 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem939)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat950 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat950)
        write(pp, flat950)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1731 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1731 = nothing
        end
        deconstruct_result948 = _t1731
        if !isnothing(deconstruct_result948)
            unwrapped949 = deconstruct_result948
            pretty_define(pp, unwrapped949)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1732 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1732 = nothing
            end
            deconstruct_result946 = _t1732
            if !isnothing(deconstruct_result946)
                unwrapped947 = deconstruct_result946
                pretty_undefine(pp, unwrapped947)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1733 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1733 = nothing
                end
                deconstruct_result944 = _t1733
                if !isnothing(deconstruct_result944)
                    unwrapped945 = deconstruct_result944
                    pretty_context(pp, unwrapped945)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1734 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1734 = nothing
                    end
                    deconstruct_result942 = _t1734
                    if !isnothing(deconstruct_result942)
                        unwrapped943 = deconstruct_result942
                        pretty_snapshot(pp, unwrapped943)
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
    flat953 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat953)
        write(pp, flat953)
        return nothing
    else
        _dollar_dollar = msg
        fields951 = _dollar_dollar.fragment
        unwrapped_fields952 = fields951
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields952)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat960 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat960)
        write(pp, flat960)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields954 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields955 = fields954
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field956 = unwrapped_fields955[1]
        pretty_new_fragment_id(pp, field956)
        field957 = unwrapped_fields955[2]
        if !isempty(field957)
            newline(pp)
            for (i1735, elem958) in enumerate(field957)
                i959 = i1735 - 1
                if (i959 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem958)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat962 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat962)
        write(pp, flat962)
        return nothing
    else
        fields961 = msg
        pretty_fragment_id(pp, fields961)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat971 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat971)
        write(pp, flat971)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1736 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1736 = nothing
        end
        deconstruct_result969 = _t1736
        if !isnothing(deconstruct_result969)
            unwrapped970 = deconstruct_result969
            pretty_def(pp, unwrapped970)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1737 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1737 = nothing
            end
            deconstruct_result967 = _t1737
            if !isnothing(deconstruct_result967)
                unwrapped968 = deconstruct_result967
                pretty_algorithm(pp, unwrapped968)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1738 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1738 = nothing
                end
                deconstruct_result965 = _t1738
                if !isnothing(deconstruct_result965)
                    unwrapped966 = deconstruct_result965
                    pretty_constraint(pp, unwrapped966)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1739 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1739 = nothing
                    end
                    deconstruct_result963 = _t1739
                    if !isnothing(deconstruct_result963)
                        unwrapped964 = deconstruct_result963
                        pretty_data(pp, unwrapped964)
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
    flat978 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat978)
        write(pp, flat978)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1740 = _dollar_dollar.attrs
        else
            _t1740 = nothing
        end
        fields972 = (_dollar_dollar.name, _dollar_dollar.body, _t1740,)
        unwrapped_fields973 = fields972
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field974 = unwrapped_fields973[1]
        pretty_relation_id(pp, field974)
        newline(pp)
        field975 = unwrapped_fields973[2]
        pretty_abstraction(pp, field975)
        field976 = unwrapped_fields973[3]
        if !isnothing(field976)
            newline(pp)
            opt_val977 = field976
            pretty_attrs(pp, opt_val977)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat983 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat983)
        write(pp, flat983)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1742 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1741 = _t1742
        else
            _t1741 = nothing
        end
        deconstruct_result981 = _t1741
        if !isnothing(deconstruct_result981)
            unwrapped982 = deconstruct_result981
            write(pp, ":")
            write(pp, unwrapped982)
        else
            _dollar_dollar = msg
            _t1743 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result979 = _t1743
            if !isnothing(deconstruct_result979)
                unwrapped980 = deconstruct_result979
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped980))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat988 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat988)
        write(pp, flat988)
        return nothing
    else
        _dollar_dollar = msg
        _t1744 = deconstruct_bindings(pp, _dollar_dollar)
        fields984 = (_t1744, _dollar_dollar.value,)
        unwrapped_fields985 = fields984
        write(pp, "(")
        indent!(pp)
        field986 = unwrapped_fields985[1]
        pretty_bindings(pp, field986)
        newline(pp)
        field987 = unwrapped_fields985[2]
        pretty_formula(pp, field987)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat996 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat996)
        write(pp, flat996)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1745 = _dollar_dollar[2]
        else
            _t1745 = nothing
        end
        fields989 = (_dollar_dollar[1], _t1745,)
        unwrapped_fields990 = fields989
        write(pp, "[")
        indent!(pp)
        field991 = unwrapped_fields990[1]
        for (i1746, elem992) in enumerate(field991)
            i993 = i1746 - 1
            if (i993 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem992)
        end
        field994 = unwrapped_fields990[2]
        if !isnothing(field994)
            newline(pp)
            opt_val995 = field994
            pretty_value_bindings(pp, opt_val995)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat1001 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat1001)
        write(pp, flat1001)
        return nothing
    else
        _dollar_dollar = msg
        fields997 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields998 = fields997
        field999 = unwrapped_fields998[1]
        write(pp, field999)
        write(pp, "::")
        field1000 = unwrapped_fields998[2]
        pretty_type(pp, field1000)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat1030 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat1030)
        write(pp, flat1030)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1747 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1747 = nothing
        end
        deconstruct_result1028 = _t1747
        if !isnothing(deconstruct_result1028)
            unwrapped1029 = deconstruct_result1028
            pretty_unspecified_type(pp, unwrapped1029)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1748 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1748 = nothing
            end
            deconstruct_result1026 = _t1748
            if !isnothing(deconstruct_result1026)
                unwrapped1027 = deconstruct_result1026
                pretty_string_type(pp, unwrapped1027)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1749 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1749 = nothing
                end
                deconstruct_result1024 = _t1749
                if !isnothing(deconstruct_result1024)
                    unwrapped1025 = deconstruct_result1024
                    pretty_int_type(pp, unwrapped1025)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1750 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1750 = nothing
                    end
                    deconstruct_result1022 = _t1750
                    if !isnothing(deconstruct_result1022)
                        unwrapped1023 = deconstruct_result1022
                        pretty_float_type(pp, unwrapped1023)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1751 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1751 = nothing
                        end
                        deconstruct_result1020 = _t1751
                        if !isnothing(deconstruct_result1020)
                            unwrapped1021 = deconstruct_result1020
                            pretty_uint128_type(pp, unwrapped1021)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1752 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1752 = nothing
                            end
                            deconstruct_result1018 = _t1752
                            if !isnothing(deconstruct_result1018)
                                unwrapped1019 = deconstruct_result1018
                                pretty_int128_type(pp, unwrapped1019)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1753 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1753 = nothing
                                end
                                deconstruct_result1016 = _t1753
                                if !isnothing(deconstruct_result1016)
                                    unwrapped1017 = deconstruct_result1016
                                    pretty_date_type(pp, unwrapped1017)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1754 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1754 = nothing
                                    end
                                    deconstruct_result1014 = _t1754
                                    if !isnothing(deconstruct_result1014)
                                        unwrapped1015 = deconstruct_result1014
                                        pretty_datetime_type(pp, unwrapped1015)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1755 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1755 = nothing
                                        end
                                        deconstruct_result1012 = _t1755
                                        if !isnothing(deconstruct_result1012)
                                            unwrapped1013 = deconstruct_result1012
                                            pretty_missing_type(pp, unwrapped1013)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1756 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1756 = nothing
                                            end
                                            deconstruct_result1010 = _t1756
                                            if !isnothing(deconstruct_result1010)
                                                unwrapped1011 = deconstruct_result1010
                                                pretty_decimal_type(pp, unwrapped1011)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1757 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1757 = nothing
                                                end
                                                deconstruct_result1008 = _t1757
                                                if !isnothing(deconstruct_result1008)
                                                    unwrapped1009 = deconstruct_result1008
                                                    pretty_boolean_type(pp, unwrapped1009)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1758 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1758 = nothing
                                                    end
                                                    deconstruct_result1006 = _t1758
                                                    if !isnothing(deconstruct_result1006)
                                                        unwrapped1007 = deconstruct_result1006
                                                        pretty_int32_type(pp, unwrapped1007)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1759 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1759 = nothing
                                                        end
                                                        deconstruct_result1004 = _t1759
                                                        if !isnothing(deconstruct_result1004)
                                                            unwrapped1005 = deconstruct_result1004
                                                            pretty_float32_type(pp, unwrapped1005)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1760 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1760 = nothing
                                                            end
                                                            deconstruct_result1002 = _t1760
                                                            if !isnothing(deconstruct_result1002)
                                                                unwrapped1003 = deconstruct_result1002
                                                                pretty_uint32_type(pp, unwrapped1003)
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
    fields1031 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields1032 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields1033 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields1034 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields1035 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields1036 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields1037 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields1038 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields1039 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat1044 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat1044)
        write(pp, flat1044)
        return nothing
    else
        _dollar_dollar = msg
        fields1040 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields1041 = fields1040
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field1042 = unwrapped_fields1041[1]
        write(pp, string(field1042))
        newline(pp)
        field1043 = unwrapped_fields1041[2]
        write(pp, string(field1043))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields1045 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields1046 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields1047 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields1048 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1052 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1052)
        write(pp, flat1052)
        return nothing
    else
        fields1049 = msg
        write(pp, "|")
        if !isempty(fields1049)
            write(pp, " ")
            for (i1761, elem1050) in enumerate(fields1049)
                i1051 = i1761 - 1
                if (i1051 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1050)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1079 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1079)
        write(pp, flat1079)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1762 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1762 = nothing
        end
        deconstruct_result1077 = _t1762
        if !isnothing(deconstruct_result1077)
            unwrapped1078 = deconstruct_result1077
            pretty_true(pp, unwrapped1078)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1763 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1763 = nothing
            end
            deconstruct_result1075 = _t1763
            if !isnothing(deconstruct_result1075)
                unwrapped1076 = deconstruct_result1075
                pretty_false(pp, unwrapped1076)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1764 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1764 = nothing
                end
                deconstruct_result1073 = _t1764
                if !isnothing(deconstruct_result1073)
                    unwrapped1074 = deconstruct_result1073
                    pretty_exists(pp, unwrapped1074)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1765 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1765 = nothing
                    end
                    deconstruct_result1071 = _t1765
                    if !isnothing(deconstruct_result1071)
                        unwrapped1072 = deconstruct_result1071
                        pretty_reduce(pp, unwrapped1072)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1766 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1766 = nothing
                        end
                        deconstruct_result1069 = _t1766
                        if !isnothing(deconstruct_result1069)
                            unwrapped1070 = deconstruct_result1069
                            pretty_conjunction(pp, unwrapped1070)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1767 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1767 = nothing
                            end
                            deconstruct_result1067 = _t1767
                            if !isnothing(deconstruct_result1067)
                                unwrapped1068 = deconstruct_result1067
                                pretty_disjunction(pp, unwrapped1068)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1768 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1768 = nothing
                                end
                                deconstruct_result1065 = _t1768
                                if !isnothing(deconstruct_result1065)
                                    unwrapped1066 = deconstruct_result1065
                                    pretty_not(pp, unwrapped1066)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1769 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1769 = nothing
                                    end
                                    deconstruct_result1063 = _t1769
                                    if !isnothing(deconstruct_result1063)
                                        unwrapped1064 = deconstruct_result1063
                                        pretty_ffi(pp, unwrapped1064)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1770 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1770 = nothing
                                        end
                                        deconstruct_result1061 = _t1770
                                        if !isnothing(deconstruct_result1061)
                                            unwrapped1062 = deconstruct_result1061
                                            pretty_atom(pp, unwrapped1062)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1771 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1771 = nothing
                                            end
                                            deconstruct_result1059 = _t1771
                                            if !isnothing(deconstruct_result1059)
                                                unwrapped1060 = deconstruct_result1059
                                                pretty_pragma(pp, unwrapped1060)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1772 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1772 = nothing
                                                end
                                                deconstruct_result1057 = _t1772
                                                if !isnothing(deconstruct_result1057)
                                                    unwrapped1058 = deconstruct_result1057
                                                    pretty_primitive(pp, unwrapped1058)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1773 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1773 = nothing
                                                    end
                                                    deconstruct_result1055 = _t1773
                                                    if !isnothing(deconstruct_result1055)
                                                        unwrapped1056 = deconstruct_result1055
                                                        pretty_rel_atom(pp, unwrapped1056)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1774 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1774 = nothing
                                                        end
                                                        deconstruct_result1053 = _t1774
                                                        if !isnothing(deconstruct_result1053)
                                                            unwrapped1054 = deconstruct_result1053
                                                            pretty_cast(pp, unwrapped1054)
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
    fields1080 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1081 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1086 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1086)
        write(pp, flat1086)
        return nothing
    else
        _dollar_dollar = msg
        _t1775 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1082 = (_t1775, _dollar_dollar.body.value,)
        unwrapped_fields1083 = fields1082
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1084 = unwrapped_fields1083[1]
        pretty_bindings(pp, field1084)
        newline(pp)
        field1085 = unwrapped_fields1083[2]
        pretty_formula(pp, field1085)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1092 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        _dollar_dollar = msg
        fields1087 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1088 = fields1087
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1089 = unwrapped_fields1088[1]
        pretty_abstraction(pp, field1089)
        newline(pp)
        field1090 = unwrapped_fields1088[2]
        pretty_abstraction(pp, field1090)
        newline(pp)
        field1091 = unwrapped_fields1088[3]
        pretty_terms(pp, field1091)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1096 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        fields1093 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1093)
            newline(pp)
            for (i1776, elem1094) in enumerate(fields1093)
                i1095 = i1776 - 1
                if (i1095 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1094)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1101 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1101)
        write(pp, flat1101)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1777 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1777 = nothing
        end
        deconstruct_result1099 = _t1777
        if !isnothing(deconstruct_result1099)
            unwrapped1100 = deconstruct_result1099
            pretty_var(pp, unwrapped1100)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1778 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1778 = nothing
            end
            deconstruct_result1097 = _t1778
            if !isnothing(deconstruct_result1097)
                unwrapped1098 = deconstruct_result1097
                pretty_value(pp, unwrapped1098)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1104 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1104)
        write(pp, flat1104)
        return nothing
    else
        _dollar_dollar = msg
        fields1102 = _dollar_dollar.name
        unwrapped_fields1103 = fields1102
        write(pp, unwrapped_fields1103)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1130 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1130)
        write(pp, flat1130)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1779 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1779 = nothing
        end
        deconstruct_result1128 = _t1779
        if !isnothing(deconstruct_result1128)
            unwrapped1129 = deconstruct_result1128
            pretty_date(pp, unwrapped1129)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1780 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1780 = nothing
            end
            deconstruct_result1126 = _t1780
            if !isnothing(deconstruct_result1126)
                unwrapped1127 = deconstruct_result1126
                pretty_datetime(pp, unwrapped1127)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1781 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1781 = nothing
                end
                deconstruct_result1124 = _t1781
                if !isnothing(deconstruct_result1124)
                    unwrapped1125 = deconstruct_result1124
                    write(pp, format_string(pp, unwrapped1125))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1782 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1782 = nothing
                    end
                    deconstruct_result1122 = _t1782
                    if !isnothing(deconstruct_result1122)
                        unwrapped1123 = deconstruct_result1122
                        write(pp, format_int32(pp, unwrapped1123))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1783 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1783 = nothing
                        end
                        deconstruct_result1120 = _t1783
                        if !isnothing(deconstruct_result1120)
                            unwrapped1121 = deconstruct_result1120
                            write(pp, format_int(pp, unwrapped1121))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1784 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1784 = nothing
                            end
                            deconstruct_result1118 = _t1784
                            if !isnothing(deconstruct_result1118)
                                unwrapped1119 = deconstruct_result1118
                                write(pp, format_float32(pp, unwrapped1119))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1785 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1785 = nothing
                                end
                                deconstruct_result1116 = _t1785
                                if !isnothing(deconstruct_result1116)
                                    unwrapped1117 = deconstruct_result1116
                                    write(pp, format_float(pp, unwrapped1117))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1786 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1786 = nothing
                                    end
                                    deconstruct_result1114 = _t1786
                                    if !isnothing(deconstruct_result1114)
                                        unwrapped1115 = deconstruct_result1114
                                        write(pp, format_uint32(pp, unwrapped1115))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1787 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1787 = nothing
                                        end
                                        deconstruct_result1112 = _t1787
                                        if !isnothing(deconstruct_result1112)
                                            unwrapped1113 = deconstruct_result1112
                                            write(pp, format_uint128(pp, unwrapped1113))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1788 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1788 = nothing
                                            end
                                            deconstruct_result1110 = _t1788
                                            if !isnothing(deconstruct_result1110)
                                                unwrapped1111 = deconstruct_result1110
                                                write(pp, format_int128(pp, unwrapped1111))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1789 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1789 = nothing
                                                end
                                                deconstruct_result1108 = _t1789
                                                if !isnothing(deconstruct_result1108)
                                                    unwrapped1109 = deconstruct_result1108
                                                    write(pp, format_decimal(pp, unwrapped1109))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1790 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1790 = nothing
                                                    end
                                                    deconstruct_result1106 = _t1790
                                                    if !isnothing(deconstruct_result1106)
                                                        unwrapped1107 = deconstruct_result1106
                                                        pretty_boolean_value(pp, unwrapped1107)
                                                    else
                                                        fields1105 = msg
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
    flat1136 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1136)
        write(pp, flat1136)
        return nothing
    else
        _dollar_dollar = msg
        fields1131 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1132 = fields1131
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1133 = unwrapped_fields1132[1]
        write(pp, format_int(pp, field1133))
        newline(pp)
        field1134 = unwrapped_fields1132[2]
        write(pp, format_int(pp, field1134))
        newline(pp)
        field1135 = unwrapped_fields1132[3]
        write(pp, format_int(pp, field1135))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1147 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1147)
        write(pp, flat1147)
        return nothing
    else
        _dollar_dollar = msg
        fields1137 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1138 = fields1137
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1139 = unwrapped_fields1138[1]
        write(pp, format_int(pp, field1139))
        newline(pp)
        field1140 = unwrapped_fields1138[2]
        write(pp, format_int(pp, field1140))
        newline(pp)
        field1141 = unwrapped_fields1138[3]
        write(pp, format_int(pp, field1141))
        newline(pp)
        field1142 = unwrapped_fields1138[4]
        write(pp, format_int(pp, field1142))
        newline(pp)
        field1143 = unwrapped_fields1138[5]
        write(pp, format_int(pp, field1143))
        newline(pp)
        field1144 = unwrapped_fields1138[6]
        write(pp, format_int(pp, field1144))
        field1145 = unwrapped_fields1138[7]
        if !isnothing(field1145)
            newline(pp)
            opt_val1146 = field1145
            write(pp, format_int(pp, opt_val1146))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1152 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1152)
        write(pp, flat1152)
        return nothing
    else
        _dollar_dollar = msg
        fields1148 = _dollar_dollar.args
        unwrapped_fields1149 = fields1148
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1149)
            newline(pp)
            for (i1791, elem1150) in enumerate(unwrapped_fields1149)
                i1151 = i1791 - 1
                if (i1151 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1150)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1157 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1157)
        write(pp, flat1157)
        return nothing
    else
        _dollar_dollar = msg
        fields1153 = _dollar_dollar.args
        unwrapped_fields1154 = fields1153
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1154)
            newline(pp)
            for (i1792, elem1155) in enumerate(unwrapped_fields1154)
                i1156 = i1792 - 1
                if (i1156 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1155)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1160 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1160)
        write(pp, flat1160)
        return nothing
    else
        _dollar_dollar = msg
        fields1158 = _dollar_dollar.arg
        unwrapped_fields1159 = fields1158
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1159)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1166 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1166)
        write(pp, flat1166)
        return nothing
    else
        _dollar_dollar = msg
        fields1161 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1162 = fields1161
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1163 = unwrapped_fields1162[1]
        pretty_name(pp, field1163)
        newline(pp)
        field1164 = unwrapped_fields1162[2]
        pretty_ffi_args(pp, field1164)
        newline(pp)
        field1165 = unwrapped_fields1162[3]
        pretty_terms(pp, field1165)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1168 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1168)
        write(pp, flat1168)
        return nothing
    else
        fields1167 = msg
        write(pp, ":")
        write(pp, fields1167)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1172 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1172)
        write(pp, flat1172)
        return nothing
    else
        fields1169 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1169)
            newline(pp)
            for (i1793, elem1170) in enumerate(fields1169)
                i1171 = i1793 - 1
                if (i1171 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1170)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1179 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        _dollar_dollar = msg
        fields1173 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1174 = fields1173
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1175 = unwrapped_fields1174[1]
        pretty_relation_id(pp, field1175)
        field1176 = unwrapped_fields1174[2]
        if !isempty(field1176)
            newline(pp)
            for (i1794, elem1177) in enumerate(field1176)
                i1178 = i1794 - 1
                if (i1178 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1177)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1186 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1186)
        write(pp, flat1186)
        return nothing
    else
        _dollar_dollar = msg
        fields1180 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1181 = fields1180
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1182 = unwrapped_fields1181[1]
        pretty_name(pp, field1182)
        field1183 = unwrapped_fields1181[2]
        if !isempty(field1183)
            newline(pp)
            for (i1795, elem1184) in enumerate(field1183)
                i1185 = i1795 - 1
                if (i1185 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1184)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1202 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1202)
        write(pp, flat1202)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1796 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1796 = nothing
        end
        guard_result1201 = _t1796
        if !isnothing(guard_result1201)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1797 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1797 = nothing
            end
            guard_result1200 = _t1797
            if !isnothing(guard_result1200)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1798 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1798 = nothing
                end
                guard_result1199 = _t1798
                if !isnothing(guard_result1199)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1799 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1799 = nothing
                    end
                    guard_result1198 = _t1799
                    if !isnothing(guard_result1198)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1800 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1800 = nothing
                        end
                        guard_result1197 = _t1800
                        if !isnothing(guard_result1197)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1801 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1801 = nothing
                            end
                            guard_result1196 = _t1801
                            if !isnothing(guard_result1196)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1802 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1802 = nothing
                                end
                                guard_result1195 = _t1802
                                if !isnothing(guard_result1195)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1803 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1803 = nothing
                                    end
                                    guard_result1194 = _t1803
                                    if !isnothing(guard_result1194)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1804 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1804 = nothing
                                        end
                                        guard_result1193 = _t1804
                                        if !isnothing(guard_result1193)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1187 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1188 = fields1187
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1189 = unwrapped_fields1188[1]
                                            pretty_name(pp, field1189)
                                            field1190 = unwrapped_fields1188[2]
                                            if !isempty(field1190)
                                                newline(pp)
                                                for (i1805, elem1191) in enumerate(field1190)
                                                    i1192 = i1805 - 1
                                                    if (i1192 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1191)
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
    flat1207 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1207)
        write(pp, flat1207)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1806 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1806 = nothing
        end
        fields1203 = _t1806
        unwrapped_fields1204 = fields1203
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1205 = unwrapped_fields1204[1]
        pretty_term(pp, field1205)
        newline(pp)
        field1206 = unwrapped_fields1204[2]
        pretty_term(pp, field1206)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1212 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1212)
        write(pp, flat1212)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1807 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1807 = nothing
        end
        fields1208 = _t1807
        unwrapped_fields1209 = fields1208
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1210 = unwrapped_fields1209[1]
        pretty_term(pp, field1210)
        newline(pp)
        field1211 = unwrapped_fields1209[2]
        pretty_term(pp, field1211)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1217 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1217)
        write(pp, flat1217)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1808 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1808 = nothing
        end
        fields1213 = _t1808
        unwrapped_fields1214 = fields1213
        write(pp, "(<=")
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

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1222 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1222)
        write(pp, flat1222)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1809 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1809 = nothing
        end
        fields1218 = _t1809
        unwrapped_fields1219 = fields1218
        write(pp, "(>")
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

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1227 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1227)
        write(pp, flat1227)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1810 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1810 = nothing
        end
        fields1223 = _t1810
        unwrapped_fields1224 = fields1223
        write(pp, "(>=")
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

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1233 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1233)
        write(pp, flat1233)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1811 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1811 = nothing
        end
        fields1228 = _t1811
        unwrapped_fields1229 = fields1228
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1230 = unwrapped_fields1229[1]
        pretty_term(pp, field1230)
        newline(pp)
        field1231 = unwrapped_fields1229[2]
        pretty_term(pp, field1231)
        newline(pp)
        field1232 = unwrapped_fields1229[3]
        pretty_term(pp, field1232)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1239 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1239)
        write(pp, flat1239)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1812 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1812 = nothing
        end
        fields1234 = _t1812
        unwrapped_fields1235 = fields1234
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1236 = unwrapped_fields1235[1]
        pretty_term(pp, field1236)
        newline(pp)
        field1237 = unwrapped_fields1235[2]
        pretty_term(pp, field1237)
        newline(pp)
        field1238 = unwrapped_fields1235[3]
        pretty_term(pp, field1238)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1245 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1245)
        write(pp, flat1245)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1813 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1813 = nothing
        end
        fields1240 = _t1813
        unwrapped_fields1241 = fields1240
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1242 = unwrapped_fields1241[1]
        pretty_term(pp, field1242)
        newline(pp)
        field1243 = unwrapped_fields1241[2]
        pretty_term(pp, field1243)
        newline(pp)
        field1244 = unwrapped_fields1241[3]
        pretty_term(pp, field1244)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1251 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1251)
        write(pp, flat1251)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1814 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1814 = nothing
        end
        fields1246 = _t1814
        unwrapped_fields1247 = fields1246
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1248 = unwrapped_fields1247[1]
        pretty_term(pp, field1248)
        newline(pp)
        field1249 = unwrapped_fields1247[2]
        pretty_term(pp, field1249)
        newline(pp)
        field1250 = unwrapped_fields1247[3]
        pretty_term(pp, field1250)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1256 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1256)
        write(pp, flat1256)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1815 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1815 = nothing
        end
        deconstruct_result1254 = _t1815
        if !isnothing(deconstruct_result1254)
            unwrapped1255 = deconstruct_result1254
            pretty_specialized_value(pp, unwrapped1255)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1816 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1816 = nothing
            end
            deconstruct_result1252 = _t1816
            if !isnothing(deconstruct_result1252)
                unwrapped1253 = deconstruct_result1252
                pretty_term(pp, unwrapped1253)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1258 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1258)
        write(pp, flat1258)
        return nothing
    else
        fields1257 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1257)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1265 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1265)
        write(pp, flat1265)
        return nothing
    else
        _dollar_dollar = msg
        fields1259 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1260 = fields1259
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1261 = unwrapped_fields1260[1]
        pretty_name(pp, field1261)
        field1262 = unwrapped_fields1260[2]
        if !isempty(field1262)
            newline(pp)
            for (i1817, elem1263) in enumerate(field1262)
                i1264 = i1817 - 1
                if (i1264 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1263)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1270 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1270)
        write(pp, flat1270)
        return nothing
    else
        _dollar_dollar = msg
        fields1266 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1267 = fields1266
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1268 = unwrapped_fields1267[1]
        pretty_term(pp, field1268)
        newline(pp)
        field1269 = unwrapped_fields1267[2]
        pretty_term(pp, field1269)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1274 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1274)
        write(pp, flat1274)
        return nothing
    else
        fields1271 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1271)
            newline(pp)
            for (i1818, elem1272) in enumerate(fields1271)
                i1273 = i1818 - 1
                if (i1273 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1272)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1281 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1281)
        write(pp, flat1281)
        return nothing
    else
        _dollar_dollar = msg
        fields1275 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1276 = fields1275
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1277 = unwrapped_fields1276[1]
        pretty_name(pp, field1277)
        field1278 = unwrapped_fields1276[2]
        if !isempty(field1278)
            newline(pp)
            for (i1819, elem1279) in enumerate(field1278)
                i1280 = i1819 - 1
                if (i1280 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1279)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1290 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1290)
        write(pp, flat1290)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1820 = _dollar_dollar.attrs
        else
            _t1820 = nothing
        end
        fields1282 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1820,)
        unwrapped_fields1283 = fields1282
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1284 = unwrapped_fields1283[1]
        if !isempty(field1284)
            newline(pp)
            for (i1821, elem1285) in enumerate(field1284)
                i1286 = i1821 - 1
                if (i1286 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1285)
            end
        end
        newline(pp)
        field1287 = unwrapped_fields1283[2]
        pretty_script(pp, field1287)
        field1288 = unwrapped_fields1283[3]
        if !isnothing(field1288)
            newline(pp)
            opt_val1289 = field1288
            pretty_attrs(pp, opt_val1289)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1295 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1295)
        write(pp, flat1295)
        return nothing
    else
        _dollar_dollar = msg
        fields1291 = _dollar_dollar.constructs
        unwrapped_fields1292 = fields1291
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1292)
            newline(pp)
            for (i1822, elem1293) in enumerate(unwrapped_fields1292)
                i1294 = i1822 - 1
                if (i1294 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1293)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1300 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1300)
        write(pp, flat1300)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1823 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1823 = nothing
        end
        deconstruct_result1298 = _t1823
        if !isnothing(deconstruct_result1298)
            unwrapped1299 = deconstruct_result1298
            pretty_loop(pp, unwrapped1299)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1824 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1824 = nothing
            end
            deconstruct_result1296 = _t1824
            if !isnothing(deconstruct_result1296)
                unwrapped1297 = deconstruct_result1296
                pretty_instruction(pp, unwrapped1297)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1307 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1307)
        write(pp, flat1307)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1825 = _dollar_dollar.attrs
        else
            _t1825 = nothing
        end
        fields1301 = (_dollar_dollar.init, _dollar_dollar.body, _t1825,)
        unwrapped_fields1302 = fields1301
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1303 = unwrapped_fields1302[1]
        pretty_init(pp, field1303)
        newline(pp)
        field1304 = unwrapped_fields1302[2]
        pretty_script(pp, field1304)
        field1305 = unwrapped_fields1302[3]
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

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1311 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1311)
        write(pp, flat1311)
        return nothing
    else
        fields1308 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1308)
            newline(pp)
            for (i1826, elem1309) in enumerate(fields1308)
                i1310 = i1826 - 1
                if (i1310 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1309)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1322 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1322)
        write(pp, flat1322)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1827 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1827 = nothing
        end
        deconstruct_result1320 = _t1827
        if !isnothing(deconstruct_result1320)
            unwrapped1321 = deconstruct_result1320
            pretty_assign(pp, unwrapped1321)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1828 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1828 = nothing
            end
            deconstruct_result1318 = _t1828
            if !isnothing(deconstruct_result1318)
                unwrapped1319 = deconstruct_result1318
                pretty_upsert(pp, unwrapped1319)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1829 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1829 = nothing
                end
                deconstruct_result1316 = _t1829
                if !isnothing(deconstruct_result1316)
                    unwrapped1317 = deconstruct_result1316
                    pretty_break(pp, unwrapped1317)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1830 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1830 = nothing
                    end
                    deconstruct_result1314 = _t1830
                    if !isnothing(deconstruct_result1314)
                        unwrapped1315 = deconstruct_result1314
                        pretty_monoid_def(pp, unwrapped1315)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1831 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1831 = nothing
                        end
                        deconstruct_result1312 = _t1831
                        if !isnothing(deconstruct_result1312)
                            unwrapped1313 = deconstruct_result1312
                            pretty_monus_def(pp, unwrapped1313)
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
    flat1329 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1329)
        write(pp, flat1329)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1832 = _dollar_dollar.attrs
        else
            _t1832 = nothing
        end
        fields1323 = (_dollar_dollar.name, _dollar_dollar.body, _t1832,)
        unwrapped_fields1324 = fields1323
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1325 = unwrapped_fields1324[1]
        pretty_relation_id(pp, field1325)
        newline(pp)
        field1326 = unwrapped_fields1324[2]
        pretty_abstraction(pp, field1326)
        field1327 = unwrapped_fields1324[3]
        if !isnothing(field1327)
            newline(pp)
            opt_val1328 = field1327
            pretty_attrs(pp, opt_val1328)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1336 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1336)
        write(pp, flat1336)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1833 = _dollar_dollar.attrs
        else
            _t1833 = nothing
        end
        fields1330 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1833,)
        unwrapped_fields1331 = fields1330
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1332 = unwrapped_fields1331[1]
        pretty_relation_id(pp, field1332)
        newline(pp)
        field1333 = unwrapped_fields1331[2]
        pretty_abstraction_with_arity(pp, field1333)
        field1334 = unwrapped_fields1331[3]
        if !isnothing(field1334)
            newline(pp)
            opt_val1335 = field1334
            pretty_attrs(pp, opt_val1335)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1341 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1341)
        write(pp, flat1341)
        return nothing
    else
        _dollar_dollar = msg
        _t1834 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1337 = (_t1834, _dollar_dollar[1].value,)
        unwrapped_fields1338 = fields1337
        write(pp, "(")
        indent!(pp)
        field1339 = unwrapped_fields1338[1]
        pretty_bindings(pp, field1339)
        newline(pp)
        field1340 = unwrapped_fields1338[2]
        pretty_formula(pp, field1340)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1348 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1348)
        write(pp, flat1348)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1835 = _dollar_dollar.attrs
        else
            _t1835 = nothing
        end
        fields1342 = (_dollar_dollar.name, _dollar_dollar.body, _t1835,)
        unwrapped_fields1343 = fields1342
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1344 = unwrapped_fields1343[1]
        pretty_relation_id(pp, field1344)
        newline(pp)
        field1345 = unwrapped_fields1343[2]
        pretty_abstraction(pp, field1345)
        field1346 = unwrapped_fields1343[3]
        if !isnothing(field1346)
            newline(pp)
            opt_val1347 = field1346
            pretty_attrs(pp, opt_val1347)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1356 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1356)
        write(pp, flat1356)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1836 = _dollar_dollar.attrs
        else
            _t1836 = nothing
        end
        fields1349 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1836,)
        unwrapped_fields1350 = fields1349
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1351 = unwrapped_fields1350[1]
        pretty_monoid(pp, field1351)
        newline(pp)
        field1352 = unwrapped_fields1350[2]
        pretty_relation_id(pp, field1352)
        newline(pp)
        field1353 = unwrapped_fields1350[3]
        pretty_abstraction_with_arity(pp, field1353)
        field1354 = unwrapped_fields1350[4]
        if !isnothing(field1354)
            newline(pp)
            opt_val1355 = field1354
            pretty_attrs(pp, opt_val1355)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1365 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1365)
        write(pp, flat1365)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1837 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1837 = nothing
        end
        deconstruct_result1363 = _t1837
        if !isnothing(deconstruct_result1363)
            unwrapped1364 = deconstruct_result1363
            pretty_or_monoid(pp, unwrapped1364)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1838 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1838 = nothing
            end
            deconstruct_result1361 = _t1838
            if !isnothing(deconstruct_result1361)
                unwrapped1362 = deconstruct_result1361
                pretty_min_monoid(pp, unwrapped1362)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1839 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1839 = nothing
                end
                deconstruct_result1359 = _t1839
                if !isnothing(deconstruct_result1359)
                    unwrapped1360 = deconstruct_result1359
                    pretty_max_monoid(pp, unwrapped1360)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1840 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1840 = nothing
                    end
                    deconstruct_result1357 = _t1840
                    if !isnothing(deconstruct_result1357)
                        unwrapped1358 = deconstruct_result1357
                        pretty_sum_monoid(pp, unwrapped1358)
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
    fields1366 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1369 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1369)
        write(pp, flat1369)
        return nothing
    else
        _dollar_dollar = msg
        fields1367 = _dollar_dollar.var"#type"
        unwrapped_fields1368 = fields1367
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1368)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1372 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1372)
        write(pp, flat1372)
        return nothing
    else
        _dollar_dollar = msg
        fields1370 = _dollar_dollar.var"#type"
        unwrapped_fields1371 = fields1370
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1371)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1375 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1375)
        write(pp, flat1375)
        return nothing
    else
        _dollar_dollar = msg
        fields1373 = _dollar_dollar.var"#type"
        unwrapped_fields1374 = fields1373
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1374)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1383 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1383)
        write(pp, flat1383)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1841 = _dollar_dollar.attrs
        else
            _t1841 = nothing
        end
        fields1376 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1841,)
        unwrapped_fields1377 = fields1376
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1378 = unwrapped_fields1377[1]
        pretty_monoid(pp, field1378)
        newline(pp)
        field1379 = unwrapped_fields1377[2]
        pretty_relation_id(pp, field1379)
        newline(pp)
        field1380 = unwrapped_fields1377[3]
        pretty_abstraction_with_arity(pp, field1380)
        field1381 = unwrapped_fields1377[4]
        if !isnothing(field1381)
            newline(pp)
            opt_val1382 = field1381
            pretty_attrs(pp, opt_val1382)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1390 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1390)
        write(pp, flat1390)
        return nothing
    else
        _dollar_dollar = msg
        fields1384 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1385 = fields1384
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1386 = unwrapped_fields1385[1]
        pretty_relation_id(pp, field1386)
        newline(pp)
        field1387 = unwrapped_fields1385[2]
        pretty_abstraction(pp, field1387)
        newline(pp)
        field1388 = unwrapped_fields1385[3]
        pretty_functional_dependency_keys(pp, field1388)
        newline(pp)
        field1389 = unwrapped_fields1385[4]
        pretty_functional_dependency_values(pp, field1389)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1394 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1394)
        write(pp, flat1394)
        return nothing
    else
        fields1391 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1391)
            newline(pp)
            for (i1842, elem1392) in enumerate(fields1391)
                i1393 = i1842 - 1
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

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1398 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1398)
        write(pp, flat1398)
        return nothing
    else
        fields1395 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1395)
            newline(pp)
            for (i1843, elem1396) in enumerate(fields1395)
                i1397 = i1843 - 1
                if (i1397 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1396)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1407 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1407)
        write(pp, flat1407)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1844 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1844 = nothing
        end
        deconstruct_result1405 = _t1844
        if !isnothing(deconstruct_result1405)
            unwrapped1406 = deconstruct_result1405
            pretty_edb(pp, unwrapped1406)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1845 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1845 = nothing
            end
            deconstruct_result1403 = _t1845
            if !isnothing(deconstruct_result1403)
                unwrapped1404 = deconstruct_result1403
                pretty_betree_relation(pp, unwrapped1404)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1846 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1846 = nothing
                end
                deconstruct_result1401 = _t1846
                if !isnothing(deconstruct_result1401)
                    unwrapped1402 = deconstruct_result1401
                    pretty_csv_data(pp, unwrapped1402)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1847 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1847 = nothing
                    end
                    deconstruct_result1399 = _t1847
                    if !isnothing(deconstruct_result1399)
                        unwrapped1400 = deconstruct_result1399
                        pretty_iceberg_data(pp, unwrapped1400)
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
    flat1413 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1413)
        write(pp, flat1413)
        return nothing
    else
        _dollar_dollar = msg
        fields1408 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1409 = fields1408
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1410 = unwrapped_fields1409[1]
        pretty_relation_id(pp, field1410)
        newline(pp)
        field1411 = unwrapped_fields1409[2]
        pretty_edb_path(pp, field1411)
        newline(pp)
        field1412 = unwrapped_fields1409[3]
        pretty_edb_types(pp, field1412)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1417 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1417)
        write(pp, flat1417)
        return nothing
    else
        fields1414 = msg
        write(pp, "[")
        indent!(pp)
        for (i1848, elem1415) in enumerate(fields1414)
            i1416 = i1848 - 1
            if (i1416 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1415))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1421 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1421)
        write(pp, flat1421)
        return nothing
    else
        fields1418 = msg
        write(pp, "[")
        indent!(pp)
        for (i1849, elem1419) in enumerate(fields1418)
            i1420 = i1849 - 1
            if (i1420 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1419)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1426 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1426)
        write(pp, flat1426)
        return nothing
    else
        _dollar_dollar = msg
        fields1422 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1423 = fields1422
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1424 = unwrapped_fields1423[1]
        pretty_relation_id(pp, field1424)
        newline(pp)
        field1425 = unwrapped_fields1423[2]
        pretty_betree_info(pp, field1425)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1432 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1432)
        write(pp, flat1432)
        return nothing
    else
        _dollar_dollar = msg
        _t1850 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1427 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1850,)
        unwrapped_fields1428 = fields1427
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1429 = unwrapped_fields1428[1]
        pretty_betree_info_key_types(pp, field1429)
        newline(pp)
        field1430 = unwrapped_fields1428[2]
        pretty_betree_info_value_types(pp, field1430)
        newline(pp)
        field1431 = unwrapped_fields1428[3]
        pretty_config_dict(pp, field1431)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1436 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1436)
        write(pp, flat1436)
        return nothing
    else
        fields1433 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1433)
            newline(pp)
            for (i1851, elem1434) in enumerate(fields1433)
                i1435 = i1851 - 1
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

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1440 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1440)
        write(pp, flat1440)
        return nothing
    else
        fields1437 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1437)
            newline(pp)
            for (i1852, elem1438) in enumerate(fields1437)
                i1439 = i1852 - 1
                if (i1439 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1438)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1450 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1450)
        write(pp, flat1450)
        return nothing
    else
        _dollar_dollar = msg
        _t1853 = deconstruct_csv_data_columns_optional(pp, _dollar_dollar)
        _t1854 = deconstruct_csv_data_relations_optional(pp, _dollar_dollar)
        fields1441 = (_dollar_dollar.locator, _dollar_dollar.config, _t1853, _t1854, _dollar_dollar.asof,)
        unwrapped_fields1442 = fields1441
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1443 = unwrapped_fields1442[1]
        pretty_csvlocator(pp, field1443)
        newline(pp)
        field1444 = unwrapped_fields1442[2]
        pretty_csv_config(pp, field1444)
        field1445 = unwrapped_fields1442[3]
        if !isnothing(field1445)
            newline(pp)
            opt_val1446 = field1445
            pretty_gnf_columns(pp, opt_val1446)
        end
        field1447 = unwrapped_fields1442[4]
        if !isnothing(field1447)
            newline(pp)
            opt_val1448 = field1447
            pretty_target_relations(pp, opt_val1448)
        end
        newline(pp)
        field1449 = unwrapped_fields1442[5]
        pretty_csv_asof(pp, field1449)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1457 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1457)
        write(pp, flat1457)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1855 = _dollar_dollar.paths
        else
            _t1855 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1856 = String(copy(_dollar_dollar.inline_data))
        else
            _t1856 = nothing
        end
        fields1451 = (_t1855, _t1856,)
        unwrapped_fields1452 = fields1451
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1453 = unwrapped_fields1452[1]
        if !isnothing(field1453)
            newline(pp)
            opt_val1454 = field1453
            pretty_csv_locator_paths(pp, opt_val1454)
        end
        field1455 = unwrapped_fields1452[2]
        if !isnothing(field1455)
            newline(pp)
            opt_val1456 = field1455
            pretty_csv_locator_inline_data(pp, opt_val1456)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1461 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1461)
        write(pp, flat1461)
        return nothing
    else
        fields1458 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1458)
            newline(pp)
            for (i1857, elem1459) in enumerate(fields1458)
                i1460 = i1857 - 1
                if (i1460 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1459))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1463 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1463)
        write(pp, flat1463)
        return nothing
    else
        fields1462 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1462))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1469 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1469)
        write(pp, flat1469)
        return nothing
    else
        _dollar_dollar = msg
        _t1858 = deconstruct_csv_config(pp, _dollar_dollar)
        _t1859 = deconstruct_csv_storage_integration_optional(pp, _dollar_dollar)
        fields1464 = (_t1858, _t1859,)
        unwrapped_fields1465 = fields1464
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1466 = unwrapped_fields1465[1]
        pretty_config_dict(pp, field1466)
        field1467 = unwrapped_fields1465[2]
        if !isnothing(field1467)
            newline(pp)
            opt_val1468 = field1467
            pretty__storage_integration(pp, opt_val1468)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty__storage_integration(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat1471 = try_flat(pp, msg, pretty__storage_integration)
    if !isnothing(flat1471)
        write(pp, flat1471)
        return nothing
    else
        fields1470 = msg
        write(pp, "(storage_integration")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, fields1470)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1475 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1475)
        write(pp, flat1475)
        return nothing
    else
        fields1472 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1472)
            newline(pp)
            for (i1860, elem1473) in enumerate(fields1472)
                i1474 = i1860 - 1
                if (i1474 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1473)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1484 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1484)
        write(pp, flat1484)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1861 = _dollar_dollar.target_id
        else
            _t1861 = nothing
        end
        fields1476 = (_dollar_dollar.column_path, _t1861, _dollar_dollar.types,)
        unwrapped_fields1477 = fields1476
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1478 = unwrapped_fields1477[1]
        pretty_gnf_column_path(pp, field1478)
        field1479 = unwrapped_fields1477[2]
        if !isnothing(field1479)
            newline(pp)
            opt_val1480 = field1479
            pretty_relation_id(pp, opt_val1480)
        end
        newline(pp)
        write(pp, "[")
        field1481 = unwrapped_fields1477[3]
        for (i1862, elem1482) in enumerate(field1481)
            i1483 = i1862 - 1
            if (i1483 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1482)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1491 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1491)
        write(pp, flat1491)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1863 = _dollar_dollar[1]
        else
            _t1863 = nothing
        end
        deconstruct_result1489 = _t1863
        if !isnothing(deconstruct_result1489)
            unwrapped1490 = deconstruct_result1489
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1490))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1864 = _dollar_dollar
            else
                _t1864 = nothing
            end
            deconstruct_result1485 = _t1864
            if !isnothing(deconstruct_result1485)
                unwrapped1486 = deconstruct_result1485
                write(pp, "[")
                indent!(pp)
                for (i1865, elem1487) in enumerate(unwrapped1486)
                    i1488 = i1865 - 1
                    if (i1488 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1487))
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
    flat1498 = try_flat(pp, msg, pretty_target_relations)
    if !isnothing(flat1498)
        write(pp, flat1498)
        return nothing
    else
        _dollar_dollar = msg
        _t1866 = deconstruct_relation_keys(pp, _dollar_dollar)
        _t1867 = deconstruct_load_errors_optional(pp, _dollar_dollar)
        fields1492 = (_t1866, _dollar_dollar, _t1867,)
        unwrapped_fields1493 = fields1492
        write(pp, "(relations")
        indent_sexp!(pp)
        newline(pp)
        field1494 = unwrapped_fields1493[1]
        pretty_relation_keys(pp, field1494)
        newline(pp)
        field1495 = unwrapped_fields1493[2]
        pretty_relation_body(pp, field1495)
        field1496 = unwrapped_fields1493[3]
        if !isnothing(field1496)
            newline(pp)
            opt_val1497 = field1496
            pretty_load_errors(pp, opt_val1497)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_keys(pp::PrettyPrinter, msg::Tuple{Vector{Proto.NamedColumn}, Bool})
    flat1505 = try_flat(pp, msg, pretty_relation_keys)
    if !isnothing(flat1505)
        write(pp, flat1505)
        return nothing
    else
        _dollar_dollar = msg
        if !_dollar_dollar[2]
            _t1868 = _dollar_dollar[1]
        else
            _t1868 = nothing
        end
        deconstruct_result1501 = _t1868
        if !isnothing(deconstruct_result1501)
            unwrapped1502 = deconstruct_result1501
            write(pp, "(keys")
            indent_sexp!(pp)
            if !isempty(unwrapped1502)
                newline(pp)
                for (i1869, elem1503) in enumerate(unwrapped1502)
                    i1504 = i1869 - 1
                    if (i1504 > 0)
                        newline(pp)
                    end
                    pretty_named_column(pp, elem1503)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _dollar_dollar[2]
                _t1870 = ()
            else
                _t1870 = nothing
            end
            deconstruct_result1499 = _t1870
            if !isnothing(deconstruct_result1499)
                unwrapped1500 = deconstruct_result1499
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
    flat1510 = try_flat(pp, msg, pretty_named_column)
    if !isnothing(flat1510)
        write(pp, flat1510)
        return nothing
    else
        _dollar_dollar = msg
        fields1506 = (_dollar_dollar.name, _dollar_dollar.var"#type",)
        unwrapped_fields1507 = fields1506
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1508 = unwrapped_fields1507[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1508))
        newline(pp)
        field1509 = unwrapped_fields1507[2]
        pretty_type(pp, field1509)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_body(pp::PrettyPrinter, msg::Proto.TargetRelations)
    flat1517 = try_flat(pp, msg, pretty_relation_body)
    if !isnothing(flat1517)
        write(pp, flat1517)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("plain"))
            _t1871 = _get_oneof_field(_dollar_dollar, :plain).targets
        else
            _t1871 = nothing
        end
        deconstruct_result1515 = _t1871
        if !isnothing(deconstruct_result1515)
            unwrapped1516 = deconstruct_result1515
            pretty_non_cdc_relations(pp, unwrapped1516)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("cdc"))
                _t1872 = (_get_oneof_field(_dollar_dollar, :cdc).inserts, _get_oneof_field(_dollar_dollar, :cdc).deletes,)
            else
                _t1872 = nothing
            end
            deconstruct_result1511 = _t1872
            if !isnothing(deconstruct_result1511)
                unwrapped1512 = deconstruct_result1511
                field1513 = unwrapped1512[1]
                pretty_cdc_inserts(pp, field1513)
                write(pp, " ")
                field1514 = unwrapped1512[2]
                pretty_cdc_deletes(pp, field1514)
            else
                throw(ParseError("No matching rule for relation_body"))
            end
        end
    end
    return nothing
end

function pretty_non_cdc_relations(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1521 = try_flat(pp, msg, pretty_non_cdc_relations)
    if !isnothing(flat1521)
        write(pp, flat1521)
        return nothing
    else
        fields1518 = msg
        for (i1873, elem1519) in enumerate(fields1518)
            i1520 = i1873 - 1
            if (i1520 > 0)
                newline(pp)
            end
            pretty_target_relation(pp, elem1519)
        end
    end
    return nothing
end

function pretty_target_relation(pp::PrettyPrinter, msg::Proto.TargetRelation)
    flat1528 = try_flat(pp, msg, pretty_target_relation)
    if !isnothing(flat1528)
        write(pp, flat1528)
        return nothing
    else
        _dollar_dollar = msg
        fields1522 = (_dollar_dollar.target_id, _dollar_dollar.values,)
        unwrapped_fields1523 = fields1522
        write(pp, "(relation")
        indent_sexp!(pp)
        newline(pp)
        field1524 = unwrapped_fields1523[1]
        pretty_relation_id(pp, field1524)
        field1525 = unwrapped_fields1523[2]
        if !isempty(field1525)
            newline(pp)
            for (i1874, elem1526) in enumerate(field1525)
                i1527 = i1874 - 1
                if (i1527 > 0)
                    newline(pp)
                end
                pretty_named_column(pp, elem1526)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_inserts(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1532 = try_flat(pp, msg, pretty_cdc_inserts)
    if !isnothing(flat1532)
        write(pp, flat1532)
        return nothing
    else
        fields1529 = msg
        write(pp, "(inserts")
        indent_sexp!(pp)
        if !isempty(fields1529)
            newline(pp)
            for (i1875, elem1530) in enumerate(fields1529)
                i1531 = i1875 - 1
                if (i1531 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1530)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_deletes(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1536 = try_flat(pp, msg, pretty_cdc_deletes)
    if !isnothing(flat1536)
        write(pp, flat1536)
        return nothing
    else
        fields1533 = msg
        write(pp, "(deletes")
        indent_sexp!(pp)
        if !isempty(fields1533)
            newline(pp)
            for (i1876, elem1534) in enumerate(fields1533)
                i1535 = i1876 - 1
                if (i1535 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1534)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_load_errors(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1538 = try_flat(pp, msg, pretty_load_errors)
    if !isnothing(flat1538)
        write(pp, flat1538)
        return nothing
    else
        fields1537 = msg
        write(pp, "(load_errors")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1537)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1540 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1540)
        write(pp, flat1540)
        return nothing
    else
        fields1539 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1539))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1551 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1551)
        write(pp, flat1551)
        return nothing
    else
        _dollar_dollar = msg
        _t1877 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1878 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1541 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1877, _t1878, _dollar_dollar.returns_delta,)
        unwrapped_fields1542 = fields1541
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1543 = unwrapped_fields1542[1]
        pretty_iceberg_locator(pp, field1543)
        newline(pp)
        field1544 = unwrapped_fields1542[2]
        pretty_iceberg_catalog_config(pp, field1544)
        newline(pp)
        field1545 = unwrapped_fields1542[3]
        pretty_gnf_columns(pp, field1545)
        field1546 = unwrapped_fields1542[4]
        if !isnothing(field1546)
            newline(pp)
            opt_val1547 = field1546
            pretty_iceberg_from_snapshot(pp, opt_val1547)
        end
        field1548 = unwrapped_fields1542[5]
        if !isnothing(field1548)
            newline(pp)
            opt_val1549 = field1548
            pretty_iceberg_to_snapshot(pp, opt_val1549)
        end
        newline(pp)
        field1550 = unwrapped_fields1542[6]
        pretty_boolean_value(pp, field1550)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1557 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1557)
        write(pp, flat1557)
        return nothing
    else
        _dollar_dollar = msg
        fields1552 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1553 = fields1552
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1554 = unwrapped_fields1553[1]
        pretty_iceberg_locator_table_name(pp, field1554)
        newline(pp)
        field1555 = unwrapped_fields1553[2]
        pretty_iceberg_locator_namespace(pp, field1555)
        newline(pp)
        field1556 = unwrapped_fields1553[3]
        pretty_iceberg_locator_warehouse(pp, field1556)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1559 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1559)
        write(pp, flat1559)
        return nothing
    else
        fields1558 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1558))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1563 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1563)
        write(pp, flat1563)
        return nothing
    else
        fields1560 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1560)
            newline(pp)
            for (i1879, elem1561) in enumerate(fields1560)
                i1562 = i1879 - 1
                if (i1562 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1561))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1565 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1565)
        write(pp, flat1565)
        return nothing
    else
        fields1564 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1564))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1573 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1573)
        write(pp, flat1573)
        return nothing
    else
        _dollar_dollar = msg
        _t1880 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1566 = (_dollar_dollar.catalog_uri, _t1880, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1567 = fields1566
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1568 = unwrapped_fields1567[1]
        pretty_iceberg_catalog_uri(pp, field1568)
        field1569 = unwrapped_fields1567[2]
        if !isnothing(field1569)
            newline(pp)
            opt_val1570 = field1569
            pretty_iceberg_catalog_config_scope(pp, opt_val1570)
        end
        newline(pp)
        field1571 = unwrapped_fields1567[3]
        pretty_iceberg_properties(pp, field1571)
        newline(pp)
        field1572 = unwrapped_fields1567[4]
        pretty_iceberg_auth_properties(pp, field1572)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1575 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1575)
        write(pp, flat1575)
        return nothing
    else
        fields1574 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1574))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1577 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1577)
        write(pp, flat1577)
        return nothing
    else
        fields1576 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1576))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1581 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1581)
        write(pp, flat1581)
        return nothing
    else
        fields1578 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1578)
            newline(pp)
            for (i1881, elem1579) in enumerate(fields1578)
                i1580 = i1881 - 1
                if (i1580 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1579)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1586 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1586)
        write(pp, flat1586)
        return nothing
    else
        _dollar_dollar = msg
        fields1582 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1583 = fields1582
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1584 = unwrapped_fields1583[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1584))
        newline(pp)
        field1585 = unwrapped_fields1583[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1585))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1590 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1590)
        write(pp, flat1590)
        return nothing
    else
        fields1587 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1587)
            newline(pp)
            for (i1882, elem1588) in enumerate(fields1587)
                i1589 = i1882 - 1
                if (i1589 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1588)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1595 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1595)
        write(pp, flat1595)
        return nothing
    else
        _dollar_dollar = msg
        _t1883 = mask_secret_value(pp, _dollar_dollar)
        fields1591 = (_dollar_dollar[1], _t1883,)
        unwrapped_fields1592 = fields1591
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1593 = unwrapped_fields1592[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1593))
        newline(pp)
        field1594 = unwrapped_fields1592[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1594))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1597 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1597)
        write(pp, flat1597)
        return nothing
    else
        fields1596 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1596))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1599 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1599)
        write(pp, flat1599)
        return nothing
    else
        fields1598 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1598))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1602 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1602)
        write(pp, flat1602)
        return nothing
    else
        _dollar_dollar = msg
        fields1600 = _dollar_dollar.fragment_id
        unwrapped_fields1601 = fields1600
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1601)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1607 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1607)
        write(pp, flat1607)
        return nothing
    else
        _dollar_dollar = msg
        fields1603 = _dollar_dollar.relations
        unwrapped_fields1604 = fields1603
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1604)
            newline(pp)
            for (i1884, elem1605) in enumerate(unwrapped_fields1604)
                i1606 = i1884 - 1
                if (i1606 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1605)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1614 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1614)
        write(pp, flat1614)
        return nothing
    else
        _dollar_dollar = msg
        fields1608 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1609 = fields1608
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1610 = unwrapped_fields1609[1]
        pretty_edb_path(pp, field1610)
        field1611 = unwrapped_fields1609[2]
        if !isempty(field1611)
            newline(pp)
            for (i1885, elem1612) in enumerate(field1611)
                i1613 = i1885 - 1
                if (i1613 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1612)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1619 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1619)
        write(pp, flat1619)
        return nothing
    else
        _dollar_dollar = msg
        fields1615 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1616 = fields1615
        field1617 = unwrapped_fields1616[1]
        pretty_edb_path(pp, field1617)
        write(pp, " ")
        field1618 = unwrapped_fields1616[2]
        pretty_relation_id(pp, field1618)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1623 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1623)
        write(pp, flat1623)
        return nothing
    else
        fields1620 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1620)
            newline(pp)
            for (i1886, elem1621) in enumerate(fields1620)
                i1622 = i1886 - 1
                if (i1622 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1621)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1634 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1634)
        write(pp, flat1634)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1887 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1887 = nothing
        end
        deconstruct_result1632 = _t1887
        if !isnothing(deconstruct_result1632)
            unwrapped1633 = deconstruct_result1632
            pretty_demand(pp, unwrapped1633)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1888 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1888 = nothing
            end
            deconstruct_result1630 = _t1888
            if !isnothing(deconstruct_result1630)
                unwrapped1631 = deconstruct_result1630
                pretty_output(pp, unwrapped1631)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1889 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1889 = nothing
                end
                deconstruct_result1628 = _t1889
                if !isnothing(deconstruct_result1628)
                    unwrapped1629 = deconstruct_result1628
                    pretty_what_if(pp, unwrapped1629)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1890 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1890 = nothing
                    end
                    deconstruct_result1626 = _t1890
                    if !isnothing(deconstruct_result1626)
                        unwrapped1627 = deconstruct_result1626
                        pretty_abort(pp, unwrapped1627)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1891 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1891 = nothing
                        end
                        deconstruct_result1624 = _t1891
                        if !isnothing(deconstruct_result1624)
                            unwrapped1625 = deconstruct_result1624
                            pretty_export(pp, unwrapped1625)
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
    flat1637 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1637)
        write(pp, flat1637)
        return nothing
    else
        _dollar_dollar = msg
        fields1635 = _dollar_dollar.relation_id
        unwrapped_fields1636 = fields1635
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1636)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1642 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1642)
        write(pp, flat1642)
        return nothing
    else
        _dollar_dollar = msg
        fields1638 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1639 = fields1638
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1640 = unwrapped_fields1639[1]
        pretty_name(pp, field1640)
        newline(pp)
        field1641 = unwrapped_fields1639[2]
        pretty_relation_id(pp, field1641)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1647 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1647)
        write(pp, flat1647)
        return nothing
    else
        _dollar_dollar = msg
        fields1643 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1644 = fields1643
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1645 = unwrapped_fields1644[1]
        pretty_name(pp, field1645)
        newline(pp)
        field1646 = unwrapped_fields1644[2]
        pretty_epoch(pp, field1646)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1653 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1653)
        write(pp, flat1653)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1892 = _dollar_dollar.name
        else
            _t1892 = nothing
        end
        fields1648 = (_t1892, _dollar_dollar.relation_id,)
        unwrapped_fields1649 = fields1648
        write(pp, "(abort")
        indent_sexp!(pp)
        field1650 = unwrapped_fields1649[1]
        if !isnothing(field1650)
            newline(pp)
            opt_val1651 = field1650
            pretty_name(pp, opt_val1651)
        end
        newline(pp)
        field1652 = unwrapped_fields1649[2]
        pretty_relation_id(pp, field1652)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1658 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1658)
        write(pp, flat1658)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1893 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1893 = nothing
        end
        deconstruct_result1656 = _t1893
        if !isnothing(deconstruct_result1656)
            unwrapped1657 = deconstruct_result1656
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1657)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1894 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1894 = nothing
            end
            deconstruct_result1654 = _t1894
            if !isnothing(deconstruct_result1654)
                unwrapped1655 = deconstruct_result1654
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1655)
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
    flat1669 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1669)
        write(pp, flat1669)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1896 = deconstruct_export_csv_output_location(pp, _dollar_dollar)
            _t1895 = (_t1896, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1895 = nothing
        end
        deconstruct_result1664 = _t1895
        if !isnothing(deconstruct_result1664)
            unwrapped1665 = deconstruct_result1664
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1666 = unwrapped1665[1]
            pretty_export_csv_output_location(pp, field1666)
            newline(pp)
            field1667 = unwrapped1665[2]
            pretty_export_csv_source(pp, field1667)
            newline(pp)
            field1668 = unwrapped1665[3]
            pretty_csv_config(pp, field1668)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1898 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1897 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1898,)
            else
                _t1897 = nothing
            end
            deconstruct_result1659 = _t1897
            if !isnothing(deconstruct_result1659)
                unwrapped1660 = deconstruct_result1659
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1661 = unwrapped1660[1]
                pretty_export_csv_path(pp, field1661)
                newline(pp)
                field1662 = unwrapped1660[2]
                pretty_export_csv_columns_list(pp, field1662)
                newline(pp)
                field1663 = unwrapped1660[3]
                pretty_config_dict(pp, field1663)
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
    flat1674 = try_flat(pp, msg, pretty_export_csv_output_location)
    if !isnothing(flat1674)
        write(pp, flat1674)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar[1] != ""
            _t1899 = _dollar_dollar[1]
        else
            _t1899 = nothing
        end
        deconstruct_result1672 = _t1899
        if !isnothing(deconstruct_result1672)
            unwrapped1673 = deconstruct_result1672
            write(pp, "(path")
            indent_sexp!(pp)
            newline(pp)
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1673))
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _dollar_dollar[2] != ""
                _t1900 = _dollar_dollar[2]
            else
                _t1900 = nothing
            end
            deconstruct_result1670 = _t1900
            if !isnothing(deconstruct_result1670)
                unwrapped1671 = deconstruct_result1670
                write(pp, "(transaction_output_name")
                indent_sexp!(pp)
                newline(pp)
                pretty_name(pp, unwrapped1671)
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
    flat1681 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1681)
        write(pp, flat1681)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1901 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1901 = nothing
        end
        deconstruct_result1677 = _t1901
        if !isnothing(deconstruct_result1677)
            unwrapped1678 = deconstruct_result1677
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1678)
                newline(pp)
                for (i1902, elem1679) in enumerate(unwrapped1678)
                    i1680 = i1902 - 1
                    if (i1680 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1679)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1903 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1903 = nothing
            end
            deconstruct_result1675 = _t1903
            if !isnothing(deconstruct_result1675)
                unwrapped1676 = deconstruct_result1675
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1676)
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
    flat1686 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1686)
        write(pp, flat1686)
        return nothing
    else
        _dollar_dollar = msg
        fields1682 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1683 = fields1682
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1684 = unwrapped_fields1683[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1684))
        newline(pp)
        field1685 = unwrapped_fields1683[2]
        pretty_relation_id(pp, field1685)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1688 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1688)
        write(pp, flat1688)
        return nothing
    else
        fields1687 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1687))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1692 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1692)
        write(pp, flat1692)
        return nothing
    else
        fields1689 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1689)
            newline(pp)
            for (i1904, elem1690) in enumerate(fields1689)
                i1691 = i1904 - 1
                if (i1691 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1690)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1701 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1701)
        write(pp, flat1701)
        return nothing
    else
        _dollar_dollar = msg
        _t1905 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1693 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1905,)
        unwrapped_fields1694 = fields1693
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1695 = unwrapped_fields1694[1]
        pretty_iceberg_locator(pp, field1695)
        newline(pp)
        field1696 = unwrapped_fields1694[2]
        pretty_iceberg_catalog_config(pp, field1696)
        newline(pp)
        field1697 = unwrapped_fields1694[3]
        pretty_export_iceberg_table_def(pp, field1697)
        newline(pp)
        field1698 = unwrapped_fields1694[4]
        pretty_iceberg_table_properties(pp, field1698)
        field1699 = unwrapped_fields1694[5]
        if !isnothing(field1699)
            newline(pp)
            opt_val1700 = field1699
            pretty_config_dict(pp, opt_val1700)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1703 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1703)
        write(pp, flat1703)
        return nothing
    else
        fields1702 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1702)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1707 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1707)
        write(pp, flat1707)
        return nothing
    else
        fields1704 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1704)
            newline(pp)
            for (i1906, elem1705) in enumerate(fields1704)
                i1706 = i1906 - 1
                if (i1706 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1705)
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
    for (i1961, _rid) in enumerate(msg.ids)
        _idx = i1961 - 1
        newline(pp)
        write(pp, "(")
        _t1962 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1962)
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
    for (i1963, _elem) in enumerate(msg.inserts)
        _idx = i1963 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":deletes (")
    for (i1964, _elem) in enumerate(msg.deletes)
        _idx = i1964 - 1
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
    for (i1965, _elem) in enumerate(msg.keys)
        _idx = i1965 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1966, _elem) in enumerate(msg.values)
        _idx = i1966 - 1
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
    for (i1967, _elem) in enumerate(msg.targets)
        _idx = i1967 - 1
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
    for (i1968, _elem) in enumerate(msg.columns)
        _idx = i1968 - 1
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
