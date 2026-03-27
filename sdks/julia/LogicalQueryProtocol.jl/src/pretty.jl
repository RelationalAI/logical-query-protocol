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
    _t1729 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1729
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1730 = Proto.Value(value=OneOf(:int_value, v))
    return _t1730
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1731 = Proto.Value(value=OneOf(:float_value, v))
    return _t1731
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1732 = Proto.Value(value=OneOf(:string_value, v))
    return _t1732
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1733 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1733
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1734 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1734
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1735 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1735,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1736 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1736,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1737 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1737,))
            end
        end
    end
    _t1738 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1738,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1739 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1739,))
    _t1740 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1740,))
    if msg.new_line != ""
        _t1741 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1741,))
    end
    _t1742 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1742,))
    _t1743 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1743,))
    _t1744 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1744,))
    if msg.comment != ""
        _t1745 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1745,))
    end
    for missing_string in msg.missing_strings
        _t1746 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1746,))
    end
    _t1747 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1747,))
    _t1748 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1748,))
    _t1749 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1749,))
    if msg.partition_size_mb != 0
        _t1750 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1750,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1751 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1751,))
    _t1752 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1752,))
    _t1753 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1753,))
    _t1754 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1754,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1755 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1755,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1756 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1756,))
        end
    end
    _t1757 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1757,))
    _t1758 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1758,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1759 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1759,))
    end
    if !isnothing(msg.compression)
        _t1760 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1760,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1761 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1761,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1762 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1762,))
    end
    if !isnothing(msg.syntax_delim)
        _t1763 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1763,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1764 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1764,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1765 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1765,))
    end
    return sort(result)
end

function deconstruct_iceberg_catalog_config_scope_optional(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)::Union{Nothing, String}
    if msg.scope != ""
        return msg.scope
    else
        _t1766 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1767 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1768 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1768,))
    end
    if msg.target_file_size_bytes != 0
        _t1769 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1769,))
    end
    if msg.compression != ""
        _t1770 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1770,))
    end
    if length(result) == 0
        return nothing
    else
        _t1771 = nothing
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
        _t1772 = nothing
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
    flat784 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat784)
        write(pp, flat784)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1550 = _dollar_dollar.configure
        else
            _t1550 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1551 = _dollar_dollar.sync
        else
            _t1551 = nothing
        end
        fields775 = (_t1550, _t1551, _dollar_dollar.epochs,)
        unwrapped_fields776 = fields775
        write(pp, "(transaction")
        indent_sexp!(pp)
        field777 = unwrapped_fields776[1]
        if !isnothing(field777)
            newline(pp)
            opt_val778 = field777
            pretty_configure(pp, opt_val778)
        end
        field779 = unwrapped_fields776[2]
        if !isnothing(field779)
            newline(pp)
            opt_val780 = field779
            pretty_sync(pp, opt_val780)
        end
        field781 = unwrapped_fields776[3]
        if !isempty(field781)
            newline(pp)
            for (i1552, elem782) in enumerate(field781)
                i783 = i1552 - 1
                if (i783 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem782)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat787 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat787)
        write(pp, flat787)
        return nothing
    else
        _dollar_dollar = msg
        _t1553 = deconstruct_configure(pp, _dollar_dollar)
        fields785 = _t1553
        unwrapped_fields786 = fields785
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields786)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat791 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat791)
        write(pp, flat791)
        return nothing
    else
        fields788 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields788)
            newline(pp)
            for (i1554, elem789) in enumerate(fields788)
                i790 = i1554 - 1
                if (i790 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem789)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat796 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat796)
        write(pp, flat796)
        return nothing
    else
        _dollar_dollar = msg
        fields792 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields793 = fields792
        write(pp, ":")
        field794 = unwrapped_fields793[1]
        write(pp, field794)
        write(pp, " ")
        field795 = unwrapped_fields793[2]
        pretty_raw_value(pp, field795)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat822 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat822)
        write(pp, flat822)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1555 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1555 = nothing
        end
        deconstruct_result820 = _t1555
        if !isnothing(deconstruct_result820)
            unwrapped821 = deconstruct_result820
            pretty_raw_date(pp, unwrapped821)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1556 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1556 = nothing
            end
            deconstruct_result818 = _t1556
            if !isnothing(deconstruct_result818)
                unwrapped819 = deconstruct_result818
                pretty_raw_datetime(pp, unwrapped819)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1557 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1557 = nothing
                end
                deconstruct_result816 = _t1557
                if !isnothing(deconstruct_result816)
                    unwrapped817 = deconstruct_result816
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped817))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1558 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1558 = nothing
                    end
                    deconstruct_result814 = _t1558
                    if !isnothing(deconstruct_result814)
                        unwrapped815 = deconstruct_result814
                        write(pp, (string(Int64(unwrapped815)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1559 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1559 = nothing
                        end
                        deconstruct_result812 = _t1559
                        if !isnothing(deconstruct_result812)
                            unwrapped813 = deconstruct_result812
                            write(pp, string(unwrapped813))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1560 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1560 = nothing
                            end
                            deconstruct_result810 = _t1560
                            if !isnothing(deconstruct_result810)
                                unwrapped811 = deconstruct_result810
                                write(pp, format_float32_literal(unwrapped811))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1561 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1561 = nothing
                                end
                                deconstruct_result808 = _t1561
                                if !isnothing(deconstruct_result808)
                                    unwrapped809 = deconstruct_result808
                                    write(pp, lowercase(string(unwrapped809)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1562 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1562 = nothing
                                    end
                                    deconstruct_result806 = _t1562
                                    if !isnothing(deconstruct_result806)
                                        unwrapped807 = deconstruct_result806
                                        write(pp, (string(Int64(unwrapped807)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1563 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1563 = nothing
                                        end
                                        deconstruct_result804 = _t1563
                                        if !isnothing(deconstruct_result804)
                                            unwrapped805 = deconstruct_result804
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped805))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1564 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1564 = nothing
                                            end
                                            deconstruct_result802 = _t1564
                                            if !isnothing(deconstruct_result802)
                                                unwrapped803 = deconstruct_result802
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped803))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1565 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1565 = nothing
                                                end
                                                deconstruct_result800 = _t1565
                                                if !isnothing(deconstruct_result800)
                                                    unwrapped801 = deconstruct_result800
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped801))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1566 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1566 = nothing
                                                    end
                                                    deconstruct_result798 = _t1566
                                                    if !isnothing(deconstruct_result798)
                                                        unwrapped799 = deconstruct_result798
                                                        pretty_boolean_value(pp, unwrapped799)
                                                    else
                                                        fields797 = msg
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
    flat828 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat828)
        write(pp, flat828)
        return nothing
    else
        _dollar_dollar = msg
        fields823 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields824 = fields823
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field825 = unwrapped_fields824[1]
        write(pp, string(field825))
        newline(pp)
        field826 = unwrapped_fields824[2]
        write(pp, string(field826))
        newline(pp)
        field827 = unwrapped_fields824[3]
        write(pp, string(field827))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat839 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat839)
        write(pp, flat839)
        return nothing
    else
        _dollar_dollar = msg
        fields829 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields830 = fields829
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field831 = unwrapped_fields830[1]
        write(pp, string(field831))
        newline(pp)
        field832 = unwrapped_fields830[2]
        write(pp, string(field832))
        newline(pp)
        field833 = unwrapped_fields830[3]
        write(pp, string(field833))
        newline(pp)
        field834 = unwrapped_fields830[4]
        write(pp, string(field834))
        newline(pp)
        field835 = unwrapped_fields830[5]
        write(pp, string(field835))
        newline(pp)
        field836 = unwrapped_fields830[6]
        write(pp, string(field836))
        field837 = unwrapped_fields830[7]
        if !isnothing(field837)
            newline(pp)
            opt_val838 = field837
            write(pp, string(opt_val838))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1567 = ()
    else
        _t1567 = nothing
    end
    deconstruct_result842 = _t1567
    if !isnothing(deconstruct_result842)
        unwrapped843 = deconstruct_result842
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1568 = ()
        else
            _t1568 = nothing
        end
        deconstruct_result840 = _t1568
        if !isnothing(deconstruct_result840)
            unwrapped841 = deconstruct_result840
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat848 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat848)
        write(pp, flat848)
        return nothing
    else
        _dollar_dollar = msg
        fields844 = _dollar_dollar.fragments
        unwrapped_fields845 = fields844
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields845)
            newline(pp)
            for (i1569, elem846) in enumerate(unwrapped_fields845)
                i847 = i1569 - 1
                if (i847 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem846)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat851 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat851)
        write(pp, flat851)
        return nothing
    else
        _dollar_dollar = msg
        fields849 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields850 = fields849
        write(pp, ":")
        write(pp, unwrapped_fields850)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat858 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat858)
        write(pp, flat858)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1570 = _dollar_dollar.writes
        else
            _t1570 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1571 = _dollar_dollar.reads
        else
            _t1571 = nothing
        end
        fields852 = (_t1570, _t1571,)
        unwrapped_fields853 = fields852
        write(pp, "(epoch")
        indent_sexp!(pp)
        field854 = unwrapped_fields853[1]
        if !isnothing(field854)
            newline(pp)
            opt_val855 = field854
            pretty_epoch_writes(pp, opt_val855)
        end
        field856 = unwrapped_fields853[2]
        if !isnothing(field856)
            newline(pp)
            opt_val857 = field856
            pretty_epoch_reads(pp, opt_val857)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat862 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat862)
        write(pp, flat862)
        return nothing
    else
        fields859 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields859)
            newline(pp)
            for (i1572, elem860) in enumerate(fields859)
                i861 = i1572 - 1
                if (i861 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem860)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat871 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat871)
        write(pp, flat871)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1573 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1573 = nothing
        end
        deconstruct_result869 = _t1573
        if !isnothing(deconstruct_result869)
            unwrapped870 = deconstruct_result869
            pretty_define(pp, unwrapped870)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1574 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1574 = nothing
            end
            deconstruct_result867 = _t1574
            if !isnothing(deconstruct_result867)
                unwrapped868 = deconstruct_result867
                pretty_undefine(pp, unwrapped868)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1575 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1575 = nothing
                end
                deconstruct_result865 = _t1575
                if !isnothing(deconstruct_result865)
                    unwrapped866 = deconstruct_result865
                    pretty_context(pp, unwrapped866)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1576 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1576 = nothing
                    end
                    deconstruct_result863 = _t1576
                    if !isnothing(deconstruct_result863)
                        unwrapped864 = deconstruct_result863
                        pretty_snapshot(pp, unwrapped864)
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
    flat874 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat874)
        write(pp, flat874)
        return nothing
    else
        _dollar_dollar = msg
        fields872 = _dollar_dollar.fragment
        unwrapped_fields873 = fields872
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields873)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat881 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat881)
        write(pp, flat881)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields875 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields876 = fields875
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field877 = unwrapped_fields876[1]
        pretty_new_fragment_id(pp, field877)
        field878 = unwrapped_fields876[2]
        if !isempty(field878)
            newline(pp)
            for (i1577, elem879) in enumerate(field878)
                i880 = i1577 - 1
                if (i880 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem879)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat883 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat883)
        write(pp, flat883)
        return nothing
    else
        fields882 = msg
        pretty_fragment_id(pp, fields882)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat892 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat892)
        write(pp, flat892)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1578 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1578 = nothing
        end
        deconstruct_result890 = _t1578
        if !isnothing(deconstruct_result890)
            unwrapped891 = deconstruct_result890
            pretty_def(pp, unwrapped891)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1579 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1579 = nothing
            end
            deconstruct_result888 = _t1579
            if !isnothing(deconstruct_result888)
                unwrapped889 = deconstruct_result888
                pretty_algorithm(pp, unwrapped889)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1580 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1580 = nothing
                end
                deconstruct_result886 = _t1580
                if !isnothing(deconstruct_result886)
                    unwrapped887 = deconstruct_result886
                    pretty_constraint(pp, unwrapped887)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1581 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1581 = nothing
                    end
                    deconstruct_result884 = _t1581
                    if !isnothing(deconstruct_result884)
                        unwrapped885 = deconstruct_result884
                        pretty_data(pp, unwrapped885)
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
    flat899 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat899)
        write(pp, flat899)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1582 = _dollar_dollar.attrs
        else
            _t1582 = nothing
        end
        fields893 = (_dollar_dollar.name, _dollar_dollar.body, _t1582,)
        unwrapped_fields894 = fields893
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field895 = unwrapped_fields894[1]
        pretty_relation_id(pp, field895)
        newline(pp)
        field896 = unwrapped_fields894[2]
        pretty_abstraction(pp, field896)
        field897 = unwrapped_fields894[3]
        if !isnothing(field897)
            newline(pp)
            opt_val898 = field897
            pretty_attrs(pp, opt_val898)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat904 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat904)
        write(pp, flat904)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1584 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1583 = _t1584
        else
            _t1583 = nothing
        end
        deconstruct_result902 = _t1583
        if !isnothing(deconstruct_result902)
            unwrapped903 = deconstruct_result902
            write(pp, ":")
            write(pp, unwrapped903)
        else
            _dollar_dollar = msg
            _t1585 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result900 = _t1585
            if !isnothing(deconstruct_result900)
                unwrapped901 = deconstruct_result900
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped901))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat909 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat909)
        write(pp, flat909)
        return nothing
    else
        _dollar_dollar = msg
        _t1586 = deconstruct_bindings(pp, _dollar_dollar)
        fields905 = (_t1586, _dollar_dollar.value,)
        unwrapped_fields906 = fields905
        write(pp, "(")
        indent!(pp)
        field907 = unwrapped_fields906[1]
        pretty_bindings(pp, field907)
        newline(pp)
        field908 = unwrapped_fields906[2]
        pretty_formula(pp, field908)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat917 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat917)
        write(pp, flat917)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1587 = _dollar_dollar[2]
        else
            _t1587 = nothing
        end
        fields910 = (_dollar_dollar[1], _t1587,)
        unwrapped_fields911 = fields910
        write(pp, "[")
        indent!(pp)
        field912 = unwrapped_fields911[1]
        for (i1588, elem913) in enumerate(field912)
            i914 = i1588 - 1
            if (i914 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem913)
        end
        field915 = unwrapped_fields911[2]
        if !isnothing(field915)
            newline(pp)
            opt_val916 = field915
            pretty_value_bindings(pp, opt_val916)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat922 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat922)
        write(pp, flat922)
        return nothing
    else
        _dollar_dollar = msg
        fields918 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields919 = fields918
        field920 = unwrapped_fields919[1]
        write(pp, field920)
        write(pp, "::")
        field921 = unwrapped_fields919[2]
        pretty_type(pp, field921)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat951 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat951)
        write(pp, flat951)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1589 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1589 = nothing
        end
        deconstruct_result949 = _t1589
        if !isnothing(deconstruct_result949)
            unwrapped950 = deconstruct_result949
            pretty_unspecified_type(pp, unwrapped950)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1590 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1590 = nothing
            end
            deconstruct_result947 = _t1590
            if !isnothing(deconstruct_result947)
                unwrapped948 = deconstruct_result947
                pretty_string_type(pp, unwrapped948)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1591 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1591 = nothing
                end
                deconstruct_result945 = _t1591
                if !isnothing(deconstruct_result945)
                    unwrapped946 = deconstruct_result945
                    pretty_int_type(pp, unwrapped946)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1592 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1592 = nothing
                    end
                    deconstruct_result943 = _t1592
                    if !isnothing(deconstruct_result943)
                        unwrapped944 = deconstruct_result943
                        pretty_float_type(pp, unwrapped944)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1593 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1593 = nothing
                        end
                        deconstruct_result941 = _t1593
                        if !isnothing(deconstruct_result941)
                            unwrapped942 = deconstruct_result941
                            pretty_uint128_type(pp, unwrapped942)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1594 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1594 = nothing
                            end
                            deconstruct_result939 = _t1594
                            if !isnothing(deconstruct_result939)
                                unwrapped940 = deconstruct_result939
                                pretty_int128_type(pp, unwrapped940)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1595 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1595 = nothing
                                end
                                deconstruct_result937 = _t1595
                                if !isnothing(deconstruct_result937)
                                    unwrapped938 = deconstruct_result937
                                    pretty_date_type(pp, unwrapped938)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1596 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1596 = nothing
                                    end
                                    deconstruct_result935 = _t1596
                                    if !isnothing(deconstruct_result935)
                                        unwrapped936 = deconstruct_result935
                                        pretty_datetime_type(pp, unwrapped936)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1597 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1597 = nothing
                                        end
                                        deconstruct_result933 = _t1597
                                        if !isnothing(deconstruct_result933)
                                            unwrapped934 = deconstruct_result933
                                            pretty_missing_type(pp, unwrapped934)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1598 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1598 = nothing
                                            end
                                            deconstruct_result931 = _t1598
                                            if !isnothing(deconstruct_result931)
                                                unwrapped932 = deconstruct_result931
                                                pretty_decimal_type(pp, unwrapped932)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1599 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1599 = nothing
                                                end
                                                deconstruct_result929 = _t1599
                                                if !isnothing(deconstruct_result929)
                                                    unwrapped930 = deconstruct_result929
                                                    pretty_boolean_type(pp, unwrapped930)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1600 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1600 = nothing
                                                    end
                                                    deconstruct_result927 = _t1600
                                                    if !isnothing(deconstruct_result927)
                                                        unwrapped928 = deconstruct_result927
                                                        pretty_int32_type(pp, unwrapped928)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1601 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1601 = nothing
                                                        end
                                                        deconstruct_result925 = _t1601
                                                        if !isnothing(deconstruct_result925)
                                                            unwrapped926 = deconstruct_result925
                                                            pretty_float32_type(pp, unwrapped926)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1602 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1602 = nothing
                                                            end
                                                            deconstruct_result923 = _t1602
                                                            if !isnothing(deconstruct_result923)
                                                                unwrapped924 = deconstruct_result923
                                                                pretty_uint32_type(pp, unwrapped924)
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
    fields952 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields953 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields954 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields955 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields956 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields957 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields958 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields959 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields960 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat965 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat965)
        write(pp, flat965)
        return nothing
    else
        _dollar_dollar = msg
        fields961 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields962 = fields961
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field963 = unwrapped_fields962[1]
        write(pp, string(field963))
        newline(pp)
        field964 = unwrapped_fields962[2]
        write(pp, string(field964))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields966 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields967 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields968 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields969 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat973 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat973)
        write(pp, flat973)
        return nothing
    else
        fields970 = msg
        write(pp, "|")
        if !isempty(fields970)
            write(pp, " ")
            for (i1603, elem971) in enumerate(fields970)
                i972 = i1603 - 1
                if (i972 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem971)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1000 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1000)
        write(pp, flat1000)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1604 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1604 = nothing
        end
        deconstruct_result998 = _t1604
        if !isnothing(deconstruct_result998)
            unwrapped999 = deconstruct_result998
            pretty_true(pp, unwrapped999)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1605 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1605 = nothing
            end
            deconstruct_result996 = _t1605
            if !isnothing(deconstruct_result996)
                unwrapped997 = deconstruct_result996
                pretty_false(pp, unwrapped997)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1606 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1606 = nothing
                end
                deconstruct_result994 = _t1606
                if !isnothing(deconstruct_result994)
                    unwrapped995 = deconstruct_result994
                    pretty_exists(pp, unwrapped995)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1607 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1607 = nothing
                    end
                    deconstruct_result992 = _t1607
                    if !isnothing(deconstruct_result992)
                        unwrapped993 = deconstruct_result992
                        pretty_reduce(pp, unwrapped993)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1608 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1608 = nothing
                        end
                        deconstruct_result990 = _t1608
                        if !isnothing(deconstruct_result990)
                            unwrapped991 = deconstruct_result990
                            pretty_conjunction(pp, unwrapped991)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1609 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1609 = nothing
                            end
                            deconstruct_result988 = _t1609
                            if !isnothing(deconstruct_result988)
                                unwrapped989 = deconstruct_result988
                                pretty_disjunction(pp, unwrapped989)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1610 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1610 = nothing
                                end
                                deconstruct_result986 = _t1610
                                if !isnothing(deconstruct_result986)
                                    unwrapped987 = deconstruct_result986
                                    pretty_not(pp, unwrapped987)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1611 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1611 = nothing
                                    end
                                    deconstruct_result984 = _t1611
                                    if !isnothing(deconstruct_result984)
                                        unwrapped985 = deconstruct_result984
                                        pretty_ffi(pp, unwrapped985)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1612 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1612 = nothing
                                        end
                                        deconstruct_result982 = _t1612
                                        if !isnothing(deconstruct_result982)
                                            unwrapped983 = deconstruct_result982
                                            pretty_atom(pp, unwrapped983)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1613 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1613 = nothing
                                            end
                                            deconstruct_result980 = _t1613
                                            if !isnothing(deconstruct_result980)
                                                unwrapped981 = deconstruct_result980
                                                pretty_pragma(pp, unwrapped981)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1614 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1614 = nothing
                                                end
                                                deconstruct_result978 = _t1614
                                                if !isnothing(deconstruct_result978)
                                                    unwrapped979 = deconstruct_result978
                                                    pretty_primitive(pp, unwrapped979)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1615 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1615 = nothing
                                                    end
                                                    deconstruct_result976 = _t1615
                                                    if !isnothing(deconstruct_result976)
                                                        unwrapped977 = deconstruct_result976
                                                        pretty_rel_atom(pp, unwrapped977)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1616 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1616 = nothing
                                                        end
                                                        deconstruct_result974 = _t1616
                                                        if !isnothing(deconstruct_result974)
                                                            unwrapped975 = deconstruct_result974
                                                            pretty_cast(pp, unwrapped975)
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
    fields1001 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1002 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1007 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1007)
        write(pp, flat1007)
        return nothing
    else
        _dollar_dollar = msg
        _t1617 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1003 = (_t1617, _dollar_dollar.body.value,)
        unwrapped_fields1004 = fields1003
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1005 = unwrapped_fields1004[1]
        pretty_bindings(pp, field1005)
        newline(pp)
        field1006 = unwrapped_fields1004[2]
        pretty_formula(pp, field1006)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1013 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1013)
        write(pp, flat1013)
        return nothing
    else
        _dollar_dollar = msg
        fields1008 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1009 = fields1008
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1010 = unwrapped_fields1009[1]
        pretty_abstraction(pp, field1010)
        newline(pp)
        field1011 = unwrapped_fields1009[2]
        pretty_abstraction(pp, field1011)
        newline(pp)
        field1012 = unwrapped_fields1009[3]
        pretty_terms(pp, field1012)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1017 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1017)
        write(pp, flat1017)
        return nothing
    else
        fields1014 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1014)
            newline(pp)
            for (i1618, elem1015) in enumerate(fields1014)
                i1016 = i1618 - 1
                if (i1016 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1015)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1022 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1022)
        write(pp, flat1022)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1619 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1619 = nothing
        end
        deconstruct_result1020 = _t1619
        if !isnothing(deconstruct_result1020)
            unwrapped1021 = deconstruct_result1020
            pretty_var(pp, unwrapped1021)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1620 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1620 = nothing
            end
            deconstruct_result1018 = _t1620
            if !isnothing(deconstruct_result1018)
                unwrapped1019 = deconstruct_result1018
                pretty_value(pp, unwrapped1019)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1025 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1025)
        write(pp, flat1025)
        return nothing
    else
        _dollar_dollar = msg
        fields1023 = _dollar_dollar.name
        unwrapped_fields1024 = fields1023
        write(pp, unwrapped_fields1024)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1051 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1051)
        write(pp, flat1051)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1621 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1621 = nothing
        end
        deconstruct_result1049 = _t1621
        if !isnothing(deconstruct_result1049)
            unwrapped1050 = deconstruct_result1049
            pretty_date(pp, unwrapped1050)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1622 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1622 = nothing
            end
            deconstruct_result1047 = _t1622
            if !isnothing(deconstruct_result1047)
                unwrapped1048 = deconstruct_result1047
                pretty_datetime(pp, unwrapped1048)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1623 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1623 = nothing
                end
                deconstruct_result1045 = _t1623
                if !isnothing(deconstruct_result1045)
                    unwrapped1046 = deconstruct_result1045
                    write(pp, format_string(pp, unwrapped1046))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1624 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1624 = nothing
                    end
                    deconstruct_result1043 = _t1624
                    if !isnothing(deconstruct_result1043)
                        unwrapped1044 = deconstruct_result1043
                        write(pp, format_int32(pp, unwrapped1044))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1625 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1625 = nothing
                        end
                        deconstruct_result1041 = _t1625
                        if !isnothing(deconstruct_result1041)
                            unwrapped1042 = deconstruct_result1041
                            write(pp, format_int(pp, unwrapped1042))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1626 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1626 = nothing
                            end
                            deconstruct_result1039 = _t1626
                            if !isnothing(deconstruct_result1039)
                                unwrapped1040 = deconstruct_result1039
                                write(pp, format_float32(pp, unwrapped1040))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1627 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1627 = nothing
                                end
                                deconstruct_result1037 = _t1627
                                if !isnothing(deconstruct_result1037)
                                    unwrapped1038 = deconstruct_result1037
                                    write(pp, format_float(pp, unwrapped1038))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1628 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1628 = nothing
                                    end
                                    deconstruct_result1035 = _t1628
                                    if !isnothing(deconstruct_result1035)
                                        unwrapped1036 = deconstruct_result1035
                                        write(pp, format_uint32(pp, unwrapped1036))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1629 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1629 = nothing
                                        end
                                        deconstruct_result1033 = _t1629
                                        if !isnothing(deconstruct_result1033)
                                            unwrapped1034 = deconstruct_result1033
                                            write(pp, format_uint128(pp, unwrapped1034))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1630 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1630 = nothing
                                            end
                                            deconstruct_result1031 = _t1630
                                            if !isnothing(deconstruct_result1031)
                                                unwrapped1032 = deconstruct_result1031
                                                write(pp, format_int128(pp, unwrapped1032))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1631 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1631 = nothing
                                                end
                                                deconstruct_result1029 = _t1631
                                                if !isnothing(deconstruct_result1029)
                                                    unwrapped1030 = deconstruct_result1029
                                                    write(pp, format_decimal(pp, unwrapped1030))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1632 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1632 = nothing
                                                    end
                                                    deconstruct_result1027 = _t1632
                                                    if !isnothing(deconstruct_result1027)
                                                        unwrapped1028 = deconstruct_result1027
                                                        pretty_boolean_value(pp, unwrapped1028)
                                                    else
                                                        fields1026 = msg
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
    flat1057 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1057)
        write(pp, flat1057)
        return nothing
    else
        _dollar_dollar = msg
        fields1052 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1053 = fields1052
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1054 = unwrapped_fields1053[1]
        write(pp, format_int(pp, field1054))
        newline(pp)
        field1055 = unwrapped_fields1053[2]
        write(pp, format_int(pp, field1055))
        newline(pp)
        field1056 = unwrapped_fields1053[3]
        write(pp, format_int(pp, field1056))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1068 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1068)
        write(pp, flat1068)
        return nothing
    else
        _dollar_dollar = msg
        fields1058 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1059 = fields1058
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1060 = unwrapped_fields1059[1]
        write(pp, format_int(pp, field1060))
        newline(pp)
        field1061 = unwrapped_fields1059[2]
        write(pp, format_int(pp, field1061))
        newline(pp)
        field1062 = unwrapped_fields1059[3]
        write(pp, format_int(pp, field1062))
        newline(pp)
        field1063 = unwrapped_fields1059[4]
        write(pp, format_int(pp, field1063))
        newline(pp)
        field1064 = unwrapped_fields1059[5]
        write(pp, format_int(pp, field1064))
        newline(pp)
        field1065 = unwrapped_fields1059[6]
        write(pp, format_int(pp, field1065))
        field1066 = unwrapped_fields1059[7]
        if !isnothing(field1066)
            newline(pp)
            opt_val1067 = field1066
            write(pp, format_int(pp, opt_val1067))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1073 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1073)
        write(pp, flat1073)
        return nothing
    else
        _dollar_dollar = msg
        fields1069 = _dollar_dollar.args
        unwrapped_fields1070 = fields1069
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1070)
            newline(pp)
            for (i1633, elem1071) in enumerate(unwrapped_fields1070)
                i1072 = i1633 - 1
                if (i1072 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1071)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1078 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1078)
        write(pp, flat1078)
        return nothing
    else
        _dollar_dollar = msg
        fields1074 = _dollar_dollar.args
        unwrapped_fields1075 = fields1074
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1075)
            newline(pp)
            for (i1634, elem1076) in enumerate(unwrapped_fields1075)
                i1077 = i1634 - 1
                if (i1077 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1076)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1081 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1081)
        write(pp, flat1081)
        return nothing
    else
        _dollar_dollar = msg
        fields1079 = _dollar_dollar.arg
        unwrapped_fields1080 = fields1079
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1080)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1087 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1087)
        write(pp, flat1087)
        return nothing
    else
        _dollar_dollar = msg
        fields1082 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1083 = fields1082
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1084 = unwrapped_fields1083[1]
        pretty_name(pp, field1084)
        newline(pp)
        field1085 = unwrapped_fields1083[2]
        pretty_ffi_args(pp, field1085)
        newline(pp)
        field1086 = unwrapped_fields1083[3]
        pretty_terms(pp, field1086)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1089 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1089)
        write(pp, flat1089)
        return nothing
    else
        fields1088 = msg
        write(pp, ":")
        write(pp, fields1088)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1093 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1093)
        write(pp, flat1093)
        return nothing
    else
        fields1090 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1090)
            newline(pp)
            for (i1635, elem1091) in enumerate(fields1090)
                i1092 = i1635 - 1
                if (i1092 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1091)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1100 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1100)
        write(pp, flat1100)
        return nothing
    else
        _dollar_dollar = msg
        fields1094 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1095 = fields1094
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1096 = unwrapped_fields1095[1]
        pretty_relation_id(pp, field1096)
        field1097 = unwrapped_fields1095[2]
        if !isempty(field1097)
            newline(pp)
            for (i1636, elem1098) in enumerate(field1097)
                i1099 = i1636 - 1
                if (i1099 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1098)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1107 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1107)
        write(pp, flat1107)
        return nothing
    else
        _dollar_dollar = msg
        fields1101 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1102 = fields1101
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1103 = unwrapped_fields1102[1]
        pretty_name(pp, field1103)
        field1104 = unwrapped_fields1102[2]
        if !isempty(field1104)
            newline(pp)
            for (i1637, elem1105) in enumerate(field1104)
                i1106 = i1637 - 1
                if (i1106 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1105)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1123 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1123)
        write(pp, flat1123)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1638 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1638 = nothing
        end
        guard_result1122 = _t1638
        if !isnothing(guard_result1122)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1639 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1639 = nothing
            end
            guard_result1121 = _t1639
            if !isnothing(guard_result1121)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1640 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1640 = nothing
                end
                guard_result1120 = _t1640
                if !isnothing(guard_result1120)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1641 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1641 = nothing
                    end
                    guard_result1119 = _t1641
                    if !isnothing(guard_result1119)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1642 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1642 = nothing
                        end
                        guard_result1118 = _t1642
                        if !isnothing(guard_result1118)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1643 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1643 = nothing
                            end
                            guard_result1117 = _t1643
                            if !isnothing(guard_result1117)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1644 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1644 = nothing
                                end
                                guard_result1116 = _t1644
                                if !isnothing(guard_result1116)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1645 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1645 = nothing
                                    end
                                    guard_result1115 = _t1645
                                    if !isnothing(guard_result1115)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1646 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1646 = nothing
                                        end
                                        guard_result1114 = _t1646
                                        if !isnothing(guard_result1114)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1108 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1109 = fields1108
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1110 = unwrapped_fields1109[1]
                                            pretty_name(pp, field1110)
                                            field1111 = unwrapped_fields1109[2]
                                            if !isempty(field1111)
                                                newline(pp)
                                                for (i1647, elem1112) in enumerate(field1111)
                                                    i1113 = i1647 - 1
                                                    if (i1113 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1112)
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
    flat1128 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1128)
        write(pp, flat1128)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1648 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1648 = nothing
        end
        fields1124 = _t1648
        unwrapped_fields1125 = fields1124
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1126 = unwrapped_fields1125[1]
        pretty_term(pp, field1126)
        newline(pp)
        field1127 = unwrapped_fields1125[2]
        pretty_term(pp, field1127)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1133 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1133)
        write(pp, flat1133)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1649 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1649 = nothing
        end
        fields1129 = _t1649
        unwrapped_fields1130 = fields1129
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1131 = unwrapped_fields1130[1]
        pretty_term(pp, field1131)
        newline(pp)
        field1132 = unwrapped_fields1130[2]
        pretty_term(pp, field1132)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1138 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1138)
        write(pp, flat1138)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1650 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1650 = nothing
        end
        fields1134 = _t1650
        unwrapped_fields1135 = fields1134
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1136 = unwrapped_fields1135[1]
        pretty_term(pp, field1136)
        newline(pp)
        field1137 = unwrapped_fields1135[2]
        pretty_term(pp, field1137)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1143 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1143)
        write(pp, flat1143)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1651 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1651 = nothing
        end
        fields1139 = _t1651
        unwrapped_fields1140 = fields1139
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1141 = unwrapped_fields1140[1]
        pretty_term(pp, field1141)
        newline(pp)
        field1142 = unwrapped_fields1140[2]
        pretty_term(pp, field1142)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1148 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1148)
        write(pp, flat1148)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1652 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1652 = nothing
        end
        fields1144 = _t1652
        unwrapped_fields1145 = fields1144
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1146 = unwrapped_fields1145[1]
        pretty_term(pp, field1146)
        newline(pp)
        field1147 = unwrapped_fields1145[2]
        pretty_term(pp, field1147)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1154 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1154)
        write(pp, flat1154)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1653 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1653 = nothing
        end
        fields1149 = _t1653
        unwrapped_fields1150 = fields1149
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1151 = unwrapped_fields1150[1]
        pretty_term(pp, field1151)
        newline(pp)
        field1152 = unwrapped_fields1150[2]
        pretty_term(pp, field1152)
        newline(pp)
        field1153 = unwrapped_fields1150[3]
        pretty_term(pp, field1153)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1160 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1160)
        write(pp, flat1160)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1654 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1654 = nothing
        end
        fields1155 = _t1654
        unwrapped_fields1156 = fields1155
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1157 = unwrapped_fields1156[1]
        pretty_term(pp, field1157)
        newline(pp)
        field1158 = unwrapped_fields1156[2]
        pretty_term(pp, field1158)
        newline(pp)
        field1159 = unwrapped_fields1156[3]
        pretty_term(pp, field1159)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1166 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1166)
        write(pp, flat1166)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1655 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1655 = nothing
        end
        fields1161 = _t1655
        unwrapped_fields1162 = fields1161
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1163 = unwrapped_fields1162[1]
        pretty_term(pp, field1163)
        newline(pp)
        field1164 = unwrapped_fields1162[2]
        pretty_term(pp, field1164)
        newline(pp)
        field1165 = unwrapped_fields1162[3]
        pretty_term(pp, field1165)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1172 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1172)
        write(pp, flat1172)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1656 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1656 = nothing
        end
        fields1167 = _t1656
        unwrapped_fields1168 = fields1167
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1169 = unwrapped_fields1168[1]
        pretty_term(pp, field1169)
        newline(pp)
        field1170 = unwrapped_fields1168[2]
        pretty_term(pp, field1170)
        newline(pp)
        field1171 = unwrapped_fields1168[3]
        pretty_term(pp, field1171)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1177 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1177)
        write(pp, flat1177)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1657 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1657 = nothing
        end
        deconstruct_result1175 = _t1657
        if !isnothing(deconstruct_result1175)
            unwrapped1176 = deconstruct_result1175
            pretty_specialized_value(pp, unwrapped1176)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1658 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1658 = nothing
            end
            deconstruct_result1173 = _t1658
            if !isnothing(deconstruct_result1173)
                unwrapped1174 = deconstruct_result1173
                pretty_term(pp, unwrapped1174)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1179 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        fields1178 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1178)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1186 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1186)
        write(pp, flat1186)
        return nothing
    else
        _dollar_dollar = msg
        fields1180 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1181 = fields1180
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1182 = unwrapped_fields1181[1]
        pretty_name(pp, field1182)
        field1183 = unwrapped_fields1181[2]
        if !isempty(field1183)
            newline(pp)
            for (i1659, elem1184) in enumerate(field1183)
                i1185 = i1659 - 1
                if (i1185 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1184)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1191 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1191)
        write(pp, flat1191)
        return nothing
    else
        _dollar_dollar = msg
        fields1187 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1188 = fields1187
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1189 = unwrapped_fields1188[1]
        pretty_term(pp, field1189)
        newline(pp)
        field1190 = unwrapped_fields1188[2]
        pretty_term(pp, field1190)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1195 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1195)
        write(pp, flat1195)
        return nothing
    else
        fields1192 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1192)
            newline(pp)
            for (i1660, elem1193) in enumerate(fields1192)
                i1194 = i1660 - 1
                if (i1194 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1193)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1202 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1202)
        write(pp, flat1202)
        return nothing
    else
        _dollar_dollar = msg
        fields1196 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1197 = fields1196
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1198 = unwrapped_fields1197[1]
        pretty_name(pp, field1198)
        field1199 = unwrapped_fields1197[2]
        if !isempty(field1199)
            newline(pp)
            for (i1661, elem1200) in enumerate(field1199)
                i1201 = i1661 - 1
                if (i1201 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1200)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1209 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1209)
        write(pp, flat1209)
        return nothing
    else
        _dollar_dollar = msg
        fields1203 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1204 = fields1203
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1205 = unwrapped_fields1204[1]
        if !isempty(field1205)
            newline(pp)
            for (i1662, elem1206) in enumerate(field1205)
                i1207 = i1662 - 1
                if (i1207 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1206)
            end
        end
        newline(pp)
        field1208 = unwrapped_fields1204[2]
        pretty_script(pp, field1208)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1214 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1214)
        write(pp, flat1214)
        return nothing
    else
        _dollar_dollar = msg
        fields1210 = _dollar_dollar.constructs
        unwrapped_fields1211 = fields1210
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1211)
            newline(pp)
            for (i1663, elem1212) in enumerate(unwrapped_fields1211)
                i1213 = i1663 - 1
                if (i1213 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1212)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1219 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1219)
        write(pp, flat1219)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1664 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1664 = nothing
        end
        deconstruct_result1217 = _t1664
        if !isnothing(deconstruct_result1217)
            unwrapped1218 = deconstruct_result1217
            pretty_loop(pp, unwrapped1218)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1665 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1665 = nothing
            end
            deconstruct_result1215 = _t1665
            if !isnothing(deconstruct_result1215)
                unwrapped1216 = deconstruct_result1215
                pretty_instruction(pp, unwrapped1216)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1224 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1224)
        write(pp, flat1224)
        return nothing
    else
        _dollar_dollar = msg
        fields1220 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1221 = fields1220
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1222 = unwrapped_fields1221[1]
        pretty_init(pp, field1222)
        newline(pp)
        field1223 = unwrapped_fields1221[2]
        pretty_script(pp, field1223)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1228 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1228)
        write(pp, flat1228)
        return nothing
    else
        fields1225 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1225)
            newline(pp)
            for (i1666, elem1226) in enumerate(fields1225)
                i1227 = i1666 - 1
                if (i1227 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1226)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1239 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1239)
        write(pp, flat1239)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1667 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1667 = nothing
        end
        deconstruct_result1237 = _t1667
        if !isnothing(deconstruct_result1237)
            unwrapped1238 = deconstruct_result1237
            pretty_assign(pp, unwrapped1238)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1668 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1668 = nothing
            end
            deconstruct_result1235 = _t1668
            if !isnothing(deconstruct_result1235)
                unwrapped1236 = deconstruct_result1235
                pretty_upsert(pp, unwrapped1236)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1669 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1669 = nothing
                end
                deconstruct_result1233 = _t1669
                if !isnothing(deconstruct_result1233)
                    unwrapped1234 = deconstruct_result1233
                    pretty_break(pp, unwrapped1234)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1670 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1670 = nothing
                    end
                    deconstruct_result1231 = _t1670
                    if !isnothing(deconstruct_result1231)
                        unwrapped1232 = deconstruct_result1231
                        pretty_monoid_def(pp, unwrapped1232)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1671 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1671 = nothing
                        end
                        deconstruct_result1229 = _t1671
                        if !isnothing(deconstruct_result1229)
                            unwrapped1230 = deconstruct_result1229
                            pretty_monus_def(pp, unwrapped1230)
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
    flat1246 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1246)
        write(pp, flat1246)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1672 = _dollar_dollar.attrs
        else
            _t1672 = nothing
        end
        fields1240 = (_dollar_dollar.name, _dollar_dollar.body, _t1672,)
        unwrapped_fields1241 = fields1240
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1242 = unwrapped_fields1241[1]
        pretty_relation_id(pp, field1242)
        newline(pp)
        field1243 = unwrapped_fields1241[2]
        pretty_abstraction(pp, field1243)
        field1244 = unwrapped_fields1241[3]
        if !isnothing(field1244)
            newline(pp)
            opt_val1245 = field1244
            pretty_attrs(pp, opt_val1245)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1253 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1673 = _dollar_dollar.attrs
        else
            _t1673 = nothing
        end
        fields1247 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1673,)
        unwrapped_fields1248 = fields1247
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1249 = unwrapped_fields1248[1]
        pretty_relation_id(pp, field1249)
        newline(pp)
        field1250 = unwrapped_fields1248[2]
        pretty_abstraction_with_arity(pp, field1250)
        field1251 = unwrapped_fields1248[3]
        if !isnothing(field1251)
            newline(pp)
            opt_val1252 = field1251
            pretty_attrs(pp, opt_val1252)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1258 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1258)
        write(pp, flat1258)
        return nothing
    else
        _dollar_dollar = msg
        _t1674 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1254 = (_t1674, _dollar_dollar[1].value,)
        unwrapped_fields1255 = fields1254
        write(pp, "(")
        indent!(pp)
        field1256 = unwrapped_fields1255[1]
        pretty_bindings(pp, field1256)
        newline(pp)
        field1257 = unwrapped_fields1255[2]
        pretty_formula(pp, field1257)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1265 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1265)
        write(pp, flat1265)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1675 = _dollar_dollar.attrs
        else
            _t1675 = nothing
        end
        fields1259 = (_dollar_dollar.name, _dollar_dollar.body, _t1675,)
        unwrapped_fields1260 = fields1259
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1261 = unwrapped_fields1260[1]
        pretty_relation_id(pp, field1261)
        newline(pp)
        field1262 = unwrapped_fields1260[2]
        pretty_abstraction(pp, field1262)
        field1263 = unwrapped_fields1260[3]
        if !isnothing(field1263)
            newline(pp)
            opt_val1264 = field1263
            pretty_attrs(pp, opt_val1264)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1273 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1273)
        write(pp, flat1273)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1676 = _dollar_dollar.attrs
        else
            _t1676 = nothing
        end
        fields1266 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1676,)
        unwrapped_fields1267 = fields1266
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1268 = unwrapped_fields1267[1]
        pretty_monoid(pp, field1268)
        newline(pp)
        field1269 = unwrapped_fields1267[2]
        pretty_relation_id(pp, field1269)
        newline(pp)
        field1270 = unwrapped_fields1267[3]
        pretty_abstraction_with_arity(pp, field1270)
        field1271 = unwrapped_fields1267[4]
        if !isnothing(field1271)
            newline(pp)
            opt_val1272 = field1271
            pretty_attrs(pp, opt_val1272)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1282 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1282)
        write(pp, flat1282)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1677 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1677 = nothing
        end
        deconstruct_result1280 = _t1677
        if !isnothing(deconstruct_result1280)
            unwrapped1281 = deconstruct_result1280
            pretty_or_monoid(pp, unwrapped1281)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1678 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1678 = nothing
            end
            deconstruct_result1278 = _t1678
            if !isnothing(deconstruct_result1278)
                unwrapped1279 = deconstruct_result1278
                pretty_min_monoid(pp, unwrapped1279)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1679 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1679 = nothing
                end
                deconstruct_result1276 = _t1679
                if !isnothing(deconstruct_result1276)
                    unwrapped1277 = deconstruct_result1276
                    pretty_max_monoid(pp, unwrapped1277)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1680 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1680 = nothing
                    end
                    deconstruct_result1274 = _t1680
                    if !isnothing(deconstruct_result1274)
                        unwrapped1275 = deconstruct_result1274
                        pretty_sum_monoid(pp, unwrapped1275)
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
    fields1283 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1286 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1286)
        write(pp, flat1286)
        return nothing
    else
        _dollar_dollar = msg
        fields1284 = _dollar_dollar.var"#type"
        unwrapped_fields1285 = fields1284
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1285)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1289 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1289)
        write(pp, flat1289)
        return nothing
    else
        _dollar_dollar = msg
        fields1287 = _dollar_dollar.var"#type"
        unwrapped_fields1288 = fields1287
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1288)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1292 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1292)
        write(pp, flat1292)
        return nothing
    else
        _dollar_dollar = msg
        fields1290 = _dollar_dollar.var"#type"
        unwrapped_fields1291 = fields1290
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1291)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1300 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1300)
        write(pp, flat1300)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1681 = _dollar_dollar.attrs
        else
            _t1681 = nothing
        end
        fields1293 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1681,)
        unwrapped_fields1294 = fields1293
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1295 = unwrapped_fields1294[1]
        pretty_monoid(pp, field1295)
        newline(pp)
        field1296 = unwrapped_fields1294[2]
        pretty_relation_id(pp, field1296)
        newline(pp)
        field1297 = unwrapped_fields1294[3]
        pretty_abstraction_with_arity(pp, field1297)
        field1298 = unwrapped_fields1294[4]
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

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1307 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1307)
        write(pp, flat1307)
        return nothing
    else
        _dollar_dollar = msg
        fields1301 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1302 = fields1301
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1303 = unwrapped_fields1302[1]
        pretty_relation_id(pp, field1303)
        newline(pp)
        field1304 = unwrapped_fields1302[2]
        pretty_abstraction(pp, field1304)
        newline(pp)
        field1305 = unwrapped_fields1302[3]
        pretty_functional_dependency_keys(pp, field1305)
        newline(pp)
        field1306 = unwrapped_fields1302[4]
        pretty_functional_dependency_values(pp, field1306)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1311 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1311)
        write(pp, flat1311)
        return nothing
    else
        fields1308 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1308)
            newline(pp)
            for (i1682, elem1309) in enumerate(fields1308)
                i1310 = i1682 - 1
                if (i1310 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1309)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1315 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1315)
        write(pp, flat1315)
        return nothing
    else
        fields1312 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1312)
            newline(pp)
            for (i1683, elem1313) in enumerate(fields1312)
                i1314 = i1683 - 1
                if (i1314 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1313)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1324 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1324)
        write(pp, flat1324)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1684 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1684 = nothing
        end
        deconstruct_result1322 = _t1684
        if !isnothing(deconstruct_result1322)
            unwrapped1323 = deconstruct_result1322
            pretty_edb(pp, unwrapped1323)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1685 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1685 = nothing
            end
            deconstruct_result1320 = _t1685
            if !isnothing(deconstruct_result1320)
                unwrapped1321 = deconstruct_result1320
                pretty_betree_relation(pp, unwrapped1321)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1686 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1686 = nothing
                end
                deconstruct_result1318 = _t1686
                if !isnothing(deconstruct_result1318)
                    unwrapped1319 = deconstruct_result1318
                    pretty_csv_data(pp, unwrapped1319)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1687 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1687 = nothing
                    end
                    deconstruct_result1316 = _t1687
                    if !isnothing(deconstruct_result1316)
                        unwrapped1317 = deconstruct_result1316
                        pretty_iceberg_data(pp, unwrapped1317)
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
    flat1330 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1330)
        write(pp, flat1330)
        return nothing
    else
        _dollar_dollar = msg
        fields1325 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1326 = fields1325
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1327 = unwrapped_fields1326[1]
        pretty_relation_id(pp, field1327)
        newline(pp)
        field1328 = unwrapped_fields1326[2]
        pretty_edb_path(pp, field1328)
        newline(pp)
        field1329 = unwrapped_fields1326[3]
        pretty_edb_types(pp, field1329)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1334 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1334)
        write(pp, flat1334)
        return nothing
    else
        fields1331 = msg
        write(pp, "[")
        indent!(pp)
        for (i1688, elem1332) in enumerate(fields1331)
            i1333 = i1688 - 1
            if (i1333 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1332))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1338 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1338)
        write(pp, flat1338)
        return nothing
    else
        fields1335 = msg
        write(pp, "[")
        indent!(pp)
        for (i1689, elem1336) in enumerate(fields1335)
            i1337 = i1689 - 1
            if (i1337 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1336)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1343 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1343)
        write(pp, flat1343)
        return nothing
    else
        _dollar_dollar = msg
        fields1339 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1340 = fields1339
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1341 = unwrapped_fields1340[1]
        pretty_relation_id(pp, field1341)
        newline(pp)
        field1342 = unwrapped_fields1340[2]
        pretty_betree_info(pp, field1342)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1349 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1349)
        write(pp, flat1349)
        return nothing
    else
        _dollar_dollar = msg
        _t1690 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1344 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1690,)
        unwrapped_fields1345 = fields1344
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1346 = unwrapped_fields1345[1]
        pretty_betree_info_key_types(pp, field1346)
        newline(pp)
        field1347 = unwrapped_fields1345[2]
        pretty_betree_info_value_types(pp, field1347)
        newline(pp)
        field1348 = unwrapped_fields1345[3]
        pretty_config_dict(pp, field1348)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1353 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1353)
        write(pp, flat1353)
        return nothing
    else
        fields1350 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1350)
            newline(pp)
            for (i1691, elem1351) in enumerate(fields1350)
                i1352 = i1691 - 1
                if (i1352 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1351)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1357 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1357)
        write(pp, flat1357)
        return nothing
    else
        fields1354 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1354)
            newline(pp)
            for (i1692, elem1355) in enumerate(fields1354)
                i1356 = i1692 - 1
                if (i1356 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1355)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1364 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1364)
        write(pp, flat1364)
        return nothing
    else
        _dollar_dollar = msg
        fields1358 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1359 = fields1358
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1360 = unwrapped_fields1359[1]
        pretty_csvlocator(pp, field1360)
        newline(pp)
        field1361 = unwrapped_fields1359[2]
        pretty_csv_config(pp, field1361)
        newline(pp)
        field1362 = unwrapped_fields1359[3]
        pretty_gnf_columns(pp, field1362)
        newline(pp)
        field1363 = unwrapped_fields1359[4]
        pretty_csv_asof(pp, field1363)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1371 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1371)
        write(pp, flat1371)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1693 = _dollar_dollar.paths
        else
            _t1693 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1694 = String(copy(_dollar_dollar.inline_data))
        else
            _t1694 = nothing
        end
        fields1365 = (_t1693, _t1694,)
        unwrapped_fields1366 = fields1365
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1367 = unwrapped_fields1366[1]
        if !isnothing(field1367)
            newline(pp)
            opt_val1368 = field1367
            pretty_csv_locator_paths(pp, opt_val1368)
        end
        field1369 = unwrapped_fields1366[2]
        if !isnothing(field1369)
            newline(pp)
            opt_val1370 = field1369
            pretty_csv_locator_inline_data(pp, opt_val1370)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1375 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1375)
        write(pp, flat1375)
        return nothing
    else
        fields1372 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1372)
            newline(pp)
            for (i1695, elem1373) in enumerate(fields1372)
                i1374 = i1695 - 1
                if (i1374 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1373))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1377 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1377)
        write(pp, flat1377)
        return nothing
    else
        fields1376 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1376))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1380 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1380)
        write(pp, flat1380)
        return nothing
    else
        _dollar_dollar = msg
        _t1696 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1378 = _t1696
        unwrapped_fields1379 = fields1378
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1379)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1384 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1384)
        write(pp, flat1384)
        return nothing
    else
        fields1381 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1381)
            newline(pp)
            for (i1697, elem1382) in enumerate(fields1381)
                i1383 = i1697 - 1
                if (i1383 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1382)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1393 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1393)
        write(pp, flat1393)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1698 = _dollar_dollar.target_id
        else
            _t1698 = nothing
        end
        fields1385 = (_dollar_dollar.column_path, _t1698, _dollar_dollar.types,)
        unwrapped_fields1386 = fields1385
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1387 = unwrapped_fields1386[1]
        pretty_gnf_column_path(pp, field1387)
        field1388 = unwrapped_fields1386[2]
        if !isnothing(field1388)
            newline(pp)
            opt_val1389 = field1388
            pretty_relation_id(pp, opt_val1389)
        end
        newline(pp)
        write(pp, "[")
        field1390 = unwrapped_fields1386[3]
        for (i1699, elem1391) in enumerate(field1390)
            i1392 = i1699 - 1
            if (i1392 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1391)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1400 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1400)
        write(pp, flat1400)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1700 = _dollar_dollar[1]
        else
            _t1700 = nothing
        end
        deconstruct_result1398 = _t1700
        if !isnothing(deconstruct_result1398)
            unwrapped1399 = deconstruct_result1398
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1399))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1701 = _dollar_dollar
            else
                _t1701 = nothing
            end
            deconstruct_result1394 = _t1701
            if !isnothing(deconstruct_result1394)
                unwrapped1395 = deconstruct_result1394
                write(pp, "[")
                indent!(pp)
                for (i1702, elem1396) in enumerate(unwrapped1395)
                    i1397 = i1702 - 1
                    if (i1397 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1396))
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
    flat1402 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1402)
        write(pp, flat1402)
        return nothing
    else
        fields1401 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1401))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1410 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1410)
        write(pp, flat1410)
        return nothing
    else
        _dollar_dollar = msg
        _t1703 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1403 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1703,)
        unwrapped_fields1404 = fields1403
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1405 = unwrapped_fields1404[1]
        pretty_iceberg_locator(pp, field1405)
        newline(pp)
        field1406 = unwrapped_fields1404[2]
        pretty_iceberg_catalog_config(pp, field1406)
        newline(pp)
        field1407 = unwrapped_fields1404[3]
        pretty_gnf_columns(pp, field1407)
        field1408 = unwrapped_fields1404[4]
        if !isnothing(field1408)
            newline(pp)
            opt_val1409 = field1408
            pretty_iceberg_to_snapshot(pp, opt_val1409)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1418 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1418)
        write(pp, flat1418)
        return nothing
    else
        _dollar_dollar = msg
        fields1411 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1412 = fields1411
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_name")
        newline(pp)
        field1413 = unwrapped_fields1412[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1413))
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "namespace")
        field1414 = unwrapped_fields1412[2]
        if !isempty(field1414)
            newline(pp)
            for (i1704, elem1415) in enumerate(field1414)
                i1416 = i1704 - 1
                if (i1416 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1415))
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "warehouse")
        newline(pp)
        field1417 = unwrapped_fields1412[3]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1417))
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1430 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1430)
        write(pp, flat1430)
        return nothing
    else
        _dollar_dollar = msg
        _t1705 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1419 = (_dollar_dollar.catalog_uri, _t1705, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1420 = fields1419
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "catalog_uri")
        newline(pp)
        field1421 = unwrapped_fields1420[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1421))
        dedent!(pp)
        write(pp, ")")
        field1422 = unwrapped_fields1420[2]
        if !isnothing(field1422)
            newline(pp)
            opt_val1423 = field1422
            pretty_iceberg_catalog_config_scope(pp, opt_val1423)
        end
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "properties")
        field1424 = unwrapped_fields1420[3]
        if !isempty(field1424)
            newline(pp)
            for (i1706, elem1425) in enumerate(field1424)
                i1426 = i1706 - 1
                if (i1426 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1425)
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "auth_properties")
        field1427 = unwrapped_fields1420[4]
        if !isempty(field1427)
            newline(pp)
            for (i1707, elem1428) in enumerate(field1427)
                i1429 = i1707 - 1
                if (i1429 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1428)
            end
        end
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1432 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1432)
        write(pp, flat1432)
        return nothing
    else
        fields1431 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1431))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1437 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1437)
        write(pp, flat1437)
        return nothing
    else
        _dollar_dollar = msg
        fields1433 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1434 = fields1433
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1435 = unwrapped_fields1434[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1435))
        newline(pp)
        field1436 = unwrapped_fields1434[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1436))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1439 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1439)
        write(pp, flat1439)
        return nothing
    else
        fields1438 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1438))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1442 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1442)
        write(pp, flat1442)
        return nothing
    else
        _dollar_dollar = msg
        fields1440 = _dollar_dollar.fragment_id
        unwrapped_fields1441 = fields1440
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1441)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1447 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1447)
        write(pp, flat1447)
        return nothing
    else
        _dollar_dollar = msg
        fields1443 = _dollar_dollar.relations
        unwrapped_fields1444 = fields1443
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1444)
            newline(pp)
            for (i1708, elem1445) in enumerate(unwrapped_fields1444)
                i1446 = i1708 - 1
                if (i1446 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1445)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1452 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1452)
        write(pp, flat1452)
        return nothing
    else
        _dollar_dollar = msg
        fields1448 = _dollar_dollar.mappings
        unwrapped_fields1449 = fields1448
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1449)
            newline(pp)
            for (i1709, elem1450) in enumerate(unwrapped_fields1449)
                i1451 = i1709 - 1
                if (i1451 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1450)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1457 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1457)
        write(pp, flat1457)
        return nothing
    else
        _dollar_dollar = msg
        fields1453 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1454 = fields1453
        field1455 = unwrapped_fields1454[1]
        pretty_edb_path(pp, field1455)
        write(pp, " ")
        field1456 = unwrapped_fields1454[2]
        pretty_relation_id(pp, field1456)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1461 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1461)
        write(pp, flat1461)
        return nothing
    else
        fields1458 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1458)
            newline(pp)
            for (i1710, elem1459) in enumerate(fields1458)
                i1460 = i1710 - 1
                if (i1460 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1459)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1472 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1472)
        write(pp, flat1472)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1711 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1711 = nothing
        end
        deconstruct_result1470 = _t1711
        if !isnothing(deconstruct_result1470)
            unwrapped1471 = deconstruct_result1470
            pretty_demand(pp, unwrapped1471)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1712 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1712 = nothing
            end
            deconstruct_result1468 = _t1712
            if !isnothing(deconstruct_result1468)
                unwrapped1469 = deconstruct_result1468
                pretty_output(pp, unwrapped1469)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1713 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1713 = nothing
                end
                deconstruct_result1466 = _t1713
                if !isnothing(deconstruct_result1466)
                    unwrapped1467 = deconstruct_result1466
                    pretty_what_if(pp, unwrapped1467)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1714 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1714 = nothing
                    end
                    deconstruct_result1464 = _t1714
                    if !isnothing(deconstruct_result1464)
                        unwrapped1465 = deconstruct_result1464
                        pretty_abort(pp, unwrapped1465)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1715 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1715 = nothing
                        end
                        deconstruct_result1462 = _t1715
                        if !isnothing(deconstruct_result1462)
                            unwrapped1463 = deconstruct_result1462
                            pretty_export(pp, unwrapped1463)
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
    flat1475 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1475)
        write(pp, flat1475)
        return nothing
    else
        _dollar_dollar = msg
        fields1473 = _dollar_dollar.relation_id
        unwrapped_fields1474 = fields1473
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1474)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1480 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1480)
        write(pp, flat1480)
        return nothing
    else
        _dollar_dollar = msg
        fields1476 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1477 = fields1476
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1478 = unwrapped_fields1477[1]
        pretty_name(pp, field1478)
        newline(pp)
        field1479 = unwrapped_fields1477[2]
        pretty_relation_id(pp, field1479)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1485 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1485)
        write(pp, flat1485)
        return nothing
    else
        _dollar_dollar = msg
        fields1481 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1482 = fields1481
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1483 = unwrapped_fields1482[1]
        pretty_name(pp, field1483)
        newline(pp)
        field1484 = unwrapped_fields1482[2]
        pretty_epoch(pp, field1484)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1491 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1491)
        write(pp, flat1491)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1716 = _dollar_dollar.name
        else
            _t1716 = nothing
        end
        fields1486 = (_t1716, _dollar_dollar.relation_id,)
        unwrapped_fields1487 = fields1486
        write(pp, "(abort")
        indent_sexp!(pp)
        field1488 = unwrapped_fields1487[1]
        if !isnothing(field1488)
            newline(pp)
            opt_val1489 = field1488
            pretty_name(pp, opt_val1489)
        end
        newline(pp)
        field1490 = unwrapped_fields1487[2]
        pretty_relation_id(pp, field1490)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1496 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1496)
        write(pp, flat1496)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1717 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1717 = nothing
        end
        deconstruct_result1494 = _t1717
        if !isnothing(deconstruct_result1494)
            unwrapped1495 = deconstruct_result1494
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1495)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1718 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1718 = nothing
            end
            deconstruct_result1492 = _t1718
            if !isnothing(deconstruct_result1492)
                unwrapped1493 = deconstruct_result1492
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1493)
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
    flat1507 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1507)
        write(pp, flat1507)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1719 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1719 = nothing
        end
        deconstruct_result1502 = _t1719
        if !isnothing(deconstruct_result1502)
            unwrapped1503 = deconstruct_result1502
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1504 = unwrapped1503[1]
            pretty_export_csv_path(pp, field1504)
            newline(pp)
            field1505 = unwrapped1503[2]
            pretty_export_csv_source(pp, field1505)
            newline(pp)
            field1506 = unwrapped1503[3]
            pretty_csv_config(pp, field1506)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1721 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1720 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1721,)
            else
                _t1720 = nothing
            end
            deconstruct_result1497 = _t1720
            if !isnothing(deconstruct_result1497)
                unwrapped1498 = deconstruct_result1497
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1499 = unwrapped1498[1]
                pretty_export_csv_path(pp, field1499)
                newline(pp)
                field1500 = unwrapped1498[2]
                pretty_export_csv_columns_list(pp, field1500)
                newline(pp)
                field1501 = unwrapped1498[3]
                pretty_config_dict(pp, field1501)
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
    flat1509 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1509)
        write(pp, flat1509)
        return nothing
    else
        fields1508 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1508))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1516 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1516)
        write(pp, flat1516)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1722 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1722 = nothing
        end
        deconstruct_result1512 = _t1722
        if !isnothing(deconstruct_result1512)
            unwrapped1513 = deconstruct_result1512
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1513)
                newline(pp)
                for (i1723, elem1514) in enumerate(unwrapped1513)
                    i1515 = i1723 - 1
                    if (i1515 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1514)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1724 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1724 = nothing
            end
            deconstruct_result1510 = _t1724
            if !isnothing(deconstruct_result1510)
                unwrapped1511 = deconstruct_result1510
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1511)
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
    flat1521 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1521)
        write(pp, flat1521)
        return nothing
    else
        _dollar_dollar = msg
        fields1517 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1518 = fields1517
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1519 = unwrapped_fields1518[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1519))
        newline(pp)
        field1520 = unwrapped_fields1518[2]
        pretty_relation_id(pp, field1520)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1525 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1525)
        write(pp, flat1525)
        return nothing
    else
        fields1522 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1522)
            newline(pp)
            for (i1725, elem1523) in enumerate(fields1522)
                i1524 = i1725 - 1
                if (i1524 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1523)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1536 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1536)
        write(pp, flat1536)
        return nothing
    else
        _dollar_dollar = msg
        _t1726 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1526 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1726,)
        unwrapped_fields1527 = fields1526
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1528 = unwrapped_fields1527[1]
        pretty_iceberg_locator(pp, field1528)
        newline(pp)
        field1529 = unwrapped_fields1527[2]
        pretty_iceberg_catalog_config(pp, field1529)
        newline(pp)
        field1530 = unwrapped_fields1527[3]
        pretty_export_iceberg_columns(pp, field1530)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_properties")
        field1531 = unwrapped_fields1527[4]
        if !isempty(field1531)
            newline(pp)
            for (i1727, elem1532) in enumerate(field1531)
                i1533 = i1727 - 1
                if (i1533 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1532)
            end
        end
        dedent!(pp)
        write(pp, ")")
        field1534 = unwrapped_fields1527[5]
        if !isnothing(field1534)
            newline(pp)
            opt_val1535 = field1534
            pretty_config_dict(pp, opt_val1535)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_columns(pp::PrettyPrinter, msg::Proto.ExportIcebergColumns)
    flat1543 = try_flat(pp, msg, pretty_export_iceberg_columns)
    if !isnothing(flat1543)
        write(pp, flat1543)
        return nothing
    else
        _dollar_dollar = msg
        fields1537 = (_dollar_dollar.source_table_def, _dollar_dollar.target_columns,)
        unwrapped_fields1538 = fields1537
        write(pp, "(columns")
        indent_sexp!(pp)
        newline(pp)
        field1539 = unwrapped_fields1538[1]
        pretty_relation_id(pp, field1539)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "target_columns")
        field1540 = unwrapped_fields1538[2]
        if !isempty(field1540)
            newline(pp)
            for (i1728, elem1541) in enumerate(field1540)
                i1542 = i1728 - 1
                if (i1542 > 0)
                    newline(pp)
                end
                pretty_export_iceberg_column(pp, elem1541)
            end
        end
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_column(pp::PrettyPrinter, msg::Proto.ExportIcebergColumn)
    flat1549 = try_flat(pp, msg, pretty_export_iceberg_column)
    if !isnothing(flat1549)
        write(pp, flat1549)
        return nothing
    else
        _dollar_dollar = msg
        fields1544 = (_dollar_dollar.name, _dollar_dollar.var"#type", _dollar_dollar.nullable,)
        unwrapped_fields1545 = fields1544
        write(pp, "(iceberg_column")
        indent_sexp!(pp)
        newline(pp)
        field1546 = unwrapped_fields1545[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1546))
        newline(pp)
        field1547 = unwrapped_fields1545[2]
        pretty_type(pp, field1547)
        newline(pp)
        field1548 = unwrapped_fields1545[3]
        pretty_boolean_value(pp, field1548)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1773, _rid) in enumerate(msg.ids)
        _idx = i1773 - 1
        newline(pp)
        write(pp, "(")
        _t1774 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1774)
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
    for (i1775, _elem) in enumerate(msg.keys)
        _idx = i1775 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1776, _elem) in enumerate(msg.values)
        _idx = i1776 - 1
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
    for (i1777, _elem) in enumerate(msg.columns)
        _idx = i1777 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportIcebergColumns) = pretty_export_iceberg_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportIcebergColumn) = pretty_export_iceberg_column(pp, x)
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
