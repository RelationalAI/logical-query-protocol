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
    _t1633 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1633
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1634 = Proto.Value(value=OneOf(:int_value, v))
    return _t1634
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1635 = Proto.Value(value=OneOf(:float_value, v))
    return _t1635
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1636 = Proto.Value(value=OneOf(:string_value, v))
    return _t1636
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1637 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1637
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1638 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1638
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1639 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1639,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1640 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1640,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1641 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1641,))
            end
        end
    end
    _t1642 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1642,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1643 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1643,))
    _t1644 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1644,))
    if msg.new_line != ""
        _t1645 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1645,))
    end
    _t1646 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1646,))
    _t1647 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1647,))
    _t1648 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1648,))
    if msg.comment != ""
        _t1649 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1649,))
    end
    for missing_string in msg.missing_strings
        _t1650 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1650,))
    end
    _t1651 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1651,))
    _t1652 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1652,))
    _t1653 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1653,))
    if msg.partition_size_mb != 0
        _t1654 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1654,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1655 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1655,))
    _t1656 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1656,))
    _t1657 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1657,))
    _t1658 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1658,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1659 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1659,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1660 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1660,))
        end
    end
    _t1661 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1661,))
    _t1662 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1662,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1663 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1663,))
    end
    if !isnothing(msg.compression)
        _t1664 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1664,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1665 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1665,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1666 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1666,))
    end
    if !isnothing(msg.syntax_delim)
        _t1667 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1667,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1668 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1668,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1669 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1669,))
    end
    return sort(result)
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1670 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1670,))
    end
    if msg.target_file_size_bytes != 0
        _t1671 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1671,))
    end
    if msg.compression != ""
        _t1672 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1672,))
    end
    if length(result) == 0
        return nothing
    else
        _t1673 = nothing
    end
    return sort(result)
end

function deconstruct_iceberg_catalog_properties_optional(pp::PrettyPrinter, msg::Proto.IcebergCatalogProperties)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.token != ""
        _t1674 = _make_value_string(pp, msg.token)
        push!(result, ("token", _t1674,))
    end
    if msg.credential != ""
        _t1675 = _make_value_string(pp, msg.credential)
        push!(result, ("credential", _t1675,))
    end
    if length(result) == 0
        return nothing
    else
        _t1676 = nothing
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
        _t1677 = nothing
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
    flat739 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat739)
        write(pp, flat739)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1460 = _dollar_dollar.configure
        else
            _t1460 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1461 = _dollar_dollar.sync
        else
            _t1461 = nothing
        end
        fields730 = (_t1460, _t1461, _dollar_dollar.epochs,)
        unwrapped_fields731 = fields730
        write(pp, "(transaction")
        indent_sexp!(pp)
        field732 = unwrapped_fields731[1]
        if !isnothing(field732)
            newline(pp)
            opt_val733 = field732
            pretty_configure(pp, opt_val733)
        end
        field734 = unwrapped_fields731[2]
        if !isnothing(field734)
            newline(pp)
            opt_val735 = field734
            pretty_sync(pp, opt_val735)
        end
        field736 = unwrapped_fields731[3]
        if !isempty(field736)
            newline(pp)
            for (i1462, elem737) in enumerate(field736)
                i738 = i1462 - 1
                if (i738 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem737)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat742 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat742)
        write(pp, flat742)
        return nothing
    else
        _dollar_dollar = msg
        _t1463 = deconstruct_configure(pp, _dollar_dollar)
        fields740 = _t1463
        unwrapped_fields741 = fields740
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields741)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat746 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat746)
        write(pp, flat746)
        return nothing
    else
        fields743 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields743)
            newline(pp)
            for (i1464, elem744) in enumerate(fields743)
                i745 = i1464 - 1
                if (i745 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem744)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat751 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat751)
        write(pp, flat751)
        return nothing
    else
        _dollar_dollar = msg
        fields747 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields748 = fields747
        write(pp, ":")
        field749 = unwrapped_fields748[1]
        write(pp, field749)
        write(pp, " ")
        field750 = unwrapped_fields748[2]
        pretty_raw_value(pp, field750)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat777 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat777)
        write(pp, flat777)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1465 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1465 = nothing
        end
        deconstruct_result775 = _t1465
        if !isnothing(deconstruct_result775)
            unwrapped776 = deconstruct_result775
            pretty_raw_date(pp, unwrapped776)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1466 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1466 = nothing
            end
            deconstruct_result773 = _t1466
            if !isnothing(deconstruct_result773)
                unwrapped774 = deconstruct_result773
                pretty_raw_datetime(pp, unwrapped774)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1467 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1467 = nothing
                end
                deconstruct_result771 = _t1467
                if !isnothing(deconstruct_result771)
                    unwrapped772 = deconstruct_result771
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped772))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1468 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1468 = nothing
                    end
                    deconstruct_result769 = _t1468
                    if !isnothing(deconstruct_result769)
                        unwrapped770 = deconstruct_result769
                        write(pp, (string(Int64(unwrapped770)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1469 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1469 = nothing
                        end
                        deconstruct_result767 = _t1469
                        if !isnothing(deconstruct_result767)
                            unwrapped768 = deconstruct_result767
                            write(pp, string(unwrapped768))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1470 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1470 = nothing
                            end
                            deconstruct_result765 = _t1470
                            if !isnothing(deconstruct_result765)
                                unwrapped766 = deconstruct_result765
                                write(pp, format_float32_literal(unwrapped766))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1471 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1471 = nothing
                                end
                                deconstruct_result763 = _t1471
                                if !isnothing(deconstruct_result763)
                                    unwrapped764 = deconstruct_result763
                                    write(pp, lowercase(string(unwrapped764)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1472 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1472 = nothing
                                    end
                                    deconstruct_result761 = _t1472
                                    if !isnothing(deconstruct_result761)
                                        unwrapped762 = deconstruct_result761
                                        write(pp, (string(Int64(unwrapped762)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1473 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1473 = nothing
                                        end
                                        deconstruct_result759 = _t1473
                                        if !isnothing(deconstruct_result759)
                                            unwrapped760 = deconstruct_result759
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped760))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1474 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1474 = nothing
                                            end
                                            deconstruct_result757 = _t1474
                                            if !isnothing(deconstruct_result757)
                                                unwrapped758 = deconstruct_result757
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped758))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1475 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1475 = nothing
                                                end
                                                deconstruct_result755 = _t1475
                                                if !isnothing(deconstruct_result755)
                                                    unwrapped756 = deconstruct_result755
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped756))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1476 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1476 = nothing
                                                    end
                                                    deconstruct_result753 = _t1476
                                                    if !isnothing(deconstruct_result753)
                                                        unwrapped754 = deconstruct_result753
                                                        pretty_boolean_value(pp, unwrapped754)
                                                    else
                                                        fields752 = msg
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
    flat783 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat783)
        write(pp, flat783)
        return nothing
    else
        _dollar_dollar = msg
        fields778 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields779 = fields778
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field780 = unwrapped_fields779[1]
        write(pp, string(field780))
        newline(pp)
        field781 = unwrapped_fields779[2]
        write(pp, string(field781))
        newline(pp)
        field782 = unwrapped_fields779[3]
        write(pp, string(field782))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat794 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat794)
        write(pp, flat794)
        return nothing
    else
        _dollar_dollar = msg
        fields784 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields785 = fields784
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field786 = unwrapped_fields785[1]
        write(pp, string(field786))
        newline(pp)
        field787 = unwrapped_fields785[2]
        write(pp, string(field787))
        newline(pp)
        field788 = unwrapped_fields785[3]
        write(pp, string(field788))
        newline(pp)
        field789 = unwrapped_fields785[4]
        write(pp, string(field789))
        newline(pp)
        field790 = unwrapped_fields785[5]
        write(pp, string(field790))
        newline(pp)
        field791 = unwrapped_fields785[6]
        write(pp, string(field791))
        field792 = unwrapped_fields785[7]
        if !isnothing(field792)
            newline(pp)
            opt_val793 = field792
            write(pp, string(opt_val793))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1477 = ()
    else
        _t1477 = nothing
    end
    deconstruct_result797 = _t1477
    if !isnothing(deconstruct_result797)
        unwrapped798 = deconstruct_result797
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1478 = ()
        else
            _t1478 = nothing
        end
        deconstruct_result795 = _t1478
        if !isnothing(deconstruct_result795)
            unwrapped796 = deconstruct_result795
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat803 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat803)
        write(pp, flat803)
        return nothing
    else
        _dollar_dollar = msg
        fields799 = _dollar_dollar.fragments
        unwrapped_fields800 = fields799
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields800)
            newline(pp)
            for (i1479, elem801) in enumerate(unwrapped_fields800)
                i802 = i1479 - 1
                if (i802 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem801)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat806 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat806)
        write(pp, flat806)
        return nothing
    else
        _dollar_dollar = msg
        fields804 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields805 = fields804
        write(pp, ":")
        write(pp, unwrapped_fields805)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat813 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat813)
        write(pp, flat813)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1480 = _dollar_dollar.writes
        else
            _t1480 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1481 = _dollar_dollar.reads
        else
            _t1481 = nothing
        end
        fields807 = (_t1480, _t1481,)
        unwrapped_fields808 = fields807
        write(pp, "(epoch")
        indent_sexp!(pp)
        field809 = unwrapped_fields808[1]
        if !isnothing(field809)
            newline(pp)
            opt_val810 = field809
            pretty_epoch_writes(pp, opt_val810)
        end
        field811 = unwrapped_fields808[2]
        if !isnothing(field811)
            newline(pp)
            opt_val812 = field811
            pretty_epoch_reads(pp, opt_val812)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat817 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat817)
        write(pp, flat817)
        return nothing
    else
        fields814 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields814)
            newline(pp)
            for (i1482, elem815) in enumerate(fields814)
                i816 = i1482 - 1
                if (i816 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem815)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat826 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat826)
        write(pp, flat826)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1483 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1483 = nothing
        end
        deconstruct_result824 = _t1483
        if !isnothing(deconstruct_result824)
            unwrapped825 = deconstruct_result824
            pretty_define(pp, unwrapped825)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1484 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1484 = nothing
            end
            deconstruct_result822 = _t1484
            if !isnothing(deconstruct_result822)
                unwrapped823 = deconstruct_result822
                pretty_undefine(pp, unwrapped823)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1485 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1485 = nothing
                end
                deconstruct_result820 = _t1485
                if !isnothing(deconstruct_result820)
                    unwrapped821 = deconstruct_result820
                    pretty_context(pp, unwrapped821)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1486 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1486 = nothing
                    end
                    deconstruct_result818 = _t1486
                    if !isnothing(deconstruct_result818)
                        unwrapped819 = deconstruct_result818
                        pretty_snapshot(pp, unwrapped819)
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
    flat829 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat829)
        write(pp, flat829)
        return nothing
    else
        _dollar_dollar = msg
        fields827 = _dollar_dollar.fragment
        unwrapped_fields828 = fields827
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields828)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat836 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat836)
        write(pp, flat836)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields830 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields831 = fields830
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field832 = unwrapped_fields831[1]
        pretty_new_fragment_id(pp, field832)
        field833 = unwrapped_fields831[2]
        if !isempty(field833)
            newline(pp)
            for (i1487, elem834) in enumerate(field833)
                i835 = i1487 - 1
                if (i835 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem834)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat838 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat838)
        write(pp, flat838)
        return nothing
    else
        fields837 = msg
        pretty_fragment_id(pp, fields837)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat847 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat847)
        write(pp, flat847)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1488 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1488 = nothing
        end
        deconstruct_result845 = _t1488
        if !isnothing(deconstruct_result845)
            unwrapped846 = deconstruct_result845
            pretty_def(pp, unwrapped846)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1489 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1489 = nothing
            end
            deconstruct_result843 = _t1489
            if !isnothing(deconstruct_result843)
                unwrapped844 = deconstruct_result843
                pretty_algorithm(pp, unwrapped844)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1490 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1490 = nothing
                end
                deconstruct_result841 = _t1490
                if !isnothing(deconstruct_result841)
                    unwrapped842 = deconstruct_result841
                    pretty_constraint(pp, unwrapped842)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1491 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1491 = nothing
                    end
                    deconstruct_result839 = _t1491
                    if !isnothing(deconstruct_result839)
                        unwrapped840 = deconstruct_result839
                        pretty_data(pp, unwrapped840)
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
    flat854 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat854)
        write(pp, flat854)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1492 = _dollar_dollar.attrs
        else
            _t1492 = nothing
        end
        fields848 = (_dollar_dollar.name, _dollar_dollar.body, _t1492,)
        unwrapped_fields849 = fields848
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field850 = unwrapped_fields849[1]
        pretty_relation_id(pp, field850)
        newline(pp)
        field851 = unwrapped_fields849[2]
        pretty_abstraction(pp, field851)
        field852 = unwrapped_fields849[3]
        if !isnothing(field852)
            newline(pp)
            opt_val853 = field852
            pretty_attrs(pp, opt_val853)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat859 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat859)
        write(pp, flat859)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1494 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1493 = _t1494
        else
            _t1493 = nothing
        end
        deconstruct_result857 = _t1493
        if !isnothing(deconstruct_result857)
            unwrapped858 = deconstruct_result857
            write(pp, ":")
            write(pp, unwrapped858)
        else
            _dollar_dollar = msg
            _t1495 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result855 = _t1495
            if !isnothing(deconstruct_result855)
                unwrapped856 = deconstruct_result855
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped856))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat864 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat864)
        write(pp, flat864)
        return nothing
    else
        _dollar_dollar = msg
        _t1496 = deconstruct_bindings(pp, _dollar_dollar)
        fields860 = (_t1496, _dollar_dollar.value,)
        unwrapped_fields861 = fields860
        write(pp, "(")
        indent!(pp)
        field862 = unwrapped_fields861[1]
        pretty_bindings(pp, field862)
        newline(pp)
        field863 = unwrapped_fields861[2]
        pretty_formula(pp, field863)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat872 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat872)
        write(pp, flat872)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1497 = _dollar_dollar[2]
        else
            _t1497 = nothing
        end
        fields865 = (_dollar_dollar[1], _t1497,)
        unwrapped_fields866 = fields865
        write(pp, "[")
        indent!(pp)
        field867 = unwrapped_fields866[1]
        for (i1498, elem868) in enumerate(field867)
            i869 = i1498 - 1
            if (i869 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem868)
        end
        field870 = unwrapped_fields866[2]
        if !isnothing(field870)
            newline(pp)
            opt_val871 = field870
            pretty_value_bindings(pp, opt_val871)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat877 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat877)
        write(pp, flat877)
        return nothing
    else
        _dollar_dollar = msg
        fields873 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields874 = fields873
        field875 = unwrapped_fields874[1]
        write(pp, field875)
        write(pp, "::")
        field876 = unwrapped_fields874[2]
        pretty_type(pp, field876)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat906 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1499 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1499 = nothing
        end
        deconstruct_result904 = _t1499
        if !isnothing(deconstruct_result904)
            unwrapped905 = deconstruct_result904
            pretty_unspecified_type(pp, unwrapped905)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1500 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1500 = nothing
            end
            deconstruct_result902 = _t1500
            if !isnothing(deconstruct_result902)
                unwrapped903 = deconstruct_result902
                pretty_string_type(pp, unwrapped903)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1501 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1501 = nothing
                end
                deconstruct_result900 = _t1501
                if !isnothing(deconstruct_result900)
                    unwrapped901 = deconstruct_result900
                    pretty_int_type(pp, unwrapped901)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1502 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1502 = nothing
                    end
                    deconstruct_result898 = _t1502
                    if !isnothing(deconstruct_result898)
                        unwrapped899 = deconstruct_result898
                        pretty_float_type(pp, unwrapped899)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1503 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1503 = nothing
                        end
                        deconstruct_result896 = _t1503
                        if !isnothing(deconstruct_result896)
                            unwrapped897 = deconstruct_result896
                            pretty_uint128_type(pp, unwrapped897)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1504 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1504 = nothing
                            end
                            deconstruct_result894 = _t1504
                            if !isnothing(deconstruct_result894)
                                unwrapped895 = deconstruct_result894
                                pretty_int128_type(pp, unwrapped895)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1505 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1505 = nothing
                                end
                                deconstruct_result892 = _t1505
                                if !isnothing(deconstruct_result892)
                                    unwrapped893 = deconstruct_result892
                                    pretty_date_type(pp, unwrapped893)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1506 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1506 = nothing
                                    end
                                    deconstruct_result890 = _t1506
                                    if !isnothing(deconstruct_result890)
                                        unwrapped891 = deconstruct_result890
                                        pretty_datetime_type(pp, unwrapped891)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1507 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1507 = nothing
                                        end
                                        deconstruct_result888 = _t1507
                                        if !isnothing(deconstruct_result888)
                                            unwrapped889 = deconstruct_result888
                                            pretty_missing_type(pp, unwrapped889)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1508 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1508 = nothing
                                            end
                                            deconstruct_result886 = _t1508
                                            if !isnothing(deconstruct_result886)
                                                unwrapped887 = deconstruct_result886
                                                pretty_decimal_type(pp, unwrapped887)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1509 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1509 = nothing
                                                end
                                                deconstruct_result884 = _t1509
                                                if !isnothing(deconstruct_result884)
                                                    unwrapped885 = deconstruct_result884
                                                    pretty_boolean_type(pp, unwrapped885)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1510 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1510 = nothing
                                                    end
                                                    deconstruct_result882 = _t1510
                                                    if !isnothing(deconstruct_result882)
                                                        unwrapped883 = deconstruct_result882
                                                        pretty_int32_type(pp, unwrapped883)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1511 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1511 = nothing
                                                        end
                                                        deconstruct_result880 = _t1511
                                                        if !isnothing(deconstruct_result880)
                                                            unwrapped881 = deconstruct_result880
                                                            pretty_float32_type(pp, unwrapped881)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1512 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1512 = nothing
                                                            end
                                                            deconstruct_result878 = _t1512
                                                            if !isnothing(deconstruct_result878)
                                                                unwrapped879 = deconstruct_result878
                                                                pretty_uint32_type(pp, unwrapped879)
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
    fields907 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields908 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields909 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields910 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields911 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields912 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields913 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields914 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields915 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat920 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat920)
        write(pp, flat920)
        return nothing
    else
        _dollar_dollar = msg
        fields916 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields917 = fields916
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field918 = unwrapped_fields917[1]
        write(pp, string(field918))
        newline(pp)
        field919 = unwrapped_fields917[2]
        write(pp, string(field919))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields921 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields922 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields923 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields924 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat928 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat928)
        write(pp, flat928)
        return nothing
    else
        fields925 = msg
        write(pp, "|")
        if !isempty(fields925)
            write(pp, " ")
            for (i1513, elem926) in enumerate(fields925)
                i927 = i1513 - 1
                if (i927 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem926)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat955 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat955)
        write(pp, flat955)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1514 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1514 = nothing
        end
        deconstruct_result953 = _t1514
        if !isnothing(deconstruct_result953)
            unwrapped954 = deconstruct_result953
            pretty_true(pp, unwrapped954)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1515 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1515 = nothing
            end
            deconstruct_result951 = _t1515
            if !isnothing(deconstruct_result951)
                unwrapped952 = deconstruct_result951
                pretty_false(pp, unwrapped952)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1516 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1516 = nothing
                end
                deconstruct_result949 = _t1516
                if !isnothing(deconstruct_result949)
                    unwrapped950 = deconstruct_result949
                    pretty_exists(pp, unwrapped950)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1517 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1517 = nothing
                    end
                    deconstruct_result947 = _t1517
                    if !isnothing(deconstruct_result947)
                        unwrapped948 = deconstruct_result947
                        pretty_reduce(pp, unwrapped948)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1518 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1518 = nothing
                        end
                        deconstruct_result945 = _t1518
                        if !isnothing(deconstruct_result945)
                            unwrapped946 = deconstruct_result945
                            pretty_conjunction(pp, unwrapped946)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1519 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1519 = nothing
                            end
                            deconstruct_result943 = _t1519
                            if !isnothing(deconstruct_result943)
                                unwrapped944 = deconstruct_result943
                                pretty_disjunction(pp, unwrapped944)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1520 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1520 = nothing
                                end
                                deconstruct_result941 = _t1520
                                if !isnothing(deconstruct_result941)
                                    unwrapped942 = deconstruct_result941
                                    pretty_not(pp, unwrapped942)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1521 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1521 = nothing
                                    end
                                    deconstruct_result939 = _t1521
                                    if !isnothing(deconstruct_result939)
                                        unwrapped940 = deconstruct_result939
                                        pretty_ffi(pp, unwrapped940)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1522 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1522 = nothing
                                        end
                                        deconstruct_result937 = _t1522
                                        if !isnothing(deconstruct_result937)
                                            unwrapped938 = deconstruct_result937
                                            pretty_atom(pp, unwrapped938)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1523 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1523 = nothing
                                            end
                                            deconstruct_result935 = _t1523
                                            if !isnothing(deconstruct_result935)
                                                unwrapped936 = deconstruct_result935
                                                pretty_pragma(pp, unwrapped936)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1524 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1524 = nothing
                                                end
                                                deconstruct_result933 = _t1524
                                                if !isnothing(deconstruct_result933)
                                                    unwrapped934 = deconstruct_result933
                                                    pretty_primitive(pp, unwrapped934)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1525 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1525 = nothing
                                                    end
                                                    deconstruct_result931 = _t1525
                                                    if !isnothing(deconstruct_result931)
                                                        unwrapped932 = deconstruct_result931
                                                        pretty_rel_atom(pp, unwrapped932)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1526 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1526 = nothing
                                                        end
                                                        deconstruct_result929 = _t1526
                                                        if !isnothing(deconstruct_result929)
                                                            unwrapped930 = deconstruct_result929
                                                            pretty_cast(pp, unwrapped930)
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
    fields956 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields957 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat962 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat962)
        write(pp, flat962)
        return nothing
    else
        _dollar_dollar = msg
        _t1527 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields958 = (_t1527, _dollar_dollar.body.value,)
        unwrapped_fields959 = fields958
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field960 = unwrapped_fields959[1]
        pretty_bindings(pp, field960)
        newline(pp)
        field961 = unwrapped_fields959[2]
        pretty_formula(pp, field961)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat968 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat968)
        write(pp, flat968)
        return nothing
    else
        _dollar_dollar = msg
        fields963 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields964 = fields963
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field965 = unwrapped_fields964[1]
        pretty_abstraction(pp, field965)
        newline(pp)
        field966 = unwrapped_fields964[2]
        pretty_abstraction(pp, field966)
        newline(pp)
        field967 = unwrapped_fields964[3]
        pretty_terms(pp, field967)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat972 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat972)
        write(pp, flat972)
        return nothing
    else
        fields969 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields969)
            newline(pp)
            for (i1528, elem970) in enumerate(fields969)
                i971 = i1528 - 1
                if (i971 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem970)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat977 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat977)
        write(pp, flat977)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1529 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1529 = nothing
        end
        deconstruct_result975 = _t1529
        if !isnothing(deconstruct_result975)
            unwrapped976 = deconstruct_result975
            pretty_var(pp, unwrapped976)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1530 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1530 = nothing
            end
            deconstruct_result973 = _t1530
            if !isnothing(deconstruct_result973)
                unwrapped974 = deconstruct_result973
                pretty_value(pp, unwrapped974)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat980 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat980)
        write(pp, flat980)
        return nothing
    else
        _dollar_dollar = msg
        fields978 = _dollar_dollar.name
        unwrapped_fields979 = fields978
        write(pp, unwrapped_fields979)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1006 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1006)
        write(pp, flat1006)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1531 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1531 = nothing
        end
        deconstruct_result1004 = _t1531
        if !isnothing(deconstruct_result1004)
            unwrapped1005 = deconstruct_result1004
            pretty_date(pp, unwrapped1005)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1532 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1532 = nothing
            end
            deconstruct_result1002 = _t1532
            if !isnothing(deconstruct_result1002)
                unwrapped1003 = deconstruct_result1002
                pretty_datetime(pp, unwrapped1003)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1533 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1533 = nothing
                end
                deconstruct_result1000 = _t1533
                if !isnothing(deconstruct_result1000)
                    unwrapped1001 = deconstruct_result1000
                    write(pp, format_string(pp, unwrapped1001))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1534 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1534 = nothing
                    end
                    deconstruct_result998 = _t1534
                    if !isnothing(deconstruct_result998)
                        unwrapped999 = deconstruct_result998
                        write(pp, format_int32(pp, unwrapped999))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1535 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1535 = nothing
                        end
                        deconstruct_result996 = _t1535
                        if !isnothing(deconstruct_result996)
                            unwrapped997 = deconstruct_result996
                            write(pp, format_int(pp, unwrapped997))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1536 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1536 = nothing
                            end
                            deconstruct_result994 = _t1536
                            if !isnothing(deconstruct_result994)
                                unwrapped995 = deconstruct_result994
                                write(pp, format_float32(pp, unwrapped995))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1537 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1537 = nothing
                                end
                                deconstruct_result992 = _t1537
                                if !isnothing(deconstruct_result992)
                                    unwrapped993 = deconstruct_result992
                                    write(pp, format_float(pp, unwrapped993))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1538 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1538 = nothing
                                    end
                                    deconstruct_result990 = _t1538
                                    if !isnothing(deconstruct_result990)
                                        unwrapped991 = deconstruct_result990
                                        write(pp, format_uint32(pp, unwrapped991))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1539 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1539 = nothing
                                        end
                                        deconstruct_result988 = _t1539
                                        if !isnothing(deconstruct_result988)
                                            unwrapped989 = deconstruct_result988
                                            write(pp, format_uint128(pp, unwrapped989))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1540 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1540 = nothing
                                            end
                                            deconstruct_result986 = _t1540
                                            if !isnothing(deconstruct_result986)
                                                unwrapped987 = deconstruct_result986
                                                write(pp, format_int128(pp, unwrapped987))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1541 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1541 = nothing
                                                end
                                                deconstruct_result984 = _t1541
                                                if !isnothing(deconstruct_result984)
                                                    unwrapped985 = deconstruct_result984
                                                    write(pp, format_decimal(pp, unwrapped985))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1542 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1542 = nothing
                                                    end
                                                    deconstruct_result982 = _t1542
                                                    if !isnothing(deconstruct_result982)
                                                        unwrapped983 = deconstruct_result982
                                                        pretty_boolean_value(pp, unwrapped983)
                                                    else
                                                        fields981 = msg
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
    flat1012 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1012)
        write(pp, flat1012)
        return nothing
    else
        _dollar_dollar = msg
        fields1007 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1008 = fields1007
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1009 = unwrapped_fields1008[1]
        write(pp, format_int(pp, field1009))
        newline(pp)
        field1010 = unwrapped_fields1008[2]
        write(pp, format_int(pp, field1010))
        newline(pp)
        field1011 = unwrapped_fields1008[3]
        write(pp, format_int(pp, field1011))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1023 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1023)
        write(pp, flat1023)
        return nothing
    else
        _dollar_dollar = msg
        fields1013 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1014 = fields1013
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1015 = unwrapped_fields1014[1]
        write(pp, format_int(pp, field1015))
        newline(pp)
        field1016 = unwrapped_fields1014[2]
        write(pp, format_int(pp, field1016))
        newline(pp)
        field1017 = unwrapped_fields1014[3]
        write(pp, format_int(pp, field1017))
        newline(pp)
        field1018 = unwrapped_fields1014[4]
        write(pp, format_int(pp, field1018))
        newline(pp)
        field1019 = unwrapped_fields1014[5]
        write(pp, format_int(pp, field1019))
        newline(pp)
        field1020 = unwrapped_fields1014[6]
        write(pp, format_int(pp, field1020))
        field1021 = unwrapped_fields1014[7]
        if !isnothing(field1021)
            newline(pp)
            opt_val1022 = field1021
            write(pp, format_int(pp, opt_val1022))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1028 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1028)
        write(pp, flat1028)
        return nothing
    else
        _dollar_dollar = msg
        fields1024 = _dollar_dollar.args
        unwrapped_fields1025 = fields1024
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1025)
            newline(pp)
            for (i1543, elem1026) in enumerate(unwrapped_fields1025)
                i1027 = i1543 - 1
                if (i1027 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1026)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1033 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1033)
        write(pp, flat1033)
        return nothing
    else
        _dollar_dollar = msg
        fields1029 = _dollar_dollar.args
        unwrapped_fields1030 = fields1029
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1030)
            newline(pp)
            for (i1544, elem1031) in enumerate(unwrapped_fields1030)
                i1032 = i1544 - 1
                if (i1032 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1031)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1036 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1036)
        write(pp, flat1036)
        return nothing
    else
        _dollar_dollar = msg
        fields1034 = _dollar_dollar.arg
        unwrapped_fields1035 = fields1034
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1035)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1042 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1042)
        write(pp, flat1042)
        return nothing
    else
        _dollar_dollar = msg
        fields1037 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1038 = fields1037
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1039 = unwrapped_fields1038[1]
        pretty_name(pp, field1039)
        newline(pp)
        field1040 = unwrapped_fields1038[2]
        pretty_ffi_args(pp, field1040)
        newline(pp)
        field1041 = unwrapped_fields1038[3]
        pretty_terms(pp, field1041)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1044 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1044)
        write(pp, flat1044)
        return nothing
    else
        fields1043 = msg
        write(pp, ":")
        write(pp, fields1043)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1048 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1048)
        write(pp, flat1048)
        return nothing
    else
        fields1045 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1045)
            newline(pp)
            for (i1545, elem1046) in enumerate(fields1045)
                i1047 = i1545 - 1
                if (i1047 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1046)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1055 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1055)
        write(pp, flat1055)
        return nothing
    else
        _dollar_dollar = msg
        fields1049 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1050 = fields1049
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1051 = unwrapped_fields1050[1]
        pretty_relation_id(pp, field1051)
        field1052 = unwrapped_fields1050[2]
        if !isempty(field1052)
            newline(pp)
            for (i1546, elem1053) in enumerate(field1052)
                i1054 = i1546 - 1
                if (i1054 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1053)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1062 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1062)
        write(pp, flat1062)
        return nothing
    else
        _dollar_dollar = msg
        fields1056 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1057 = fields1056
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1058 = unwrapped_fields1057[1]
        pretty_name(pp, field1058)
        field1059 = unwrapped_fields1057[2]
        if !isempty(field1059)
            newline(pp)
            for (i1547, elem1060) in enumerate(field1059)
                i1061 = i1547 - 1
                if (i1061 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1060)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1078 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1078)
        write(pp, flat1078)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1548 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1548 = nothing
        end
        guard_result1077 = _t1548
        if !isnothing(guard_result1077)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1549 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1549 = nothing
            end
            guard_result1076 = _t1549
            if !isnothing(guard_result1076)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1550 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1550 = nothing
                end
                guard_result1075 = _t1550
                if !isnothing(guard_result1075)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1551 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1551 = nothing
                    end
                    guard_result1074 = _t1551
                    if !isnothing(guard_result1074)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1552 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1552 = nothing
                        end
                        guard_result1073 = _t1552
                        if !isnothing(guard_result1073)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1553 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1553 = nothing
                            end
                            guard_result1072 = _t1553
                            if !isnothing(guard_result1072)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1554 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1554 = nothing
                                end
                                guard_result1071 = _t1554
                                if !isnothing(guard_result1071)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1555 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1555 = nothing
                                    end
                                    guard_result1070 = _t1555
                                    if !isnothing(guard_result1070)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1556 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1556 = nothing
                                        end
                                        guard_result1069 = _t1556
                                        if !isnothing(guard_result1069)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1063 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1064 = fields1063
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1065 = unwrapped_fields1064[1]
                                            pretty_name(pp, field1065)
                                            field1066 = unwrapped_fields1064[2]
                                            if !isempty(field1066)
                                                newline(pp)
                                                for (i1557, elem1067) in enumerate(field1066)
                                                    i1068 = i1557 - 1
                                                    if (i1068 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1067)
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
    flat1083 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1083)
        write(pp, flat1083)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1558 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1558 = nothing
        end
        fields1079 = _t1558
        unwrapped_fields1080 = fields1079
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1081 = unwrapped_fields1080[1]
        pretty_term(pp, field1081)
        newline(pp)
        field1082 = unwrapped_fields1080[2]
        pretty_term(pp, field1082)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1088 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1088)
        write(pp, flat1088)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1559 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1559 = nothing
        end
        fields1084 = _t1559
        unwrapped_fields1085 = fields1084
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1086 = unwrapped_fields1085[1]
        pretty_term(pp, field1086)
        newline(pp)
        field1087 = unwrapped_fields1085[2]
        pretty_term(pp, field1087)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1093 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1093)
        write(pp, flat1093)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1560 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1560 = nothing
        end
        fields1089 = _t1560
        unwrapped_fields1090 = fields1089
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1091 = unwrapped_fields1090[1]
        pretty_term(pp, field1091)
        newline(pp)
        field1092 = unwrapped_fields1090[2]
        pretty_term(pp, field1092)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1098 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1098)
        write(pp, flat1098)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1561 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1561 = nothing
        end
        fields1094 = _t1561
        unwrapped_fields1095 = fields1094
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1096 = unwrapped_fields1095[1]
        pretty_term(pp, field1096)
        newline(pp)
        field1097 = unwrapped_fields1095[2]
        pretty_term(pp, field1097)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1103 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1103)
        write(pp, flat1103)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1562 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1562 = nothing
        end
        fields1099 = _t1562
        unwrapped_fields1100 = fields1099
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1101 = unwrapped_fields1100[1]
        pretty_term(pp, field1101)
        newline(pp)
        field1102 = unwrapped_fields1100[2]
        pretty_term(pp, field1102)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1109 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1109)
        write(pp, flat1109)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1563 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1563 = nothing
        end
        fields1104 = _t1563
        unwrapped_fields1105 = fields1104
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1106 = unwrapped_fields1105[1]
        pretty_term(pp, field1106)
        newline(pp)
        field1107 = unwrapped_fields1105[2]
        pretty_term(pp, field1107)
        newline(pp)
        field1108 = unwrapped_fields1105[3]
        pretty_term(pp, field1108)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1115 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1115)
        write(pp, flat1115)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1564 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1564 = nothing
        end
        fields1110 = _t1564
        unwrapped_fields1111 = fields1110
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1112 = unwrapped_fields1111[1]
        pretty_term(pp, field1112)
        newline(pp)
        field1113 = unwrapped_fields1111[2]
        pretty_term(pp, field1113)
        newline(pp)
        field1114 = unwrapped_fields1111[3]
        pretty_term(pp, field1114)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1121 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1121)
        write(pp, flat1121)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1565 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1565 = nothing
        end
        fields1116 = _t1565
        unwrapped_fields1117 = fields1116
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1118 = unwrapped_fields1117[1]
        pretty_term(pp, field1118)
        newline(pp)
        field1119 = unwrapped_fields1117[2]
        pretty_term(pp, field1119)
        newline(pp)
        field1120 = unwrapped_fields1117[3]
        pretty_term(pp, field1120)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1127 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1127)
        write(pp, flat1127)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1566 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1566 = nothing
        end
        fields1122 = _t1566
        unwrapped_fields1123 = fields1122
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1124 = unwrapped_fields1123[1]
        pretty_term(pp, field1124)
        newline(pp)
        field1125 = unwrapped_fields1123[2]
        pretty_term(pp, field1125)
        newline(pp)
        field1126 = unwrapped_fields1123[3]
        pretty_term(pp, field1126)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1132 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1132)
        write(pp, flat1132)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1567 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1567 = nothing
        end
        deconstruct_result1130 = _t1567
        if !isnothing(deconstruct_result1130)
            unwrapped1131 = deconstruct_result1130
            pretty_specialized_value(pp, unwrapped1131)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1568 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1568 = nothing
            end
            deconstruct_result1128 = _t1568
            if !isnothing(deconstruct_result1128)
                unwrapped1129 = deconstruct_result1128
                pretty_term(pp, unwrapped1129)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1134 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1134)
        write(pp, flat1134)
        return nothing
    else
        fields1133 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1133)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1141 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1141)
        write(pp, flat1141)
        return nothing
    else
        _dollar_dollar = msg
        fields1135 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1136 = fields1135
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1137 = unwrapped_fields1136[1]
        pretty_name(pp, field1137)
        field1138 = unwrapped_fields1136[2]
        if !isempty(field1138)
            newline(pp)
            for (i1569, elem1139) in enumerate(field1138)
                i1140 = i1569 - 1
                if (i1140 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1139)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1146 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1146)
        write(pp, flat1146)
        return nothing
    else
        _dollar_dollar = msg
        fields1142 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1143 = fields1142
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1144 = unwrapped_fields1143[1]
        pretty_term(pp, field1144)
        newline(pp)
        field1145 = unwrapped_fields1143[2]
        pretty_term(pp, field1145)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1150 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1150)
        write(pp, flat1150)
        return nothing
    else
        fields1147 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1147)
            newline(pp)
            for (i1570, elem1148) in enumerate(fields1147)
                i1149 = i1570 - 1
                if (i1149 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1148)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1157 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1157)
        write(pp, flat1157)
        return nothing
    else
        _dollar_dollar = msg
        fields1151 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1152 = fields1151
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1153 = unwrapped_fields1152[1]
        pretty_name(pp, field1153)
        field1154 = unwrapped_fields1152[2]
        if !isempty(field1154)
            newline(pp)
            for (i1571, elem1155) in enumerate(field1154)
                i1156 = i1571 - 1
                if (i1156 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1155)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1164 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1164)
        write(pp, flat1164)
        return nothing
    else
        _dollar_dollar = msg
        fields1158 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1159 = fields1158
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1160 = unwrapped_fields1159[1]
        if !isempty(field1160)
            newline(pp)
            for (i1572, elem1161) in enumerate(field1160)
                i1162 = i1572 - 1
                if (i1162 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1161)
            end
        end
        newline(pp)
        field1163 = unwrapped_fields1159[2]
        pretty_script(pp, field1163)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1169 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1169)
        write(pp, flat1169)
        return nothing
    else
        _dollar_dollar = msg
        fields1165 = _dollar_dollar.constructs
        unwrapped_fields1166 = fields1165
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1166)
            newline(pp)
            for (i1573, elem1167) in enumerate(unwrapped_fields1166)
                i1168 = i1573 - 1
                if (i1168 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1167)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1174 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1174)
        write(pp, flat1174)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1574 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1574 = nothing
        end
        deconstruct_result1172 = _t1574
        if !isnothing(deconstruct_result1172)
            unwrapped1173 = deconstruct_result1172
            pretty_loop(pp, unwrapped1173)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1575 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1575 = nothing
            end
            deconstruct_result1170 = _t1575
            if !isnothing(deconstruct_result1170)
                unwrapped1171 = deconstruct_result1170
                pretty_instruction(pp, unwrapped1171)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1179 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        _dollar_dollar = msg
        fields1175 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1176 = fields1175
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1177 = unwrapped_fields1176[1]
        pretty_init(pp, field1177)
        newline(pp)
        field1178 = unwrapped_fields1176[2]
        pretty_script(pp, field1178)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1183 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1183)
        write(pp, flat1183)
        return nothing
    else
        fields1180 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1180)
            newline(pp)
            for (i1576, elem1181) in enumerate(fields1180)
                i1182 = i1576 - 1
                if (i1182 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1181)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1194 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1194)
        write(pp, flat1194)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1577 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1577 = nothing
        end
        deconstruct_result1192 = _t1577
        if !isnothing(deconstruct_result1192)
            unwrapped1193 = deconstruct_result1192
            pretty_assign(pp, unwrapped1193)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1578 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1578 = nothing
            end
            deconstruct_result1190 = _t1578
            if !isnothing(deconstruct_result1190)
                unwrapped1191 = deconstruct_result1190
                pretty_upsert(pp, unwrapped1191)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1579 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1579 = nothing
                end
                deconstruct_result1188 = _t1579
                if !isnothing(deconstruct_result1188)
                    unwrapped1189 = deconstruct_result1188
                    pretty_break(pp, unwrapped1189)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1580 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1580 = nothing
                    end
                    deconstruct_result1186 = _t1580
                    if !isnothing(deconstruct_result1186)
                        unwrapped1187 = deconstruct_result1186
                        pretty_monoid_def(pp, unwrapped1187)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1581 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1581 = nothing
                        end
                        deconstruct_result1184 = _t1581
                        if !isnothing(deconstruct_result1184)
                            unwrapped1185 = deconstruct_result1184
                            pretty_monus_def(pp, unwrapped1185)
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
    flat1201 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1201)
        write(pp, flat1201)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1582 = _dollar_dollar.attrs
        else
            _t1582 = nothing
        end
        fields1195 = (_dollar_dollar.name, _dollar_dollar.body, _t1582,)
        unwrapped_fields1196 = fields1195
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1197 = unwrapped_fields1196[1]
        pretty_relation_id(pp, field1197)
        newline(pp)
        field1198 = unwrapped_fields1196[2]
        pretty_abstraction(pp, field1198)
        field1199 = unwrapped_fields1196[3]
        if !isnothing(field1199)
            newline(pp)
            opt_val1200 = field1199
            pretty_attrs(pp, opt_val1200)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1208 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1208)
        write(pp, flat1208)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1583 = _dollar_dollar.attrs
        else
            _t1583 = nothing
        end
        fields1202 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1583,)
        unwrapped_fields1203 = fields1202
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1204 = unwrapped_fields1203[1]
        pretty_relation_id(pp, field1204)
        newline(pp)
        field1205 = unwrapped_fields1203[2]
        pretty_abstraction_with_arity(pp, field1205)
        field1206 = unwrapped_fields1203[3]
        if !isnothing(field1206)
            newline(pp)
            opt_val1207 = field1206
            pretty_attrs(pp, opt_val1207)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1213 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1213)
        write(pp, flat1213)
        return nothing
    else
        _dollar_dollar = msg
        _t1584 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1209 = (_t1584, _dollar_dollar[1].value,)
        unwrapped_fields1210 = fields1209
        write(pp, "(")
        indent!(pp)
        field1211 = unwrapped_fields1210[1]
        pretty_bindings(pp, field1211)
        newline(pp)
        field1212 = unwrapped_fields1210[2]
        pretty_formula(pp, field1212)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1220 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1585 = _dollar_dollar.attrs
        else
            _t1585 = nothing
        end
        fields1214 = (_dollar_dollar.name, _dollar_dollar.body, _t1585,)
        unwrapped_fields1215 = fields1214
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1216 = unwrapped_fields1215[1]
        pretty_relation_id(pp, field1216)
        newline(pp)
        field1217 = unwrapped_fields1215[2]
        pretty_abstraction(pp, field1217)
        field1218 = unwrapped_fields1215[3]
        if !isnothing(field1218)
            newline(pp)
            opt_val1219 = field1218
            pretty_attrs(pp, opt_val1219)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1228 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1228)
        write(pp, flat1228)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1586 = _dollar_dollar.attrs
        else
            _t1586 = nothing
        end
        fields1221 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1586,)
        unwrapped_fields1222 = fields1221
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1223 = unwrapped_fields1222[1]
        pretty_monoid(pp, field1223)
        newline(pp)
        field1224 = unwrapped_fields1222[2]
        pretty_relation_id(pp, field1224)
        newline(pp)
        field1225 = unwrapped_fields1222[3]
        pretty_abstraction_with_arity(pp, field1225)
        field1226 = unwrapped_fields1222[4]
        if !isnothing(field1226)
            newline(pp)
            opt_val1227 = field1226
            pretty_attrs(pp, opt_val1227)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1237 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1237)
        write(pp, flat1237)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1587 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1587 = nothing
        end
        deconstruct_result1235 = _t1587
        if !isnothing(deconstruct_result1235)
            unwrapped1236 = deconstruct_result1235
            pretty_or_monoid(pp, unwrapped1236)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1588 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1588 = nothing
            end
            deconstruct_result1233 = _t1588
            if !isnothing(deconstruct_result1233)
                unwrapped1234 = deconstruct_result1233
                pretty_min_monoid(pp, unwrapped1234)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1589 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1589 = nothing
                end
                deconstruct_result1231 = _t1589
                if !isnothing(deconstruct_result1231)
                    unwrapped1232 = deconstruct_result1231
                    pretty_max_monoid(pp, unwrapped1232)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1590 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1590 = nothing
                    end
                    deconstruct_result1229 = _t1590
                    if !isnothing(deconstruct_result1229)
                        unwrapped1230 = deconstruct_result1229
                        pretty_sum_monoid(pp, unwrapped1230)
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
    fields1238 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1241 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1241)
        write(pp, flat1241)
        return nothing
    else
        _dollar_dollar = msg
        fields1239 = _dollar_dollar.var"#type"
        unwrapped_fields1240 = fields1239
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1240)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1244 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1244)
        write(pp, flat1244)
        return nothing
    else
        _dollar_dollar = msg
        fields1242 = _dollar_dollar.var"#type"
        unwrapped_fields1243 = fields1242
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1243)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1247 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1247)
        write(pp, flat1247)
        return nothing
    else
        _dollar_dollar = msg
        fields1245 = _dollar_dollar.var"#type"
        unwrapped_fields1246 = fields1245
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1246)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1255 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1255)
        write(pp, flat1255)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1591 = _dollar_dollar.attrs
        else
            _t1591 = nothing
        end
        fields1248 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1591,)
        unwrapped_fields1249 = fields1248
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1250 = unwrapped_fields1249[1]
        pretty_monoid(pp, field1250)
        newline(pp)
        field1251 = unwrapped_fields1249[2]
        pretty_relation_id(pp, field1251)
        newline(pp)
        field1252 = unwrapped_fields1249[3]
        pretty_abstraction_with_arity(pp, field1252)
        field1253 = unwrapped_fields1249[4]
        if !isnothing(field1253)
            newline(pp)
            opt_val1254 = field1253
            pretty_attrs(pp, opt_val1254)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1262 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1262)
        write(pp, flat1262)
        return nothing
    else
        _dollar_dollar = msg
        fields1256 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1257 = fields1256
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1258 = unwrapped_fields1257[1]
        pretty_relation_id(pp, field1258)
        newline(pp)
        field1259 = unwrapped_fields1257[2]
        pretty_abstraction(pp, field1259)
        newline(pp)
        field1260 = unwrapped_fields1257[3]
        pretty_functional_dependency_keys(pp, field1260)
        newline(pp)
        field1261 = unwrapped_fields1257[4]
        pretty_functional_dependency_values(pp, field1261)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1266 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1266)
        write(pp, flat1266)
        return nothing
    else
        fields1263 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1263)
            newline(pp)
            for (i1592, elem1264) in enumerate(fields1263)
                i1265 = i1592 - 1
                if (i1265 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1264)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1270 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1270)
        write(pp, flat1270)
        return nothing
    else
        fields1267 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1267)
            newline(pp)
            for (i1593, elem1268) in enumerate(fields1267)
                i1269 = i1593 - 1
                if (i1269 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1268)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1277 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1277)
        write(pp, flat1277)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1594 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1594 = nothing
        end
        deconstruct_result1275 = _t1594
        if !isnothing(deconstruct_result1275)
            unwrapped1276 = deconstruct_result1275
            pretty_edb(pp, unwrapped1276)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1595 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1595 = nothing
            end
            deconstruct_result1273 = _t1595
            if !isnothing(deconstruct_result1273)
                unwrapped1274 = deconstruct_result1273
                pretty_betree_relation(pp, unwrapped1274)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1596 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1596 = nothing
                end
                deconstruct_result1271 = _t1596
                if !isnothing(deconstruct_result1271)
                    unwrapped1272 = deconstruct_result1271
                    pretty_csv_data(pp, unwrapped1272)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_edb(pp::PrettyPrinter, msg::Proto.EDB)
    flat1283 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1283)
        write(pp, flat1283)
        return nothing
    else
        _dollar_dollar = msg
        fields1278 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1279 = fields1278
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1280 = unwrapped_fields1279[1]
        pretty_relation_id(pp, field1280)
        newline(pp)
        field1281 = unwrapped_fields1279[2]
        pretty_edb_path(pp, field1281)
        newline(pp)
        field1282 = unwrapped_fields1279[3]
        pretty_edb_types(pp, field1282)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1287 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1287)
        write(pp, flat1287)
        return nothing
    else
        fields1284 = msg
        write(pp, "[")
        indent!(pp)
        for (i1597, elem1285) in enumerate(fields1284)
            i1286 = i1597 - 1
            if (i1286 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1285))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1291 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1291)
        write(pp, flat1291)
        return nothing
    else
        fields1288 = msg
        write(pp, "[")
        indent!(pp)
        for (i1598, elem1289) in enumerate(fields1288)
            i1290 = i1598 - 1
            if (i1290 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1289)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1296 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1296)
        write(pp, flat1296)
        return nothing
    else
        _dollar_dollar = msg
        fields1292 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1293 = fields1292
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1294 = unwrapped_fields1293[1]
        pretty_relation_id(pp, field1294)
        newline(pp)
        field1295 = unwrapped_fields1293[2]
        pretty_betree_info(pp, field1295)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1302 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1302)
        write(pp, flat1302)
        return nothing
    else
        _dollar_dollar = msg
        _t1599 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1297 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1599,)
        unwrapped_fields1298 = fields1297
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1299 = unwrapped_fields1298[1]
        pretty_betree_info_key_types(pp, field1299)
        newline(pp)
        field1300 = unwrapped_fields1298[2]
        pretty_betree_info_value_types(pp, field1300)
        newline(pp)
        field1301 = unwrapped_fields1298[3]
        pretty_config_dict(pp, field1301)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1306 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1306)
        write(pp, flat1306)
        return nothing
    else
        fields1303 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1303)
            newline(pp)
            for (i1600, elem1304) in enumerate(fields1303)
                i1305 = i1600 - 1
                if (i1305 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1304)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1310 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1310)
        write(pp, flat1310)
        return nothing
    else
        fields1307 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1307)
            newline(pp)
            for (i1601, elem1308) in enumerate(fields1307)
                i1309 = i1601 - 1
                if (i1309 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1308)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1317 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1317)
        write(pp, flat1317)
        return nothing
    else
        _dollar_dollar = msg
        fields1311 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1312 = fields1311
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1313 = unwrapped_fields1312[1]
        pretty_csvlocator(pp, field1313)
        newline(pp)
        field1314 = unwrapped_fields1312[2]
        pretty_csv_config(pp, field1314)
        newline(pp)
        field1315 = unwrapped_fields1312[3]
        pretty_gnf_columns(pp, field1315)
        newline(pp)
        field1316 = unwrapped_fields1312[4]
        pretty_csv_asof(pp, field1316)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1324 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1324)
        write(pp, flat1324)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1602 = _dollar_dollar.paths
        else
            _t1602 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1603 = String(copy(_dollar_dollar.inline_data))
        else
            _t1603 = nothing
        end
        fields1318 = (_t1602, _t1603,)
        unwrapped_fields1319 = fields1318
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1320 = unwrapped_fields1319[1]
        if !isnothing(field1320)
            newline(pp)
            opt_val1321 = field1320
            pretty_csv_locator_paths(pp, opt_val1321)
        end
        field1322 = unwrapped_fields1319[2]
        if !isnothing(field1322)
            newline(pp)
            opt_val1323 = field1322
            pretty_csv_locator_inline_data(pp, opt_val1323)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1328 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1328)
        write(pp, flat1328)
        return nothing
    else
        fields1325 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1325)
            newline(pp)
            for (i1604, elem1326) in enumerate(fields1325)
                i1327 = i1604 - 1
                if (i1327 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1326))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1330 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1330)
        write(pp, flat1330)
        return nothing
    else
        fields1329 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1329))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1333 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1333)
        write(pp, flat1333)
        return nothing
    else
        _dollar_dollar = msg
        _t1605 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1331 = _t1605
        unwrapped_fields1332 = fields1331
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1332)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1337 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1337)
        write(pp, flat1337)
        return nothing
    else
        fields1334 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1334)
            newline(pp)
            for (i1606, elem1335) in enumerate(fields1334)
                i1336 = i1606 - 1
                if (i1336 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1335)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1346 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1346)
        write(pp, flat1346)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1607 = _dollar_dollar.target_id
        else
            _t1607 = nothing
        end
        fields1338 = (_dollar_dollar.column_path, _t1607, _dollar_dollar.types,)
        unwrapped_fields1339 = fields1338
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1340 = unwrapped_fields1339[1]
        pretty_gnf_column_path(pp, field1340)
        field1341 = unwrapped_fields1339[2]
        if !isnothing(field1341)
            newline(pp)
            opt_val1342 = field1341
            pretty_relation_id(pp, opt_val1342)
        end
        newline(pp)
        write(pp, "[")
        field1343 = unwrapped_fields1339[3]
        for (i1608, elem1344) in enumerate(field1343)
            i1345 = i1608 - 1
            if (i1345 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1344)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1353 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1353)
        write(pp, flat1353)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1609 = _dollar_dollar[1]
        else
            _t1609 = nothing
        end
        deconstruct_result1351 = _t1609
        if !isnothing(deconstruct_result1351)
            unwrapped1352 = deconstruct_result1351
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1352))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1610 = _dollar_dollar
            else
                _t1610 = nothing
            end
            deconstruct_result1347 = _t1610
            if !isnothing(deconstruct_result1347)
                unwrapped1348 = deconstruct_result1347
                write(pp, "[")
                indent!(pp)
                for (i1611, elem1349) in enumerate(unwrapped1348)
                    i1350 = i1611 - 1
                    if (i1350 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1349))
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
    flat1355 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1355)
        write(pp, flat1355)
        return nothing
    else
        fields1354 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1354))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1358 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1358)
        write(pp, flat1358)
        return nothing
    else
        _dollar_dollar = msg
        fields1356 = _dollar_dollar.fragment_id
        unwrapped_fields1357 = fields1356
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1357)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1363 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1363)
        write(pp, flat1363)
        return nothing
    else
        _dollar_dollar = msg
        fields1359 = _dollar_dollar.relations
        unwrapped_fields1360 = fields1359
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1360)
            newline(pp)
            for (i1612, elem1361) in enumerate(unwrapped_fields1360)
                i1362 = i1612 - 1
                if (i1362 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1361)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1368 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1368)
        write(pp, flat1368)
        return nothing
    else
        _dollar_dollar = msg
        fields1364 = _dollar_dollar.mappings
        unwrapped_fields1365 = fields1364
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1365)
            newline(pp)
            for (i1613, elem1366) in enumerate(unwrapped_fields1365)
                i1367 = i1613 - 1
                if (i1367 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1366)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1373 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1373)
        write(pp, flat1373)
        return nothing
    else
        _dollar_dollar = msg
        fields1369 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1370 = fields1369
        field1371 = unwrapped_fields1370[1]
        pretty_edb_path(pp, field1371)
        write(pp, " ")
        field1372 = unwrapped_fields1370[2]
        pretty_relation_id(pp, field1372)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1377 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1377)
        write(pp, flat1377)
        return nothing
    else
        fields1374 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1374)
            newline(pp)
            for (i1614, elem1375) in enumerate(fields1374)
                i1376 = i1614 - 1
                if (i1376 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1375)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1388 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1388)
        write(pp, flat1388)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1615 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1615 = nothing
        end
        deconstruct_result1386 = _t1615
        if !isnothing(deconstruct_result1386)
            unwrapped1387 = deconstruct_result1386
            pretty_demand(pp, unwrapped1387)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1616 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1616 = nothing
            end
            deconstruct_result1384 = _t1616
            if !isnothing(deconstruct_result1384)
                unwrapped1385 = deconstruct_result1384
                pretty_output(pp, unwrapped1385)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1617 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1617 = nothing
                end
                deconstruct_result1382 = _t1617
                if !isnothing(deconstruct_result1382)
                    unwrapped1383 = deconstruct_result1382
                    pretty_what_if(pp, unwrapped1383)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1618 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1618 = nothing
                    end
                    deconstruct_result1380 = _t1618
                    if !isnothing(deconstruct_result1380)
                        unwrapped1381 = deconstruct_result1380
                        pretty_abort(pp, unwrapped1381)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1619 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1619 = nothing
                        end
                        deconstruct_result1378 = _t1619
                        if !isnothing(deconstruct_result1378)
                            unwrapped1379 = deconstruct_result1378
                            pretty_export(pp, unwrapped1379)
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
    flat1391 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1391)
        write(pp, flat1391)
        return nothing
    else
        _dollar_dollar = msg
        fields1389 = _dollar_dollar.relation_id
        unwrapped_fields1390 = fields1389
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1390)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1396 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1396)
        write(pp, flat1396)
        return nothing
    else
        _dollar_dollar = msg
        fields1392 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1393 = fields1392
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1394 = unwrapped_fields1393[1]
        pretty_name(pp, field1394)
        newline(pp)
        field1395 = unwrapped_fields1393[2]
        pretty_relation_id(pp, field1395)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1401 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1401)
        write(pp, flat1401)
        return nothing
    else
        _dollar_dollar = msg
        fields1397 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1398 = fields1397
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1399 = unwrapped_fields1398[1]
        pretty_name(pp, field1399)
        newline(pp)
        field1400 = unwrapped_fields1398[2]
        pretty_epoch(pp, field1400)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1407 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1407)
        write(pp, flat1407)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1620 = _dollar_dollar.name
        else
            _t1620 = nothing
        end
        fields1402 = (_t1620, _dollar_dollar.relation_id,)
        unwrapped_fields1403 = fields1402
        write(pp, "(abort")
        indent_sexp!(pp)
        field1404 = unwrapped_fields1403[1]
        if !isnothing(field1404)
            newline(pp)
            opt_val1405 = field1404
            pretty_name(pp, opt_val1405)
        end
        newline(pp)
        field1406 = unwrapped_fields1403[2]
        pretty_relation_id(pp, field1406)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1412 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1412)
        write(pp, flat1412)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1621 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1621 = nothing
        end
        deconstruct_result1410 = _t1621
        if !isnothing(deconstruct_result1410)
            unwrapped1411 = deconstruct_result1410
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1411)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1622 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1622 = nothing
            end
            deconstruct_result1408 = _t1622
            if !isnothing(deconstruct_result1408)
                unwrapped1409 = deconstruct_result1408
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1409)
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
    flat1423 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1423)
        write(pp, flat1423)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1623 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1623 = nothing
        end
        deconstruct_result1418 = _t1623
        if !isnothing(deconstruct_result1418)
            unwrapped1419 = deconstruct_result1418
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1420 = unwrapped1419[1]
            pretty_export_csv_path(pp, field1420)
            newline(pp)
            field1421 = unwrapped1419[2]
            pretty_export_csv_source(pp, field1421)
            newline(pp)
            field1422 = unwrapped1419[3]
            pretty_csv_config(pp, field1422)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1625 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1624 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1625,)
            else
                _t1624 = nothing
            end
            deconstruct_result1413 = _t1624
            if !isnothing(deconstruct_result1413)
                unwrapped1414 = deconstruct_result1413
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1415 = unwrapped1414[1]
                pretty_export_csv_path(pp, field1415)
                newline(pp)
                field1416 = unwrapped1414[2]
                pretty_export_csv_columns_list(pp, field1416)
                newline(pp)
                field1417 = unwrapped1414[3]
                pretty_config_dict(pp, field1417)
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
    flat1425 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1425)
        write(pp, flat1425)
        return nothing
    else
        fields1424 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1424))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1432 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1432)
        write(pp, flat1432)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1626 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1626 = nothing
        end
        deconstruct_result1428 = _t1626
        if !isnothing(deconstruct_result1428)
            unwrapped1429 = deconstruct_result1428
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1429)
                newline(pp)
                for (i1627, elem1430) in enumerate(unwrapped1429)
                    i1431 = i1627 - 1
                    if (i1431 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1430)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1628 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1628 = nothing
            end
            deconstruct_result1426 = _t1628
            if !isnothing(deconstruct_result1426)
                unwrapped1427 = deconstruct_result1426
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1427)
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
    flat1437 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1437)
        write(pp, flat1437)
        return nothing
    else
        _dollar_dollar = msg
        fields1433 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1434 = fields1433
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1435 = unwrapped_fields1434[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1435))
        newline(pp)
        field1436 = unwrapped_fields1434[2]
        pretty_relation_id(pp, field1436)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1441 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1441)
        write(pp, flat1441)
        return nothing
    else
        fields1438 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1438)
            newline(pp)
            for (i1629, elem1439) in enumerate(fields1438)
                i1440 = i1629 - 1
                if (i1440 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1439)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1453 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1453)
        write(pp, flat1453)
        return nothing
    else
        _dollar_dollar = msg
        _t1630 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1442 = (_dollar_dollar.catalog_uri, _dollar_dollar.namespace, _dollar_dollar.table_name, _dollar_dollar.catalog_properties, _dollar_dollar.schema, _t1630,)
        unwrapped_fields1443 = fields1442
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "catalog_uri")
        newline(pp)
        field1444 = unwrapped_fields1443[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1444))
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "namespace")
        field1445 = unwrapped_fields1443[2]
        if !isempty(field1445)
            newline(pp)
            for (i1631, elem1446) in enumerate(field1445)
                i1447 = i1631 - 1
                if (i1447 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1446))
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_name")
        newline(pp)
        field1448 = unwrapped_fields1443[3]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1448))
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        field1449 = unwrapped_fields1443[4]
        pretty_export_iceberg_catalog_properties(pp, field1449)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "schema")
        newline(pp)
        field1450 = unwrapped_fields1443[5]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1450))
        dedent!(pp)
        write(pp, ")")
        field1451 = unwrapped_fields1443[6]
        if !isnothing(field1451)
            newline(pp)
            opt_val1452 = field1451
            pretty_config_dict(pp, opt_val1452)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_catalog_properties(pp::PrettyPrinter, msg::Proto.IcebergCatalogProperties)
    flat1459 = try_flat(pp, msg, pretty_export_iceberg_catalog_properties)
    if !isnothing(flat1459)
        write(pp, flat1459)
        return nothing
    else
        _dollar_dollar = msg
        _t1632 = deconstruct_iceberg_catalog_properties_optional(pp, _dollar_dollar)
        fields1454 = (_dollar_dollar.warehouse, _t1632,)
        unwrapped_fields1455 = fields1454
        write(pp, "(catalog_properties")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "warehouse")
        newline(pp)
        field1456 = unwrapped_fields1455[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1456))
        dedent!(pp)
        write(pp, ")")
        field1457 = unwrapped_fields1455[2]
        if !isnothing(field1457)
            newline(pp)
            opt_val1458 = field1457
            pretty_config_dict(pp, opt_val1458)
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
    for (i1678, _rid) in enumerate(msg.ids)
        _idx = i1678 - 1
        newline(pp)
        write(pp, "(")
        _t1679 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1679)
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
    for (i1680, _elem) in enumerate(msg.keys)
        _idx = i1680 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1681, _elem) in enumerate(msg.values)
        _idx = i1681 - 1
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
    for (i1682, _elem) in enumerate(msg.columns)
        _idx = i1682 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.IcebergCatalogProperties) = pretty_export_iceberg_catalog_properties(pp, x)
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
