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
        _t1926 = nothing
    end
    return nothing
end

function deconstruct_csv_data_columns_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Vector{Proto.GNFColumn}}
    if _has_proto_field(msg, Symbol("relations"))
        return nothing
    else
        _t1927 = nothing
    end
    return msg.columns
end

function deconstruct_csv_data_relations_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Proto.TargetRelations}
    if _has_proto_field(msg, Symbol("relations"))
        return msg.relations
    else
        _t1928 = nothing
    end
    return nothing
end

function deconstruct_export_csv_output_location(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Tuple{String, String}
    return (msg.path, msg.transaction_output_name,)
end

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1929 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1929
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1930 = Proto.Value(value=OneOf(:int_value, v))
    return _t1930
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1931 = Proto.Value(value=OneOf(:float_value, v))
    return _t1931
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1932 = Proto.Value(value=OneOf(:string_value, v))
    return _t1932
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1933 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1933
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1934 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1934
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1935 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1935,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1936 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1936,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1937 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1937,))
            end
        end
    end
    _t1938 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1938,))
    for pair in sort([(k, v) for (k, v) in msg.configuration_values])
        push!(result, pair)
    end
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1939 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1939,))
    _t1940 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1940,))
    if msg.new_line != ""
        _t1941 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1941,))
    end
    _t1942 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1942,))
    _t1943 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1943,))
    _t1944 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1944,))
    if msg.comment != ""
        _t1945 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1945,))
    end
    for missing_string in msg.missing_strings
        _t1946 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1946,))
    end
    _t1947 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1947,))
    _t1948 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1948,))
    _t1949 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1949,))
    if msg.partition_size_mb != 0
        _t1950 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1950,))
    end
    return sort(result)
end

function deconstruct_csv_storage_integration_optional(pp::PrettyPrinter, msg::Proto.CSVConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    if !_has_proto_field(msg, Symbol("storage_integration"))
        return nothing
    else
        _t1951 = nothing
    end
    si = msg.storage_integration
    result = Tuple{String, Proto.Value}[]
    if si.provider != ""
        _t1952 = _make_value_string(pp, si.provider)
        push!(result, ("provider", _t1952,))
    end
    if si.azure_sas_token != ""
        _t1953 = _make_value_string(pp, "***")
        push!(result, ("azure_sas_token", _t1953,))
    end
    if si.s3_region != ""
        _t1954 = _make_value_string(pp, si.s3_region)
        push!(result, ("s3_region", _t1954,))
    end
    if si.s3_access_key_id != ""
        _t1955 = _make_value_string(pp, "***")
        push!(result, ("s3_access_key_id", _t1955,))
    end
    if si.s3_secret_access_key != ""
        _t1956 = _make_value_string(pp, "***")
        push!(result, ("s3_secret_access_key", _t1956,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1957 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1957,))
    _t1958 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1958,))
    _t1959 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1959,))
    _t1960 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1960,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1961 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1961,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1962 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1962,))
        end
    end
    _t1963 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1963,))
    _t1964 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1964,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1965 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1965,))
    end
    if !isnothing(msg.compression)
        _t1966 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1966,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1967 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1967,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1968 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1968,))
    end
    if !isnothing(msg.syntax_delim)
        _t1969 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1969,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1970 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1970,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1971 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1971,))
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
        _t1972 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_columns_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, Vector{Proto.GNFColumn}}
    if _has_proto_field(msg, Symbol("relations"))
        return nothing
    else
        _t1973 = nothing
    end
    return msg.columns
end

function deconstruct_iceberg_data_relations_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, Proto.TargetRelations}
    if _has_proto_field(msg, Symbol("relations"))
        return msg.relations
    else
        _t1974 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1975 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1976 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1977 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1977,))
    end
    if msg.target_file_size_bytes != 0
        _t1978 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1978,))
    end
    if msg.compression != ""
        _t1979 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1979,))
    end
    if length(result) == 0
        return nothing
    else
        _t1980 = nothing
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
        _t1981 = nothing
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
    flat871 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat871)
        write(pp, flat871)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1724 = _dollar_dollar.configure
        else
            _t1724 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1725 = _dollar_dollar.sync
        else
            _t1725 = nothing
        end
        fields862 = (_t1724, _t1725, _dollar_dollar.epochs,)
        unwrapped_fields863 = fields862
        write(pp, "(transaction")
        indent_sexp!(pp)
        field864 = unwrapped_fields863[1]
        if !isnothing(field864)
            newline(pp)
            opt_val865 = field864
            pretty_configure(pp, opt_val865)
        end
        field866 = unwrapped_fields863[2]
        if !isnothing(field866)
            newline(pp)
            opt_val867 = field866
            pretty_sync(pp, opt_val867)
        end
        field868 = unwrapped_fields863[3]
        if !isempty(field868)
            newline(pp)
            for (i1726, elem869) in enumerate(field868)
                i870 = i1726 - 1
                if (i870 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem869)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat874 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat874)
        write(pp, flat874)
        return nothing
    else
        _dollar_dollar = msg
        _t1727 = deconstruct_configure(pp, _dollar_dollar)
        fields872 = _t1727
        unwrapped_fields873 = fields872
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields873)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat878 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat878)
        write(pp, flat878)
        return nothing
    else
        fields875 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields875)
            newline(pp)
            for (i1728, elem876) in enumerate(fields875)
                i877 = i1728 - 1
                if (i877 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem876)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat883 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat883)
        write(pp, flat883)
        return nothing
    else
        _dollar_dollar = msg
        fields879 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields880 = fields879
        write(pp, ":")
        field881 = unwrapped_fields880[1]
        write(pp, field881)
        write(pp, " ")
        field882 = unwrapped_fields880[2]
        pretty_raw_value(pp, field882)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat909 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat909)
        write(pp, flat909)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1729 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1729 = nothing
        end
        deconstruct_result907 = _t1729
        if !isnothing(deconstruct_result907)
            unwrapped908 = deconstruct_result907
            pretty_raw_date(pp, unwrapped908)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1730 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1730 = nothing
            end
            deconstruct_result905 = _t1730
            if !isnothing(deconstruct_result905)
                unwrapped906 = deconstruct_result905
                pretty_raw_datetime(pp, unwrapped906)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1731 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1731 = nothing
                end
                deconstruct_result903 = _t1731
                if !isnothing(deconstruct_result903)
                    unwrapped904 = deconstruct_result903
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped904))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1732 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1732 = nothing
                    end
                    deconstruct_result901 = _t1732
                    if !isnothing(deconstruct_result901)
                        unwrapped902 = deconstruct_result901
                        write(pp, (string(Int64(unwrapped902)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1733 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1733 = nothing
                        end
                        deconstruct_result899 = _t1733
                        if !isnothing(deconstruct_result899)
                            unwrapped900 = deconstruct_result899
                            write(pp, string(unwrapped900))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1734 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1734 = nothing
                            end
                            deconstruct_result897 = _t1734
                            if !isnothing(deconstruct_result897)
                                unwrapped898 = deconstruct_result897
                                write(pp, format_float32_literal(unwrapped898))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1735 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1735 = nothing
                                end
                                deconstruct_result895 = _t1735
                                if !isnothing(deconstruct_result895)
                                    unwrapped896 = deconstruct_result895
                                    write(pp, lowercase(string(unwrapped896)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1736 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1736 = nothing
                                    end
                                    deconstruct_result893 = _t1736
                                    if !isnothing(deconstruct_result893)
                                        unwrapped894 = deconstruct_result893
                                        write(pp, (string(Int64(unwrapped894)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1737 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1737 = nothing
                                        end
                                        deconstruct_result891 = _t1737
                                        if !isnothing(deconstruct_result891)
                                            unwrapped892 = deconstruct_result891
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped892))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1738 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1738 = nothing
                                            end
                                            deconstruct_result889 = _t1738
                                            if !isnothing(deconstruct_result889)
                                                unwrapped890 = deconstruct_result889
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped890))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1739 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1739 = nothing
                                                end
                                                deconstruct_result887 = _t1739
                                                if !isnothing(deconstruct_result887)
                                                    unwrapped888 = deconstruct_result887
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped888))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1740 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1740 = nothing
                                                    end
                                                    deconstruct_result885 = _t1740
                                                    if !isnothing(deconstruct_result885)
                                                        unwrapped886 = deconstruct_result885
                                                        pretty_boolean_value(pp, unwrapped886)
                                                    else
                                                        fields884 = msg
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
    flat915 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat915)
        write(pp, flat915)
        return nothing
    else
        _dollar_dollar = msg
        fields910 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields911 = fields910
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field912 = unwrapped_fields911[1]
        write(pp, string(field912))
        newline(pp)
        field913 = unwrapped_fields911[2]
        write(pp, string(field913))
        newline(pp)
        field914 = unwrapped_fields911[3]
        write(pp, string(field914))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat926 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat926)
        write(pp, flat926)
        return nothing
    else
        _dollar_dollar = msg
        fields916 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields917 = fields916
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field918 = unwrapped_fields917[1]
        write(pp, string(field918))
        newline(pp)
        field919 = unwrapped_fields917[2]
        write(pp, string(field919))
        newline(pp)
        field920 = unwrapped_fields917[3]
        write(pp, string(field920))
        newline(pp)
        field921 = unwrapped_fields917[4]
        write(pp, string(field921))
        newline(pp)
        field922 = unwrapped_fields917[5]
        write(pp, string(field922))
        newline(pp)
        field923 = unwrapped_fields917[6]
        write(pp, string(field923))
        field924 = unwrapped_fields917[7]
        if !isnothing(field924)
            newline(pp)
            opt_val925 = field924
            write(pp, string(opt_val925))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1741 = ()
    else
        _t1741 = nothing
    end
    deconstruct_result929 = _t1741
    if !isnothing(deconstruct_result929)
        unwrapped930 = deconstruct_result929
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1742 = ()
        else
            _t1742 = nothing
        end
        deconstruct_result927 = _t1742
        if !isnothing(deconstruct_result927)
            unwrapped928 = deconstruct_result927
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat935 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat935)
        write(pp, flat935)
        return nothing
    else
        _dollar_dollar = msg
        fields931 = _dollar_dollar.fragments
        unwrapped_fields932 = fields931
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields932)
            newline(pp)
            for (i1743, elem933) in enumerate(unwrapped_fields932)
                i934 = i1743 - 1
                if (i934 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem933)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat938 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat938)
        write(pp, flat938)
        return nothing
    else
        _dollar_dollar = msg
        fields936 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields937 = fields936
        write(pp, ":")
        write(pp, unwrapped_fields937)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat945 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat945)
        write(pp, flat945)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1744 = _dollar_dollar.writes
        else
            _t1744 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1745 = _dollar_dollar.reads
        else
            _t1745 = nothing
        end
        fields939 = (_t1744, _t1745,)
        unwrapped_fields940 = fields939
        write(pp, "(epoch")
        indent_sexp!(pp)
        field941 = unwrapped_fields940[1]
        if !isnothing(field941)
            newline(pp)
            opt_val942 = field941
            pretty_epoch_writes(pp, opt_val942)
        end
        field943 = unwrapped_fields940[2]
        if !isnothing(field943)
            newline(pp)
            opt_val944 = field943
            pretty_epoch_reads(pp, opt_val944)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat949 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat949)
        write(pp, flat949)
        return nothing
    else
        fields946 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields946)
            newline(pp)
            for (i1746, elem947) in enumerate(fields946)
                i948 = i1746 - 1
                if (i948 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem947)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat958 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat958)
        write(pp, flat958)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1747 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1747 = nothing
        end
        deconstruct_result956 = _t1747
        if !isnothing(deconstruct_result956)
            unwrapped957 = deconstruct_result956
            pretty_define(pp, unwrapped957)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1748 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1748 = nothing
            end
            deconstruct_result954 = _t1748
            if !isnothing(deconstruct_result954)
                unwrapped955 = deconstruct_result954
                pretty_undefine(pp, unwrapped955)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1749 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1749 = nothing
                end
                deconstruct_result952 = _t1749
                if !isnothing(deconstruct_result952)
                    unwrapped953 = deconstruct_result952
                    pretty_context(pp, unwrapped953)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1750 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1750 = nothing
                    end
                    deconstruct_result950 = _t1750
                    if !isnothing(deconstruct_result950)
                        unwrapped951 = deconstruct_result950
                        pretty_snapshot(pp, unwrapped951)
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
    flat961 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat961)
        write(pp, flat961)
        return nothing
    else
        _dollar_dollar = msg
        fields959 = _dollar_dollar.fragment
        unwrapped_fields960 = fields959
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields960)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat968 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat968)
        write(pp, flat968)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields962 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields963 = fields962
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field964 = unwrapped_fields963[1]
        pretty_new_fragment_id(pp, field964)
        field965 = unwrapped_fields963[2]
        if !isempty(field965)
            newline(pp)
            for (i1751, elem966) in enumerate(field965)
                i967 = i1751 - 1
                if (i967 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem966)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat970 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat970)
        write(pp, flat970)
        return nothing
    else
        fields969 = msg
        pretty_fragment_id(pp, fields969)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat979 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat979)
        write(pp, flat979)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1752 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1752 = nothing
        end
        deconstruct_result977 = _t1752
        if !isnothing(deconstruct_result977)
            unwrapped978 = deconstruct_result977
            pretty_def(pp, unwrapped978)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1753 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1753 = nothing
            end
            deconstruct_result975 = _t1753
            if !isnothing(deconstruct_result975)
                unwrapped976 = deconstruct_result975
                pretty_algorithm(pp, unwrapped976)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1754 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1754 = nothing
                end
                deconstruct_result973 = _t1754
                if !isnothing(deconstruct_result973)
                    unwrapped974 = deconstruct_result973
                    pretty_constraint(pp, unwrapped974)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1755 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1755 = nothing
                    end
                    deconstruct_result971 = _t1755
                    if !isnothing(deconstruct_result971)
                        unwrapped972 = deconstruct_result971
                        pretty_data(pp, unwrapped972)
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
    flat986 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat986)
        write(pp, flat986)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1756 = _dollar_dollar.attrs
        else
            _t1756 = nothing
        end
        fields980 = (_dollar_dollar.name, _dollar_dollar.body, _t1756,)
        unwrapped_fields981 = fields980
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field982 = unwrapped_fields981[1]
        pretty_relation_id(pp, field982)
        newline(pp)
        field983 = unwrapped_fields981[2]
        pretty_abstraction(pp, field983)
        field984 = unwrapped_fields981[3]
        if !isnothing(field984)
            newline(pp)
            opt_val985 = field984
            pretty_attrs(pp, opt_val985)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat991 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat991)
        write(pp, flat991)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1758 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1757 = _t1758
        else
            _t1757 = nothing
        end
        deconstruct_result989 = _t1757
        if !isnothing(deconstruct_result989)
            unwrapped990 = deconstruct_result989
            write(pp, ":")
            write(pp, unwrapped990)
        else
            _dollar_dollar = msg
            _t1759 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result987 = _t1759
            if !isnothing(deconstruct_result987)
                unwrapped988 = deconstruct_result987
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped988))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat996 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat996)
        write(pp, flat996)
        return nothing
    else
        _dollar_dollar = msg
        _t1760 = deconstruct_bindings(pp, _dollar_dollar)
        fields992 = (_t1760, _dollar_dollar.value,)
        unwrapped_fields993 = fields992
        write(pp, "(")
        indent!(pp)
        field994 = unwrapped_fields993[1]
        pretty_bindings(pp, field994)
        newline(pp)
        field995 = unwrapped_fields993[2]
        pretty_formula(pp, field995)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat1004 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat1004)
        write(pp, flat1004)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1761 = _dollar_dollar[2]
        else
            _t1761 = nothing
        end
        fields997 = (_dollar_dollar[1], _t1761,)
        unwrapped_fields998 = fields997
        write(pp, "[")
        indent!(pp)
        field999 = unwrapped_fields998[1]
        for (i1762, elem1000) in enumerate(field999)
            i1001 = i1762 - 1
            if (i1001 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem1000)
        end
        field1002 = unwrapped_fields998[2]
        if !isnothing(field1002)
            newline(pp)
            opt_val1003 = field1002
            pretty_value_bindings(pp, opt_val1003)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat1009 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat1009)
        write(pp, flat1009)
        return nothing
    else
        _dollar_dollar = msg
        fields1005 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields1006 = fields1005
        field1007 = unwrapped_fields1006[1]
        write(pp, field1007)
        write(pp, "::")
        field1008 = unwrapped_fields1006[2]
        pretty_type(pp, field1008)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat1040 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat1040)
        write(pp, flat1040)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1763 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1763 = nothing
        end
        deconstruct_result1038 = _t1763
        if !isnothing(deconstruct_result1038)
            unwrapped1039 = deconstruct_result1038
            pretty_unspecified_type(pp, unwrapped1039)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1764 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1764 = nothing
            end
            deconstruct_result1036 = _t1764
            if !isnothing(deconstruct_result1036)
                unwrapped1037 = deconstruct_result1036
                pretty_string_type(pp, unwrapped1037)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1765 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1765 = nothing
                end
                deconstruct_result1034 = _t1765
                if !isnothing(deconstruct_result1034)
                    unwrapped1035 = deconstruct_result1034
                    pretty_int_type(pp, unwrapped1035)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1766 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1766 = nothing
                    end
                    deconstruct_result1032 = _t1766
                    if !isnothing(deconstruct_result1032)
                        unwrapped1033 = deconstruct_result1032
                        pretty_float_type(pp, unwrapped1033)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1767 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1767 = nothing
                        end
                        deconstruct_result1030 = _t1767
                        if !isnothing(deconstruct_result1030)
                            unwrapped1031 = deconstruct_result1030
                            pretty_uint128_type(pp, unwrapped1031)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1768 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1768 = nothing
                            end
                            deconstruct_result1028 = _t1768
                            if !isnothing(deconstruct_result1028)
                                unwrapped1029 = deconstruct_result1028
                                pretty_int128_type(pp, unwrapped1029)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1769 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1769 = nothing
                                end
                                deconstruct_result1026 = _t1769
                                if !isnothing(deconstruct_result1026)
                                    unwrapped1027 = deconstruct_result1026
                                    pretty_date_type(pp, unwrapped1027)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1770 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1770 = nothing
                                    end
                                    deconstruct_result1024 = _t1770
                                    if !isnothing(deconstruct_result1024)
                                        unwrapped1025 = deconstruct_result1024
                                        pretty_datetime_type(pp, unwrapped1025)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1771 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1771 = nothing
                                        end
                                        deconstruct_result1022 = _t1771
                                        if !isnothing(deconstruct_result1022)
                                            unwrapped1023 = deconstruct_result1022
                                            pretty_missing_type(pp, unwrapped1023)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1772 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1772 = nothing
                                            end
                                            deconstruct_result1020 = _t1772
                                            if !isnothing(deconstruct_result1020)
                                                unwrapped1021 = deconstruct_result1020
                                                pretty_decimal_type(pp, unwrapped1021)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1773 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1773 = nothing
                                                end
                                                deconstruct_result1018 = _t1773
                                                if !isnothing(deconstruct_result1018)
                                                    unwrapped1019 = deconstruct_result1018
                                                    pretty_boolean_type(pp, unwrapped1019)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1774 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1774 = nothing
                                                    end
                                                    deconstruct_result1016 = _t1774
                                                    if !isnothing(deconstruct_result1016)
                                                        unwrapped1017 = deconstruct_result1016
                                                        pretty_int32_type(pp, unwrapped1017)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1775 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1775 = nothing
                                                        end
                                                        deconstruct_result1014 = _t1775
                                                        if !isnothing(deconstruct_result1014)
                                                            unwrapped1015 = deconstruct_result1014
                                                            pretty_float32_type(pp, unwrapped1015)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1776 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1776 = nothing
                                                            end
                                                            deconstruct_result1012 = _t1776
                                                            if !isnothing(deconstruct_result1012)
                                                                unwrapped1013 = deconstruct_result1012
                                                                pretty_uint32_type(pp, unwrapped1013)
                                                            else
                                                                _dollar_dollar = msg
                                                                if _has_proto_field(_dollar_dollar, Symbol("fixed_type"))
                                                                    _t1777 = _get_oneof_field(_dollar_dollar, :fixed_type)
                                                                else
                                                                    _t1777 = nothing
                                                                end
                                                                deconstruct_result1010 = _t1777
                                                                if !isnothing(deconstruct_result1010)
                                                                    unwrapped1011 = deconstruct_result1010
                                                                    pretty_fixed_type(pp, unwrapped1011)
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
    fields1041 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields1042 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields1043 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields1044 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields1045 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields1046 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields1047 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields1048 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields1049 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat1054 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat1054)
        write(pp, flat1054)
        return nothing
    else
        _dollar_dollar = msg
        fields1050 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields1051 = fields1050
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field1052 = unwrapped_fields1051[1]
        write(pp, string(field1052))
        newline(pp)
        field1053 = unwrapped_fields1051[2]
        write(pp, string(field1053))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields1055 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields1056 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields1057 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields1058 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_fixed_type(pp::PrettyPrinter, msg::Proto.FixedType)
    flat1061 = try_flat(pp, msg, pretty_fixed_type)
    if !isnothing(flat1061)
        write(pp, flat1061)
        return nothing
    else
        _dollar_dollar = msg
        fields1059 = Int64(_dollar_dollar.length)
        unwrapped_fields1060 = fields1059
        write(pp, "(FIXED")
        indent_sexp!(pp)
        newline(pp)
        write(pp, string(unwrapped_fields1060))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1065 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1065)
        write(pp, flat1065)
        return nothing
    else
        fields1062 = msg
        write(pp, "|")
        if !isempty(fields1062)
            write(pp, " ")
            for (i1778, elem1063) in enumerate(fields1062)
                i1064 = i1778 - 1
                if (i1064 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1063)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1092 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1779 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1779 = nothing
        end
        deconstruct_result1090 = _t1779
        if !isnothing(deconstruct_result1090)
            unwrapped1091 = deconstruct_result1090
            pretty_true(pp, unwrapped1091)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1780 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1780 = nothing
            end
            deconstruct_result1088 = _t1780
            if !isnothing(deconstruct_result1088)
                unwrapped1089 = deconstruct_result1088
                pretty_false(pp, unwrapped1089)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1781 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1781 = nothing
                end
                deconstruct_result1086 = _t1781
                if !isnothing(deconstruct_result1086)
                    unwrapped1087 = deconstruct_result1086
                    pretty_exists(pp, unwrapped1087)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1782 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1782 = nothing
                    end
                    deconstruct_result1084 = _t1782
                    if !isnothing(deconstruct_result1084)
                        unwrapped1085 = deconstruct_result1084
                        pretty_reduce(pp, unwrapped1085)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1783 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1783 = nothing
                        end
                        deconstruct_result1082 = _t1783
                        if !isnothing(deconstruct_result1082)
                            unwrapped1083 = deconstruct_result1082
                            pretty_conjunction(pp, unwrapped1083)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1784 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1784 = nothing
                            end
                            deconstruct_result1080 = _t1784
                            if !isnothing(deconstruct_result1080)
                                unwrapped1081 = deconstruct_result1080
                                pretty_disjunction(pp, unwrapped1081)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1785 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1785 = nothing
                                end
                                deconstruct_result1078 = _t1785
                                if !isnothing(deconstruct_result1078)
                                    unwrapped1079 = deconstruct_result1078
                                    pretty_not(pp, unwrapped1079)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1786 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1786 = nothing
                                    end
                                    deconstruct_result1076 = _t1786
                                    if !isnothing(deconstruct_result1076)
                                        unwrapped1077 = deconstruct_result1076
                                        pretty_ffi(pp, unwrapped1077)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1787 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1787 = nothing
                                        end
                                        deconstruct_result1074 = _t1787
                                        if !isnothing(deconstruct_result1074)
                                            unwrapped1075 = deconstruct_result1074
                                            pretty_atom(pp, unwrapped1075)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1788 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1788 = nothing
                                            end
                                            deconstruct_result1072 = _t1788
                                            if !isnothing(deconstruct_result1072)
                                                unwrapped1073 = deconstruct_result1072
                                                pretty_pragma(pp, unwrapped1073)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1789 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1789 = nothing
                                                end
                                                deconstruct_result1070 = _t1789
                                                if !isnothing(deconstruct_result1070)
                                                    unwrapped1071 = deconstruct_result1070
                                                    pretty_primitive(pp, unwrapped1071)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1790 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1790 = nothing
                                                    end
                                                    deconstruct_result1068 = _t1790
                                                    if !isnothing(deconstruct_result1068)
                                                        unwrapped1069 = deconstruct_result1068
                                                        pretty_rel_atom(pp, unwrapped1069)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1791 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1791 = nothing
                                                        end
                                                        deconstruct_result1066 = _t1791
                                                        if !isnothing(deconstruct_result1066)
                                                            unwrapped1067 = deconstruct_result1066
                                                            pretty_cast(pp, unwrapped1067)
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
    fields1093 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1094 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1099 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1099)
        write(pp, flat1099)
        return nothing
    else
        _dollar_dollar = msg
        _t1792 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1095 = (_t1792, _dollar_dollar.body.value,)
        unwrapped_fields1096 = fields1095
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1097 = unwrapped_fields1096[1]
        pretty_bindings(pp, field1097)
        newline(pp)
        field1098 = unwrapped_fields1096[2]
        pretty_formula(pp, field1098)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1105 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1105)
        write(pp, flat1105)
        return nothing
    else
        _dollar_dollar = msg
        fields1100 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1101 = fields1100
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1102 = unwrapped_fields1101[1]
        pretty_abstraction(pp, field1102)
        newline(pp)
        field1103 = unwrapped_fields1101[2]
        pretty_abstraction(pp, field1103)
        newline(pp)
        field1104 = unwrapped_fields1101[3]
        pretty_terms(pp, field1104)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1109 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1109)
        write(pp, flat1109)
        return nothing
    else
        fields1106 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1106)
            newline(pp)
            for (i1793, elem1107) in enumerate(fields1106)
                i1108 = i1793 - 1
                if (i1108 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1107)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1114 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1114)
        write(pp, flat1114)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1794 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1794 = nothing
        end
        deconstruct_result1112 = _t1794
        if !isnothing(deconstruct_result1112)
            unwrapped1113 = deconstruct_result1112
            pretty_var(pp, unwrapped1113)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1795 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1795 = nothing
            end
            deconstruct_result1110 = _t1795
            if !isnothing(deconstruct_result1110)
                unwrapped1111 = deconstruct_result1110
                pretty_value(pp, unwrapped1111)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1117 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1117)
        write(pp, flat1117)
        return nothing
    else
        _dollar_dollar = msg
        fields1115 = _dollar_dollar.name
        unwrapped_fields1116 = fields1115
        write(pp, unwrapped_fields1116)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1143 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1143)
        write(pp, flat1143)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1796 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1796 = nothing
        end
        deconstruct_result1141 = _t1796
        if !isnothing(deconstruct_result1141)
            unwrapped1142 = deconstruct_result1141
            pretty_date(pp, unwrapped1142)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1797 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1797 = nothing
            end
            deconstruct_result1139 = _t1797
            if !isnothing(deconstruct_result1139)
                unwrapped1140 = deconstruct_result1139
                pretty_datetime(pp, unwrapped1140)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1798 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1798 = nothing
                end
                deconstruct_result1137 = _t1798
                if !isnothing(deconstruct_result1137)
                    unwrapped1138 = deconstruct_result1137
                    write(pp, format_string(pp, unwrapped1138))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1799 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1799 = nothing
                    end
                    deconstruct_result1135 = _t1799
                    if !isnothing(deconstruct_result1135)
                        unwrapped1136 = deconstruct_result1135
                        write(pp, format_int32(pp, unwrapped1136))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1800 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1800 = nothing
                        end
                        deconstruct_result1133 = _t1800
                        if !isnothing(deconstruct_result1133)
                            unwrapped1134 = deconstruct_result1133
                            write(pp, format_int(pp, unwrapped1134))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1801 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1801 = nothing
                            end
                            deconstruct_result1131 = _t1801
                            if !isnothing(deconstruct_result1131)
                                unwrapped1132 = deconstruct_result1131
                                write(pp, format_float32(pp, unwrapped1132))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1802 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1802 = nothing
                                end
                                deconstruct_result1129 = _t1802
                                if !isnothing(deconstruct_result1129)
                                    unwrapped1130 = deconstruct_result1129
                                    write(pp, format_float(pp, unwrapped1130))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1803 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1803 = nothing
                                    end
                                    deconstruct_result1127 = _t1803
                                    if !isnothing(deconstruct_result1127)
                                        unwrapped1128 = deconstruct_result1127
                                        write(pp, format_uint32(pp, unwrapped1128))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1804 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1804 = nothing
                                        end
                                        deconstruct_result1125 = _t1804
                                        if !isnothing(deconstruct_result1125)
                                            unwrapped1126 = deconstruct_result1125
                                            write(pp, format_uint128(pp, unwrapped1126))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1805 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1805 = nothing
                                            end
                                            deconstruct_result1123 = _t1805
                                            if !isnothing(deconstruct_result1123)
                                                unwrapped1124 = deconstruct_result1123
                                                write(pp, format_int128(pp, unwrapped1124))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1806 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1806 = nothing
                                                end
                                                deconstruct_result1121 = _t1806
                                                if !isnothing(deconstruct_result1121)
                                                    unwrapped1122 = deconstruct_result1121
                                                    write(pp, format_decimal(pp, unwrapped1122))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1807 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1807 = nothing
                                                    end
                                                    deconstruct_result1119 = _t1807
                                                    if !isnothing(deconstruct_result1119)
                                                        unwrapped1120 = deconstruct_result1119
                                                        pretty_boolean_value(pp, unwrapped1120)
                                                    else
                                                        fields1118 = msg
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
    flat1149 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1149)
        write(pp, flat1149)
        return nothing
    else
        _dollar_dollar = msg
        fields1144 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1145 = fields1144
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1146 = unwrapped_fields1145[1]
        write(pp, format_int(pp, field1146))
        newline(pp)
        field1147 = unwrapped_fields1145[2]
        write(pp, format_int(pp, field1147))
        newline(pp)
        field1148 = unwrapped_fields1145[3]
        write(pp, format_int(pp, field1148))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1160 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1160)
        write(pp, flat1160)
        return nothing
    else
        _dollar_dollar = msg
        fields1150 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1151 = fields1150
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1152 = unwrapped_fields1151[1]
        write(pp, format_int(pp, field1152))
        newline(pp)
        field1153 = unwrapped_fields1151[2]
        write(pp, format_int(pp, field1153))
        newline(pp)
        field1154 = unwrapped_fields1151[3]
        write(pp, format_int(pp, field1154))
        newline(pp)
        field1155 = unwrapped_fields1151[4]
        write(pp, format_int(pp, field1155))
        newline(pp)
        field1156 = unwrapped_fields1151[5]
        write(pp, format_int(pp, field1156))
        newline(pp)
        field1157 = unwrapped_fields1151[6]
        write(pp, format_int(pp, field1157))
        field1158 = unwrapped_fields1151[7]
        if !isnothing(field1158)
            newline(pp)
            opt_val1159 = field1158
            write(pp, format_int(pp, opt_val1159))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1165 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1165)
        write(pp, flat1165)
        return nothing
    else
        _dollar_dollar = msg
        fields1161 = _dollar_dollar.args
        unwrapped_fields1162 = fields1161
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1162)
            newline(pp)
            for (i1808, elem1163) in enumerate(unwrapped_fields1162)
                i1164 = i1808 - 1
                if (i1164 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1163)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1170 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1170)
        write(pp, flat1170)
        return nothing
    else
        _dollar_dollar = msg
        fields1166 = _dollar_dollar.args
        unwrapped_fields1167 = fields1166
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1167)
            newline(pp)
            for (i1809, elem1168) in enumerate(unwrapped_fields1167)
                i1169 = i1809 - 1
                if (i1169 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1168)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1173 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1173)
        write(pp, flat1173)
        return nothing
    else
        _dollar_dollar = msg
        fields1171 = _dollar_dollar.arg
        unwrapped_fields1172 = fields1171
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1172)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1179 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        _dollar_dollar = msg
        fields1174 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1175 = fields1174
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1176 = unwrapped_fields1175[1]
        pretty_name(pp, field1176)
        newline(pp)
        field1177 = unwrapped_fields1175[2]
        pretty_ffi_args(pp, field1177)
        newline(pp)
        field1178 = unwrapped_fields1175[3]
        pretty_terms(pp, field1178)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1181 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1181)
        write(pp, flat1181)
        return nothing
    else
        fields1180 = msg
        write(pp, ":")
        write(pp, fields1180)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1185 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1185)
        write(pp, flat1185)
        return nothing
    else
        fields1182 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1182)
            newline(pp)
            for (i1810, elem1183) in enumerate(fields1182)
                i1184 = i1810 - 1
                if (i1184 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1183)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1192 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1192)
        write(pp, flat1192)
        return nothing
    else
        _dollar_dollar = msg
        fields1186 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1187 = fields1186
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1188 = unwrapped_fields1187[1]
        pretty_relation_id(pp, field1188)
        field1189 = unwrapped_fields1187[2]
        if !isempty(field1189)
            newline(pp)
            for (i1811, elem1190) in enumerate(field1189)
                i1191 = i1811 - 1
                if (i1191 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1190)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1199 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1199)
        write(pp, flat1199)
        return nothing
    else
        _dollar_dollar = msg
        fields1193 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1194 = fields1193
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1195 = unwrapped_fields1194[1]
        pretty_name(pp, field1195)
        field1196 = unwrapped_fields1194[2]
        if !isempty(field1196)
            newline(pp)
            for (i1812, elem1197) in enumerate(field1196)
                i1198 = i1812 - 1
                if (i1198 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1197)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1215 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1813 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1813 = nothing
        end
        guard_result1214 = _t1813
        if !isnothing(guard_result1214)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1814 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1814 = nothing
            end
            guard_result1213 = _t1814
            if !isnothing(guard_result1213)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1815 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1815 = nothing
                end
                guard_result1212 = _t1815
                if !isnothing(guard_result1212)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1816 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1816 = nothing
                    end
                    guard_result1211 = _t1816
                    if !isnothing(guard_result1211)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1817 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1817 = nothing
                        end
                        guard_result1210 = _t1817
                        if !isnothing(guard_result1210)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1818 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1818 = nothing
                            end
                            guard_result1209 = _t1818
                            if !isnothing(guard_result1209)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1819 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1819 = nothing
                                end
                                guard_result1208 = _t1819
                                if !isnothing(guard_result1208)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1820 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1820 = nothing
                                    end
                                    guard_result1207 = _t1820
                                    if !isnothing(guard_result1207)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1821 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1821 = nothing
                                        end
                                        guard_result1206 = _t1821
                                        if !isnothing(guard_result1206)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1200 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1201 = fields1200
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1202 = unwrapped_fields1201[1]
                                            pretty_name(pp, field1202)
                                            field1203 = unwrapped_fields1201[2]
                                            if !isempty(field1203)
                                                newline(pp)
                                                for (i1822, elem1204) in enumerate(field1203)
                                                    i1205 = i1822 - 1
                                                    if (i1205 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1204)
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
    flat1220 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1823 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1823 = nothing
        end
        fields1216 = _t1823
        unwrapped_fields1217 = fields1216
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1218 = unwrapped_fields1217[1]
        pretty_term(pp, field1218)
        newline(pp)
        field1219 = unwrapped_fields1217[2]
        pretty_term(pp, field1219)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1225 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1225)
        write(pp, flat1225)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1824 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1824 = nothing
        end
        fields1221 = _t1824
        unwrapped_fields1222 = fields1221
        write(pp, "(<")
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

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1230 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1230)
        write(pp, flat1230)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1825 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1825 = nothing
        end
        fields1226 = _t1825
        unwrapped_fields1227 = fields1226
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1228 = unwrapped_fields1227[1]
        pretty_term(pp, field1228)
        newline(pp)
        field1229 = unwrapped_fields1227[2]
        pretty_term(pp, field1229)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1235 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1235)
        write(pp, flat1235)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1826 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1826 = nothing
        end
        fields1231 = _t1826
        unwrapped_fields1232 = fields1231
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1233 = unwrapped_fields1232[1]
        pretty_term(pp, field1233)
        newline(pp)
        field1234 = unwrapped_fields1232[2]
        pretty_term(pp, field1234)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1240 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1240)
        write(pp, flat1240)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1827 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1827 = nothing
        end
        fields1236 = _t1827
        unwrapped_fields1237 = fields1236
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1238 = unwrapped_fields1237[1]
        pretty_term(pp, field1238)
        newline(pp)
        field1239 = unwrapped_fields1237[2]
        pretty_term(pp, field1239)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1246 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1246)
        write(pp, flat1246)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1828 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1828 = nothing
        end
        fields1241 = _t1828
        unwrapped_fields1242 = fields1241
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1243 = unwrapped_fields1242[1]
        pretty_term(pp, field1243)
        newline(pp)
        field1244 = unwrapped_fields1242[2]
        pretty_term(pp, field1244)
        newline(pp)
        field1245 = unwrapped_fields1242[3]
        pretty_term(pp, field1245)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1252 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1252)
        write(pp, flat1252)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1829 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1829 = nothing
        end
        fields1247 = _t1829
        unwrapped_fields1248 = fields1247
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1249 = unwrapped_fields1248[1]
        pretty_term(pp, field1249)
        newline(pp)
        field1250 = unwrapped_fields1248[2]
        pretty_term(pp, field1250)
        newline(pp)
        field1251 = unwrapped_fields1248[3]
        pretty_term(pp, field1251)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1258 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1258)
        write(pp, flat1258)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1830 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1830 = nothing
        end
        fields1253 = _t1830
        unwrapped_fields1254 = fields1253
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1255 = unwrapped_fields1254[1]
        pretty_term(pp, field1255)
        newline(pp)
        field1256 = unwrapped_fields1254[2]
        pretty_term(pp, field1256)
        newline(pp)
        field1257 = unwrapped_fields1254[3]
        pretty_term(pp, field1257)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1264 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1264)
        write(pp, flat1264)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1831 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1831 = nothing
        end
        fields1259 = _t1831
        unwrapped_fields1260 = fields1259
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1261 = unwrapped_fields1260[1]
        pretty_term(pp, field1261)
        newline(pp)
        field1262 = unwrapped_fields1260[2]
        pretty_term(pp, field1262)
        newline(pp)
        field1263 = unwrapped_fields1260[3]
        pretty_term(pp, field1263)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1269 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1269)
        write(pp, flat1269)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1832 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1832 = nothing
        end
        deconstruct_result1267 = _t1832
        if !isnothing(deconstruct_result1267)
            unwrapped1268 = deconstruct_result1267
            pretty_specialized_value(pp, unwrapped1268)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1833 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1833 = nothing
            end
            deconstruct_result1265 = _t1833
            if !isnothing(deconstruct_result1265)
                unwrapped1266 = deconstruct_result1265
                pretty_term(pp, unwrapped1266)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1271 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1271)
        write(pp, flat1271)
        return nothing
    else
        fields1270 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1270)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1278 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1278)
        write(pp, flat1278)
        return nothing
    else
        _dollar_dollar = msg
        fields1272 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1273 = fields1272
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1274 = unwrapped_fields1273[1]
        pretty_name(pp, field1274)
        field1275 = unwrapped_fields1273[2]
        if !isempty(field1275)
            newline(pp)
            for (i1834, elem1276) in enumerate(field1275)
                i1277 = i1834 - 1
                if (i1277 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1276)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1283 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1283)
        write(pp, flat1283)
        return nothing
    else
        _dollar_dollar = msg
        fields1279 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1280 = fields1279
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1281 = unwrapped_fields1280[1]
        pretty_term(pp, field1281)
        newline(pp)
        field1282 = unwrapped_fields1280[2]
        pretty_term(pp, field1282)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1287 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1287)
        write(pp, flat1287)
        return nothing
    else
        fields1284 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1284)
            newline(pp)
            for (i1835, elem1285) in enumerate(fields1284)
                i1286 = i1835 - 1
                if (i1286 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1285)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1294 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1294)
        write(pp, flat1294)
        return nothing
    else
        _dollar_dollar = msg
        fields1288 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1289 = fields1288
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1290 = unwrapped_fields1289[1]
        pretty_name(pp, field1290)
        field1291 = unwrapped_fields1289[2]
        if !isempty(field1291)
            newline(pp)
            for (i1836, elem1292) in enumerate(field1291)
                i1293 = i1836 - 1
                if (i1293 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1292)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1303 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1303)
        write(pp, flat1303)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1837 = _dollar_dollar.attrs
        else
            _t1837 = nothing
        end
        fields1295 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1837,)
        unwrapped_fields1296 = fields1295
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1297 = unwrapped_fields1296[1]
        if !isempty(field1297)
            newline(pp)
            for (i1838, elem1298) in enumerate(field1297)
                i1299 = i1838 - 1
                if (i1299 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1298)
            end
        end
        newline(pp)
        field1300 = unwrapped_fields1296[2]
        pretty_script(pp, field1300)
        field1301 = unwrapped_fields1296[3]
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

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1308 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1308)
        write(pp, flat1308)
        return nothing
    else
        _dollar_dollar = msg
        fields1304 = _dollar_dollar.constructs
        unwrapped_fields1305 = fields1304
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1305)
            newline(pp)
            for (i1839, elem1306) in enumerate(unwrapped_fields1305)
                i1307 = i1839 - 1
                if (i1307 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1306)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1313 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1313)
        write(pp, flat1313)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1840 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1840 = nothing
        end
        deconstruct_result1311 = _t1840
        if !isnothing(deconstruct_result1311)
            unwrapped1312 = deconstruct_result1311
            pretty_loop(pp, unwrapped1312)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1841 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1841 = nothing
            end
            deconstruct_result1309 = _t1841
            if !isnothing(deconstruct_result1309)
                unwrapped1310 = deconstruct_result1309
                pretty_instruction(pp, unwrapped1310)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1320 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1320)
        write(pp, flat1320)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1842 = _dollar_dollar.attrs
        else
            _t1842 = nothing
        end
        fields1314 = (_dollar_dollar.init, _dollar_dollar.body, _t1842,)
        unwrapped_fields1315 = fields1314
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1316 = unwrapped_fields1315[1]
        pretty_init(pp, field1316)
        newline(pp)
        field1317 = unwrapped_fields1315[2]
        pretty_script(pp, field1317)
        field1318 = unwrapped_fields1315[3]
        if !isnothing(field1318)
            newline(pp)
            opt_val1319 = field1318
            pretty_attrs(pp, opt_val1319)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1324 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1324)
        write(pp, flat1324)
        return nothing
    else
        fields1321 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1321)
            newline(pp)
            for (i1843, elem1322) in enumerate(fields1321)
                i1323 = i1843 - 1
                if (i1323 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1322)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1335 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1335)
        write(pp, flat1335)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1844 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1844 = nothing
        end
        deconstruct_result1333 = _t1844
        if !isnothing(deconstruct_result1333)
            unwrapped1334 = deconstruct_result1333
            pretty_assign(pp, unwrapped1334)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1845 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1845 = nothing
            end
            deconstruct_result1331 = _t1845
            if !isnothing(deconstruct_result1331)
                unwrapped1332 = deconstruct_result1331
                pretty_upsert(pp, unwrapped1332)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1846 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1846 = nothing
                end
                deconstruct_result1329 = _t1846
                if !isnothing(deconstruct_result1329)
                    unwrapped1330 = deconstruct_result1329
                    pretty_break(pp, unwrapped1330)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1847 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1847 = nothing
                    end
                    deconstruct_result1327 = _t1847
                    if !isnothing(deconstruct_result1327)
                        unwrapped1328 = deconstruct_result1327
                        pretty_monoid_def(pp, unwrapped1328)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1848 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1848 = nothing
                        end
                        deconstruct_result1325 = _t1848
                        if !isnothing(deconstruct_result1325)
                            unwrapped1326 = deconstruct_result1325
                            pretty_monus_def(pp, unwrapped1326)
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
    flat1342 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1342)
        write(pp, flat1342)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1849 = _dollar_dollar.attrs
        else
            _t1849 = nothing
        end
        fields1336 = (_dollar_dollar.name, _dollar_dollar.body, _t1849,)
        unwrapped_fields1337 = fields1336
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1338 = unwrapped_fields1337[1]
        pretty_relation_id(pp, field1338)
        newline(pp)
        field1339 = unwrapped_fields1337[2]
        pretty_abstraction(pp, field1339)
        field1340 = unwrapped_fields1337[3]
        if !isnothing(field1340)
            newline(pp)
            opt_val1341 = field1340
            pretty_attrs(pp, opt_val1341)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1349 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1349)
        write(pp, flat1349)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1850 = _dollar_dollar.attrs
        else
            _t1850 = nothing
        end
        fields1343 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1850,)
        unwrapped_fields1344 = fields1343
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1345 = unwrapped_fields1344[1]
        pretty_relation_id(pp, field1345)
        newline(pp)
        field1346 = unwrapped_fields1344[2]
        pretty_abstraction_with_arity(pp, field1346)
        field1347 = unwrapped_fields1344[3]
        if !isnothing(field1347)
            newline(pp)
            opt_val1348 = field1347
            pretty_attrs(pp, opt_val1348)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1354 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1354)
        write(pp, flat1354)
        return nothing
    else
        _dollar_dollar = msg
        _t1851 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1350 = (_t1851, _dollar_dollar[1].value,)
        unwrapped_fields1351 = fields1350
        write(pp, "(")
        indent!(pp)
        field1352 = unwrapped_fields1351[1]
        pretty_bindings(pp, field1352)
        newline(pp)
        field1353 = unwrapped_fields1351[2]
        pretty_formula(pp, field1353)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1361 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1361)
        write(pp, flat1361)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1852 = _dollar_dollar.attrs
        else
            _t1852 = nothing
        end
        fields1355 = (_dollar_dollar.name, _dollar_dollar.body, _t1852,)
        unwrapped_fields1356 = fields1355
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1357 = unwrapped_fields1356[1]
        pretty_relation_id(pp, field1357)
        newline(pp)
        field1358 = unwrapped_fields1356[2]
        pretty_abstraction(pp, field1358)
        field1359 = unwrapped_fields1356[3]
        if !isnothing(field1359)
            newline(pp)
            opt_val1360 = field1359
            pretty_attrs(pp, opt_val1360)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1369 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1369)
        write(pp, flat1369)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1853 = _dollar_dollar.attrs
        else
            _t1853 = nothing
        end
        fields1362 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1853,)
        unwrapped_fields1363 = fields1362
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1364 = unwrapped_fields1363[1]
        pretty_monoid(pp, field1364)
        newline(pp)
        field1365 = unwrapped_fields1363[2]
        pretty_relation_id(pp, field1365)
        newline(pp)
        field1366 = unwrapped_fields1363[3]
        pretty_abstraction_with_arity(pp, field1366)
        field1367 = unwrapped_fields1363[4]
        if !isnothing(field1367)
            newline(pp)
            opt_val1368 = field1367
            pretty_attrs(pp, opt_val1368)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1378 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1378)
        write(pp, flat1378)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1854 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1854 = nothing
        end
        deconstruct_result1376 = _t1854
        if !isnothing(deconstruct_result1376)
            unwrapped1377 = deconstruct_result1376
            pretty_or_monoid(pp, unwrapped1377)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1855 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1855 = nothing
            end
            deconstruct_result1374 = _t1855
            if !isnothing(deconstruct_result1374)
                unwrapped1375 = deconstruct_result1374
                pretty_min_monoid(pp, unwrapped1375)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1856 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1856 = nothing
                end
                deconstruct_result1372 = _t1856
                if !isnothing(deconstruct_result1372)
                    unwrapped1373 = deconstruct_result1372
                    pretty_max_monoid(pp, unwrapped1373)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1857 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1857 = nothing
                    end
                    deconstruct_result1370 = _t1857
                    if !isnothing(deconstruct_result1370)
                        unwrapped1371 = deconstruct_result1370
                        pretty_sum_monoid(pp, unwrapped1371)
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
    fields1379 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1382 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1382)
        write(pp, flat1382)
        return nothing
    else
        _dollar_dollar = msg
        fields1380 = _dollar_dollar.var"#type"
        unwrapped_fields1381 = fields1380
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1381)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1385 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1385)
        write(pp, flat1385)
        return nothing
    else
        _dollar_dollar = msg
        fields1383 = _dollar_dollar.var"#type"
        unwrapped_fields1384 = fields1383
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1384)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1388 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1388)
        write(pp, flat1388)
        return nothing
    else
        _dollar_dollar = msg
        fields1386 = _dollar_dollar.var"#type"
        unwrapped_fields1387 = fields1386
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1387)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1396 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1396)
        write(pp, flat1396)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1858 = _dollar_dollar.attrs
        else
            _t1858 = nothing
        end
        fields1389 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1858,)
        unwrapped_fields1390 = fields1389
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1391 = unwrapped_fields1390[1]
        pretty_monoid(pp, field1391)
        newline(pp)
        field1392 = unwrapped_fields1390[2]
        pretty_relation_id(pp, field1392)
        newline(pp)
        field1393 = unwrapped_fields1390[3]
        pretty_abstraction_with_arity(pp, field1393)
        field1394 = unwrapped_fields1390[4]
        if !isnothing(field1394)
            newline(pp)
            opt_val1395 = field1394
            pretty_attrs(pp, opt_val1395)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1403 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1403)
        write(pp, flat1403)
        return nothing
    else
        _dollar_dollar = msg
        fields1397 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1398 = fields1397
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1399 = unwrapped_fields1398[1]
        pretty_relation_id(pp, field1399)
        newline(pp)
        field1400 = unwrapped_fields1398[2]
        pretty_abstraction(pp, field1400)
        newline(pp)
        field1401 = unwrapped_fields1398[3]
        pretty_functional_dependency_keys(pp, field1401)
        newline(pp)
        field1402 = unwrapped_fields1398[4]
        pretty_functional_dependency_values(pp, field1402)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1407 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1407)
        write(pp, flat1407)
        return nothing
    else
        fields1404 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1404)
            newline(pp)
            for (i1859, elem1405) in enumerate(fields1404)
                i1406 = i1859 - 1
                if (i1406 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1405)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1411 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1411)
        write(pp, flat1411)
        return nothing
    else
        fields1408 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1408)
            newline(pp)
            for (i1860, elem1409) in enumerate(fields1408)
                i1410 = i1860 - 1
                if (i1410 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1409)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1420 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1420)
        write(pp, flat1420)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1861 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1861 = nothing
        end
        deconstruct_result1418 = _t1861
        if !isnothing(deconstruct_result1418)
            unwrapped1419 = deconstruct_result1418
            pretty_edb(pp, unwrapped1419)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1862 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1862 = nothing
            end
            deconstruct_result1416 = _t1862
            if !isnothing(deconstruct_result1416)
                unwrapped1417 = deconstruct_result1416
                pretty_betree_relation(pp, unwrapped1417)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1863 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1863 = nothing
                end
                deconstruct_result1414 = _t1863
                if !isnothing(deconstruct_result1414)
                    unwrapped1415 = deconstruct_result1414
                    pretty_csv_data(pp, unwrapped1415)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1864 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1864 = nothing
                    end
                    deconstruct_result1412 = _t1864
                    if !isnothing(deconstruct_result1412)
                        unwrapped1413 = deconstruct_result1412
                        pretty_iceberg_data(pp, unwrapped1413)
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
    flat1426 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1426)
        write(pp, flat1426)
        return nothing
    else
        _dollar_dollar = msg
        fields1421 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1422 = fields1421
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1423 = unwrapped_fields1422[1]
        pretty_relation_id(pp, field1423)
        newline(pp)
        field1424 = unwrapped_fields1422[2]
        pretty_edb_path(pp, field1424)
        newline(pp)
        field1425 = unwrapped_fields1422[3]
        pretty_edb_types(pp, field1425)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1430 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1430)
        write(pp, flat1430)
        return nothing
    else
        fields1427 = msg
        write(pp, "[")
        indent!(pp)
        for (i1865, elem1428) in enumerate(fields1427)
            i1429 = i1865 - 1
            if (i1429 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1428))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1434 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1434)
        write(pp, flat1434)
        return nothing
    else
        fields1431 = msg
        write(pp, "[")
        indent!(pp)
        for (i1866, elem1432) in enumerate(fields1431)
            i1433 = i1866 - 1
            if (i1433 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1432)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1439 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1439)
        write(pp, flat1439)
        return nothing
    else
        _dollar_dollar = msg
        fields1435 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1436 = fields1435
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1437 = unwrapped_fields1436[1]
        pretty_relation_id(pp, field1437)
        newline(pp)
        field1438 = unwrapped_fields1436[2]
        pretty_betree_info(pp, field1438)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1445 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1445)
        write(pp, flat1445)
        return nothing
    else
        _dollar_dollar = msg
        _t1867 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1440 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1867,)
        unwrapped_fields1441 = fields1440
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1442 = unwrapped_fields1441[1]
        pretty_betree_info_key_types(pp, field1442)
        newline(pp)
        field1443 = unwrapped_fields1441[2]
        pretty_betree_info_value_types(pp, field1443)
        newline(pp)
        field1444 = unwrapped_fields1441[3]
        pretty_config_dict(pp, field1444)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1449 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1449)
        write(pp, flat1449)
        return nothing
    else
        fields1446 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1446)
            newline(pp)
            for (i1868, elem1447) in enumerate(fields1446)
                i1448 = i1868 - 1
                if (i1448 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1447)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1453 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1453)
        write(pp, flat1453)
        return nothing
    else
        fields1450 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1450)
            newline(pp)
            for (i1869, elem1451) in enumerate(fields1450)
                i1452 = i1869 - 1
                if (i1452 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1451)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1463 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1463)
        write(pp, flat1463)
        return nothing
    else
        _dollar_dollar = msg
        _t1870 = deconstruct_csv_data_columns_optional(pp, _dollar_dollar)
        _t1871 = deconstruct_csv_data_relations_optional(pp, _dollar_dollar)
        fields1454 = (_dollar_dollar.locator, _dollar_dollar.config, _t1870, _t1871, _dollar_dollar.asof,)
        unwrapped_fields1455 = fields1454
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1456 = unwrapped_fields1455[1]
        pretty_csvlocator(pp, field1456)
        newline(pp)
        field1457 = unwrapped_fields1455[2]
        pretty_csv_config(pp, field1457)
        field1458 = unwrapped_fields1455[3]
        if !isnothing(field1458)
            newline(pp)
            opt_val1459 = field1458
            pretty_gnf_columns(pp, opt_val1459)
        end
        field1460 = unwrapped_fields1455[4]
        if !isnothing(field1460)
            newline(pp)
            opt_val1461 = field1460
            pretty_target_relations(pp, opt_val1461)
        end
        newline(pp)
        field1462 = unwrapped_fields1455[5]
        pretty_csv_asof(pp, field1462)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1470 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1470)
        write(pp, flat1470)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1872 = _dollar_dollar.paths
        else
            _t1872 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1873 = String(copy(_dollar_dollar.inline_data))
        else
            _t1873 = nothing
        end
        fields1464 = (_t1872, _t1873,)
        unwrapped_fields1465 = fields1464
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1466 = unwrapped_fields1465[1]
        if !isnothing(field1466)
            newline(pp)
            opt_val1467 = field1466
            pretty_csv_locator_paths(pp, opt_val1467)
        end
        field1468 = unwrapped_fields1465[2]
        if !isnothing(field1468)
            newline(pp)
            opt_val1469 = field1468
            pretty_csv_locator_inline_data(pp, opt_val1469)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1474 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1474)
        write(pp, flat1474)
        return nothing
    else
        fields1471 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1471)
            newline(pp)
            for (i1874, elem1472) in enumerate(fields1471)
                i1473 = i1874 - 1
                if (i1473 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1472))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1476 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1476)
        write(pp, flat1476)
        return nothing
    else
        fields1475 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1475))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1482 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1482)
        write(pp, flat1482)
        return nothing
    else
        _dollar_dollar = msg
        _t1875 = deconstruct_csv_config(pp, _dollar_dollar)
        _t1876 = deconstruct_csv_storage_integration_optional(pp, _dollar_dollar)
        fields1477 = (_t1875, _t1876,)
        unwrapped_fields1478 = fields1477
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1479 = unwrapped_fields1478[1]
        pretty_config_dict(pp, field1479)
        field1480 = unwrapped_fields1478[2]
        if !isnothing(field1480)
            newline(pp)
            opt_val1481 = field1480
            pretty__storage_integration(pp, opt_val1481)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty__storage_integration(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat1484 = try_flat(pp, msg, pretty__storage_integration)
    if !isnothing(flat1484)
        write(pp, flat1484)
        return nothing
    else
        fields1483 = msg
        write(pp, "(storage_integration")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, fields1483)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1488 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1488)
        write(pp, flat1488)
        return nothing
    else
        fields1485 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1485)
            newline(pp)
            for (i1877, elem1486) in enumerate(fields1485)
                i1487 = i1877 - 1
                if (i1487 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1486)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1497 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1497)
        write(pp, flat1497)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1878 = _dollar_dollar.target_id
        else
            _t1878 = nothing
        end
        fields1489 = (_dollar_dollar.column_path, _t1878, _dollar_dollar.types,)
        unwrapped_fields1490 = fields1489
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1491 = unwrapped_fields1490[1]
        pretty_gnf_column_path(pp, field1491)
        field1492 = unwrapped_fields1490[2]
        if !isnothing(field1492)
            newline(pp)
            opt_val1493 = field1492
            pretty_relation_id(pp, opt_val1493)
        end
        newline(pp)
        write(pp, "[")
        field1494 = unwrapped_fields1490[3]
        for (i1879, elem1495) in enumerate(field1494)
            i1496 = i1879 - 1
            if (i1496 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1495)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1504 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1504)
        write(pp, flat1504)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1880 = _dollar_dollar[1]
        else
            _t1880 = nothing
        end
        deconstruct_result1502 = _t1880
        if !isnothing(deconstruct_result1502)
            unwrapped1503 = deconstruct_result1502
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1503))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1881 = _dollar_dollar
            else
                _t1881 = nothing
            end
            deconstruct_result1498 = _t1881
            if !isnothing(deconstruct_result1498)
                unwrapped1499 = deconstruct_result1498
                write(pp, "[")
                indent!(pp)
                for (i1882, elem1500) in enumerate(unwrapped1499)
                    i1501 = i1882 - 1
                    if (i1501 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1500))
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
    flat1511 = try_flat(pp, msg, pretty_target_relations)
    if !isnothing(flat1511)
        write(pp, flat1511)
        return nothing
    else
        _dollar_dollar = msg
        _t1883 = deconstruct_relation_keys(pp, _dollar_dollar)
        _t1884 = deconstruct_load_errors_optional(pp, _dollar_dollar)
        fields1505 = (_t1883, _dollar_dollar, _t1884,)
        unwrapped_fields1506 = fields1505
        write(pp, "(relations")
        indent_sexp!(pp)
        newline(pp)
        field1507 = unwrapped_fields1506[1]
        pretty_relation_keys(pp, field1507)
        newline(pp)
        field1508 = unwrapped_fields1506[2]
        pretty_relation_body(pp, field1508)
        field1509 = unwrapped_fields1506[3]
        if !isnothing(field1509)
            newline(pp)
            opt_val1510 = field1509
            pretty_load_errors(pp, opt_val1510)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_keys(pp::PrettyPrinter, msg::Tuple{Vector{Proto.NamedColumn}, Bool})
    flat1518 = try_flat(pp, msg, pretty_relation_keys)
    if !isnothing(flat1518)
        write(pp, flat1518)
        return nothing
    else
        _dollar_dollar = msg
        if !_dollar_dollar[2]
            _t1885 = _dollar_dollar[1]
        else
            _t1885 = nothing
        end
        deconstruct_result1514 = _t1885
        if !isnothing(deconstruct_result1514)
            unwrapped1515 = deconstruct_result1514
            write(pp, "(keys")
            indent_sexp!(pp)
            if !isempty(unwrapped1515)
                newline(pp)
                for (i1886, elem1516) in enumerate(unwrapped1515)
                    i1517 = i1886 - 1
                    if (i1517 > 0)
                        newline(pp)
                    end
                    pretty_named_column(pp, elem1516)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _dollar_dollar[2]
                _t1887 = ()
            else
                _t1887 = nothing
            end
            deconstruct_result1512 = _t1887
            if !isnothing(deconstruct_result1512)
                unwrapped1513 = deconstruct_result1512
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
    flat1523 = try_flat(pp, msg, pretty_named_column)
    if !isnothing(flat1523)
        write(pp, flat1523)
        return nothing
    else
        _dollar_dollar = msg
        fields1519 = (_dollar_dollar.name, _dollar_dollar.var"#type",)
        unwrapped_fields1520 = fields1519
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1521 = unwrapped_fields1520[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1521))
        newline(pp)
        field1522 = unwrapped_fields1520[2]
        pretty_type(pp, field1522)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_body(pp::PrettyPrinter, msg::Proto.TargetRelations)
    flat1530 = try_flat(pp, msg, pretty_relation_body)
    if !isnothing(flat1530)
        write(pp, flat1530)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("plain"))
            _t1888 = _get_oneof_field(_dollar_dollar, :plain).targets
        else
            _t1888 = nothing
        end
        deconstruct_result1528 = _t1888
        if !isnothing(deconstruct_result1528)
            unwrapped1529 = deconstruct_result1528
            pretty_non_cdc_relations(pp, unwrapped1529)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("cdc"))
                _t1889 = (_get_oneof_field(_dollar_dollar, :cdc).inserts, _get_oneof_field(_dollar_dollar, :cdc).deletes,)
            else
                _t1889 = nothing
            end
            deconstruct_result1524 = _t1889
            if !isnothing(deconstruct_result1524)
                unwrapped1525 = deconstruct_result1524
                field1526 = unwrapped1525[1]
                pretty_cdc_inserts(pp, field1526)
                write(pp, " ")
                field1527 = unwrapped1525[2]
                pretty_cdc_deletes(pp, field1527)
            else
                throw(ParseError("No matching rule for relation_body"))
            end
        end
    end
    return nothing
end

function pretty_non_cdc_relations(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1534 = try_flat(pp, msg, pretty_non_cdc_relations)
    if !isnothing(flat1534)
        write(pp, flat1534)
        return nothing
    else
        fields1531 = msg
        for (i1890, elem1532) in enumerate(fields1531)
            i1533 = i1890 - 1
            if (i1533 > 0)
                newline(pp)
            end
            pretty_target_relation(pp, elem1532)
        end
    end
    return nothing
end

function pretty_target_relation(pp::PrettyPrinter, msg::Proto.TargetRelation)
    flat1541 = try_flat(pp, msg, pretty_target_relation)
    if !isnothing(flat1541)
        write(pp, flat1541)
        return nothing
    else
        _dollar_dollar = msg
        fields1535 = (_dollar_dollar.target_id, _dollar_dollar.values,)
        unwrapped_fields1536 = fields1535
        write(pp, "(relation")
        indent_sexp!(pp)
        newline(pp)
        field1537 = unwrapped_fields1536[1]
        pretty_relation_id(pp, field1537)
        field1538 = unwrapped_fields1536[2]
        if !isempty(field1538)
            newline(pp)
            for (i1891, elem1539) in enumerate(field1538)
                i1540 = i1891 - 1
                if (i1540 > 0)
                    newline(pp)
                end
                pretty_named_column(pp, elem1539)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_inserts(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1545 = try_flat(pp, msg, pretty_cdc_inserts)
    if !isnothing(flat1545)
        write(pp, flat1545)
        return nothing
    else
        fields1542 = msg
        write(pp, "(inserts")
        indent_sexp!(pp)
        if !isempty(fields1542)
            newline(pp)
            for (i1892, elem1543) in enumerate(fields1542)
                i1544 = i1892 - 1
                if (i1544 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1543)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_deletes(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1549 = try_flat(pp, msg, pretty_cdc_deletes)
    if !isnothing(flat1549)
        write(pp, flat1549)
        return nothing
    else
        fields1546 = msg
        write(pp, "(deletes")
        indent_sexp!(pp)
        if !isempty(fields1546)
            newline(pp)
            for (i1893, elem1547) in enumerate(fields1546)
                i1548 = i1893 - 1
                if (i1548 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1547)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_load_errors(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1551 = try_flat(pp, msg, pretty_load_errors)
    if !isnothing(flat1551)
        write(pp, flat1551)
        return nothing
    else
        fields1550 = msg
        write(pp, "(load_errors")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1550)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1553 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1553)
        write(pp, flat1553)
        return nothing
    else
        fields1552 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1552))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1567 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1567)
        write(pp, flat1567)
        return nothing
    else
        _dollar_dollar = msg
        _t1894 = deconstruct_iceberg_data_columns_optional(pp, _dollar_dollar)
        _t1895 = deconstruct_iceberg_data_relations_optional(pp, _dollar_dollar)
        _t1896 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1897 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1554 = (_dollar_dollar.locator, _dollar_dollar.config, _t1894, _t1895, _t1896, _t1897, _dollar_dollar.returns_delta,)
        unwrapped_fields1555 = fields1554
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1556 = unwrapped_fields1555[1]
        pretty_iceberg_locator(pp, field1556)
        newline(pp)
        field1557 = unwrapped_fields1555[2]
        pretty_iceberg_catalog_config(pp, field1557)
        field1558 = unwrapped_fields1555[3]
        if !isnothing(field1558)
            newline(pp)
            opt_val1559 = field1558
            pretty_gnf_columns(pp, opt_val1559)
        end
        field1560 = unwrapped_fields1555[4]
        if !isnothing(field1560)
            newline(pp)
            opt_val1561 = field1560
            pretty_target_relations(pp, opt_val1561)
        end
        field1562 = unwrapped_fields1555[5]
        if !isnothing(field1562)
            newline(pp)
            opt_val1563 = field1562
            pretty_iceberg_from_snapshot(pp, opt_val1563)
        end
        field1564 = unwrapped_fields1555[6]
        if !isnothing(field1564)
            newline(pp)
            opt_val1565 = field1564
            pretty_iceberg_to_snapshot(pp, opt_val1565)
        end
        newline(pp)
        field1566 = unwrapped_fields1555[7]
        pretty_boolean_value(pp, field1566)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1573 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1573)
        write(pp, flat1573)
        return nothing
    else
        _dollar_dollar = msg
        fields1568 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1569 = fields1568
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1570 = unwrapped_fields1569[1]
        pretty_iceberg_locator_table_name(pp, field1570)
        newline(pp)
        field1571 = unwrapped_fields1569[2]
        pretty_iceberg_locator_namespace(pp, field1571)
        newline(pp)
        field1572 = unwrapped_fields1569[3]
        pretty_iceberg_locator_warehouse(pp, field1572)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1575 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1575)
        write(pp, flat1575)
        return nothing
    else
        fields1574 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1574))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1579 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1579)
        write(pp, flat1579)
        return nothing
    else
        fields1576 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1576)
            newline(pp)
            for (i1898, elem1577) in enumerate(fields1576)
                i1578 = i1898 - 1
                if (i1578 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1577))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1581 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1581)
        write(pp, flat1581)
        return nothing
    else
        fields1580 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1580))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1589 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1589)
        write(pp, flat1589)
        return nothing
    else
        _dollar_dollar = msg
        _t1899 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1582 = (_dollar_dollar.catalog_uri, _t1899, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1583 = fields1582
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1584 = unwrapped_fields1583[1]
        pretty_iceberg_catalog_uri(pp, field1584)
        field1585 = unwrapped_fields1583[2]
        if !isnothing(field1585)
            newline(pp)
            opt_val1586 = field1585
            pretty_iceberg_catalog_config_scope(pp, opt_val1586)
        end
        newline(pp)
        field1587 = unwrapped_fields1583[3]
        pretty_iceberg_properties(pp, field1587)
        newline(pp)
        field1588 = unwrapped_fields1583[4]
        pretty_iceberg_auth_properties(pp, field1588)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1591 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1591)
        write(pp, flat1591)
        return nothing
    else
        fields1590 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1590))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1593 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1593)
        write(pp, flat1593)
        return nothing
    else
        fields1592 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1592))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1597 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1597)
        write(pp, flat1597)
        return nothing
    else
        fields1594 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1594)
            newline(pp)
            for (i1900, elem1595) in enumerate(fields1594)
                i1596 = i1900 - 1
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

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1602 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1602)
        write(pp, flat1602)
        return nothing
    else
        _dollar_dollar = msg
        fields1598 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1599 = fields1598
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1600 = unwrapped_fields1599[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1600))
        newline(pp)
        field1601 = unwrapped_fields1599[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1601))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1606 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1606)
        write(pp, flat1606)
        return nothing
    else
        fields1603 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1603)
            newline(pp)
            for (i1901, elem1604) in enumerate(fields1603)
                i1605 = i1901 - 1
                if (i1605 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1604)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1611 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1611)
        write(pp, flat1611)
        return nothing
    else
        _dollar_dollar = msg
        _t1902 = mask_secret_value(pp, _dollar_dollar)
        fields1607 = (_dollar_dollar[1], _t1902,)
        unwrapped_fields1608 = fields1607
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1609 = unwrapped_fields1608[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1609))
        newline(pp)
        field1610 = unwrapped_fields1608[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1610))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1613 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1613)
        write(pp, flat1613)
        return nothing
    else
        fields1612 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1612))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1615 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1615)
        write(pp, flat1615)
        return nothing
    else
        fields1614 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1614))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1618 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1618)
        write(pp, flat1618)
        return nothing
    else
        _dollar_dollar = msg
        fields1616 = _dollar_dollar.fragment_id
        unwrapped_fields1617 = fields1616
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1617)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1623 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1623)
        write(pp, flat1623)
        return nothing
    else
        _dollar_dollar = msg
        fields1619 = _dollar_dollar.relations
        unwrapped_fields1620 = fields1619
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1620)
            newline(pp)
            for (i1903, elem1621) in enumerate(unwrapped_fields1620)
                i1622 = i1903 - 1
                if (i1622 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1621)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1630 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1630)
        write(pp, flat1630)
        return nothing
    else
        _dollar_dollar = msg
        fields1624 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1625 = fields1624
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1626 = unwrapped_fields1625[1]
        pretty_edb_path(pp, field1626)
        field1627 = unwrapped_fields1625[2]
        if !isempty(field1627)
            newline(pp)
            for (i1904, elem1628) in enumerate(field1627)
                i1629 = i1904 - 1
                if (i1629 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1628)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1635 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1635)
        write(pp, flat1635)
        return nothing
    else
        _dollar_dollar = msg
        fields1631 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1632 = fields1631
        field1633 = unwrapped_fields1632[1]
        pretty_edb_path(pp, field1633)
        write(pp, " ")
        field1634 = unwrapped_fields1632[2]
        pretty_relation_id(pp, field1634)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1639 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1639)
        write(pp, flat1639)
        return nothing
    else
        fields1636 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1636)
            newline(pp)
            for (i1905, elem1637) in enumerate(fields1636)
                i1638 = i1905 - 1
                if (i1638 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1637)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1650 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1650)
        write(pp, flat1650)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1906 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1906 = nothing
        end
        deconstruct_result1648 = _t1906
        if !isnothing(deconstruct_result1648)
            unwrapped1649 = deconstruct_result1648
            pretty_demand(pp, unwrapped1649)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1907 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1907 = nothing
            end
            deconstruct_result1646 = _t1907
            if !isnothing(deconstruct_result1646)
                unwrapped1647 = deconstruct_result1646
                pretty_output(pp, unwrapped1647)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1908 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1908 = nothing
                end
                deconstruct_result1644 = _t1908
                if !isnothing(deconstruct_result1644)
                    unwrapped1645 = deconstruct_result1644
                    pretty_what_if(pp, unwrapped1645)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1909 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1909 = nothing
                    end
                    deconstruct_result1642 = _t1909
                    if !isnothing(deconstruct_result1642)
                        unwrapped1643 = deconstruct_result1642
                        pretty_abort(pp, unwrapped1643)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1910 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1910 = nothing
                        end
                        deconstruct_result1640 = _t1910
                        if !isnothing(deconstruct_result1640)
                            unwrapped1641 = deconstruct_result1640
                            pretty_export(pp, unwrapped1641)
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
    flat1653 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1653)
        write(pp, flat1653)
        return nothing
    else
        _dollar_dollar = msg
        fields1651 = _dollar_dollar.relation_id
        unwrapped_fields1652 = fields1651
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1652)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1658 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1658)
        write(pp, flat1658)
        return nothing
    else
        _dollar_dollar = msg
        fields1654 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1655 = fields1654
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1656 = unwrapped_fields1655[1]
        pretty_name(pp, field1656)
        newline(pp)
        field1657 = unwrapped_fields1655[2]
        pretty_relation_id(pp, field1657)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1663 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1663)
        write(pp, flat1663)
        return nothing
    else
        _dollar_dollar = msg
        fields1659 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1660 = fields1659
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1661 = unwrapped_fields1660[1]
        pretty_name(pp, field1661)
        newline(pp)
        field1662 = unwrapped_fields1660[2]
        pretty_epoch(pp, field1662)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1669 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1669)
        write(pp, flat1669)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1911 = _dollar_dollar.name
        else
            _t1911 = nothing
        end
        fields1664 = (_t1911, _dollar_dollar.relation_id,)
        unwrapped_fields1665 = fields1664
        write(pp, "(abort")
        indent_sexp!(pp)
        field1666 = unwrapped_fields1665[1]
        if !isnothing(field1666)
            newline(pp)
            opt_val1667 = field1666
            pretty_name(pp, opt_val1667)
        end
        newline(pp)
        field1668 = unwrapped_fields1665[2]
        pretty_relation_id(pp, field1668)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1674 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1674)
        write(pp, flat1674)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1912 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1912 = nothing
        end
        deconstruct_result1672 = _t1912
        if !isnothing(deconstruct_result1672)
            unwrapped1673 = deconstruct_result1672
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1673)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1913 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1913 = nothing
            end
            deconstruct_result1670 = _t1913
            if !isnothing(deconstruct_result1670)
                unwrapped1671 = deconstruct_result1670
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1671)
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
    flat1685 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1685)
        write(pp, flat1685)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1915 = deconstruct_export_csv_output_location(pp, _dollar_dollar)
            _t1914 = (_t1915, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1914 = nothing
        end
        deconstruct_result1680 = _t1914
        if !isnothing(deconstruct_result1680)
            unwrapped1681 = deconstruct_result1680
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1682 = unwrapped1681[1]
            pretty_export_csv_output_location(pp, field1682)
            newline(pp)
            field1683 = unwrapped1681[2]
            pretty_export_csv_source(pp, field1683)
            newline(pp)
            field1684 = unwrapped1681[3]
            pretty_csv_config(pp, field1684)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1917 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1916 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1917,)
            else
                _t1916 = nothing
            end
            deconstruct_result1675 = _t1916
            if !isnothing(deconstruct_result1675)
                unwrapped1676 = deconstruct_result1675
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1677 = unwrapped1676[1]
                pretty_export_csv_path(pp, field1677)
                newline(pp)
                field1678 = unwrapped1676[2]
                pretty_export_csv_columns_list(pp, field1678)
                newline(pp)
                field1679 = unwrapped1676[3]
                pretty_config_dict(pp, field1679)
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
    flat1690 = try_flat(pp, msg, pretty_export_csv_output_location)
    if !isnothing(flat1690)
        write(pp, flat1690)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar[1] != ""
            _t1918 = _dollar_dollar[1]
        else
            _t1918 = nothing
        end
        deconstruct_result1688 = _t1918
        if !isnothing(deconstruct_result1688)
            unwrapped1689 = deconstruct_result1688
            write(pp, "(path")
            indent_sexp!(pp)
            newline(pp)
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1689))
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _dollar_dollar[2] != ""
                _t1919 = _dollar_dollar[2]
            else
                _t1919 = nothing
            end
            deconstruct_result1686 = _t1919
            if !isnothing(deconstruct_result1686)
                unwrapped1687 = deconstruct_result1686
                write(pp, "(transaction_output_name")
                indent_sexp!(pp)
                newline(pp)
                pretty_name(pp, unwrapped1687)
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
    flat1697 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1697)
        write(pp, flat1697)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1920 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1920 = nothing
        end
        deconstruct_result1693 = _t1920
        if !isnothing(deconstruct_result1693)
            unwrapped1694 = deconstruct_result1693
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1694)
                newline(pp)
                for (i1921, elem1695) in enumerate(unwrapped1694)
                    i1696 = i1921 - 1
                    if (i1696 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1695)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1922 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1922 = nothing
            end
            deconstruct_result1691 = _t1922
            if !isnothing(deconstruct_result1691)
                unwrapped1692 = deconstruct_result1691
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1692)
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
    flat1702 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1702)
        write(pp, flat1702)
        return nothing
    else
        _dollar_dollar = msg
        fields1698 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1699 = fields1698
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1700 = unwrapped_fields1699[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1700))
        newline(pp)
        field1701 = unwrapped_fields1699[2]
        pretty_relation_id(pp, field1701)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1704 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1704)
        write(pp, flat1704)
        return nothing
    else
        fields1703 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1703))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1708 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1708)
        write(pp, flat1708)
        return nothing
    else
        fields1705 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1705)
            newline(pp)
            for (i1923, elem1706) in enumerate(fields1705)
                i1707 = i1923 - 1
                if (i1707 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1706)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1717 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1717)
        write(pp, flat1717)
        return nothing
    else
        _dollar_dollar = msg
        _t1924 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1709 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1924,)
        unwrapped_fields1710 = fields1709
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1711 = unwrapped_fields1710[1]
        pretty_iceberg_locator(pp, field1711)
        newline(pp)
        field1712 = unwrapped_fields1710[2]
        pretty_iceberg_catalog_config(pp, field1712)
        newline(pp)
        field1713 = unwrapped_fields1710[3]
        pretty_export_iceberg_table_def(pp, field1713)
        newline(pp)
        field1714 = unwrapped_fields1710[4]
        pretty_iceberg_table_properties(pp, field1714)
        field1715 = unwrapped_fields1710[5]
        if !isnothing(field1715)
            newline(pp)
            opt_val1716 = field1715
            pretty_config_dict(pp, opt_val1716)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1719 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1719)
        write(pp, flat1719)
        return nothing
    else
        fields1718 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1718)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1723 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1723)
        write(pp, flat1723)
        return nothing
    else
        fields1720 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1720)
            newline(pp)
            for (i1925, elem1721) in enumerate(fields1720)
                i1722 = i1925 - 1
                if (i1722 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1721)
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
    for (i1982, _rid) in enumerate(msg.ids)
        _idx = i1982 - 1
        newline(pp)
        write(pp, "(")
        _t1983 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1983)
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
    for (i1984, _elem) in enumerate(msg.inserts)
        _idx = i1984 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":deletes (")
    for (i1985, _elem) in enumerate(msg.deletes)
        _idx = i1985 - 1
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
    for (i1986, _elem) in enumerate(msg.keys)
        _idx = i1986 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1987, _elem) in enumerate(msg.values)
        _idx = i1987 - 1
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
    for (i1988, _elem) in enumerate(msg.targets)
        _idx = i1988 - 1
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
    for (i1989, _elem) in enumerate(msg.columns)
        _idx = i1989 - 1
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
