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

function deconstruct_csv_data_columns_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Vector{Proto.GNFColumn}}
    if _has_proto_field(msg, Symbol("relations"))
        return nothing
    else
        _t1889 = nothing
    end
    return msg.columns
end

function deconstruct_csv_data_relations_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Proto.TargetRelations}
    if _has_proto_field(msg, Symbol("relations"))
        return msg.relations
    else
        _t1890 = nothing
    end
    return nothing
end

function deconstruct_export_csv_output_location(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Tuple{String, String}
    return (msg.path, msg.transaction_output_name,)
end

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1891 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1891
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1892 = Proto.Value(value=OneOf(:int_value, v))
    return _t1892
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1893 = Proto.Value(value=OneOf(:float_value, v))
    return _t1893
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1894 = Proto.Value(value=OneOf(:string_value, v))
    return _t1894
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1895 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1895
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1896 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1896
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1897 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1897,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1898 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1898,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1899 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1899,))
            end
        end
    end
    _t1900 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1900,))
    if msg.ast_size_limit.warning_limit != 0
        _t1901 = _make_value_int64(pp, msg.ast_size_limit.warning_limit)
        push!(result, ("ast_size.warning_limit", _t1901,))
    end
    if msg.ast_size_limit.exception_limit != 0
        _t1902 = _make_value_int64(pp, msg.ast_size_limit.exception_limit)
        push!(result, ("ast_size.exception_limit", _t1902,))
    end
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1903 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1903,))
    _t1904 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1904,))
    if msg.new_line != ""
        _t1905 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1905,))
    end
    _t1906 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1906,))
    _t1907 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1907,))
    _t1908 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1908,))
    if msg.comment != ""
        _t1909 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1909,))
    end
    for missing_string in msg.missing_strings
        _t1910 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1910,))
    end
    _t1911 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1911,))
    _t1912 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1912,))
    _t1913 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1913,))
    if msg.partition_size_mb != 0
        _t1914 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1914,))
    end
    return sort(result)
end

function deconstruct_csv_storage_integration_optional(pp::PrettyPrinter, msg::Proto.CSVConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    if !_has_proto_field(msg, Symbol("storage_integration"))
        return nothing
    else
        _t1915 = nothing
    end
    si = msg.storage_integration
    result = Tuple{String, Proto.Value}[]
    if si.provider != ""
        _t1916 = _make_value_string(pp, si.provider)
        push!(result, ("provider", _t1916,))
    end
    if si.azure_sas_token != ""
        _t1917 = _make_value_string(pp, "***")
        push!(result, ("azure_sas_token", _t1917,))
    end
    if si.s3_region != ""
        _t1918 = _make_value_string(pp, si.s3_region)
        push!(result, ("s3_region", _t1918,))
    end
    if si.s3_access_key_id != ""
        _t1919 = _make_value_string(pp, "***")
        push!(result, ("s3_access_key_id", _t1919,))
    end
    if si.s3_secret_access_key != ""
        _t1920 = _make_value_string(pp, "***")
        push!(result, ("s3_secret_access_key", _t1920,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1921 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1921,))
    _t1922 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1922,))
    _t1923 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1923,))
    _t1924 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1924,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1925 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1925,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1926 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1926,))
        end
    end
    _t1927 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1927,))
    _t1928 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1928,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1929 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1929,))
    end
    if !isnothing(msg.compression)
        _t1930 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1930,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1931 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1931,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1932 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1932,))
    end
    if !isnothing(msg.syntax_delim)
        _t1933 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1933,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1934 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1934,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1935 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1935,))
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
        _t1936 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1937 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1938 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1939 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1939,))
    end
    if msg.target_file_size_bytes != 0
        _t1940 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1940,))
    end
    if msg.compression != ""
        _t1941 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1941,))
    end
    if length(result) == 0
        return nothing
    else
        _t1942 = nothing
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
        _t1943 = nothing
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
    flat856 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat856)
        write(pp, flat856)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1694 = _dollar_dollar.configure
        else
            _t1694 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1695 = _dollar_dollar.sync
        else
            _t1695 = nothing
        end
        fields847 = (_t1694, _t1695, _dollar_dollar.epochs,)
        unwrapped_fields848 = fields847
        write(pp, "(transaction")
        indent_sexp!(pp)
        field849 = unwrapped_fields848[1]
        if !isnothing(field849)
            newline(pp)
            opt_val850 = field849
            pretty_configure(pp, opt_val850)
        end
        field851 = unwrapped_fields848[2]
        if !isnothing(field851)
            newline(pp)
            opt_val852 = field851
            pretty_sync(pp, opt_val852)
        end
        field853 = unwrapped_fields848[3]
        if !isempty(field853)
            newline(pp)
            for (i1696, elem854) in enumerate(field853)
                i855 = i1696 - 1
                if (i855 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem854)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat859 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat859)
        write(pp, flat859)
        return nothing
    else
        _dollar_dollar = msg
        _t1697 = deconstruct_configure(pp, _dollar_dollar)
        fields857 = _t1697
        unwrapped_fields858 = fields857
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields858)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat863 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat863)
        write(pp, flat863)
        return nothing
    else
        fields860 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields860)
            newline(pp)
            for (i1698, elem861) in enumerate(fields860)
                i862 = i1698 - 1
                if (i862 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem861)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat868 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat868)
        write(pp, flat868)
        return nothing
    else
        _dollar_dollar = msg
        fields864 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields865 = fields864
        write(pp, ":")
        field866 = unwrapped_fields865[1]
        write(pp, field866)
        write(pp, " ")
        field867 = unwrapped_fields865[2]
        pretty_raw_value(pp, field867)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat894 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat894)
        write(pp, flat894)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1699 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1699 = nothing
        end
        deconstruct_result892 = _t1699
        if !isnothing(deconstruct_result892)
            unwrapped893 = deconstruct_result892
            pretty_raw_date(pp, unwrapped893)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1700 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1700 = nothing
            end
            deconstruct_result890 = _t1700
            if !isnothing(deconstruct_result890)
                unwrapped891 = deconstruct_result890
                pretty_raw_datetime(pp, unwrapped891)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1701 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1701 = nothing
                end
                deconstruct_result888 = _t1701
                if !isnothing(deconstruct_result888)
                    unwrapped889 = deconstruct_result888
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped889))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1702 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1702 = nothing
                    end
                    deconstruct_result886 = _t1702
                    if !isnothing(deconstruct_result886)
                        unwrapped887 = deconstruct_result886
                        write(pp, (string(Int64(unwrapped887)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1703 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1703 = nothing
                        end
                        deconstruct_result884 = _t1703
                        if !isnothing(deconstruct_result884)
                            unwrapped885 = deconstruct_result884
                            write(pp, string(unwrapped885))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1704 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1704 = nothing
                            end
                            deconstruct_result882 = _t1704
                            if !isnothing(deconstruct_result882)
                                unwrapped883 = deconstruct_result882
                                write(pp, format_float32_literal(unwrapped883))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1705 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1705 = nothing
                                end
                                deconstruct_result880 = _t1705
                                if !isnothing(deconstruct_result880)
                                    unwrapped881 = deconstruct_result880
                                    write(pp, lowercase(string(unwrapped881)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1706 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1706 = nothing
                                    end
                                    deconstruct_result878 = _t1706
                                    if !isnothing(deconstruct_result878)
                                        unwrapped879 = deconstruct_result878
                                        write(pp, (string(Int64(unwrapped879)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1707 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1707 = nothing
                                        end
                                        deconstruct_result876 = _t1707
                                        if !isnothing(deconstruct_result876)
                                            unwrapped877 = deconstruct_result876
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped877))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1708 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1708 = nothing
                                            end
                                            deconstruct_result874 = _t1708
                                            if !isnothing(deconstruct_result874)
                                                unwrapped875 = deconstruct_result874
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped875))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1709 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1709 = nothing
                                                end
                                                deconstruct_result872 = _t1709
                                                if !isnothing(deconstruct_result872)
                                                    unwrapped873 = deconstruct_result872
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped873))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1710 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1710 = nothing
                                                    end
                                                    deconstruct_result870 = _t1710
                                                    if !isnothing(deconstruct_result870)
                                                        unwrapped871 = deconstruct_result870
                                                        pretty_boolean_value(pp, unwrapped871)
                                                    else
                                                        fields869 = msg
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
    flat900 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat900)
        write(pp, flat900)
        return nothing
    else
        _dollar_dollar = msg
        fields895 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields896 = fields895
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field897 = unwrapped_fields896[1]
        write(pp, string(field897))
        newline(pp)
        field898 = unwrapped_fields896[2]
        write(pp, string(field898))
        newline(pp)
        field899 = unwrapped_fields896[3]
        write(pp, string(field899))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat911 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat911)
        write(pp, flat911)
        return nothing
    else
        _dollar_dollar = msg
        fields901 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields902 = fields901
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field903 = unwrapped_fields902[1]
        write(pp, string(field903))
        newline(pp)
        field904 = unwrapped_fields902[2]
        write(pp, string(field904))
        newline(pp)
        field905 = unwrapped_fields902[3]
        write(pp, string(field905))
        newline(pp)
        field906 = unwrapped_fields902[4]
        write(pp, string(field906))
        newline(pp)
        field907 = unwrapped_fields902[5]
        write(pp, string(field907))
        newline(pp)
        field908 = unwrapped_fields902[6]
        write(pp, string(field908))
        field909 = unwrapped_fields902[7]
        if !isnothing(field909)
            newline(pp)
            opt_val910 = field909
            write(pp, string(opt_val910))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1711 = ()
    else
        _t1711 = nothing
    end
    deconstruct_result914 = _t1711
    if !isnothing(deconstruct_result914)
        unwrapped915 = deconstruct_result914
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1712 = ()
        else
            _t1712 = nothing
        end
        deconstruct_result912 = _t1712
        if !isnothing(deconstruct_result912)
            unwrapped913 = deconstruct_result912
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat920 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat920)
        write(pp, flat920)
        return nothing
    else
        _dollar_dollar = msg
        fields916 = _dollar_dollar.fragments
        unwrapped_fields917 = fields916
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields917)
            newline(pp)
            for (i1713, elem918) in enumerate(unwrapped_fields917)
                i919 = i1713 - 1
                if (i919 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem918)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat923 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat923)
        write(pp, flat923)
        return nothing
    else
        _dollar_dollar = msg
        fields921 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields922 = fields921
        write(pp, ":")
        write(pp, unwrapped_fields922)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat930 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat930)
        write(pp, flat930)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1714 = _dollar_dollar.writes
        else
            _t1714 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1715 = _dollar_dollar.reads
        else
            _t1715 = nothing
        end
        fields924 = (_t1714, _t1715,)
        unwrapped_fields925 = fields924
        write(pp, "(epoch")
        indent_sexp!(pp)
        field926 = unwrapped_fields925[1]
        if !isnothing(field926)
            newline(pp)
            opt_val927 = field926
            pretty_epoch_writes(pp, opt_val927)
        end
        field928 = unwrapped_fields925[2]
        if !isnothing(field928)
            newline(pp)
            opt_val929 = field928
            pretty_epoch_reads(pp, opt_val929)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat934 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat934)
        write(pp, flat934)
        return nothing
    else
        fields931 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields931)
            newline(pp)
            for (i1716, elem932) in enumerate(fields931)
                i933 = i1716 - 1
                if (i933 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem932)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat943 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat943)
        write(pp, flat943)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1717 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1717 = nothing
        end
        deconstruct_result941 = _t1717
        if !isnothing(deconstruct_result941)
            unwrapped942 = deconstruct_result941
            pretty_define(pp, unwrapped942)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1718 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1718 = nothing
            end
            deconstruct_result939 = _t1718
            if !isnothing(deconstruct_result939)
                unwrapped940 = deconstruct_result939
                pretty_undefine(pp, unwrapped940)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1719 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1719 = nothing
                end
                deconstruct_result937 = _t1719
                if !isnothing(deconstruct_result937)
                    unwrapped938 = deconstruct_result937
                    pretty_context(pp, unwrapped938)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1720 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1720 = nothing
                    end
                    deconstruct_result935 = _t1720
                    if !isnothing(deconstruct_result935)
                        unwrapped936 = deconstruct_result935
                        pretty_snapshot(pp, unwrapped936)
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
    flat946 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        _dollar_dollar = msg
        fields944 = _dollar_dollar.fragment
        unwrapped_fields945 = fields944
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields945)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat953 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat953)
        write(pp, flat953)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields947 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields948 = fields947
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field949 = unwrapped_fields948[1]
        pretty_new_fragment_id(pp, field949)
        field950 = unwrapped_fields948[2]
        if !isempty(field950)
            newline(pp)
            for (i1721, elem951) in enumerate(field950)
                i952 = i1721 - 1
                if (i952 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem951)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat955 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat955)
        write(pp, flat955)
        return nothing
    else
        fields954 = msg
        pretty_fragment_id(pp, fields954)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat964 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat964)
        write(pp, flat964)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1722 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1722 = nothing
        end
        deconstruct_result962 = _t1722
        if !isnothing(deconstruct_result962)
            unwrapped963 = deconstruct_result962
            pretty_def(pp, unwrapped963)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1723 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1723 = nothing
            end
            deconstruct_result960 = _t1723
            if !isnothing(deconstruct_result960)
                unwrapped961 = deconstruct_result960
                pretty_algorithm(pp, unwrapped961)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1724 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1724 = nothing
                end
                deconstruct_result958 = _t1724
                if !isnothing(deconstruct_result958)
                    unwrapped959 = deconstruct_result958
                    pretty_constraint(pp, unwrapped959)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1725 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1725 = nothing
                    end
                    deconstruct_result956 = _t1725
                    if !isnothing(deconstruct_result956)
                        unwrapped957 = deconstruct_result956
                        pretty_data(pp, unwrapped957)
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
    flat971 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat971)
        write(pp, flat971)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1726 = _dollar_dollar.attrs
        else
            _t1726 = nothing
        end
        fields965 = (_dollar_dollar.name, _dollar_dollar.body, _t1726,)
        unwrapped_fields966 = fields965
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field967 = unwrapped_fields966[1]
        pretty_relation_id(pp, field967)
        newline(pp)
        field968 = unwrapped_fields966[2]
        pretty_abstraction(pp, field968)
        field969 = unwrapped_fields966[3]
        if !isnothing(field969)
            newline(pp)
            opt_val970 = field969
            pretty_attrs(pp, opt_val970)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat976 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat976)
        write(pp, flat976)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1728 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1727 = _t1728
        else
            _t1727 = nothing
        end
        deconstruct_result974 = _t1727
        if !isnothing(deconstruct_result974)
            unwrapped975 = deconstruct_result974
            write(pp, ":")
            write(pp, unwrapped975)
        else
            _dollar_dollar = msg
            _t1729 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result972 = _t1729
            if !isnothing(deconstruct_result972)
                unwrapped973 = deconstruct_result972
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped973))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat981 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat981)
        write(pp, flat981)
        return nothing
    else
        _dollar_dollar = msg
        _t1730 = deconstruct_bindings(pp, _dollar_dollar)
        fields977 = (_t1730, _dollar_dollar.value,)
        unwrapped_fields978 = fields977
        write(pp, "(")
        indent!(pp)
        field979 = unwrapped_fields978[1]
        pretty_bindings(pp, field979)
        newline(pp)
        field980 = unwrapped_fields978[2]
        pretty_formula(pp, field980)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat989 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat989)
        write(pp, flat989)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1731 = _dollar_dollar[2]
        else
            _t1731 = nothing
        end
        fields982 = (_dollar_dollar[1], _t1731,)
        unwrapped_fields983 = fields982
        write(pp, "[")
        indent!(pp)
        field984 = unwrapped_fields983[1]
        for (i1732, elem985) in enumerate(field984)
            i986 = i1732 - 1
            if (i986 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem985)
        end
        field987 = unwrapped_fields983[2]
        if !isnothing(field987)
            newline(pp)
            opt_val988 = field987
            pretty_value_bindings(pp, opt_val988)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat994 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat994)
        write(pp, flat994)
        return nothing
    else
        _dollar_dollar = msg
        fields990 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields991 = fields990
        field992 = unwrapped_fields991[1]
        write(pp, field992)
        write(pp, "::")
        field993 = unwrapped_fields991[2]
        pretty_type(pp, field993)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat1023 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat1023)
        write(pp, flat1023)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1733 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1733 = nothing
        end
        deconstruct_result1021 = _t1733
        if !isnothing(deconstruct_result1021)
            unwrapped1022 = deconstruct_result1021
            pretty_unspecified_type(pp, unwrapped1022)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1734 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1734 = nothing
            end
            deconstruct_result1019 = _t1734
            if !isnothing(deconstruct_result1019)
                unwrapped1020 = deconstruct_result1019
                pretty_string_type(pp, unwrapped1020)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1735 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1735 = nothing
                end
                deconstruct_result1017 = _t1735
                if !isnothing(deconstruct_result1017)
                    unwrapped1018 = deconstruct_result1017
                    pretty_int_type(pp, unwrapped1018)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1736 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1736 = nothing
                    end
                    deconstruct_result1015 = _t1736
                    if !isnothing(deconstruct_result1015)
                        unwrapped1016 = deconstruct_result1015
                        pretty_float_type(pp, unwrapped1016)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1737 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1737 = nothing
                        end
                        deconstruct_result1013 = _t1737
                        if !isnothing(deconstruct_result1013)
                            unwrapped1014 = deconstruct_result1013
                            pretty_uint128_type(pp, unwrapped1014)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1738 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1738 = nothing
                            end
                            deconstruct_result1011 = _t1738
                            if !isnothing(deconstruct_result1011)
                                unwrapped1012 = deconstruct_result1011
                                pretty_int128_type(pp, unwrapped1012)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1739 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1739 = nothing
                                end
                                deconstruct_result1009 = _t1739
                                if !isnothing(deconstruct_result1009)
                                    unwrapped1010 = deconstruct_result1009
                                    pretty_date_type(pp, unwrapped1010)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1740 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1740 = nothing
                                    end
                                    deconstruct_result1007 = _t1740
                                    if !isnothing(deconstruct_result1007)
                                        unwrapped1008 = deconstruct_result1007
                                        pretty_datetime_type(pp, unwrapped1008)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1741 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1741 = nothing
                                        end
                                        deconstruct_result1005 = _t1741
                                        if !isnothing(deconstruct_result1005)
                                            unwrapped1006 = deconstruct_result1005
                                            pretty_missing_type(pp, unwrapped1006)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1742 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1742 = nothing
                                            end
                                            deconstruct_result1003 = _t1742
                                            if !isnothing(deconstruct_result1003)
                                                unwrapped1004 = deconstruct_result1003
                                                pretty_decimal_type(pp, unwrapped1004)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1743 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1743 = nothing
                                                end
                                                deconstruct_result1001 = _t1743
                                                if !isnothing(deconstruct_result1001)
                                                    unwrapped1002 = deconstruct_result1001
                                                    pretty_boolean_type(pp, unwrapped1002)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1744 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1744 = nothing
                                                    end
                                                    deconstruct_result999 = _t1744
                                                    if !isnothing(deconstruct_result999)
                                                        unwrapped1000 = deconstruct_result999
                                                        pretty_int32_type(pp, unwrapped1000)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1745 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1745 = nothing
                                                        end
                                                        deconstruct_result997 = _t1745
                                                        if !isnothing(deconstruct_result997)
                                                            unwrapped998 = deconstruct_result997
                                                            pretty_float32_type(pp, unwrapped998)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1746 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1746 = nothing
                                                            end
                                                            deconstruct_result995 = _t1746
                                                            if !isnothing(deconstruct_result995)
                                                                unwrapped996 = deconstruct_result995
                                                                pretty_uint32_type(pp, unwrapped996)
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
    fields1024 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields1025 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields1026 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields1027 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields1028 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields1029 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields1030 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields1031 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields1032 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat1037 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat1037)
        write(pp, flat1037)
        return nothing
    else
        _dollar_dollar = msg
        fields1033 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields1034 = fields1033
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field1035 = unwrapped_fields1034[1]
        write(pp, string(field1035))
        newline(pp)
        field1036 = unwrapped_fields1034[2]
        write(pp, string(field1036))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields1038 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields1039 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields1040 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields1041 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1045 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1045)
        write(pp, flat1045)
        return nothing
    else
        fields1042 = msg
        write(pp, "|")
        if !isempty(fields1042)
            write(pp, " ")
            for (i1747, elem1043) in enumerate(fields1042)
                i1044 = i1747 - 1
                if (i1044 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1043)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1072 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1072)
        write(pp, flat1072)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1748 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1748 = nothing
        end
        deconstruct_result1070 = _t1748
        if !isnothing(deconstruct_result1070)
            unwrapped1071 = deconstruct_result1070
            pretty_true(pp, unwrapped1071)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1749 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1749 = nothing
            end
            deconstruct_result1068 = _t1749
            if !isnothing(deconstruct_result1068)
                unwrapped1069 = deconstruct_result1068
                pretty_false(pp, unwrapped1069)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1750 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1750 = nothing
                end
                deconstruct_result1066 = _t1750
                if !isnothing(deconstruct_result1066)
                    unwrapped1067 = deconstruct_result1066
                    pretty_exists(pp, unwrapped1067)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1751 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1751 = nothing
                    end
                    deconstruct_result1064 = _t1751
                    if !isnothing(deconstruct_result1064)
                        unwrapped1065 = deconstruct_result1064
                        pretty_reduce(pp, unwrapped1065)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1752 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1752 = nothing
                        end
                        deconstruct_result1062 = _t1752
                        if !isnothing(deconstruct_result1062)
                            unwrapped1063 = deconstruct_result1062
                            pretty_conjunction(pp, unwrapped1063)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1753 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1753 = nothing
                            end
                            deconstruct_result1060 = _t1753
                            if !isnothing(deconstruct_result1060)
                                unwrapped1061 = deconstruct_result1060
                                pretty_disjunction(pp, unwrapped1061)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1754 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1754 = nothing
                                end
                                deconstruct_result1058 = _t1754
                                if !isnothing(deconstruct_result1058)
                                    unwrapped1059 = deconstruct_result1058
                                    pretty_not(pp, unwrapped1059)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1755 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1755 = nothing
                                    end
                                    deconstruct_result1056 = _t1755
                                    if !isnothing(deconstruct_result1056)
                                        unwrapped1057 = deconstruct_result1056
                                        pretty_ffi(pp, unwrapped1057)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1756 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1756 = nothing
                                        end
                                        deconstruct_result1054 = _t1756
                                        if !isnothing(deconstruct_result1054)
                                            unwrapped1055 = deconstruct_result1054
                                            pretty_atom(pp, unwrapped1055)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1757 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1757 = nothing
                                            end
                                            deconstruct_result1052 = _t1757
                                            if !isnothing(deconstruct_result1052)
                                                unwrapped1053 = deconstruct_result1052
                                                pretty_pragma(pp, unwrapped1053)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1758 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1758 = nothing
                                                end
                                                deconstruct_result1050 = _t1758
                                                if !isnothing(deconstruct_result1050)
                                                    unwrapped1051 = deconstruct_result1050
                                                    pretty_primitive(pp, unwrapped1051)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1759 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1759 = nothing
                                                    end
                                                    deconstruct_result1048 = _t1759
                                                    if !isnothing(deconstruct_result1048)
                                                        unwrapped1049 = deconstruct_result1048
                                                        pretty_rel_atom(pp, unwrapped1049)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1760 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1760 = nothing
                                                        end
                                                        deconstruct_result1046 = _t1760
                                                        if !isnothing(deconstruct_result1046)
                                                            unwrapped1047 = deconstruct_result1046
                                                            pretty_cast(pp, unwrapped1047)
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
    fields1073 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1074 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1079 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1079)
        write(pp, flat1079)
        return nothing
    else
        _dollar_dollar = msg
        _t1761 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1075 = (_t1761, _dollar_dollar.body.value,)
        unwrapped_fields1076 = fields1075
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1077 = unwrapped_fields1076[1]
        pretty_bindings(pp, field1077)
        newline(pp)
        field1078 = unwrapped_fields1076[2]
        pretty_formula(pp, field1078)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1085 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1085)
        write(pp, flat1085)
        return nothing
    else
        _dollar_dollar = msg
        fields1080 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1081 = fields1080
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1082 = unwrapped_fields1081[1]
        pretty_abstraction(pp, field1082)
        newline(pp)
        field1083 = unwrapped_fields1081[2]
        pretty_abstraction(pp, field1083)
        newline(pp)
        field1084 = unwrapped_fields1081[3]
        pretty_terms(pp, field1084)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1089 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1089)
        write(pp, flat1089)
        return nothing
    else
        fields1086 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1086)
            newline(pp)
            for (i1762, elem1087) in enumerate(fields1086)
                i1088 = i1762 - 1
                if (i1088 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1087)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1094 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1094)
        write(pp, flat1094)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1763 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1763 = nothing
        end
        deconstruct_result1092 = _t1763
        if !isnothing(deconstruct_result1092)
            unwrapped1093 = deconstruct_result1092
            pretty_var(pp, unwrapped1093)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1764 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1764 = nothing
            end
            deconstruct_result1090 = _t1764
            if !isnothing(deconstruct_result1090)
                unwrapped1091 = deconstruct_result1090
                pretty_value(pp, unwrapped1091)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1097 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1097)
        write(pp, flat1097)
        return nothing
    else
        _dollar_dollar = msg
        fields1095 = _dollar_dollar.name
        unwrapped_fields1096 = fields1095
        write(pp, unwrapped_fields1096)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1123 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1123)
        write(pp, flat1123)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1765 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1765 = nothing
        end
        deconstruct_result1121 = _t1765
        if !isnothing(deconstruct_result1121)
            unwrapped1122 = deconstruct_result1121
            pretty_date(pp, unwrapped1122)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1766 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1766 = nothing
            end
            deconstruct_result1119 = _t1766
            if !isnothing(deconstruct_result1119)
                unwrapped1120 = deconstruct_result1119
                pretty_datetime(pp, unwrapped1120)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1767 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1767 = nothing
                end
                deconstruct_result1117 = _t1767
                if !isnothing(deconstruct_result1117)
                    unwrapped1118 = deconstruct_result1117
                    write(pp, format_string(pp, unwrapped1118))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1768 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1768 = nothing
                    end
                    deconstruct_result1115 = _t1768
                    if !isnothing(deconstruct_result1115)
                        unwrapped1116 = deconstruct_result1115
                        write(pp, format_int32(pp, unwrapped1116))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1769 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1769 = nothing
                        end
                        deconstruct_result1113 = _t1769
                        if !isnothing(deconstruct_result1113)
                            unwrapped1114 = deconstruct_result1113
                            write(pp, format_int(pp, unwrapped1114))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1770 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1770 = nothing
                            end
                            deconstruct_result1111 = _t1770
                            if !isnothing(deconstruct_result1111)
                                unwrapped1112 = deconstruct_result1111
                                write(pp, format_float32(pp, unwrapped1112))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1771 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1771 = nothing
                                end
                                deconstruct_result1109 = _t1771
                                if !isnothing(deconstruct_result1109)
                                    unwrapped1110 = deconstruct_result1109
                                    write(pp, format_float(pp, unwrapped1110))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1772 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1772 = nothing
                                    end
                                    deconstruct_result1107 = _t1772
                                    if !isnothing(deconstruct_result1107)
                                        unwrapped1108 = deconstruct_result1107
                                        write(pp, format_uint32(pp, unwrapped1108))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1773 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1773 = nothing
                                        end
                                        deconstruct_result1105 = _t1773
                                        if !isnothing(deconstruct_result1105)
                                            unwrapped1106 = deconstruct_result1105
                                            write(pp, format_uint128(pp, unwrapped1106))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1774 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1774 = nothing
                                            end
                                            deconstruct_result1103 = _t1774
                                            if !isnothing(deconstruct_result1103)
                                                unwrapped1104 = deconstruct_result1103
                                                write(pp, format_int128(pp, unwrapped1104))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1775 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1775 = nothing
                                                end
                                                deconstruct_result1101 = _t1775
                                                if !isnothing(deconstruct_result1101)
                                                    unwrapped1102 = deconstruct_result1101
                                                    write(pp, format_decimal(pp, unwrapped1102))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1776 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1776 = nothing
                                                    end
                                                    deconstruct_result1099 = _t1776
                                                    if !isnothing(deconstruct_result1099)
                                                        unwrapped1100 = deconstruct_result1099
                                                        pretty_boolean_value(pp, unwrapped1100)
                                                    else
                                                        fields1098 = msg
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
    flat1129 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1129)
        write(pp, flat1129)
        return nothing
    else
        _dollar_dollar = msg
        fields1124 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1125 = fields1124
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1126 = unwrapped_fields1125[1]
        write(pp, format_int(pp, field1126))
        newline(pp)
        field1127 = unwrapped_fields1125[2]
        write(pp, format_int(pp, field1127))
        newline(pp)
        field1128 = unwrapped_fields1125[3]
        write(pp, format_int(pp, field1128))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1140 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1140)
        write(pp, flat1140)
        return nothing
    else
        _dollar_dollar = msg
        fields1130 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1131 = fields1130
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1132 = unwrapped_fields1131[1]
        write(pp, format_int(pp, field1132))
        newline(pp)
        field1133 = unwrapped_fields1131[2]
        write(pp, format_int(pp, field1133))
        newline(pp)
        field1134 = unwrapped_fields1131[3]
        write(pp, format_int(pp, field1134))
        newline(pp)
        field1135 = unwrapped_fields1131[4]
        write(pp, format_int(pp, field1135))
        newline(pp)
        field1136 = unwrapped_fields1131[5]
        write(pp, format_int(pp, field1136))
        newline(pp)
        field1137 = unwrapped_fields1131[6]
        write(pp, format_int(pp, field1137))
        field1138 = unwrapped_fields1131[7]
        if !isnothing(field1138)
            newline(pp)
            opt_val1139 = field1138
            write(pp, format_int(pp, opt_val1139))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1145 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1145)
        write(pp, flat1145)
        return nothing
    else
        _dollar_dollar = msg
        fields1141 = _dollar_dollar.args
        unwrapped_fields1142 = fields1141
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1142)
            newline(pp)
            for (i1777, elem1143) in enumerate(unwrapped_fields1142)
                i1144 = i1777 - 1
                if (i1144 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1143)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1150 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1150)
        write(pp, flat1150)
        return nothing
    else
        _dollar_dollar = msg
        fields1146 = _dollar_dollar.args
        unwrapped_fields1147 = fields1146
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1147)
            newline(pp)
            for (i1778, elem1148) in enumerate(unwrapped_fields1147)
                i1149 = i1778 - 1
                if (i1149 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1148)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1153 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1153)
        write(pp, flat1153)
        return nothing
    else
        _dollar_dollar = msg
        fields1151 = _dollar_dollar.arg
        unwrapped_fields1152 = fields1151
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1152)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1159 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1159)
        write(pp, flat1159)
        return nothing
    else
        _dollar_dollar = msg
        fields1154 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1155 = fields1154
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1156 = unwrapped_fields1155[1]
        pretty_name(pp, field1156)
        newline(pp)
        field1157 = unwrapped_fields1155[2]
        pretty_ffi_args(pp, field1157)
        newline(pp)
        field1158 = unwrapped_fields1155[3]
        pretty_terms(pp, field1158)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1161 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1161)
        write(pp, flat1161)
        return nothing
    else
        fields1160 = msg
        write(pp, ":")
        write(pp, fields1160)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1165 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1165)
        write(pp, flat1165)
        return nothing
    else
        fields1162 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1162)
            newline(pp)
            for (i1779, elem1163) in enumerate(fields1162)
                i1164 = i1779 - 1
                if (i1164 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1163)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1172 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1172)
        write(pp, flat1172)
        return nothing
    else
        _dollar_dollar = msg
        fields1166 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1167 = fields1166
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1168 = unwrapped_fields1167[1]
        pretty_relation_id(pp, field1168)
        field1169 = unwrapped_fields1167[2]
        if !isempty(field1169)
            newline(pp)
            for (i1780, elem1170) in enumerate(field1169)
                i1171 = i1780 - 1
                if (i1171 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1170)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1179 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        _dollar_dollar = msg
        fields1173 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1174 = fields1173
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1175 = unwrapped_fields1174[1]
        pretty_name(pp, field1175)
        field1176 = unwrapped_fields1174[2]
        if !isempty(field1176)
            newline(pp)
            for (i1781, elem1177) in enumerate(field1176)
                i1178 = i1781 - 1
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

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1195 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1195)
        write(pp, flat1195)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1782 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1782 = nothing
        end
        guard_result1194 = _t1782
        if !isnothing(guard_result1194)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1783 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1783 = nothing
            end
            guard_result1193 = _t1783
            if !isnothing(guard_result1193)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1784 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1784 = nothing
                end
                guard_result1192 = _t1784
                if !isnothing(guard_result1192)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1785 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1785 = nothing
                    end
                    guard_result1191 = _t1785
                    if !isnothing(guard_result1191)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1786 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1786 = nothing
                        end
                        guard_result1190 = _t1786
                        if !isnothing(guard_result1190)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1787 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1787 = nothing
                            end
                            guard_result1189 = _t1787
                            if !isnothing(guard_result1189)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1788 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1788 = nothing
                                end
                                guard_result1188 = _t1788
                                if !isnothing(guard_result1188)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1789 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1789 = nothing
                                    end
                                    guard_result1187 = _t1789
                                    if !isnothing(guard_result1187)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1790 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1790 = nothing
                                        end
                                        guard_result1186 = _t1790
                                        if !isnothing(guard_result1186)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1180 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1181 = fields1180
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1182 = unwrapped_fields1181[1]
                                            pretty_name(pp, field1182)
                                            field1183 = unwrapped_fields1181[2]
                                            if !isempty(field1183)
                                                newline(pp)
                                                for (i1791, elem1184) in enumerate(field1183)
                                                    i1185 = i1791 - 1
                                                    if (i1185 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1184)
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
    flat1200 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1200)
        write(pp, flat1200)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1792 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1792 = nothing
        end
        fields1196 = _t1792
        unwrapped_fields1197 = fields1196
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1198 = unwrapped_fields1197[1]
        pretty_term(pp, field1198)
        newline(pp)
        field1199 = unwrapped_fields1197[2]
        pretty_term(pp, field1199)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1205 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1205)
        write(pp, flat1205)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1793 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1793 = nothing
        end
        fields1201 = _t1793
        unwrapped_fields1202 = fields1201
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1203 = unwrapped_fields1202[1]
        pretty_term(pp, field1203)
        newline(pp)
        field1204 = unwrapped_fields1202[2]
        pretty_term(pp, field1204)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1210 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1210)
        write(pp, flat1210)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1794 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1794 = nothing
        end
        fields1206 = _t1794
        unwrapped_fields1207 = fields1206
        write(pp, "(<=")
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

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1215 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1795 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1795 = nothing
        end
        fields1211 = _t1795
        unwrapped_fields1212 = fields1211
        write(pp, "(>")
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

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1220 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1796 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1796 = nothing
        end
        fields1216 = _t1796
        unwrapped_fields1217 = fields1216
        write(pp, "(>=")
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

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1226 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1226)
        write(pp, flat1226)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1797 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1797 = nothing
        end
        fields1221 = _t1797
        unwrapped_fields1222 = fields1221
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1223 = unwrapped_fields1222[1]
        pretty_term(pp, field1223)
        newline(pp)
        field1224 = unwrapped_fields1222[2]
        pretty_term(pp, field1224)
        newline(pp)
        field1225 = unwrapped_fields1222[3]
        pretty_term(pp, field1225)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1232 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1232)
        write(pp, flat1232)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1798 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1798 = nothing
        end
        fields1227 = _t1798
        unwrapped_fields1228 = fields1227
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1229 = unwrapped_fields1228[1]
        pretty_term(pp, field1229)
        newline(pp)
        field1230 = unwrapped_fields1228[2]
        pretty_term(pp, field1230)
        newline(pp)
        field1231 = unwrapped_fields1228[3]
        pretty_term(pp, field1231)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1238 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1238)
        write(pp, flat1238)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1799 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1799 = nothing
        end
        fields1233 = _t1799
        unwrapped_fields1234 = fields1233
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1235 = unwrapped_fields1234[1]
        pretty_term(pp, field1235)
        newline(pp)
        field1236 = unwrapped_fields1234[2]
        pretty_term(pp, field1236)
        newline(pp)
        field1237 = unwrapped_fields1234[3]
        pretty_term(pp, field1237)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1244 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1244)
        write(pp, flat1244)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1800 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1800 = nothing
        end
        fields1239 = _t1800
        unwrapped_fields1240 = fields1239
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1241 = unwrapped_fields1240[1]
        pretty_term(pp, field1241)
        newline(pp)
        field1242 = unwrapped_fields1240[2]
        pretty_term(pp, field1242)
        newline(pp)
        field1243 = unwrapped_fields1240[3]
        pretty_term(pp, field1243)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1249 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1249)
        write(pp, flat1249)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1801 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1801 = nothing
        end
        deconstruct_result1247 = _t1801
        if !isnothing(deconstruct_result1247)
            unwrapped1248 = deconstruct_result1247
            pretty_specialized_value(pp, unwrapped1248)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1802 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1802 = nothing
            end
            deconstruct_result1245 = _t1802
            if !isnothing(deconstruct_result1245)
                unwrapped1246 = deconstruct_result1245
                pretty_term(pp, unwrapped1246)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1251 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1251)
        write(pp, flat1251)
        return nothing
    else
        fields1250 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1250)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1258 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1258)
        write(pp, flat1258)
        return nothing
    else
        _dollar_dollar = msg
        fields1252 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1253 = fields1252
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1254 = unwrapped_fields1253[1]
        pretty_name(pp, field1254)
        field1255 = unwrapped_fields1253[2]
        if !isempty(field1255)
            newline(pp)
            for (i1803, elem1256) in enumerate(field1255)
                i1257 = i1803 - 1
                if (i1257 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1256)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1263 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1263)
        write(pp, flat1263)
        return nothing
    else
        _dollar_dollar = msg
        fields1259 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1260 = fields1259
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1261 = unwrapped_fields1260[1]
        pretty_term(pp, field1261)
        newline(pp)
        field1262 = unwrapped_fields1260[2]
        pretty_term(pp, field1262)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1267 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1267)
        write(pp, flat1267)
        return nothing
    else
        fields1264 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1264)
            newline(pp)
            for (i1804, elem1265) in enumerate(fields1264)
                i1266 = i1804 - 1
                if (i1266 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1265)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1274 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1274)
        write(pp, flat1274)
        return nothing
    else
        _dollar_dollar = msg
        fields1268 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1269 = fields1268
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1270 = unwrapped_fields1269[1]
        pretty_name(pp, field1270)
        field1271 = unwrapped_fields1269[2]
        if !isempty(field1271)
            newline(pp)
            for (i1805, elem1272) in enumerate(field1271)
                i1273 = i1805 - 1
                if (i1273 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1272)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1283 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1283)
        write(pp, flat1283)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1806 = _dollar_dollar.attrs
        else
            _t1806 = nothing
        end
        fields1275 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1806,)
        unwrapped_fields1276 = fields1275
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1277 = unwrapped_fields1276[1]
        if !isempty(field1277)
            newline(pp)
            for (i1807, elem1278) in enumerate(field1277)
                i1279 = i1807 - 1
                if (i1279 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1278)
            end
        end
        newline(pp)
        field1280 = unwrapped_fields1276[2]
        pretty_script(pp, field1280)
        field1281 = unwrapped_fields1276[3]
        if !isnothing(field1281)
            newline(pp)
            opt_val1282 = field1281
            pretty_attrs(pp, opt_val1282)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1288 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1288)
        write(pp, flat1288)
        return nothing
    else
        _dollar_dollar = msg
        fields1284 = _dollar_dollar.constructs
        unwrapped_fields1285 = fields1284
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1285)
            newline(pp)
            for (i1808, elem1286) in enumerate(unwrapped_fields1285)
                i1287 = i1808 - 1
                if (i1287 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1286)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1293 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1293)
        write(pp, flat1293)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1809 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1809 = nothing
        end
        deconstruct_result1291 = _t1809
        if !isnothing(deconstruct_result1291)
            unwrapped1292 = deconstruct_result1291
            pretty_loop(pp, unwrapped1292)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1810 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1810 = nothing
            end
            deconstruct_result1289 = _t1810
            if !isnothing(deconstruct_result1289)
                unwrapped1290 = deconstruct_result1289
                pretty_instruction(pp, unwrapped1290)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1300 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1300)
        write(pp, flat1300)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1811 = _dollar_dollar.attrs
        else
            _t1811 = nothing
        end
        fields1294 = (_dollar_dollar.init, _dollar_dollar.body, _t1811,)
        unwrapped_fields1295 = fields1294
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1296 = unwrapped_fields1295[1]
        pretty_init(pp, field1296)
        newline(pp)
        field1297 = unwrapped_fields1295[2]
        pretty_script(pp, field1297)
        field1298 = unwrapped_fields1295[3]
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

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1304 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1304)
        write(pp, flat1304)
        return nothing
    else
        fields1301 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1301)
            newline(pp)
            for (i1812, elem1302) in enumerate(fields1301)
                i1303 = i1812 - 1
                if (i1303 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1302)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1315 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1315)
        write(pp, flat1315)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1813 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1813 = nothing
        end
        deconstruct_result1313 = _t1813
        if !isnothing(deconstruct_result1313)
            unwrapped1314 = deconstruct_result1313
            pretty_assign(pp, unwrapped1314)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1814 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1814 = nothing
            end
            deconstruct_result1311 = _t1814
            if !isnothing(deconstruct_result1311)
                unwrapped1312 = deconstruct_result1311
                pretty_upsert(pp, unwrapped1312)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1815 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1815 = nothing
                end
                deconstruct_result1309 = _t1815
                if !isnothing(deconstruct_result1309)
                    unwrapped1310 = deconstruct_result1309
                    pretty_break(pp, unwrapped1310)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1816 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1816 = nothing
                    end
                    deconstruct_result1307 = _t1816
                    if !isnothing(deconstruct_result1307)
                        unwrapped1308 = deconstruct_result1307
                        pretty_monoid_def(pp, unwrapped1308)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1817 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1817 = nothing
                        end
                        deconstruct_result1305 = _t1817
                        if !isnothing(deconstruct_result1305)
                            unwrapped1306 = deconstruct_result1305
                            pretty_monus_def(pp, unwrapped1306)
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
    flat1322 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1322)
        write(pp, flat1322)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1818 = _dollar_dollar.attrs
        else
            _t1818 = nothing
        end
        fields1316 = (_dollar_dollar.name, _dollar_dollar.body, _t1818,)
        unwrapped_fields1317 = fields1316
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1318 = unwrapped_fields1317[1]
        pretty_relation_id(pp, field1318)
        newline(pp)
        field1319 = unwrapped_fields1317[2]
        pretty_abstraction(pp, field1319)
        field1320 = unwrapped_fields1317[3]
        if !isnothing(field1320)
            newline(pp)
            opt_val1321 = field1320
            pretty_attrs(pp, opt_val1321)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1329 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1329)
        write(pp, flat1329)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1819 = _dollar_dollar.attrs
        else
            _t1819 = nothing
        end
        fields1323 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1819,)
        unwrapped_fields1324 = fields1323
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1325 = unwrapped_fields1324[1]
        pretty_relation_id(pp, field1325)
        newline(pp)
        field1326 = unwrapped_fields1324[2]
        pretty_abstraction_with_arity(pp, field1326)
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

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1334 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1334)
        write(pp, flat1334)
        return nothing
    else
        _dollar_dollar = msg
        _t1820 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1330 = (_t1820, _dollar_dollar[1].value,)
        unwrapped_fields1331 = fields1330
        write(pp, "(")
        indent!(pp)
        field1332 = unwrapped_fields1331[1]
        pretty_bindings(pp, field1332)
        newline(pp)
        field1333 = unwrapped_fields1331[2]
        pretty_formula(pp, field1333)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1341 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1341)
        write(pp, flat1341)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1821 = _dollar_dollar.attrs
        else
            _t1821 = nothing
        end
        fields1335 = (_dollar_dollar.name, _dollar_dollar.body, _t1821,)
        unwrapped_fields1336 = fields1335
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1337 = unwrapped_fields1336[1]
        pretty_relation_id(pp, field1337)
        newline(pp)
        field1338 = unwrapped_fields1336[2]
        pretty_abstraction(pp, field1338)
        field1339 = unwrapped_fields1336[3]
        if !isnothing(field1339)
            newline(pp)
            opt_val1340 = field1339
            pretty_attrs(pp, opt_val1340)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1349 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1349)
        write(pp, flat1349)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1822 = _dollar_dollar.attrs
        else
            _t1822 = nothing
        end
        fields1342 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1822,)
        unwrapped_fields1343 = fields1342
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1344 = unwrapped_fields1343[1]
        pretty_monoid(pp, field1344)
        newline(pp)
        field1345 = unwrapped_fields1343[2]
        pretty_relation_id(pp, field1345)
        newline(pp)
        field1346 = unwrapped_fields1343[3]
        pretty_abstraction_with_arity(pp, field1346)
        field1347 = unwrapped_fields1343[4]
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

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1358 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1358)
        write(pp, flat1358)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1823 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1823 = nothing
        end
        deconstruct_result1356 = _t1823
        if !isnothing(deconstruct_result1356)
            unwrapped1357 = deconstruct_result1356
            pretty_or_monoid(pp, unwrapped1357)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1824 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1824 = nothing
            end
            deconstruct_result1354 = _t1824
            if !isnothing(deconstruct_result1354)
                unwrapped1355 = deconstruct_result1354
                pretty_min_monoid(pp, unwrapped1355)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1825 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1825 = nothing
                end
                deconstruct_result1352 = _t1825
                if !isnothing(deconstruct_result1352)
                    unwrapped1353 = deconstruct_result1352
                    pretty_max_monoid(pp, unwrapped1353)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1826 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1826 = nothing
                    end
                    deconstruct_result1350 = _t1826
                    if !isnothing(deconstruct_result1350)
                        unwrapped1351 = deconstruct_result1350
                        pretty_sum_monoid(pp, unwrapped1351)
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
    fields1359 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1362 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1362)
        write(pp, flat1362)
        return nothing
    else
        _dollar_dollar = msg
        fields1360 = _dollar_dollar.var"#type"
        unwrapped_fields1361 = fields1360
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1361)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1365 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1365)
        write(pp, flat1365)
        return nothing
    else
        _dollar_dollar = msg
        fields1363 = _dollar_dollar.var"#type"
        unwrapped_fields1364 = fields1363
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1364)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1368 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1368)
        write(pp, flat1368)
        return nothing
    else
        _dollar_dollar = msg
        fields1366 = _dollar_dollar.var"#type"
        unwrapped_fields1367 = fields1366
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1367)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1376 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1827 = _dollar_dollar.attrs
        else
            _t1827 = nothing
        end
        fields1369 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1827,)
        unwrapped_fields1370 = fields1369
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1371 = unwrapped_fields1370[1]
        pretty_monoid(pp, field1371)
        newline(pp)
        field1372 = unwrapped_fields1370[2]
        pretty_relation_id(pp, field1372)
        newline(pp)
        field1373 = unwrapped_fields1370[3]
        pretty_abstraction_with_arity(pp, field1373)
        field1374 = unwrapped_fields1370[4]
        if !isnothing(field1374)
            newline(pp)
            opt_val1375 = field1374
            pretty_attrs(pp, opt_val1375)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1383 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1383)
        write(pp, flat1383)
        return nothing
    else
        _dollar_dollar = msg
        fields1377 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1378 = fields1377
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1379 = unwrapped_fields1378[1]
        pretty_relation_id(pp, field1379)
        newline(pp)
        field1380 = unwrapped_fields1378[2]
        pretty_abstraction(pp, field1380)
        newline(pp)
        field1381 = unwrapped_fields1378[3]
        pretty_functional_dependency_keys(pp, field1381)
        newline(pp)
        field1382 = unwrapped_fields1378[4]
        pretty_functional_dependency_values(pp, field1382)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1387 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1387)
        write(pp, flat1387)
        return nothing
    else
        fields1384 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1384)
            newline(pp)
            for (i1828, elem1385) in enumerate(fields1384)
                i1386 = i1828 - 1
                if (i1386 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1385)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1391 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1391)
        write(pp, flat1391)
        return nothing
    else
        fields1388 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1388)
            newline(pp)
            for (i1829, elem1389) in enumerate(fields1388)
                i1390 = i1829 - 1
                if (i1390 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1389)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1400 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1400)
        write(pp, flat1400)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1830 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1830 = nothing
        end
        deconstruct_result1398 = _t1830
        if !isnothing(deconstruct_result1398)
            unwrapped1399 = deconstruct_result1398
            pretty_edb(pp, unwrapped1399)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1831 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1831 = nothing
            end
            deconstruct_result1396 = _t1831
            if !isnothing(deconstruct_result1396)
                unwrapped1397 = deconstruct_result1396
                pretty_betree_relation(pp, unwrapped1397)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1832 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1832 = nothing
                end
                deconstruct_result1394 = _t1832
                if !isnothing(deconstruct_result1394)
                    unwrapped1395 = deconstruct_result1394
                    pretty_csv_data(pp, unwrapped1395)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1833 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1833 = nothing
                    end
                    deconstruct_result1392 = _t1833
                    if !isnothing(deconstruct_result1392)
                        unwrapped1393 = deconstruct_result1392
                        pretty_iceberg_data(pp, unwrapped1393)
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
    flat1406 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1406)
        write(pp, flat1406)
        return nothing
    else
        _dollar_dollar = msg
        fields1401 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1402 = fields1401
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1403 = unwrapped_fields1402[1]
        pretty_relation_id(pp, field1403)
        newline(pp)
        field1404 = unwrapped_fields1402[2]
        pretty_edb_path(pp, field1404)
        newline(pp)
        field1405 = unwrapped_fields1402[3]
        pretty_edb_types(pp, field1405)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1410 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1410)
        write(pp, flat1410)
        return nothing
    else
        fields1407 = msg
        write(pp, "[")
        indent!(pp)
        for (i1834, elem1408) in enumerate(fields1407)
            i1409 = i1834 - 1
            if (i1409 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1408))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1414 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1414)
        write(pp, flat1414)
        return nothing
    else
        fields1411 = msg
        write(pp, "[")
        indent!(pp)
        for (i1835, elem1412) in enumerate(fields1411)
            i1413 = i1835 - 1
            if (i1413 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1412)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1419 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1419)
        write(pp, flat1419)
        return nothing
    else
        _dollar_dollar = msg
        fields1415 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1416 = fields1415
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1417 = unwrapped_fields1416[1]
        pretty_relation_id(pp, field1417)
        newline(pp)
        field1418 = unwrapped_fields1416[2]
        pretty_betree_info(pp, field1418)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1425 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1425)
        write(pp, flat1425)
        return nothing
    else
        _dollar_dollar = msg
        _t1836 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1420 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1836,)
        unwrapped_fields1421 = fields1420
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1422 = unwrapped_fields1421[1]
        pretty_betree_info_key_types(pp, field1422)
        newline(pp)
        field1423 = unwrapped_fields1421[2]
        pretty_betree_info_value_types(pp, field1423)
        newline(pp)
        field1424 = unwrapped_fields1421[3]
        pretty_config_dict(pp, field1424)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1429 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1429)
        write(pp, flat1429)
        return nothing
    else
        fields1426 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1426)
            newline(pp)
            for (i1837, elem1427) in enumerate(fields1426)
                i1428 = i1837 - 1
                if (i1428 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1427)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1433 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1433)
        write(pp, flat1433)
        return nothing
    else
        fields1430 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1430)
            newline(pp)
            for (i1838, elem1431) in enumerate(fields1430)
                i1432 = i1838 - 1
                if (i1432 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1431)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1443 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1443)
        write(pp, flat1443)
        return nothing
    else
        _dollar_dollar = msg
        _t1839 = deconstruct_csv_data_columns_optional(pp, _dollar_dollar)
        _t1840 = deconstruct_csv_data_relations_optional(pp, _dollar_dollar)
        fields1434 = (_dollar_dollar.locator, _dollar_dollar.config, _t1839, _t1840, _dollar_dollar.asof,)
        unwrapped_fields1435 = fields1434
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1436 = unwrapped_fields1435[1]
        pretty_csvlocator(pp, field1436)
        newline(pp)
        field1437 = unwrapped_fields1435[2]
        pretty_csv_config(pp, field1437)
        field1438 = unwrapped_fields1435[3]
        if !isnothing(field1438)
            newline(pp)
            opt_val1439 = field1438
            pretty_gnf_columns(pp, opt_val1439)
        end
        field1440 = unwrapped_fields1435[4]
        if !isnothing(field1440)
            newline(pp)
            opt_val1441 = field1440
            pretty_target_relations(pp, opt_val1441)
        end
        newline(pp)
        field1442 = unwrapped_fields1435[5]
        pretty_csv_asof(pp, field1442)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1450 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1450)
        write(pp, flat1450)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1841 = _dollar_dollar.paths
        else
            _t1841 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1842 = String(copy(_dollar_dollar.inline_data))
        else
            _t1842 = nothing
        end
        fields1444 = (_t1841, _t1842,)
        unwrapped_fields1445 = fields1444
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1446 = unwrapped_fields1445[1]
        if !isnothing(field1446)
            newline(pp)
            opt_val1447 = field1446
            pretty_csv_locator_paths(pp, opt_val1447)
        end
        field1448 = unwrapped_fields1445[2]
        if !isnothing(field1448)
            newline(pp)
            opt_val1449 = field1448
            pretty_csv_locator_inline_data(pp, opt_val1449)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1454 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1454)
        write(pp, flat1454)
        return nothing
    else
        fields1451 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1451)
            newline(pp)
            for (i1843, elem1452) in enumerate(fields1451)
                i1453 = i1843 - 1
                if (i1453 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1452))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1456 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1456)
        write(pp, flat1456)
        return nothing
    else
        fields1455 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1455))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1462 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1462)
        write(pp, flat1462)
        return nothing
    else
        _dollar_dollar = msg
        _t1844 = deconstruct_csv_config(pp, _dollar_dollar)
        _t1845 = deconstruct_csv_storage_integration_optional(pp, _dollar_dollar)
        fields1457 = (_t1844, _t1845,)
        unwrapped_fields1458 = fields1457
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1459 = unwrapped_fields1458[1]
        pretty_config_dict(pp, field1459)
        field1460 = unwrapped_fields1458[2]
        if !isnothing(field1460)
            newline(pp)
            opt_val1461 = field1460
            pretty__storage_integration(pp, opt_val1461)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty__storage_integration(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat1464 = try_flat(pp, msg, pretty__storage_integration)
    if !isnothing(flat1464)
        write(pp, flat1464)
        return nothing
    else
        fields1463 = msg
        write(pp, "(storage_integration")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, fields1463)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1468 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1468)
        write(pp, flat1468)
        return nothing
    else
        fields1465 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1465)
            newline(pp)
            for (i1846, elem1466) in enumerate(fields1465)
                i1467 = i1846 - 1
                if (i1467 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1466)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1477 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1477)
        write(pp, flat1477)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1847 = _dollar_dollar.target_id
        else
            _t1847 = nothing
        end
        fields1469 = (_dollar_dollar.column_path, _t1847, _dollar_dollar.types,)
        unwrapped_fields1470 = fields1469
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1471 = unwrapped_fields1470[1]
        pretty_gnf_column_path(pp, field1471)
        field1472 = unwrapped_fields1470[2]
        if !isnothing(field1472)
            newline(pp)
            opt_val1473 = field1472
            pretty_relation_id(pp, opt_val1473)
        end
        newline(pp)
        write(pp, "[")
        field1474 = unwrapped_fields1470[3]
        for (i1848, elem1475) in enumerate(field1474)
            i1476 = i1848 - 1
            if (i1476 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1475)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1484 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1484)
        write(pp, flat1484)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1849 = _dollar_dollar[1]
        else
            _t1849 = nothing
        end
        deconstruct_result1482 = _t1849
        if !isnothing(deconstruct_result1482)
            unwrapped1483 = deconstruct_result1482
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1483))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1850 = _dollar_dollar
            else
                _t1850 = nothing
            end
            deconstruct_result1478 = _t1850
            if !isnothing(deconstruct_result1478)
                unwrapped1479 = deconstruct_result1478
                write(pp, "[")
                indent!(pp)
                for (i1851, elem1480) in enumerate(unwrapped1479)
                    i1481 = i1851 - 1
                    if (i1481 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1480))
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
    flat1489 = try_flat(pp, msg, pretty_target_relations)
    if !isnothing(flat1489)
        write(pp, flat1489)
        return nothing
    else
        _dollar_dollar = msg
        fields1485 = (_dollar_dollar.keys, _dollar_dollar,)
        unwrapped_fields1486 = fields1485
        write(pp, "(relations")
        indent_sexp!(pp)
        newline(pp)
        field1487 = unwrapped_fields1486[1]
        pretty_relation_keys(pp, field1487)
        newline(pp)
        field1488 = unwrapped_fields1486[2]
        pretty_relation_body(pp, field1488)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_keys(pp::PrettyPrinter, msg::Vector{Proto.NamedColumn})
    flat1493 = try_flat(pp, msg, pretty_relation_keys)
    if !isnothing(flat1493)
        write(pp, flat1493)
        return nothing
    else
        fields1490 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1490)
            newline(pp)
            for (i1852, elem1491) in enumerate(fields1490)
                i1492 = i1852 - 1
                if (i1492 > 0)
                    newline(pp)
                end
                pretty_named_column(pp, elem1491)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_named_column(pp::PrettyPrinter, msg::Proto.NamedColumn)
    flat1498 = try_flat(pp, msg, pretty_named_column)
    if !isnothing(flat1498)
        write(pp, flat1498)
        return nothing
    else
        _dollar_dollar = msg
        fields1494 = (_dollar_dollar.name, _dollar_dollar.var"#type",)
        unwrapped_fields1495 = fields1494
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1496 = unwrapped_fields1495[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1496))
        newline(pp)
        field1497 = unwrapped_fields1495[2]
        pretty_type(pp, field1497)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_body(pp::PrettyPrinter, msg::Proto.TargetRelations)
    flat1505 = try_flat(pp, msg, pretty_relation_body)
    if !isnothing(flat1505)
        write(pp, flat1505)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("plain"))
            _t1853 = _get_oneof_field(_dollar_dollar, :plain).targets
        else
            _t1853 = nothing
        end
        deconstruct_result1503 = _t1853
        if !isnothing(deconstruct_result1503)
            unwrapped1504 = deconstruct_result1503
            pretty_non_cdc_relations(pp, unwrapped1504)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("cdc"))
                _t1854 = (_get_oneof_field(_dollar_dollar, :cdc).inserts, _get_oneof_field(_dollar_dollar, :cdc).deletes,)
            else
                _t1854 = nothing
            end
            deconstruct_result1499 = _t1854
            if !isnothing(deconstruct_result1499)
                unwrapped1500 = deconstruct_result1499
                field1501 = unwrapped1500[1]
                pretty_cdc_inserts(pp, field1501)
                write(pp, " ")
                field1502 = unwrapped1500[2]
                pretty_cdc_deletes(pp, field1502)
            else
                throw(ParseError("No matching rule for relation_body"))
            end
        end
    end
    return nothing
end

function pretty_non_cdc_relations(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1509 = try_flat(pp, msg, pretty_non_cdc_relations)
    if !isnothing(flat1509)
        write(pp, flat1509)
        return nothing
    else
        fields1506 = msg
        for (i1855, elem1507) in enumerate(fields1506)
            i1508 = i1855 - 1
            if (i1508 > 0)
                newline(pp)
            end
            pretty_target_relation(pp, elem1507)
        end
    end
    return nothing
end

function pretty_target_relation(pp::PrettyPrinter, msg::Proto.TargetRelation)
    flat1516 = try_flat(pp, msg, pretty_target_relation)
    if !isnothing(flat1516)
        write(pp, flat1516)
        return nothing
    else
        _dollar_dollar = msg
        fields1510 = (_dollar_dollar.target_id, _dollar_dollar.values,)
        unwrapped_fields1511 = fields1510
        write(pp, "(relation")
        indent_sexp!(pp)
        newline(pp)
        field1512 = unwrapped_fields1511[1]
        pretty_relation_id(pp, field1512)
        field1513 = unwrapped_fields1511[2]
        if !isempty(field1513)
            newline(pp)
            for (i1856, elem1514) in enumerate(field1513)
                i1515 = i1856 - 1
                if (i1515 > 0)
                    newline(pp)
                end
                pretty_named_column(pp, elem1514)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_inserts(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1520 = try_flat(pp, msg, pretty_cdc_inserts)
    if !isnothing(flat1520)
        write(pp, flat1520)
        return nothing
    else
        fields1517 = msg
        write(pp, "(inserts")
        indent_sexp!(pp)
        if !isempty(fields1517)
            newline(pp)
            for (i1857, elem1518) in enumerate(fields1517)
                i1519 = i1857 - 1
                if (i1519 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1518)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_deletes(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1524 = try_flat(pp, msg, pretty_cdc_deletes)
    if !isnothing(flat1524)
        write(pp, flat1524)
        return nothing
    else
        fields1521 = msg
        write(pp, "(deletes")
        indent_sexp!(pp)
        if !isempty(fields1521)
            newline(pp)
            for (i1858, elem1522) in enumerate(fields1521)
                i1523 = i1858 - 1
                if (i1523 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1522)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1526 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1526)
        write(pp, flat1526)
        return nothing
    else
        fields1525 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1525))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1537 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1537)
        write(pp, flat1537)
        return nothing
    else
        _dollar_dollar = msg
        _t1859 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1860 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1527 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1859, _t1860, _dollar_dollar.returns_delta,)
        unwrapped_fields1528 = fields1527
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1529 = unwrapped_fields1528[1]
        pretty_iceberg_locator(pp, field1529)
        newline(pp)
        field1530 = unwrapped_fields1528[2]
        pretty_iceberg_catalog_config(pp, field1530)
        newline(pp)
        field1531 = unwrapped_fields1528[3]
        pretty_gnf_columns(pp, field1531)
        field1532 = unwrapped_fields1528[4]
        if !isnothing(field1532)
            newline(pp)
            opt_val1533 = field1532
            pretty_iceberg_from_snapshot(pp, opt_val1533)
        end
        field1534 = unwrapped_fields1528[5]
        if !isnothing(field1534)
            newline(pp)
            opt_val1535 = field1534
            pretty_iceberg_to_snapshot(pp, opt_val1535)
        end
        newline(pp)
        field1536 = unwrapped_fields1528[6]
        pretty_boolean_value(pp, field1536)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1543 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1543)
        write(pp, flat1543)
        return nothing
    else
        _dollar_dollar = msg
        fields1538 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1539 = fields1538
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1540 = unwrapped_fields1539[1]
        pretty_iceberg_locator_table_name(pp, field1540)
        newline(pp)
        field1541 = unwrapped_fields1539[2]
        pretty_iceberg_locator_namespace(pp, field1541)
        newline(pp)
        field1542 = unwrapped_fields1539[3]
        pretty_iceberg_locator_warehouse(pp, field1542)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1545 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1545)
        write(pp, flat1545)
        return nothing
    else
        fields1544 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1544))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1549 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1549)
        write(pp, flat1549)
        return nothing
    else
        fields1546 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1546)
            newline(pp)
            for (i1861, elem1547) in enumerate(fields1546)
                i1548 = i1861 - 1
                if (i1548 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1547))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1551 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1551)
        write(pp, flat1551)
        return nothing
    else
        fields1550 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1550))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1559 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1559)
        write(pp, flat1559)
        return nothing
    else
        _dollar_dollar = msg
        _t1862 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1552 = (_dollar_dollar.catalog_uri, _t1862, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1553 = fields1552
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1554 = unwrapped_fields1553[1]
        pretty_iceberg_catalog_uri(pp, field1554)
        field1555 = unwrapped_fields1553[2]
        if !isnothing(field1555)
            newline(pp)
            opt_val1556 = field1555
            pretty_iceberg_catalog_config_scope(pp, opt_val1556)
        end
        newline(pp)
        field1557 = unwrapped_fields1553[3]
        pretty_iceberg_properties(pp, field1557)
        newline(pp)
        field1558 = unwrapped_fields1553[4]
        pretty_iceberg_auth_properties(pp, field1558)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1561 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1561)
        write(pp, flat1561)
        return nothing
    else
        fields1560 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1560))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1563 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1563)
        write(pp, flat1563)
        return nothing
    else
        fields1562 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1562))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1567 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1567)
        write(pp, flat1567)
        return nothing
    else
        fields1564 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1564)
            newline(pp)
            for (i1863, elem1565) in enumerate(fields1564)
                i1566 = i1863 - 1
                if (i1566 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1565)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1572 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1572)
        write(pp, flat1572)
        return nothing
    else
        _dollar_dollar = msg
        fields1568 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1569 = fields1568
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1570 = unwrapped_fields1569[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1570))
        newline(pp)
        field1571 = unwrapped_fields1569[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1571))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1576 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1576)
        write(pp, flat1576)
        return nothing
    else
        fields1573 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1573)
            newline(pp)
            for (i1864, elem1574) in enumerate(fields1573)
                i1575 = i1864 - 1
                if (i1575 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1574)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1581 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1581)
        write(pp, flat1581)
        return nothing
    else
        _dollar_dollar = msg
        _t1865 = mask_secret_value(pp, _dollar_dollar)
        fields1577 = (_dollar_dollar[1], _t1865,)
        unwrapped_fields1578 = fields1577
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1579 = unwrapped_fields1578[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1579))
        newline(pp)
        field1580 = unwrapped_fields1578[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1580))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1583 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1583)
        write(pp, flat1583)
        return nothing
    else
        fields1582 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1582))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1585 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1585)
        write(pp, flat1585)
        return nothing
    else
        fields1584 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1584))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1588 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1588)
        write(pp, flat1588)
        return nothing
    else
        _dollar_dollar = msg
        fields1586 = _dollar_dollar.fragment_id
        unwrapped_fields1587 = fields1586
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1587)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1593 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1593)
        write(pp, flat1593)
        return nothing
    else
        _dollar_dollar = msg
        fields1589 = _dollar_dollar.relations
        unwrapped_fields1590 = fields1589
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1590)
            newline(pp)
            for (i1866, elem1591) in enumerate(unwrapped_fields1590)
                i1592 = i1866 - 1
                if (i1592 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1591)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1600 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1600)
        write(pp, flat1600)
        return nothing
    else
        _dollar_dollar = msg
        fields1594 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1595 = fields1594
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1596 = unwrapped_fields1595[1]
        pretty_edb_path(pp, field1596)
        field1597 = unwrapped_fields1595[2]
        if !isempty(field1597)
            newline(pp)
            for (i1867, elem1598) in enumerate(field1597)
                i1599 = i1867 - 1
                if (i1599 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1598)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1605 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1605)
        write(pp, flat1605)
        return nothing
    else
        _dollar_dollar = msg
        fields1601 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1602 = fields1601
        field1603 = unwrapped_fields1602[1]
        pretty_edb_path(pp, field1603)
        write(pp, " ")
        field1604 = unwrapped_fields1602[2]
        pretty_relation_id(pp, field1604)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1609 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1609)
        write(pp, flat1609)
        return nothing
    else
        fields1606 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1606)
            newline(pp)
            for (i1868, elem1607) in enumerate(fields1606)
                i1608 = i1868 - 1
                if (i1608 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1607)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1620 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1620)
        write(pp, flat1620)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1869 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1869 = nothing
        end
        deconstruct_result1618 = _t1869
        if !isnothing(deconstruct_result1618)
            unwrapped1619 = deconstruct_result1618
            pretty_demand(pp, unwrapped1619)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1870 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1870 = nothing
            end
            deconstruct_result1616 = _t1870
            if !isnothing(deconstruct_result1616)
                unwrapped1617 = deconstruct_result1616
                pretty_output(pp, unwrapped1617)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1871 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1871 = nothing
                end
                deconstruct_result1614 = _t1871
                if !isnothing(deconstruct_result1614)
                    unwrapped1615 = deconstruct_result1614
                    pretty_what_if(pp, unwrapped1615)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1872 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1872 = nothing
                    end
                    deconstruct_result1612 = _t1872
                    if !isnothing(deconstruct_result1612)
                        unwrapped1613 = deconstruct_result1612
                        pretty_abort(pp, unwrapped1613)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1873 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1873 = nothing
                        end
                        deconstruct_result1610 = _t1873
                        if !isnothing(deconstruct_result1610)
                            unwrapped1611 = deconstruct_result1610
                            pretty_export(pp, unwrapped1611)
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
    flat1623 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1623)
        write(pp, flat1623)
        return nothing
    else
        _dollar_dollar = msg
        fields1621 = _dollar_dollar.relation_id
        unwrapped_fields1622 = fields1621
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1622)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1628 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1628)
        write(pp, flat1628)
        return nothing
    else
        _dollar_dollar = msg
        fields1624 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1625 = fields1624
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1626 = unwrapped_fields1625[1]
        pretty_name(pp, field1626)
        newline(pp)
        field1627 = unwrapped_fields1625[2]
        pretty_relation_id(pp, field1627)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1633 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1633)
        write(pp, flat1633)
        return nothing
    else
        _dollar_dollar = msg
        fields1629 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1630 = fields1629
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1631 = unwrapped_fields1630[1]
        pretty_name(pp, field1631)
        newline(pp)
        field1632 = unwrapped_fields1630[2]
        pretty_epoch(pp, field1632)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1639 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1639)
        write(pp, flat1639)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1874 = _dollar_dollar.name
        else
            _t1874 = nothing
        end
        fields1634 = (_t1874, _dollar_dollar.relation_id,)
        unwrapped_fields1635 = fields1634
        write(pp, "(abort")
        indent_sexp!(pp)
        field1636 = unwrapped_fields1635[1]
        if !isnothing(field1636)
            newline(pp)
            opt_val1637 = field1636
            pretty_name(pp, opt_val1637)
        end
        newline(pp)
        field1638 = unwrapped_fields1635[2]
        pretty_relation_id(pp, field1638)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1644 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1644)
        write(pp, flat1644)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1875 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1875 = nothing
        end
        deconstruct_result1642 = _t1875
        if !isnothing(deconstruct_result1642)
            unwrapped1643 = deconstruct_result1642
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1643)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1876 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1876 = nothing
            end
            deconstruct_result1640 = _t1876
            if !isnothing(deconstruct_result1640)
                unwrapped1641 = deconstruct_result1640
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1641)
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
    flat1655 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1655)
        write(pp, flat1655)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1878 = deconstruct_export_csv_output_location(pp, _dollar_dollar)
            _t1877 = (_t1878, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1877 = nothing
        end
        deconstruct_result1650 = _t1877
        if !isnothing(deconstruct_result1650)
            unwrapped1651 = deconstruct_result1650
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1652 = unwrapped1651[1]
            pretty_export_csv_output_location(pp, field1652)
            newline(pp)
            field1653 = unwrapped1651[2]
            pretty_export_csv_source(pp, field1653)
            newline(pp)
            field1654 = unwrapped1651[3]
            pretty_csv_config(pp, field1654)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1880 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1879 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1880,)
            else
                _t1879 = nothing
            end
            deconstruct_result1645 = _t1879
            if !isnothing(deconstruct_result1645)
                unwrapped1646 = deconstruct_result1645
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1647 = unwrapped1646[1]
                pretty_export_csv_path(pp, field1647)
                newline(pp)
                field1648 = unwrapped1646[2]
                pretty_export_csv_columns_list(pp, field1648)
                newline(pp)
                field1649 = unwrapped1646[3]
                pretty_config_dict(pp, field1649)
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
    flat1660 = try_flat(pp, msg, pretty_export_csv_output_location)
    if !isnothing(flat1660)
        write(pp, flat1660)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar[1] != ""
            _t1881 = _dollar_dollar[1]
        else
            _t1881 = nothing
        end
        deconstruct_result1658 = _t1881
        if !isnothing(deconstruct_result1658)
            unwrapped1659 = deconstruct_result1658
            write(pp, "(path")
            indent_sexp!(pp)
            newline(pp)
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1659))
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _dollar_dollar[2] != ""
                _t1882 = _dollar_dollar[2]
            else
                _t1882 = nothing
            end
            deconstruct_result1656 = _t1882
            if !isnothing(deconstruct_result1656)
                unwrapped1657 = deconstruct_result1656
                write(pp, "(transaction_output_name")
                indent_sexp!(pp)
                newline(pp)
                pretty_name(pp, unwrapped1657)
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
    flat1667 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1667)
        write(pp, flat1667)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1883 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1883 = nothing
        end
        deconstruct_result1663 = _t1883
        if !isnothing(deconstruct_result1663)
            unwrapped1664 = deconstruct_result1663
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1664)
                newline(pp)
                for (i1884, elem1665) in enumerate(unwrapped1664)
                    i1666 = i1884 - 1
                    if (i1666 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1665)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1885 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1885 = nothing
            end
            deconstruct_result1661 = _t1885
            if !isnothing(deconstruct_result1661)
                unwrapped1662 = deconstruct_result1661
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1662)
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
    flat1672 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1672)
        write(pp, flat1672)
        return nothing
    else
        _dollar_dollar = msg
        fields1668 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1669 = fields1668
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1670 = unwrapped_fields1669[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1670))
        newline(pp)
        field1671 = unwrapped_fields1669[2]
        pretty_relation_id(pp, field1671)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1674 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1674)
        write(pp, flat1674)
        return nothing
    else
        fields1673 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1673))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1678 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1678)
        write(pp, flat1678)
        return nothing
    else
        fields1675 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1675)
            newline(pp)
            for (i1886, elem1676) in enumerate(fields1675)
                i1677 = i1886 - 1
                if (i1677 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1676)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1687 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1687)
        write(pp, flat1687)
        return nothing
    else
        _dollar_dollar = msg
        _t1887 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1679 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1887,)
        unwrapped_fields1680 = fields1679
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1681 = unwrapped_fields1680[1]
        pretty_iceberg_locator(pp, field1681)
        newline(pp)
        field1682 = unwrapped_fields1680[2]
        pretty_iceberg_catalog_config(pp, field1682)
        newline(pp)
        field1683 = unwrapped_fields1680[3]
        pretty_export_iceberg_table_def(pp, field1683)
        newline(pp)
        field1684 = unwrapped_fields1680[4]
        pretty_iceberg_table_properties(pp, field1684)
        field1685 = unwrapped_fields1680[5]
        if !isnothing(field1685)
            newline(pp)
            opt_val1686 = field1685
            pretty_config_dict(pp, opt_val1686)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1689 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1689)
        write(pp, flat1689)
        return nothing
    else
        fields1688 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1688)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1693 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1693)
        write(pp, flat1693)
        return nothing
    else
        fields1690 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1690)
            newline(pp)
            for (i1888, elem1691) in enumerate(fields1690)
                i1692 = i1888 - 1
                if (i1692 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1691)
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
    for (i1944, _rid) in enumerate(msg.ids)
        _idx = i1944 - 1
        newline(pp)
        write(pp, "(")
        _t1945 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1945)
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
    for (i1946, _elem) in enumerate(msg.inserts)
        _idx = i1946 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":deletes (")
    for (i1947, _elem) in enumerate(msg.deletes)
        _idx = i1947 - 1
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
    for (i1948, _elem) in enumerate(msg.keys)
        _idx = i1948 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1949, _elem) in enumerate(msg.values)
        _idx = i1949 - 1
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
    for (i1950, _elem) in enumerate(msg.targets)
        _idx = i1950 - 1
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

function pretty_ast_size_limit(pp::PrettyPrinter, msg::Proto.ASTSizeLimit)
    write(pp, "(ast_size_limit")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":warning_limit ")
    write(pp, string(msg.warning_limit))
    newline(pp)
    write(pp, ":exception_limit ")
    write(pp, string(msg.exception_limit))
    write(pp, ")")
    dedent!(pp)
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Proto.ExportCSVColumns)
    write(pp, "(export_csv_columns")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":columns (")
    for (i1951, _elem) in enumerate(msg.columns)
        _idx = i1951 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.NamedColumn}) = pretty_relation_keys(pp, x)
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ASTSizeLimit) = pretty_ast_size_limit(pp, x)
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
