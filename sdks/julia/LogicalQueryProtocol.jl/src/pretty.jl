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
    _t1807 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1807
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1808 = Proto.Value(value=OneOf(:int_value, v))
    return _t1808
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1809 = Proto.Value(value=OneOf(:float_value, v))
    return _t1809
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1810 = Proto.Value(value=OneOf(:string_value, v))
    return _t1810
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1811 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1811
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1812 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1812
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1813 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1813,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1814 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1814,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1815 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1815,))
            end
        end
    end
    _t1816 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1816,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1817 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1817,))
    _t1818 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1818,))
    if msg.new_line != ""
        _t1819 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1819,))
    end
    _t1820 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1820,))
    _t1821 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1821,))
    _t1822 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1822,))
    if msg.comment != ""
        _t1823 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1823,))
    end
    for missing_string in msg.missing_strings
        _t1824 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1824,))
    end
    _t1825 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1825,))
    _t1826 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1826,))
    _t1827 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1827,))
    if msg.partition_size_mb != 0
        _t1828 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1828,))
    end
    return sort(result)
end

function deconstruct_csv_storage_integration_optional(pp::PrettyPrinter, msg::Proto.CSVConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    if !_has_proto_field(msg, Symbol("storage_integration"))
        return nothing
    else
        _t1829 = nothing
    end
    si = msg.storage_integration
    result = Tuple{String, Proto.Value}[]
    if si.provider != ""
        _t1830 = _make_value_string(pp, si.provider)
        push!(result, ("provider", _t1830,))
    end
    if si.azure_sas_token != ""
        _t1831 = _make_value_string(pp, "***")
        push!(result, ("azure_sas_token", _t1831,))
    end
    if si.s3_region != ""
        _t1832 = _make_value_string(pp, si.s3_region)
        push!(result, ("s3_region", _t1832,))
    end
    if si.s3_access_key_id != ""
        _t1833 = _make_value_string(pp, "***")
        push!(result, ("s3_access_key_id", _t1833,))
    end
    if si.s3_secret_access_key != ""
        _t1834 = _make_value_string(pp, "***")
        push!(result, ("s3_secret_access_key", _t1834,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1835 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1835,))
    _t1836 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1836,))
    _t1837 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1837,))
    _t1838 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1838,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1839 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1839,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1840 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1840,))
        end
    end
    _t1841 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1841,))
    _t1842 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1842,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1843 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1843,))
    end
    if !isnothing(msg.compression)
        _t1844 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1844,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1845 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1845,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1846 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1846,))
    end
    if !isnothing(msg.syntax_delim)
        _t1847 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1847,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1848 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1848,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1849 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1849,))
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
        _t1850 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1851 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1852 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1853 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1853,))
    end
    if msg.target_file_size_bytes != 0
        _t1854 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1854,))
    end
    if msg.compression != ""
        _t1855 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1855,))
    end
    if length(result) == 0
        return nothing
    else
        _t1856 = nothing
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
        _t1857 = nothing
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
    flat820 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat820)
        write(pp, flat820)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1622 = _dollar_dollar.configure
        else
            _t1622 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1623 = _dollar_dollar.sync
        else
            _t1623 = nothing
        end
        fields811 = (_t1622, _t1623, _dollar_dollar.epochs,)
        unwrapped_fields812 = fields811
        write(pp, "(transaction")
        indent_sexp!(pp)
        field813 = unwrapped_fields812[1]
        if !isnothing(field813)
            newline(pp)
            opt_val814 = field813
            pretty_configure(pp, opt_val814)
        end
        field815 = unwrapped_fields812[2]
        if !isnothing(field815)
            newline(pp)
            opt_val816 = field815
            pretty_sync(pp, opt_val816)
        end
        field817 = unwrapped_fields812[3]
        if !isempty(field817)
            newline(pp)
            for (i1624, elem818) in enumerate(field817)
                i819 = i1624 - 1
                if (i819 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem818)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat823 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat823)
        write(pp, flat823)
        return nothing
    else
        _dollar_dollar = msg
        _t1625 = deconstruct_configure(pp, _dollar_dollar)
        fields821 = _t1625
        unwrapped_fields822 = fields821
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields822)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat827 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat827)
        write(pp, flat827)
        return nothing
    else
        fields824 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields824)
            newline(pp)
            for (i1626, elem825) in enumerate(fields824)
                i826 = i1626 - 1
                if (i826 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem825)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat832 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat832)
        write(pp, flat832)
        return nothing
    else
        _dollar_dollar = msg
        fields828 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields829 = fields828
        write(pp, ":")
        field830 = unwrapped_fields829[1]
        write(pp, field830)
        write(pp, " ")
        field831 = unwrapped_fields829[2]
        pretty_raw_value(pp, field831)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat858 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat858)
        write(pp, flat858)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1627 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1627 = nothing
        end
        deconstruct_result856 = _t1627
        if !isnothing(deconstruct_result856)
            unwrapped857 = deconstruct_result856
            pretty_raw_date(pp, unwrapped857)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1628 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1628 = nothing
            end
            deconstruct_result854 = _t1628
            if !isnothing(deconstruct_result854)
                unwrapped855 = deconstruct_result854
                pretty_raw_datetime(pp, unwrapped855)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1629 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1629 = nothing
                end
                deconstruct_result852 = _t1629
                if !isnothing(deconstruct_result852)
                    unwrapped853 = deconstruct_result852
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped853))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1630 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1630 = nothing
                    end
                    deconstruct_result850 = _t1630
                    if !isnothing(deconstruct_result850)
                        unwrapped851 = deconstruct_result850
                        write(pp, (string(Int64(unwrapped851)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1631 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1631 = nothing
                        end
                        deconstruct_result848 = _t1631
                        if !isnothing(deconstruct_result848)
                            unwrapped849 = deconstruct_result848
                            write(pp, string(unwrapped849))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1632 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1632 = nothing
                            end
                            deconstruct_result846 = _t1632
                            if !isnothing(deconstruct_result846)
                                unwrapped847 = deconstruct_result846
                                write(pp, format_float32_literal(unwrapped847))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1633 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1633 = nothing
                                end
                                deconstruct_result844 = _t1633
                                if !isnothing(deconstruct_result844)
                                    unwrapped845 = deconstruct_result844
                                    write(pp, lowercase(string(unwrapped845)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1634 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1634 = nothing
                                    end
                                    deconstruct_result842 = _t1634
                                    if !isnothing(deconstruct_result842)
                                        unwrapped843 = deconstruct_result842
                                        write(pp, (string(Int64(unwrapped843)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1635 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1635 = nothing
                                        end
                                        deconstruct_result840 = _t1635
                                        if !isnothing(deconstruct_result840)
                                            unwrapped841 = deconstruct_result840
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped841))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1636 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1636 = nothing
                                            end
                                            deconstruct_result838 = _t1636
                                            if !isnothing(deconstruct_result838)
                                                unwrapped839 = deconstruct_result838
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped839))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1637 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1637 = nothing
                                                end
                                                deconstruct_result836 = _t1637
                                                if !isnothing(deconstruct_result836)
                                                    unwrapped837 = deconstruct_result836
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped837))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1638 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1638 = nothing
                                                    end
                                                    deconstruct_result834 = _t1638
                                                    if !isnothing(deconstruct_result834)
                                                        unwrapped835 = deconstruct_result834
                                                        pretty_boolean_value(pp, unwrapped835)
                                                    else
                                                        fields833 = msg
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
    flat864 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat864)
        write(pp, flat864)
        return nothing
    else
        _dollar_dollar = msg
        fields859 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields860 = fields859
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field861 = unwrapped_fields860[1]
        write(pp, string(field861))
        newline(pp)
        field862 = unwrapped_fields860[2]
        write(pp, string(field862))
        newline(pp)
        field863 = unwrapped_fields860[3]
        write(pp, string(field863))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat875 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat875)
        write(pp, flat875)
        return nothing
    else
        _dollar_dollar = msg
        fields865 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields866 = fields865
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field867 = unwrapped_fields866[1]
        write(pp, string(field867))
        newline(pp)
        field868 = unwrapped_fields866[2]
        write(pp, string(field868))
        newline(pp)
        field869 = unwrapped_fields866[3]
        write(pp, string(field869))
        newline(pp)
        field870 = unwrapped_fields866[4]
        write(pp, string(field870))
        newline(pp)
        field871 = unwrapped_fields866[5]
        write(pp, string(field871))
        newline(pp)
        field872 = unwrapped_fields866[6]
        write(pp, string(field872))
        field873 = unwrapped_fields866[7]
        if !isnothing(field873)
            newline(pp)
            opt_val874 = field873
            write(pp, string(opt_val874))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1639 = ()
    else
        _t1639 = nothing
    end
    deconstruct_result878 = _t1639
    if !isnothing(deconstruct_result878)
        unwrapped879 = deconstruct_result878
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1640 = ()
        else
            _t1640 = nothing
        end
        deconstruct_result876 = _t1640
        if !isnothing(deconstruct_result876)
            unwrapped877 = deconstruct_result876
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat884 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat884)
        write(pp, flat884)
        return nothing
    else
        _dollar_dollar = msg
        fields880 = _dollar_dollar.fragments
        unwrapped_fields881 = fields880
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields881)
            newline(pp)
            for (i1641, elem882) in enumerate(unwrapped_fields881)
                i883 = i1641 - 1
                if (i883 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem882)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat887 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat887)
        write(pp, flat887)
        return nothing
    else
        _dollar_dollar = msg
        fields885 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields886 = fields885
        write(pp, ":")
        write(pp, unwrapped_fields886)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat894 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat894)
        write(pp, flat894)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1642 = _dollar_dollar.writes
        else
            _t1642 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1643 = _dollar_dollar.reads
        else
            _t1643 = nothing
        end
        fields888 = (_t1642, _t1643,)
        unwrapped_fields889 = fields888
        write(pp, "(epoch")
        indent_sexp!(pp)
        field890 = unwrapped_fields889[1]
        if !isnothing(field890)
            newline(pp)
            opt_val891 = field890
            pretty_epoch_writes(pp, opt_val891)
        end
        field892 = unwrapped_fields889[2]
        if !isnothing(field892)
            newline(pp)
            opt_val893 = field892
            pretty_epoch_reads(pp, opt_val893)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat898 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat898)
        write(pp, flat898)
        return nothing
    else
        fields895 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields895)
            newline(pp)
            for (i1644, elem896) in enumerate(fields895)
                i897 = i1644 - 1
                if (i897 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem896)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat907 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat907)
        write(pp, flat907)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1645 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1645 = nothing
        end
        deconstruct_result905 = _t1645
        if !isnothing(deconstruct_result905)
            unwrapped906 = deconstruct_result905
            pretty_define(pp, unwrapped906)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1646 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1646 = nothing
            end
            deconstruct_result903 = _t1646
            if !isnothing(deconstruct_result903)
                unwrapped904 = deconstruct_result903
                pretty_undefine(pp, unwrapped904)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1647 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1647 = nothing
                end
                deconstruct_result901 = _t1647
                if !isnothing(deconstruct_result901)
                    unwrapped902 = deconstruct_result901
                    pretty_context(pp, unwrapped902)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1648 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1648 = nothing
                    end
                    deconstruct_result899 = _t1648
                    if !isnothing(deconstruct_result899)
                        unwrapped900 = deconstruct_result899
                        pretty_snapshot(pp, unwrapped900)
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
    flat910 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat910)
        write(pp, flat910)
        return nothing
    else
        _dollar_dollar = msg
        fields908 = _dollar_dollar.fragment
        unwrapped_fields909 = fields908
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields909)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat917 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat917)
        write(pp, flat917)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields911 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields912 = fields911
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field913 = unwrapped_fields912[1]
        pretty_new_fragment_id(pp, field913)
        field914 = unwrapped_fields912[2]
        if !isempty(field914)
            newline(pp)
            for (i1649, elem915) in enumerate(field914)
                i916 = i1649 - 1
                if (i916 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem915)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat919 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat919)
        write(pp, flat919)
        return nothing
    else
        fields918 = msg
        pretty_fragment_id(pp, fields918)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat928 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat928)
        write(pp, flat928)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1650 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1650 = nothing
        end
        deconstruct_result926 = _t1650
        if !isnothing(deconstruct_result926)
            unwrapped927 = deconstruct_result926
            pretty_def(pp, unwrapped927)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1651 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1651 = nothing
            end
            deconstruct_result924 = _t1651
            if !isnothing(deconstruct_result924)
                unwrapped925 = deconstruct_result924
                pretty_algorithm(pp, unwrapped925)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1652 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1652 = nothing
                end
                deconstruct_result922 = _t1652
                if !isnothing(deconstruct_result922)
                    unwrapped923 = deconstruct_result922
                    pretty_constraint(pp, unwrapped923)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1653 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1653 = nothing
                    end
                    deconstruct_result920 = _t1653
                    if !isnothing(deconstruct_result920)
                        unwrapped921 = deconstruct_result920
                        pretty_data(pp, unwrapped921)
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
    flat935 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat935)
        write(pp, flat935)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1654 = _dollar_dollar.attrs
        else
            _t1654 = nothing
        end
        fields929 = (_dollar_dollar.name, _dollar_dollar.body, _t1654,)
        unwrapped_fields930 = fields929
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field931 = unwrapped_fields930[1]
        pretty_relation_id(pp, field931)
        newline(pp)
        field932 = unwrapped_fields930[2]
        pretty_abstraction(pp, field932)
        field933 = unwrapped_fields930[3]
        if !isnothing(field933)
            newline(pp)
            opt_val934 = field933
            pretty_attrs(pp, opt_val934)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat940 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat940)
        write(pp, flat940)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1656 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1655 = _t1656
        else
            _t1655 = nothing
        end
        deconstruct_result938 = _t1655
        if !isnothing(deconstruct_result938)
            unwrapped939 = deconstruct_result938
            write(pp, ":")
            write(pp, unwrapped939)
        else
            _dollar_dollar = msg
            _t1657 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result936 = _t1657
            if !isnothing(deconstruct_result936)
                unwrapped937 = deconstruct_result936
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped937))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat945 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat945)
        write(pp, flat945)
        return nothing
    else
        _dollar_dollar = msg
        _t1658 = deconstruct_bindings(pp, _dollar_dollar)
        fields941 = (_t1658, _dollar_dollar.value,)
        unwrapped_fields942 = fields941
        write(pp, "(")
        indent!(pp)
        field943 = unwrapped_fields942[1]
        pretty_bindings(pp, field943)
        newline(pp)
        field944 = unwrapped_fields942[2]
        pretty_formula(pp, field944)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat953 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat953)
        write(pp, flat953)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1659 = _dollar_dollar[2]
        else
            _t1659 = nothing
        end
        fields946 = (_dollar_dollar[1], _t1659,)
        unwrapped_fields947 = fields946
        write(pp, "[")
        indent!(pp)
        field948 = unwrapped_fields947[1]
        for (i1660, elem949) in enumerate(field948)
            i950 = i1660 - 1
            if (i950 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem949)
        end
        field951 = unwrapped_fields947[2]
        if !isnothing(field951)
            newline(pp)
            opt_val952 = field951
            pretty_value_bindings(pp, opt_val952)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat958 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat958)
        write(pp, flat958)
        return nothing
    else
        _dollar_dollar = msg
        fields954 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields955 = fields954
        field956 = unwrapped_fields955[1]
        write(pp, field956)
        write(pp, "::")
        field957 = unwrapped_fields955[2]
        pretty_type(pp, field957)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat987 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat987)
        write(pp, flat987)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1661 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1661 = nothing
        end
        deconstruct_result985 = _t1661
        if !isnothing(deconstruct_result985)
            unwrapped986 = deconstruct_result985
            pretty_unspecified_type(pp, unwrapped986)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1662 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1662 = nothing
            end
            deconstruct_result983 = _t1662
            if !isnothing(deconstruct_result983)
                unwrapped984 = deconstruct_result983
                pretty_string_type(pp, unwrapped984)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1663 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1663 = nothing
                end
                deconstruct_result981 = _t1663
                if !isnothing(deconstruct_result981)
                    unwrapped982 = deconstruct_result981
                    pretty_int_type(pp, unwrapped982)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1664 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1664 = nothing
                    end
                    deconstruct_result979 = _t1664
                    if !isnothing(deconstruct_result979)
                        unwrapped980 = deconstruct_result979
                        pretty_float_type(pp, unwrapped980)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1665 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1665 = nothing
                        end
                        deconstruct_result977 = _t1665
                        if !isnothing(deconstruct_result977)
                            unwrapped978 = deconstruct_result977
                            pretty_uint128_type(pp, unwrapped978)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1666 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1666 = nothing
                            end
                            deconstruct_result975 = _t1666
                            if !isnothing(deconstruct_result975)
                                unwrapped976 = deconstruct_result975
                                pretty_int128_type(pp, unwrapped976)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1667 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1667 = nothing
                                end
                                deconstruct_result973 = _t1667
                                if !isnothing(deconstruct_result973)
                                    unwrapped974 = deconstruct_result973
                                    pretty_date_type(pp, unwrapped974)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1668 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1668 = nothing
                                    end
                                    deconstruct_result971 = _t1668
                                    if !isnothing(deconstruct_result971)
                                        unwrapped972 = deconstruct_result971
                                        pretty_datetime_type(pp, unwrapped972)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1669 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1669 = nothing
                                        end
                                        deconstruct_result969 = _t1669
                                        if !isnothing(deconstruct_result969)
                                            unwrapped970 = deconstruct_result969
                                            pretty_missing_type(pp, unwrapped970)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1670 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1670 = nothing
                                            end
                                            deconstruct_result967 = _t1670
                                            if !isnothing(deconstruct_result967)
                                                unwrapped968 = deconstruct_result967
                                                pretty_decimal_type(pp, unwrapped968)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1671 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1671 = nothing
                                                end
                                                deconstruct_result965 = _t1671
                                                if !isnothing(deconstruct_result965)
                                                    unwrapped966 = deconstruct_result965
                                                    pretty_boolean_type(pp, unwrapped966)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1672 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1672 = nothing
                                                    end
                                                    deconstruct_result963 = _t1672
                                                    if !isnothing(deconstruct_result963)
                                                        unwrapped964 = deconstruct_result963
                                                        pretty_int32_type(pp, unwrapped964)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1673 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1673 = nothing
                                                        end
                                                        deconstruct_result961 = _t1673
                                                        if !isnothing(deconstruct_result961)
                                                            unwrapped962 = deconstruct_result961
                                                            pretty_float32_type(pp, unwrapped962)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1674 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1674 = nothing
                                                            end
                                                            deconstruct_result959 = _t1674
                                                            if !isnothing(deconstruct_result959)
                                                                unwrapped960 = deconstruct_result959
                                                                pretty_uint32_type(pp, unwrapped960)
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
    fields988 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields989 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields990 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields991 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields992 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields993 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields994 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields995 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields996 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat1001 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat1001)
        write(pp, flat1001)
        return nothing
    else
        _dollar_dollar = msg
        fields997 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields998 = fields997
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field999 = unwrapped_fields998[1]
        write(pp, string(field999))
        newline(pp)
        field1000 = unwrapped_fields998[2]
        write(pp, string(field1000))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields1002 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields1003 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields1004 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields1005 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1009 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1009)
        write(pp, flat1009)
        return nothing
    else
        fields1006 = msg
        write(pp, "|")
        if !isempty(fields1006)
            write(pp, " ")
            for (i1675, elem1007) in enumerate(fields1006)
                i1008 = i1675 - 1
                if (i1008 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1007)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1036 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1036)
        write(pp, flat1036)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1676 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1676 = nothing
        end
        deconstruct_result1034 = _t1676
        if !isnothing(deconstruct_result1034)
            unwrapped1035 = deconstruct_result1034
            pretty_true(pp, unwrapped1035)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1677 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1677 = nothing
            end
            deconstruct_result1032 = _t1677
            if !isnothing(deconstruct_result1032)
                unwrapped1033 = deconstruct_result1032
                pretty_false(pp, unwrapped1033)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1678 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1678 = nothing
                end
                deconstruct_result1030 = _t1678
                if !isnothing(deconstruct_result1030)
                    unwrapped1031 = deconstruct_result1030
                    pretty_exists(pp, unwrapped1031)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1679 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1679 = nothing
                    end
                    deconstruct_result1028 = _t1679
                    if !isnothing(deconstruct_result1028)
                        unwrapped1029 = deconstruct_result1028
                        pretty_reduce(pp, unwrapped1029)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1680 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1680 = nothing
                        end
                        deconstruct_result1026 = _t1680
                        if !isnothing(deconstruct_result1026)
                            unwrapped1027 = deconstruct_result1026
                            pretty_conjunction(pp, unwrapped1027)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1681 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1681 = nothing
                            end
                            deconstruct_result1024 = _t1681
                            if !isnothing(deconstruct_result1024)
                                unwrapped1025 = deconstruct_result1024
                                pretty_disjunction(pp, unwrapped1025)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1682 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1682 = nothing
                                end
                                deconstruct_result1022 = _t1682
                                if !isnothing(deconstruct_result1022)
                                    unwrapped1023 = deconstruct_result1022
                                    pretty_not(pp, unwrapped1023)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1683 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1683 = nothing
                                    end
                                    deconstruct_result1020 = _t1683
                                    if !isnothing(deconstruct_result1020)
                                        unwrapped1021 = deconstruct_result1020
                                        pretty_ffi(pp, unwrapped1021)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1684 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1684 = nothing
                                        end
                                        deconstruct_result1018 = _t1684
                                        if !isnothing(deconstruct_result1018)
                                            unwrapped1019 = deconstruct_result1018
                                            pretty_atom(pp, unwrapped1019)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1685 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1685 = nothing
                                            end
                                            deconstruct_result1016 = _t1685
                                            if !isnothing(deconstruct_result1016)
                                                unwrapped1017 = deconstruct_result1016
                                                pretty_pragma(pp, unwrapped1017)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1686 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1686 = nothing
                                                end
                                                deconstruct_result1014 = _t1686
                                                if !isnothing(deconstruct_result1014)
                                                    unwrapped1015 = deconstruct_result1014
                                                    pretty_primitive(pp, unwrapped1015)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1687 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1687 = nothing
                                                    end
                                                    deconstruct_result1012 = _t1687
                                                    if !isnothing(deconstruct_result1012)
                                                        unwrapped1013 = deconstruct_result1012
                                                        pretty_rel_atom(pp, unwrapped1013)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1688 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1688 = nothing
                                                        end
                                                        deconstruct_result1010 = _t1688
                                                        if !isnothing(deconstruct_result1010)
                                                            unwrapped1011 = deconstruct_result1010
                                                            pretty_cast(pp, unwrapped1011)
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
    fields1037 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1038 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1043 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1043)
        write(pp, flat1043)
        return nothing
    else
        _dollar_dollar = msg
        _t1689 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1039 = (_t1689, _dollar_dollar.body.value,)
        unwrapped_fields1040 = fields1039
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1041 = unwrapped_fields1040[1]
        pretty_bindings(pp, field1041)
        newline(pp)
        field1042 = unwrapped_fields1040[2]
        pretty_formula(pp, field1042)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1049 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1049)
        write(pp, flat1049)
        return nothing
    else
        _dollar_dollar = msg
        fields1044 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1045 = fields1044
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1046 = unwrapped_fields1045[1]
        pretty_abstraction(pp, field1046)
        newline(pp)
        field1047 = unwrapped_fields1045[2]
        pretty_abstraction(pp, field1047)
        newline(pp)
        field1048 = unwrapped_fields1045[3]
        pretty_terms(pp, field1048)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1053 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1053)
        write(pp, flat1053)
        return nothing
    else
        fields1050 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1050)
            newline(pp)
            for (i1690, elem1051) in enumerate(fields1050)
                i1052 = i1690 - 1
                if (i1052 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1051)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1058 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1058)
        write(pp, flat1058)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1691 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1691 = nothing
        end
        deconstruct_result1056 = _t1691
        if !isnothing(deconstruct_result1056)
            unwrapped1057 = deconstruct_result1056
            pretty_var(pp, unwrapped1057)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1692 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1692 = nothing
            end
            deconstruct_result1054 = _t1692
            if !isnothing(deconstruct_result1054)
                unwrapped1055 = deconstruct_result1054
                pretty_value(pp, unwrapped1055)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1061 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1061)
        write(pp, flat1061)
        return nothing
    else
        _dollar_dollar = msg
        fields1059 = _dollar_dollar.name
        unwrapped_fields1060 = fields1059
        write(pp, unwrapped_fields1060)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1087 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1087)
        write(pp, flat1087)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1693 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1693 = nothing
        end
        deconstruct_result1085 = _t1693
        if !isnothing(deconstruct_result1085)
            unwrapped1086 = deconstruct_result1085
            pretty_date(pp, unwrapped1086)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1694 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1694 = nothing
            end
            deconstruct_result1083 = _t1694
            if !isnothing(deconstruct_result1083)
                unwrapped1084 = deconstruct_result1083
                pretty_datetime(pp, unwrapped1084)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1695 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1695 = nothing
                end
                deconstruct_result1081 = _t1695
                if !isnothing(deconstruct_result1081)
                    unwrapped1082 = deconstruct_result1081
                    write(pp, format_string(pp, unwrapped1082))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1696 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1696 = nothing
                    end
                    deconstruct_result1079 = _t1696
                    if !isnothing(deconstruct_result1079)
                        unwrapped1080 = deconstruct_result1079
                        write(pp, format_int32(pp, unwrapped1080))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1697 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1697 = nothing
                        end
                        deconstruct_result1077 = _t1697
                        if !isnothing(deconstruct_result1077)
                            unwrapped1078 = deconstruct_result1077
                            write(pp, format_int(pp, unwrapped1078))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1698 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1698 = nothing
                            end
                            deconstruct_result1075 = _t1698
                            if !isnothing(deconstruct_result1075)
                                unwrapped1076 = deconstruct_result1075
                                write(pp, format_float32(pp, unwrapped1076))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1699 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1699 = nothing
                                end
                                deconstruct_result1073 = _t1699
                                if !isnothing(deconstruct_result1073)
                                    unwrapped1074 = deconstruct_result1073
                                    write(pp, format_float(pp, unwrapped1074))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1700 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1700 = nothing
                                    end
                                    deconstruct_result1071 = _t1700
                                    if !isnothing(deconstruct_result1071)
                                        unwrapped1072 = deconstruct_result1071
                                        write(pp, format_uint32(pp, unwrapped1072))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1701 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1701 = nothing
                                        end
                                        deconstruct_result1069 = _t1701
                                        if !isnothing(deconstruct_result1069)
                                            unwrapped1070 = deconstruct_result1069
                                            write(pp, format_uint128(pp, unwrapped1070))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1702 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1702 = nothing
                                            end
                                            deconstruct_result1067 = _t1702
                                            if !isnothing(deconstruct_result1067)
                                                unwrapped1068 = deconstruct_result1067
                                                write(pp, format_int128(pp, unwrapped1068))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1703 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1703 = nothing
                                                end
                                                deconstruct_result1065 = _t1703
                                                if !isnothing(deconstruct_result1065)
                                                    unwrapped1066 = deconstruct_result1065
                                                    write(pp, format_decimal(pp, unwrapped1066))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1704 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1704 = nothing
                                                    end
                                                    deconstruct_result1063 = _t1704
                                                    if !isnothing(deconstruct_result1063)
                                                        unwrapped1064 = deconstruct_result1063
                                                        pretty_boolean_value(pp, unwrapped1064)
                                                    else
                                                        fields1062 = msg
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
    flat1093 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1093)
        write(pp, flat1093)
        return nothing
    else
        _dollar_dollar = msg
        fields1088 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1089 = fields1088
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1090 = unwrapped_fields1089[1]
        write(pp, format_int(pp, field1090))
        newline(pp)
        field1091 = unwrapped_fields1089[2]
        write(pp, format_int(pp, field1091))
        newline(pp)
        field1092 = unwrapped_fields1089[3]
        write(pp, format_int(pp, field1092))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1104 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1104)
        write(pp, flat1104)
        return nothing
    else
        _dollar_dollar = msg
        fields1094 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1095 = fields1094
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1096 = unwrapped_fields1095[1]
        write(pp, format_int(pp, field1096))
        newline(pp)
        field1097 = unwrapped_fields1095[2]
        write(pp, format_int(pp, field1097))
        newline(pp)
        field1098 = unwrapped_fields1095[3]
        write(pp, format_int(pp, field1098))
        newline(pp)
        field1099 = unwrapped_fields1095[4]
        write(pp, format_int(pp, field1099))
        newline(pp)
        field1100 = unwrapped_fields1095[5]
        write(pp, format_int(pp, field1100))
        newline(pp)
        field1101 = unwrapped_fields1095[6]
        write(pp, format_int(pp, field1101))
        field1102 = unwrapped_fields1095[7]
        if !isnothing(field1102)
            newline(pp)
            opt_val1103 = field1102
            write(pp, format_int(pp, opt_val1103))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1109 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1109)
        write(pp, flat1109)
        return nothing
    else
        _dollar_dollar = msg
        fields1105 = _dollar_dollar.args
        unwrapped_fields1106 = fields1105
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1106)
            newline(pp)
            for (i1705, elem1107) in enumerate(unwrapped_fields1106)
                i1108 = i1705 - 1
                if (i1108 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1107)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1114 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1114)
        write(pp, flat1114)
        return nothing
    else
        _dollar_dollar = msg
        fields1110 = _dollar_dollar.args
        unwrapped_fields1111 = fields1110
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1111)
            newline(pp)
            for (i1706, elem1112) in enumerate(unwrapped_fields1111)
                i1113 = i1706 - 1
                if (i1113 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1112)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1117 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1117)
        write(pp, flat1117)
        return nothing
    else
        _dollar_dollar = msg
        fields1115 = _dollar_dollar.arg
        unwrapped_fields1116 = fields1115
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1116)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1123 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1123)
        write(pp, flat1123)
        return nothing
    else
        _dollar_dollar = msg
        fields1118 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1119 = fields1118
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1120 = unwrapped_fields1119[1]
        pretty_name(pp, field1120)
        newline(pp)
        field1121 = unwrapped_fields1119[2]
        pretty_ffi_args(pp, field1121)
        newline(pp)
        field1122 = unwrapped_fields1119[3]
        pretty_terms(pp, field1122)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1125 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1125)
        write(pp, flat1125)
        return nothing
    else
        fields1124 = msg
        write(pp, ":")
        write(pp, fields1124)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1129 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1129)
        write(pp, flat1129)
        return nothing
    else
        fields1126 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1126)
            newline(pp)
            for (i1707, elem1127) in enumerate(fields1126)
                i1128 = i1707 - 1
                if (i1128 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1127)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1136 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1136)
        write(pp, flat1136)
        return nothing
    else
        _dollar_dollar = msg
        fields1130 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1131 = fields1130
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1132 = unwrapped_fields1131[1]
        pretty_relation_id(pp, field1132)
        field1133 = unwrapped_fields1131[2]
        if !isempty(field1133)
            newline(pp)
            for (i1708, elem1134) in enumerate(field1133)
                i1135 = i1708 - 1
                if (i1135 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1134)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1143 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1143)
        write(pp, flat1143)
        return nothing
    else
        _dollar_dollar = msg
        fields1137 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1138 = fields1137
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1139 = unwrapped_fields1138[1]
        pretty_name(pp, field1139)
        field1140 = unwrapped_fields1138[2]
        if !isempty(field1140)
            newline(pp)
            for (i1709, elem1141) in enumerate(field1140)
                i1142 = i1709 - 1
                if (i1142 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1141)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1159 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1159)
        write(pp, flat1159)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1710 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1710 = nothing
        end
        guard_result1158 = _t1710
        if !isnothing(guard_result1158)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1711 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1711 = nothing
            end
            guard_result1157 = _t1711
            if !isnothing(guard_result1157)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1712 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1712 = nothing
                end
                guard_result1156 = _t1712
                if !isnothing(guard_result1156)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1713 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1713 = nothing
                    end
                    guard_result1155 = _t1713
                    if !isnothing(guard_result1155)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1714 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1714 = nothing
                        end
                        guard_result1154 = _t1714
                        if !isnothing(guard_result1154)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1715 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1715 = nothing
                            end
                            guard_result1153 = _t1715
                            if !isnothing(guard_result1153)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1716 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1716 = nothing
                                end
                                guard_result1152 = _t1716
                                if !isnothing(guard_result1152)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1717 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1717 = nothing
                                    end
                                    guard_result1151 = _t1717
                                    if !isnothing(guard_result1151)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1718 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1718 = nothing
                                        end
                                        guard_result1150 = _t1718
                                        if !isnothing(guard_result1150)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1144 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1145 = fields1144
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1146 = unwrapped_fields1145[1]
                                            pretty_name(pp, field1146)
                                            field1147 = unwrapped_fields1145[2]
                                            if !isempty(field1147)
                                                newline(pp)
                                                for (i1719, elem1148) in enumerate(field1147)
                                                    i1149 = i1719 - 1
                                                    if (i1149 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1148)
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
    flat1164 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1164)
        write(pp, flat1164)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1720 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1720 = nothing
        end
        fields1160 = _t1720
        unwrapped_fields1161 = fields1160
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1162 = unwrapped_fields1161[1]
        pretty_term(pp, field1162)
        newline(pp)
        field1163 = unwrapped_fields1161[2]
        pretty_term(pp, field1163)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1169 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1169)
        write(pp, flat1169)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1721 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1721 = nothing
        end
        fields1165 = _t1721
        unwrapped_fields1166 = fields1165
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1167 = unwrapped_fields1166[1]
        pretty_term(pp, field1167)
        newline(pp)
        field1168 = unwrapped_fields1166[2]
        pretty_term(pp, field1168)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1174 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1174)
        write(pp, flat1174)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1722 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1722 = nothing
        end
        fields1170 = _t1722
        unwrapped_fields1171 = fields1170
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1172 = unwrapped_fields1171[1]
        pretty_term(pp, field1172)
        newline(pp)
        field1173 = unwrapped_fields1171[2]
        pretty_term(pp, field1173)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1179 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1723 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1723 = nothing
        end
        fields1175 = _t1723
        unwrapped_fields1176 = fields1175
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1177 = unwrapped_fields1176[1]
        pretty_term(pp, field1177)
        newline(pp)
        field1178 = unwrapped_fields1176[2]
        pretty_term(pp, field1178)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1184 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1184)
        write(pp, flat1184)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1724 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1724 = nothing
        end
        fields1180 = _t1724
        unwrapped_fields1181 = fields1180
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1182 = unwrapped_fields1181[1]
        pretty_term(pp, field1182)
        newline(pp)
        field1183 = unwrapped_fields1181[2]
        pretty_term(pp, field1183)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1190 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1190)
        write(pp, flat1190)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1725 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1725 = nothing
        end
        fields1185 = _t1725
        unwrapped_fields1186 = fields1185
        write(pp, "(+")
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

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1196 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1196)
        write(pp, flat1196)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1726 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1726 = nothing
        end
        fields1191 = _t1726
        unwrapped_fields1192 = fields1191
        write(pp, "(-")
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

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1202 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1202)
        write(pp, flat1202)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1727 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1727 = nothing
        end
        fields1197 = _t1727
        unwrapped_fields1198 = fields1197
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1199 = unwrapped_fields1198[1]
        pretty_term(pp, field1199)
        newline(pp)
        field1200 = unwrapped_fields1198[2]
        pretty_term(pp, field1200)
        newline(pp)
        field1201 = unwrapped_fields1198[3]
        pretty_term(pp, field1201)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1208 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1208)
        write(pp, flat1208)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1728 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1728 = nothing
        end
        fields1203 = _t1728
        unwrapped_fields1204 = fields1203
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1205 = unwrapped_fields1204[1]
        pretty_term(pp, field1205)
        newline(pp)
        field1206 = unwrapped_fields1204[2]
        pretty_term(pp, field1206)
        newline(pp)
        field1207 = unwrapped_fields1204[3]
        pretty_term(pp, field1207)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1213 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1213)
        write(pp, flat1213)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1729 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1729 = nothing
        end
        deconstruct_result1211 = _t1729
        if !isnothing(deconstruct_result1211)
            unwrapped1212 = deconstruct_result1211
            pretty_specialized_value(pp, unwrapped1212)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1730 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1730 = nothing
            end
            deconstruct_result1209 = _t1730
            if !isnothing(deconstruct_result1209)
                unwrapped1210 = deconstruct_result1209
                pretty_term(pp, unwrapped1210)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1215 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        fields1214 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1214)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1222 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1222)
        write(pp, flat1222)
        return nothing
    else
        _dollar_dollar = msg
        fields1216 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1217 = fields1216
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1218 = unwrapped_fields1217[1]
        pretty_name(pp, field1218)
        field1219 = unwrapped_fields1217[2]
        if !isempty(field1219)
            newline(pp)
            for (i1731, elem1220) in enumerate(field1219)
                i1221 = i1731 - 1
                if (i1221 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1220)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1227 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1227)
        write(pp, flat1227)
        return nothing
    else
        _dollar_dollar = msg
        fields1223 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1224 = fields1223
        write(pp, "(cast")
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

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1231 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1231)
        write(pp, flat1231)
        return nothing
    else
        fields1228 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1228)
            newline(pp)
            for (i1732, elem1229) in enumerate(fields1228)
                i1230 = i1732 - 1
                if (i1230 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1229)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1238 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1238)
        write(pp, flat1238)
        return nothing
    else
        _dollar_dollar = msg
        fields1232 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1233 = fields1232
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1234 = unwrapped_fields1233[1]
        pretty_name(pp, field1234)
        field1235 = unwrapped_fields1233[2]
        if !isempty(field1235)
            newline(pp)
            for (i1733, elem1236) in enumerate(field1235)
                i1237 = i1733 - 1
                if (i1237 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1236)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1247 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1247)
        write(pp, flat1247)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1734 = _dollar_dollar.attrs
        else
            _t1734 = nothing
        end
        fields1239 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1734,)
        unwrapped_fields1240 = fields1239
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1241 = unwrapped_fields1240[1]
        if !isempty(field1241)
            newline(pp)
            for (i1735, elem1242) in enumerate(field1241)
                i1243 = i1735 - 1
                if (i1243 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1242)
            end
        end
        newline(pp)
        field1244 = unwrapped_fields1240[2]
        pretty_script(pp, field1244)
        field1245 = unwrapped_fields1240[3]
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

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1252 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1252)
        write(pp, flat1252)
        return nothing
    else
        _dollar_dollar = msg
        fields1248 = _dollar_dollar.constructs
        unwrapped_fields1249 = fields1248
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1249)
            newline(pp)
            for (i1736, elem1250) in enumerate(unwrapped_fields1249)
                i1251 = i1736 - 1
                if (i1251 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1250)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1257 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1257)
        write(pp, flat1257)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1737 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1737 = nothing
        end
        deconstruct_result1255 = _t1737
        if !isnothing(deconstruct_result1255)
            unwrapped1256 = deconstruct_result1255
            pretty_loop(pp, unwrapped1256)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1738 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1738 = nothing
            end
            deconstruct_result1253 = _t1738
            if !isnothing(deconstruct_result1253)
                unwrapped1254 = deconstruct_result1253
                pretty_instruction(pp, unwrapped1254)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1264 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1264)
        write(pp, flat1264)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1739 = _dollar_dollar.attrs
        else
            _t1739 = nothing
        end
        fields1258 = (_dollar_dollar.init, _dollar_dollar.body, _t1739,)
        unwrapped_fields1259 = fields1258
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1260 = unwrapped_fields1259[1]
        pretty_init(pp, field1260)
        newline(pp)
        field1261 = unwrapped_fields1259[2]
        pretty_script(pp, field1261)
        field1262 = unwrapped_fields1259[3]
        if !isnothing(field1262)
            newline(pp)
            opt_val1263 = field1262
            pretty_attrs(pp, opt_val1263)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1268 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1268)
        write(pp, flat1268)
        return nothing
    else
        fields1265 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1265)
            newline(pp)
            for (i1740, elem1266) in enumerate(fields1265)
                i1267 = i1740 - 1
                if (i1267 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1266)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1279 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1279)
        write(pp, flat1279)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1741 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1741 = nothing
        end
        deconstruct_result1277 = _t1741
        if !isnothing(deconstruct_result1277)
            unwrapped1278 = deconstruct_result1277
            pretty_assign(pp, unwrapped1278)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1742 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1742 = nothing
            end
            deconstruct_result1275 = _t1742
            if !isnothing(deconstruct_result1275)
                unwrapped1276 = deconstruct_result1275
                pretty_upsert(pp, unwrapped1276)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1743 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1743 = nothing
                end
                deconstruct_result1273 = _t1743
                if !isnothing(deconstruct_result1273)
                    unwrapped1274 = deconstruct_result1273
                    pretty_break(pp, unwrapped1274)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1744 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1744 = nothing
                    end
                    deconstruct_result1271 = _t1744
                    if !isnothing(deconstruct_result1271)
                        unwrapped1272 = deconstruct_result1271
                        pretty_monoid_def(pp, unwrapped1272)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1745 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1745 = nothing
                        end
                        deconstruct_result1269 = _t1745
                        if !isnothing(deconstruct_result1269)
                            unwrapped1270 = deconstruct_result1269
                            pretty_monus_def(pp, unwrapped1270)
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
    flat1286 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1286)
        write(pp, flat1286)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1746 = _dollar_dollar.attrs
        else
            _t1746 = nothing
        end
        fields1280 = (_dollar_dollar.name, _dollar_dollar.body, _t1746,)
        unwrapped_fields1281 = fields1280
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1282 = unwrapped_fields1281[1]
        pretty_relation_id(pp, field1282)
        newline(pp)
        field1283 = unwrapped_fields1281[2]
        pretty_abstraction(pp, field1283)
        field1284 = unwrapped_fields1281[3]
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

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1293 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1293)
        write(pp, flat1293)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1747 = _dollar_dollar.attrs
        else
            _t1747 = nothing
        end
        fields1287 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1747,)
        unwrapped_fields1288 = fields1287
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1289 = unwrapped_fields1288[1]
        pretty_relation_id(pp, field1289)
        newline(pp)
        field1290 = unwrapped_fields1288[2]
        pretty_abstraction_with_arity(pp, field1290)
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

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1298 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1298)
        write(pp, flat1298)
        return nothing
    else
        _dollar_dollar = msg
        _t1748 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1294 = (_t1748, _dollar_dollar[1].value,)
        unwrapped_fields1295 = fields1294
        write(pp, "(")
        indent!(pp)
        field1296 = unwrapped_fields1295[1]
        pretty_bindings(pp, field1296)
        newline(pp)
        field1297 = unwrapped_fields1295[2]
        pretty_formula(pp, field1297)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1305 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1305)
        write(pp, flat1305)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1749 = _dollar_dollar.attrs
        else
            _t1749 = nothing
        end
        fields1299 = (_dollar_dollar.name, _dollar_dollar.body, _t1749,)
        unwrapped_fields1300 = fields1299
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1301 = unwrapped_fields1300[1]
        pretty_relation_id(pp, field1301)
        newline(pp)
        field1302 = unwrapped_fields1300[2]
        pretty_abstraction(pp, field1302)
        field1303 = unwrapped_fields1300[3]
        if !isnothing(field1303)
            newline(pp)
            opt_val1304 = field1303
            pretty_attrs(pp, opt_val1304)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1313 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1313)
        write(pp, flat1313)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1750 = _dollar_dollar.attrs
        else
            _t1750 = nothing
        end
        fields1306 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1750,)
        unwrapped_fields1307 = fields1306
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1308 = unwrapped_fields1307[1]
        pretty_monoid(pp, field1308)
        newline(pp)
        field1309 = unwrapped_fields1307[2]
        pretty_relation_id(pp, field1309)
        newline(pp)
        field1310 = unwrapped_fields1307[3]
        pretty_abstraction_with_arity(pp, field1310)
        field1311 = unwrapped_fields1307[4]
        if !isnothing(field1311)
            newline(pp)
            opt_val1312 = field1311
            pretty_attrs(pp, opt_val1312)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1322 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1322)
        write(pp, flat1322)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1751 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1751 = nothing
        end
        deconstruct_result1320 = _t1751
        if !isnothing(deconstruct_result1320)
            unwrapped1321 = deconstruct_result1320
            pretty_or_monoid(pp, unwrapped1321)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1752 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1752 = nothing
            end
            deconstruct_result1318 = _t1752
            if !isnothing(deconstruct_result1318)
                unwrapped1319 = deconstruct_result1318
                pretty_min_monoid(pp, unwrapped1319)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1753 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1753 = nothing
                end
                deconstruct_result1316 = _t1753
                if !isnothing(deconstruct_result1316)
                    unwrapped1317 = deconstruct_result1316
                    pretty_max_monoid(pp, unwrapped1317)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1754 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1754 = nothing
                    end
                    deconstruct_result1314 = _t1754
                    if !isnothing(deconstruct_result1314)
                        unwrapped1315 = deconstruct_result1314
                        pretty_sum_monoid(pp, unwrapped1315)
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
    fields1323 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1326 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1326)
        write(pp, flat1326)
        return nothing
    else
        _dollar_dollar = msg
        fields1324 = _dollar_dollar.var"#type"
        unwrapped_fields1325 = fields1324
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1325)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1329 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1329)
        write(pp, flat1329)
        return nothing
    else
        _dollar_dollar = msg
        fields1327 = _dollar_dollar.var"#type"
        unwrapped_fields1328 = fields1327
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1328)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1332 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1332)
        write(pp, flat1332)
        return nothing
    else
        _dollar_dollar = msg
        fields1330 = _dollar_dollar.var"#type"
        unwrapped_fields1331 = fields1330
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1331)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1340 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1340)
        write(pp, flat1340)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1755 = _dollar_dollar.attrs
        else
            _t1755 = nothing
        end
        fields1333 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1755,)
        unwrapped_fields1334 = fields1333
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1335 = unwrapped_fields1334[1]
        pretty_monoid(pp, field1335)
        newline(pp)
        field1336 = unwrapped_fields1334[2]
        pretty_relation_id(pp, field1336)
        newline(pp)
        field1337 = unwrapped_fields1334[3]
        pretty_abstraction_with_arity(pp, field1337)
        field1338 = unwrapped_fields1334[4]
        if !isnothing(field1338)
            newline(pp)
            opt_val1339 = field1338
            pretty_attrs(pp, opt_val1339)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1347 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1347)
        write(pp, flat1347)
        return nothing
    else
        _dollar_dollar = msg
        fields1341 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1342 = fields1341
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1343 = unwrapped_fields1342[1]
        pretty_relation_id(pp, field1343)
        newline(pp)
        field1344 = unwrapped_fields1342[2]
        pretty_abstraction(pp, field1344)
        newline(pp)
        field1345 = unwrapped_fields1342[3]
        pretty_functional_dependency_keys(pp, field1345)
        newline(pp)
        field1346 = unwrapped_fields1342[4]
        pretty_functional_dependency_values(pp, field1346)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1351 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1351)
        write(pp, flat1351)
        return nothing
    else
        fields1348 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1348)
            newline(pp)
            for (i1756, elem1349) in enumerate(fields1348)
                i1350 = i1756 - 1
                if (i1350 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1349)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1355 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1355)
        write(pp, flat1355)
        return nothing
    else
        fields1352 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1352)
            newline(pp)
            for (i1757, elem1353) in enumerate(fields1352)
                i1354 = i1757 - 1
                if (i1354 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1353)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1364 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1364)
        write(pp, flat1364)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1758 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1758 = nothing
        end
        deconstruct_result1362 = _t1758
        if !isnothing(deconstruct_result1362)
            unwrapped1363 = deconstruct_result1362
            pretty_edb(pp, unwrapped1363)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1759 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1759 = nothing
            end
            deconstruct_result1360 = _t1759
            if !isnothing(deconstruct_result1360)
                unwrapped1361 = deconstruct_result1360
                pretty_betree_relation(pp, unwrapped1361)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1760 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1760 = nothing
                end
                deconstruct_result1358 = _t1760
                if !isnothing(deconstruct_result1358)
                    unwrapped1359 = deconstruct_result1358
                    pretty_csv_data(pp, unwrapped1359)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1761 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1761 = nothing
                    end
                    deconstruct_result1356 = _t1761
                    if !isnothing(deconstruct_result1356)
                        unwrapped1357 = deconstruct_result1356
                        pretty_iceberg_data(pp, unwrapped1357)
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
    flat1370 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1370)
        write(pp, flat1370)
        return nothing
    else
        _dollar_dollar = msg
        fields1365 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1366 = fields1365
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1367 = unwrapped_fields1366[1]
        pretty_relation_id(pp, field1367)
        newline(pp)
        field1368 = unwrapped_fields1366[2]
        pretty_edb_path(pp, field1368)
        newline(pp)
        field1369 = unwrapped_fields1366[3]
        pretty_edb_types(pp, field1369)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1374 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1374)
        write(pp, flat1374)
        return nothing
    else
        fields1371 = msg
        write(pp, "[")
        indent!(pp)
        for (i1762, elem1372) in enumerate(fields1371)
            i1373 = i1762 - 1
            if (i1373 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1372))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1378 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1378)
        write(pp, flat1378)
        return nothing
    else
        fields1375 = msg
        write(pp, "[")
        indent!(pp)
        for (i1763, elem1376) in enumerate(fields1375)
            i1377 = i1763 - 1
            if (i1377 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1376)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1383 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1383)
        write(pp, flat1383)
        return nothing
    else
        _dollar_dollar = msg
        fields1379 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1380 = fields1379
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1381 = unwrapped_fields1380[1]
        pretty_relation_id(pp, field1381)
        newline(pp)
        field1382 = unwrapped_fields1380[2]
        pretty_betree_info(pp, field1382)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1389 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1389)
        write(pp, flat1389)
        return nothing
    else
        _dollar_dollar = msg
        _t1764 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1384 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1764,)
        unwrapped_fields1385 = fields1384
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1386 = unwrapped_fields1385[1]
        pretty_betree_info_key_types(pp, field1386)
        newline(pp)
        field1387 = unwrapped_fields1385[2]
        pretty_betree_info_value_types(pp, field1387)
        newline(pp)
        field1388 = unwrapped_fields1385[3]
        pretty_config_dict(pp, field1388)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1393 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1393)
        write(pp, flat1393)
        return nothing
    else
        fields1390 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1390)
            newline(pp)
            for (i1765, elem1391) in enumerate(fields1390)
                i1392 = i1765 - 1
                if (i1392 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1391)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1397 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1397)
        write(pp, flat1397)
        return nothing
    else
        fields1394 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1394)
            newline(pp)
            for (i1766, elem1395) in enumerate(fields1394)
                i1396 = i1766 - 1
                if (i1396 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1395)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1404 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1404)
        write(pp, flat1404)
        return nothing
    else
        _dollar_dollar = msg
        fields1398 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1399 = fields1398
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1400 = unwrapped_fields1399[1]
        pretty_csvlocator(pp, field1400)
        newline(pp)
        field1401 = unwrapped_fields1399[2]
        pretty_csv_config(pp, field1401)
        newline(pp)
        field1402 = unwrapped_fields1399[3]
        pretty_gnf_columns(pp, field1402)
        newline(pp)
        field1403 = unwrapped_fields1399[4]
        pretty_csv_asof(pp, field1403)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1411 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1411)
        write(pp, flat1411)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1767 = _dollar_dollar.paths
        else
            _t1767 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1768 = String(copy(_dollar_dollar.inline_data))
        else
            _t1768 = nothing
        end
        fields1405 = (_t1767, _t1768,)
        unwrapped_fields1406 = fields1405
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1407 = unwrapped_fields1406[1]
        if !isnothing(field1407)
            newline(pp)
            opt_val1408 = field1407
            pretty_csv_locator_paths(pp, opt_val1408)
        end
        field1409 = unwrapped_fields1406[2]
        if !isnothing(field1409)
            newline(pp)
            opt_val1410 = field1409
            pretty_csv_locator_inline_data(pp, opt_val1410)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1415 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1415)
        write(pp, flat1415)
        return nothing
    else
        fields1412 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1412)
            newline(pp)
            for (i1769, elem1413) in enumerate(fields1412)
                i1414 = i1769 - 1
                if (i1414 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1413))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1417 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1417)
        write(pp, flat1417)
        return nothing
    else
        fields1416 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1416))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1423 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1423)
        write(pp, flat1423)
        return nothing
    else
        _dollar_dollar = msg
        _t1770 = deconstruct_csv_config(pp, _dollar_dollar)
        _t1771 = deconstruct_csv_storage_integration_optional(pp, _dollar_dollar)
        fields1418 = (_t1770, _t1771,)
        unwrapped_fields1419 = fields1418
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1420 = unwrapped_fields1419[1]
        pretty_config_dict(pp, field1420)
        field1421 = unwrapped_fields1419[2]
        if !isnothing(field1421)
            newline(pp)
            opt_val1422 = field1421
            pretty__storage_integration(pp, opt_val1422)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty__storage_integration(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat1425 = try_flat(pp, msg, pretty__storage_integration)
    if !isnothing(flat1425)
        write(pp, flat1425)
        return nothing
    else
        fields1424 = msg
        write(pp, "(storage_integration")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, fields1424)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1429 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1429)
        write(pp, flat1429)
        return nothing
    else
        fields1426 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1426)
            newline(pp)
            for (i1772, elem1427) in enumerate(fields1426)
                i1428 = i1772 - 1
                if (i1428 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1427)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1438 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1438)
        write(pp, flat1438)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1773 = _dollar_dollar.target_id
        else
            _t1773 = nothing
        end
        fields1430 = (_dollar_dollar.column_path, _t1773, _dollar_dollar.types,)
        unwrapped_fields1431 = fields1430
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1432 = unwrapped_fields1431[1]
        pretty_gnf_column_path(pp, field1432)
        field1433 = unwrapped_fields1431[2]
        if !isnothing(field1433)
            newline(pp)
            opt_val1434 = field1433
            pretty_relation_id(pp, opt_val1434)
        end
        newline(pp)
        write(pp, "[")
        field1435 = unwrapped_fields1431[3]
        for (i1774, elem1436) in enumerate(field1435)
            i1437 = i1774 - 1
            if (i1437 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1436)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1445 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1445)
        write(pp, flat1445)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1775 = _dollar_dollar[1]
        else
            _t1775 = nothing
        end
        deconstruct_result1443 = _t1775
        if !isnothing(deconstruct_result1443)
            unwrapped1444 = deconstruct_result1443
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1444))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1776 = _dollar_dollar
            else
                _t1776 = nothing
            end
            deconstruct_result1439 = _t1776
            if !isnothing(deconstruct_result1439)
                unwrapped1440 = deconstruct_result1439
                write(pp, "[")
                indent!(pp)
                for (i1777, elem1441) in enumerate(unwrapped1440)
                    i1442 = i1777 - 1
                    if (i1442 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1441))
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
    flat1447 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1447)
        write(pp, flat1447)
        return nothing
    else
        fields1446 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1446))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1458 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1458)
        write(pp, flat1458)
        return nothing
    else
        _dollar_dollar = msg
        _t1778 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1779 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1448 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1778, _t1779, _dollar_dollar.returns_delta,)
        unwrapped_fields1449 = fields1448
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1450 = unwrapped_fields1449[1]
        pretty_iceberg_locator(pp, field1450)
        newline(pp)
        field1451 = unwrapped_fields1449[2]
        pretty_iceberg_catalog_config(pp, field1451)
        newline(pp)
        field1452 = unwrapped_fields1449[3]
        pretty_gnf_columns(pp, field1452)
        field1453 = unwrapped_fields1449[4]
        if !isnothing(field1453)
            newline(pp)
            opt_val1454 = field1453
            pretty_iceberg_from_snapshot(pp, opt_val1454)
        end
        field1455 = unwrapped_fields1449[5]
        if !isnothing(field1455)
            newline(pp)
            opt_val1456 = field1455
            pretty_iceberg_to_snapshot(pp, opt_val1456)
        end
        newline(pp)
        field1457 = unwrapped_fields1449[6]
        pretty_boolean_value(pp, field1457)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1464 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1464)
        write(pp, flat1464)
        return nothing
    else
        _dollar_dollar = msg
        fields1459 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1460 = fields1459
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1461 = unwrapped_fields1460[1]
        pretty_iceberg_locator_table_name(pp, field1461)
        newline(pp)
        field1462 = unwrapped_fields1460[2]
        pretty_iceberg_locator_namespace(pp, field1462)
        newline(pp)
        field1463 = unwrapped_fields1460[3]
        pretty_iceberg_locator_warehouse(pp, field1463)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1466 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1466)
        write(pp, flat1466)
        return nothing
    else
        fields1465 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1465))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1470 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1470)
        write(pp, flat1470)
        return nothing
    else
        fields1467 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1467)
            newline(pp)
            for (i1780, elem1468) in enumerate(fields1467)
                i1469 = i1780 - 1
                if (i1469 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1468))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1472 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1472)
        write(pp, flat1472)
        return nothing
    else
        fields1471 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1471))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1480 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1480)
        write(pp, flat1480)
        return nothing
    else
        _dollar_dollar = msg
        _t1781 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1473 = (_dollar_dollar.catalog_uri, _t1781, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1474 = fields1473
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1475 = unwrapped_fields1474[1]
        pretty_iceberg_catalog_uri(pp, field1475)
        field1476 = unwrapped_fields1474[2]
        if !isnothing(field1476)
            newline(pp)
            opt_val1477 = field1476
            pretty_iceberg_catalog_config_scope(pp, opt_val1477)
        end
        newline(pp)
        field1478 = unwrapped_fields1474[3]
        pretty_iceberg_properties(pp, field1478)
        newline(pp)
        field1479 = unwrapped_fields1474[4]
        pretty_iceberg_auth_properties(pp, field1479)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1482 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1482)
        write(pp, flat1482)
        return nothing
    else
        fields1481 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1481))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1484 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1484)
        write(pp, flat1484)
        return nothing
    else
        fields1483 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1483))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1488 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1488)
        write(pp, flat1488)
        return nothing
    else
        fields1485 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1485)
            newline(pp)
            for (i1782, elem1486) in enumerate(fields1485)
                i1487 = i1782 - 1
                if (i1487 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1486)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1493 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1493)
        write(pp, flat1493)
        return nothing
    else
        _dollar_dollar = msg
        fields1489 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1490 = fields1489
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1491 = unwrapped_fields1490[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1491))
        newline(pp)
        field1492 = unwrapped_fields1490[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1492))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1497 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1497)
        write(pp, flat1497)
        return nothing
    else
        fields1494 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1494)
            newline(pp)
            for (i1783, elem1495) in enumerate(fields1494)
                i1496 = i1783 - 1
                if (i1496 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1495)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1502 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1502)
        write(pp, flat1502)
        return nothing
    else
        _dollar_dollar = msg
        _t1784 = mask_secret_value(pp, _dollar_dollar)
        fields1498 = (_dollar_dollar[1], _t1784,)
        unwrapped_fields1499 = fields1498
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1500 = unwrapped_fields1499[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1500))
        newline(pp)
        field1501 = unwrapped_fields1499[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1501))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1504 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1504)
        write(pp, flat1504)
        return nothing
    else
        fields1503 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1503))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1506 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1506)
        write(pp, flat1506)
        return nothing
    else
        fields1505 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1505))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1509 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1509)
        write(pp, flat1509)
        return nothing
    else
        _dollar_dollar = msg
        fields1507 = _dollar_dollar.fragment_id
        unwrapped_fields1508 = fields1507
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1508)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1514 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1514)
        write(pp, flat1514)
        return nothing
    else
        _dollar_dollar = msg
        fields1510 = _dollar_dollar.relations
        unwrapped_fields1511 = fields1510
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1511)
            newline(pp)
            for (i1785, elem1512) in enumerate(unwrapped_fields1511)
                i1513 = i1785 - 1
                if (i1513 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1512)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1521 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1521)
        write(pp, flat1521)
        return nothing
    else
        _dollar_dollar = msg
        fields1515 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1516 = fields1515
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1517 = unwrapped_fields1516[1]
        pretty_edb_path(pp, field1517)
        field1518 = unwrapped_fields1516[2]
        if !isempty(field1518)
            newline(pp)
            for (i1786, elem1519) in enumerate(field1518)
                i1520 = i1786 - 1
                if (i1520 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1519)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1526 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1526)
        write(pp, flat1526)
        return nothing
    else
        _dollar_dollar = msg
        fields1522 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1523 = fields1522
        field1524 = unwrapped_fields1523[1]
        pretty_edb_path(pp, field1524)
        write(pp, " ")
        field1525 = unwrapped_fields1523[2]
        pretty_relation_id(pp, field1525)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1530 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1530)
        write(pp, flat1530)
        return nothing
    else
        fields1527 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1527)
            newline(pp)
            for (i1787, elem1528) in enumerate(fields1527)
                i1529 = i1787 - 1
                if (i1529 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1528)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1543 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1543)
        write(pp, flat1543)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1788 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1788 = nothing
        end
        deconstruct_result1541 = _t1788
        if !isnothing(deconstruct_result1541)
            unwrapped1542 = deconstruct_result1541
            pretty_demand(pp, unwrapped1542)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1789 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1789 = nothing
            end
            deconstruct_result1539 = _t1789
            if !isnothing(deconstruct_result1539)
                unwrapped1540 = deconstruct_result1539
                pretty_output(pp, unwrapped1540)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1790 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1790 = nothing
                end
                deconstruct_result1537 = _t1790
                if !isnothing(deconstruct_result1537)
                    unwrapped1538 = deconstruct_result1537
                    pretty_what_if(pp, unwrapped1538)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1791 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1791 = nothing
                    end
                    deconstruct_result1535 = _t1791
                    if !isnothing(deconstruct_result1535)
                        unwrapped1536 = deconstruct_result1535
                        pretty_abort(pp, unwrapped1536)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1792 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1792 = nothing
                        end
                        deconstruct_result1533 = _t1792
                        if !isnothing(deconstruct_result1533)
                            unwrapped1534 = deconstruct_result1533
                            pretty_export(pp, unwrapped1534)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("export_output"))
                                _t1793 = _get_oneof_field(_dollar_dollar, :export_output)
                            else
                                _t1793 = nothing
                            end
                            deconstruct_result1531 = _t1793
                            if !isnothing(deconstruct_result1531)
                                unwrapped1532 = deconstruct_result1531
                                pretty_export_output(pp, unwrapped1532)
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
    flat1546 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1546)
        write(pp, flat1546)
        return nothing
    else
        _dollar_dollar = msg
        fields1544 = _dollar_dollar.relation_id
        unwrapped_fields1545 = fields1544
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1545)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1551 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1551)
        write(pp, flat1551)
        return nothing
    else
        _dollar_dollar = msg
        fields1547 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1548 = fields1547
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1549 = unwrapped_fields1548[1]
        pretty_name(pp, field1549)
        newline(pp)
        field1550 = unwrapped_fields1548[2]
        pretty_relation_id(pp, field1550)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1556 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1556)
        write(pp, flat1556)
        return nothing
    else
        _dollar_dollar = msg
        fields1552 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1553 = fields1552
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1554 = unwrapped_fields1553[1]
        pretty_name(pp, field1554)
        newline(pp)
        field1555 = unwrapped_fields1553[2]
        pretty_epoch(pp, field1555)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1562 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1562)
        write(pp, flat1562)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1794 = _dollar_dollar.name
        else
            _t1794 = nothing
        end
        fields1557 = (_t1794, _dollar_dollar.relation_id,)
        unwrapped_fields1558 = fields1557
        write(pp, "(abort")
        indent_sexp!(pp)
        field1559 = unwrapped_fields1558[1]
        if !isnothing(field1559)
            newline(pp)
            opt_val1560 = field1559
            pretty_name(pp, opt_val1560)
        end
        newline(pp)
        field1561 = unwrapped_fields1558[2]
        pretty_relation_id(pp, field1561)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1567 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1567)
        write(pp, flat1567)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1795 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1795 = nothing
        end
        deconstruct_result1565 = _t1795
        if !isnothing(deconstruct_result1565)
            unwrapped1566 = deconstruct_result1565
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1566)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1796 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1796 = nothing
            end
            deconstruct_result1563 = _t1796
            if !isnothing(deconstruct_result1563)
                unwrapped1564 = deconstruct_result1563
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1564)
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
    flat1578 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1578)
        write(pp, flat1578)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1797 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1797 = nothing
        end
        deconstruct_result1573 = _t1797
        if !isnothing(deconstruct_result1573)
            unwrapped1574 = deconstruct_result1573
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1575 = unwrapped1574[1]
            pretty_export_csv_path(pp, field1575)
            newline(pp)
            field1576 = unwrapped1574[2]
            pretty_export_csv_source(pp, field1576)
            newline(pp)
            field1577 = unwrapped1574[3]
            pretty_csv_config(pp, field1577)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1799 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1798 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1799,)
            else
                _t1798 = nothing
            end
            deconstruct_result1568 = _t1798
            if !isnothing(deconstruct_result1568)
                unwrapped1569 = deconstruct_result1568
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1570 = unwrapped1569[1]
                pretty_export_csv_path(pp, field1570)
                newline(pp)
                field1571 = unwrapped1569[2]
                pretty_export_csv_columns_list(pp, field1571)
                newline(pp)
                field1572 = unwrapped1569[3]
                pretty_config_dict(pp, field1572)
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
    flat1580 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1580)
        write(pp, flat1580)
        return nothing
    else
        fields1579 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1579))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1587 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1587)
        write(pp, flat1587)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1800 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1800 = nothing
        end
        deconstruct_result1583 = _t1800
        if !isnothing(deconstruct_result1583)
            unwrapped1584 = deconstruct_result1583
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1584)
                newline(pp)
                for (i1801, elem1585) in enumerate(unwrapped1584)
                    i1586 = i1801 - 1
                    if (i1586 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1585)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1802 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1802 = nothing
            end
            deconstruct_result1581 = _t1802
            if !isnothing(deconstruct_result1581)
                unwrapped1582 = deconstruct_result1581
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1582)
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
    flat1592 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1592)
        write(pp, flat1592)
        return nothing
    else
        _dollar_dollar = msg
        fields1588 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1589 = fields1588
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1590 = unwrapped_fields1589[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1590))
        newline(pp)
        field1591 = unwrapped_fields1589[2]
        pretty_relation_id(pp, field1591)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1596 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1596)
        write(pp, flat1596)
        return nothing
    else
        fields1593 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1593)
            newline(pp)
            for (i1803, elem1594) in enumerate(fields1593)
                i1595 = i1803 - 1
                if (i1595 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1594)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1605 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1605)
        write(pp, flat1605)
        return nothing
    else
        _dollar_dollar = msg
        _t1804 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1597 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1804,)
        unwrapped_fields1598 = fields1597
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1599 = unwrapped_fields1598[1]
        pretty_iceberg_locator(pp, field1599)
        newline(pp)
        field1600 = unwrapped_fields1598[2]
        pretty_iceberg_catalog_config(pp, field1600)
        newline(pp)
        field1601 = unwrapped_fields1598[3]
        pretty_export_iceberg_table_def(pp, field1601)
        newline(pp)
        field1602 = unwrapped_fields1598[4]
        pretty_iceberg_table_properties(pp, field1602)
        field1603 = unwrapped_fields1598[5]
        if !isnothing(field1603)
            newline(pp)
            opt_val1604 = field1603
            pretty_config_dict(pp, opt_val1604)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1607 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1607)
        write(pp, flat1607)
        return nothing
    else
        fields1606 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1606)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1611 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1611)
        write(pp, flat1611)
        return nothing
    else
        fields1608 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1608)
            newline(pp)
            for (i1805, elem1609) in enumerate(fields1608)
                i1610 = i1805 - 1
                if (i1610 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1609)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_output(pp::PrettyPrinter, msg::Proto.ExportOutput)
    flat1616 = try_flat(pp, msg, pretty_export_output)
    if !isnothing(flat1616)
        write(pp, flat1616)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv"))
            _t1806 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :csv),)
        else
            _t1806 = nothing
        end
        fields1612 = _t1806
        unwrapped_fields1613 = fields1612
        write(pp, "(export_output")
        indent_sexp!(pp)
        newline(pp)
        field1614 = unwrapped_fields1613[1]
        pretty_name(pp, field1614)
        newline(pp)
        field1615 = unwrapped_fields1613[2]
        pretty_export_csv_output(pp, field1615)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_output(pp::PrettyPrinter, msg::Proto.ExportCSVOutput)
    flat1621 = try_flat(pp, msg, pretty_export_csv_output)
    if !isnothing(flat1621)
        write(pp, flat1621)
        return nothing
    else
        _dollar_dollar = msg
        fields1617 = (_dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        unwrapped_fields1618 = fields1617
        write(pp, "(csv")
        indent_sexp!(pp)
        newline(pp)
        field1619 = unwrapped_fields1618[1]
        pretty_export_csv_source(pp, field1619)
        newline(pp)
        field1620 = unwrapped_fields1618[2]
        pretty_csv_config(pp, field1620)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1858, _rid) in enumerate(msg.ids)
        _idx = i1858 - 1
        newline(pp)
        write(pp, "(")
        _t1859 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1859)
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
    for (i1860, _elem) in enumerate(msg.keys)
        _idx = i1860 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1861, _elem) in enumerate(msg.values)
        _idx = i1861 - 1
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
    for (i1862, _elem) in enumerate(msg.columns)
        _idx = i1862 - 1
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
