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
    _computing::Set{UInt}
    _memo::Dict{UInt,String}
    _memo_refs::Vector{Any}
    print_symbolic_relation_ids::Bool
    debug_info::Dict{Tuple{UInt64,UInt64},String}
    constant_formatter::ConstantFormatter
end

function PrettyPrinter(; max_width::Int=92, print_symbolic_relation_ids::Bool=true, constant_formatter::ConstantFormatter=DEFAULT_CONSTANT_FORMATTER)
    return PrettyPrinter(
        IOBuffer(), [0], 0, true, "\n", max_width,
        Set{UInt}(), Dict{UInt,String}(), Any[],
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
    msg_id = objectid(msg)
    if !haskey(pp._memo, msg_id) && !(msg_id in pp._computing)
        push!(pp._computing, msg_id)
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
            pp._memo[msg_id] = String(copy(pp.io.data[1:pp.io.size]))
            push!(pp._memo_refs, msg)
        finally
            pp.io = saved_io
            pp.separator = saved_sep
            pp.indent_stack = saved_indent
            pp.column = saved_col
            pp.at_line_start = saved_at_line_start
            delete!(pp._computing, msg_id)
        end
    end
    if haskey(pp._memo, msg_id)
        flat = pp._memo[msg_id]
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
    _t1777 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1777
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1778 = Proto.Value(value=OneOf(:int_value, v))
    return _t1778
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1779 = Proto.Value(value=OneOf(:float_value, v))
    return _t1779
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1780 = Proto.Value(value=OneOf(:string_value, v))
    return _t1780
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1781 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1781
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1782 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1782
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1783 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1783,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1784 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1784,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1785 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1785,))
            end
        end
    end
    _t1786 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1786,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1787 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1787,))
    _t1788 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1788,))
    if msg.new_line != ""
        _t1789 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1789,))
    end
    _t1790 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1790,))
    _t1791 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1791,))
    _t1792 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1792,))
    if msg.comment != ""
        _t1793 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1793,))
    end
    for missing_string in msg.missing_strings
        _t1794 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1794,))
    end
    _t1795 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1795,))
    _t1796 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1796,))
    _t1797 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1797,))
    if msg.partition_size_mb != 0
        _t1798 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1798,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1799 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1799,))
    _t1800 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1800,))
    _t1801 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1801,))
    _t1802 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1802,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1803 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1803,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1804 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1804,))
        end
    end
    _t1805 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1805,))
    _t1806 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1806,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1807 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1807,))
    end
    if !isnothing(msg.compression)
        _t1808 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1808,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1809 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1809,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1810 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1810,))
    end
    if !isnothing(msg.syntax_delim)
        _t1811 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1811,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1812 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1812,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1813 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1813,))
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
        _t1814 = nothing
    end
    return nothing
end

function deconstruct_iceberg_locator_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergLocator)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1815 = nothing
    end
    return nothing
end

function deconstruct_iceberg_locator_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergLocator)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1816 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1817 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1817,))
    end
    if msg.target_file_size_bytes != 0
        _t1818 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1818,))
    end
    if msg.compression != ""
        _t1819 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1819,))
    end
    if length(result) == 0
        return nothing
    else
        _t1820 = nothing
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
        _t1821 = nothing
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
    flat807 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat807)
        write(pp, flat807)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1596 = _dollar_dollar.configure
        else
            _t1596 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1597 = _dollar_dollar.sync
        else
            _t1597 = nothing
        end
        fields798 = (_t1596, _t1597, _dollar_dollar.epochs,)
        unwrapped_fields799 = fields798
        write(pp, "(transaction")
        indent_sexp!(pp)
        field800 = unwrapped_fields799[1]
        if !isnothing(field800)
            newline(pp)
            opt_val801 = field800
            pretty_configure(pp, opt_val801)
        end
        field802 = unwrapped_fields799[2]
        if !isnothing(field802)
            newline(pp)
            opt_val803 = field802
            pretty_sync(pp, opt_val803)
        end
        field804 = unwrapped_fields799[3]
        if !isempty(field804)
            newline(pp)
            for (i1598, elem805) in enumerate(field804)
                i806 = i1598 - 1
                if (i806 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem805)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat810 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat810)
        write(pp, flat810)
        return nothing
    else
        _dollar_dollar = msg
        _t1599 = deconstruct_configure(pp, _dollar_dollar)
        fields808 = _t1599
        unwrapped_fields809 = fields808
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields809)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat814 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat814)
        write(pp, flat814)
        return nothing
    else
        fields811 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields811)
            newline(pp)
            for (i1600, elem812) in enumerate(fields811)
                i813 = i1600 - 1
                if (i813 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem812)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat819 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat819)
        write(pp, flat819)
        return nothing
    else
        _dollar_dollar = msg
        fields815 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields816 = fields815
        write(pp, ":")
        field817 = unwrapped_fields816[1]
        write(pp, field817)
        write(pp, " ")
        field818 = unwrapped_fields816[2]
        pretty_raw_value(pp, field818)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat845 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat845)
        write(pp, flat845)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1601 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1601 = nothing
        end
        deconstruct_result843 = _t1601
        if !isnothing(deconstruct_result843)
            unwrapped844 = deconstruct_result843
            pretty_raw_date(pp, unwrapped844)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1602 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1602 = nothing
            end
            deconstruct_result841 = _t1602
            if !isnothing(deconstruct_result841)
                unwrapped842 = deconstruct_result841
                pretty_raw_datetime(pp, unwrapped842)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1603 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1603 = nothing
                end
                deconstruct_result839 = _t1603
                if !isnothing(deconstruct_result839)
                    unwrapped840 = deconstruct_result839
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped840))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1604 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1604 = nothing
                    end
                    deconstruct_result837 = _t1604
                    if !isnothing(deconstruct_result837)
                        unwrapped838 = deconstruct_result837
                        write(pp, (string(Int64(unwrapped838)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1605 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1605 = nothing
                        end
                        deconstruct_result835 = _t1605
                        if !isnothing(deconstruct_result835)
                            unwrapped836 = deconstruct_result835
                            write(pp, string(unwrapped836))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1606 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1606 = nothing
                            end
                            deconstruct_result833 = _t1606
                            if !isnothing(deconstruct_result833)
                                unwrapped834 = deconstruct_result833
                                write(pp, format_float32_literal(unwrapped834))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1607 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1607 = nothing
                                end
                                deconstruct_result831 = _t1607
                                if !isnothing(deconstruct_result831)
                                    unwrapped832 = deconstruct_result831
                                    write(pp, lowercase(string(unwrapped832)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1608 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1608 = nothing
                                    end
                                    deconstruct_result829 = _t1608
                                    if !isnothing(deconstruct_result829)
                                        unwrapped830 = deconstruct_result829
                                        write(pp, (string(Int64(unwrapped830)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1609 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1609 = nothing
                                        end
                                        deconstruct_result827 = _t1609
                                        if !isnothing(deconstruct_result827)
                                            unwrapped828 = deconstruct_result827
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped828))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1610 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1610 = nothing
                                            end
                                            deconstruct_result825 = _t1610
                                            if !isnothing(deconstruct_result825)
                                                unwrapped826 = deconstruct_result825
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped826))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1611 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1611 = nothing
                                                end
                                                deconstruct_result823 = _t1611
                                                if !isnothing(deconstruct_result823)
                                                    unwrapped824 = deconstruct_result823
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped824))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1612 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1612 = nothing
                                                    end
                                                    deconstruct_result821 = _t1612
                                                    if !isnothing(deconstruct_result821)
                                                        unwrapped822 = deconstruct_result821
                                                        pretty_boolean_value(pp, unwrapped822)
                                                    else
                                                        fields820 = msg
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
    flat851 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat851)
        write(pp, flat851)
        return nothing
    else
        _dollar_dollar = msg
        fields846 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields847 = fields846
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field848 = unwrapped_fields847[1]
        write(pp, string(field848))
        newline(pp)
        field849 = unwrapped_fields847[2]
        write(pp, string(field849))
        newline(pp)
        field850 = unwrapped_fields847[3]
        write(pp, string(field850))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat862 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat862)
        write(pp, flat862)
        return nothing
    else
        _dollar_dollar = msg
        fields852 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields853 = fields852
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field854 = unwrapped_fields853[1]
        write(pp, string(field854))
        newline(pp)
        field855 = unwrapped_fields853[2]
        write(pp, string(field855))
        newline(pp)
        field856 = unwrapped_fields853[3]
        write(pp, string(field856))
        newline(pp)
        field857 = unwrapped_fields853[4]
        write(pp, string(field857))
        newline(pp)
        field858 = unwrapped_fields853[5]
        write(pp, string(field858))
        newline(pp)
        field859 = unwrapped_fields853[6]
        write(pp, string(field859))
        field860 = unwrapped_fields853[7]
        if !isnothing(field860)
            newline(pp)
            opt_val861 = field860
            write(pp, string(opt_val861))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1613 = ()
    else
        _t1613 = nothing
    end
    deconstruct_result865 = _t1613
    if !isnothing(deconstruct_result865)
        unwrapped866 = deconstruct_result865
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1614 = ()
        else
            _t1614 = nothing
        end
        deconstruct_result863 = _t1614
        if !isnothing(deconstruct_result863)
            unwrapped864 = deconstruct_result863
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat871 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat871)
        write(pp, flat871)
        return nothing
    else
        _dollar_dollar = msg
        fields867 = _dollar_dollar.fragments
        unwrapped_fields868 = fields867
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields868)
            newline(pp)
            for (i1615, elem869) in enumerate(unwrapped_fields868)
                i870 = i1615 - 1
                if (i870 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem869)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat874 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat874)
        write(pp, flat874)
        return nothing
    else
        _dollar_dollar = msg
        fields872 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields873 = fields872
        write(pp, ":")
        write(pp, unwrapped_fields873)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat881 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat881)
        write(pp, flat881)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1616 = _dollar_dollar.writes
        else
            _t1616 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1617 = _dollar_dollar.reads
        else
            _t1617 = nothing
        end
        fields875 = (_t1616, _t1617,)
        unwrapped_fields876 = fields875
        write(pp, "(epoch")
        indent_sexp!(pp)
        field877 = unwrapped_fields876[1]
        if !isnothing(field877)
            newline(pp)
            opt_val878 = field877
            pretty_epoch_writes(pp, opt_val878)
        end
        field879 = unwrapped_fields876[2]
        if !isnothing(field879)
            newline(pp)
            opt_val880 = field879
            pretty_epoch_reads(pp, opt_val880)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat885 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat885)
        write(pp, flat885)
        return nothing
    else
        fields882 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields882)
            newline(pp)
            for (i1618, elem883) in enumerate(fields882)
                i884 = i1618 - 1
                if (i884 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem883)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat894 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat894)
        write(pp, flat894)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1619 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1619 = nothing
        end
        deconstruct_result892 = _t1619
        if !isnothing(deconstruct_result892)
            unwrapped893 = deconstruct_result892
            pretty_define(pp, unwrapped893)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1620 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1620 = nothing
            end
            deconstruct_result890 = _t1620
            if !isnothing(deconstruct_result890)
                unwrapped891 = deconstruct_result890
                pretty_undefine(pp, unwrapped891)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1621 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1621 = nothing
                end
                deconstruct_result888 = _t1621
                if !isnothing(deconstruct_result888)
                    unwrapped889 = deconstruct_result888
                    pretty_context(pp, unwrapped889)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1622 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1622 = nothing
                    end
                    deconstruct_result886 = _t1622
                    if !isnothing(deconstruct_result886)
                        unwrapped887 = deconstruct_result886
                        pretty_snapshot(pp, unwrapped887)
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
    flat897 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat897)
        write(pp, flat897)
        return nothing
    else
        _dollar_dollar = msg
        fields895 = _dollar_dollar.fragment
        unwrapped_fields896 = fields895
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields896)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat904 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat904)
        write(pp, flat904)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields898 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields899 = fields898
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field900 = unwrapped_fields899[1]
        pretty_new_fragment_id(pp, field900)
        field901 = unwrapped_fields899[2]
        if !isempty(field901)
            newline(pp)
            for (i1623, elem902) in enumerate(field901)
                i903 = i1623 - 1
                if (i903 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem902)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat906 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        fields905 = msg
        pretty_fragment_id(pp, fields905)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat915 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat915)
        write(pp, flat915)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1624 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1624 = nothing
        end
        deconstruct_result913 = _t1624
        if !isnothing(deconstruct_result913)
            unwrapped914 = deconstruct_result913
            pretty_def(pp, unwrapped914)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1625 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1625 = nothing
            end
            deconstruct_result911 = _t1625
            if !isnothing(deconstruct_result911)
                unwrapped912 = deconstruct_result911
                pretty_algorithm(pp, unwrapped912)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1626 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1626 = nothing
                end
                deconstruct_result909 = _t1626
                if !isnothing(deconstruct_result909)
                    unwrapped910 = deconstruct_result909
                    pretty_constraint(pp, unwrapped910)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1627 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1627 = nothing
                    end
                    deconstruct_result907 = _t1627
                    if !isnothing(deconstruct_result907)
                        unwrapped908 = deconstruct_result907
                        pretty_data(pp, unwrapped908)
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
    flat922 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat922)
        write(pp, flat922)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1628 = _dollar_dollar.attrs
        else
            _t1628 = nothing
        end
        fields916 = (_dollar_dollar.name, _dollar_dollar.body, _t1628,)
        unwrapped_fields917 = fields916
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field918 = unwrapped_fields917[1]
        pretty_relation_id(pp, field918)
        newline(pp)
        field919 = unwrapped_fields917[2]
        pretty_abstraction(pp, field919)
        field920 = unwrapped_fields917[3]
        if !isnothing(field920)
            newline(pp)
            opt_val921 = field920
            pretty_attrs(pp, opt_val921)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat927 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat927)
        write(pp, flat927)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1630 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1629 = _t1630
        else
            _t1629 = nothing
        end
        deconstruct_result925 = _t1629
        if !isnothing(deconstruct_result925)
            unwrapped926 = deconstruct_result925
            write(pp, ":")
            write(pp, unwrapped926)
        else
            _dollar_dollar = msg
            _t1631 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result923 = _t1631
            if !isnothing(deconstruct_result923)
                unwrapped924 = deconstruct_result923
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped924))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat932 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat932)
        write(pp, flat932)
        return nothing
    else
        _dollar_dollar = msg
        _t1632 = deconstruct_bindings(pp, _dollar_dollar)
        fields928 = (_t1632, _dollar_dollar.value,)
        unwrapped_fields929 = fields928
        write(pp, "(")
        indent!(pp)
        field930 = unwrapped_fields929[1]
        pretty_bindings(pp, field930)
        newline(pp)
        field931 = unwrapped_fields929[2]
        pretty_formula(pp, field931)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat940 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat940)
        write(pp, flat940)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1633 = _dollar_dollar[2]
        else
            _t1633 = nothing
        end
        fields933 = (_dollar_dollar[1], _t1633,)
        unwrapped_fields934 = fields933
        write(pp, "[")
        indent!(pp)
        field935 = unwrapped_fields934[1]
        for (i1634, elem936) in enumerate(field935)
            i937 = i1634 - 1
            if (i937 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem936)
        end
        field938 = unwrapped_fields934[2]
        if !isnothing(field938)
            newline(pp)
            opt_val939 = field938
            pretty_value_bindings(pp, opt_val939)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat945 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat945)
        write(pp, flat945)
        return nothing
    else
        _dollar_dollar = msg
        fields941 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields942 = fields941
        field943 = unwrapped_fields942[1]
        write(pp, field943)
        write(pp, "::")
        field944 = unwrapped_fields942[2]
        pretty_type(pp, field944)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat974 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat974)
        write(pp, flat974)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1635 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1635 = nothing
        end
        deconstruct_result972 = _t1635
        if !isnothing(deconstruct_result972)
            unwrapped973 = deconstruct_result972
            pretty_unspecified_type(pp, unwrapped973)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1636 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1636 = nothing
            end
            deconstruct_result970 = _t1636
            if !isnothing(deconstruct_result970)
                unwrapped971 = deconstruct_result970
                pretty_string_type(pp, unwrapped971)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1637 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1637 = nothing
                end
                deconstruct_result968 = _t1637
                if !isnothing(deconstruct_result968)
                    unwrapped969 = deconstruct_result968
                    pretty_int_type(pp, unwrapped969)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1638 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1638 = nothing
                    end
                    deconstruct_result966 = _t1638
                    if !isnothing(deconstruct_result966)
                        unwrapped967 = deconstruct_result966
                        pretty_float_type(pp, unwrapped967)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1639 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1639 = nothing
                        end
                        deconstruct_result964 = _t1639
                        if !isnothing(deconstruct_result964)
                            unwrapped965 = deconstruct_result964
                            pretty_uint128_type(pp, unwrapped965)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1640 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1640 = nothing
                            end
                            deconstruct_result962 = _t1640
                            if !isnothing(deconstruct_result962)
                                unwrapped963 = deconstruct_result962
                                pretty_int128_type(pp, unwrapped963)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1641 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1641 = nothing
                                end
                                deconstruct_result960 = _t1641
                                if !isnothing(deconstruct_result960)
                                    unwrapped961 = deconstruct_result960
                                    pretty_date_type(pp, unwrapped961)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1642 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1642 = nothing
                                    end
                                    deconstruct_result958 = _t1642
                                    if !isnothing(deconstruct_result958)
                                        unwrapped959 = deconstruct_result958
                                        pretty_datetime_type(pp, unwrapped959)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1643 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1643 = nothing
                                        end
                                        deconstruct_result956 = _t1643
                                        if !isnothing(deconstruct_result956)
                                            unwrapped957 = deconstruct_result956
                                            pretty_missing_type(pp, unwrapped957)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1644 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1644 = nothing
                                            end
                                            deconstruct_result954 = _t1644
                                            if !isnothing(deconstruct_result954)
                                                unwrapped955 = deconstruct_result954
                                                pretty_decimal_type(pp, unwrapped955)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1645 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1645 = nothing
                                                end
                                                deconstruct_result952 = _t1645
                                                if !isnothing(deconstruct_result952)
                                                    unwrapped953 = deconstruct_result952
                                                    pretty_boolean_type(pp, unwrapped953)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1646 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1646 = nothing
                                                    end
                                                    deconstruct_result950 = _t1646
                                                    if !isnothing(deconstruct_result950)
                                                        unwrapped951 = deconstruct_result950
                                                        pretty_int32_type(pp, unwrapped951)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1647 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1647 = nothing
                                                        end
                                                        deconstruct_result948 = _t1647
                                                        if !isnothing(deconstruct_result948)
                                                            unwrapped949 = deconstruct_result948
                                                            pretty_float32_type(pp, unwrapped949)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1648 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1648 = nothing
                                                            end
                                                            deconstruct_result946 = _t1648
                                                            if !isnothing(deconstruct_result946)
                                                                unwrapped947 = deconstruct_result946
                                                                pretty_uint32_type(pp, unwrapped947)
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
    fields975 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields976 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields977 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields978 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields979 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields980 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields981 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields982 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields983 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat988 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat988)
        write(pp, flat988)
        return nothing
    else
        _dollar_dollar = msg
        fields984 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields985 = fields984
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field986 = unwrapped_fields985[1]
        write(pp, string(field986))
        newline(pp)
        field987 = unwrapped_fields985[2]
        write(pp, string(field987))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields989 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields990 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields991 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields992 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat996 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat996)
        write(pp, flat996)
        return nothing
    else
        fields993 = msg
        write(pp, "|")
        if !isempty(fields993)
            write(pp, " ")
            for (i1649, elem994) in enumerate(fields993)
                i995 = i1649 - 1
                if (i995 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem994)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1023 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1023)
        write(pp, flat1023)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1650 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1650 = nothing
        end
        deconstruct_result1021 = _t1650
        if !isnothing(deconstruct_result1021)
            unwrapped1022 = deconstruct_result1021
            pretty_true(pp, unwrapped1022)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1651 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1651 = nothing
            end
            deconstruct_result1019 = _t1651
            if !isnothing(deconstruct_result1019)
                unwrapped1020 = deconstruct_result1019
                pretty_false(pp, unwrapped1020)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1652 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1652 = nothing
                end
                deconstruct_result1017 = _t1652
                if !isnothing(deconstruct_result1017)
                    unwrapped1018 = deconstruct_result1017
                    pretty_exists(pp, unwrapped1018)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1653 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1653 = nothing
                    end
                    deconstruct_result1015 = _t1653
                    if !isnothing(deconstruct_result1015)
                        unwrapped1016 = deconstruct_result1015
                        pretty_reduce(pp, unwrapped1016)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1654 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1654 = nothing
                        end
                        deconstruct_result1013 = _t1654
                        if !isnothing(deconstruct_result1013)
                            unwrapped1014 = deconstruct_result1013
                            pretty_conjunction(pp, unwrapped1014)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1655 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1655 = nothing
                            end
                            deconstruct_result1011 = _t1655
                            if !isnothing(deconstruct_result1011)
                                unwrapped1012 = deconstruct_result1011
                                pretty_disjunction(pp, unwrapped1012)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1656 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1656 = nothing
                                end
                                deconstruct_result1009 = _t1656
                                if !isnothing(deconstruct_result1009)
                                    unwrapped1010 = deconstruct_result1009
                                    pretty_not(pp, unwrapped1010)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1657 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1657 = nothing
                                    end
                                    deconstruct_result1007 = _t1657
                                    if !isnothing(deconstruct_result1007)
                                        unwrapped1008 = deconstruct_result1007
                                        pretty_ffi(pp, unwrapped1008)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1658 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1658 = nothing
                                        end
                                        deconstruct_result1005 = _t1658
                                        if !isnothing(deconstruct_result1005)
                                            unwrapped1006 = deconstruct_result1005
                                            pretty_atom(pp, unwrapped1006)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1659 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1659 = nothing
                                            end
                                            deconstruct_result1003 = _t1659
                                            if !isnothing(deconstruct_result1003)
                                                unwrapped1004 = deconstruct_result1003
                                                pretty_pragma(pp, unwrapped1004)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1660 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1660 = nothing
                                                end
                                                deconstruct_result1001 = _t1660
                                                if !isnothing(deconstruct_result1001)
                                                    unwrapped1002 = deconstruct_result1001
                                                    pretty_primitive(pp, unwrapped1002)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1661 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1661 = nothing
                                                    end
                                                    deconstruct_result999 = _t1661
                                                    if !isnothing(deconstruct_result999)
                                                        unwrapped1000 = deconstruct_result999
                                                        pretty_rel_atom(pp, unwrapped1000)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1662 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1662 = nothing
                                                        end
                                                        deconstruct_result997 = _t1662
                                                        if !isnothing(deconstruct_result997)
                                                            unwrapped998 = deconstruct_result997
                                                            pretty_cast(pp, unwrapped998)
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
    fields1024 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1025 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1030 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1030)
        write(pp, flat1030)
        return nothing
    else
        _dollar_dollar = msg
        _t1663 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1026 = (_t1663, _dollar_dollar.body.value,)
        unwrapped_fields1027 = fields1026
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1028 = unwrapped_fields1027[1]
        pretty_bindings(pp, field1028)
        newline(pp)
        field1029 = unwrapped_fields1027[2]
        pretty_formula(pp, field1029)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1036 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1036)
        write(pp, flat1036)
        return nothing
    else
        _dollar_dollar = msg
        fields1031 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1032 = fields1031
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1033 = unwrapped_fields1032[1]
        pretty_abstraction(pp, field1033)
        newline(pp)
        field1034 = unwrapped_fields1032[2]
        pretty_abstraction(pp, field1034)
        newline(pp)
        field1035 = unwrapped_fields1032[3]
        pretty_terms(pp, field1035)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1040 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1040)
        write(pp, flat1040)
        return nothing
    else
        fields1037 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1037)
            newline(pp)
            for (i1664, elem1038) in enumerate(fields1037)
                i1039 = i1664 - 1
                if (i1039 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1038)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1045 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1045)
        write(pp, flat1045)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1665 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1665 = nothing
        end
        deconstruct_result1043 = _t1665
        if !isnothing(deconstruct_result1043)
            unwrapped1044 = deconstruct_result1043
            pretty_var(pp, unwrapped1044)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1666 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1666 = nothing
            end
            deconstruct_result1041 = _t1666
            if !isnothing(deconstruct_result1041)
                unwrapped1042 = deconstruct_result1041
                pretty_value(pp, unwrapped1042)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1048 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1048)
        write(pp, flat1048)
        return nothing
    else
        _dollar_dollar = msg
        fields1046 = _dollar_dollar.name
        unwrapped_fields1047 = fields1046
        write(pp, unwrapped_fields1047)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1074 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1074)
        write(pp, flat1074)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1667 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1667 = nothing
        end
        deconstruct_result1072 = _t1667
        if !isnothing(deconstruct_result1072)
            unwrapped1073 = deconstruct_result1072
            pretty_date(pp, unwrapped1073)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1668 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1668 = nothing
            end
            deconstruct_result1070 = _t1668
            if !isnothing(deconstruct_result1070)
                unwrapped1071 = deconstruct_result1070
                pretty_datetime(pp, unwrapped1071)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1669 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1669 = nothing
                end
                deconstruct_result1068 = _t1669
                if !isnothing(deconstruct_result1068)
                    unwrapped1069 = deconstruct_result1068
                    write(pp, format_string(pp, unwrapped1069))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1670 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1670 = nothing
                    end
                    deconstruct_result1066 = _t1670
                    if !isnothing(deconstruct_result1066)
                        unwrapped1067 = deconstruct_result1066
                        write(pp, format_int32(pp, unwrapped1067))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1671 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1671 = nothing
                        end
                        deconstruct_result1064 = _t1671
                        if !isnothing(deconstruct_result1064)
                            unwrapped1065 = deconstruct_result1064
                            write(pp, format_int(pp, unwrapped1065))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1672 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1672 = nothing
                            end
                            deconstruct_result1062 = _t1672
                            if !isnothing(deconstruct_result1062)
                                unwrapped1063 = deconstruct_result1062
                                write(pp, format_float32(pp, unwrapped1063))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1673 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1673 = nothing
                                end
                                deconstruct_result1060 = _t1673
                                if !isnothing(deconstruct_result1060)
                                    unwrapped1061 = deconstruct_result1060
                                    write(pp, format_float(pp, unwrapped1061))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1674 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1674 = nothing
                                    end
                                    deconstruct_result1058 = _t1674
                                    if !isnothing(deconstruct_result1058)
                                        unwrapped1059 = deconstruct_result1058
                                        write(pp, format_uint32(pp, unwrapped1059))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1675 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1675 = nothing
                                        end
                                        deconstruct_result1056 = _t1675
                                        if !isnothing(deconstruct_result1056)
                                            unwrapped1057 = deconstruct_result1056
                                            write(pp, format_uint128(pp, unwrapped1057))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1676 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1676 = nothing
                                            end
                                            deconstruct_result1054 = _t1676
                                            if !isnothing(deconstruct_result1054)
                                                unwrapped1055 = deconstruct_result1054
                                                write(pp, format_int128(pp, unwrapped1055))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1677 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1677 = nothing
                                                end
                                                deconstruct_result1052 = _t1677
                                                if !isnothing(deconstruct_result1052)
                                                    unwrapped1053 = deconstruct_result1052
                                                    write(pp, format_decimal(pp, unwrapped1053))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1678 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1678 = nothing
                                                    end
                                                    deconstruct_result1050 = _t1678
                                                    if !isnothing(deconstruct_result1050)
                                                        unwrapped1051 = deconstruct_result1050
                                                        pretty_boolean_value(pp, unwrapped1051)
                                                    else
                                                        fields1049 = msg
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
    flat1080 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1080)
        write(pp, flat1080)
        return nothing
    else
        _dollar_dollar = msg
        fields1075 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1076 = fields1075
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1077 = unwrapped_fields1076[1]
        write(pp, format_int(pp, field1077))
        newline(pp)
        field1078 = unwrapped_fields1076[2]
        write(pp, format_int(pp, field1078))
        newline(pp)
        field1079 = unwrapped_fields1076[3]
        write(pp, format_int(pp, field1079))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1091 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1091)
        write(pp, flat1091)
        return nothing
    else
        _dollar_dollar = msg
        fields1081 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1082 = fields1081
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1083 = unwrapped_fields1082[1]
        write(pp, format_int(pp, field1083))
        newline(pp)
        field1084 = unwrapped_fields1082[2]
        write(pp, format_int(pp, field1084))
        newline(pp)
        field1085 = unwrapped_fields1082[3]
        write(pp, format_int(pp, field1085))
        newline(pp)
        field1086 = unwrapped_fields1082[4]
        write(pp, format_int(pp, field1086))
        newline(pp)
        field1087 = unwrapped_fields1082[5]
        write(pp, format_int(pp, field1087))
        newline(pp)
        field1088 = unwrapped_fields1082[6]
        write(pp, format_int(pp, field1088))
        field1089 = unwrapped_fields1082[7]
        if !isnothing(field1089)
            newline(pp)
            opt_val1090 = field1089
            write(pp, format_int(pp, opt_val1090))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1096 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        _dollar_dollar = msg
        fields1092 = _dollar_dollar.args
        unwrapped_fields1093 = fields1092
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1093)
            newline(pp)
            for (i1679, elem1094) in enumerate(unwrapped_fields1093)
                i1095 = i1679 - 1
                if (i1095 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1094)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1101 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1101)
        write(pp, flat1101)
        return nothing
    else
        _dollar_dollar = msg
        fields1097 = _dollar_dollar.args
        unwrapped_fields1098 = fields1097
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1098)
            newline(pp)
            for (i1680, elem1099) in enumerate(unwrapped_fields1098)
                i1100 = i1680 - 1
                if (i1100 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1099)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1104 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1104)
        write(pp, flat1104)
        return nothing
    else
        _dollar_dollar = msg
        fields1102 = _dollar_dollar.arg
        unwrapped_fields1103 = fields1102
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1103)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1110 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1110)
        write(pp, flat1110)
        return nothing
    else
        _dollar_dollar = msg
        fields1105 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1106 = fields1105
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1107 = unwrapped_fields1106[1]
        pretty_name(pp, field1107)
        newline(pp)
        field1108 = unwrapped_fields1106[2]
        pretty_ffi_args(pp, field1108)
        newline(pp)
        field1109 = unwrapped_fields1106[3]
        pretty_terms(pp, field1109)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1112 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1112)
        write(pp, flat1112)
        return nothing
    else
        fields1111 = msg
        write(pp, ":")
        write(pp, fields1111)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1116 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1116)
        write(pp, flat1116)
        return nothing
    else
        fields1113 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1113)
            newline(pp)
            for (i1681, elem1114) in enumerate(fields1113)
                i1115 = i1681 - 1
                if (i1115 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1114)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1123 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1123)
        write(pp, flat1123)
        return nothing
    else
        _dollar_dollar = msg
        fields1117 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1118 = fields1117
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1119 = unwrapped_fields1118[1]
        pretty_relation_id(pp, field1119)
        field1120 = unwrapped_fields1118[2]
        if !isempty(field1120)
            newline(pp)
            for (i1682, elem1121) in enumerate(field1120)
                i1122 = i1682 - 1
                if (i1122 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1121)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1130 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1130)
        write(pp, flat1130)
        return nothing
    else
        _dollar_dollar = msg
        fields1124 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1125 = fields1124
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1126 = unwrapped_fields1125[1]
        pretty_name(pp, field1126)
        field1127 = unwrapped_fields1125[2]
        if !isempty(field1127)
            newline(pp)
            for (i1683, elem1128) in enumerate(field1127)
                i1129 = i1683 - 1
                if (i1129 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1128)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1146 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1146)
        write(pp, flat1146)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1684 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1684 = nothing
        end
        guard_result1145 = _t1684
        if !isnothing(guard_result1145)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1685 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1685 = nothing
            end
            guard_result1144 = _t1685
            if !isnothing(guard_result1144)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1686 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1686 = nothing
                end
                guard_result1143 = _t1686
                if !isnothing(guard_result1143)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1687 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1687 = nothing
                    end
                    guard_result1142 = _t1687
                    if !isnothing(guard_result1142)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1688 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1688 = nothing
                        end
                        guard_result1141 = _t1688
                        if !isnothing(guard_result1141)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1689 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1689 = nothing
                            end
                            guard_result1140 = _t1689
                            if !isnothing(guard_result1140)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1690 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1690 = nothing
                                end
                                guard_result1139 = _t1690
                                if !isnothing(guard_result1139)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1691 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1691 = nothing
                                    end
                                    guard_result1138 = _t1691
                                    if !isnothing(guard_result1138)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1692 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1692 = nothing
                                        end
                                        guard_result1137 = _t1692
                                        if !isnothing(guard_result1137)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1131 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1132 = fields1131
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1133 = unwrapped_fields1132[1]
                                            pretty_name(pp, field1133)
                                            field1134 = unwrapped_fields1132[2]
                                            if !isempty(field1134)
                                                newline(pp)
                                                for (i1693, elem1135) in enumerate(field1134)
                                                    i1136 = i1693 - 1
                                                    if (i1136 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1135)
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
    flat1151 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1151)
        write(pp, flat1151)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1694 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1694 = nothing
        end
        fields1147 = _t1694
        unwrapped_fields1148 = fields1147
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1149 = unwrapped_fields1148[1]
        pretty_term(pp, field1149)
        newline(pp)
        field1150 = unwrapped_fields1148[2]
        pretty_term(pp, field1150)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1156 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1156)
        write(pp, flat1156)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1695 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1695 = nothing
        end
        fields1152 = _t1695
        unwrapped_fields1153 = fields1152
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1154 = unwrapped_fields1153[1]
        pretty_term(pp, field1154)
        newline(pp)
        field1155 = unwrapped_fields1153[2]
        pretty_term(pp, field1155)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1161 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1161)
        write(pp, flat1161)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1696 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1696 = nothing
        end
        fields1157 = _t1696
        unwrapped_fields1158 = fields1157
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1159 = unwrapped_fields1158[1]
        pretty_term(pp, field1159)
        newline(pp)
        field1160 = unwrapped_fields1158[2]
        pretty_term(pp, field1160)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1166 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1166)
        write(pp, flat1166)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1697 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1697 = nothing
        end
        fields1162 = _t1697
        unwrapped_fields1163 = fields1162
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1164 = unwrapped_fields1163[1]
        pretty_term(pp, field1164)
        newline(pp)
        field1165 = unwrapped_fields1163[2]
        pretty_term(pp, field1165)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1171 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1171)
        write(pp, flat1171)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1698 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1698 = nothing
        end
        fields1167 = _t1698
        unwrapped_fields1168 = fields1167
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1169 = unwrapped_fields1168[1]
        pretty_term(pp, field1169)
        newline(pp)
        field1170 = unwrapped_fields1168[2]
        pretty_term(pp, field1170)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1177 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1177)
        write(pp, flat1177)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1699 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1699 = nothing
        end
        fields1172 = _t1699
        unwrapped_fields1173 = fields1172
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1174 = unwrapped_fields1173[1]
        pretty_term(pp, field1174)
        newline(pp)
        field1175 = unwrapped_fields1173[2]
        pretty_term(pp, field1175)
        newline(pp)
        field1176 = unwrapped_fields1173[3]
        pretty_term(pp, field1176)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1183 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1183)
        write(pp, flat1183)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1700 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1700 = nothing
        end
        fields1178 = _t1700
        unwrapped_fields1179 = fields1178
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1180 = unwrapped_fields1179[1]
        pretty_term(pp, field1180)
        newline(pp)
        field1181 = unwrapped_fields1179[2]
        pretty_term(pp, field1181)
        newline(pp)
        field1182 = unwrapped_fields1179[3]
        pretty_term(pp, field1182)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1189 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1189)
        write(pp, flat1189)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1701 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1701 = nothing
        end
        fields1184 = _t1701
        unwrapped_fields1185 = fields1184
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1186 = unwrapped_fields1185[1]
        pretty_term(pp, field1186)
        newline(pp)
        field1187 = unwrapped_fields1185[2]
        pretty_term(pp, field1187)
        newline(pp)
        field1188 = unwrapped_fields1185[3]
        pretty_term(pp, field1188)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1195 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1195)
        write(pp, flat1195)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1702 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1702 = nothing
        end
        fields1190 = _t1702
        unwrapped_fields1191 = fields1190
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1192 = unwrapped_fields1191[1]
        pretty_term(pp, field1192)
        newline(pp)
        field1193 = unwrapped_fields1191[2]
        pretty_term(pp, field1193)
        newline(pp)
        field1194 = unwrapped_fields1191[3]
        pretty_term(pp, field1194)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1200 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1200)
        write(pp, flat1200)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1703 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1703 = nothing
        end
        deconstruct_result1198 = _t1703
        if !isnothing(deconstruct_result1198)
            unwrapped1199 = deconstruct_result1198
            pretty_specialized_value(pp, unwrapped1199)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1704 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1704 = nothing
            end
            deconstruct_result1196 = _t1704
            if !isnothing(deconstruct_result1196)
                unwrapped1197 = deconstruct_result1196
                pretty_term(pp, unwrapped1197)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1202 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1202)
        write(pp, flat1202)
        return nothing
    else
        fields1201 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1201)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1209 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1209)
        write(pp, flat1209)
        return nothing
    else
        _dollar_dollar = msg
        fields1203 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1204 = fields1203
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1205 = unwrapped_fields1204[1]
        pretty_name(pp, field1205)
        field1206 = unwrapped_fields1204[2]
        if !isempty(field1206)
            newline(pp)
            for (i1705, elem1207) in enumerate(field1206)
                i1208 = i1705 - 1
                if (i1208 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1207)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1214 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1214)
        write(pp, flat1214)
        return nothing
    else
        _dollar_dollar = msg
        fields1210 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1211 = fields1210
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1212 = unwrapped_fields1211[1]
        pretty_term(pp, field1212)
        newline(pp)
        field1213 = unwrapped_fields1211[2]
        pretty_term(pp, field1213)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1218 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1218)
        write(pp, flat1218)
        return nothing
    else
        fields1215 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1215)
            newline(pp)
            for (i1706, elem1216) in enumerate(fields1215)
                i1217 = i1706 - 1
                if (i1217 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1216)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1225 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1225)
        write(pp, flat1225)
        return nothing
    else
        _dollar_dollar = msg
        fields1219 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1220 = fields1219
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1221 = unwrapped_fields1220[1]
        pretty_name(pp, field1221)
        field1222 = unwrapped_fields1220[2]
        if !isempty(field1222)
            newline(pp)
            for (i1707, elem1223) in enumerate(field1222)
                i1224 = i1707 - 1
                if (i1224 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1223)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1232 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1232)
        write(pp, flat1232)
        return nothing
    else
        _dollar_dollar = msg
        fields1226 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1227 = fields1226
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1228 = unwrapped_fields1227[1]
        if !isempty(field1228)
            newline(pp)
            for (i1708, elem1229) in enumerate(field1228)
                i1230 = i1708 - 1
                if (i1230 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1229)
            end
        end
        newline(pp)
        field1231 = unwrapped_fields1227[2]
        pretty_script(pp, field1231)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1237 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1237)
        write(pp, flat1237)
        return nothing
    else
        _dollar_dollar = msg
        fields1233 = _dollar_dollar.constructs
        unwrapped_fields1234 = fields1233
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1234)
            newline(pp)
            for (i1709, elem1235) in enumerate(unwrapped_fields1234)
                i1236 = i1709 - 1
                if (i1236 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1235)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1242 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1242)
        write(pp, flat1242)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1710 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1710 = nothing
        end
        deconstruct_result1240 = _t1710
        if !isnothing(deconstruct_result1240)
            unwrapped1241 = deconstruct_result1240
            pretty_loop(pp, unwrapped1241)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1711 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1711 = nothing
            end
            deconstruct_result1238 = _t1711
            if !isnothing(deconstruct_result1238)
                unwrapped1239 = deconstruct_result1238
                pretty_instruction(pp, unwrapped1239)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1247 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1247)
        write(pp, flat1247)
        return nothing
    else
        _dollar_dollar = msg
        fields1243 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1244 = fields1243
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1245 = unwrapped_fields1244[1]
        pretty_init(pp, field1245)
        newline(pp)
        field1246 = unwrapped_fields1244[2]
        pretty_script(pp, field1246)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1251 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1251)
        write(pp, flat1251)
        return nothing
    else
        fields1248 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1248)
            newline(pp)
            for (i1712, elem1249) in enumerate(fields1248)
                i1250 = i1712 - 1
                if (i1250 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1249)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1262 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1262)
        write(pp, flat1262)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1713 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1713 = nothing
        end
        deconstruct_result1260 = _t1713
        if !isnothing(deconstruct_result1260)
            unwrapped1261 = deconstruct_result1260
            pretty_assign(pp, unwrapped1261)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1714 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1714 = nothing
            end
            deconstruct_result1258 = _t1714
            if !isnothing(deconstruct_result1258)
                unwrapped1259 = deconstruct_result1258
                pretty_upsert(pp, unwrapped1259)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1715 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1715 = nothing
                end
                deconstruct_result1256 = _t1715
                if !isnothing(deconstruct_result1256)
                    unwrapped1257 = deconstruct_result1256
                    pretty_break(pp, unwrapped1257)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1716 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1716 = nothing
                    end
                    deconstruct_result1254 = _t1716
                    if !isnothing(deconstruct_result1254)
                        unwrapped1255 = deconstruct_result1254
                        pretty_monoid_def(pp, unwrapped1255)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1717 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1717 = nothing
                        end
                        deconstruct_result1252 = _t1717
                        if !isnothing(deconstruct_result1252)
                            unwrapped1253 = deconstruct_result1252
                            pretty_monus_def(pp, unwrapped1253)
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
    flat1269 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1269)
        write(pp, flat1269)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1718 = _dollar_dollar.attrs
        else
            _t1718 = nothing
        end
        fields1263 = (_dollar_dollar.name, _dollar_dollar.body, _t1718,)
        unwrapped_fields1264 = fields1263
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1265 = unwrapped_fields1264[1]
        pretty_relation_id(pp, field1265)
        newline(pp)
        field1266 = unwrapped_fields1264[2]
        pretty_abstraction(pp, field1266)
        field1267 = unwrapped_fields1264[3]
        if !isnothing(field1267)
            newline(pp)
            opt_val1268 = field1267
            pretty_attrs(pp, opt_val1268)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1276 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1276)
        write(pp, flat1276)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1719 = _dollar_dollar.attrs
        else
            _t1719 = nothing
        end
        fields1270 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1719,)
        unwrapped_fields1271 = fields1270
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1272 = unwrapped_fields1271[1]
        pretty_relation_id(pp, field1272)
        newline(pp)
        field1273 = unwrapped_fields1271[2]
        pretty_abstraction_with_arity(pp, field1273)
        field1274 = unwrapped_fields1271[3]
        if !isnothing(field1274)
            newline(pp)
            opt_val1275 = field1274
            pretty_attrs(pp, opt_val1275)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1281 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1281)
        write(pp, flat1281)
        return nothing
    else
        _dollar_dollar = msg
        _t1720 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1277 = (_t1720, _dollar_dollar[1].value,)
        unwrapped_fields1278 = fields1277
        write(pp, "(")
        indent!(pp)
        field1279 = unwrapped_fields1278[1]
        pretty_bindings(pp, field1279)
        newline(pp)
        field1280 = unwrapped_fields1278[2]
        pretty_formula(pp, field1280)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1288 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1288)
        write(pp, flat1288)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1721 = _dollar_dollar.attrs
        else
            _t1721 = nothing
        end
        fields1282 = (_dollar_dollar.name, _dollar_dollar.body, _t1721,)
        unwrapped_fields1283 = fields1282
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1284 = unwrapped_fields1283[1]
        pretty_relation_id(pp, field1284)
        newline(pp)
        field1285 = unwrapped_fields1283[2]
        pretty_abstraction(pp, field1285)
        field1286 = unwrapped_fields1283[3]
        if !isnothing(field1286)
            newline(pp)
            opt_val1287 = field1286
            pretty_attrs(pp, opt_val1287)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1296 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1296)
        write(pp, flat1296)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1722 = _dollar_dollar.attrs
        else
            _t1722 = nothing
        end
        fields1289 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1722,)
        unwrapped_fields1290 = fields1289
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1291 = unwrapped_fields1290[1]
        pretty_monoid(pp, field1291)
        newline(pp)
        field1292 = unwrapped_fields1290[2]
        pretty_relation_id(pp, field1292)
        newline(pp)
        field1293 = unwrapped_fields1290[3]
        pretty_abstraction_with_arity(pp, field1293)
        field1294 = unwrapped_fields1290[4]
        if !isnothing(field1294)
            newline(pp)
            opt_val1295 = field1294
            pretty_attrs(pp, opt_val1295)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1305 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1305)
        write(pp, flat1305)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1723 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1723 = nothing
        end
        deconstruct_result1303 = _t1723
        if !isnothing(deconstruct_result1303)
            unwrapped1304 = deconstruct_result1303
            pretty_or_monoid(pp, unwrapped1304)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1724 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1724 = nothing
            end
            deconstruct_result1301 = _t1724
            if !isnothing(deconstruct_result1301)
                unwrapped1302 = deconstruct_result1301
                pretty_min_monoid(pp, unwrapped1302)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1725 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1725 = nothing
                end
                deconstruct_result1299 = _t1725
                if !isnothing(deconstruct_result1299)
                    unwrapped1300 = deconstruct_result1299
                    pretty_max_monoid(pp, unwrapped1300)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1726 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1726 = nothing
                    end
                    deconstruct_result1297 = _t1726
                    if !isnothing(deconstruct_result1297)
                        unwrapped1298 = deconstruct_result1297
                        pretty_sum_monoid(pp, unwrapped1298)
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
    fields1306 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1309 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1309)
        write(pp, flat1309)
        return nothing
    else
        _dollar_dollar = msg
        fields1307 = _dollar_dollar.var"#type"
        unwrapped_fields1308 = fields1307
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1308)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1312 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1312)
        write(pp, flat1312)
        return nothing
    else
        _dollar_dollar = msg
        fields1310 = _dollar_dollar.var"#type"
        unwrapped_fields1311 = fields1310
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1311)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1315 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1315)
        write(pp, flat1315)
        return nothing
    else
        _dollar_dollar = msg
        fields1313 = _dollar_dollar.var"#type"
        unwrapped_fields1314 = fields1313
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1314)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1323 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1323)
        write(pp, flat1323)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1727 = _dollar_dollar.attrs
        else
            _t1727 = nothing
        end
        fields1316 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1727,)
        unwrapped_fields1317 = fields1316
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1318 = unwrapped_fields1317[1]
        pretty_monoid(pp, field1318)
        newline(pp)
        field1319 = unwrapped_fields1317[2]
        pretty_relation_id(pp, field1319)
        newline(pp)
        field1320 = unwrapped_fields1317[3]
        pretty_abstraction_with_arity(pp, field1320)
        field1321 = unwrapped_fields1317[4]
        if !isnothing(field1321)
            newline(pp)
            opt_val1322 = field1321
            pretty_attrs(pp, opt_val1322)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1330 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1330)
        write(pp, flat1330)
        return nothing
    else
        _dollar_dollar = msg
        fields1324 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1325 = fields1324
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1326 = unwrapped_fields1325[1]
        pretty_relation_id(pp, field1326)
        newline(pp)
        field1327 = unwrapped_fields1325[2]
        pretty_abstraction(pp, field1327)
        newline(pp)
        field1328 = unwrapped_fields1325[3]
        pretty_functional_dependency_keys(pp, field1328)
        newline(pp)
        field1329 = unwrapped_fields1325[4]
        pretty_functional_dependency_values(pp, field1329)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1334 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1334)
        write(pp, flat1334)
        return nothing
    else
        fields1331 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1331)
            newline(pp)
            for (i1728, elem1332) in enumerate(fields1331)
                i1333 = i1728 - 1
                if (i1333 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1332)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1338 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1338)
        write(pp, flat1338)
        return nothing
    else
        fields1335 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1335)
            newline(pp)
            for (i1729, elem1336) in enumerate(fields1335)
                i1337 = i1729 - 1
                if (i1337 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1336)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1347 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1347)
        write(pp, flat1347)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1730 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1730 = nothing
        end
        deconstruct_result1345 = _t1730
        if !isnothing(deconstruct_result1345)
            unwrapped1346 = deconstruct_result1345
            pretty_edb(pp, unwrapped1346)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1731 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1731 = nothing
            end
            deconstruct_result1343 = _t1731
            if !isnothing(deconstruct_result1343)
                unwrapped1344 = deconstruct_result1343
                pretty_betree_relation(pp, unwrapped1344)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1732 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1732 = nothing
                end
                deconstruct_result1341 = _t1732
                if !isnothing(deconstruct_result1341)
                    unwrapped1342 = deconstruct_result1341
                    pretty_csv_data(pp, unwrapped1342)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1733 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1733 = nothing
                    end
                    deconstruct_result1339 = _t1733
                    if !isnothing(deconstruct_result1339)
                        unwrapped1340 = deconstruct_result1339
                        pretty_iceberg_data(pp, unwrapped1340)
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
    flat1353 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1353)
        write(pp, flat1353)
        return nothing
    else
        _dollar_dollar = msg
        fields1348 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1349 = fields1348
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1350 = unwrapped_fields1349[1]
        pretty_relation_id(pp, field1350)
        newline(pp)
        field1351 = unwrapped_fields1349[2]
        pretty_edb_path(pp, field1351)
        newline(pp)
        field1352 = unwrapped_fields1349[3]
        pretty_edb_types(pp, field1352)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1357 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1357)
        write(pp, flat1357)
        return nothing
    else
        fields1354 = msg
        write(pp, "[")
        indent!(pp)
        for (i1734, elem1355) in enumerate(fields1354)
            i1356 = i1734 - 1
            if (i1356 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1355))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1361 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1361)
        write(pp, flat1361)
        return nothing
    else
        fields1358 = msg
        write(pp, "[")
        indent!(pp)
        for (i1735, elem1359) in enumerate(fields1358)
            i1360 = i1735 - 1
            if (i1360 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1359)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1366 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1366)
        write(pp, flat1366)
        return nothing
    else
        _dollar_dollar = msg
        fields1362 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1363 = fields1362
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1364 = unwrapped_fields1363[1]
        pretty_relation_id(pp, field1364)
        newline(pp)
        field1365 = unwrapped_fields1363[2]
        pretty_betree_info(pp, field1365)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1372 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1372)
        write(pp, flat1372)
        return nothing
    else
        _dollar_dollar = msg
        _t1736 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1367 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1736,)
        unwrapped_fields1368 = fields1367
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1369 = unwrapped_fields1368[1]
        pretty_betree_info_key_types(pp, field1369)
        newline(pp)
        field1370 = unwrapped_fields1368[2]
        pretty_betree_info_value_types(pp, field1370)
        newline(pp)
        field1371 = unwrapped_fields1368[3]
        pretty_config_dict(pp, field1371)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1376 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        fields1373 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1373)
            newline(pp)
            for (i1737, elem1374) in enumerate(fields1373)
                i1375 = i1737 - 1
                if (i1375 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1374)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1380 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1380)
        write(pp, flat1380)
        return nothing
    else
        fields1377 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1377)
            newline(pp)
            for (i1738, elem1378) in enumerate(fields1377)
                i1379 = i1738 - 1
                if (i1379 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1378)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1387 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1387)
        write(pp, flat1387)
        return nothing
    else
        _dollar_dollar = msg
        fields1381 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1382 = fields1381
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1383 = unwrapped_fields1382[1]
        pretty_csvlocator(pp, field1383)
        newline(pp)
        field1384 = unwrapped_fields1382[2]
        pretty_csv_config(pp, field1384)
        newline(pp)
        field1385 = unwrapped_fields1382[3]
        pretty_gnf_columns(pp, field1385)
        newline(pp)
        field1386 = unwrapped_fields1382[4]
        pretty_csv_asof(pp, field1386)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1394 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1394)
        write(pp, flat1394)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1739 = _dollar_dollar.paths
        else
            _t1739 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1740 = String(copy(_dollar_dollar.inline_data))
        else
            _t1740 = nothing
        end
        fields1388 = (_t1739, _t1740,)
        unwrapped_fields1389 = fields1388
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1390 = unwrapped_fields1389[1]
        if !isnothing(field1390)
            newline(pp)
            opt_val1391 = field1390
            pretty_csv_locator_paths(pp, opt_val1391)
        end
        field1392 = unwrapped_fields1389[2]
        if !isnothing(field1392)
            newline(pp)
            opt_val1393 = field1392
            pretty_csv_locator_inline_data(pp, opt_val1393)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1398 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1398)
        write(pp, flat1398)
        return nothing
    else
        fields1395 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1395)
            newline(pp)
            for (i1741, elem1396) in enumerate(fields1395)
                i1397 = i1741 - 1
                if (i1397 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1396))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1400 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1400)
        write(pp, flat1400)
        return nothing
    else
        fields1399 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1399))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1403 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1403)
        write(pp, flat1403)
        return nothing
    else
        _dollar_dollar = msg
        _t1742 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1401 = _t1742
        unwrapped_fields1402 = fields1401
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1402)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1407 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1407)
        write(pp, flat1407)
        return nothing
    else
        fields1404 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1404)
            newline(pp)
            for (i1743, elem1405) in enumerate(fields1404)
                i1406 = i1743 - 1
                if (i1406 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1405)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1416 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1416)
        write(pp, flat1416)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1744 = _dollar_dollar.target_id
        else
            _t1744 = nothing
        end
        fields1408 = (_dollar_dollar.column_path, _t1744, _dollar_dollar.types,)
        unwrapped_fields1409 = fields1408
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1410 = unwrapped_fields1409[1]
        pretty_gnf_column_path(pp, field1410)
        field1411 = unwrapped_fields1409[2]
        if !isnothing(field1411)
            newline(pp)
            opt_val1412 = field1411
            pretty_relation_id(pp, opt_val1412)
        end
        newline(pp)
        write(pp, "[")
        field1413 = unwrapped_fields1409[3]
        for (i1745, elem1414) in enumerate(field1413)
            i1415 = i1745 - 1
            if (i1415 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1414)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1423 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1423)
        write(pp, flat1423)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1746 = _dollar_dollar[1]
        else
            _t1746 = nothing
        end
        deconstruct_result1421 = _t1746
        if !isnothing(deconstruct_result1421)
            unwrapped1422 = deconstruct_result1421
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1422))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1747 = _dollar_dollar
            else
                _t1747 = nothing
            end
            deconstruct_result1417 = _t1747
            if !isnothing(deconstruct_result1417)
                unwrapped1418 = deconstruct_result1417
                write(pp, "[")
                indent!(pp)
                for (i1748, elem1419) in enumerate(unwrapped1418)
                    i1420 = i1748 - 1
                    if (i1420 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1419))
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
    flat1425 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1425)
        write(pp, flat1425)
        return nothing
    else
        fields1424 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1424))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1432 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1432)
        write(pp, flat1432)
        return nothing
    else
        _dollar_dollar = msg
        fields1426 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.returns_delta,)
        unwrapped_fields1427 = fields1426
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1428 = unwrapped_fields1427[1]
        pretty_iceberg_locator(pp, field1428)
        newline(pp)
        field1429 = unwrapped_fields1427[2]
        pretty_iceberg_catalog_config(pp, field1429)
        newline(pp)
        field1430 = unwrapped_fields1427[3]
        pretty_gnf_columns(pp, field1430)
        newline(pp)
        field1431 = unwrapped_fields1427[4]
        pretty_boolean_value(pp, field1431)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1442 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1442)
        write(pp, flat1442)
        return nothing
    else
        _dollar_dollar = msg
        _t1749 = deconstruct_iceberg_locator_from_snapshot_optional(pp, _dollar_dollar)
        _t1750 = deconstruct_iceberg_locator_to_snapshot_optional(pp, _dollar_dollar)
        fields1433 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse, _t1749, _t1750,)
        unwrapped_fields1434 = fields1433
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1435 = unwrapped_fields1434[1]
        pretty_iceberg_locator_table_name(pp, field1435)
        newline(pp)
        field1436 = unwrapped_fields1434[2]
        pretty_iceberg_locator_namespace(pp, field1436)
        newline(pp)
        field1437 = unwrapped_fields1434[3]
        pretty_iceberg_locator_warehouse(pp, field1437)
        field1438 = unwrapped_fields1434[4]
        if !isnothing(field1438)
            newline(pp)
            opt_val1439 = field1438
            pretty_iceberg_from_snapshot(pp, opt_val1439)
        end
        field1440 = unwrapped_fields1434[5]
        if !isnothing(field1440)
            newline(pp)
            opt_val1441 = field1440
            pretty_iceberg_to_snapshot(pp, opt_val1441)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1444 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1444)
        write(pp, flat1444)
        return nothing
    else
        fields1443 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1443))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1448 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1448)
        write(pp, flat1448)
        return nothing
    else
        fields1445 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1445)
            newline(pp)
            for (i1751, elem1446) in enumerate(fields1445)
                i1447 = i1751 - 1
                if (i1447 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1446))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1450 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1450)
        write(pp, flat1450)
        return nothing
    else
        fields1449 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1449))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1452 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1452)
        write(pp, flat1452)
        return nothing
    else
        fields1451 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1451))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1454 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1454)
        write(pp, flat1454)
        return nothing
    else
        fields1453 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1453))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1462 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1462)
        write(pp, flat1462)
        return nothing
    else
        _dollar_dollar = msg
        _t1752 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1455 = (_dollar_dollar.catalog_uri, _t1752, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1456 = fields1455
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1457 = unwrapped_fields1456[1]
        pretty_iceberg_catalog_uri(pp, field1457)
        field1458 = unwrapped_fields1456[2]
        if !isnothing(field1458)
            newline(pp)
            opt_val1459 = field1458
            pretty_iceberg_catalog_config_scope(pp, opt_val1459)
        end
        newline(pp)
        field1460 = unwrapped_fields1456[3]
        pretty_iceberg_properties(pp, field1460)
        newline(pp)
        field1461 = unwrapped_fields1456[4]
        pretty_iceberg_auth_properties(pp, field1461)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1464 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1464)
        write(pp, flat1464)
        return nothing
    else
        fields1463 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1463))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1466 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1466)
        write(pp, flat1466)
        return nothing
    else
        fields1465 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1465))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1470 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1470)
        write(pp, flat1470)
        return nothing
    else
        fields1467 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1467)
            newline(pp)
            for (i1753, elem1468) in enumerate(fields1467)
                i1469 = i1753 - 1
                if (i1469 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1468)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1475 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1475)
        write(pp, flat1475)
        return nothing
    else
        _dollar_dollar = msg
        fields1471 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1472 = fields1471
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1473 = unwrapped_fields1472[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1473))
        newline(pp)
        field1474 = unwrapped_fields1472[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1474))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1479 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1479)
        write(pp, flat1479)
        return nothing
    else
        fields1476 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1476)
            newline(pp)
            for (i1754, elem1477) in enumerate(fields1476)
                i1478 = i1754 - 1
                if (i1478 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1477)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1484 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1484)
        write(pp, flat1484)
        return nothing
    else
        _dollar_dollar = msg
        _t1755 = mask_secret_value(pp, _dollar_dollar)
        fields1480 = (_dollar_dollar[1], _t1755,)
        unwrapped_fields1481 = fields1480
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1482 = unwrapped_fields1481[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1482))
        newline(pp)
        field1483 = unwrapped_fields1481[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1483))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1487 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1487)
        write(pp, flat1487)
        return nothing
    else
        _dollar_dollar = msg
        fields1485 = _dollar_dollar.fragment_id
        unwrapped_fields1486 = fields1485
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1486)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1492 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1492)
        write(pp, flat1492)
        return nothing
    else
        _dollar_dollar = msg
        fields1488 = _dollar_dollar.relations
        unwrapped_fields1489 = fields1488
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1489)
            newline(pp)
            for (i1756, elem1490) in enumerate(unwrapped_fields1489)
                i1491 = i1756 - 1
                if (i1491 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1490)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1497 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1497)
        write(pp, flat1497)
        return nothing
    else
        _dollar_dollar = msg
        fields1493 = _dollar_dollar.mappings
        unwrapped_fields1494 = fields1493
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1494)
            newline(pp)
            for (i1757, elem1495) in enumerate(unwrapped_fields1494)
                i1496 = i1757 - 1
                if (i1496 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1495)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1502 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1502)
        write(pp, flat1502)
        return nothing
    else
        _dollar_dollar = msg
        fields1498 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1499 = fields1498
        field1500 = unwrapped_fields1499[1]
        pretty_edb_path(pp, field1500)
        write(pp, " ")
        field1501 = unwrapped_fields1499[2]
        pretty_relation_id(pp, field1501)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1506 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1506)
        write(pp, flat1506)
        return nothing
    else
        fields1503 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1503)
            newline(pp)
            for (i1758, elem1504) in enumerate(fields1503)
                i1505 = i1758 - 1
                if (i1505 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1504)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1517 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1517)
        write(pp, flat1517)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1759 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1759 = nothing
        end
        deconstruct_result1515 = _t1759
        if !isnothing(deconstruct_result1515)
            unwrapped1516 = deconstruct_result1515
            pretty_demand(pp, unwrapped1516)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1760 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1760 = nothing
            end
            deconstruct_result1513 = _t1760
            if !isnothing(deconstruct_result1513)
                unwrapped1514 = deconstruct_result1513
                pretty_output(pp, unwrapped1514)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1761 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1761 = nothing
                end
                deconstruct_result1511 = _t1761
                if !isnothing(deconstruct_result1511)
                    unwrapped1512 = deconstruct_result1511
                    pretty_what_if(pp, unwrapped1512)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1762 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1762 = nothing
                    end
                    deconstruct_result1509 = _t1762
                    if !isnothing(deconstruct_result1509)
                        unwrapped1510 = deconstruct_result1509
                        pretty_abort(pp, unwrapped1510)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1763 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1763 = nothing
                        end
                        deconstruct_result1507 = _t1763
                        if !isnothing(deconstruct_result1507)
                            unwrapped1508 = deconstruct_result1507
                            pretty_export(pp, unwrapped1508)
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
    flat1520 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1520)
        write(pp, flat1520)
        return nothing
    else
        _dollar_dollar = msg
        fields1518 = _dollar_dollar.relation_id
        unwrapped_fields1519 = fields1518
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1519)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1525 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1525)
        write(pp, flat1525)
        return nothing
    else
        _dollar_dollar = msg
        fields1521 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1522 = fields1521
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1523 = unwrapped_fields1522[1]
        pretty_name(pp, field1523)
        newline(pp)
        field1524 = unwrapped_fields1522[2]
        pretty_relation_id(pp, field1524)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1530 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1530)
        write(pp, flat1530)
        return nothing
    else
        _dollar_dollar = msg
        fields1526 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1527 = fields1526
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1528 = unwrapped_fields1527[1]
        pretty_name(pp, field1528)
        newline(pp)
        field1529 = unwrapped_fields1527[2]
        pretty_epoch(pp, field1529)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1536 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1536)
        write(pp, flat1536)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1764 = _dollar_dollar.name
        else
            _t1764 = nothing
        end
        fields1531 = (_t1764, _dollar_dollar.relation_id,)
        unwrapped_fields1532 = fields1531
        write(pp, "(abort")
        indent_sexp!(pp)
        field1533 = unwrapped_fields1532[1]
        if !isnothing(field1533)
            newline(pp)
            opt_val1534 = field1533
            pretty_name(pp, opt_val1534)
        end
        newline(pp)
        field1535 = unwrapped_fields1532[2]
        pretty_relation_id(pp, field1535)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1541 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1541)
        write(pp, flat1541)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1765 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1765 = nothing
        end
        deconstruct_result1539 = _t1765
        if !isnothing(deconstruct_result1539)
            unwrapped1540 = deconstruct_result1539
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1540)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1766 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1766 = nothing
            end
            deconstruct_result1537 = _t1766
            if !isnothing(deconstruct_result1537)
                unwrapped1538 = deconstruct_result1537
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1538)
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
    flat1552 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1552)
        write(pp, flat1552)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1767 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1767 = nothing
        end
        deconstruct_result1547 = _t1767
        if !isnothing(deconstruct_result1547)
            unwrapped1548 = deconstruct_result1547
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1549 = unwrapped1548[1]
            pretty_export_csv_path(pp, field1549)
            newline(pp)
            field1550 = unwrapped1548[2]
            pretty_export_csv_source(pp, field1550)
            newline(pp)
            field1551 = unwrapped1548[3]
            pretty_csv_config(pp, field1551)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1769 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1768 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1769,)
            else
                _t1768 = nothing
            end
            deconstruct_result1542 = _t1768
            if !isnothing(deconstruct_result1542)
                unwrapped1543 = deconstruct_result1542
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1544 = unwrapped1543[1]
                pretty_export_csv_path(pp, field1544)
                newline(pp)
                field1545 = unwrapped1543[2]
                pretty_export_csv_columns_list(pp, field1545)
                newline(pp)
                field1546 = unwrapped1543[3]
                pretty_config_dict(pp, field1546)
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
    flat1554 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1554)
        write(pp, flat1554)
        return nothing
    else
        fields1553 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1553))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1561 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1561)
        write(pp, flat1561)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1770 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1770 = nothing
        end
        deconstruct_result1557 = _t1770
        if !isnothing(deconstruct_result1557)
            unwrapped1558 = deconstruct_result1557
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1558)
                newline(pp)
                for (i1771, elem1559) in enumerate(unwrapped1558)
                    i1560 = i1771 - 1
                    if (i1560 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1559)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1772 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1772 = nothing
            end
            deconstruct_result1555 = _t1772
            if !isnothing(deconstruct_result1555)
                unwrapped1556 = deconstruct_result1555
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1556)
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
    flat1566 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1566)
        write(pp, flat1566)
        return nothing
    else
        _dollar_dollar = msg
        fields1562 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1563 = fields1562
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1564 = unwrapped_fields1563[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1564))
        newline(pp)
        field1565 = unwrapped_fields1563[2]
        pretty_relation_id(pp, field1565)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1570 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1570)
        write(pp, flat1570)
        return nothing
    else
        fields1567 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1567)
            newline(pp)
            for (i1773, elem1568) in enumerate(fields1567)
                i1569 = i1773 - 1
                if (i1569 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1568)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1580 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1580)
        write(pp, flat1580)
        return nothing
    else
        _dollar_dollar = msg
        _t1774 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1571 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, _dollar_dollar.columns, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1774,)
        unwrapped_fields1572 = fields1571
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1573 = unwrapped_fields1572[1]
        pretty_iceberg_locator(pp, field1573)
        newline(pp)
        field1574 = unwrapped_fields1572[2]
        pretty_iceberg_catalog_config(pp, field1574)
        newline(pp)
        field1575 = unwrapped_fields1572[3]
        pretty_export_iceberg_table_def(pp, field1575)
        newline(pp)
        field1576 = unwrapped_fields1572[4]
        pretty_export_iceberg_columns(pp, field1576)
        newline(pp)
        field1577 = unwrapped_fields1572[5]
        pretty_iceberg_table_properties(pp, field1577)
        field1578 = unwrapped_fields1572[6]
        if !isnothing(field1578)
            newline(pp)
            opt_val1579 = field1578
            pretty_config_dict(pp, opt_val1579)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1582 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1582)
        write(pp, flat1582)
        return nothing
    else
        fields1581 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1581)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportGNFColumn})
    flat1586 = try_flat(pp, msg, pretty_export_iceberg_columns)
    if !isnothing(flat1586)
        write(pp, flat1586)
        return nothing
    else
        fields1583 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1583)
            newline(pp)
            for (i1775, elem1584) in enumerate(fields1583)
                i1585 = i1775 - 1
                if (i1585 > 0)
                    newline(pp)
                end
                pretty_export_gnf_column(pp, elem1584)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_gnf_column(pp::PrettyPrinter, msg::Proto.ExportGNFColumn)
    flat1591 = try_flat(pp, msg, pretty_export_gnf_column)
    if !isnothing(flat1591)
        write(pp, flat1591)
        return nothing
    else
        _dollar_dollar = msg
        fields1587 = (_dollar_dollar.name, _dollar_dollar.nullable,)
        unwrapped_fields1588 = fields1587
        write(pp, "(gnf_column")
        indent_sexp!(pp)
        newline(pp)
        field1589 = unwrapped_fields1588[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1589))
        newline(pp)
        field1590 = unwrapped_fields1588[2]
        pretty_boolean_value(pp, field1590)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1595 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1595)
        write(pp, flat1595)
        return nothing
    else
        fields1592 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1592)
            newline(pp)
            for (i1776, elem1593) in enumerate(fields1592)
                i1594 = i1776 - 1
                if (i1594 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1593)
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
    for (i1822, _rid) in enumerate(msg.ids)
        _idx = i1822 - 1
        newline(pp)
        write(pp, "(")
        _t1823 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1823)
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
    for (i1824, _elem) in enumerate(msg.keys)
        _idx = i1824 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1825, _elem) in enumerate(msg.values)
        _idx = i1825 - 1
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
    for (i1826, _elem) in enumerate(msg.columns)
        _idx = i1826 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.ExportGNFColumn}) = pretty_export_iceberg_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportGNFColumn) = pretty_export_gnf_column(pp, x)
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
