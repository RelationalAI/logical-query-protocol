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
        _t1876 = nothing
    end
    return msg.columns
end

function deconstruct_csv_data_relations_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Proto.TargetRelations}
    if _has_proto_field(msg, Symbol("relations"))
        return msg.relations
    else
        _t1877 = nothing
    end
    return nothing
end

function _make_value_int32(pp::PrettyPrinter, v::Int32)::Proto.Value
    _t1878 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1878
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1879 = Proto.Value(value=OneOf(:int_value, v))
    return _t1879
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1880 = Proto.Value(value=OneOf(:float_value, v))
    return _t1880
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1881 = Proto.Value(value=OneOf(:string_value, v))
    return _t1881
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1882 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1882
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1883 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1883
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1884 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1884,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1885 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1885,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1886 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1886,))
            end
        end
    end
    _t1887 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1887,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1888 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1888,))
    _t1889 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1889,))
    if msg.new_line != ""
        _t1890 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1890,))
    end
    _t1891 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1891,))
    _t1892 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1892,))
    _t1893 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1893,))
    if msg.comment != ""
        _t1894 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1894,))
    end
    for missing_string in msg.missing_strings
        _t1895 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1895,))
    end
    _t1896 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1896,))
    _t1897 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1897,))
    _t1898 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1898,))
    if msg.partition_size_mb != 0
        _t1899 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1899,))
    end
    return sort(result)
end

function deconstruct_csv_storage_integration_optional(pp::PrettyPrinter, msg::Proto.CSVConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    if !_has_proto_field(msg, Symbol("storage_integration"))
        return nothing
    else
        _t1900 = nothing
    end
    si = msg.storage_integration
    result = Tuple{String, Proto.Value}[]
    if si.provider != ""
        _t1901 = _make_value_string(pp, si.provider)
        push!(result, ("provider", _t1901,))
    end
    if si.azure_sas_token != ""
        _t1902 = _make_value_string(pp, "***")
        push!(result, ("azure_sas_token", _t1902,))
    end
    if si.s3_region != ""
        _t1903 = _make_value_string(pp, si.s3_region)
        push!(result, ("s3_region", _t1903,))
    end
    if si.s3_access_key_id != ""
        _t1904 = _make_value_string(pp, "***")
        push!(result, ("s3_access_key_id", _t1904,))
    end
    if si.s3_secret_access_key != ""
        _t1905 = _make_value_string(pp, "***")
        push!(result, ("s3_secret_access_key", _t1905,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1906 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1906,))
    _t1907 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1907,))
    _t1908 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1908,))
    _t1909 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1909,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1910 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1910,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1911 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1911,))
        end
    end
    _t1912 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1912,))
    _t1913 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1913,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1914 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1914,))
    end
    if !isnothing(msg.compression)
        _t1915 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1915,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1916 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1916,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1917 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1917,))
    end
    if !isnothing(msg.syntax_delim)
        _t1918 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1918,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1919 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1919,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1920 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1920,))
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
        _t1921 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1922 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1923 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1924 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1924,))
    end
    if msg.target_file_size_bytes != 0
        _t1925 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1925,))
    end
    if msg.compression != ""
        _t1926 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1926,))
    end
    if length(result) == 0
        return nothing
    else
        _t1927 = nothing
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
        _t1928 = nothing
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
    flat851 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat851)
        write(pp, flat851)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1684 = _dollar_dollar.configure
        else
            _t1684 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1685 = _dollar_dollar.sync
        else
            _t1685 = nothing
        end
        fields842 = (_t1684, _t1685, _dollar_dollar.epochs,)
        unwrapped_fields843 = fields842
        write(pp, "(transaction")
        indent_sexp!(pp)
        field844 = unwrapped_fields843[1]
        if !isnothing(field844)
            newline(pp)
            opt_val845 = field844
            pretty_configure(pp, opt_val845)
        end
        field846 = unwrapped_fields843[2]
        if !isnothing(field846)
            newline(pp)
            opt_val847 = field846
            pretty_sync(pp, opt_val847)
        end
        field848 = unwrapped_fields843[3]
        if !isempty(field848)
            newline(pp)
            for (i1686, elem849) in enumerate(field848)
                i850 = i1686 - 1
                if (i850 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem849)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat854 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat854)
        write(pp, flat854)
        return nothing
    else
        _dollar_dollar = msg
        _t1687 = deconstruct_configure(pp, _dollar_dollar)
        fields852 = _t1687
        unwrapped_fields853 = fields852
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields853)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat858 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat858)
        write(pp, flat858)
        return nothing
    else
        fields855 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields855)
            newline(pp)
            for (i1688, elem856) in enumerate(fields855)
                i857 = i1688 - 1
                if (i857 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem856)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat863 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat863)
        write(pp, flat863)
        return nothing
    else
        _dollar_dollar = msg
        fields859 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields860 = fields859
        write(pp, ":")
        field861 = unwrapped_fields860[1]
        write(pp, field861)
        write(pp, " ")
        field862 = unwrapped_fields860[2]
        pretty_raw_value(pp, field862)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat889 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat889)
        write(pp, flat889)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1689 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1689 = nothing
        end
        deconstruct_result887 = _t1689
        if !isnothing(deconstruct_result887)
            unwrapped888 = deconstruct_result887
            pretty_raw_date(pp, unwrapped888)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1690 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1690 = nothing
            end
            deconstruct_result885 = _t1690
            if !isnothing(deconstruct_result885)
                unwrapped886 = deconstruct_result885
                pretty_raw_datetime(pp, unwrapped886)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1691 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1691 = nothing
                end
                deconstruct_result883 = _t1691
                if !isnothing(deconstruct_result883)
                    unwrapped884 = deconstruct_result883
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped884))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1692 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1692 = nothing
                    end
                    deconstruct_result881 = _t1692
                    if !isnothing(deconstruct_result881)
                        unwrapped882 = deconstruct_result881
                        write(pp, (string(Int64(unwrapped882)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1693 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1693 = nothing
                        end
                        deconstruct_result879 = _t1693
                        if !isnothing(deconstruct_result879)
                            unwrapped880 = deconstruct_result879
                            write(pp, string(unwrapped880))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1694 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1694 = nothing
                            end
                            deconstruct_result877 = _t1694
                            if !isnothing(deconstruct_result877)
                                unwrapped878 = deconstruct_result877
                                write(pp, format_float32_literal(unwrapped878))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1695 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1695 = nothing
                                end
                                deconstruct_result875 = _t1695
                                if !isnothing(deconstruct_result875)
                                    unwrapped876 = deconstruct_result875
                                    write(pp, lowercase(string(unwrapped876)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1696 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1696 = nothing
                                    end
                                    deconstruct_result873 = _t1696
                                    if !isnothing(deconstruct_result873)
                                        unwrapped874 = deconstruct_result873
                                        write(pp, (string(Int64(unwrapped874)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1697 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1697 = nothing
                                        end
                                        deconstruct_result871 = _t1697
                                        if !isnothing(deconstruct_result871)
                                            unwrapped872 = deconstruct_result871
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped872))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1698 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1698 = nothing
                                            end
                                            deconstruct_result869 = _t1698
                                            if !isnothing(deconstruct_result869)
                                                unwrapped870 = deconstruct_result869
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped870))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1699 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1699 = nothing
                                                end
                                                deconstruct_result867 = _t1699
                                                if !isnothing(deconstruct_result867)
                                                    unwrapped868 = deconstruct_result867
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped868))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1700 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1700 = nothing
                                                    end
                                                    deconstruct_result865 = _t1700
                                                    if !isnothing(deconstruct_result865)
                                                        unwrapped866 = deconstruct_result865
                                                        pretty_boolean_value(pp, unwrapped866)
                                                    else
                                                        fields864 = msg
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
    flat895 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat895)
        write(pp, flat895)
        return nothing
    else
        _dollar_dollar = msg
        fields890 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields891 = fields890
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field892 = unwrapped_fields891[1]
        write(pp, string(field892))
        newline(pp)
        field893 = unwrapped_fields891[2]
        write(pp, string(field893))
        newline(pp)
        field894 = unwrapped_fields891[3]
        write(pp, string(field894))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat906 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        _dollar_dollar = msg
        fields896 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields897 = fields896
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field898 = unwrapped_fields897[1]
        write(pp, string(field898))
        newline(pp)
        field899 = unwrapped_fields897[2]
        write(pp, string(field899))
        newline(pp)
        field900 = unwrapped_fields897[3]
        write(pp, string(field900))
        newline(pp)
        field901 = unwrapped_fields897[4]
        write(pp, string(field901))
        newline(pp)
        field902 = unwrapped_fields897[5]
        write(pp, string(field902))
        newline(pp)
        field903 = unwrapped_fields897[6]
        write(pp, string(field903))
        field904 = unwrapped_fields897[7]
        if !isnothing(field904)
            newline(pp)
            opt_val905 = field904
            write(pp, string(opt_val905))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1701 = ()
    else
        _t1701 = nothing
    end
    deconstruct_result909 = _t1701
    if !isnothing(deconstruct_result909)
        unwrapped910 = deconstruct_result909
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1702 = ()
        else
            _t1702 = nothing
        end
        deconstruct_result907 = _t1702
        if !isnothing(deconstruct_result907)
            unwrapped908 = deconstruct_result907
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat915 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat915)
        write(pp, flat915)
        return nothing
    else
        _dollar_dollar = msg
        fields911 = _dollar_dollar.fragments
        unwrapped_fields912 = fields911
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields912)
            newline(pp)
            for (i1703, elem913) in enumerate(unwrapped_fields912)
                i914 = i1703 - 1
                if (i914 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem913)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat918 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat918)
        write(pp, flat918)
        return nothing
    else
        _dollar_dollar = msg
        fields916 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields917 = fields916
        write(pp, ":")
        write(pp, unwrapped_fields917)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat925 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat925)
        write(pp, flat925)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1704 = _dollar_dollar.writes
        else
            _t1704 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1705 = _dollar_dollar.reads
        else
            _t1705 = nothing
        end
        fields919 = (_t1704, _t1705,)
        unwrapped_fields920 = fields919
        write(pp, "(epoch")
        indent_sexp!(pp)
        field921 = unwrapped_fields920[1]
        if !isnothing(field921)
            newline(pp)
            opt_val922 = field921
            pretty_epoch_writes(pp, opt_val922)
        end
        field923 = unwrapped_fields920[2]
        if !isnothing(field923)
            newline(pp)
            opt_val924 = field923
            pretty_epoch_reads(pp, opt_val924)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat929 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat929)
        write(pp, flat929)
        return nothing
    else
        fields926 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields926)
            newline(pp)
            for (i1706, elem927) in enumerate(fields926)
                i928 = i1706 - 1
                if (i928 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem927)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat938 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat938)
        write(pp, flat938)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1707 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1707 = nothing
        end
        deconstruct_result936 = _t1707
        if !isnothing(deconstruct_result936)
            unwrapped937 = deconstruct_result936
            pretty_define(pp, unwrapped937)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1708 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1708 = nothing
            end
            deconstruct_result934 = _t1708
            if !isnothing(deconstruct_result934)
                unwrapped935 = deconstruct_result934
                pretty_undefine(pp, unwrapped935)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1709 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1709 = nothing
                end
                deconstruct_result932 = _t1709
                if !isnothing(deconstruct_result932)
                    unwrapped933 = deconstruct_result932
                    pretty_context(pp, unwrapped933)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1710 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1710 = nothing
                    end
                    deconstruct_result930 = _t1710
                    if !isnothing(deconstruct_result930)
                        unwrapped931 = deconstruct_result930
                        pretty_snapshot(pp, unwrapped931)
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
    flat941 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat941)
        write(pp, flat941)
        return nothing
    else
        _dollar_dollar = msg
        fields939 = _dollar_dollar.fragment
        unwrapped_fields940 = fields939
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields940)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat948 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat948)
        write(pp, flat948)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields942 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields943 = fields942
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field944 = unwrapped_fields943[1]
        pretty_new_fragment_id(pp, field944)
        field945 = unwrapped_fields943[2]
        if !isempty(field945)
            newline(pp)
            for (i1711, elem946) in enumerate(field945)
                i947 = i1711 - 1
                if (i947 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem946)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat950 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat950)
        write(pp, flat950)
        return nothing
    else
        fields949 = msg
        pretty_fragment_id(pp, fields949)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat959 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat959)
        write(pp, flat959)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1712 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1712 = nothing
        end
        deconstruct_result957 = _t1712
        if !isnothing(deconstruct_result957)
            unwrapped958 = deconstruct_result957
            pretty_def(pp, unwrapped958)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1713 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1713 = nothing
            end
            deconstruct_result955 = _t1713
            if !isnothing(deconstruct_result955)
                unwrapped956 = deconstruct_result955
                pretty_algorithm(pp, unwrapped956)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1714 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1714 = nothing
                end
                deconstruct_result953 = _t1714
                if !isnothing(deconstruct_result953)
                    unwrapped954 = deconstruct_result953
                    pretty_constraint(pp, unwrapped954)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1715 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1715 = nothing
                    end
                    deconstruct_result951 = _t1715
                    if !isnothing(deconstruct_result951)
                        unwrapped952 = deconstruct_result951
                        pretty_data(pp, unwrapped952)
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
    flat966 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat966)
        write(pp, flat966)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1716 = _dollar_dollar.attrs
        else
            _t1716 = nothing
        end
        fields960 = (_dollar_dollar.name, _dollar_dollar.body, _t1716,)
        unwrapped_fields961 = fields960
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field962 = unwrapped_fields961[1]
        pretty_relation_id(pp, field962)
        newline(pp)
        field963 = unwrapped_fields961[2]
        pretty_abstraction(pp, field963)
        field964 = unwrapped_fields961[3]
        if !isnothing(field964)
            newline(pp)
            opt_val965 = field964
            pretty_attrs(pp, opt_val965)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat971 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat971)
        write(pp, flat971)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1718 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1717 = _t1718
        else
            _t1717 = nothing
        end
        deconstruct_result969 = _t1717
        if !isnothing(deconstruct_result969)
            unwrapped970 = deconstruct_result969
            write(pp, ":")
            write(pp, unwrapped970)
        else
            _dollar_dollar = msg
            _t1719 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result967 = _t1719
            if !isnothing(deconstruct_result967)
                unwrapped968 = deconstruct_result967
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped968))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat976 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat976)
        write(pp, flat976)
        return nothing
    else
        _dollar_dollar = msg
        _t1720 = deconstruct_bindings(pp, _dollar_dollar)
        fields972 = (_t1720, _dollar_dollar.value,)
        unwrapped_fields973 = fields972
        write(pp, "(")
        indent!(pp)
        field974 = unwrapped_fields973[1]
        pretty_bindings(pp, field974)
        newline(pp)
        field975 = unwrapped_fields973[2]
        pretty_formula(pp, field975)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat984 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat984)
        write(pp, flat984)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1721 = _dollar_dollar[2]
        else
            _t1721 = nothing
        end
        fields977 = (_dollar_dollar[1], _t1721,)
        unwrapped_fields978 = fields977
        write(pp, "[")
        indent!(pp)
        field979 = unwrapped_fields978[1]
        for (i1722, elem980) in enumerate(field979)
            i981 = i1722 - 1
            if (i981 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem980)
        end
        field982 = unwrapped_fields978[2]
        if !isnothing(field982)
            newline(pp)
            opt_val983 = field982
            pretty_value_bindings(pp, opt_val983)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat989 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat989)
        write(pp, flat989)
        return nothing
    else
        _dollar_dollar = msg
        fields985 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields986 = fields985
        field987 = unwrapped_fields986[1]
        write(pp, field987)
        write(pp, "::")
        field988 = unwrapped_fields986[2]
        pretty_type(pp, field988)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat1018 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat1018)
        write(pp, flat1018)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1723 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1723 = nothing
        end
        deconstruct_result1016 = _t1723
        if !isnothing(deconstruct_result1016)
            unwrapped1017 = deconstruct_result1016
            pretty_unspecified_type(pp, unwrapped1017)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1724 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1724 = nothing
            end
            deconstruct_result1014 = _t1724
            if !isnothing(deconstruct_result1014)
                unwrapped1015 = deconstruct_result1014
                pretty_string_type(pp, unwrapped1015)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1725 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1725 = nothing
                end
                deconstruct_result1012 = _t1725
                if !isnothing(deconstruct_result1012)
                    unwrapped1013 = deconstruct_result1012
                    pretty_int_type(pp, unwrapped1013)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1726 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1726 = nothing
                    end
                    deconstruct_result1010 = _t1726
                    if !isnothing(deconstruct_result1010)
                        unwrapped1011 = deconstruct_result1010
                        pretty_float_type(pp, unwrapped1011)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1727 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1727 = nothing
                        end
                        deconstruct_result1008 = _t1727
                        if !isnothing(deconstruct_result1008)
                            unwrapped1009 = deconstruct_result1008
                            pretty_uint128_type(pp, unwrapped1009)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1728 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1728 = nothing
                            end
                            deconstruct_result1006 = _t1728
                            if !isnothing(deconstruct_result1006)
                                unwrapped1007 = deconstruct_result1006
                                pretty_int128_type(pp, unwrapped1007)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1729 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1729 = nothing
                                end
                                deconstruct_result1004 = _t1729
                                if !isnothing(deconstruct_result1004)
                                    unwrapped1005 = deconstruct_result1004
                                    pretty_date_type(pp, unwrapped1005)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1730 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1730 = nothing
                                    end
                                    deconstruct_result1002 = _t1730
                                    if !isnothing(deconstruct_result1002)
                                        unwrapped1003 = deconstruct_result1002
                                        pretty_datetime_type(pp, unwrapped1003)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1731 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1731 = nothing
                                        end
                                        deconstruct_result1000 = _t1731
                                        if !isnothing(deconstruct_result1000)
                                            unwrapped1001 = deconstruct_result1000
                                            pretty_missing_type(pp, unwrapped1001)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1732 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1732 = nothing
                                            end
                                            deconstruct_result998 = _t1732
                                            if !isnothing(deconstruct_result998)
                                                unwrapped999 = deconstruct_result998
                                                pretty_decimal_type(pp, unwrapped999)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1733 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1733 = nothing
                                                end
                                                deconstruct_result996 = _t1733
                                                if !isnothing(deconstruct_result996)
                                                    unwrapped997 = deconstruct_result996
                                                    pretty_boolean_type(pp, unwrapped997)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1734 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1734 = nothing
                                                    end
                                                    deconstruct_result994 = _t1734
                                                    if !isnothing(deconstruct_result994)
                                                        unwrapped995 = deconstruct_result994
                                                        pretty_int32_type(pp, unwrapped995)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1735 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1735 = nothing
                                                        end
                                                        deconstruct_result992 = _t1735
                                                        if !isnothing(deconstruct_result992)
                                                            unwrapped993 = deconstruct_result992
                                                            pretty_float32_type(pp, unwrapped993)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1736 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1736 = nothing
                                                            end
                                                            deconstruct_result990 = _t1736
                                                            if !isnothing(deconstruct_result990)
                                                                unwrapped991 = deconstruct_result990
                                                                pretty_uint32_type(pp, unwrapped991)
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
    fields1019 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields1020 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields1021 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields1022 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields1023 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields1024 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields1025 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields1026 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields1027 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat1032 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat1032)
        write(pp, flat1032)
        return nothing
    else
        _dollar_dollar = msg
        fields1028 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields1029 = fields1028
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field1030 = unwrapped_fields1029[1]
        write(pp, string(field1030))
        newline(pp)
        field1031 = unwrapped_fields1029[2]
        write(pp, string(field1031))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields1033 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields1034 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields1035 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields1036 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1040 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1040)
        write(pp, flat1040)
        return nothing
    else
        fields1037 = msg
        write(pp, "|")
        if !isempty(fields1037)
            write(pp, " ")
            for (i1737, elem1038) in enumerate(fields1037)
                i1039 = i1737 - 1
                if (i1039 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1038)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1067 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1067)
        write(pp, flat1067)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1738 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1738 = nothing
        end
        deconstruct_result1065 = _t1738
        if !isnothing(deconstruct_result1065)
            unwrapped1066 = deconstruct_result1065
            pretty_true(pp, unwrapped1066)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1739 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1739 = nothing
            end
            deconstruct_result1063 = _t1739
            if !isnothing(deconstruct_result1063)
                unwrapped1064 = deconstruct_result1063
                pretty_false(pp, unwrapped1064)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1740 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1740 = nothing
                end
                deconstruct_result1061 = _t1740
                if !isnothing(deconstruct_result1061)
                    unwrapped1062 = deconstruct_result1061
                    pretty_exists(pp, unwrapped1062)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1741 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1741 = nothing
                    end
                    deconstruct_result1059 = _t1741
                    if !isnothing(deconstruct_result1059)
                        unwrapped1060 = deconstruct_result1059
                        pretty_reduce(pp, unwrapped1060)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1742 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1742 = nothing
                        end
                        deconstruct_result1057 = _t1742
                        if !isnothing(deconstruct_result1057)
                            unwrapped1058 = deconstruct_result1057
                            pretty_conjunction(pp, unwrapped1058)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1743 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1743 = nothing
                            end
                            deconstruct_result1055 = _t1743
                            if !isnothing(deconstruct_result1055)
                                unwrapped1056 = deconstruct_result1055
                                pretty_disjunction(pp, unwrapped1056)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1744 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1744 = nothing
                                end
                                deconstruct_result1053 = _t1744
                                if !isnothing(deconstruct_result1053)
                                    unwrapped1054 = deconstruct_result1053
                                    pretty_not(pp, unwrapped1054)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1745 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1745 = nothing
                                    end
                                    deconstruct_result1051 = _t1745
                                    if !isnothing(deconstruct_result1051)
                                        unwrapped1052 = deconstruct_result1051
                                        pretty_ffi(pp, unwrapped1052)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1746 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1746 = nothing
                                        end
                                        deconstruct_result1049 = _t1746
                                        if !isnothing(deconstruct_result1049)
                                            unwrapped1050 = deconstruct_result1049
                                            pretty_atom(pp, unwrapped1050)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1747 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1747 = nothing
                                            end
                                            deconstruct_result1047 = _t1747
                                            if !isnothing(deconstruct_result1047)
                                                unwrapped1048 = deconstruct_result1047
                                                pretty_pragma(pp, unwrapped1048)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1748 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1748 = nothing
                                                end
                                                deconstruct_result1045 = _t1748
                                                if !isnothing(deconstruct_result1045)
                                                    unwrapped1046 = deconstruct_result1045
                                                    pretty_primitive(pp, unwrapped1046)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1749 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1749 = nothing
                                                    end
                                                    deconstruct_result1043 = _t1749
                                                    if !isnothing(deconstruct_result1043)
                                                        unwrapped1044 = deconstruct_result1043
                                                        pretty_rel_atom(pp, unwrapped1044)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1750 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1750 = nothing
                                                        end
                                                        deconstruct_result1041 = _t1750
                                                        if !isnothing(deconstruct_result1041)
                                                            unwrapped1042 = deconstruct_result1041
                                                            pretty_cast(pp, unwrapped1042)
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
    fields1068 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1069 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1074 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1074)
        write(pp, flat1074)
        return nothing
    else
        _dollar_dollar = msg
        _t1751 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1070 = (_t1751, _dollar_dollar.body.value,)
        unwrapped_fields1071 = fields1070
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1072 = unwrapped_fields1071[1]
        pretty_bindings(pp, field1072)
        newline(pp)
        field1073 = unwrapped_fields1071[2]
        pretty_formula(pp, field1073)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1080 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1080)
        write(pp, flat1080)
        return nothing
    else
        _dollar_dollar = msg
        fields1075 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1076 = fields1075
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1077 = unwrapped_fields1076[1]
        pretty_abstraction(pp, field1077)
        newline(pp)
        field1078 = unwrapped_fields1076[2]
        pretty_abstraction(pp, field1078)
        newline(pp)
        field1079 = unwrapped_fields1076[3]
        pretty_terms(pp, field1079)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1084 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1084)
        write(pp, flat1084)
        return nothing
    else
        fields1081 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1081)
            newline(pp)
            for (i1752, elem1082) in enumerate(fields1081)
                i1083 = i1752 - 1
                if (i1083 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1082)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1089 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1089)
        write(pp, flat1089)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1753 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1753 = nothing
        end
        deconstruct_result1087 = _t1753
        if !isnothing(deconstruct_result1087)
            unwrapped1088 = deconstruct_result1087
            pretty_var(pp, unwrapped1088)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1754 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1754 = nothing
            end
            deconstruct_result1085 = _t1754
            if !isnothing(deconstruct_result1085)
                unwrapped1086 = deconstruct_result1085
                pretty_value(pp, unwrapped1086)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1092 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        _dollar_dollar = msg
        fields1090 = _dollar_dollar.name
        unwrapped_fields1091 = fields1090
        write(pp, unwrapped_fields1091)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1118 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1118)
        write(pp, flat1118)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1755 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1755 = nothing
        end
        deconstruct_result1116 = _t1755
        if !isnothing(deconstruct_result1116)
            unwrapped1117 = deconstruct_result1116
            pretty_date(pp, unwrapped1117)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1756 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1756 = nothing
            end
            deconstruct_result1114 = _t1756
            if !isnothing(deconstruct_result1114)
                unwrapped1115 = deconstruct_result1114
                pretty_datetime(pp, unwrapped1115)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1757 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1757 = nothing
                end
                deconstruct_result1112 = _t1757
                if !isnothing(deconstruct_result1112)
                    unwrapped1113 = deconstruct_result1112
                    write(pp, format_string(pp, unwrapped1113))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1758 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1758 = nothing
                    end
                    deconstruct_result1110 = _t1758
                    if !isnothing(deconstruct_result1110)
                        unwrapped1111 = deconstruct_result1110
                        write(pp, format_int32(pp, unwrapped1111))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1759 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1759 = nothing
                        end
                        deconstruct_result1108 = _t1759
                        if !isnothing(deconstruct_result1108)
                            unwrapped1109 = deconstruct_result1108
                            write(pp, format_int(pp, unwrapped1109))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1760 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1760 = nothing
                            end
                            deconstruct_result1106 = _t1760
                            if !isnothing(deconstruct_result1106)
                                unwrapped1107 = deconstruct_result1106
                                write(pp, format_float32(pp, unwrapped1107))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1761 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1761 = nothing
                                end
                                deconstruct_result1104 = _t1761
                                if !isnothing(deconstruct_result1104)
                                    unwrapped1105 = deconstruct_result1104
                                    write(pp, format_float(pp, unwrapped1105))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1762 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1762 = nothing
                                    end
                                    deconstruct_result1102 = _t1762
                                    if !isnothing(deconstruct_result1102)
                                        unwrapped1103 = deconstruct_result1102
                                        write(pp, format_uint32(pp, unwrapped1103))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1763 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1763 = nothing
                                        end
                                        deconstruct_result1100 = _t1763
                                        if !isnothing(deconstruct_result1100)
                                            unwrapped1101 = deconstruct_result1100
                                            write(pp, format_uint128(pp, unwrapped1101))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1764 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1764 = nothing
                                            end
                                            deconstruct_result1098 = _t1764
                                            if !isnothing(deconstruct_result1098)
                                                unwrapped1099 = deconstruct_result1098
                                                write(pp, format_int128(pp, unwrapped1099))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1765 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1765 = nothing
                                                end
                                                deconstruct_result1096 = _t1765
                                                if !isnothing(deconstruct_result1096)
                                                    unwrapped1097 = deconstruct_result1096
                                                    write(pp, format_decimal(pp, unwrapped1097))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1766 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1766 = nothing
                                                    end
                                                    deconstruct_result1094 = _t1766
                                                    if !isnothing(deconstruct_result1094)
                                                        unwrapped1095 = deconstruct_result1094
                                                        pretty_boolean_value(pp, unwrapped1095)
                                                    else
                                                        fields1093 = msg
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
    flat1124 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1124)
        write(pp, flat1124)
        return nothing
    else
        _dollar_dollar = msg
        fields1119 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1120 = fields1119
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1121 = unwrapped_fields1120[1]
        write(pp, format_int(pp, field1121))
        newline(pp)
        field1122 = unwrapped_fields1120[2]
        write(pp, format_int(pp, field1122))
        newline(pp)
        field1123 = unwrapped_fields1120[3]
        write(pp, format_int(pp, field1123))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1135 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1135)
        write(pp, flat1135)
        return nothing
    else
        _dollar_dollar = msg
        fields1125 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1126 = fields1125
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1127 = unwrapped_fields1126[1]
        write(pp, format_int(pp, field1127))
        newline(pp)
        field1128 = unwrapped_fields1126[2]
        write(pp, format_int(pp, field1128))
        newline(pp)
        field1129 = unwrapped_fields1126[3]
        write(pp, format_int(pp, field1129))
        newline(pp)
        field1130 = unwrapped_fields1126[4]
        write(pp, format_int(pp, field1130))
        newline(pp)
        field1131 = unwrapped_fields1126[5]
        write(pp, format_int(pp, field1131))
        newline(pp)
        field1132 = unwrapped_fields1126[6]
        write(pp, format_int(pp, field1132))
        field1133 = unwrapped_fields1126[7]
        if !isnothing(field1133)
            newline(pp)
            opt_val1134 = field1133
            write(pp, format_int(pp, opt_val1134))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1140 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1140)
        write(pp, flat1140)
        return nothing
    else
        _dollar_dollar = msg
        fields1136 = _dollar_dollar.args
        unwrapped_fields1137 = fields1136
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1137)
            newline(pp)
            for (i1767, elem1138) in enumerate(unwrapped_fields1137)
                i1139 = i1767 - 1
                if (i1139 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1138)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1145 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1145)
        write(pp, flat1145)
        return nothing
    else
        _dollar_dollar = msg
        fields1141 = _dollar_dollar.args
        unwrapped_fields1142 = fields1141
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1142)
            newline(pp)
            for (i1768, elem1143) in enumerate(unwrapped_fields1142)
                i1144 = i1768 - 1
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

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1148 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1148)
        write(pp, flat1148)
        return nothing
    else
        _dollar_dollar = msg
        fields1146 = _dollar_dollar.arg
        unwrapped_fields1147 = fields1146
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1147)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1154 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1154)
        write(pp, flat1154)
        return nothing
    else
        _dollar_dollar = msg
        fields1149 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1150 = fields1149
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1151 = unwrapped_fields1150[1]
        pretty_name(pp, field1151)
        newline(pp)
        field1152 = unwrapped_fields1150[2]
        pretty_ffi_args(pp, field1152)
        newline(pp)
        field1153 = unwrapped_fields1150[3]
        pretty_terms(pp, field1153)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1156 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1156)
        write(pp, flat1156)
        return nothing
    else
        fields1155 = msg
        write(pp, ":")
        write(pp, fields1155)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1160 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1160)
        write(pp, flat1160)
        return nothing
    else
        fields1157 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1157)
            newline(pp)
            for (i1769, elem1158) in enumerate(fields1157)
                i1159 = i1769 - 1
                if (i1159 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1158)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1167 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        _dollar_dollar = msg
        fields1161 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1162 = fields1161
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1163 = unwrapped_fields1162[1]
        pretty_relation_id(pp, field1163)
        field1164 = unwrapped_fields1162[2]
        if !isempty(field1164)
            newline(pp)
            for (i1770, elem1165) in enumerate(field1164)
                i1166 = i1770 - 1
                if (i1166 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1165)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1174 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1174)
        write(pp, flat1174)
        return nothing
    else
        _dollar_dollar = msg
        fields1168 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1169 = fields1168
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1170 = unwrapped_fields1169[1]
        pretty_name(pp, field1170)
        field1171 = unwrapped_fields1169[2]
        if !isempty(field1171)
            newline(pp)
            for (i1771, elem1172) in enumerate(field1171)
                i1173 = i1771 - 1
                if (i1173 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1172)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1190 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1190)
        write(pp, flat1190)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1772 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1772 = nothing
        end
        guard_result1189 = _t1772
        if !isnothing(guard_result1189)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1773 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1773 = nothing
            end
            guard_result1188 = _t1773
            if !isnothing(guard_result1188)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1774 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1774 = nothing
                end
                guard_result1187 = _t1774
                if !isnothing(guard_result1187)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1775 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1775 = nothing
                    end
                    guard_result1186 = _t1775
                    if !isnothing(guard_result1186)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1776 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1776 = nothing
                        end
                        guard_result1185 = _t1776
                        if !isnothing(guard_result1185)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1777 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1777 = nothing
                            end
                            guard_result1184 = _t1777
                            if !isnothing(guard_result1184)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1778 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1778 = nothing
                                end
                                guard_result1183 = _t1778
                                if !isnothing(guard_result1183)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1779 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1779 = nothing
                                    end
                                    guard_result1182 = _t1779
                                    if !isnothing(guard_result1182)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1780 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1780 = nothing
                                        end
                                        guard_result1181 = _t1780
                                        if !isnothing(guard_result1181)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1175 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1176 = fields1175
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1177 = unwrapped_fields1176[1]
                                            pretty_name(pp, field1177)
                                            field1178 = unwrapped_fields1176[2]
                                            if !isempty(field1178)
                                                newline(pp)
                                                for (i1781, elem1179) in enumerate(field1178)
                                                    i1180 = i1781 - 1
                                                    if (i1180 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1179)
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
    flat1195 = try_flat(pp, msg, pretty_eq)
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
        fields1191 = _t1782
        unwrapped_fields1192 = fields1191
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1193 = unwrapped_fields1192[1]
        pretty_term(pp, field1193)
        newline(pp)
        field1194 = unwrapped_fields1192[2]
        pretty_term(pp, field1194)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1200 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1200)
        write(pp, flat1200)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1783 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1783 = nothing
        end
        fields1196 = _t1783
        unwrapped_fields1197 = fields1196
        write(pp, "(<")
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

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1205 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1205)
        write(pp, flat1205)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1784 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1784 = nothing
        end
        fields1201 = _t1784
        unwrapped_fields1202 = fields1201
        write(pp, "(<=")
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

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1210 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1210)
        write(pp, flat1210)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1785 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1785 = nothing
        end
        fields1206 = _t1785
        unwrapped_fields1207 = fields1206
        write(pp, "(>")
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

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1215 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1786 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1786 = nothing
        end
        fields1211 = _t1786
        unwrapped_fields1212 = fields1211
        write(pp, "(>=")
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

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1221 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1221)
        write(pp, flat1221)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1787 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1787 = nothing
        end
        fields1216 = _t1787
        unwrapped_fields1217 = fields1216
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1218 = unwrapped_fields1217[1]
        pretty_term(pp, field1218)
        newline(pp)
        field1219 = unwrapped_fields1217[2]
        pretty_term(pp, field1219)
        newline(pp)
        field1220 = unwrapped_fields1217[3]
        pretty_term(pp, field1220)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1227 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1227)
        write(pp, flat1227)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1788 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1788 = nothing
        end
        fields1222 = _t1788
        unwrapped_fields1223 = fields1222
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1224 = unwrapped_fields1223[1]
        pretty_term(pp, field1224)
        newline(pp)
        field1225 = unwrapped_fields1223[2]
        pretty_term(pp, field1225)
        newline(pp)
        field1226 = unwrapped_fields1223[3]
        pretty_term(pp, field1226)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1233 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1233)
        write(pp, flat1233)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1789 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1789 = nothing
        end
        fields1228 = _t1789
        unwrapped_fields1229 = fields1228
        write(pp, "(*")
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

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1239 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1239)
        write(pp, flat1239)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1790 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1790 = nothing
        end
        fields1234 = _t1790
        unwrapped_fields1235 = fields1234
        write(pp, "(/")
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

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1244 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1244)
        write(pp, flat1244)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1791 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1791 = nothing
        end
        deconstruct_result1242 = _t1791
        if !isnothing(deconstruct_result1242)
            unwrapped1243 = deconstruct_result1242
            pretty_specialized_value(pp, unwrapped1243)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1792 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1792 = nothing
            end
            deconstruct_result1240 = _t1792
            if !isnothing(deconstruct_result1240)
                unwrapped1241 = deconstruct_result1240
                pretty_term(pp, unwrapped1241)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1246 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1246)
        write(pp, flat1246)
        return nothing
    else
        fields1245 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1245)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1253 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        _dollar_dollar = msg
        fields1247 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1248 = fields1247
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1249 = unwrapped_fields1248[1]
        pretty_name(pp, field1249)
        field1250 = unwrapped_fields1248[2]
        if !isempty(field1250)
            newline(pp)
            for (i1793, elem1251) in enumerate(field1250)
                i1252 = i1793 - 1
                if (i1252 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1251)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1258 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1258)
        write(pp, flat1258)
        return nothing
    else
        _dollar_dollar = msg
        fields1254 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1255 = fields1254
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1256 = unwrapped_fields1255[1]
        pretty_term(pp, field1256)
        newline(pp)
        field1257 = unwrapped_fields1255[2]
        pretty_term(pp, field1257)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1262 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1262)
        write(pp, flat1262)
        return nothing
    else
        fields1259 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1259)
            newline(pp)
            for (i1794, elem1260) in enumerate(fields1259)
                i1261 = i1794 - 1
                if (i1261 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1260)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1269 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1269)
        write(pp, flat1269)
        return nothing
    else
        _dollar_dollar = msg
        fields1263 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1264 = fields1263
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1265 = unwrapped_fields1264[1]
        pretty_name(pp, field1265)
        field1266 = unwrapped_fields1264[2]
        if !isempty(field1266)
            newline(pp)
            for (i1795, elem1267) in enumerate(field1266)
                i1268 = i1795 - 1
                if (i1268 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1267)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1278 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1278)
        write(pp, flat1278)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1796 = _dollar_dollar.attrs
        else
            _t1796 = nothing
        end
        fields1270 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1796,)
        unwrapped_fields1271 = fields1270
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1272 = unwrapped_fields1271[1]
        if !isempty(field1272)
            newline(pp)
            for (i1797, elem1273) in enumerate(field1272)
                i1274 = i1797 - 1
                if (i1274 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1273)
            end
        end
        newline(pp)
        field1275 = unwrapped_fields1271[2]
        pretty_script(pp, field1275)
        field1276 = unwrapped_fields1271[3]
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

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1283 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1283)
        write(pp, flat1283)
        return nothing
    else
        _dollar_dollar = msg
        fields1279 = _dollar_dollar.constructs
        unwrapped_fields1280 = fields1279
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1280)
            newline(pp)
            for (i1798, elem1281) in enumerate(unwrapped_fields1280)
                i1282 = i1798 - 1
                if (i1282 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1281)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1288 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1288)
        write(pp, flat1288)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1799 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1799 = nothing
        end
        deconstruct_result1286 = _t1799
        if !isnothing(deconstruct_result1286)
            unwrapped1287 = deconstruct_result1286
            pretty_loop(pp, unwrapped1287)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1800 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1800 = nothing
            end
            deconstruct_result1284 = _t1800
            if !isnothing(deconstruct_result1284)
                unwrapped1285 = deconstruct_result1284
                pretty_instruction(pp, unwrapped1285)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1295 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1295)
        write(pp, flat1295)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1801 = _dollar_dollar.attrs
        else
            _t1801 = nothing
        end
        fields1289 = (_dollar_dollar.init, _dollar_dollar.body, _t1801,)
        unwrapped_fields1290 = fields1289
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1291 = unwrapped_fields1290[1]
        pretty_init(pp, field1291)
        newline(pp)
        field1292 = unwrapped_fields1290[2]
        pretty_script(pp, field1292)
        field1293 = unwrapped_fields1290[3]
        if !isnothing(field1293)
            newline(pp)
            opt_val1294 = field1293
            pretty_attrs(pp, opt_val1294)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1299 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1299)
        write(pp, flat1299)
        return nothing
    else
        fields1296 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1296)
            newline(pp)
            for (i1802, elem1297) in enumerate(fields1296)
                i1298 = i1802 - 1
                if (i1298 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1297)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1310 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1310)
        write(pp, flat1310)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1803 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1803 = nothing
        end
        deconstruct_result1308 = _t1803
        if !isnothing(deconstruct_result1308)
            unwrapped1309 = deconstruct_result1308
            pretty_assign(pp, unwrapped1309)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1804 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1804 = nothing
            end
            deconstruct_result1306 = _t1804
            if !isnothing(deconstruct_result1306)
                unwrapped1307 = deconstruct_result1306
                pretty_upsert(pp, unwrapped1307)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1805 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1805 = nothing
                end
                deconstruct_result1304 = _t1805
                if !isnothing(deconstruct_result1304)
                    unwrapped1305 = deconstruct_result1304
                    pretty_break(pp, unwrapped1305)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1806 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1806 = nothing
                    end
                    deconstruct_result1302 = _t1806
                    if !isnothing(deconstruct_result1302)
                        unwrapped1303 = deconstruct_result1302
                        pretty_monoid_def(pp, unwrapped1303)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1807 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1807 = nothing
                        end
                        deconstruct_result1300 = _t1807
                        if !isnothing(deconstruct_result1300)
                            unwrapped1301 = deconstruct_result1300
                            pretty_monus_def(pp, unwrapped1301)
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
    flat1317 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1317)
        write(pp, flat1317)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1808 = _dollar_dollar.attrs
        else
            _t1808 = nothing
        end
        fields1311 = (_dollar_dollar.name, _dollar_dollar.body, _t1808,)
        unwrapped_fields1312 = fields1311
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1313 = unwrapped_fields1312[1]
        pretty_relation_id(pp, field1313)
        newline(pp)
        field1314 = unwrapped_fields1312[2]
        pretty_abstraction(pp, field1314)
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

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1324 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1324)
        write(pp, flat1324)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1809 = _dollar_dollar.attrs
        else
            _t1809 = nothing
        end
        fields1318 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1809,)
        unwrapped_fields1319 = fields1318
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1320 = unwrapped_fields1319[1]
        pretty_relation_id(pp, field1320)
        newline(pp)
        field1321 = unwrapped_fields1319[2]
        pretty_abstraction_with_arity(pp, field1321)
        field1322 = unwrapped_fields1319[3]
        if !isnothing(field1322)
            newline(pp)
            opt_val1323 = field1322
            pretty_attrs(pp, opt_val1323)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1329 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1329)
        write(pp, flat1329)
        return nothing
    else
        _dollar_dollar = msg
        _t1810 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1325 = (_t1810, _dollar_dollar[1].value,)
        unwrapped_fields1326 = fields1325
        write(pp, "(")
        indent!(pp)
        field1327 = unwrapped_fields1326[1]
        pretty_bindings(pp, field1327)
        newline(pp)
        field1328 = unwrapped_fields1326[2]
        pretty_formula(pp, field1328)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1336 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1336)
        write(pp, flat1336)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1811 = _dollar_dollar.attrs
        else
            _t1811 = nothing
        end
        fields1330 = (_dollar_dollar.name, _dollar_dollar.body, _t1811,)
        unwrapped_fields1331 = fields1330
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1332 = unwrapped_fields1331[1]
        pretty_relation_id(pp, field1332)
        newline(pp)
        field1333 = unwrapped_fields1331[2]
        pretty_abstraction(pp, field1333)
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

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1344 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1344)
        write(pp, flat1344)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1812 = _dollar_dollar.attrs
        else
            _t1812 = nothing
        end
        fields1337 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1812,)
        unwrapped_fields1338 = fields1337
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1339 = unwrapped_fields1338[1]
        pretty_monoid(pp, field1339)
        newline(pp)
        field1340 = unwrapped_fields1338[2]
        pretty_relation_id(pp, field1340)
        newline(pp)
        field1341 = unwrapped_fields1338[3]
        pretty_abstraction_with_arity(pp, field1341)
        field1342 = unwrapped_fields1338[4]
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

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1353 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1353)
        write(pp, flat1353)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1813 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1813 = nothing
        end
        deconstruct_result1351 = _t1813
        if !isnothing(deconstruct_result1351)
            unwrapped1352 = deconstruct_result1351
            pretty_or_monoid(pp, unwrapped1352)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1814 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1814 = nothing
            end
            deconstruct_result1349 = _t1814
            if !isnothing(deconstruct_result1349)
                unwrapped1350 = deconstruct_result1349
                pretty_min_monoid(pp, unwrapped1350)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1815 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1815 = nothing
                end
                deconstruct_result1347 = _t1815
                if !isnothing(deconstruct_result1347)
                    unwrapped1348 = deconstruct_result1347
                    pretty_max_monoid(pp, unwrapped1348)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1816 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1816 = nothing
                    end
                    deconstruct_result1345 = _t1816
                    if !isnothing(deconstruct_result1345)
                        unwrapped1346 = deconstruct_result1345
                        pretty_sum_monoid(pp, unwrapped1346)
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
    fields1354 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1357 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1357)
        write(pp, flat1357)
        return nothing
    else
        _dollar_dollar = msg
        fields1355 = _dollar_dollar.var"#type"
        unwrapped_fields1356 = fields1355
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1356)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1360 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1360)
        write(pp, flat1360)
        return nothing
    else
        _dollar_dollar = msg
        fields1358 = _dollar_dollar.var"#type"
        unwrapped_fields1359 = fields1358
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1359)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1363 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1363)
        write(pp, flat1363)
        return nothing
    else
        _dollar_dollar = msg
        fields1361 = _dollar_dollar.var"#type"
        unwrapped_fields1362 = fields1361
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1362)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1371 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1371)
        write(pp, flat1371)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1817 = _dollar_dollar.attrs
        else
            _t1817 = nothing
        end
        fields1364 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1817,)
        unwrapped_fields1365 = fields1364
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1366 = unwrapped_fields1365[1]
        pretty_monoid(pp, field1366)
        newline(pp)
        field1367 = unwrapped_fields1365[2]
        pretty_relation_id(pp, field1367)
        newline(pp)
        field1368 = unwrapped_fields1365[3]
        pretty_abstraction_with_arity(pp, field1368)
        field1369 = unwrapped_fields1365[4]
        if !isnothing(field1369)
            newline(pp)
            opt_val1370 = field1369
            pretty_attrs(pp, opt_val1370)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1378 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1378)
        write(pp, flat1378)
        return nothing
    else
        _dollar_dollar = msg
        fields1372 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1373 = fields1372
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1374 = unwrapped_fields1373[1]
        pretty_relation_id(pp, field1374)
        newline(pp)
        field1375 = unwrapped_fields1373[2]
        pretty_abstraction(pp, field1375)
        newline(pp)
        field1376 = unwrapped_fields1373[3]
        pretty_functional_dependency_keys(pp, field1376)
        newline(pp)
        field1377 = unwrapped_fields1373[4]
        pretty_functional_dependency_values(pp, field1377)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1382 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1382)
        write(pp, flat1382)
        return nothing
    else
        fields1379 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1379)
            newline(pp)
            for (i1818, elem1380) in enumerate(fields1379)
                i1381 = i1818 - 1
                if (i1381 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1380)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1386 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1386)
        write(pp, flat1386)
        return nothing
    else
        fields1383 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1383)
            newline(pp)
            for (i1819, elem1384) in enumerate(fields1383)
                i1385 = i1819 - 1
                if (i1385 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1384)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1395 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1395)
        write(pp, flat1395)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1820 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1820 = nothing
        end
        deconstruct_result1393 = _t1820
        if !isnothing(deconstruct_result1393)
            unwrapped1394 = deconstruct_result1393
            pretty_edb(pp, unwrapped1394)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1821 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1821 = nothing
            end
            deconstruct_result1391 = _t1821
            if !isnothing(deconstruct_result1391)
                unwrapped1392 = deconstruct_result1391
                pretty_betree_relation(pp, unwrapped1392)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1822 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1822 = nothing
                end
                deconstruct_result1389 = _t1822
                if !isnothing(deconstruct_result1389)
                    unwrapped1390 = deconstruct_result1389
                    pretty_csv_data(pp, unwrapped1390)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1823 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1823 = nothing
                    end
                    deconstruct_result1387 = _t1823
                    if !isnothing(deconstruct_result1387)
                        unwrapped1388 = deconstruct_result1387
                        pretty_iceberg_data(pp, unwrapped1388)
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
    flat1401 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1401)
        write(pp, flat1401)
        return nothing
    else
        _dollar_dollar = msg
        fields1396 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1397 = fields1396
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1398 = unwrapped_fields1397[1]
        pretty_relation_id(pp, field1398)
        newline(pp)
        field1399 = unwrapped_fields1397[2]
        pretty_edb_path(pp, field1399)
        newline(pp)
        field1400 = unwrapped_fields1397[3]
        pretty_edb_types(pp, field1400)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1405 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1405)
        write(pp, flat1405)
        return nothing
    else
        fields1402 = msg
        write(pp, "[")
        indent!(pp)
        for (i1824, elem1403) in enumerate(fields1402)
            i1404 = i1824 - 1
            if (i1404 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1403))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1409 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1409)
        write(pp, flat1409)
        return nothing
    else
        fields1406 = msg
        write(pp, "[")
        indent!(pp)
        for (i1825, elem1407) in enumerate(fields1406)
            i1408 = i1825 - 1
            if (i1408 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1407)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1414 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1414)
        write(pp, flat1414)
        return nothing
    else
        _dollar_dollar = msg
        fields1410 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1411 = fields1410
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1412 = unwrapped_fields1411[1]
        pretty_relation_id(pp, field1412)
        newline(pp)
        field1413 = unwrapped_fields1411[2]
        pretty_betree_info(pp, field1413)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1420 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1420)
        write(pp, flat1420)
        return nothing
    else
        _dollar_dollar = msg
        _t1826 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1415 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1826,)
        unwrapped_fields1416 = fields1415
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1417 = unwrapped_fields1416[1]
        pretty_betree_info_key_types(pp, field1417)
        newline(pp)
        field1418 = unwrapped_fields1416[2]
        pretty_betree_info_value_types(pp, field1418)
        newline(pp)
        field1419 = unwrapped_fields1416[3]
        pretty_config_dict(pp, field1419)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1424 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1424)
        write(pp, flat1424)
        return nothing
    else
        fields1421 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1421)
            newline(pp)
            for (i1827, elem1422) in enumerate(fields1421)
                i1423 = i1827 - 1
                if (i1423 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1422)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1428 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1428)
        write(pp, flat1428)
        return nothing
    else
        fields1425 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1425)
            newline(pp)
            for (i1828, elem1426) in enumerate(fields1425)
                i1427 = i1828 - 1
                if (i1427 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1426)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1438 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1438)
        write(pp, flat1438)
        return nothing
    else
        _dollar_dollar = msg
        _t1829 = deconstruct_csv_data_columns_optional(pp, _dollar_dollar)
        _t1830 = deconstruct_csv_data_relations_optional(pp, _dollar_dollar)
        fields1429 = (_dollar_dollar.locator, _dollar_dollar.config, _t1829, _t1830, _dollar_dollar.asof,)
        unwrapped_fields1430 = fields1429
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1431 = unwrapped_fields1430[1]
        pretty_csvlocator(pp, field1431)
        newline(pp)
        field1432 = unwrapped_fields1430[2]
        pretty_csv_config(pp, field1432)
        field1433 = unwrapped_fields1430[3]
        if !isnothing(field1433)
            newline(pp)
            opt_val1434 = field1433
            pretty_gnf_columns(pp, opt_val1434)
        end
        field1435 = unwrapped_fields1430[4]
        if !isnothing(field1435)
            newline(pp)
            opt_val1436 = field1435
            pretty_target_relations(pp, opt_val1436)
        end
        newline(pp)
        field1437 = unwrapped_fields1430[5]
        pretty_csv_asof(pp, field1437)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1445 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1445)
        write(pp, flat1445)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1831 = _dollar_dollar.paths
        else
            _t1831 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1832 = String(copy(_dollar_dollar.inline_data))
        else
            _t1832 = nothing
        end
        fields1439 = (_t1831, _t1832,)
        unwrapped_fields1440 = fields1439
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1441 = unwrapped_fields1440[1]
        if !isnothing(field1441)
            newline(pp)
            opt_val1442 = field1441
            pretty_csv_locator_paths(pp, opt_val1442)
        end
        field1443 = unwrapped_fields1440[2]
        if !isnothing(field1443)
            newline(pp)
            opt_val1444 = field1443
            pretty_csv_locator_inline_data(pp, opt_val1444)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1449 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1449)
        write(pp, flat1449)
        return nothing
    else
        fields1446 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1446)
            newline(pp)
            for (i1833, elem1447) in enumerate(fields1446)
                i1448 = i1833 - 1
                if (i1448 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1447))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1451 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1451)
        write(pp, flat1451)
        return nothing
    else
        fields1450 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1450))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1457 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1457)
        write(pp, flat1457)
        return nothing
    else
        _dollar_dollar = msg
        _t1834 = deconstruct_csv_config(pp, _dollar_dollar)
        _t1835 = deconstruct_csv_storage_integration_optional(pp, _dollar_dollar)
        fields1452 = (_t1834, _t1835,)
        unwrapped_fields1453 = fields1452
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1454 = unwrapped_fields1453[1]
        pretty_config_dict(pp, field1454)
        field1455 = unwrapped_fields1453[2]
        if !isnothing(field1455)
            newline(pp)
            opt_val1456 = field1455
            pretty__storage_integration(pp, opt_val1456)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty__storage_integration(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat1459 = try_flat(pp, msg, pretty__storage_integration)
    if !isnothing(flat1459)
        write(pp, flat1459)
        return nothing
    else
        fields1458 = msg
        write(pp, "(storage_integration")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, fields1458)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1463 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1463)
        write(pp, flat1463)
        return nothing
    else
        fields1460 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1460)
            newline(pp)
            for (i1836, elem1461) in enumerate(fields1460)
                i1462 = i1836 - 1
                if (i1462 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1461)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1472 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1472)
        write(pp, flat1472)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1837 = _dollar_dollar.target_id
        else
            _t1837 = nothing
        end
        fields1464 = (_dollar_dollar.column_path, _t1837, _dollar_dollar.types,)
        unwrapped_fields1465 = fields1464
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1466 = unwrapped_fields1465[1]
        pretty_gnf_column_path(pp, field1466)
        field1467 = unwrapped_fields1465[2]
        if !isnothing(field1467)
            newline(pp)
            opt_val1468 = field1467
            pretty_relation_id(pp, opt_val1468)
        end
        newline(pp)
        write(pp, "[")
        field1469 = unwrapped_fields1465[3]
        for (i1838, elem1470) in enumerate(field1469)
            i1471 = i1838 - 1
            if (i1471 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1470)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1479 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1479)
        write(pp, flat1479)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1839 = _dollar_dollar[1]
        else
            _t1839 = nothing
        end
        deconstruct_result1477 = _t1839
        if !isnothing(deconstruct_result1477)
            unwrapped1478 = deconstruct_result1477
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1478))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1840 = _dollar_dollar
            else
                _t1840 = nothing
            end
            deconstruct_result1473 = _t1840
            if !isnothing(deconstruct_result1473)
                unwrapped1474 = deconstruct_result1473
                write(pp, "[")
                indent!(pp)
                for (i1841, elem1475) in enumerate(unwrapped1474)
                    i1476 = i1841 - 1
                    if (i1476 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1475))
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
    flat1484 = try_flat(pp, msg, pretty_target_relations)
    if !isnothing(flat1484)
        write(pp, flat1484)
        return nothing
    else
        _dollar_dollar = msg
        fields1480 = (_dollar_dollar.keys, _dollar_dollar,)
        unwrapped_fields1481 = fields1480
        write(pp, "(relations")
        indent_sexp!(pp)
        newline(pp)
        field1482 = unwrapped_fields1481[1]
        pretty_relation_keys(pp, field1482)
        newline(pp)
        field1483 = unwrapped_fields1481[2]
        pretty_relation_body(pp, field1483)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_keys(pp::PrettyPrinter, msg::Vector{Proto.NamedColumn})
    flat1488 = try_flat(pp, msg, pretty_relation_keys)
    if !isnothing(flat1488)
        write(pp, flat1488)
        return nothing
    else
        fields1485 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1485)
            newline(pp)
            for (i1842, elem1486) in enumerate(fields1485)
                i1487 = i1842 - 1
                if (i1487 > 0)
                    newline(pp)
                end
                pretty_named_column(pp, elem1486)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_named_column(pp::PrettyPrinter, msg::Proto.NamedColumn)
    flat1493 = try_flat(pp, msg, pretty_named_column)
    if !isnothing(flat1493)
        write(pp, flat1493)
        return nothing
    else
        _dollar_dollar = msg
        fields1489 = (_dollar_dollar.name, _dollar_dollar.var"#type",)
        unwrapped_fields1490 = fields1489
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1491 = unwrapped_fields1490[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1491))
        newline(pp)
        field1492 = unwrapped_fields1490[2]
        pretty_type(pp, field1492)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_body(pp::PrettyPrinter, msg::Proto.TargetRelations)
    flat1500 = try_flat(pp, msg, pretty_relation_body)
    if !isnothing(flat1500)
        write(pp, flat1500)
        return nothing
    else
        _dollar_dollar = msg
        if (isempty(_dollar_dollar.inserts) && isempty(_dollar_dollar.deletes))
            _t1843 = _dollar_dollar.relations
        else
            _t1843 = nothing
        end
        deconstruct_result1498 = _t1843
        if !isnothing(deconstruct_result1498)
            unwrapped1499 = deconstruct_result1498
            pretty_non_cdc_relations(pp, unwrapped1499)
        else
            _dollar_dollar = msg
            if !(isempty(_dollar_dollar.inserts) && isempty(_dollar_dollar.deletes))
                _t1844 = (_dollar_dollar.inserts, _dollar_dollar.deletes,)
            else
                _t1844 = nothing
            end
            deconstruct_result1494 = _t1844
            if !isnothing(deconstruct_result1494)
                unwrapped1495 = deconstruct_result1494
                field1496 = unwrapped1495[1]
                pretty_cdc_inserts(pp, field1496)
                write(pp, " ")
                field1497 = unwrapped1495[2]
                pretty_cdc_deletes(pp, field1497)
            else
                throw(ParseError("No matching rule for relation_body"))
            end
        end
    end
    return nothing
end

function pretty_non_cdc_relations(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1504 = try_flat(pp, msg, pretty_non_cdc_relations)
    if !isnothing(flat1504)
        write(pp, flat1504)
        return nothing
    else
        fields1501 = msg
        for (i1845, elem1502) in enumerate(fields1501)
            i1503 = i1845 - 1
            if (i1503 > 0)
                newline(pp)
            end
            pretty_target_relation(pp, elem1502)
        end
    end
    return nothing
end

function pretty_target_relation(pp::PrettyPrinter, msg::Proto.TargetRelation)
    flat1511 = try_flat(pp, msg, pretty_target_relation)
    if !isnothing(flat1511)
        write(pp, flat1511)
        return nothing
    else
        _dollar_dollar = msg
        fields1505 = (_dollar_dollar.target_id, _dollar_dollar.values,)
        unwrapped_fields1506 = fields1505
        write(pp, "(relation")
        indent_sexp!(pp)
        newline(pp)
        field1507 = unwrapped_fields1506[1]
        pretty_relation_id(pp, field1507)
        field1508 = unwrapped_fields1506[2]
        if !isempty(field1508)
            newline(pp)
            for (i1846, elem1509) in enumerate(field1508)
                i1510 = i1846 - 1
                if (i1510 > 0)
                    newline(pp)
                end
                pretty_named_column(pp, elem1509)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_inserts(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1515 = try_flat(pp, msg, pretty_cdc_inserts)
    if !isnothing(flat1515)
        write(pp, flat1515)
        return nothing
    else
        fields1512 = msg
        write(pp, "(inserts")
        indent_sexp!(pp)
        if !isempty(fields1512)
            newline(pp)
            for (i1847, elem1513) in enumerate(fields1512)
                i1514 = i1847 - 1
                if (i1514 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1513)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cdc_deletes(pp::PrettyPrinter, msg::Vector{Proto.TargetRelation})
    flat1519 = try_flat(pp, msg, pretty_cdc_deletes)
    if !isnothing(flat1519)
        write(pp, flat1519)
        return nothing
    else
        fields1516 = msg
        write(pp, "(deletes")
        indent_sexp!(pp)
        if !isempty(fields1516)
            newline(pp)
            for (i1848, elem1517) in enumerate(fields1516)
                i1518 = i1848 - 1
                if (i1518 > 0)
                    newline(pp)
                end
                pretty_target_relation(pp, elem1517)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1521 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1521)
        write(pp, flat1521)
        return nothing
    else
        fields1520 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1520))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1532 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1532)
        write(pp, flat1532)
        return nothing
    else
        _dollar_dollar = msg
        _t1849 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1850 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1522 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1849, _t1850, _dollar_dollar.returns_delta,)
        unwrapped_fields1523 = fields1522
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1524 = unwrapped_fields1523[1]
        pretty_iceberg_locator(pp, field1524)
        newline(pp)
        field1525 = unwrapped_fields1523[2]
        pretty_iceberg_catalog_config(pp, field1525)
        newline(pp)
        field1526 = unwrapped_fields1523[3]
        pretty_gnf_columns(pp, field1526)
        field1527 = unwrapped_fields1523[4]
        if !isnothing(field1527)
            newline(pp)
            opt_val1528 = field1527
            pretty_iceberg_from_snapshot(pp, opt_val1528)
        end
        field1529 = unwrapped_fields1523[5]
        if !isnothing(field1529)
            newline(pp)
            opt_val1530 = field1529
            pretty_iceberg_to_snapshot(pp, opt_val1530)
        end
        newline(pp)
        field1531 = unwrapped_fields1523[6]
        pretty_boolean_value(pp, field1531)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1538 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1538)
        write(pp, flat1538)
        return nothing
    else
        _dollar_dollar = msg
        fields1533 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1534 = fields1533
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1535 = unwrapped_fields1534[1]
        pretty_iceberg_locator_table_name(pp, field1535)
        newline(pp)
        field1536 = unwrapped_fields1534[2]
        pretty_iceberg_locator_namespace(pp, field1536)
        newline(pp)
        field1537 = unwrapped_fields1534[3]
        pretty_iceberg_locator_warehouse(pp, field1537)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1540 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1540)
        write(pp, flat1540)
        return nothing
    else
        fields1539 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1539))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1544 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1544)
        write(pp, flat1544)
        return nothing
    else
        fields1541 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1541)
            newline(pp)
            for (i1851, elem1542) in enumerate(fields1541)
                i1543 = i1851 - 1
                if (i1543 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1542))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1546 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1546)
        write(pp, flat1546)
        return nothing
    else
        fields1545 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1545))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1554 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1554)
        write(pp, flat1554)
        return nothing
    else
        _dollar_dollar = msg
        _t1852 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1547 = (_dollar_dollar.catalog_uri, _t1852, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1548 = fields1547
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1549 = unwrapped_fields1548[1]
        pretty_iceberg_catalog_uri(pp, field1549)
        field1550 = unwrapped_fields1548[2]
        if !isnothing(field1550)
            newline(pp)
            opt_val1551 = field1550
            pretty_iceberg_catalog_config_scope(pp, opt_val1551)
        end
        newline(pp)
        field1552 = unwrapped_fields1548[3]
        pretty_iceberg_properties(pp, field1552)
        newline(pp)
        field1553 = unwrapped_fields1548[4]
        pretty_iceberg_auth_properties(pp, field1553)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1556 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1556)
        write(pp, flat1556)
        return nothing
    else
        fields1555 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1555))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1558 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1558)
        write(pp, flat1558)
        return nothing
    else
        fields1557 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1557))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1562 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1562)
        write(pp, flat1562)
        return nothing
    else
        fields1559 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1559)
            newline(pp)
            for (i1853, elem1560) in enumerate(fields1559)
                i1561 = i1853 - 1
                if (i1561 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1560)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1567 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1567)
        write(pp, flat1567)
        return nothing
    else
        _dollar_dollar = msg
        fields1563 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1564 = fields1563
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1565 = unwrapped_fields1564[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1565))
        newline(pp)
        field1566 = unwrapped_fields1564[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1566))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1571 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1571)
        write(pp, flat1571)
        return nothing
    else
        fields1568 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1568)
            newline(pp)
            for (i1854, elem1569) in enumerate(fields1568)
                i1570 = i1854 - 1
                if (i1570 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1569)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1576 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1576)
        write(pp, flat1576)
        return nothing
    else
        _dollar_dollar = msg
        _t1855 = mask_secret_value(pp, _dollar_dollar)
        fields1572 = (_dollar_dollar[1], _t1855,)
        unwrapped_fields1573 = fields1572
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1574 = unwrapped_fields1573[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1574))
        newline(pp)
        field1575 = unwrapped_fields1573[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1575))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1578 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1578)
        write(pp, flat1578)
        return nothing
    else
        fields1577 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1577))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1580 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1580)
        write(pp, flat1580)
        return nothing
    else
        fields1579 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1579))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1583 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1583)
        write(pp, flat1583)
        return nothing
    else
        _dollar_dollar = msg
        fields1581 = _dollar_dollar.fragment_id
        unwrapped_fields1582 = fields1581
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1582)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1588 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1588)
        write(pp, flat1588)
        return nothing
    else
        _dollar_dollar = msg
        fields1584 = _dollar_dollar.relations
        unwrapped_fields1585 = fields1584
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1585)
            newline(pp)
            for (i1856, elem1586) in enumerate(unwrapped_fields1585)
                i1587 = i1856 - 1
                if (i1587 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1586)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1595 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1595)
        write(pp, flat1595)
        return nothing
    else
        _dollar_dollar = msg
        fields1589 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1590 = fields1589
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1591 = unwrapped_fields1590[1]
        pretty_edb_path(pp, field1591)
        field1592 = unwrapped_fields1590[2]
        if !isempty(field1592)
            newline(pp)
            for (i1857, elem1593) in enumerate(field1592)
                i1594 = i1857 - 1
                if (i1594 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1593)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1600 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1600)
        write(pp, flat1600)
        return nothing
    else
        _dollar_dollar = msg
        fields1596 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1597 = fields1596
        field1598 = unwrapped_fields1597[1]
        pretty_edb_path(pp, field1598)
        write(pp, " ")
        field1599 = unwrapped_fields1597[2]
        pretty_relation_id(pp, field1599)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1604 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1604)
        write(pp, flat1604)
        return nothing
    else
        fields1601 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1601)
            newline(pp)
            for (i1858, elem1602) in enumerate(fields1601)
                i1603 = i1858 - 1
                if (i1603 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1602)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1615 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1615)
        write(pp, flat1615)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1859 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1859 = nothing
        end
        deconstruct_result1613 = _t1859
        if !isnothing(deconstruct_result1613)
            unwrapped1614 = deconstruct_result1613
            pretty_demand(pp, unwrapped1614)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1860 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1860 = nothing
            end
            deconstruct_result1611 = _t1860
            if !isnothing(deconstruct_result1611)
                unwrapped1612 = deconstruct_result1611
                pretty_output(pp, unwrapped1612)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1861 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1861 = nothing
                end
                deconstruct_result1609 = _t1861
                if !isnothing(deconstruct_result1609)
                    unwrapped1610 = deconstruct_result1609
                    pretty_what_if(pp, unwrapped1610)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1862 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1862 = nothing
                    end
                    deconstruct_result1607 = _t1862
                    if !isnothing(deconstruct_result1607)
                        unwrapped1608 = deconstruct_result1607
                        pretty_abort(pp, unwrapped1608)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1863 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1863 = nothing
                        end
                        deconstruct_result1605 = _t1863
                        if !isnothing(deconstruct_result1605)
                            unwrapped1606 = deconstruct_result1605
                            pretty_export(pp, unwrapped1606)
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
    flat1618 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1618)
        write(pp, flat1618)
        return nothing
    else
        _dollar_dollar = msg
        fields1616 = _dollar_dollar.relation_id
        unwrapped_fields1617 = fields1616
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1617)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1623 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1623)
        write(pp, flat1623)
        return nothing
    else
        _dollar_dollar = msg
        fields1619 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1620 = fields1619
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1621 = unwrapped_fields1620[1]
        pretty_name(pp, field1621)
        newline(pp)
        field1622 = unwrapped_fields1620[2]
        pretty_relation_id(pp, field1622)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1628 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1628)
        write(pp, flat1628)
        return nothing
    else
        _dollar_dollar = msg
        fields1624 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1625 = fields1624
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1626 = unwrapped_fields1625[1]
        pretty_name(pp, field1626)
        newline(pp)
        field1627 = unwrapped_fields1625[2]
        pretty_epoch(pp, field1627)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1634 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1634)
        write(pp, flat1634)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1864 = _dollar_dollar.name
        else
            _t1864 = nothing
        end
        fields1629 = (_t1864, _dollar_dollar.relation_id,)
        unwrapped_fields1630 = fields1629
        write(pp, "(abort")
        indent_sexp!(pp)
        field1631 = unwrapped_fields1630[1]
        if !isnothing(field1631)
            newline(pp)
            opt_val1632 = field1631
            pretty_name(pp, opt_val1632)
        end
        newline(pp)
        field1633 = unwrapped_fields1630[2]
        pretty_relation_id(pp, field1633)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1639 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1639)
        write(pp, flat1639)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1865 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1865 = nothing
        end
        deconstruct_result1637 = _t1865
        if !isnothing(deconstruct_result1637)
            unwrapped1638 = deconstruct_result1637
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1638)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1866 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1866 = nothing
            end
            deconstruct_result1635 = _t1866
            if !isnothing(deconstruct_result1635)
                unwrapped1636 = deconstruct_result1635
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1636)
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
    flat1650 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1650)
        write(pp, flat1650)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1867 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1867 = nothing
        end
        deconstruct_result1645 = _t1867
        if !isnothing(deconstruct_result1645)
            unwrapped1646 = deconstruct_result1645
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1647 = unwrapped1646[1]
            pretty_export_csv_path(pp, field1647)
            newline(pp)
            field1648 = unwrapped1646[2]
            pretty_export_csv_source(pp, field1648)
            newline(pp)
            field1649 = unwrapped1646[3]
            pretty_csv_config(pp, field1649)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1869 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1868 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1869,)
            else
                _t1868 = nothing
            end
            deconstruct_result1640 = _t1868
            if !isnothing(deconstruct_result1640)
                unwrapped1641 = deconstruct_result1640
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1642 = unwrapped1641[1]
                pretty_export_csv_path(pp, field1642)
                newline(pp)
                field1643 = unwrapped1641[2]
                pretty_export_csv_columns_list(pp, field1643)
                newline(pp)
                field1644 = unwrapped1641[3]
                pretty_config_dict(pp, field1644)
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
    flat1652 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1652)
        write(pp, flat1652)
        return nothing
    else
        fields1651 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1651))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1659 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1659)
        write(pp, flat1659)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1870 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1870 = nothing
        end
        deconstruct_result1655 = _t1870
        if !isnothing(deconstruct_result1655)
            unwrapped1656 = deconstruct_result1655
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1656)
                newline(pp)
                for (i1871, elem1657) in enumerate(unwrapped1656)
                    i1658 = i1871 - 1
                    if (i1658 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1657)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1872 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1872 = nothing
            end
            deconstruct_result1653 = _t1872
            if !isnothing(deconstruct_result1653)
                unwrapped1654 = deconstruct_result1653
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1654)
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
    flat1664 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1664)
        write(pp, flat1664)
        return nothing
    else
        _dollar_dollar = msg
        fields1660 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1661 = fields1660
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1662 = unwrapped_fields1661[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1662))
        newline(pp)
        field1663 = unwrapped_fields1661[2]
        pretty_relation_id(pp, field1663)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1668 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1668)
        write(pp, flat1668)
        return nothing
    else
        fields1665 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1665)
            newline(pp)
            for (i1873, elem1666) in enumerate(fields1665)
                i1667 = i1873 - 1
                if (i1667 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1666)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1677 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1677)
        write(pp, flat1677)
        return nothing
    else
        _dollar_dollar = msg
        _t1874 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1669 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1874,)
        unwrapped_fields1670 = fields1669
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1671 = unwrapped_fields1670[1]
        pretty_iceberg_locator(pp, field1671)
        newline(pp)
        field1672 = unwrapped_fields1670[2]
        pretty_iceberg_catalog_config(pp, field1672)
        newline(pp)
        field1673 = unwrapped_fields1670[3]
        pretty_export_iceberg_table_def(pp, field1673)
        newline(pp)
        field1674 = unwrapped_fields1670[4]
        pretty_iceberg_table_properties(pp, field1674)
        field1675 = unwrapped_fields1670[5]
        if !isnothing(field1675)
            newline(pp)
            opt_val1676 = field1675
            pretty_config_dict(pp, opt_val1676)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1679 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1679)
        write(pp, flat1679)
        return nothing
    else
        fields1678 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1678)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1683 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1683)
        write(pp, flat1683)
        return nothing
    else
        fields1680 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1680)
            newline(pp)
            for (i1875, elem1681) in enumerate(fields1680)
                i1682 = i1875 - 1
                if (i1682 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1681)
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
    for (i1929, _rid) in enumerate(msg.ids)
        _idx = i1929 - 1
        newline(pp)
        write(pp, "(")
        _t1930 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1930)
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
    for (i1931, _elem) in enumerate(msg.keys)
        _idx = i1931 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1932, _elem) in enumerate(msg.values)
        _idx = i1932 - 1
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
    for (i1933, _elem) in enumerate(msg.columns)
        _idx = i1933 - 1
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
