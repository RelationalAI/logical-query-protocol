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

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1803 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1803,))
    _t1804 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1804,))
    _t1805 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1805,))
    _t1806 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1806,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1807 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1807,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1808 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1808,))
        end
    end
    _t1809 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1809,))
    _t1810 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1810,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1811 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1811,))
    end
    if !isnothing(msg.compression)
        _t1812 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1812,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1813 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1813,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1814 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1814,))
    end
    if !isnothing(msg.syntax_delim)
        _t1815 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1815,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1816 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1816,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1817 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1817,))
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
        _t1818 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1819 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1820 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1821 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1821,))
    end
    if msg.target_file_size_bytes != 0
        _t1822 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1822,))
    end
    if msg.compression != ""
        _t1823 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1823,))
    end
    if length(result) == 0
        return nothing
    else
        _t1824 = nothing
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
        _t1825 = nothing
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
    flat809 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat809)
        write(pp, flat809)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1600 = _dollar_dollar.configure
        else
            _t1600 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1601 = _dollar_dollar.sync
        else
            _t1601 = nothing
        end
        fields800 = (_t1600, _t1601, _dollar_dollar.epochs,)
        unwrapped_fields801 = fields800
        write(pp, "(transaction")
        indent_sexp!(pp)
        field802 = unwrapped_fields801[1]
        if !isnothing(field802)
            newline(pp)
            opt_val803 = field802
            pretty_configure(pp, opt_val803)
        end
        field804 = unwrapped_fields801[2]
        if !isnothing(field804)
            newline(pp)
            opt_val805 = field804
            pretty_sync(pp, opt_val805)
        end
        field806 = unwrapped_fields801[3]
        if !isempty(field806)
            newline(pp)
            for (i1602, elem807) in enumerate(field806)
                i808 = i1602 - 1
                if (i808 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem807)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat812 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat812)
        write(pp, flat812)
        return nothing
    else
        _dollar_dollar = msg
        _t1603 = deconstruct_configure(pp, _dollar_dollar)
        fields810 = _t1603
        unwrapped_fields811 = fields810
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields811)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat816 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat816)
        write(pp, flat816)
        return nothing
    else
        fields813 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields813)
            newline(pp)
            for (i1604, elem814) in enumerate(fields813)
                i815 = i1604 - 1
                if (i815 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem814)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat821 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat821)
        write(pp, flat821)
        return nothing
    else
        _dollar_dollar = msg
        fields817 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields818 = fields817
        write(pp, ":")
        field819 = unwrapped_fields818[1]
        write(pp, field819)
        write(pp, " ")
        field820 = unwrapped_fields818[2]
        pretty_raw_value(pp, field820)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat847 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat847)
        write(pp, flat847)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1605 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1605 = nothing
        end
        deconstruct_result845 = _t1605
        if !isnothing(deconstruct_result845)
            unwrapped846 = deconstruct_result845
            pretty_raw_date(pp, unwrapped846)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1606 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1606 = nothing
            end
            deconstruct_result843 = _t1606
            if !isnothing(deconstruct_result843)
                unwrapped844 = deconstruct_result843
                pretty_raw_datetime(pp, unwrapped844)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1607 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1607 = nothing
                end
                deconstruct_result841 = _t1607
                if !isnothing(deconstruct_result841)
                    unwrapped842 = deconstruct_result841
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped842))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1608 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1608 = nothing
                    end
                    deconstruct_result839 = _t1608
                    if !isnothing(deconstruct_result839)
                        unwrapped840 = deconstruct_result839
                        write(pp, (string(Int64(unwrapped840)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1609 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1609 = nothing
                        end
                        deconstruct_result837 = _t1609
                        if !isnothing(deconstruct_result837)
                            unwrapped838 = deconstruct_result837
                            write(pp, string(unwrapped838))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1610 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1610 = nothing
                            end
                            deconstruct_result835 = _t1610
                            if !isnothing(deconstruct_result835)
                                unwrapped836 = deconstruct_result835
                                write(pp, format_float32_literal(unwrapped836))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1611 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1611 = nothing
                                end
                                deconstruct_result833 = _t1611
                                if !isnothing(deconstruct_result833)
                                    unwrapped834 = deconstruct_result833
                                    write(pp, lowercase(string(unwrapped834)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1612 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1612 = nothing
                                    end
                                    deconstruct_result831 = _t1612
                                    if !isnothing(deconstruct_result831)
                                        unwrapped832 = deconstruct_result831
                                        write(pp, (string(Int64(unwrapped832)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1613 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1613 = nothing
                                        end
                                        deconstruct_result829 = _t1613
                                        if !isnothing(deconstruct_result829)
                                            unwrapped830 = deconstruct_result829
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped830))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1614 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1614 = nothing
                                            end
                                            deconstruct_result827 = _t1614
                                            if !isnothing(deconstruct_result827)
                                                unwrapped828 = deconstruct_result827
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped828))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1615 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1615 = nothing
                                                end
                                                deconstruct_result825 = _t1615
                                                if !isnothing(deconstruct_result825)
                                                    unwrapped826 = deconstruct_result825
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped826))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1616 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1616 = nothing
                                                    end
                                                    deconstruct_result823 = _t1616
                                                    if !isnothing(deconstruct_result823)
                                                        unwrapped824 = deconstruct_result823
                                                        pretty_boolean_value(pp, unwrapped824)
                                                    else
                                                        fields822 = msg
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
    flat853 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat853)
        write(pp, flat853)
        return nothing
    else
        _dollar_dollar = msg
        fields848 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields849 = fields848
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field850 = unwrapped_fields849[1]
        write(pp, string(field850))
        newline(pp)
        field851 = unwrapped_fields849[2]
        write(pp, string(field851))
        newline(pp)
        field852 = unwrapped_fields849[3]
        write(pp, string(field852))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat864 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat864)
        write(pp, flat864)
        return nothing
    else
        _dollar_dollar = msg
        fields854 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields855 = fields854
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field856 = unwrapped_fields855[1]
        write(pp, string(field856))
        newline(pp)
        field857 = unwrapped_fields855[2]
        write(pp, string(field857))
        newline(pp)
        field858 = unwrapped_fields855[3]
        write(pp, string(field858))
        newline(pp)
        field859 = unwrapped_fields855[4]
        write(pp, string(field859))
        newline(pp)
        field860 = unwrapped_fields855[5]
        write(pp, string(field860))
        newline(pp)
        field861 = unwrapped_fields855[6]
        write(pp, string(field861))
        field862 = unwrapped_fields855[7]
        if !isnothing(field862)
            newline(pp)
            opt_val863 = field862
            write(pp, string(opt_val863))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1617 = ()
    else
        _t1617 = nothing
    end
    deconstruct_result867 = _t1617
    if !isnothing(deconstruct_result867)
        unwrapped868 = deconstruct_result867
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1618 = ()
        else
            _t1618 = nothing
        end
        deconstruct_result865 = _t1618
        if !isnothing(deconstruct_result865)
            unwrapped866 = deconstruct_result865
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat873 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat873)
        write(pp, flat873)
        return nothing
    else
        _dollar_dollar = msg
        fields869 = _dollar_dollar.fragments
        unwrapped_fields870 = fields869
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields870)
            newline(pp)
            for (i1619, elem871) in enumerate(unwrapped_fields870)
                i872 = i1619 - 1
                if (i872 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem871)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat876 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat876)
        write(pp, flat876)
        return nothing
    else
        _dollar_dollar = msg
        fields874 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields875 = fields874
        write(pp, ":")
        write(pp, unwrapped_fields875)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat883 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat883)
        write(pp, flat883)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1620 = _dollar_dollar.writes
        else
            _t1620 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1621 = _dollar_dollar.reads
        else
            _t1621 = nothing
        end
        fields877 = (_t1620, _t1621,)
        unwrapped_fields878 = fields877
        write(pp, "(epoch")
        indent_sexp!(pp)
        field879 = unwrapped_fields878[1]
        if !isnothing(field879)
            newline(pp)
            opt_val880 = field879
            pretty_epoch_writes(pp, opt_val880)
        end
        field881 = unwrapped_fields878[2]
        if !isnothing(field881)
            newline(pp)
            opt_val882 = field881
            pretty_epoch_reads(pp, opt_val882)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat887 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat887)
        write(pp, flat887)
        return nothing
    else
        fields884 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields884)
            newline(pp)
            for (i1622, elem885) in enumerate(fields884)
                i886 = i1622 - 1
                if (i886 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem885)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat896 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat896)
        write(pp, flat896)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1623 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1623 = nothing
        end
        deconstruct_result894 = _t1623
        if !isnothing(deconstruct_result894)
            unwrapped895 = deconstruct_result894
            pretty_define(pp, unwrapped895)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1624 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1624 = nothing
            end
            deconstruct_result892 = _t1624
            if !isnothing(deconstruct_result892)
                unwrapped893 = deconstruct_result892
                pretty_undefine(pp, unwrapped893)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1625 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1625 = nothing
                end
                deconstruct_result890 = _t1625
                if !isnothing(deconstruct_result890)
                    unwrapped891 = deconstruct_result890
                    pretty_context(pp, unwrapped891)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1626 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1626 = nothing
                    end
                    deconstruct_result888 = _t1626
                    if !isnothing(deconstruct_result888)
                        unwrapped889 = deconstruct_result888
                        pretty_snapshot(pp, unwrapped889)
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
    flat899 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat899)
        write(pp, flat899)
        return nothing
    else
        _dollar_dollar = msg
        fields897 = _dollar_dollar.fragment
        unwrapped_fields898 = fields897
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields898)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat906 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields900 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields901 = fields900
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field902 = unwrapped_fields901[1]
        pretty_new_fragment_id(pp, field902)
        field903 = unwrapped_fields901[2]
        if !isempty(field903)
            newline(pp)
            for (i1627, elem904) in enumerate(field903)
                i905 = i1627 - 1
                if (i905 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem904)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat908 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat908)
        write(pp, flat908)
        return nothing
    else
        fields907 = msg
        pretty_fragment_id(pp, fields907)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat917 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat917)
        write(pp, flat917)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1628 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1628 = nothing
        end
        deconstruct_result915 = _t1628
        if !isnothing(deconstruct_result915)
            unwrapped916 = deconstruct_result915
            pretty_def(pp, unwrapped916)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1629 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1629 = nothing
            end
            deconstruct_result913 = _t1629
            if !isnothing(deconstruct_result913)
                unwrapped914 = deconstruct_result913
                pretty_algorithm(pp, unwrapped914)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1630 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1630 = nothing
                end
                deconstruct_result911 = _t1630
                if !isnothing(deconstruct_result911)
                    unwrapped912 = deconstruct_result911
                    pretty_constraint(pp, unwrapped912)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1631 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1631 = nothing
                    end
                    deconstruct_result909 = _t1631
                    if !isnothing(deconstruct_result909)
                        unwrapped910 = deconstruct_result909
                        pretty_data(pp, unwrapped910)
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
    flat924 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat924)
        write(pp, flat924)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1632 = _dollar_dollar.attrs
        else
            _t1632 = nothing
        end
        fields918 = (_dollar_dollar.name, _dollar_dollar.body, _t1632,)
        unwrapped_fields919 = fields918
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field920 = unwrapped_fields919[1]
        pretty_relation_id(pp, field920)
        newline(pp)
        field921 = unwrapped_fields919[2]
        pretty_abstraction(pp, field921)
        field922 = unwrapped_fields919[3]
        if !isnothing(field922)
            newline(pp)
            opt_val923 = field922
            pretty_attrs(pp, opt_val923)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat929 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat929)
        write(pp, flat929)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1634 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1633 = _t1634
        else
            _t1633 = nothing
        end
        deconstruct_result927 = _t1633
        if !isnothing(deconstruct_result927)
            unwrapped928 = deconstruct_result927
            write(pp, ":")
            write(pp, unwrapped928)
        else
            _dollar_dollar = msg
            _t1635 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result925 = _t1635
            if !isnothing(deconstruct_result925)
                unwrapped926 = deconstruct_result925
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped926))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat934 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat934)
        write(pp, flat934)
        return nothing
    else
        _dollar_dollar = msg
        _t1636 = deconstruct_bindings(pp, _dollar_dollar)
        fields930 = (_t1636, _dollar_dollar.value,)
        unwrapped_fields931 = fields930
        write(pp, "(")
        indent!(pp)
        field932 = unwrapped_fields931[1]
        pretty_bindings(pp, field932)
        newline(pp)
        field933 = unwrapped_fields931[2]
        pretty_formula(pp, field933)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat942 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat942)
        write(pp, flat942)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1637 = _dollar_dollar[2]
        else
            _t1637 = nothing
        end
        fields935 = (_dollar_dollar[1], _t1637,)
        unwrapped_fields936 = fields935
        write(pp, "[")
        indent!(pp)
        field937 = unwrapped_fields936[1]
        for (i1638, elem938) in enumerate(field937)
            i939 = i1638 - 1
            if (i939 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem938)
        end
        field940 = unwrapped_fields936[2]
        if !isnothing(field940)
            newline(pp)
            opt_val941 = field940
            pretty_value_bindings(pp, opt_val941)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat947 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat947)
        write(pp, flat947)
        return nothing
    else
        _dollar_dollar = msg
        fields943 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields944 = fields943
        field945 = unwrapped_fields944[1]
        write(pp, field945)
        write(pp, "::")
        field946 = unwrapped_fields944[2]
        pretty_type(pp, field946)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat976 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat976)
        write(pp, flat976)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1639 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1639 = nothing
        end
        deconstruct_result974 = _t1639
        if !isnothing(deconstruct_result974)
            unwrapped975 = deconstruct_result974
            pretty_unspecified_type(pp, unwrapped975)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1640 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1640 = nothing
            end
            deconstruct_result972 = _t1640
            if !isnothing(deconstruct_result972)
                unwrapped973 = deconstruct_result972
                pretty_string_type(pp, unwrapped973)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1641 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1641 = nothing
                end
                deconstruct_result970 = _t1641
                if !isnothing(deconstruct_result970)
                    unwrapped971 = deconstruct_result970
                    pretty_int_type(pp, unwrapped971)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1642 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1642 = nothing
                    end
                    deconstruct_result968 = _t1642
                    if !isnothing(deconstruct_result968)
                        unwrapped969 = deconstruct_result968
                        pretty_float_type(pp, unwrapped969)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1643 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1643 = nothing
                        end
                        deconstruct_result966 = _t1643
                        if !isnothing(deconstruct_result966)
                            unwrapped967 = deconstruct_result966
                            pretty_uint128_type(pp, unwrapped967)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1644 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1644 = nothing
                            end
                            deconstruct_result964 = _t1644
                            if !isnothing(deconstruct_result964)
                                unwrapped965 = deconstruct_result964
                                pretty_int128_type(pp, unwrapped965)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1645 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1645 = nothing
                                end
                                deconstruct_result962 = _t1645
                                if !isnothing(deconstruct_result962)
                                    unwrapped963 = deconstruct_result962
                                    pretty_date_type(pp, unwrapped963)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1646 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1646 = nothing
                                    end
                                    deconstruct_result960 = _t1646
                                    if !isnothing(deconstruct_result960)
                                        unwrapped961 = deconstruct_result960
                                        pretty_datetime_type(pp, unwrapped961)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1647 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1647 = nothing
                                        end
                                        deconstruct_result958 = _t1647
                                        if !isnothing(deconstruct_result958)
                                            unwrapped959 = deconstruct_result958
                                            pretty_missing_type(pp, unwrapped959)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1648 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1648 = nothing
                                            end
                                            deconstruct_result956 = _t1648
                                            if !isnothing(deconstruct_result956)
                                                unwrapped957 = deconstruct_result956
                                                pretty_decimal_type(pp, unwrapped957)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1649 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1649 = nothing
                                                end
                                                deconstruct_result954 = _t1649
                                                if !isnothing(deconstruct_result954)
                                                    unwrapped955 = deconstruct_result954
                                                    pretty_boolean_type(pp, unwrapped955)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1650 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1650 = nothing
                                                    end
                                                    deconstruct_result952 = _t1650
                                                    if !isnothing(deconstruct_result952)
                                                        unwrapped953 = deconstruct_result952
                                                        pretty_int32_type(pp, unwrapped953)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1651 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1651 = nothing
                                                        end
                                                        deconstruct_result950 = _t1651
                                                        if !isnothing(deconstruct_result950)
                                                            unwrapped951 = deconstruct_result950
                                                            pretty_float32_type(pp, unwrapped951)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1652 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1652 = nothing
                                                            end
                                                            deconstruct_result948 = _t1652
                                                            if !isnothing(deconstruct_result948)
                                                                unwrapped949 = deconstruct_result948
                                                                pretty_uint32_type(pp, unwrapped949)
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
    fields977 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields978 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields979 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields980 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields981 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields982 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields983 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields984 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields985 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat990 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat990)
        write(pp, flat990)
        return nothing
    else
        _dollar_dollar = msg
        fields986 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields987 = fields986
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field988 = unwrapped_fields987[1]
        write(pp, string(field988))
        newline(pp)
        field989 = unwrapped_fields987[2]
        write(pp, string(field989))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields991 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields992 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields993 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields994 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat998 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat998)
        write(pp, flat998)
        return nothing
    else
        fields995 = msg
        write(pp, "|")
        if !isempty(fields995)
            write(pp, " ")
            for (i1653, elem996) in enumerate(fields995)
                i997 = i1653 - 1
                if (i997 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem996)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1025 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1025)
        write(pp, flat1025)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1654 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1654 = nothing
        end
        deconstruct_result1023 = _t1654
        if !isnothing(deconstruct_result1023)
            unwrapped1024 = deconstruct_result1023
            pretty_true(pp, unwrapped1024)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1655 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1655 = nothing
            end
            deconstruct_result1021 = _t1655
            if !isnothing(deconstruct_result1021)
                unwrapped1022 = deconstruct_result1021
                pretty_false(pp, unwrapped1022)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1656 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1656 = nothing
                end
                deconstruct_result1019 = _t1656
                if !isnothing(deconstruct_result1019)
                    unwrapped1020 = deconstruct_result1019
                    pretty_exists(pp, unwrapped1020)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1657 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1657 = nothing
                    end
                    deconstruct_result1017 = _t1657
                    if !isnothing(deconstruct_result1017)
                        unwrapped1018 = deconstruct_result1017
                        pretty_reduce(pp, unwrapped1018)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1658 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1658 = nothing
                        end
                        deconstruct_result1015 = _t1658
                        if !isnothing(deconstruct_result1015)
                            unwrapped1016 = deconstruct_result1015
                            pretty_conjunction(pp, unwrapped1016)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1659 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1659 = nothing
                            end
                            deconstruct_result1013 = _t1659
                            if !isnothing(deconstruct_result1013)
                                unwrapped1014 = deconstruct_result1013
                                pretty_disjunction(pp, unwrapped1014)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1660 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1660 = nothing
                                end
                                deconstruct_result1011 = _t1660
                                if !isnothing(deconstruct_result1011)
                                    unwrapped1012 = deconstruct_result1011
                                    pretty_not(pp, unwrapped1012)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1661 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1661 = nothing
                                    end
                                    deconstruct_result1009 = _t1661
                                    if !isnothing(deconstruct_result1009)
                                        unwrapped1010 = deconstruct_result1009
                                        pretty_ffi(pp, unwrapped1010)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1662 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1662 = nothing
                                        end
                                        deconstruct_result1007 = _t1662
                                        if !isnothing(deconstruct_result1007)
                                            unwrapped1008 = deconstruct_result1007
                                            pretty_atom(pp, unwrapped1008)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1663 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1663 = nothing
                                            end
                                            deconstruct_result1005 = _t1663
                                            if !isnothing(deconstruct_result1005)
                                                unwrapped1006 = deconstruct_result1005
                                                pretty_pragma(pp, unwrapped1006)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1664 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1664 = nothing
                                                end
                                                deconstruct_result1003 = _t1664
                                                if !isnothing(deconstruct_result1003)
                                                    unwrapped1004 = deconstruct_result1003
                                                    pretty_primitive(pp, unwrapped1004)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1665 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1665 = nothing
                                                    end
                                                    deconstruct_result1001 = _t1665
                                                    if !isnothing(deconstruct_result1001)
                                                        unwrapped1002 = deconstruct_result1001
                                                        pretty_rel_atom(pp, unwrapped1002)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1666 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1666 = nothing
                                                        end
                                                        deconstruct_result999 = _t1666
                                                        if !isnothing(deconstruct_result999)
                                                            unwrapped1000 = deconstruct_result999
                                                            pretty_cast(pp, unwrapped1000)
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
    fields1026 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1027 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1032 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1032)
        write(pp, flat1032)
        return nothing
    else
        _dollar_dollar = msg
        _t1667 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1028 = (_t1667, _dollar_dollar.body.value,)
        unwrapped_fields1029 = fields1028
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1030 = unwrapped_fields1029[1]
        pretty_bindings(pp, field1030)
        newline(pp)
        field1031 = unwrapped_fields1029[2]
        pretty_formula(pp, field1031)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1038 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1038)
        write(pp, flat1038)
        return nothing
    else
        _dollar_dollar = msg
        fields1033 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1034 = fields1033
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1035 = unwrapped_fields1034[1]
        pretty_abstraction(pp, field1035)
        newline(pp)
        field1036 = unwrapped_fields1034[2]
        pretty_abstraction(pp, field1036)
        newline(pp)
        field1037 = unwrapped_fields1034[3]
        pretty_terms(pp, field1037)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1042 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1042)
        write(pp, flat1042)
        return nothing
    else
        fields1039 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1039)
            newline(pp)
            for (i1668, elem1040) in enumerate(fields1039)
                i1041 = i1668 - 1
                if (i1041 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1040)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1047 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1047)
        write(pp, flat1047)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1669 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1669 = nothing
        end
        deconstruct_result1045 = _t1669
        if !isnothing(deconstruct_result1045)
            unwrapped1046 = deconstruct_result1045
            pretty_var(pp, unwrapped1046)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1670 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1670 = nothing
            end
            deconstruct_result1043 = _t1670
            if !isnothing(deconstruct_result1043)
                unwrapped1044 = deconstruct_result1043
                pretty_value(pp, unwrapped1044)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1050 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1050)
        write(pp, flat1050)
        return nothing
    else
        _dollar_dollar = msg
        fields1048 = _dollar_dollar.name
        unwrapped_fields1049 = fields1048
        write(pp, unwrapped_fields1049)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1076 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1076)
        write(pp, flat1076)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1671 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1671 = nothing
        end
        deconstruct_result1074 = _t1671
        if !isnothing(deconstruct_result1074)
            unwrapped1075 = deconstruct_result1074
            pretty_date(pp, unwrapped1075)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1672 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1672 = nothing
            end
            deconstruct_result1072 = _t1672
            if !isnothing(deconstruct_result1072)
                unwrapped1073 = deconstruct_result1072
                pretty_datetime(pp, unwrapped1073)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1673 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1673 = nothing
                end
                deconstruct_result1070 = _t1673
                if !isnothing(deconstruct_result1070)
                    unwrapped1071 = deconstruct_result1070
                    write(pp, format_string(pp, unwrapped1071))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1674 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1674 = nothing
                    end
                    deconstruct_result1068 = _t1674
                    if !isnothing(deconstruct_result1068)
                        unwrapped1069 = deconstruct_result1068
                        write(pp, format_int32(pp, unwrapped1069))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1675 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1675 = nothing
                        end
                        deconstruct_result1066 = _t1675
                        if !isnothing(deconstruct_result1066)
                            unwrapped1067 = deconstruct_result1066
                            write(pp, format_int(pp, unwrapped1067))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1676 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1676 = nothing
                            end
                            deconstruct_result1064 = _t1676
                            if !isnothing(deconstruct_result1064)
                                unwrapped1065 = deconstruct_result1064
                                write(pp, format_float32(pp, unwrapped1065))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1677 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1677 = nothing
                                end
                                deconstruct_result1062 = _t1677
                                if !isnothing(deconstruct_result1062)
                                    unwrapped1063 = deconstruct_result1062
                                    write(pp, format_float(pp, unwrapped1063))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1678 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1678 = nothing
                                    end
                                    deconstruct_result1060 = _t1678
                                    if !isnothing(deconstruct_result1060)
                                        unwrapped1061 = deconstruct_result1060
                                        write(pp, format_uint32(pp, unwrapped1061))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1679 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1679 = nothing
                                        end
                                        deconstruct_result1058 = _t1679
                                        if !isnothing(deconstruct_result1058)
                                            unwrapped1059 = deconstruct_result1058
                                            write(pp, format_uint128(pp, unwrapped1059))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1680 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1680 = nothing
                                            end
                                            deconstruct_result1056 = _t1680
                                            if !isnothing(deconstruct_result1056)
                                                unwrapped1057 = deconstruct_result1056
                                                write(pp, format_int128(pp, unwrapped1057))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1681 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1681 = nothing
                                                end
                                                deconstruct_result1054 = _t1681
                                                if !isnothing(deconstruct_result1054)
                                                    unwrapped1055 = deconstruct_result1054
                                                    write(pp, format_decimal(pp, unwrapped1055))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1682 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1682 = nothing
                                                    end
                                                    deconstruct_result1052 = _t1682
                                                    if !isnothing(deconstruct_result1052)
                                                        unwrapped1053 = deconstruct_result1052
                                                        pretty_boolean_value(pp, unwrapped1053)
                                                    else
                                                        fields1051 = msg
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
    flat1082 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1082)
        write(pp, flat1082)
        return nothing
    else
        _dollar_dollar = msg
        fields1077 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1078 = fields1077
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1079 = unwrapped_fields1078[1]
        write(pp, format_int(pp, field1079))
        newline(pp)
        field1080 = unwrapped_fields1078[2]
        write(pp, format_int(pp, field1080))
        newline(pp)
        field1081 = unwrapped_fields1078[3]
        write(pp, format_int(pp, field1081))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1093 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1093)
        write(pp, flat1093)
        return nothing
    else
        _dollar_dollar = msg
        fields1083 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1084 = fields1083
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1085 = unwrapped_fields1084[1]
        write(pp, format_int(pp, field1085))
        newline(pp)
        field1086 = unwrapped_fields1084[2]
        write(pp, format_int(pp, field1086))
        newline(pp)
        field1087 = unwrapped_fields1084[3]
        write(pp, format_int(pp, field1087))
        newline(pp)
        field1088 = unwrapped_fields1084[4]
        write(pp, format_int(pp, field1088))
        newline(pp)
        field1089 = unwrapped_fields1084[5]
        write(pp, format_int(pp, field1089))
        newline(pp)
        field1090 = unwrapped_fields1084[6]
        write(pp, format_int(pp, field1090))
        field1091 = unwrapped_fields1084[7]
        if !isnothing(field1091)
            newline(pp)
            opt_val1092 = field1091
            write(pp, format_int(pp, opt_val1092))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1098 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1098)
        write(pp, flat1098)
        return nothing
    else
        _dollar_dollar = msg
        fields1094 = _dollar_dollar.args
        unwrapped_fields1095 = fields1094
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1095)
            newline(pp)
            for (i1683, elem1096) in enumerate(unwrapped_fields1095)
                i1097 = i1683 - 1
                if (i1097 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1096)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1103 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1103)
        write(pp, flat1103)
        return nothing
    else
        _dollar_dollar = msg
        fields1099 = _dollar_dollar.args
        unwrapped_fields1100 = fields1099
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1100)
            newline(pp)
            for (i1684, elem1101) in enumerate(unwrapped_fields1100)
                i1102 = i1684 - 1
                if (i1102 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1101)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1106 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1106)
        write(pp, flat1106)
        return nothing
    else
        _dollar_dollar = msg
        fields1104 = _dollar_dollar.arg
        unwrapped_fields1105 = fields1104
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1105)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1112 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1112)
        write(pp, flat1112)
        return nothing
    else
        _dollar_dollar = msg
        fields1107 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1108 = fields1107
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1109 = unwrapped_fields1108[1]
        pretty_name(pp, field1109)
        newline(pp)
        field1110 = unwrapped_fields1108[2]
        pretty_ffi_args(pp, field1110)
        newline(pp)
        field1111 = unwrapped_fields1108[3]
        pretty_terms(pp, field1111)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1114 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1114)
        write(pp, flat1114)
        return nothing
    else
        fields1113 = msg
        write(pp, ":")
        write(pp, fields1113)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1118 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1118)
        write(pp, flat1118)
        return nothing
    else
        fields1115 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1115)
            newline(pp)
            for (i1685, elem1116) in enumerate(fields1115)
                i1117 = i1685 - 1
                if (i1117 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1116)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1125 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1125)
        write(pp, flat1125)
        return nothing
    else
        _dollar_dollar = msg
        fields1119 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1120 = fields1119
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1121 = unwrapped_fields1120[1]
        pretty_relation_id(pp, field1121)
        field1122 = unwrapped_fields1120[2]
        if !isempty(field1122)
            newline(pp)
            for (i1686, elem1123) in enumerate(field1122)
                i1124 = i1686 - 1
                if (i1124 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1123)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1132 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1132)
        write(pp, flat1132)
        return nothing
    else
        _dollar_dollar = msg
        fields1126 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1127 = fields1126
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1128 = unwrapped_fields1127[1]
        pretty_name(pp, field1128)
        field1129 = unwrapped_fields1127[2]
        if !isempty(field1129)
            newline(pp)
            for (i1687, elem1130) in enumerate(field1129)
                i1131 = i1687 - 1
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

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1148 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1148)
        write(pp, flat1148)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1688 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1688 = nothing
        end
        guard_result1147 = _t1688
        if !isnothing(guard_result1147)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1689 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1689 = nothing
            end
            guard_result1146 = _t1689
            if !isnothing(guard_result1146)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1690 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1690 = nothing
                end
                guard_result1145 = _t1690
                if !isnothing(guard_result1145)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1691 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1691 = nothing
                    end
                    guard_result1144 = _t1691
                    if !isnothing(guard_result1144)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1692 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1692 = nothing
                        end
                        guard_result1143 = _t1692
                        if !isnothing(guard_result1143)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1693 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1693 = nothing
                            end
                            guard_result1142 = _t1693
                            if !isnothing(guard_result1142)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1694 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1694 = nothing
                                end
                                guard_result1141 = _t1694
                                if !isnothing(guard_result1141)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1695 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1695 = nothing
                                    end
                                    guard_result1140 = _t1695
                                    if !isnothing(guard_result1140)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1696 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1696 = nothing
                                        end
                                        guard_result1139 = _t1696
                                        if !isnothing(guard_result1139)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1133 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1134 = fields1133
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1135 = unwrapped_fields1134[1]
                                            pretty_name(pp, field1135)
                                            field1136 = unwrapped_fields1134[2]
                                            if !isempty(field1136)
                                                newline(pp)
                                                for (i1697, elem1137) in enumerate(field1136)
                                                    i1138 = i1697 - 1
                                                    if (i1138 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1137)
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
    flat1153 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1153)
        write(pp, flat1153)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1698 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1698 = nothing
        end
        fields1149 = _t1698
        unwrapped_fields1150 = fields1149
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1151 = unwrapped_fields1150[1]
        pretty_term(pp, field1151)
        newline(pp)
        field1152 = unwrapped_fields1150[2]
        pretty_term(pp, field1152)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1158 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1158)
        write(pp, flat1158)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1699 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1699 = nothing
        end
        fields1154 = _t1699
        unwrapped_fields1155 = fields1154
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1156 = unwrapped_fields1155[1]
        pretty_term(pp, field1156)
        newline(pp)
        field1157 = unwrapped_fields1155[2]
        pretty_term(pp, field1157)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1163 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1163)
        write(pp, flat1163)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1700 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1700 = nothing
        end
        fields1159 = _t1700
        unwrapped_fields1160 = fields1159
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1161 = unwrapped_fields1160[1]
        pretty_term(pp, field1161)
        newline(pp)
        field1162 = unwrapped_fields1160[2]
        pretty_term(pp, field1162)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1168 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1168)
        write(pp, flat1168)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1701 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1701 = nothing
        end
        fields1164 = _t1701
        unwrapped_fields1165 = fields1164
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1166 = unwrapped_fields1165[1]
        pretty_term(pp, field1166)
        newline(pp)
        field1167 = unwrapped_fields1165[2]
        pretty_term(pp, field1167)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1173 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1173)
        write(pp, flat1173)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1702 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1702 = nothing
        end
        fields1169 = _t1702
        unwrapped_fields1170 = fields1169
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1171 = unwrapped_fields1170[1]
        pretty_term(pp, field1171)
        newline(pp)
        field1172 = unwrapped_fields1170[2]
        pretty_term(pp, field1172)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1179 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1703 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1703 = nothing
        end
        fields1174 = _t1703
        unwrapped_fields1175 = fields1174
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1176 = unwrapped_fields1175[1]
        pretty_term(pp, field1176)
        newline(pp)
        field1177 = unwrapped_fields1175[2]
        pretty_term(pp, field1177)
        newline(pp)
        field1178 = unwrapped_fields1175[3]
        pretty_term(pp, field1178)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1185 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1185)
        write(pp, flat1185)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1704 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1704 = nothing
        end
        fields1180 = _t1704
        unwrapped_fields1181 = fields1180
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1182 = unwrapped_fields1181[1]
        pretty_term(pp, field1182)
        newline(pp)
        field1183 = unwrapped_fields1181[2]
        pretty_term(pp, field1183)
        newline(pp)
        field1184 = unwrapped_fields1181[3]
        pretty_term(pp, field1184)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1191 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1191)
        write(pp, flat1191)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1705 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1705 = nothing
        end
        fields1186 = _t1705
        unwrapped_fields1187 = fields1186
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1188 = unwrapped_fields1187[1]
        pretty_term(pp, field1188)
        newline(pp)
        field1189 = unwrapped_fields1187[2]
        pretty_term(pp, field1189)
        newline(pp)
        field1190 = unwrapped_fields1187[3]
        pretty_term(pp, field1190)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1197 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1197)
        write(pp, flat1197)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1706 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1706 = nothing
        end
        fields1192 = _t1706
        unwrapped_fields1193 = fields1192
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1194 = unwrapped_fields1193[1]
        pretty_term(pp, field1194)
        newline(pp)
        field1195 = unwrapped_fields1193[2]
        pretty_term(pp, field1195)
        newline(pp)
        field1196 = unwrapped_fields1193[3]
        pretty_term(pp, field1196)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1202 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1202)
        write(pp, flat1202)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1707 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1707 = nothing
        end
        deconstruct_result1200 = _t1707
        if !isnothing(deconstruct_result1200)
            unwrapped1201 = deconstruct_result1200
            pretty_specialized_value(pp, unwrapped1201)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1708 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1708 = nothing
            end
            deconstruct_result1198 = _t1708
            if !isnothing(deconstruct_result1198)
                unwrapped1199 = deconstruct_result1198
                pretty_term(pp, unwrapped1199)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1204 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1204)
        write(pp, flat1204)
        return nothing
    else
        fields1203 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1203)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1211 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1211)
        write(pp, flat1211)
        return nothing
    else
        _dollar_dollar = msg
        fields1205 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1206 = fields1205
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1207 = unwrapped_fields1206[1]
        pretty_name(pp, field1207)
        field1208 = unwrapped_fields1206[2]
        if !isempty(field1208)
            newline(pp)
            for (i1709, elem1209) in enumerate(field1208)
                i1210 = i1709 - 1
                if (i1210 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1209)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1216 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1216)
        write(pp, flat1216)
        return nothing
    else
        _dollar_dollar = msg
        fields1212 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1213 = fields1212
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1214 = unwrapped_fields1213[1]
        pretty_term(pp, field1214)
        newline(pp)
        field1215 = unwrapped_fields1213[2]
        pretty_term(pp, field1215)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1220 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        fields1217 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1217)
            newline(pp)
            for (i1710, elem1218) in enumerate(fields1217)
                i1219 = i1710 - 1
                if (i1219 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1218)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1227 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1227)
        write(pp, flat1227)
        return nothing
    else
        _dollar_dollar = msg
        fields1221 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1222 = fields1221
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1223 = unwrapped_fields1222[1]
        pretty_name(pp, field1223)
        field1224 = unwrapped_fields1222[2]
        if !isempty(field1224)
            newline(pp)
            for (i1711, elem1225) in enumerate(field1224)
                i1226 = i1711 - 1
                if (i1226 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1225)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1234 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1234)
        write(pp, flat1234)
        return nothing
    else
        _dollar_dollar = msg
        fields1228 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1229 = fields1228
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1230 = unwrapped_fields1229[1]
        if !isempty(field1230)
            newline(pp)
            for (i1712, elem1231) in enumerate(field1230)
                i1232 = i1712 - 1
                if (i1232 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1231)
            end
        end
        newline(pp)
        field1233 = unwrapped_fields1229[2]
        pretty_script(pp, field1233)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1239 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1239)
        write(pp, flat1239)
        return nothing
    else
        _dollar_dollar = msg
        fields1235 = _dollar_dollar.constructs
        unwrapped_fields1236 = fields1235
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1236)
            newline(pp)
            for (i1713, elem1237) in enumerate(unwrapped_fields1236)
                i1238 = i1713 - 1
                if (i1238 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1237)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1244 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1244)
        write(pp, flat1244)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1714 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1714 = nothing
        end
        deconstruct_result1242 = _t1714
        if !isnothing(deconstruct_result1242)
            unwrapped1243 = deconstruct_result1242
            pretty_loop(pp, unwrapped1243)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1715 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1715 = nothing
            end
            deconstruct_result1240 = _t1715
            if !isnothing(deconstruct_result1240)
                unwrapped1241 = deconstruct_result1240
                pretty_instruction(pp, unwrapped1241)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1249 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1249)
        write(pp, flat1249)
        return nothing
    else
        _dollar_dollar = msg
        fields1245 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1246 = fields1245
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1247 = unwrapped_fields1246[1]
        pretty_init(pp, field1247)
        newline(pp)
        field1248 = unwrapped_fields1246[2]
        pretty_script(pp, field1248)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1253 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        fields1250 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1250)
            newline(pp)
            for (i1716, elem1251) in enumerate(fields1250)
                i1252 = i1716 - 1
                if (i1252 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1251)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1264 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1264)
        write(pp, flat1264)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1717 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1717 = nothing
        end
        deconstruct_result1262 = _t1717
        if !isnothing(deconstruct_result1262)
            unwrapped1263 = deconstruct_result1262
            pretty_assign(pp, unwrapped1263)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1718 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1718 = nothing
            end
            deconstruct_result1260 = _t1718
            if !isnothing(deconstruct_result1260)
                unwrapped1261 = deconstruct_result1260
                pretty_upsert(pp, unwrapped1261)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1719 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1719 = nothing
                end
                deconstruct_result1258 = _t1719
                if !isnothing(deconstruct_result1258)
                    unwrapped1259 = deconstruct_result1258
                    pretty_break(pp, unwrapped1259)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1720 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1720 = nothing
                    end
                    deconstruct_result1256 = _t1720
                    if !isnothing(deconstruct_result1256)
                        unwrapped1257 = deconstruct_result1256
                        pretty_monoid_def(pp, unwrapped1257)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1721 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1721 = nothing
                        end
                        deconstruct_result1254 = _t1721
                        if !isnothing(deconstruct_result1254)
                            unwrapped1255 = deconstruct_result1254
                            pretty_monus_def(pp, unwrapped1255)
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
    flat1271 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1271)
        write(pp, flat1271)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1722 = _dollar_dollar.attrs
        else
            _t1722 = nothing
        end
        fields1265 = (_dollar_dollar.name, _dollar_dollar.body, _t1722,)
        unwrapped_fields1266 = fields1265
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1267 = unwrapped_fields1266[1]
        pretty_relation_id(pp, field1267)
        newline(pp)
        field1268 = unwrapped_fields1266[2]
        pretty_abstraction(pp, field1268)
        field1269 = unwrapped_fields1266[3]
        if !isnothing(field1269)
            newline(pp)
            opt_val1270 = field1269
            pretty_attrs(pp, opt_val1270)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1278 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1278)
        write(pp, flat1278)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1723 = _dollar_dollar.attrs
        else
            _t1723 = nothing
        end
        fields1272 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1723,)
        unwrapped_fields1273 = fields1272
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1274 = unwrapped_fields1273[1]
        pretty_relation_id(pp, field1274)
        newline(pp)
        field1275 = unwrapped_fields1273[2]
        pretty_abstraction_with_arity(pp, field1275)
        field1276 = unwrapped_fields1273[3]
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

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1283 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1283)
        write(pp, flat1283)
        return nothing
    else
        _dollar_dollar = msg
        _t1724 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1279 = (_t1724, _dollar_dollar[1].value,)
        unwrapped_fields1280 = fields1279
        write(pp, "(")
        indent!(pp)
        field1281 = unwrapped_fields1280[1]
        pretty_bindings(pp, field1281)
        newline(pp)
        field1282 = unwrapped_fields1280[2]
        pretty_formula(pp, field1282)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1290 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1290)
        write(pp, flat1290)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1725 = _dollar_dollar.attrs
        else
            _t1725 = nothing
        end
        fields1284 = (_dollar_dollar.name, _dollar_dollar.body, _t1725,)
        unwrapped_fields1285 = fields1284
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1286 = unwrapped_fields1285[1]
        pretty_relation_id(pp, field1286)
        newline(pp)
        field1287 = unwrapped_fields1285[2]
        pretty_abstraction(pp, field1287)
        field1288 = unwrapped_fields1285[3]
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

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1298 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1298)
        write(pp, flat1298)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1726 = _dollar_dollar.attrs
        else
            _t1726 = nothing
        end
        fields1291 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1726,)
        unwrapped_fields1292 = fields1291
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1293 = unwrapped_fields1292[1]
        pretty_monoid(pp, field1293)
        newline(pp)
        field1294 = unwrapped_fields1292[2]
        pretty_relation_id(pp, field1294)
        newline(pp)
        field1295 = unwrapped_fields1292[3]
        pretty_abstraction_with_arity(pp, field1295)
        field1296 = unwrapped_fields1292[4]
        if !isnothing(field1296)
            newline(pp)
            opt_val1297 = field1296
            pretty_attrs(pp, opt_val1297)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1307 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1307)
        write(pp, flat1307)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1727 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1727 = nothing
        end
        deconstruct_result1305 = _t1727
        if !isnothing(deconstruct_result1305)
            unwrapped1306 = deconstruct_result1305
            pretty_or_monoid(pp, unwrapped1306)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1728 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1728 = nothing
            end
            deconstruct_result1303 = _t1728
            if !isnothing(deconstruct_result1303)
                unwrapped1304 = deconstruct_result1303
                pretty_min_monoid(pp, unwrapped1304)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1729 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1729 = nothing
                end
                deconstruct_result1301 = _t1729
                if !isnothing(deconstruct_result1301)
                    unwrapped1302 = deconstruct_result1301
                    pretty_max_monoid(pp, unwrapped1302)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1730 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1730 = nothing
                    end
                    deconstruct_result1299 = _t1730
                    if !isnothing(deconstruct_result1299)
                        unwrapped1300 = deconstruct_result1299
                        pretty_sum_monoid(pp, unwrapped1300)
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
    fields1308 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1311 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1311)
        write(pp, flat1311)
        return nothing
    else
        _dollar_dollar = msg
        fields1309 = _dollar_dollar.var"#type"
        unwrapped_fields1310 = fields1309
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1310)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1314 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1314)
        write(pp, flat1314)
        return nothing
    else
        _dollar_dollar = msg
        fields1312 = _dollar_dollar.var"#type"
        unwrapped_fields1313 = fields1312
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1313)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1317 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1317)
        write(pp, flat1317)
        return nothing
    else
        _dollar_dollar = msg
        fields1315 = _dollar_dollar.var"#type"
        unwrapped_fields1316 = fields1315
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1316)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1325 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1325)
        write(pp, flat1325)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1731 = _dollar_dollar.attrs
        else
            _t1731 = nothing
        end
        fields1318 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1731,)
        unwrapped_fields1319 = fields1318
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1320 = unwrapped_fields1319[1]
        pretty_monoid(pp, field1320)
        newline(pp)
        field1321 = unwrapped_fields1319[2]
        pretty_relation_id(pp, field1321)
        newline(pp)
        field1322 = unwrapped_fields1319[3]
        pretty_abstraction_with_arity(pp, field1322)
        field1323 = unwrapped_fields1319[4]
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

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1332 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1332)
        write(pp, flat1332)
        return nothing
    else
        _dollar_dollar = msg
        fields1326 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1327 = fields1326
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1328 = unwrapped_fields1327[1]
        pretty_relation_id(pp, field1328)
        newline(pp)
        field1329 = unwrapped_fields1327[2]
        pretty_abstraction(pp, field1329)
        newline(pp)
        field1330 = unwrapped_fields1327[3]
        pretty_functional_dependency_keys(pp, field1330)
        newline(pp)
        field1331 = unwrapped_fields1327[4]
        pretty_functional_dependency_values(pp, field1331)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1336 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1336)
        write(pp, flat1336)
        return nothing
    else
        fields1333 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1333)
            newline(pp)
            for (i1732, elem1334) in enumerate(fields1333)
                i1335 = i1732 - 1
                if (i1335 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1334)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1340 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1340)
        write(pp, flat1340)
        return nothing
    else
        fields1337 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1337)
            newline(pp)
            for (i1733, elem1338) in enumerate(fields1337)
                i1339 = i1733 - 1
                if (i1339 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1338)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1349 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1349)
        write(pp, flat1349)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1734 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1734 = nothing
        end
        deconstruct_result1347 = _t1734
        if !isnothing(deconstruct_result1347)
            unwrapped1348 = deconstruct_result1347
            pretty_edb(pp, unwrapped1348)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1735 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1735 = nothing
            end
            deconstruct_result1345 = _t1735
            if !isnothing(deconstruct_result1345)
                unwrapped1346 = deconstruct_result1345
                pretty_betree_relation(pp, unwrapped1346)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1736 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1736 = nothing
                end
                deconstruct_result1343 = _t1736
                if !isnothing(deconstruct_result1343)
                    unwrapped1344 = deconstruct_result1343
                    pretty_csv_data(pp, unwrapped1344)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1737 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1737 = nothing
                    end
                    deconstruct_result1341 = _t1737
                    if !isnothing(deconstruct_result1341)
                        unwrapped1342 = deconstruct_result1341
                        pretty_iceberg_data(pp, unwrapped1342)
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
    flat1355 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1355)
        write(pp, flat1355)
        return nothing
    else
        _dollar_dollar = msg
        fields1350 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1351 = fields1350
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1352 = unwrapped_fields1351[1]
        pretty_relation_id(pp, field1352)
        newline(pp)
        field1353 = unwrapped_fields1351[2]
        pretty_edb_path(pp, field1353)
        newline(pp)
        field1354 = unwrapped_fields1351[3]
        pretty_edb_types(pp, field1354)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1359 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1359)
        write(pp, flat1359)
        return nothing
    else
        fields1356 = msg
        write(pp, "[")
        indent!(pp)
        for (i1738, elem1357) in enumerate(fields1356)
            i1358 = i1738 - 1
            if (i1358 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1357))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1363 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1363)
        write(pp, flat1363)
        return nothing
    else
        fields1360 = msg
        write(pp, "[")
        indent!(pp)
        for (i1739, elem1361) in enumerate(fields1360)
            i1362 = i1739 - 1
            if (i1362 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1361)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1368 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1368)
        write(pp, flat1368)
        return nothing
    else
        _dollar_dollar = msg
        fields1364 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1365 = fields1364
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1366 = unwrapped_fields1365[1]
        pretty_relation_id(pp, field1366)
        newline(pp)
        field1367 = unwrapped_fields1365[2]
        pretty_betree_info(pp, field1367)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1374 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1374)
        write(pp, flat1374)
        return nothing
    else
        _dollar_dollar = msg
        _t1740 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1369 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1740,)
        unwrapped_fields1370 = fields1369
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1371 = unwrapped_fields1370[1]
        pretty_betree_info_key_types(pp, field1371)
        newline(pp)
        field1372 = unwrapped_fields1370[2]
        pretty_betree_info_value_types(pp, field1372)
        newline(pp)
        field1373 = unwrapped_fields1370[3]
        pretty_config_dict(pp, field1373)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1378 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1378)
        write(pp, flat1378)
        return nothing
    else
        fields1375 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1375)
            newline(pp)
            for (i1741, elem1376) in enumerate(fields1375)
                i1377 = i1741 - 1
                if (i1377 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1376)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1382 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1382)
        write(pp, flat1382)
        return nothing
    else
        fields1379 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1379)
            newline(pp)
            for (i1742, elem1380) in enumerate(fields1379)
                i1381 = i1742 - 1
                if (i1381 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1380)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1389 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1389)
        write(pp, flat1389)
        return nothing
    else
        _dollar_dollar = msg
        fields1383 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1384 = fields1383
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1385 = unwrapped_fields1384[1]
        pretty_csvlocator(pp, field1385)
        newline(pp)
        field1386 = unwrapped_fields1384[2]
        pretty_csv_config(pp, field1386)
        newline(pp)
        field1387 = unwrapped_fields1384[3]
        pretty_gnf_columns(pp, field1387)
        newline(pp)
        field1388 = unwrapped_fields1384[4]
        pretty_csv_asof(pp, field1388)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1396 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1396)
        write(pp, flat1396)
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
        fields1390 = (_t1743, _t1744,)
        unwrapped_fields1391 = fields1390
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1392 = unwrapped_fields1391[1]
        if !isnothing(field1392)
            newline(pp)
            opt_val1393 = field1392
            pretty_csv_locator_paths(pp, opt_val1393)
        end
        field1394 = unwrapped_fields1391[2]
        if !isnothing(field1394)
            newline(pp)
            opt_val1395 = field1394
            pretty_csv_locator_inline_data(pp, opt_val1395)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1400 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1400)
        write(pp, flat1400)
        return nothing
    else
        fields1397 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1397)
            newline(pp)
            for (i1745, elem1398) in enumerate(fields1397)
                i1399 = i1745 - 1
                if (i1399 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1398))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1402 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1402)
        write(pp, flat1402)
        return nothing
    else
        fields1401 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1401))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1405 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1405)
        write(pp, flat1405)
        return nothing
    else
        _dollar_dollar = msg
        _t1746 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1403 = _t1746
        unwrapped_fields1404 = fields1403
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1404)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1409 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1409)
        write(pp, flat1409)
        return nothing
    else
        fields1406 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1406)
            newline(pp)
            for (i1747, elem1407) in enumerate(fields1406)
                i1408 = i1747 - 1
                if (i1408 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1407)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1418 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1418)
        write(pp, flat1418)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1748 = _dollar_dollar.target_id
        else
            _t1748 = nothing
        end
        fields1410 = (_dollar_dollar.column_path, _t1748, _dollar_dollar.types,)
        unwrapped_fields1411 = fields1410
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1412 = unwrapped_fields1411[1]
        pretty_gnf_column_path(pp, field1412)
        field1413 = unwrapped_fields1411[2]
        if !isnothing(field1413)
            newline(pp)
            opt_val1414 = field1413
            pretty_relation_id(pp, opt_val1414)
        end
        newline(pp)
        write(pp, "[")
        field1415 = unwrapped_fields1411[3]
        for (i1749, elem1416) in enumerate(field1415)
            i1417 = i1749 - 1
            if (i1417 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1416)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1425 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1425)
        write(pp, flat1425)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1750 = _dollar_dollar[1]
        else
            _t1750 = nothing
        end
        deconstruct_result1423 = _t1750
        if !isnothing(deconstruct_result1423)
            unwrapped1424 = deconstruct_result1423
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1424))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1751 = _dollar_dollar
            else
                _t1751 = nothing
            end
            deconstruct_result1419 = _t1751
            if !isnothing(deconstruct_result1419)
                unwrapped1420 = deconstruct_result1419
                write(pp, "[")
                indent!(pp)
                for (i1752, elem1421) in enumerate(unwrapped1420)
                    i1422 = i1752 - 1
                    if (i1422 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1421))
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
    flat1427 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1427)
        write(pp, flat1427)
        return nothing
    else
        fields1426 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1426))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1438 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1438)
        write(pp, flat1438)
        return nothing
    else
        _dollar_dollar = msg
        _t1753 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1754 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1428 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1753, _t1754, _dollar_dollar.returns_delta,)
        unwrapped_fields1429 = fields1428
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1430 = unwrapped_fields1429[1]
        pretty_iceberg_locator(pp, field1430)
        newline(pp)
        field1431 = unwrapped_fields1429[2]
        pretty_iceberg_catalog_config(pp, field1431)
        newline(pp)
        field1432 = unwrapped_fields1429[3]
        pretty_gnf_columns(pp, field1432)
        field1433 = unwrapped_fields1429[4]
        if !isnothing(field1433)
            newline(pp)
            opt_val1434 = field1433
            pretty_iceberg_from_snapshot(pp, opt_val1434)
        end
        field1435 = unwrapped_fields1429[5]
        if !isnothing(field1435)
            newline(pp)
            opt_val1436 = field1435
            pretty_iceberg_to_snapshot(pp, opt_val1436)
        end
        newline(pp)
        field1437 = unwrapped_fields1429[6]
        pretty_boolean_value(pp, field1437)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1444 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1444)
        write(pp, flat1444)
        return nothing
    else
        _dollar_dollar = msg
        fields1439 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1440 = fields1439
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1441 = unwrapped_fields1440[1]
        pretty_iceberg_locator_table_name(pp, field1441)
        newline(pp)
        field1442 = unwrapped_fields1440[2]
        pretty_iceberg_locator_namespace(pp, field1442)
        newline(pp)
        field1443 = unwrapped_fields1440[3]
        pretty_iceberg_locator_warehouse(pp, field1443)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1446 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1446)
        write(pp, flat1446)
        return nothing
    else
        fields1445 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1445))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1450 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1450)
        write(pp, flat1450)
        return nothing
    else
        fields1447 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1447)
            newline(pp)
            for (i1755, elem1448) in enumerate(fields1447)
                i1449 = i1755 - 1
                if (i1449 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1448))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1452 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1452)
        write(pp, flat1452)
        return nothing
    else
        fields1451 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1451))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1460 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1460)
        write(pp, flat1460)
        return nothing
    else
        _dollar_dollar = msg
        _t1756 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1453 = (_dollar_dollar.catalog_uri, _t1756, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1454 = fields1453
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1455 = unwrapped_fields1454[1]
        pretty_iceberg_catalog_uri(pp, field1455)
        field1456 = unwrapped_fields1454[2]
        if !isnothing(field1456)
            newline(pp)
            opt_val1457 = field1456
            pretty_iceberg_catalog_config_scope(pp, opt_val1457)
        end
        newline(pp)
        field1458 = unwrapped_fields1454[3]
        pretty_iceberg_properties(pp, field1458)
        newline(pp)
        field1459 = unwrapped_fields1454[4]
        pretty_iceberg_auth_properties(pp, field1459)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1462 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1462)
        write(pp, flat1462)
        return nothing
    else
        fields1461 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1461))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1464 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1464)
        write(pp, flat1464)
        return nothing
    else
        fields1463 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1463))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1468 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1468)
        write(pp, flat1468)
        return nothing
    else
        fields1465 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1465)
            newline(pp)
            for (i1757, elem1466) in enumerate(fields1465)
                i1467 = i1757 - 1
                if (i1467 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1466)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1473 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1473)
        write(pp, flat1473)
        return nothing
    else
        _dollar_dollar = msg
        fields1469 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1470 = fields1469
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1471 = unwrapped_fields1470[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1471))
        newline(pp)
        field1472 = unwrapped_fields1470[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1472))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1477 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1477)
        write(pp, flat1477)
        return nothing
    else
        fields1474 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1474)
            newline(pp)
            for (i1758, elem1475) in enumerate(fields1474)
                i1476 = i1758 - 1
                if (i1476 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1475)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1482 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1482)
        write(pp, flat1482)
        return nothing
    else
        _dollar_dollar = msg
        _t1759 = mask_secret_value(pp, _dollar_dollar)
        fields1478 = (_dollar_dollar[1], _t1759,)
        unwrapped_fields1479 = fields1478
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1480 = unwrapped_fields1479[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1480))
        newline(pp)
        field1481 = unwrapped_fields1479[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1481))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1484 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1484)
        write(pp, flat1484)
        return nothing
    else
        fields1483 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1483))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1486 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1486)
        write(pp, flat1486)
        return nothing
    else
        fields1485 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1485))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1489 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1489)
        write(pp, flat1489)
        return nothing
    else
        _dollar_dollar = msg
        fields1487 = _dollar_dollar.fragment_id
        unwrapped_fields1488 = fields1487
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1488)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1494 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1494)
        write(pp, flat1494)
        return nothing
    else
        _dollar_dollar = msg
        fields1490 = _dollar_dollar.relations
        unwrapped_fields1491 = fields1490
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1491)
            newline(pp)
            for (i1760, elem1492) in enumerate(unwrapped_fields1491)
                i1493 = i1760 - 1
                if (i1493 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1492)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1501 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1501)
        write(pp, flat1501)
        return nothing
    else
        _dollar_dollar = msg
        fields1495 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1496 = fields1495
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1497 = unwrapped_fields1496[1]
        pretty_edb_path(pp, field1497)
        field1498 = unwrapped_fields1496[2]
        if !isempty(field1498)
            newline(pp)
            for (i1761, elem1499) in enumerate(field1498)
                i1500 = i1761 - 1
                if (i1500 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1499)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1506 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1506)
        write(pp, flat1506)
        return nothing
    else
        _dollar_dollar = msg
        fields1502 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1503 = fields1502
        field1504 = unwrapped_fields1503[1]
        pretty_edb_path(pp, field1504)
        write(pp, " ")
        field1505 = unwrapped_fields1503[2]
        pretty_relation_id(pp, field1505)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1510 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1510)
        write(pp, flat1510)
        return nothing
    else
        fields1507 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1507)
            newline(pp)
            for (i1762, elem1508) in enumerate(fields1507)
                i1509 = i1762 - 1
                if (i1509 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1508)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1521 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1521)
        write(pp, flat1521)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1763 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1763 = nothing
        end
        deconstruct_result1519 = _t1763
        if !isnothing(deconstruct_result1519)
            unwrapped1520 = deconstruct_result1519
            pretty_demand(pp, unwrapped1520)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1764 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1764 = nothing
            end
            deconstruct_result1517 = _t1764
            if !isnothing(deconstruct_result1517)
                unwrapped1518 = deconstruct_result1517
                pretty_output(pp, unwrapped1518)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1765 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1765 = nothing
                end
                deconstruct_result1515 = _t1765
                if !isnothing(deconstruct_result1515)
                    unwrapped1516 = deconstruct_result1515
                    pretty_what_if(pp, unwrapped1516)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1766 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1766 = nothing
                    end
                    deconstruct_result1513 = _t1766
                    if !isnothing(deconstruct_result1513)
                        unwrapped1514 = deconstruct_result1513
                        pretty_abort(pp, unwrapped1514)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1767 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1767 = nothing
                        end
                        deconstruct_result1511 = _t1767
                        if !isnothing(deconstruct_result1511)
                            unwrapped1512 = deconstruct_result1511
                            pretty_export(pp, unwrapped1512)
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
    flat1524 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1524)
        write(pp, flat1524)
        return nothing
    else
        _dollar_dollar = msg
        fields1522 = _dollar_dollar.relation_id
        unwrapped_fields1523 = fields1522
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1523)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1529 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1529)
        write(pp, flat1529)
        return nothing
    else
        _dollar_dollar = msg
        fields1525 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1526 = fields1525
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1527 = unwrapped_fields1526[1]
        pretty_name(pp, field1527)
        newline(pp)
        field1528 = unwrapped_fields1526[2]
        pretty_relation_id(pp, field1528)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1534 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1534)
        write(pp, flat1534)
        return nothing
    else
        _dollar_dollar = msg
        fields1530 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1531 = fields1530
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1532 = unwrapped_fields1531[1]
        pretty_name(pp, field1532)
        newline(pp)
        field1533 = unwrapped_fields1531[2]
        pretty_epoch(pp, field1533)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1540 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1540)
        write(pp, flat1540)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1768 = _dollar_dollar.name
        else
            _t1768 = nothing
        end
        fields1535 = (_t1768, _dollar_dollar.relation_id,)
        unwrapped_fields1536 = fields1535
        write(pp, "(abort")
        indent_sexp!(pp)
        field1537 = unwrapped_fields1536[1]
        if !isnothing(field1537)
            newline(pp)
            opt_val1538 = field1537
            pretty_name(pp, opt_val1538)
        end
        newline(pp)
        field1539 = unwrapped_fields1536[2]
        pretty_relation_id(pp, field1539)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1545 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1545)
        write(pp, flat1545)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1769 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1769 = nothing
        end
        deconstruct_result1543 = _t1769
        if !isnothing(deconstruct_result1543)
            unwrapped1544 = deconstruct_result1543
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1544)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1770 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1770 = nothing
            end
            deconstruct_result1541 = _t1770
            if !isnothing(deconstruct_result1541)
                unwrapped1542 = deconstruct_result1541
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1542)
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
    flat1556 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1556)
        write(pp, flat1556)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1771 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1771 = nothing
        end
        deconstruct_result1551 = _t1771
        if !isnothing(deconstruct_result1551)
            unwrapped1552 = deconstruct_result1551
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1553 = unwrapped1552[1]
            pretty_export_csv_path(pp, field1553)
            newline(pp)
            field1554 = unwrapped1552[2]
            pretty_export_csv_source(pp, field1554)
            newline(pp)
            field1555 = unwrapped1552[3]
            pretty_csv_config(pp, field1555)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1773 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1772 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1773,)
            else
                _t1772 = nothing
            end
            deconstruct_result1546 = _t1772
            if !isnothing(deconstruct_result1546)
                unwrapped1547 = deconstruct_result1546
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1548 = unwrapped1547[1]
                pretty_export_csv_path(pp, field1548)
                newline(pp)
                field1549 = unwrapped1547[2]
                pretty_export_csv_columns_list(pp, field1549)
                newline(pp)
                field1550 = unwrapped1547[3]
                pretty_config_dict(pp, field1550)
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
    flat1558 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1558)
        write(pp, flat1558)
        return nothing
    else
        fields1557 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1557))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1565 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1565)
        write(pp, flat1565)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1774 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1774 = nothing
        end
        deconstruct_result1561 = _t1774
        if !isnothing(deconstruct_result1561)
            unwrapped1562 = deconstruct_result1561
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1562)
                newline(pp)
                for (i1775, elem1563) in enumerate(unwrapped1562)
                    i1564 = i1775 - 1
                    if (i1564 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1563)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1776 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1776 = nothing
            end
            deconstruct_result1559 = _t1776
            if !isnothing(deconstruct_result1559)
                unwrapped1560 = deconstruct_result1559
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1560)
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
    flat1570 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1570)
        write(pp, flat1570)
        return nothing
    else
        _dollar_dollar = msg
        fields1566 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1567 = fields1566
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1568 = unwrapped_fields1567[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1568))
        newline(pp)
        field1569 = unwrapped_fields1567[2]
        pretty_relation_id(pp, field1569)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1574 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1574)
        write(pp, flat1574)
        return nothing
    else
        fields1571 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1571)
            newline(pp)
            for (i1777, elem1572) in enumerate(fields1571)
                i1573 = i1777 - 1
                if (i1573 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1572)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1584 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1584)
        write(pp, flat1584)
        return nothing
    else
        _dollar_dollar = msg
        _t1778 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1575 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, _dollar_dollar.columns, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1778,)
        unwrapped_fields1576 = fields1575
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1577 = unwrapped_fields1576[1]
        pretty_iceberg_locator(pp, field1577)
        newline(pp)
        field1578 = unwrapped_fields1576[2]
        pretty_iceberg_catalog_config(pp, field1578)
        newline(pp)
        field1579 = unwrapped_fields1576[3]
        pretty_export_iceberg_table_def(pp, field1579)
        newline(pp)
        field1580 = unwrapped_fields1576[4]
        pretty_export_iceberg_columns(pp, field1580)
        newline(pp)
        field1581 = unwrapped_fields1576[5]
        pretty_iceberg_table_properties(pp, field1581)
        field1582 = unwrapped_fields1576[6]
        if !isnothing(field1582)
            newline(pp)
            opt_val1583 = field1582
            pretty_config_dict(pp, opt_val1583)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1586 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1586)
        write(pp, flat1586)
        return nothing
    else
        fields1585 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1585)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportColumn})
    flat1590 = try_flat(pp, msg, pretty_export_iceberg_columns)
    if !isnothing(flat1590)
        write(pp, flat1590)
        return nothing
    else
        fields1587 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1587)
            newline(pp)
            for (i1779, elem1588) in enumerate(fields1587)
                i1589 = i1779 - 1
                if (i1589 > 0)
                    newline(pp)
                end
                pretty_export_iceberg_column(pp, elem1588)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_column(pp::PrettyPrinter, msg::Proto.ExportColumn)
    flat1595 = try_flat(pp, msg, pretty_export_iceberg_column)
    if !isnothing(flat1595)
        write(pp, flat1595)
        return nothing
    else
        _dollar_dollar = msg
        fields1591 = (_dollar_dollar.name, _dollar_dollar.nullable,)
        unwrapped_fields1592 = fields1591
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1593 = unwrapped_fields1592[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1593))
        newline(pp)
        field1594 = unwrapped_fields1592[2]
        pretty_boolean_value(pp, field1594)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1599 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1599)
        write(pp, flat1599)
        return nothing
    else
        fields1596 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1596)
            newline(pp)
            for (i1780, elem1597) in enumerate(fields1596)
                i1598 = i1780 - 1
                if (i1598 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1597)
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
    for (i1826, _rid) in enumerate(msg.ids)
        _idx = i1826 - 1
        newline(pp)
        write(pp, "(")
        _t1827 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1827)
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
    for (i1828, _elem) in enumerate(msg.keys)
        _idx = i1828 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1829, _elem) in enumerate(msg.values)
        _idx = i1829 - 1
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
    for (i1830, _elem) in enumerate(msg.columns)
        _idx = i1830 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.ExportColumn}) = pretty_export_iceberg_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportColumn) = pretty_export_iceberg_column(pp, x)
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
