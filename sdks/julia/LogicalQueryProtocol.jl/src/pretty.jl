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
    _t1800 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1800
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1801 = Proto.Value(value=OneOf(:int_value, v))
    return _t1801
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1802 = Proto.Value(value=OneOf(:float_value, v))
    return _t1802
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1803 = Proto.Value(value=OneOf(:string_value, v))
    return _t1803
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1804 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1804
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1805 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1805
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1806 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1806,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1807 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1807,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1808 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1808,))
            end
        end
    end
    _t1809 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1809,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1810 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1810,))
    _t1811 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1811,))
    if msg.new_line != ""
        _t1812 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1812,))
    end
    _t1813 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1813,))
    _t1814 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1814,))
    _t1815 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1815,))
    if msg.comment != ""
        _t1816 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1816,))
    end
    for missing_string in msg.missing_strings
        _t1817 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1817,))
    end
    _t1818 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1818,))
    _t1819 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1819,))
    _t1820 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1820,))
    if msg.partition_size_mb != 0
        _t1821 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1821,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1822 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1822,))
    _t1823 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1823,))
    _t1824 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1824,))
    _t1825 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1825,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1826 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1826,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1827 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1827,))
        end
    end
    _t1828 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1828,))
    _t1829 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1829,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1830 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1830,))
    end
    if !isnothing(msg.compression)
        _t1831 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1831,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1832 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1832,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1833 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1833,))
    end
    if !isnothing(msg.syntax_delim)
        _t1834 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1834,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1835 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1835,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1836 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1836,))
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
        _t1837 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1838 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1839 = nothing
    end
    return nothing
end

function deconstruct_csv_data_columns_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Vector{Proto.GNFColumn}}
    if !_has_proto_field(msg, Symbol("target"))
        return msg.columns
    else
        _t1840 = nothing
    end
    return nothing
end

function deconstruct_csv_data_target_optional(pp::PrettyPrinter, msg::Proto.CSVData)::Union{Nothing, Proto.CSVTarget}
    if _has_proto_field(msg, Symbol("target"))
        return msg.target
    else
        _t1841 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1842 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1842,))
    end
    if msg.target_file_size_bytes != 0
        _t1843 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1843,))
    end
    if msg.compression != ""
        _t1844 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1844,))
    end
    if length(result) == 0
        return nothing
    else
        _t1845 = nothing
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
        _t1846 = nothing
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
    flat816 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat816)
        write(pp, flat816)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1614 = _dollar_dollar.configure
        else
            _t1614 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1615 = _dollar_dollar.sync
        else
            _t1615 = nothing
        end
        fields807 = (_t1614, _t1615, _dollar_dollar.epochs,)
        unwrapped_fields808 = fields807
        write(pp, "(transaction")
        indent_sexp!(pp)
        field809 = unwrapped_fields808[1]
        if !isnothing(field809)
            newline(pp)
            opt_val810 = field809
            pretty_configure(pp, opt_val810)
        end
        field811 = unwrapped_fields808[2]
        if !isnothing(field811)
            newline(pp)
            opt_val812 = field811
            pretty_sync(pp, opt_val812)
        end
        field813 = unwrapped_fields808[3]
        if !isempty(field813)
            newline(pp)
            for (i1616, elem814) in enumerate(field813)
                i815 = i1616 - 1
                if (i815 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem814)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat819 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat819)
        write(pp, flat819)
        return nothing
    else
        _dollar_dollar = msg
        _t1617 = deconstruct_configure(pp, _dollar_dollar)
        fields817 = _t1617
        unwrapped_fields818 = fields817
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields818)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat823 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat823)
        write(pp, flat823)
        return nothing
    else
        fields820 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields820)
            newline(pp)
            for (i1618, elem821) in enumerate(fields820)
                i822 = i1618 - 1
                if (i822 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem821)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat828 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat828)
        write(pp, flat828)
        return nothing
    else
        _dollar_dollar = msg
        fields824 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields825 = fields824
        write(pp, ":")
        field826 = unwrapped_fields825[1]
        write(pp, field826)
        write(pp, " ")
        field827 = unwrapped_fields825[2]
        pretty_raw_value(pp, field827)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat854 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat854)
        write(pp, flat854)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1619 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1619 = nothing
        end
        deconstruct_result852 = _t1619
        if !isnothing(deconstruct_result852)
            unwrapped853 = deconstruct_result852
            pretty_raw_date(pp, unwrapped853)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1620 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1620 = nothing
            end
            deconstruct_result850 = _t1620
            if !isnothing(deconstruct_result850)
                unwrapped851 = deconstruct_result850
                pretty_raw_datetime(pp, unwrapped851)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1621 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1621 = nothing
                end
                deconstruct_result848 = _t1621
                if !isnothing(deconstruct_result848)
                    unwrapped849 = deconstruct_result848
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped849))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1622 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1622 = nothing
                    end
                    deconstruct_result846 = _t1622
                    if !isnothing(deconstruct_result846)
                        unwrapped847 = deconstruct_result846
                        write(pp, (string(Int64(unwrapped847)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1623 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1623 = nothing
                        end
                        deconstruct_result844 = _t1623
                        if !isnothing(deconstruct_result844)
                            unwrapped845 = deconstruct_result844
                            write(pp, string(unwrapped845))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1624 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1624 = nothing
                            end
                            deconstruct_result842 = _t1624
                            if !isnothing(deconstruct_result842)
                                unwrapped843 = deconstruct_result842
                                write(pp, format_float32_literal(unwrapped843))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1625 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1625 = nothing
                                end
                                deconstruct_result840 = _t1625
                                if !isnothing(deconstruct_result840)
                                    unwrapped841 = deconstruct_result840
                                    write(pp, lowercase(string(unwrapped841)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1626 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1626 = nothing
                                    end
                                    deconstruct_result838 = _t1626
                                    if !isnothing(deconstruct_result838)
                                        unwrapped839 = deconstruct_result838
                                        write(pp, (string(Int64(unwrapped839)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1627 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1627 = nothing
                                        end
                                        deconstruct_result836 = _t1627
                                        if !isnothing(deconstruct_result836)
                                            unwrapped837 = deconstruct_result836
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped837))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1628 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1628 = nothing
                                            end
                                            deconstruct_result834 = _t1628
                                            if !isnothing(deconstruct_result834)
                                                unwrapped835 = deconstruct_result834
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped835))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1629 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1629 = nothing
                                                end
                                                deconstruct_result832 = _t1629
                                                if !isnothing(deconstruct_result832)
                                                    unwrapped833 = deconstruct_result832
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped833))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1630 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1630 = nothing
                                                    end
                                                    deconstruct_result830 = _t1630
                                                    if !isnothing(deconstruct_result830)
                                                        unwrapped831 = deconstruct_result830
                                                        pretty_boolean_value(pp, unwrapped831)
                                                    else
                                                        fields829 = msg
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
    flat860 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat860)
        write(pp, flat860)
        return nothing
    else
        _dollar_dollar = msg
        fields855 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields856 = fields855
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field857 = unwrapped_fields856[1]
        write(pp, string(field857))
        newline(pp)
        field858 = unwrapped_fields856[2]
        write(pp, string(field858))
        newline(pp)
        field859 = unwrapped_fields856[3]
        write(pp, string(field859))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat871 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat871)
        write(pp, flat871)
        return nothing
    else
        _dollar_dollar = msg
        fields861 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields862 = fields861
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field863 = unwrapped_fields862[1]
        write(pp, string(field863))
        newline(pp)
        field864 = unwrapped_fields862[2]
        write(pp, string(field864))
        newline(pp)
        field865 = unwrapped_fields862[3]
        write(pp, string(field865))
        newline(pp)
        field866 = unwrapped_fields862[4]
        write(pp, string(field866))
        newline(pp)
        field867 = unwrapped_fields862[5]
        write(pp, string(field867))
        newline(pp)
        field868 = unwrapped_fields862[6]
        write(pp, string(field868))
        field869 = unwrapped_fields862[7]
        if !isnothing(field869)
            newline(pp)
            opt_val870 = field869
            write(pp, string(opt_val870))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1631 = ()
    else
        _t1631 = nothing
    end
    deconstruct_result874 = _t1631
    if !isnothing(deconstruct_result874)
        unwrapped875 = deconstruct_result874
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1632 = ()
        else
            _t1632 = nothing
        end
        deconstruct_result872 = _t1632
        if !isnothing(deconstruct_result872)
            unwrapped873 = deconstruct_result872
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat880 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat880)
        write(pp, flat880)
        return nothing
    else
        _dollar_dollar = msg
        fields876 = _dollar_dollar.fragments
        unwrapped_fields877 = fields876
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields877)
            newline(pp)
            for (i1633, elem878) in enumerate(unwrapped_fields877)
                i879 = i1633 - 1
                if (i879 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem878)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat883 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat883)
        write(pp, flat883)
        return nothing
    else
        _dollar_dollar = msg
        fields881 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields882 = fields881
        write(pp, ":")
        write(pp, unwrapped_fields882)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat890 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat890)
        write(pp, flat890)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1634 = _dollar_dollar.writes
        else
            _t1634 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1635 = _dollar_dollar.reads
        else
            _t1635 = nothing
        end
        fields884 = (_t1634, _t1635,)
        unwrapped_fields885 = fields884
        write(pp, "(epoch")
        indent_sexp!(pp)
        field886 = unwrapped_fields885[1]
        if !isnothing(field886)
            newline(pp)
            opt_val887 = field886
            pretty_epoch_writes(pp, opt_val887)
        end
        field888 = unwrapped_fields885[2]
        if !isnothing(field888)
            newline(pp)
            opt_val889 = field888
            pretty_epoch_reads(pp, opt_val889)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat894 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat894)
        write(pp, flat894)
        return nothing
    else
        fields891 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields891)
            newline(pp)
            for (i1636, elem892) in enumerate(fields891)
                i893 = i1636 - 1
                if (i893 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem892)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat903 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat903)
        write(pp, flat903)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1637 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1637 = nothing
        end
        deconstruct_result901 = _t1637
        if !isnothing(deconstruct_result901)
            unwrapped902 = deconstruct_result901
            pretty_define(pp, unwrapped902)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1638 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1638 = nothing
            end
            deconstruct_result899 = _t1638
            if !isnothing(deconstruct_result899)
                unwrapped900 = deconstruct_result899
                pretty_undefine(pp, unwrapped900)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1639 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1639 = nothing
                end
                deconstruct_result897 = _t1639
                if !isnothing(deconstruct_result897)
                    unwrapped898 = deconstruct_result897
                    pretty_context(pp, unwrapped898)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1640 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1640 = nothing
                    end
                    deconstruct_result895 = _t1640
                    if !isnothing(deconstruct_result895)
                        unwrapped896 = deconstruct_result895
                        pretty_snapshot(pp, unwrapped896)
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
    flat906 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        _dollar_dollar = msg
        fields904 = _dollar_dollar.fragment
        unwrapped_fields905 = fields904
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields905)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat913 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat913)
        write(pp, flat913)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields907 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields908 = fields907
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field909 = unwrapped_fields908[1]
        pretty_new_fragment_id(pp, field909)
        field910 = unwrapped_fields908[2]
        if !isempty(field910)
            newline(pp)
            for (i1641, elem911) in enumerate(field910)
                i912 = i1641 - 1
                if (i912 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem911)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat915 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat915)
        write(pp, flat915)
        return nothing
    else
        fields914 = msg
        pretty_fragment_id(pp, fields914)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat924 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat924)
        write(pp, flat924)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1642 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1642 = nothing
        end
        deconstruct_result922 = _t1642
        if !isnothing(deconstruct_result922)
            unwrapped923 = deconstruct_result922
            pretty_def(pp, unwrapped923)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1643 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1643 = nothing
            end
            deconstruct_result920 = _t1643
            if !isnothing(deconstruct_result920)
                unwrapped921 = deconstruct_result920
                pretty_algorithm(pp, unwrapped921)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1644 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1644 = nothing
                end
                deconstruct_result918 = _t1644
                if !isnothing(deconstruct_result918)
                    unwrapped919 = deconstruct_result918
                    pretty_constraint(pp, unwrapped919)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1645 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1645 = nothing
                    end
                    deconstruct_result916 = _t1645
                    if !isnothing(deconstruct_result916)
                        unwrapped917 = deconstruct_result916
                        pretty_data(pp, unwrapped917)
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
    flat931 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat931)
        write(pp, flat931)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1646 = _dollar_dollar.attrs
        else
            _t1646 = nothing
        end
        fields925 = (_dollar_dollar.name, _dollar_dollar.body, _t1646,)
        unwrapped_fields926 = fields925
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field927 = unwrapped_fields926[1]
        pretty_relation_id(pp, field927)
        newline(pp)
        field928 = unwrapped_fields926[2]
        pretty_abstraction(pp, field928)
        field929 = unwrapped_fields926[3]
        if !isnothing(field929)
            newline(pp)
            opt_val930 = field929
            pretty_attrs(pp, opt_val930)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat936 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat936)
        write(pp, flat936)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1648 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1647 = _t1648
        else
            _t1647 = nothing
        end
        deconstruct_result934 = _t1647
        if !isnothing(deconstruct_result934)
            unwrapped935 = deconstruct_result934
            write(pp, ":")
            write(pp, unwrapped935)
        else
            _dollar_dollar = msg
            _t1649 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result932 = _t1649
            if !isnothing(deconstruct_result932)
                unwrapped933 = deconstruct_result932
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped933))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat941 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat941)
        write(pp, flat941)
        return nothing
    else
        _dollar_dollar = msg
        _t1650 = deconstruct_bindings(pp, _dollar_dollar)
        fields937 = (_t1650, _dollar_dollar.value,)
        unwrapped_fields938 = fields937
        write(pp, "(")
        indent!(pp)
        field939 = unwrapped_fields938[1]
        pretty_bindings(pp, field939)
        newline(pp)
        field940 = unwrapped_fields938[2]
        pretty_formula(pp, field940)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat949 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat949)
        write(pp, flat949)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1651 = _dollar_dollar[2]
        else
            _t1651 = nothing
        end
        fields942 = (_dollar_dollar[1], _t1651,)
        unwrapped_fields943 = fields942
        write(pp, "[")
        indent!(pp)
        field944 = unwrapped_fields943[1]
        for (i1652, elem945) in enumerate(field944)
            i946 = i1652 - 1
            if (i946 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem945)
        end
        field947 = unwrapped_fields943[2]
        if !isnothing(field947)
            newline(pp)
            opt_val948 = field947
            pretty_value_bindings(pp, opt_val948)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat954 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat954)
        write(pp, flat954)
        return nothing
    else
        _dollar_dollar = msg
        fields950 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields951 = fields950
        field952 = unwrapped_fields951[1]
        write(pp, field952)
        write(pp, "::")
        field953 = unwrapped_fields951[2]
        pretty_type(pp, field953)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat983 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat983)
        write(pp, flat983)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1653 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1653 = nothing
        end
        deconstruct_result981 = _t1653
        if !isnothing(deconstruct_result981)
            unwrapped982 = deconstruct_result981
            pretty_unspecified_type(pp, unwrapped982)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1654 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1654 = nothing
            end
            deconstruct_result979 = _t1654
            if !isnothing(deconstruct_result979)
                unwrapped980 = deconstruct_result979
                pretty_string_type(pp, unwrapped980)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1655 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1655 = nothing
                end
                deconstruct_result977 = _t1655
                if !isnothing(deconstruct_result977)
                    unwrapped978 = deconstruct_result977
                    pretty_int_type(pp, unwrapped978)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1656 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1656 = nothing
                    end
                    deconstruct_result975 = _t1656
                    if !isnothing(deconstruct_result975)
                        unwrapped976 = deconstruct_result975
                        pretty_float_type(pp, unwrapped976)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1657 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1657 = nothing
                        end
                        deconstruct_result973 = _t1657
                        if !isnothing(deconstruct_result973)
                            unwrapped974 = deconstruct_result973
                            pretty_uint128_type(pp, unwrapped974)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1658 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1658 = nothing
                            end
                            deconstruct_result971 = _t1658
                            if !isnothing(deconstruct_result971)
                                unwrapped972 = deconstruct_result971
                                pretty_int128_type(pp, unwrapped972)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1659 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1659 = nothing
                                end
                                deconstruct_result969 = _t1659
                                if !isnothing(deconstruct_result969)
                                    unwrapped970 = deconstruct_result969
                                    pretty_date_type(pp, unwrapped970)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1660 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1660 = nothing
                                    end
                                    deconstruct_result967 = _t1660
                                    if !isnothing(deconstruct_result967)
                                        unwrapped968 = deconstruct_result967
                                        pretty_datetime_type(pp, unwrapped968)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1661 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1661 = nothing
                                        end
                                        deconstruct_result965 = _t1661
                                        if !isnothing(deconstruct_result965)
                                            unwrapped966 = deconstruct_result965
                                            pretty_missing_type(pp, unwrapped966)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1662 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1662 = nothing
                                            end
                                            deconstruct_result963 = _t1662
                                            if !isnothing(deconstruct_result963)
                                                unwrapped964 = deconstruct_result963
                                                pretty_decimal_type(pp, unwrapped964)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1663 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1663 = nothing
                                                end
                                                deconstruct_result961 = _t1663
                                                if !isnothing(deconstruct_result961)
                                                    unwrapped962 = deconstruct_result961
                                                    pretty_boolean_type(pp, unwrapped962)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1664 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1664 = nothing
                                                    end
                                                    deconstruct_result959 = _t1664
                                                    if !isnothing(deconstruct_result959)
                                                        unwrapped960 = deconstruct_result959
                                                        pretty_int32_type(pp, unwrapped960)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1665 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1665 = nothing
                                                        end
                                                        deconstruct_result957 = _t1665
                                                        if !isnothing(deconstruct_result957)
                                                            unwrapped958 = deconstruct_result957
                                                            pretty_float32_type(pp, unwrapped958)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1666 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1666 = nothing
                                                            end
                                                            deconstruct_result955 = _t1666
                                                            if !isnothing(deconstruct_result955)
                                                                unwrapped956 = deconstruct_result955
                                                                pretty_uint32_type(pp, unwrapped956)
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
    fields984 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields985 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields986 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields987 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields988 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields989 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields990 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields991 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields992 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat997 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat997)
        write(pp, flat997)
        return nothing
    else
        _dollar_dollar = msg
        fields993 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields994 = fields993
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field995 = unwrapped_fields994[1]
        write(pp, string(field995))
        newline(pp)
        field996 = unwrapped_fields994[2]
        write(pp, string(field996))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields998 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields999 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields1000 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields1001 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1005 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1005)
        write(pp, flat1005)
        return nothing
    else
        fields1002 = msg
        write(pp, "|")
        if !isempty(fields1002)
            write(pp, " ")
            for (i1667, elem1003) in enumerate(fields1002)
                i1004 = i1667 - 1
                if (i1004 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1003)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1032 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1032)
        write(pp, flat1032)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1668 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1668 = nothing
        end
        deconstruct_result1030 = _t1668
        if !isnothing(deconstruct_result1030)
            unwrapped1031 = deconstruct_result1030
            pretty_true(pp, unwrapped1031)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1669 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1669 = nothing
            end
            deconstruct_result1028 = _t1669
            if !isnothing(deconstruct_result1028)
                unwrapped1029 = deconstruct_result1028
                pretty_false(pp, unwrapped1029)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1670 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1670 = nothing
                end
                deconstruct_result1026 = _t1670
                if !isnothing(deconstruct_result1026)
                    unwrapped1027 = deconstruct_result1026
                    pretty_exists(pp, unwrapped1027)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1671 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1671 = nothing
                    end
                    deconstruct_result1024 = _t1671
                    if !isnothing(deconstruct_result1024)
                        unwrapped1025 = deconstruct_result1024
                        pretty_reduce(pp, unwrapped1025)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1672 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1672 = nothing
                        end
                        deconstruct_result1022 = _t1672
                        if !isnothing(deconstruct_result1022)
                            unwrapped1023 = deconstruct_result1022
                            pretty_conjunction(pp, unwrapped1023)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1673 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1673 = nothing
                            end
                            deconstruct_result1020 = _t1673
                            if !isnothing(deconstruct_result1020)
                                unwrapped1021 = deconstruct_result1020
                                pretty_disjunction(pp, unwrapped1021)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1674 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1674 = nothing
                                end
                                deconstruct_result1018 = _t1674
                                if !isnothing(deconstruct_result1018)
                                    unwrapped1019 = deconstruct_result1018
                                    pretty_not(pp, unwrapped1019)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1675 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1675 = nothing
                                    end
                                    deconstruct_result1016 = _t1675
                                    if !isnothing(deconstruct_result1016)
                                        unwrapped1017 = deconstruct_result1016
                                        pretty_ffi(pp, unwrapped1017)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1676 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1676 = nothing
                                        end
                                        deconstruct_result1014 = _t1676
                                        if !isnothing(deconstruct_result1014)
                                            unwrapped1015 = deconstruct_result1014
                                            pretty_atom(pp, unwrapped1015)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1677 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1677 = nothing
                                            end
                                            deconstruct_result1012 = _t1677
                                            if !isnothing(deconstruct_result1012)
                                                unwrapped1013 = deconstruct_result1012
                                                pretty_pragma(pp, unwrapped1013)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1678 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1678 = nothing
                                                end
                                                deconstruct_result1010 = _t1678
                                                if !isnothing(deconstruct_result1010)
                                                    unwrapped1011 = deconstruct_result1010
                                                    pretty_primitive(pp, unwrapped1011)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1679 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1679 = nothing
                                                    end
                                                    deconstruct_result1008 = _t1679
                                                    if !isnothing(deconstruct_result1008)
                                                        unwrapped1009 = deconstruct_result1008
                                                        pretty_rel_atom(pp, unwrapped1009)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1680 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1680 = nothing
                                                        end
                                                        deconstruct_result1006 = _t1680
                                                        if !isnothing(deconstruct_result1006)
                                                            unwrapped1007 = deconstruct_result1006
                                                            pretty_cast(pp, unwrapped1007)
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
    fields1033 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1034 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1039 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1039)
        write(pp, flat1039)
        return nothing
    else
        _dollar_dollar = msg
        _t1681 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1035 = (_t1681, _dollar_dollar.body.value,)
        unwrapped_fields1036 = fields1035
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1037 = unwrapped_fields1036[1]
        pretty_bindings(pp, field1037)
        newline(pp)
        field1038 = unwrapped_fields1036[2]
        pretty_formula(pp, field1038)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1045 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1045)
        write(pp, flat1045)
        return nothing
    else
        _dollar_dollar = msg
        fields1040 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1041 = fields1040
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1042 = unwrapped_fields1041[1]
        pretty_abstraction(pp, field1042)
        newline(pp)
        field1043 = unwrapped_fields1041[2]
        pretty_abstraction(pp, field1043)
        newline(pp)
        field1044 = unwrapped_fields1041[3]
        pretty_terms(pp, field1044)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1049 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1049)
        write(pp, flat1049)
        return nothing
    else
        fields1046 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1046)
            newline(pp)
            for (i1682, elem1047) in enumerate(fields1046)
                i1048 = i1682 - 1
                if (i1048 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1047)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1054 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1054)
        write(pp, flat1054)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1683 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1683 = nothing
        end
        deconstruct_result1052 = _t1683
        if !isnothing(deconstruct_result1052)
            unwrapped1053 = deconstruct_result1052
            pretty_var(pp, unwrapped1053)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1684 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1684 = nothing
            end
            deconstruct_result1050 = _t1684
            if !isnothing(deconstruct_result1050)
                unwrapped1051 = deconstruct_result1050
                pretty_value(pp, unwrapped1051)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1057 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1057)
        write(pp, flat1057)
        return nothing
    else
        _dollar_dollar = msg
        fields1055 = _dollar_dollar.name
        unwrapped_fields1056 = fields1055
        write(pp, unwrapped_fields1056)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1083 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1083)
        write(pp, flat1083)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1685 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1685 = nothing
        end
        deconstruct_result1081 = _t1685
        if !isnothing(deconstruct_result1081)
            unwrapped1082 = deconstruct_result1081
            pretty_date(pp, unwrapped1082)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1686 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1686 = nothing
            end
            deconstruct_result1079 = _t1686
            if !isnothing(deconstruct_result1079)
                unwrapped1080 = deconstruct_result1079
                pretty_datetime(pp, unwrapped1080)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1687 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1687 = nothing
                end
                deconstruct_result1077 = _t1687
                if !isnothing(deconstruct_result1077)
                    unwrapped1078 = deconstruct_result1077
                    write(pp, format_string(pp, unwrapped1078))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1688 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1688 = nothing
                    end
                    deconstruct_result1075 = _t1688
                    if !isnothing(deconstruct_result1075)
                        unwrapped1076 = deconstruct_result1075
                        write(pp, format_int32(pp, unwrapped1076))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1689 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1689 = nothing
                        end
                        deconstruct_result1073 = _t1689
                        if !isnothing(deconstruct_result1073)
                            unwrapped1074 = deconstruct_result1073
                            write(pp, format_int(pp, unwrapped1074))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1690 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1690 = nothing
                            end
                            deconstruct_result1071 = _t1690
                            if !isnothing(deconstruct_result1071)
                                unwrapped1072 = deconstruct_result1071
                                write(pp, format_float32(pp, unwrapped1072))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1691 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1691 = nothing
                                end
                                deconstruct_result1069 = _t1691
                                if !isnothing(deconstruct_result1069)
                                    unwrapped1070 = deconstruct_result1069
                                    write(pp, format_float(pp, unwrapped1070))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1692 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1692 = nothing
                                    end
                                    deconstruct_result1067 = _t1692
                                    if !isnothing(deconstruct_result1067)
                                        unwrapped1068 = deconstruct_result1067
                                        write(pp, format_uint32(pp, unwrapped1068))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1693 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1693 = nothing
                                        end
                                        deconstruct_result1065 = _t1693
                                        if !isnothing(deconstruct_result1065)
                                            unwrapped1066 = deconstruct_result1065
                                            write(pp, format_uint128(pp, unwrapped1066))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1694 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1694 = nothing
                                            end
                                            deconstruct_result1063 = _t1694
                                            if !isnothing(deconstruct_result1063)
                                                unwrapped1064 = deconstruct_result1063
                                                write(pp, format_int128(pp, unwrapped1064))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1695 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1695 = nothing
                                                end
                                                deconstruct_result1061 = _t1695
                                                if !isnothing(deconstruct_result1061)
                                                    unwrapped1062 = deconstruct_result1061
                                                    write(pp, format_decimal(pp, unwrapped1062))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1696 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1696 = nothing
                                                    end
                                                    deconstruct_result1059 = _t1696
                                                    if !isnothing(deconstruct_result1059)
                                                        unwrapped1060 = deconstruct_result1059
                                                        pretty_boolean_value(pp, unwrapped1060)
                                                    else
                                                        fields1058 = msg
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
    flat1089 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1089)
        write(pp, flat1089)
        return nothing
    else
        _dollar_dollar = msg
        fields1084 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1085 = fields1084
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1086 = unwrapped_fields1085[1]
        write(pp, format_int(pp, field1086))
        newline(pp)
        field1087 = unwrapped_fields1085[2]
        write(pp, format_int(pp, field1087))
        newline(pp)
        field1088 = unwrapped_fields1085[3]
        write(pp, format_int(pp, field1088))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1100 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1100)
        write(pp, flat1100)
        return nothing
    else
        _dollar_dollar = msg
        fields1090 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1091 = fields1090
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1092 = unwrapped_fields1091[1]
        write(pp, format_int(pp, field1092))
        newline(pp)
        field1093 = unwrapped_fields1091[2]
        write(pp, format_int(pp, field1093))
        newline(pp)
        field1094 = unwrapped_fields1091[3]
        write(pp, format_int(pp, field1094))
        newline(pp)
        field1095 = unwrapped_fields1091[4]
        write(pp, format_int(pp, field1095))
        newline(pp)
        field1096 = unwrapped_fields1091[5]
        write(pp, format_int(pp, field1096))
        newline(pp)
        field1097 = unwrapped_fields1091[6]
        write(pp, format_int(pp, field1097))
        field1098 = unwrapped_fields1091[7]
        if !isnothing(field1098)
            newline(pp)
            opt_val1099 = field1098
            write(pp, format_int(pp, opt_val1099))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1105 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1105)
        write(pp, flat1105)
        return nothing
    else
        _dollar_dollar = msg
        fields1101 = _dollar_dollar.args
        unwrapped_fields1102 = fields1101
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1102)
            newline(pp)
            for (i1697, elem1103) in enumerate(unwrapped_fields1102)
                i1104 = i1697 - 1
                if (i1104 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1103)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1110 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1110)
        write(pp, flat1110)
        return nothing
    else
        _dollar_dollar = msg
        fields1106 = _dollar_dollar.args
        unwrapped_fields1107 = fields1106
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1107)
            newline(pp)
            for (i1698, elem1108) in enumerate(unwrapped_fields1107)
                i1109 = i1698 - 1
                if (i1109 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1108)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1113 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1113)
        write(pp, flat1113)
        return nothing
    else
        _dollar_dollar = msg
        fields1111 = _dollar_dollar.arg
        unwrapped_fields1112 = fields1111
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1112)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1119 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1119)
        write(pp, flat1119)
        return nothing
    else
        _dollar_dollar = msg
        fields1114 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1115 = fields1114
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1116 = unwrapped_fields1115[1]
        pretty_name(pp, field1116)
        newline(pp)
        field1117 = unwrapped_fields1115[2]
        pretty_ffi_args(pp, field1117)
        newline(pp)
        field1118 = unwrapped_fields1115[3]
        pretty_terms(pp, field1118)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1121 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1121)
        write(pp, flat1121)
        return nothing
    else
        fields1120 = msg
        write(pp, ":")
        write(pp, fields1120)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1125 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1125)
        write(pp, flat1125)
        return nothing
    else
        fields1122 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1122)
            newline(pp)
            for (i1699, elem1123) in enumerate(fields1122)
                i1124 = i1699 - 1
                if (i1124 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1123)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1132 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1132)
        write(pp, flat1132)
        return nothing
    else
        _dollar_dollar = msg
        fields1126 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1127 = fields1126
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1128 = unwrapped_fields1127[1]
        pretty_relation_id(pp, field1128)
        field1129 = unwrapped_fields1127[2]
        if !isempty(field1129)
            newline(pp)
            for (i1700, elem1130) in enumerate(field1129)
                i1131 = i1700 - 1
                if (i1131 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1130)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1139 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1139)
        write(pp, flat1139)
        return nothing
    else
        _dollar_dollar = msg
        fields1133 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1134 = fields1133
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1135 = unwrapped_fields1134[1]
        pretty_name(pp, field1135)
        field1136 = unwrapped_fields1134[2]
        if !isempty(field1136)
            newline(pp)
            for (i1701, elem1137) in enumerate(field1136)
                i1138 = i1701 - 1
                if (i1138 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1137)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1155 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1155)
        write(pp, flat1155)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1702 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1702 = nothing
        end
        guard_result1154 = _t1702
        if !isnothing(guard_result1154)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1703 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1703 = nothing
            end
            guard_result1153 = _t1703
            if !isnothing(guard_result1153)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1704 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1704 = nothing
                end
                guard_result1152 = _t1704
                if !isnothing(guard_result1152)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1705 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1705 = nothing
                    end
                    guard_result1151 = _t1705
                    if !isnothing(guard_result1151)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1706 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1706 = nothing
                        end
                        guard_result1150 = _t1706
                        if !isnothing(guard_result1150)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1707 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1707 = nothing
                            end
                            guard_result1149 = _t1707
                            if !isnothing(guard_result1149)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1708 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1708 = nothing
                                end
                                guard_result1148 = _t1708
                                if !isnothing(guard_result1148)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1709 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1709 = nothing
                                    end
                                    guard_result1147 = _t1709
                                    if !isnothing(guard_result1147)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1710 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1710 = nothing
                                        end
                                        guard_result1146 = _t1710
                                        if !isnothing(guard_result1146)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1140 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1141 = fields1140
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1142 = unwrapped_fields1141[1]
                                            pretty_name(pp, field1142)
                                            field1143 = unwrapped_fields1141[2]
                                            if !isempty(field1143)
                                                newline(pp)
                                                for (i1711, elem1144) in enumerate(field1143)
                                                    i1145 = i1711 - 1
                                                    if (i1145 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1144)
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
    flat1160 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1160)
        write(pp, flat1160)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1712 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1712 = nothing
        end
        fields1156 = _t1712
        unwrapped_fields1157 = fields1156
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1158 = unwrapped_fields1157[1]
        pretty_term(pp, field1158)
        newline(pp)
        field1159 = unwrapped_fields1157[2]
        pretty_term(pp, field1159)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1165 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1165)
        write(pp, flat1165)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1713 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1713 = nothing
        end
        fields1161 = _t1713
        unwrapped_fields1162 = fields1161
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1163 = unwrapped_fields1162[1]
        pretty_term(pp, field1163)
        newline(pp)
        field1164 = unwrapped_fields1162[2]
        pretty_term(pp, field1164)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1170 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1170)
        write(pp, flat1170)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1714 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1714 = nothing
        end
        fields1166 = _t1714
        unwrapped_fields1167 = fields1166
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1168 = unwrapped_fields1167[1]
        pretty_term(pp, field1168)
        newline(pp)
        field1169 = unwrapped_fields1167[2]
        pretty_term(pp, field1169)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1175 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1175)
        write(pp, flat1175)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1715 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1715 = nothing
        end
        fields1171 = _t1715
        unwrapped_fields1172 = fields1171
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1173 = unwrapped_fields1172[1]
        pretty_term(pp, field1173)
        newline(pp)
        field1174 = unwrapped_fields1172[2]
        pretty_term(pp, field1174)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1180 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1180)
        write(pp, flat1180)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1716 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1716 = nothing
        end
        fields1176 = _t1716
        unwrapped_fields1177 = fields1176
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1178 = unwrapped_fields1177[1]
        pretty_term(pp, field1178)
        newline(pp)
        field1179 = unwrapped_fields1177[2]
        pretty_term(pp, field1179)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1186 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1186)
        write(pp, flat1186)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1717 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1717 = nothing
        end
        fields1181 = _t1717
        unwrapped_fields1182 = fields1181
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1183 = unwrapped_fields1182[1]
        pretty_term(pp, field1183)
        newline(pp)
        field1184 = unwrapped_fields1182[2]
        pretty_term(pp, field1184)
        newline(pp)
        field1185 = unwrapped_fields1182[3]
        pretty_term(pp, field1185)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1192 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1192)
        write(pp, flat1192)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1718 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1718 = nothing
        end
        fields1187 = _t1718
        unwrapped_fields1188 = fields1187
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1189 = unwrapped_fields1188[1]
        pretty_term(pp, field1189)
        newline(pp)
        field1190 = unwrapped_fields1188[2]
        pretty_term(pp, field1190)
        newline(pp)
        field1191 = unwrapped_fields1188[3]
        pretty_term(pp, field1191)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1198 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1198)
        write(pp, flat1198)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1719 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1719 = nothing
        end
        fields1193 = _t1719
        unwrapped_fields1194 = fields1193
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1195 = unwrapped_fields1194[1]
        pretty_term(pp, field1195)
        newline(pp)
        field1196 = unwrapped_fields1194[2]
        pretty_term(pp, field1196)
        newline(pp)
        field1197 = unwrapped_fields1194[3]
        pretty_term(pp, field1197)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1204 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1204)
        write(pp, flat1204)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1720 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1720 = nothing
        end
        fields1199 = _t1720
        unwrapped_fields1200 = fields1199
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1201 = unwrapped_fields1200[1]
        pretty_term(pp, field1201)
        newline(pp)
        field1202 = unwrapped_fields1200[2]
        pretty_term(pp, field1202)
        newline(pp)
        field1203 = unwrapped_fields1200[3]
        pretty_term(pp, field1203)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1209 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1209)
        write(pp, flat1209)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1721 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1721 = nothing
        end
        deconstruct_result1207 = _t1721
        if !isnothing(deconstruct_result1207)
            unwrapped1208 = deconstruct_result1207
            pretty_specialized_value(pp, unwrapped1208)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1722 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1722 = nothing
            end
            deconstruct_result1205 = _t1722
            if !isnothing(deconstruct_result1205)
                unwrapped1206 = deconstruct_result1205
                pretty_term(pp, unwrapped1206)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1211 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1211)
        write(pp, flat1211)
        return nothing
    else
        fields1210 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1210)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1218 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1218)
        write(pp, flat1218)
        return nothing
    else
        _dollar_dollar = msg
        fields1212 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1213 = fields1212
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1214 = unwrapped_fields1213[1]
        pretty_name(pp, field1214)
        field1215 = unwrapped_fields1213[2]
        if !isempty(field1215)
            newline(pp)
            for (i1723, elem1216) in enumerate(field1215)
                i1217 = i1723 - 1
                if (i1217 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1216)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1223 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1223)
        write(pp, flat1223)
        return nothing
    else
        _dollar_dollar = msg
        fields1219 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1220 = fields1219
        write(pp, "(cast")
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

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1227 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1227)
        write(pp, flat1227)
        return nothing
    else
        fields1224 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1224)
            newline(pp)
            for (i1724, elem1225) in enumerate(fields1224)
                i1226 = i1724 - 1
                if (i1226 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1225)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1234 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1234)
        write(pp, flat1234)
        return nothing
    else
        _dollar_dollar = msg
        fields1228 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1229 = fields1228
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1230 = unwrapped_fields1229[1]
        pretty_name(pp, field1230)
        field1231 = unwrapped_fields1229[2]
        if !isempty(field1231)
            newline(pp)
            for (i1725, elem1232) in enumerate(field1231)
                i1233 = i1725 - 1
                if (i1233 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1232)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1243 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1243)
        write(pp, flat1243)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1726 = _dollar_dollar.attrs
        else
            _t1726 = nothing
        end
        fields1235 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1726,)
        unwrapped_fields1236 = fields1235
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1237 = unwrapped_fields1236[1]
        if !isempty(field1237)
            newline(pp)
            for (i1727, elem1238) in enumerate(field1237)
                i1239 = i1727 - 1
                if (i1239 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1238)
            end
        end
        newline(pp)
        field1240 = unwrapped_fields1236[2]
        pretty_script(pp, field1240)
        field1241 = unwrapped_fields1236[3]
        if !isnothing(field1241)
            newline(pp)
            opt_val1242 = field1241
            pretty_attrs(pp, opt_val1242)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1248 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1248)
        write(pp, flat1248)
        return nothing
    else
        _dollar_dollar = msg
        fields1244 = _dollar_dollar.constructs
        unwrapped_fields1245 = fields1244
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1245)
            newline(pp)
            for (i1728, elem1246) in enumerate(unwrapped_fields1245)
                i1247 = i1728 - 1
                if (i1247 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1246)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1253 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1729 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1729 = nothing
        end
        deconstruct_result1251 = _t1729
        if !isnothing(deconstruct_result1251)
            unwrapped1252 = deconstruct_result1251
            pretty_loop(pp, unwrapped1252)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1730 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1730 = nothing
            end
            deconstruct_result1249 = _t1730
            if !isnothing(deconstruct_result1249)
                unwrapped1250 = deconstruct_result1249
                pretty_instruction(pp, unwrapped1250)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1260 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1260)
        write(pp, flat1260)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1731 = _dollar_dollar.attrs
        else
            _t1731 = nothing
        end
        fields1254 = (_dollar_dollar.init, _dollar_dollar.body, _t1731,)
        unwrapped_fields1255 = fields1254
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1256 = unwrapped_fields1255[1]
        pretty_init(pp, field1256)
        newline(pp)
        field1257 = unwrapped_fields1255[2]
        pretty_script(pp, field1257)
        field1258 = unwrapped_fields1255[3]
        if !isnothing(field1258)
            newline(pp)
            opt_val1259 = field1258
            pretty_attrs(pp, opt_val1259)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1264 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1264)
        write(pp, flat1264)
        return nothing
    else
        fields1261 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1261)
            newline(pp)
            for (i1732, elem1262) in enumerate(fields1261)
                i1263 = i1732 - 1
                if (i1263 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1262)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1275 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1275)
        write(pp, flat1275)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1733 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1733 = nothing
        end
        deconstruct_result1273 = _t1733
        if !isnothing(deconstruct_result1273)
            unwrapped1274 = deconstruct_result1273
            pretty_assign(pp, unwrapped1274)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1734 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1734 = nothing
            end
            deconstruct_result1271 = _t1734
            if !isnothing(deconstruct_result1271)
                unwrapped1272 = deconstruct_result1271
                pretty_upsert(pp, unwrapped1272)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1735 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1735 = nothing
                end
                deconstruct_result1269 = _t1735
                if !isnothing(deconstruct_result1269)
                    unwrapped1270 = deconstruct_result1269
                    pretty_break(pp, unwrapped1270)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1736 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1736 = nothing
                    end
                    deconstruct_result1267 = _t1736
                    if !isnothing(deconstruct_result1267)
                        unwrapped1268 = deconstruct_result1267
                        pretty_monoid_def(pp, unwrapped1268)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1737 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1737 = nothing
                        end
                        deconstruct_result1265 = _t1737
                        if !isnothing(deconstruct_result1265)
                            unwrapped1266 = deconstruct_result1265
                            pretty_monus_def(pp, unwrapped1266)
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
    flat1282 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1282)
        write(pp, flat1282)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1738 = _dollar_dollar.attrs
        else
            _t1738 = nothing
        end
        fields1276 = (_dollar_dollar.name, _dollar_dollar.body, _t1738,)
        unwrapped_fields1277 = fields1276
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1278 = unwrapped_fields1277[1]
        pretty_relation_id(pp, field1278)
        newline(pp)
        field1279 = unwrapped_fields1277[2]
        pretty_abstraction(pp, field1279)
        field1280 = unwrapped_fields1277[3]
        if !isnothing(field1280)
            newline(pp)
            opt_val1281 = field1280
            pretty_attrs(pp, opt_val1281)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1289 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1289)
        write(pp, flat1289)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1739 = _dollar_dollar.attrs
        else
            _t1739 = nothing
        end
        fields1283 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1739,)
        unwrapped_fields1284 = fields1283
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1285 = unwrapped_fields1284[1]
        pretty_relation_id(pp, field1285)
        newline(pp)
        field1286 = unwrapped_fields1284[2]
        pretty_abstraction_with_arity(pp, field1286)
        field1287 = unwrapped_fields1284[3]
        if !isnothing(field1287)
            newline(pp)
            opt_val1288 = field1287
            pretty_attrs(pp, opt_val1288)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1294 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1294)
        write(pp, flat1294)
        return nothing
    else
        _dollar_dollar = msg
        _t1740 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1290 = (_t1740, _dollar_dollar[1].value,)
        unwrapped_fields1291 = fields1290
        write(pp, "(")
        indent!(pp)
        field1292 = unwrapped_fields1291[1]
        pretty_bindings(pp, field1292)
        newline(pp)
        field1293 = unwrapped_fields1291[2]
        pretty_formula(pp, field1293)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1301 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1301)
        write(pp, flat1301)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1741 = _dollar_dollar.attrs
        else
            _t1741 = nothing
        end
        fields1295 = (_dollar_dollar.name, _dollar_dollar.body, _t1741,)
        unwrapped_fields1296 = fields1295
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1297 = unwrapped_fields1296[1]
        pretty_relation_id(pp, field1297)
        newline(pp)
        field1298 = unwrapped_fields1296[2]
        pretty_abstraction(pp, field1298)
        field1299 = unwrapped_fields1296[3]
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

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1309 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1309)
        write(pp, flat1309)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1742 = _dollar_dollar.attrs
        else
            _t1742 = nothing
        end
        fields1302 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1742,)
        unwrapped_fields1303 = fields1302
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1304 = unwrapped_fields1303[1]
        pretty_monoid(pp, field1304)
        newline(pp)
        field1305 = unwrapped_fields1303[2]
        pretty_relation_id(pp, field1305)
        newline(pp)
        field1306 = unwrapped_fields1303[3]
        pretty_abstraction_with_arity(pp, field1306)
        field1307 = unwrapped_fields1303[4]
        if !isnothing(field1307)
            newline(pp)
            opt_val1308 = field1307
            pretty_attrs(pp, opt_val1308)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1318 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1318)
        write(pp, flat1318)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1743 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1743 = nothing
        end
        deconstruct_result1316 = _t1743
        if !isnothing(deconstruct_result1316)
            unwrapped1317 = deconstruct_result1316
            pretty_or_monoid(pp, unwrapped1317)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1744 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1744 = nothing
            end
            deconstruct_result1314 = _t1744
            if !isnothing(deconstruct_result1314)
                unwrapped1315 = deconstruct_result1314
                pretty_min_monoid(pp, unwrapped1315)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1745 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1745 = nothing
                end
                deconstruct_result1312 = _t1745
                if !isnothing(deconstruct_result1312)
                    unwrapped1313 = deconstruct_result1312
                    pretty_max_monoid(pp, unwrapped1313)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1746 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1746 = nothing
                    end
                    deconstruct_result1310 = _t1746
                    if !isnothing(deconstruct_result1310)
                        unwrapped1311 = deconstruct_result1310
                        pretty_sum_monoid(pp, unwrapped1311)
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
    fields1319 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1322 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1322)
        write(pp, flat1322)
        return nothing
    else
        _dollar_dollar = msg
        fields1320 = _dollar_dollar.var"#type"
        unwrapped_fields1321 = fields1320
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1321)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1325 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1325)
        write(pp, flat1325)
        return nothing
    else
        _dollar_dollar = msg
        fields1323 = _dollar_dollar.var"#type"
        unwrapped_fields1324 = fields1323
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1324)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1328 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1328)
        write(pp, flat1328)
        return nothing
    else
        _dollar_dollar = msg
        fields1326 = _dollar_dollar.var"#type"
        unwrapped_fields1327 = fields1326
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1327)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1336 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1336)
        write(pp, flat1336)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1747 = _dollar_dollar.attrs
        else
            _t1747 = nothing
        end
        fields1329 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1747,)
        unwrapped_fields1330 = fields1329
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1331 = unwrapped_fields1330[1]
        pretty_monoid(pp, field1331)
        newline(pp)
        field1332 = unwrapped_fields1330[2]
        pretty_relation_id(pp, field1332)
        newline(pp)
        field1333 = unwrapped_fields1330[3]
        pretty_abstraction_with_arity(pp, field1333)
        field1334 = unwrapped_fields1330[4]
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

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1343 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1343)
        write(pp, flat1343)
        return nothing
    else
        _dollar_dollar = msg
        fields1337 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1338 = fields1337
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1339 = unwrapped_fields1338[1]
        pretty_relation_id(pp, field1339)
        newline(pp)
        field1340 = unwrapped_fields1338[2]
        pretty_abstraction(pp, field1340)
        newline(pp)
        field1341 = unwrapped_fields1338[3]
        pretty_functional_dependency_keys(pp, field1341)
        newline(pp)
        field1342 = unwrapped_fields1338[4]
        pretty_functional_dependency_values(pp, field1342)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1347 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1347)
        write(pp, flat1347)
        return nothing
    else
        fields1344 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1344)
            newline(pp)
            for (i1748, elem1345) in enumerate(fields1344)
                i1346 = i1748 - 1
                if (i1346 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1345)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1351 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1351)
        write(pp, flat1351)
        return nothing
    else
        fields1348 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1348)
            newline(pp)
            for (i1749, elem1349) in enumerate(fields1348)
                i1350 = i1749 - 1
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

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1360 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1360)
        write(pp, flat1360)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1750 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1750 = nothing
        end
        deconstruct_result1358 = _t1750
        if !isnothing(deconstruct_result1358)
            unwrapped1359 = deconstruct_result1358
            pretty_edb(pp, unwrapped1359)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1751 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1751 = nothing
            end
            deconstruct_result1356 = _t1751
            if !isnothing(deconstruct_result1356)
                unwrapped1357 = deconstruct_result1356
                pretty_betree_relation(pp, unwrapped1357)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1752 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1752 = nothing
                end
                deconstruct_result1354 = _t1752
                if !isnothing(deconstruct_result1354)
                    unwrapped1355 = deconstruct_result1354
                    pretty_csv_data(pp, unwrapped1355)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1753 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1753 = nothing
                    end
                    deconstruct_result1352 = _t1753
                    if !isnothing(deconstruct_result1352)
                        unwrapped1353 = deconstruct_result1352
                        pretty_iceberg_data(pp, unwrapped1353)
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
    flat1366 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1366)
        write(pp, flat1366)
        return nothing
    else
        _dollar_dollar = msg
        fields1361 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1362 = fields1361
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1363 = unwrapped_fields1362[1]
        pretty_relation_id(pp, field1363)
        newline(pp)
        field1364 = unwrapped_fields1362[2]
        pretty_edb_path(pp, field1364)
        newline(pp)
        field1365 = unwrapped_fields1362[3]
        pretty_edb_types(pp, field1365)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1370 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1370)
        write(pp, flat1370)
        return nothing
    else
        fields1367 = msg
        write(pp, "[")
        indent!(pp)
        for (i1754, elem1368) in enumerate(fields1367)
            i1369 = i1754 - 1
            if (i1369 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1368))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1374 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1374)
        write(pp, flat1374)
        return nothing
    else
        fields1371 = msg
        write(pp, "[")
        indent!(pp)
        for (i1755, elem1372) in enumerate(fields1371)
            i1373 = i1755 - 1
            if (i1373 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1372)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1379 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1379)
        write(pp, flat1379)
        return nothing
    else
        _dollar_dollar = msg
        fields1375 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1376 = fields1375
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1377 = unwrapped_fields1376[1]
        pretty_relation_id(pp, field1377)
        newline(pp)
        field1378 = unwrapped_fields1376[2]
        pretty_betree_info(pp, field1378)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1385 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1385)
        write(pp, flat1385)
        return nothing
    else
        _dollar_dollar = msg
        _t1756 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1380 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1756,)
        unwrapped_fields1381 = fields1380
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1382 = unwrapped_fields1381[1]
        pretty_betree_info_key_types(pp, field1382)
        newline(pp)
        field1383 = unwrapped_fields1381[2]
        pretty_betree_info_value_types(pp, field1383)
        newline(pp)
        field1384 = unwrapped_fields1381[3]
        pretty_config_dict(pp, field1384)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1389 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1389)
        write(pp, flat1389)
        return nothing
    else
        fields1386 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1386)
            newline(pp)
            for (i1757, elem1387) in enumerate(fields1386)
                i1388 = i1757 - 1
                if (i1388 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1387)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1393 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1393)
        write(pp, flat1393)
        return nothing
    else
        fields1390 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1390)
            newline(pp)
            for (i1758, elem1391) in enumerate(fields1390)
                i1392 = i1758 - 1
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

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1403 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1403)
        write(pp, flat1403)
        return nothing
    else
        _dollar_dollar = msg
        _t1759 = deconstruct_csv_data_columns_optional(pp, _dollar_dollar)
        _t1760 = deconstruct_csv_data_target_optional(pp, _dollar_dollar)
        fields1394 = (_dollar_dollar.locator, _dollar_dollar.config, _t1759, _t1760, _dollar_dollar.asof,)
        unwrapped_fields1395 = fields1394
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1396 = unwrapped_fields1395[1]
        pretty_csvlocator(pp, field1396)
        newline(pp)
        field1397 = unwrapped_fields1395[2]
        pretty_csv_config(pp, field1397)
        field1398 = unwrapped_fields1395[3]
        if !isnothing(field1398)
            newline(pp)
            opt_val1399 = field1398
            pretty_gnf_columns(pp, opt_val1399)
        end
        field1400 = unwrapped_fields1395[4]
        if !isnothing(field1400)
            newline(pp)
            opt_val1401 = field1400
            pretty_csv_table(pp, opt_val1401)
        end
        newline(pp)
        field1402 = unwrapped_fields1395[5]
        pretty_csv_asof(pp, field1402)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1410 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1410)
        write(pp, flat1410)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1761 = _dollar_dollar.paths
        else
            _t1761 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1762 = String(copy(_dollar_dollar.inline_data))
        else
            _t1762 = nothing
        end
        fields1404 = (_t1761, _t1762,)
        unwrapped_fields1405 = fields1404
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1406 = unwrapped_fields1405[1]
        if !isnothing(field1406)
            newline(pp)
            opt_val1407 = field1406
            pretty_csv_locator_paths(pp, opt_val1407)
        end
        field1408 = unwrapped_fields1405[2]
        if !isnothing(field1408)
            newline(pp)
            opt_val1409 = field1408
            pretty_csv_locator_inline_data(pp, opt_val1409)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1414 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1414)
        write(pp, flat1414)
        return nothing
    else
        fields1411 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1411)
            newline(pp)
            for (i1763, elem1412) in enumerate(fields1411)
                i1413 = i1763 - 1
                if (i1413 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1412))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1416 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1416)
        write(pp, flat1416)
        return nothing
    else
        fields1415 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1415))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1419 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1419)
        write(pp, flat1419)
        return nothing
    else
        _dollar_dollar = msg
        _t1764 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1417 = _t1764
        unwrapped_fields1418 = fields1417
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1418)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1423 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1423)
        write(pp, flat1423)
        return nothing
    else
        fields1420 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1420)
            newline(pp)
            for (i1765, elem1421) in enumerate(fields1420)
                i1422 = i1765 - 1
                if (i1422 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1421)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1432 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1432)
        write(pp, flat1432)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1766 = _dollar_dollar.target_id
        else
            _t1766 = nothing
        end
        fields1424 = (_dollar_dollar.column_path, _t1766, _dollar_dollar.types,)
        unwrapped_fields1425 = fields1424
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1426 = unwrapped_fields1425[1]
        pretty_gnf_column_path(pp, field1426)
        field1427 = unwrapped_fields1425[2]
        if !isnothing(field1427)
            newline(pp)
            opt_val1428 = field1427
            pretty_relation_id(pp, opt_val1428)
        end
        newline(pp)
        write(pp, "[")
        field1429 = unwrapped_fields1425[3]
        for (i1767, elem1430) in enumerate(field1429)
            i1431 = i1767 - 1
            if (i1431 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1430)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1439 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1439)
        write(pp, flat1439)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1768 = _dollar_dollar[1]
        else
            _t1768 = nothing
        end
        deconstruct_result1437 = _t1768
        if !isnothing(deconstruct_result1437)
            unwrapped1438 = deconstruct_result1437
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1438))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1769 = _dollar_dollar
            else
                _t1769 = nothing
            end
            deconstruct_result1433 = _t1769
            if !isnothing(deconstruct_result1433)
                unwrapped1434 = deconstruct_result1433
                write(pp, "[")
                indent!(pp)
                for (i1770, elem1435) in enumerate(unwrapped1434)
                    i1436 = i1770 - 1
                    if (i1436 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1435))
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

function pretty_csv_table(pp::PrettyPrinter, msg::Proto.CSVTarget)
    flat1449 = try_flat(pp, msg, pretty_csv_table)
    if !isnothing(flat1449)
        write(pp, flat1449)
        return nothing
    else
        _dollar_dollar = msg
        fields1440 = (_dollar_dollar.target_id, _dollar_dollar.column_names, _dollar_dollar.types,)
        unwrapped_fields1441 = fields1440
        write(pp, "(table")
        indent_sexp!(pp)
        newline(pp)
        field1442 = unwrapped_fields1441[1]
        pretty_relation_id(pp, field1442)
        newline(pp)
        write(pp, "[")
        field1443 = unwrapped_fields1441[2]
        for (i1771, elem1444) in enumerate(field1443)
            i1445 = i1771 - 1
            if (i1445 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1444))
        end
        write(pp, "]")
        newline(pp)
        write(pp, "[")
        field1446 = unwrapped_fields1441[3]
        for (i1772, elem1447) in enumerate(field1446)
            i1448 = i1772 - 1
            if (i1448 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1447)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1451 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1451)
        write(pp, flat1451)
        return nothing
    else
        fields1450 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1450))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1462 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1462)
        write(pp, flat1462)
        return nothing
    else
        _dollar_dollar = msg
        _t1773 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1774 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1452 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1773, _t1774, _dollar_dollar.returns_delta,)
        unwrapped_fields1453 = fields1452
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1454 = unwrapped_fields1453[1]
        pretty_iceberg_locator(pp, field1454)
        newline(pp)
        field1455 = unwrapped_fields1453[2]
        pretty_iceberg_catalog_config(pp, field1455)
        newline(pp)
        field1456 = unwrapped_fields1453[3]
        pretty_gnf_columns(pp, field1456)
        field1457 = unwrapped_fields1453[4]
        if !isnothing(field1457)
            newline(pp)
            opt_val1458 = field1457
            pretty_iceberg_from_snapshot(pp, opt_val1458)
        end
        field1459 = unwrapped_fields1453[5]
        if !isnothing(field1459)
            newline(pp)
            opt_val1460 = field1459
            pretty_iceberg_to_snapshot(pp, opt_val1460)
        end
        newline(pp)
        field1461 = unwrapped_fields1453[6]
        pretty_boolean_value(pp, field1461)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1468 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1468)
        write(pp, flat1468)
        return nothing
    else
        _dollar_dollar = msg
        fields1463 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1464 = fields1463
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1465 = unwrapped_fields1464[1]
        pretty_iceberg_locator_table_name(pp, field1465)
        newline(pp)
        field1466 = unwrapped_fields1464[2]
        pretty_iceberg_locator_namespace(pp, field1466)
        newline(pp)
        field1467 = unwrapped_fields1464[3]
        pretty_iceberg_locator_warehouse(pp, field1467)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1470 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1470)
        write(pp, flat1470)
        return nothing
    else
        fields1469 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1469))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1474 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1474)
        write(pp, flat1474)
        return nothing
    else
        fields1471 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1471)
            newline(pp)
            for (i1775, elem1472) in enumerate(fields1471)
                i1473 = i1775 - 1
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

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1476 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1476)
        write(pp, flat1476)
        return nothing
    else
        fields1475 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1475))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1484 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1484)
        write(pp, flat1484)
        return nothing
    else
        _dollar_dollar = msg
        _t1776 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1477 = (_dollar_dollar.catalog_uri, _t1776, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1478 = fields1477
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1479 = unwrapped_fields1478[1]
        pretty_iceberg_catalog_uri(pp, field1479)
        field1480 = unwrapped_fields1478[2]
        if !isnothing(field1480)
            newline(pp)
            opt_val1481 = field1480
            pretty_iceberg_catalog_config_scope(pp, opt_val1481)
        end
        newline(pp)
        field1482 = unwrapped_fields1478[3]
        pretty_iceberg_properties(pp, field1482)
        newline(pp)
        field1483 = unwrapped_fields1478[4]
        pretty_iceberg_auth_properties(pp, field1483)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1486 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1486)
        write(pp, flat1486)
        return nothing
    else
        fields1485 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1485))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1488 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1488)
        write(pp, flat1488)
        return nothing
    else
        fields1487 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1487))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1492 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1492)
        write(pp, flat1492)
        return nothing
    else
        fields1489 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1489)
            newline(pp)
            for (i1777, elem1490) in enumerate(fields1489)
                i1491 = i1777 - 1
                if (i1491 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1490)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1497 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1497)
        write(pp, flat1497)
        return nothing
    else
        _dollar_dollar = msg
        fields1493 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1494 = fields1493
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1495 = unwrapped_fields1494[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1495))
        newline(pp)
        field1496 = unwrapped_fields1494[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1496))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1501 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1501)
        write(pp, flat1501)
        return nothing
    else
        fields1498 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1498)
            newline(pp)
            for (i1778, elem1499) in enumerate(fields1498)
                i1500 = i1778 - 1
                if (i1500 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1499)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1506 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1506)
        write(pp, flat1506)
        return nothing
    else
        _dollar_dollar = msg
        _t1779 = mask_secret_value(pp, _dollar_dollar)
        fields1502 = (_dollar_dollar[1], _t1779,)
        unwrapped_fields1503 = fields1502
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1504 = unwrapped_fields1503[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1504))
        newline(pp)
        field1505 = unwrapped_fields1503[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1505))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1508 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1508)
        write(pp, flat1508)
        return nothing
    else
        fields1507 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1507))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1510 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1510)
        write(pp, flat1510)
        return nothing
    else
        fields1509 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1509))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1513 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1513)
        write(pp, flat1513)
        return nothing
    else
        _dollar_dollar = msg
        fields1511 = _dollar_dollar.fragment_id
        unwrapped_fields1512 = fields1511
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1512)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1518 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1518)
        write(pp, flat1518)
        return nothing
    else
        _dollar_dollar = msg
        fields1514 = _dollar_dollar.relations
        unwrapped_fields1515 = fields1514
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1515)
            newline(pp)
            for (i1780, elem1516) in enumerate(unwrapped_fields1515)
                i1517 = i1780 - 1
                if (i1517 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1516)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1525 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1525)
        write(pp, flat1525)
        return nothing
    else
        _dollar_dollar = msg
        fields1519 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1520 = fields1519
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1521 = unwrapped_fields1520[1]
        pretty_edb_path(pp, field1521)
        field1522 = unwrapped_fields1520[2]
        if !isempty(field1522)
            newline(pp)
            for (i1781, elem1523) in enumerate(field1522)
                i1524 = i1781 - 1
                if (i1524 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1523)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1530 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1530)
        write(pp, flat1530)
        return nothing
    else
        _dollar_dollar = msg
        fields1526 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1527 = fields1526
        field1528 = unwrapped_fields1527[1]
        pretty_edb_path(pp, field1528)
        write(pp, " ")
        field1529 = unwrapped_fields1527[2]
        pretty_relation_id(pp, field1529)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1534 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1534)
        write(pp, flat1534)
        return nothing
    else
        fields1531 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1531)
            newline(pp)
            for (i1782, elem1532) in enumerate(fields1531)
                i1533 = i1782 - 1
                if (i1533 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1532)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1545 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1545)
        write(pp, flat1545)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1783 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1783 = nothing
        end
        deconstruct_result1543 = _t1783
        if !isnothing(deconstruct_result1543)
            unwrapped1544 = deconstruct_result1543
            pretty_demand(pp, unwrapped1544)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1784 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1784 = nothing
            end
            deconstruct_result1541 = _t1784
            if !isnothing(deconstruct_result1541)
                unwrapped1542 = deconstruct_result1541
                pretty_output(pp, unwrapped1542)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1785 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1785 = nothing
                end
                deconstruct_result1539 = _t1785
                if !isnothing(deconstruct_result1539)
                    unwrapped1540 = deconstruct_result1539
                    pretty_what_if(pp, unwrapped1540)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1786 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1786 = nothing
                    end
                    deconstruct_result1537 = _t1786
                    if !isnothing(deconstruct_result1537)
                        unwrapped1538 = deconstruct_result1537
                        pretty_abort(pp, unwrapped1538)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1787 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1787 = nothing
                        end
                        deconstruct_result1535 = _t1787
                        if !isnothing(deconstruct_result1535)
                            unwrapped1536 = deconstruct_result1535
                            pretty_export(pp, unwrapped1536)
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
    flat1548 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1548)
        write(pp, flat1548)
        return nothing
    else
        _dollar_dollar = msg
        fields1546 = _dollar_dollar.relation_id
        unwrapped_fields1547 = fields1546
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1547)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1553 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1553)
        write(pp, flat1553)
        return nothing
    else
        _dollar_dollar = msg
        fields1549 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1550 = fields1549
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1551 = unwrapped_fields1550[1]
        pretty_name(pp, field1551)
        newline(pp)
        field1552 = unwrapped_fields1550[2]
        pretty_relation_id(pp, field1552)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1558 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1558)
        write(pp, flat1558)
        return nothing
    else
        _dollar_dollar = msg
        fields1554 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1555 = fields1554
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1556 = unwrapped_fields1555[1]
        pretty_name(pp, field1556)
        newline(pp)
        field1557 = unwrapped_fields1555[2]
        pretty_epoch(pp, field1557)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1564 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1564)
        write(pp, flat1564)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1788 = _dollar_dollar.name
        else
            _t1788 = nothing
        end
        fields1559 = (_t1788, _dollar_dollar.relation_id,)
        unwrapped_fields1560 = fields1559
        write(pp, "(abort")
        indent_sexp!(pp)
        field1561 = unwrapped_fields1560[1]
        if !isnothing(field1561)
            newline(pp)
            opt_val1562 = field1561
            pretty_name(pp, opt_val1562)
        end
        newline(pp)
        field1563 = unwrapped_fields1560[2]
        pretty_relation_id(pp, field1563)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1569 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1569)
        write(pp, flat1569)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1789 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1789 = nothing
        end
        deconstruct_result1567 = _t1789
        if !isnothing(deconstruct_result1567)
            unwrapped1568 = deconstruct_result1567
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1568)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1790 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1790 = nothing
            end
            deconstruct_result1565 = _t1790
            if !isnothing(deconstruct_result1565)
                unwrapped1566 = deconstruct_result1565
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1566)
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
    flat1580 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1580)
        write(pp, flat1580)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1791 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1791 = nothing
        end
        deconstruct_result1575 = _t1791
        if !isnothing(deconstruct_result1575)
            unwrapped1576 = deconstruct_result1575
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1577 = unwrapped1576[1]
            pretty_export_csv_path(pp, field1577)
            newline(pp)
            field1578 = unwrapped1576[2]
            pretty_export_csv_source(pp, field1578)
            newline(pp)
            field1579 = unwrapped1576[3]
            pretty_csv_config(pp, field1579)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1793 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1792 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1793,)
            else
                _t1792 = nothing
            end
            deconstruct_result1570 = _t1792
            if !isnothing(deconstruct_result1570)
                unwrapped1571 = deconstruct_result1570
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1572 = unwrapped1571[1]
                pretty_export_csv_path(pp, field1572)
                newline(pp)
                field1573 = unwrapped1571[2]
                pretty_export_csv_columns_list(pp, field1573)
                newline(pp)
                field1574 = unwrapped1571[3]
                pretty_config_dict(pp, field1574)
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
    flat1582 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1582)
        write(pp, flat1582)
        return nothing
    else
        fields1581 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1581))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1589 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1589)
        write(pp, flat1589)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1794 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1794 = nothing
        end
        deconstruct_result1585 = _t1794
        if !isnothing(deconstruct_result1585)
            unwrapped1586 = deconstruct_result1585
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1586)
                newline(pp)
                for (i1795, elem1587) in enumerate(unwrapped1586)
                    i1588 = i1795 - 1
                    if (i1588 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1587)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1796 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1796 = nothing
            end
            deconstruct_result1583 = _t1796
            if !isnothing(deconstruct_result1583)
                unwrapped1584 = deconstruct_result1583
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1584)
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
    flat1594 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1594)
        write(pp, flat1594)
        return nothing
    else
        _dollar_dollar = msg
        fields1590 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1591 = fields1590
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1592 = unwrapped_fields1591[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1592))
        newline(pp)
        field1593 = unwrapped_fields1591[2]
        pretty_relation_id(pp, field1593)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1598 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1598)
        write(pp, flat1598)
        return nothing
    else
        fields1595 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1595)
            newline(pp)
            for (i1797, elem1596) in enumerate(fields1595)
                i1597 = i1797 - 1
                if (i1597 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1596)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1607 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1607)
        write(pp, flat1607)
        return nothing
    else
        _dollar_dollar = msg
        _t1798 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1599 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1798,)
        unwrapped_fields1600 = fields1599
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1601 = unwrapped_fields1600[1]
        pretty_iceberg_locator(pp, field1601)
        newline(pp)
        field1602 = unwrapped_fields1600[2]
        pretty_iceberg_catalog_config(pp, field1602)
        newline(pp)
        field1603 = unwrapped_fields1600[3]
        pretty_export_iceberg_table_def(pp, field1603)
        newline(pp)
        field1604 = unwrapped_fields1600[4]
        pretty_iceberg_table_properties(pp, field1604)
        field1605 = unwrapped_fields1600[5]
        if !isnothing(field1605)
            newline(pp)
            opt_val1606 = field1605
            pretty_config_dict(pp, opt_val1606)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1609 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1609)
        write(pp, flat1609)
        return nothing
    else
        fields1608 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1608)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1613 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1613)
        write(pp, flat1613)
        return nothing
    else
        fields1610 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1610)
            newline(pp)
            for (i1799, elem1611) in enumerate(fields1610)
                i1612 = i1799 - 1
                if (i1612 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1611)
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
    for (i1847, _rid) in enumerate(msg.ids)
        _idx = i1847 - 1
        newline(pp)
        write(pp, "(")
        _t1848 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1848)
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
    for (i1849, _elem) in enumerate(msg.keys)
        _idx = i1849 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1850, _elem) in enumerate(msg.values)
        _idx = i1850 - 1
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
    for (i1851, _elem) in enumerate(msg.columns)
        _idx = i1851 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVTarget) = pretty_csv_table(pp, x)
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
