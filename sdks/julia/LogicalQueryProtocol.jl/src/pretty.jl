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
    _t1721 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1721
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1722 = Proto.Value(value=OneOf(:int_value, v))
    return _t1722
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1723 = Proto.Value(value=OneOf(:float_value, v))
    return _t1723
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1724 = Proto.Value(value=OneOf(:string_value, v))
    return _t1724
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1725 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1725
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1726 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1726
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1727 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1727,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1728 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1728,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1729 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1729,))
            end
        end
    end
    _t1730 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1730,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1731 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1731,))
    _t1732 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1732,))
    if msg.new_line != ""
        _t1733 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1733,))
    end
    _t1734 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1734,))
    _t1735 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1735,))
    _t1736 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1736,))
    if msg.comment != ""
        _t1737 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1737,))
    end
    for missing_string in msg.missing_strings
        _t1738 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1738,))
    end
    _t1739 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1739,))
    _t1740 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1740,))
    _t1741 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1741,))
    if msg.partition_size_mb != 0
        _t1742 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1742,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1743 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1743,))
    _t1744 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1744,))
    _t1745 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1745,))
    _t1746 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1746,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1747 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1747,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1748 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1748,))
        end
    end
    _t1749 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1749,))
    _t1750 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1750,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1751 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1751,))
    end
    if !isnothing(msg.compression)
        _t1752 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1752,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1753 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1753,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1754 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1754,))
    end
    if !isnothing(msg.syntax_delim)
        _t1755 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1755,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1756 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1756,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1757 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1757,))
    end
    return sort(result)
end

function deconstruct_iceberg_catalog_config_scope_optional(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)::Union{Nothing, String}
    if msg.scope != ""
        return msg.scope
    else
        _t1758 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1759 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1760 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1760,))
    end
    if msg.target_file_size_bytes != 0
        _t1761 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1761,))
    end
    if msg.compression != ""
        _t1762 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1762,))
    end
    if length(result) == 0
        return nothing
    else
        _t1763 = nothing
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
        _t1764 = nothing
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
    flat780 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat780)
        write(pp, flat780)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1542 = _dollar_dollar.configure
        else
            _t1542 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1543 = _dollar_dollar.sync
        else
            _t1543 = nothing
        end
        fields771 = (_t1542, _t1543, _dollar_dollar.epochs,)
        unwrapped_fields772 = fields771
        write(pp, "(transaction")
        indent_sexp!(pp)
        field773 = unwrapped_fields772[1]
        if !isnothing(field773)
            newline(pp)
            opt_val774 = field773
            pretty_configure(pp, opt_val774)
        end
        field775 = unwrapped_fields772[2]
        if !isnothing(field775)
            newline(pp)
            opt_val776 = field775
            pretty_sync(pp, opt_val776)
        end
        field777 = unwrapped_fields772[3]
        if !isempty(field777)
            newline(pp)
            for (i1544, elem778) in enumerate(field777)
                i779 = i1544 - 1
                if (i779 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem778)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat783 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat783)
        write(pp, flat783)
        return nothing
    else
        _dollar_dollar = msg
        _t1545 = deconstruct_configure(pp, _dollar_dollar)
        fields781 = _t1545
        unwrapped_fields782 = fields781
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields782)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat787 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat787)
        write(pp, flat787)
        return nothing
    else
        fields784 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields784)
            newline(pp)
            for (i1546, elem785) in enumerate(fields784)
                i786 = i1546 - 1
                if (i786 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem785)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat792 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat792)
        write(pp, flat792)
        return nothing
    else
        _dollar_dollar = msg
        fields788 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields789 = fields788
        write(pp, ":")
        field790 = unwrapped_fields789[1]
        write(pp, field790)
        write(pp, " ")
        field791 = unwrapped_fields789[2]
        pretty_raw_value(pp, field791)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat818 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat818)
        write(pp, flat818)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1547 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1547 = nothing
        end
        deconstruct_result816 = _t1547
        if !isnothing(deconstruct_result816)
            unwrapped817 = deconstruct_result816
            pretty_raw_date(pp, unwrapped817)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1548 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1548 = nothing
            end
            deconstruct_result814 = _t1548
            if !isnothing(deconstruct_result814)
                unwrapped815 = deconstruct_result814
                pretty_raw_datetime(pp, unwrapped815)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1549 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1549 = nothing
                end
                deconstruct_result812 = _t1549
                if !isnothing(deconstruct_result812)
                    unwrapped813 = deconstruct_result812
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped813))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1550 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1550 = nothing
                    end
                    deconstruct_result810 = _t1550
                    if !isnothing(deconstruct_result810)
                        unwrapped811 = deconstruct_result810
                        write(pp, (string(Int64(unwrapped811)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1551 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1551 = nothing
                        end
                        deconstruct_result808 = _t1551
                        if !isnothing(deconstruct_result808)
                            unwrapped809 = deconstruct_result808
                            write(pp, string(unwrapped809))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1552 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1552 = nothing
                            end
                            deconstruct_result806 = _t1552
                            if !isnothing(deconstruct_result806)
                                unwrapped807 = deconstruct_result806
                                write(pp, format_float32_literal(unwrapped807))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1553 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1553 = nothing
                                end
                                deconstruct_result804 = _t1553
                                if !isnothing(deconstruct_result804)
                                    unwrapped805 = deconstruct_result804
                                    write(pp, lowercase(string(unwrapped805)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1554 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1554 = nothing
                                    end
                                    deconstruct_result802 = _t1554
                                    if !isnothing(deconstruct_result802)
                                        unwrapped803 = deconstruct_result802
                                        write(pp, (string(Int64(unwrapped803)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1555 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1555 = nothing
                                        end
                                        deconstruct_result800 = _t1555
                                        if !isnothing(deconstruct_result800)
                                            unwrapped801 = deconstruct_result800
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped801))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1556 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1556 = nothing
                                            end
                                            deconstruct_result798 = _t1556
                                            if !isnothing(deconstruct_result798)
                                                unwrapped799 = deconstruct_result798
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped799))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1557 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1557 = nothing
                                                end
                                                deconstruct_result796 = _t1557
                                                if !isnothing(deconstruct_result796)
                                                    unwrapped797 = deconstruct_result796
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped797))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1558 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1558 = nothing
                                                    end
                                                    deconstruct_result794 = _t1558
                                                    if !isnothing(deconstruct_result794)
                                                        unwrapped795 = deconstruct_result794
                                                        pretty_boolean_value(pp, unwrapped795)
                                                    else
                                                        fields793 = msg
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
    flat824 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat824)
        write(pp, flat824)
        return nothing
    else
        _dollar_dollar = msg
        fields819 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields820 = fields819
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field821 = unwrapped_fields820[1]
        write(pp, string(field821))
        newline(pp)
        field822 = unwrapped_fields820[2]
        write(pp, string(field822))
        newline(pp)
        field823 = unwrapped_fields820[3]
        write(pp, string(field823))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat835 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat835)
        write(pp, flat835)
        return nothing
    else
        _dollar_dollar = msg
        fields825 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields826 = fields825
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field827 = unwrapped_fields826[1]
        write(pp, string(field827))
        newline(pp)
        field828 = unwrapped_fields826[2]
        write(pp, string(field828))
        newline(pp)
        field829 = unwrapped_fields826[3]
        write(pp, string(field829))
        newline(pp)
        field830 = unwrapped_fields826[4]
        write(pp, string(field830))
        newline(pp)
        field831 = unwrapped_fields826[5]
        write(pp, string(field831))
        newline(pp)
        field832 = unwrapped_fields826[6]
        write(pp, string(field832))
        field833 = unwrapped_fields826[7]
        if !isnothing(field833)
            newline(pp)
            opt_val834 = field833
            write(pp, string(opt_val834))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1559 = ()
    else
        _t1559 = nothing
    end
    deconstruct_result838 = _t1559
    if !isnothing(deconstruct_result838)
        unwrapped839 = deconstruct_result838
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1560 = ()
        else
            _t1560 = nothing
        end
        deconstruct_result836 = _t1560
        if !isnothing(deconstruct_result836)
            unwrapped837 = deconstruct_result836
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat844 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat844)
        write(pp, flat844)
        return nothing
    else
        _dollar_dollar = msg
        fields840 = _dollar_dollar.fragments
        unwrapped_fields841 = fields840
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields841)
            newline(pp)
            for (i1561, elem842) in enumerate(unwrapped_fields841)
                i843 = i1561 - 1
                if (i843 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem842)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat847 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat847)
        write(pp, flat847)
        return nothing
    else
        _dollar_dollar = msg
        fields845 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields846 = fields845
        write(pp, ":")
        write(pp, unwrapped_fields846)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat854 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat854)
        write(pp, flat854)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1562 = _dollar_dollar.writes
        else
            _t1562 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1563 = _dollar_dollar.reads
        else
            _t1563 = nothing
        end
        fields848 = (_t1562, _t1563,)
        unwrapped_fields849 = fields848
        write(pp, "(epoch")
        indent_sexp!(pp)
        field850 = unwrapped_fields849[1]
        if !isnothing(field850)
            newline(pp)
            opt_val851 = field850
            pretty_epoch_writes(pp, opt_val851)
        end
        field852 = unwrapped_fields849[2]
        if !isnothing(field852)
            newline(pp)
            opt_val853 = field852
            pretty_epoch_reads(pp, opt_val853)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat858 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat858)
        write(pp, flat858)
        return nothing
    else
        fields855 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields855)
            newline(pp)
            for (i1564, elem856) in enumerate(fields855)
                i857 = i1564 - 1
                if (i857 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem856)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat867 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat867)
        write(pp, flat867)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1565 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1565 = nothing
        end
        deconstruct_result865 = _t1565
        if !isnothing(deconstruct_result865)
            unwrapped866 = deconstruct_result865
            pretty_define(pp, unwrapped866)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1566 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1566 = nothing
            end
            deconstruct_result863 = _t1566
            if !isnothing(deconstruct_result863)
                unwrapped864 = deconstruct_result863
                pretty_undefine(pp, unwrapped864)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1567 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1567 = nothing
                end
                deconstruct_result861 = _t1567
                if !isnothing(deconstruct_result861)
                    unwrapped862 = deconstruct_result861
                    pretty_context(pp, unwrapped862)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1568 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1568 = nothing
                    end
                    deconstruct_result859 = _t1568
                    if !isnothing(deconstruct_result859)
                        unwrapped860 = deconstruct_result859
                        pretty_snapshot(pp, unwrapped860)
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
    flat870 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat870)
        write(pp, flat870)
        return nothing
    else
        _dollar_dollar = msg
        fields868 = _dollar_dollar.fragment
        unwrapped_fields869 = fields868
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields869)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat877 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat877)
        write(pp, flat877)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields871 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields872 = fields871
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field873 = unwrapped_fields872[1]
        pretty_new_fragment_id(pp, field873)
        field874 = unwrapped_fields872[2]
        if !isempty(field874)
            newline(pp)
            for (i1569, elem875) in enumerate(field874)
                i876 = i1569 - 1
                if (i876 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem875)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat879 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat879)
        write(pp, flat879)
        return nothing
    else
        fields878 = msg
        pretty_fragment_id(pp, fields878)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat888 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat888)
        write(pp, flat888)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1570 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1570 = nothing
        end
        deconstruct_result886 = _t1570
        if !isnothing(deconstruct_result886)
            unwrapped887 = deconstruct_result886
            pretty_def(pp, unwrapped887)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1571 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1571 = nothing
            end
            deconstruct_result884 = _t1571
            if !isnothing(deconstruct_result884)
                unwrapped885 = deconstruct_result884
                pretty_algorithm(pp, unwrapped885)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1572 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1572 = nothing
                end
                deconstruct_result882 = _t1572
                if !isnothing(deconstruct_result882)
                    unwrapped883 = deconstruct_result882
                    pretty_constraint(pp, unwrapped883)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1573 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1573 = nothing
                    end
                    deconstruct_result880 = _t1573
                    if !isnothing(deconstruct_result880)
                        unwrapped881 = deconstruct_result880
                        pretty_data(pp, unwrapped881)
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
    flat895 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat895)
        write(pp, flat895)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1574 = _dollar_dollar.attrs
        else
            _t1574 = nothing
        end
        fields889 = (_dollar_dollar.name, _dollar_dollar.body, _t1574,)
        unwrapped_fields890 = fields889
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field891 = unwrapped_fields890[1]
        pretty_relation_id(pp, field891)
        newline(pp)
        field892 = unwrapped_fields890[2]
        pretty_abstraction(pp, field892)
        field893 = unwrapped_fields890[3]
        if !isnothing(field893)
            newline(pp)
            opt_val894 = field893
            pretty_attrs(pp, opt_val894)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat900 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat900)
        write(pp, flat900)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1576 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1575 = _t1576
        else
            _t1575 = nothing
        end
        deconstruct_result898 = _t1575
        if !isnothing(deconstruct_result898)
            unwrapped899 = deconstruct_result898
            write(pp, ":")
            write(pp, unwrapped899)
        else
            _dollar_dollar = msg
            _t1577 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result896 = _t1577
            if !isnothing(deconstruct_result896)
                unwrapped897 = deconstruct_result896
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped897))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat905 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat905)
        write(pp, flat905)
        return nothing
    else
        _dollar_dollar = msg
        _t1578 = deconstruct_bindings(pp, _dollar_dollar)
        fields901 = (_t1578, _dollar_dollar.value,)
        unwrapped_fields902 = fields901
        write(pp, "(")
        indent!(pp)
        field903 = unwrapped_fields902[1]
        pretty_bindings(pp, field903)
        newline(pp)
        field904 = unwrapped_fields902[2]
        pretty_formula(pp, field904)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat913 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat913)
        write(pp, flat913)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1579 = _dollar_dollar[2]
        else
            _t1579 = nothing
        end
        fields906 = (_dollar_dollar[1], _t1579,)
        unwrapped_fields907 = fields906
        write(pp, "[")
        indent!(pp)
        field908 = unwrapped_fields907[1]
        for (i1580, elem909) in enumerate(field908)
            i910 = i1580 - 1
            if (i910 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem909)
        end
        field911 = unwrapped_fields907[2]
        if !isnothing(field911)
            newline(pp)
            opt_val912 = field911
            pretty_value_bindings(pp, opt_val912)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat918 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat918)
        write(pp, flat918)
        return nothing
    else
        _dollar_dollar = msg
        fields914 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields915 = fields914
        field916 = unwrapped_fields915[1]
        write(pp, field916)
        write(pp, "::")
        field917 = unwrapped_fields915[2]
        pretty_type(pp, field917)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat947 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat947)
        write(pp, flat947)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1581 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1581 = nothing
        end
        deconstruct_result945 = _t1581
        if !isnothing(deconstruct_result945)
            unwrapped946 = deconstruct_result945
            pretty_unspecified_type(pp, unwrapped946)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1582 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1582 = nothing
            end
            deconstruct_result943 = _t1582
            if !isnothing(deconstruct_result943)
                unwrapped944 = deconstruct_result943
                pretty_string_type(pp, unwrapped944)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1583 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1583 = nothing
                end
                deconstruct_result941 = _t1583
                if !isnothing(deconstruct_result941)
                    unwrapped942 = deconstruct_result941
                    pretty_int_type(pp, unwrapped942)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1584 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1584 = nothing
                    end
                    deconstruct_result939 = _t1584
                    if !isnothing(deconstruct_result939)
                        unwrapped940 = deconstruct_result939
                        pretty_float_type(pp, unwrapped940)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1585 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1585 = nothing
                        end
                        deconstruct_result937 = _t1585
                        if !isnothing(deconstruct_result937)
                            unwrapped938 = deconstruct_result937
                            pretty_uint128_type(pp, unwrapped938)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1586 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1586 = nothing
                            end
                            deconstruct_result935 = _t1586
                            if !isnothing(deconstruct_result935)
                                unwrapped936 = deconstruct_result935
                                pretty_int128_type(pp, unwrapped936)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1587 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1587 = nothing
                                end
                                deconstruct_result933 = _t1587
                                if !isnothing(deconstruct_result933)
                                    unwrapped934 = deconstruct_result933
                                    pretty_date_type(pp, unwrapped934)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1588 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1588 = nothing
                                    end
                                    deconstruct_result931 = _t1588
                                    if !isnothing(deconstruct_result931)
                                        unwrapped932 = deconstruct_result931
                                        pretty_datetime_type(pp, unwrapped932)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1589 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1589 = nothing
                                        end
                                        deconstruct_result929 = _t1589
                                        if !isnothing(deconstruct_result929)
                                            unwrapped930 = deconstruct_result929
                                            pretty_missing_type(pp, unwrapped930)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1590 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1590 = nothing
                                            end
                                            deconstruct_result927 = _t1590
                                            if !isnothing(deconstruct_result927)
                                                unwrapped928 = deconstruct_result927
                                                pretty_decimal_type(pp, unwrapped928)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1591 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1591 = nothing
                                                end
                                                deconstruct_result925 = _t1591
                                                if !isnothing(deconstruct_result925)
                                                    unwrapped926 = deconstruct_result925
                                                    pretty_boolean_type(pp, unwrapped926)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1592 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1592 = nothing
                                                    end
                                                    deconstruct_result923 = _t1592
                                                    if !isnothing(deconstruct_result923)
                                                        unwrapped924 = deconstruct_result923
                                                        pretty_int32_type(pp, unwrapped924)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1593 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1593 = nothing
                                                        end
                                                        deconstruct_result921 = _t1593
                                                        if !isnothing(deconstruct_result921)
                                                            unwrapped922 = deconstruct_result921
                                                            pretty_float32_type(pp, unwrapped922)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1594 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1594 = nothing
                                                            end
                                                            deconstruct_result919 = _t1594
                                                            if !isnothing(deconstruct_result919)
                                                                unwrapped920 = deconstruct_result919
                                                                pretty_uint32_type(pp, unwrapped920)
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
    fields948 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields949 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields950 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields951 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields952 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields953 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields954 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields955 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields956 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat961 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat961)
        write(pp, flat961)
        return nothing
    else
        _dollar_dollar = msg
        fields957 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields958 = fields957
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field959 = unwrapped_fields958[1]
        write(pp, string(field959))
        newline(pp)
        field960 = unwrapped_fields958[2]
        write(pp, string(field960))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields962 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields963 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields964 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields965 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat969 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat969)
        write(pp, flat969)
        return nothing
    else
        fields966 = msg
        write(pp, "|")
        if !isempty(fields966)
            write(pp, " ")
            for (i1595, elem967) in enumerate(fields966)
                i968 = i1595 - 1
                if (i968 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem967)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat996 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat996)
        write(pp, flat996)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1596 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1596 = nothing
        end
        deconstruct_result994 = _t1596
        if !isnothing(deconstruct_result994)
            unwrapped995 = deconstruct_result994
            pretty_true(pp, unwrapped995)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1597 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1597 = nothing
            end
            deconstruct_result992 = _t1597
            if !isnothing(deconstruct_result992)
                unwrapped993 = deconstruct_result992
                pretty_false(pp, unwrapped993)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1598 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1598 = nothing
                end
                deconstruct_result990 = _t1598
                if !isnothing(deconstruct_result990)
                    unwrapped991 = deconstruct_result990
                    pretty_exists(pp, unwrapped991)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1599 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1599 = nothing
                    end
                    deconstruct_result988 = _t1599
                    if !isnothing(deconstruct_result988)
                        unwrapped989 = deconstruct_result988
                        pretty_reduce(pp, unwrapped989)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1600 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1600 = nothing
                        end
                        deconstruct_result986 = _t1600
                        if !isnothing(deconstruct_result986)
                            unwrapped987 = deconstruct_result986
                            pretty_conjunction(pp, unwrapped987)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1601 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1601 = nothing
                            end
                            deconstruct_result984 = _t1601
                            if !isnothing(deconstruct_result984)
                                unwrapped985 = deconstruct_result984
                                pretty_disjunction(pp, unwrapped985)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1602 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1602 = nothing
                                end
                                deconstruct_result982 = _t1602
                                if !isnothing(deconstruct_result982)
                                    unwrapped983 = deconstruct_result982
                                    pretty_not(pp, unwrapped983)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1603 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1603 = nothing
                                    end
                                    deconstruct_result980 = _t1603
                                    if !isnothing(deconstruct_result980)
                                        unwrapped981 = deconstruct_result980
                                        pretty_ffi(pp, unwrapped981)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1604 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1604 = nothing
                                        end
                                        deconstruct_result978 = _t1604
                                        if !isnothing(deconstruct_result978)
                                            unwrapped979 = deconstruct_result978
                                            pretty_atom(pp, unwrapped979)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1605 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1605 = nothing
                                            end
                                            deconstruct_result976 = _t1605
                                            if !isnothing(deconstruct_result976)
                                                unwrapped977 = deconstruct_result976
                                                pretty_pragma(pp, unwrapped977)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1606 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1606 = nothing
                                                end
                                                deconstruct_result974 = _t1606
                                                if !isnothing(deconstruct_result974)
                                                    unwrapped975 = deconstruct_result974
                                                    pretty_primitive(pp, unwrapped975)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1607 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1607 = nothing
                                                    end
                                                    deconstruct_result972 = _t1607
                                                    if !isnothing(deconstruct_result972)
                                                        unwrapped973 = deconstruct_result972
                                                        pretty_rel_atom(pp, unwrapped973)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1608 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1608 = nothing
                                                        end
                                                        deconstruct_result970 = _t1608
                                                        if !isnothing(deconstruct_result970)
                                                            unwrapped971 = deconstruct_result970
                                                            pretty_cast(pp, unwrapped971)
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
    fields997 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields998 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1003 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1003)
        write(pp, flat1003)
        return nothing
    else
        _dollar_dollar = msg
        _t1609 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields999 = (_t1609, _dollar_dollar.body.value,)
        unwrapped_fields1000 = fields999
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1001 = unwrapped_fields1000[1]
        pretty_bindings(pp, field1001)
        newline(pp)
        field1002 = unwrapped_fields1000[2]
        pretty_formula(pp, field1002)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1009 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1009)
        write(pp, flat1009)
        return nothing
    else
        _dollar_dollar = msg
        fields1004 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1005 = fields1004
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1006 = unwrapped_fields1005[1]
        pretty_abstraction(pp, field1006)
        newline(pp)
        field1007 = unwrapped_fields1005[2]
        pretty_abstraction(pp, field1007)
        newline(pp)
        field1008 = unwrapped_fields1005[3]
        pretty_terms(pp, field1008)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1013 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1013)
        write(pp, flat1013)
        return nothing
    else
        fields1010 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1010)
            newline(pp)
            for (i1610, elem1011) in enumerate(fields1010)
                i1012 = i1610 - 1
                if (i1012 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1011)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1018 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1018)
        write(pp, flat1018)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1611 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1611 = nothing
        end
        deconstruct_result1016 = _t1611
        if !isnothing(deconstruct_result1016)
            unwrapped1017 = deconstruct_result1016
            pretty_var(pp, unwrapped1017)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1612 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1612 = nothing
            end
            deconstruct_result1014 = _t1612
            if !isnothing(deconstruct_result1014)
                unwrapped1015 = deconstruct_result1014
                pretty_value(pp, unwrapped1015)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1021 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1021)
        write(pp, flat1021)
        return nothing
    else
        _dollar_dollar = msg
        fields1019 = _dollar_dollar.name
        unwrapped_fields1020 = fields1019
        write(pp, unwrapped_fields1020)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1047 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1047)
        write(pp, flat1047)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1613 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1613 = nothing
        end
        deconstruct_result1045 = _t1613
        if !isnothing(deconstruct_result1045)
            unwrapped1046 = deconstruct_result1045
            pretty_date(pp, unwrapped1046)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1614 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1614 = nothing
            end
            deconstruct_result1043 = _t1614
            if !isnothing(deconstruct_result1043)
                unwrapped1044 = deconstruct_result1043
                pretty_datetime(pp, unwrapped1044)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1615 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1615 = nothing
                end
                deconstruct_result1041 = _t1615
                if !isnothing(deconstruct_result1041)
                    unwrapped1042 = deconstruct_result1041
                    write(pp, format_string(pp, unwrapped1042))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1616 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1616 = nothing
                    end
                    deconstruct_result1039 = _t1616
                    if !isnothing(deconstruct_result1039)
                        unwrapped1040 = deconstruct_result1039
                        write(pp, format_int32(pp, unwrapped1040))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1617 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1617 = nothing
                        end
                        deconstruct_result1037 = _t1617
                        if !isnothing(deconstruct_result1037)
                            unwrapped1038 = deconstruct_result1037
                            write(pp, format_int(pp, unwrapped1038))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1618 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1618 = nothing
                            end
                            deconstruct_result1035 = _t1618
                            if !isnothing(deconstruct_result1035)
                                unwrapped1036 = deconstruct_result1035
                                write(pp, format_float32(pp, unwrapped1036))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1619 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1619 = nothing
                                end
                                deconstruct_result1033 = _t1619
                                if !isnothing(deconstruct_result1033)
                                    unwrapped1034 = deconstruct_result1033
                                    write(pp, format_float(pp, unwrapped1034))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1620 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1620 = nothing
                                    end
                                    deconstruct_result1031 = _t1620
                                    if !isnothing(deconstruct_result1031)
                                        unwrapped1032 = deconstruct_result1031
                                        write(pp, format_uint32(pp, unwrapped1032))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1621 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1621 = nothing
                                        end
                                        deconstruct_result1029 = _t1621
                                        if !isnothing(deconstruct_result1029)
                                            unwrapped1030 = deconstruct_result1029
                                            write(pp, format_uint128(pp, unwrapped1030))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1622 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1622 = nothing
                                            end
                                            deconstruct_result1027 = _t1622
                                            if !isnothing(deconstruct_result1027)
                                                unwrapped1028 = deconstruct_result1027
                                                write(pp, format_int128(pp, unwrapped1028))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1623 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1623 = nothing
                                                end
                                                deconstruct_result1025 = _t1623
                                                if !isnothing(deconstruct_result1025)
                                                    unwrapped1026 = deconstruct_result1025
                                                    write(pp, format_decimal(pp, unwrapped1026))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1624 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1624 = nothing
                                                    end
                                                    deconstruct_result1023 = _t1624
                                                    if !isnothing(deconstruct_result1023)
                                                        unwrapped1024 = deconstruct_result1023
                                                        pretty_boolean_value(pp, unwrapped1024)
                                                    else
                                                        fields1022 = msg
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
    flat1053 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1053)
        write(pp, flat1053)
        return nothing
    else
        _dollar_dollar = msg
        fields1048 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1049 = fields1048
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1050 = unwrapped_fields1049[1]
        write(pp, format_int(pp, field1050))
        newline(pp)
        field1051 = unwrapped_fields1049[2]
        write(pp, format_int(pp, field1051))
        newline(pp)
        field1052 = unwrapped_fields1049[3]
        write(pp, format_int(pp, field1052))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1064 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1064)
        write(pp, flat1064)
        return nothing
    else
        _dollar_dollar = msg
        fields1054 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1055 = fields1054
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1056 = unwrapped_fields1055[1]
        write(pp, format_int(pp, field1056))
        newline(pp)
        field1057 = unwrapped_fields1055[2]
        write(pp, format_int(pp, field1057))
        newline(pp)
        field1058 = unwrapped_fields1055[3]
        write(pp, format_int(pp, field1058))
        newline(pp)
        field1059 = unwrapped_fields1055[4]
        write(pp, format_int(pp, field1059))
        newline(pp)
        field1060 = unwrapped_fields1055[5]
        write(pp, format_int(pp, field1060))
        newline(pp)
        field1061 = unwrapped_fields1055[6]
        write(pp, format_int(pp, field1061))
        field1062 = unwrapped_fields1055[7]
        if !isnothing(field1062)
            newline(pp)
            opt_val1063 = field1062
            write(pp, format_int(pp, opt_val1063))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1069 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1069)
        write(pp, flat1069)
        return nothing
    else
        _dollar_dollar = msg
        fields1065 = _dollar_dollar.args
        unwrapped_fields1066 = fields1065
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1066)
            newline(pp)
            for (i1625, elem1067) in enumerate(unwrapped_fields1066)
                i1068 = i1625 - 1
                if (i1068 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1067)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1074 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1074)
        write(pp, flat1074)
        return nothing
    else
        _dollar_dollar = msg
        fields1070 = _dollar_dollar.args
        unwrapped_fields1071 = fields1070
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1071)
            newline(pp)
            for (i1626, elem1072) in enumerate(unwrapped_fields1071)
                i1073 = i1626 - 1
                if (i1073 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1072)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1077 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1077)
        write(pp, flat1077)
        return nothing
    else
        _dollar_dollar = msg
        fields1075 = _dollar_dollar.arg
        unwrapped_fields1076 = fields1075
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1076)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1083 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1083)
        write(pp, flat1083)
        return nothing
    else
        _dollar_dollar = msg
        fields1078 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1079 = fields1078
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1080 = unwrapped_fields1079[1]
        pretty_name(pp, field1080)
        newline(pp)
        field1081 = unwrapped_fields1079[2]
        pretty_ffi_args(pp, field1081)
        newline(pp)
        field1082 = unwrapped_fields1079[3]
        pretty_terms(pp, field1082)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1085 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1085)
        write(pp, flat1085)
        return nothing
    else
        fields1084 = msg
        write(pp, ":")
        write(pp, fields1084)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1089 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1089)
        write(pp, flat1089)
        return nothing
    else
        fields1086 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1086)
            newline(pp)
            for (i1627, elem1087) in enumerate(fields1086)
                i1088 = i1627 - 1
                if (i1088 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1087)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1096 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        _dollar_dollar = msg
        fields1090 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1091 = fields1090
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1092 = unwrapped_fields1091[1]
        pretty_relation_id(pp, field1092)
        field1093 = unwrapped_fields1091[2]
        if !isempty(field1093)
            newline(pp)
            for (i1628, elem1094) in enumerate(field1093)
                i1095 = i1628 - 1
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

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1103 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1103)
        write(pp, flat1103)
        return nothing
    else
        _dollar_dollar = msg
        fields1097 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1098 = fields1097
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1099 = unwrapped_fields1098[1]
        pretty_name(pp, field1099)
        field1100 = unwrapped_fields1098[2]
        if !isempty(field1100)
            newline(pp)
            for (i1629, elem1101) in enumerate(field1100)
                i1102 = i1629 - 1
                if (i1102 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1101)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1119 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1119)
        write(pp, flat1119)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1630 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1630 = nothing
        end
        guard_result1118 = _t1630
        if !isnothing(guard_result1118)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1631 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1631 = nothing
            end
            guard_result1117 = _t1631
            if !isnothing(guard_result1117)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1632 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1632 = nothing
                end
                guard_result1116 = _t1632
                if !isnothing(guard_result1116)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1633 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1633 = nothing
                    end
                    guard_result1115 = _t1633
                    if !isnothing(guard_result1115)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1634 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1634 = nothing
                        end
                        guard_result1114 = _t1634
                        if !isnothing(guard_result1114)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1635 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1635 = nothing
                            end
                            guard_result1113 = _t1635
                            if !isnothing(guard_result1113)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1636 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1636 = nothing
                                end
                                guard_result1112 = _t1636
                                if !isnothing(guard_result1112)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1637 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1637 = nothing
                                    end
                                    guard_result1111 = _t1637
                                    if !isnothing(guard_result1111)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1638 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1638 = nothing
                                        end
                                        guard_result1110 = _t1638
                                        if !isnothing(guard_result1110)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1104 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1105 = fields1104
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1106 = unwrapped_fields1105[1]
                                            pretty_name(pp, field1106)
                                            field1107 = unwrapped_fields1105[2]
                                            if !isempty(field1107)
                                                newline(pp)
                                                for (i1639, elem1108) in enumerate(field1107)
                                                    i1109 = i1639 - 1
                                                    if (i1109 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1108)
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
    flat1124 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1124)
        write(pp, flat1124)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1640 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1640 = nothing
        end
        fields1120 = _t1640
        unwrapped_fields1121 = fields1120
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1122 = unwrapped_fields1121[1]
        pretty_term(pp, field1122)
        newline(pp)
        field1123 = unwrapped_fields1121[2]
        pretty_term(pp, field1123)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1129 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1129)
        write(pp, flat1129)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1641 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1641 = nothing
        end
        fields1125 = _t1641
        unwrapped_fields1126 = fields1125
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1127 = unwrapped_fields1126[1]
        pretty_term(pp, field1127)
        newline(pp)
        field1128 = unwrapped_fields1126[2]
        pretty_term(pp, field1128)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1134 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1134)
        write(pp, flat1134)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1642 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1642 = nothing
        end
        fields1130 = _t1642
        unwrapped_fields1131 = fields1130
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1132 = unwrapped_fields1131[1]
        pretty_term(pp, field1132)
        newline(pp)
        field1133 = unwrapped_fields1131[2]
        pretty_term(pp, field1133)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1139 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1139)
        write(pp, flat1139)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1643 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1643 = nothing
        end
        fields1135 = _t1643
        unwrapped_fields1136 = fields1135
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1137 = unwrapped_fields1136[1]
        pretty_term(pp, field1137)
        newline(pp)
        field1138 = unwrapped_fields1136[2]
        pretty_term(pp, field1138)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1144 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1144)
        write(pp, flat1144)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1644 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1644 = nothing
        end
        fields1140 = _t1644
        unwrapped_fields1141 = fields1140
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1142 = unwrapped_fields1141[1]
        pretty_term(pp, field1142)
        newline(pp)
        field1143 = unwrapped_fields1141[2]
        pretty_term(pp, field1143)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1150 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1150)
        write(pp, flat1150)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1645 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1645 = nothing
        end
        fields1145 = _t1645
        unwrapped_fields1146 = fields1145
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1147 = unwrapped_fields1146[1]
        pretty_term(pp, field1147)
        newline(pp)
        field1148 = unwrapped_fields1146[2]
        pretty_term(pp, field1148)
        newline(pp)
        field1149 = unwrapped_fields1146[3]
        pretty_term(pp, field1149)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1156 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1156)
        write(pp, flat1156)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1646 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1646 = nothing
        end
        fields1151 = _t1646
        unwrapped_fields1152 = fields1151
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1153 = unwrapped_fields1152[1]
        pretty_term(pp, field1153)
        newline(pp)
        field1154 = unwrapped_fields1152[2]
        pretty_term(pp, field1154)
        newline(pp)
        field1155 = unwrapped_fields1152[3]
        pretty_term(pp, field1155)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1162 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1162)
        write(pp, flat1162)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1647 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1647 = nothing
        end
        fields1157 = _t1647
        unwrapped_fields1158 = fields1157
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1159 = unwrapped_fields1158[1]
        pretty_term(pp, field1159)
        newline(pp)
        field1160 = unwrapped_fields1158[2]
        pretty_term(pp, field1160)
        newline(pp)
        field1161 = unwrapped_fields1158[3]
        pretty_term(pp, field1161)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1168 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1168)
        write(pp, flat1168)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1648 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1648 = nothing
        end
        fields1163 = _t1648
        unwrapped_fields1164 = fields1163
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1165 = unwrapped_fields1164[1]
        pretty_term(pp, field1165)
        newline(pp)
        field1166 = unwrapped_fields1164[2]
        pretty_term(pp, field1166)
        newline(pp)
        field1167 = unwrapped_fields1164[3]
        pretty_term(pp, field1167)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1173 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1173)
        write(pp, flat1173)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1649 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1649 = nothing
        end
        deconstruct_result1171 = _t1649
        if !isnothing(deconstruct_result1171)
            unwrapped1172 = deconstruct_result1171
            pretty_specialized_value(pp, unwrapped1172)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1650 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1650 = nothing
            end
            deconstruct_result1169 = _t1650
            if !isnothing(deconstruct_result1169)
                unwrapped1170 = deconstruct_result1169
                pretty_term(pp, unwrapped1170)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1175 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1175)
        write(pp, flat1175)
        return nothing
    else
        fields1174 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1174)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1182 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1182)
        write(pp, flat1182)
        return nothing
    else
        _dollar_dollar = msg
        fields1176 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1177 = fields1176
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1178 = unwrapped_fields1177[1]
        pretty_name(pp, field1178)
        field1179 = unwrapped_fields1177[2]
        if !isempty(field1179)
            newline(pp)
            for (i1651, elem1180) in enumerate(field1179)
                i1181 = i1651 - 1
                if (i1181 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1180)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1187 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1187)
        write(pp, flat1187)
        return nothing
    else
        _dollar_dollar = msg
        fields1183 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1184 = fields1183
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1185 = unwrapped_fields1184[1]
        pretty_term(pp, field1185)
        newline(pp)
        field1186 = unwrapped_fields1184[2]
        pretty_term(pp, field1186)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1191 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1191)
        write(pp, flat1191)
        return nothing
    else
        fields1188 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1188)
            newline(pp)
            for (i1652, elem1189) in enumerate(fields1188)
                i1190 = i1652 - 1
                if (i1190 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1189)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1198 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1198)
        write(pp, flat1198)
        return nothing
    else
        _dollar_dollar = msg
        fields1192 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1193 = fields1192
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1194 = unwrapped_fields1193[1]
        pretty_name(pp, field1194)
        field1195 = unwrapped_fields1193[2]
        if !isempty(field1195)
            newline(pp)
            for (i1653, elem1196) in enumerate(field1195)
                i1197 = i1653 - 1
                if (i1197 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1196)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1205 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1205)
        write(pp, flat1205)
        return nothing
    else
        _dollar_dollar = msg
        fields1199 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1200 = fields1199
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1201 = unwrapped_fields1200[1]
        if !isempty(field1201)
            newline(pp)
            for (i1654, elem1202) in enumerate(field1201)
                i1203 = i1654 - 1
                if (i1203 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1202)
            end
        end
        newline(pp)
        field1204 = unwrapped_fields1200[2]
        pretty_script(pp, field1204)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1210 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1210)
        write(pp, flat1210)
        return nothing
    else
        _dollar_dollar = msg
        fields1206 = _dollar_dollar.constructs
        unwrapped_fields1207 = fields1206
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1207)
            newline(pp)
            for (i1655, elem1208) in enumerate(unwrapped_fields1207)
                i1209 = i1655 - 1
                if (i1209 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1208)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1215 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1656 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1656 = nothing
        end
        deconstruct_result1213 = _t1656
        if !isnothing(deconstruct_result1213)
            unwrapped1214 = deconstruct_result1213
            pretty_loop(pp, unwrapped1214)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1657 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1657 = nothing
            end
            deconstruct_result1211 = _t1657
            if !isnothing(deconstruct_result1211)
                unwrapped1212 = deconstruct_result1211
                pretty_instruction(pp, unwrapped1212)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1220 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        _dollar_dollar = msg
        fields1216 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1217 = fields1216
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1218 = unwrapped_fields1217[1]
        pretty_init(pp, field1218)
        newline(pp)
        field1219 = unwrapped_fields1217[2]
        pretty_script(pp, field1219)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1224 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1224)
        write(pp, flat1224)
        return nothing
    else
        fields1221 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1221)
            newline(pp)
            for (i1658, elem1222) in enumerate(fields1221)
                i1223 = i1658 - 1
                if (i1223 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1222)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1235 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1235)
        write(pp, flat1235)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1659 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1659 = nothing
        end
        deconstruct_result1233 = _t1659
        if !isnothing(deconstruct_result1233)
            unwrapped1234 = deconstruct_result1233
            pretty_assign(pp, unwrapped1234)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1660 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1660 = nothing
            end
            deconstruct_result1231 = _t1660
            if !isnothing(deconstruct_result1231)
                unwrapped1232 = deconstruct_result1231
                pretty_upsert(pp, unwrapped1232)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1661 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1661 = nothing
                end
                deconstruct_result1229 = _t1661
                if !isnothing(deconstruct_result1229)
                    unwrapped1230 = deconstruct_result1229
                    pretty_break(pp, unwrapped1230)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1662 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1662 = nothing
                    end
                    deconstruct_result1227 = _t1662
                    if !isnothing(deconstruct_result1227)
                        unwrapped1228 = deconstruct_result1227
                        pretty_monoid_def(pp, unwrapped1228)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1663 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1663 = nothing
                        end
                        deconstruct_result1225 = _t1663
                        if !isnothing(deconstruct_result1225)
                            unwrapped1226 = deconstruct_result1225
                            pretty_monus_def(pp, unwrapped1226)
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
    flat1242 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1242)
        write(pp, flat1242)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1664 = _dollar_dollar.attrs
        else
            _t1664 = nothing
        end
        fields1236 = (_dollar_dollar.name, _dollar_dollar.body, _t1664,)
        unwrapped_fields1237 = fields1236
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1238 = unwrapped_fields1237[1]
        pretty_relation_id(pp, field1238)
        newline(pp)
        field1239 = unwrapped_fields1237[2]
        pretty_abstraction(pp, field1239)
        field1240 = unwrapped_fields1237[3]
        if !isnothing(field1240)
            newline(pp)
            opt_val1241 = field1240
            pretty_attrs(pp, opt_val1241)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1249 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1249)
        write(pp, flat1249)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1665 = _dollar_dollar.attrs
        else
            _t1665 = nothing
        end
        fields1243 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1665,)
        unwrapped_fields1244 = fields1243
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1245 = unwrapped_fields1244[1]
        pretty_relation_id(pp, field1245)
        newline(pp)
        field1246 = unwrapped_fields1244[2]
        pretty_abstraction_with_arity(pp, field1246)
        field1247 = unwrapped_fields1244[3]
        if !isnothing(field1247)
            newline(pp)
            opt_val1248 = field1247
            pretty_attrs(pp, opt_val1248)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1254 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1254)
        write(pp, flat1254)
        return nothing
    else
        _dollar_dollar = msg
        _t1666 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1250 = (_t1666, _dollar_dollar[1].value,)
        unwrapped_fields1251 = fields1250
        write(pp, "(")
        indent!(pp)
        field1252 = unwrapped_fields1251[1]
        pretty_bindings(pp, field1252)
        newline(pp)
        field1253 = unwrapped_fields1251[2]
        pretty_formula(pp, field1253)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1261 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1261)
        write(pp, flat1261)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1667 = _dollar_dollar.attrs
        else
            _t1667 = nothing
        end
        fields1255 = (_dollar_dollar.name, _dollar_dollar.body, _t1667,)
        unwrapped_fields1256 = fields1255
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1257 = unwrapped_fields1256[1]
        pretty_relation_id(pp, field1257)
        newline(pp)
        field1258 = unwrapped_fields1256[2]
        pretty_abstraction(pp, field1258)
        field1259 = unwrapped_fields1256[3]
        if !isnothing(field1259)
            newline(pp)
            opt_val1260 = field1259
            pretty_attrs(pp, opt_val1260)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1269 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1269)
        write(pp, flat1269)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1668 = _dollar_dollar.attrs
        else
            _t1668 = nothing
        end
        fields1262 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1668,)
        unwrapped_fields1263 = fields1262
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1264 = unwrapped_fields1263[1]
        pretty_monoid(pp, field1264)
        newline(pp)
        field1265 = unwrapped_fields1263[2]
        pretty_relation_id(pp, field1265)
        newline(pp)
        field1266 = unwrapped_fields1263[3]
        pretty_abstraction_with_arity(pp, field1266)
        field1267 = unwrapped_fields1263[4]
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

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1278 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1278)
        write(pp, flat1278)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1669 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1669 = nothing
        end
        deconstruct_result1276 = _t1669
        if !isnothing(deconstruct_result1276)
            unwrapped1277 = deconstruct_result1276
            pretty_or_monoid(pp, unwrapped1277)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1670 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1670 = nothing
            end
            deconstruct_result1274 = _t1670
            if !isnothing(deconstruct_result1274)
                unwrapped1275 = deconstruct_result1274
                pretty_min_monoid(pp, unwrapped1275)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1671 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1671 = nothing
                end
                deconstruct_result1272 = _t1671
                if !isnothing(deconstruct_result1272)
                    unwrapped1273 = deconstruct_result1272
                    pretty_max_monoid(pp, unwrapped1273)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1672 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1672 = nothing
                    end
                    deconstruct_result1270 = _t1672
                    if !isnothing(deconstruct_result1270)
                        unwrapped1271 = deconstruct_result1270
                        pretty_sum_monoid(pp, unwrapped1271)
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
    fields1279 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1282 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1282)
        write(pp, flat1282)
        return nothing
    else
        _dollar_dollar = msg
        fields1280 = _dollar_dollar.var"#type"
        unwrapped_fields1281 = fields1280
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1281)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1285 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1285)
        write(pp, flat1285)
        return nothing
    else
        _dollar_dollar = msg
        fields1283 = _dollar_dollar.var"#type"
        unwrapped_fields1284 = fields1283
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1284)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1288 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1288)
        write(pp, flat1288)
        return nothing
    else
        _dollar_dollar = msg
        fields1286 = _dollar_dollar.var"#type"
        unwrapped_fields1287 = fields1286
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1287)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1296 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1296)
        write(pp, flat1296)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1673 = _dollar_dollar.attrs
        else
            _t1673 = nothing
        end
        fields1289 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1673,)
        unwrapped_fields1290 = fields1289
        write(pp, "(monus")
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

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1303 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1303)
        write(pp, flat1303)
        return nothing
    else
        _dollar_dollar = msg
        fields1297 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1298 = fields1297
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1299 = unwrapped_fields1298[1]
        pretty_relation_id(pp, field1299)
        newline(pp)
        field1300 = unwrapped_fields1298[2]
        pretty_abstraction(pp, field1300)
        newline(pp)
        field1301 = unwrapped_fields1298[3]
        pretty_functional_dependency_keys(pp, field1301)
        newline(pp)
        field1302 = unwrapped_fields1298[4]
        pretty_functional_dependency_values(pp, field1302)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1307 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1307)
        write(pp, flat1307)
        return nothing
    else
        fields1304 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1304)
            newline(pp)
            for (i1674, elem1305) in enumerate(fields1304)
                i1306 = i1674 - 1
                if (i1306 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1305)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1311 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1311)
        write(pp, flat1311)
        return nothing
    else
        fields1308 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1308)
            newline(pp)
            for (i1675, elem1309) in enumerate(fields1308)
                i1310 = i1675 - 1
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

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1320 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1320)
        write(pp, flat1320)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1676 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1676 = nothing
        end
        deconstruct_result1318 = _t1676
        if !isnothing(deconstruct_result1318)
            unwrapped1319 = deconstruct_result1318
            pretty_edb(pp, unwrapped1319)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1677 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1677 = nothing
            end
            deconstruct_result1316 = _t1677
            if !isnothing(deconstruct_result1316)
                unwrapped1317 = deconstruct_result1316
                pretty_betree_relation(pp, unwrapped1317)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1678 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1678 = nothing
                end
                deconstruct_result1314 = _t1678
                if !isnothing(deconstruct_result1314)
                    unwrapped1315 = deconstruct_result1314
                    pretty_csv_data(pp, unwrapped1315)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1679 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1679 = nothing
                    end
                    deconstruct_result1312 = _t1679
                    if !isnothing(deconstruct_result1312)
                        unwrapped1313 = deconstruct_result1312
                        pretty_iceberg_data(pp, unwrapped1313)
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
    flat1326 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1326)
        write(pp, flat1326)
        return nothing
    else
        _dollar_dollar = msg
        fields1321 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1322 = fields1321
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1323 = unwrapped_fields1322[1]
        pretty_relation_id(pp, field1323)
        newline(pp)
        field1324 = unwrapped_fields1322[2]
        pretty_edb_path(pp, field1324)
        newline(pp)
        field1325 = unwrapped_fields1322[3]
        pretty_edb_types(pp, field1325)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1330 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1330)
        write(pp, flat1330)
        return nothing
    else
        fields1327 = msg
        write(pp, "[")
        indent!(pp)
        for (i1680, elem1328) in enumerate(fields1327)
            i1329 = i1680 - 1
            if (i1329 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1328))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1334 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1334)
        write(pp, flat1334)
        return nothing
    else
        fields1331 = msg
        write(pp, "[")
        indent!(pp)
        for (i1681, elem1332) in enumerate(fields1331)
            i1333 = i1681 - 1
            if (i1333 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1332)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1339 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1339)
        write(pp, flat1339)
        return nothing
    else
        _dollar_dollar = msg
        fields1335 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1336 = fields1335
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1337 = unwrapped_fields1336[1]
        pretty_relation_id(pp, field1337)
        newline(pp)
        field1338 = unwrapped_fields1336[2]
        pretty_betree_info(pp, field1338)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1345 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1345)
        write(pp, flat1345)
        return nothing
    else
        _dollar_dollar = msg
        _t1682 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1340 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1682,)
        unwrapped_fields1341 = fields1340
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1342 = unwrapped_fields1341[1]
        pretty_betree_info_key_types(pp, field1342)
        newline(pp)
        field1343 = unwrapped_fields1341[2]
        pretty_betree_info_value_types(pp, field1343)
        newline(pp)
        field1344 = unwrapped_fields1341[3]
        pretty_config_dict(pp, field1344)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1349 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1349)
        write(pp, flat1349)
        return nothing
    else
        fields1346 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1346)
            newline(pp)
            for (i1683, elem1347) in enumerate(fields1346)
                i1348 = i1683 - 1
                if (i1348 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1347)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1353 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1353)
        write(pp, flat1353)
        return nothing
    else
        fields1350 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1350)
            newline(pp)
            for (i1684, elem1351) in enumerate(fields1350)
                i1352 = i1684 - 1
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

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1360 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1360)
        write(pp, flat1360)
        return nothing
    else
        _dollar_dollar = msg
        fields1354 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1355 = fields1354
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1356 = unwrapped_fields1355[1]
        pretty_csvlocator(pp, field1356)
        newline(pp)
        field1357 = unwrapped_fields1355[2]
        pretty_csv_config(pp, field1357)
        newline(pp)
        field1358 = unwrapped_fields1355[3]
        pretty_gnf_columns(pp, field1358)
        newline(pp)
        field1359 = unwrapped_fields1355[4]
        pretty_csv_asof(pp, field1359)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1367 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1367)
        write(pp, flat1367)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1685 = _dollar_dollar.paths
        else
            _t1685 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1686 = String(copy(_dollar_dollar.inline_data))
        else
            _t1686 = nothing
        end
        fields1361 = (_t1685, _t1686,)
        unwrapped_fields1362 = fields1361
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1363 = unwrapped_fields1362[1]
        if !isnothing(field1363)
            newline(pp)
            opt_val1364 = field1363
            pretty_csv_locator_paths(pp, opt_val1364)
        end
        field1365 = unwrapped_fields1362[2]
        if !isnothing(field1365)
            newline(pp)
            opt_val1366 = field1365
            pretty_csv_locator_inline_data(pp, opt_val1366)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1371 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1371)
        write(pp, flat1371)
        return nothing
    else
        fields1368 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1368)
            newline(pp)
            for (i1687, elem1369) in enumerate(fields1368)
                i1370 = i1687 - 1
                if (i1370 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1369))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1373 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1373)
        write(pp, flat1373)
        return nothing
    else
        fields1372 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1372))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1376 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        _dollar_dollar = msg
        _t1688 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1374 = _t1688
        unwrapped_fields1375 = fields1374
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1375)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1380 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1380)
        write(pp, flat1380)
        return nothing
    else
        fields1377 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1377)
            newline(pp)
            for (i1689, elem1378) in enumerate(fields1377)
                i1379 = i1689 - 1
                if (i1379 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1378)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1389 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1389)
        write(pp, flat1389)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1690 = _dollar_dollar.target_id
        else
            _t1690 = nothing
        end
        fields1381 = (_dollar_dollar.column_path, _t1690, _dollar_dollar.types,)
        unwrapped_fields1382 = fields1381
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1383 = unwrapped_fields1382[1]
        pretty_gnf_column_path(pp, field1383)
        field1384 = unwrapped_fields1382[2]
        if !isnothing(field1384)
            newline(pp)
            opt_val1385 = field1384
            pretty_relation_id(pp, opt_val1385)
        end
        newline(pp)
        write(pp, "[")
        field1386 = unwrapped_fields1382[3]
        for (i1691, elem1387) in enumerate(field1386)
            i1388 = i1691 - 1
            if (i1388 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1387)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1396 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1396)
        write(pp, flat1396)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1692 = _dollar_dollar[1]
        else
            _t1692 = nothing
        end
        deconstruct_result1394 = _t1692
        if !isnothing(deconstruct_result1394)
            unwrapped1395 = deconstruct_result1394
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1395))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1693 = _dollar_dollar
            else
                _t1693 = nothing
            end
            deconstruct_result1390 = _t1693
            if !isnothing(deconstruct_result1390)
                unwrapped1391 = deconstruct_result1390
                write(pp, "[")
                indent!(pp)
                for (i1694, elem1392) in enumerate(unwrapped1391)
                    i1393 = i1694 - 1
                    if (i1393 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1392))
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
    flat1398 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1398)
        write(pp, flat1398)
        return nothing
    else
        fields1397 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1397))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1406 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1406)
        write(pp, flat1406)
        return nothing
    else
        _dollar_dollar = msg
        _t1695 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1399 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1695,)
        unwrapped_fields1400 = fields1399
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1401 = unwrapped_fields1400[1]
        pretty_iceberg_locator(pp, field1401)
        newline(pp)
        field1402 = unwrapped_fields1400[2]
        pretty_iceberg_catalog_config(pp, field1402)
        newline(pp)
        field1403 = unwrapped_fields1400[3]
        pretty_gnf_columns(pp, field1403)
        field1404 = unwrapped_fields1400[4]
        if !isnothing(field1404)
            newline(pp)
            opt_val1405 = field1404
            pretty_iceberg_to_snapshot(pp, opt_val1405)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1414 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1414)
        write(pp, flat1414)
        return nothing
    else
        _dollar_dollar = msg
        fields1407 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1408 = fields1407
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_name")
        newline(pp)
        field1409 = unwrapped_fields1408[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1409))
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "namespace")
        field1410 = unwrapped_fields1408[2]
        if !isempty(field1410)
            newline(pp)
            for (i1696, elem1411) in enumerate(field1410)
                i1412 = i1696 - 1
                if (i1412 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1411))
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "warehouse")
        newline(pp)
        field1413 = unwrapped_fields1408[3]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1413))
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1426 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1426)
        write(pp, flat1426)
        return nothing
    else
        _dollar_dollar = msg
        _t1697 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1415 = (_dollar_dollar.catalog_uri, _t1697, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1416 = fields1415
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "catalog_uri")
        newline(pp)
        field1417 = unwrapped_fields1416[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1417))
        dedent!(pp)
        write(pp, ")")
        field1418 = unwrapped_fields1416[2]
        if !isnothing(field1418)
            newline(pp)
            opt_val1419 = field1418
            pretty_iceberg_catalog_config_scope(pp, opt_val1419)
        end
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "properties")
        field1420 = unwrapped_fields1416[3]
        if !isempty(field1420)
            newline(pp)
            for (i1698, elem1421) in enumerate(field1420)
                i1422 = i1698 - 1
                if (i1422 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1421)
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "auth_properties")
        field1423 = unwrapped_fields1416[4]
        if !isempty(field1423)
            newline(pp)
            for (i1699, elem1424) in enumerate(field1423)
                i1425 = i1699 - 1
                if (i1425 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1424)
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
    flat1428 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1428)
        write(pp, flat1428)
        return nothing
    else
        fields1427 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1427))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1433 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1433)
        write(pp, flat1433)
        return nothing
    else
        _dollar_dollar = msg
        fields1429 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1430 = fields1429
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1431 = unwrapped_fields1430[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1431))
        newline(pp)
        field1432 = unwrapped_fields1430[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1432))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1435 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1435)
        write(pp, flat1435)
        return nothing
    else
        fields1434 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1434))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1438 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1438)
        write(pp, flat1438)
        return nothing
    else
        _dollar_dollar = msg
        fields1436 = _dollar_dollar.fragment_id
        unwrapped_fields1437 = fields1436
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1437)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1443 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1443)
        write(pp, flat1443)
        return nothing
    else
        _dollar_dollar = msg
        fields1439 = _dollar_dollar.relations
        unwrapped_fields1440 = fields1439
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1440)
            newline(pp)
            for (i1700, elem1441) in enumerate(unwrapped_fields1440)
                i1442 = i1700 - 1
                if (i1442 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1441)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1448 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1448)
        write(pp, flat1448)
        return nothing
    else
        _dollar_dollar = msg
        fields1444 = _dollar_dollar.mappings
        unwrapped_fields1445 = fields1444
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1445)
            newline(pp)
            for (i1701, elem1446) in enumerate(unwrapped_fields1445)
                i1447 = i1701 - 1
                if (i1447 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1446)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1453 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1453)
        write(pp, flat1453)
        return nothing
    else
        _dollar_dollar = msg
        fields1449 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1450 = fields1449
        field1451 = unwrapped_fields1450[1]
        pretty_edb_path(pp, field1451)
        write(pp, " ")
        field1452 = unwrapped_fields1450[2]
        pretty_relation_id(pp, field1452)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1457 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1457)
        write(pp, flat1457)
        return nothing
    else
        fields1454 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1454)
            newline(pp)
            for (i1702, elem1455) in enumerate(fields1454)
                i1456 = i1702 - 1
                if (i1456 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1455)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1468 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1468)
        write(pp, flat1468)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1703 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1703 = nothing
        end
        deconstruct_result1466 = _t1703
        if !isnothing(deconstruct_result1466)
            unwrapped1467 = deconstruct_result1466
            pretty_demand(pp, unwrapped1467)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1704 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1704 = nothing
            end
            deconstruct_result1464 = _t1704
            if !isnothing(deconstruct_result1464)
                unwrapped1465 = deconstruct_result1464
                pretty_output(pp, unwrapped1465)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1705 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1705 = nothing
                end
                deconstruct_result1462 = _t1705
                if !isnothing(deconstruct_result1462)
                    unwrapped1463 = deconstruct_result1462
                    pretty_what_if(pp, unwrapped1463)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1706 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1706 = nothing
                    end
                    deconstruct_result1460 = _t1706
                    if !isnothing(deconstruct_result1460)
                        unwrapped1461 = deconstruct_result1460
                        pretty_abort(pp, unwrapped1461)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1707 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1707 = nothing
                        end
                        deconstruct_result1458 = _t1707
                        if !isnothing(deconstruct_result1458)
                            unwrapped1459 = deconstruct_result1458
                            pretty_export(pp, unwrapped1459)
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
    flat1471 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1471)
        write(pp, flat1471)
        return nothing
    else
        _dollar_dollar = msg
        fields1469 = _dollar_dollar.relation_id
        unwrapped_fields1470 = fields1469
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1470)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1476 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1476)
        write(pp, flat1476)
        return nothing
    else
        _dollar_dollar = msg
        fields1472 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1473 = fields1472
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1474 = unwrapped_fields1473[1]
        pretty_name(pp, field1474)
        newline(pp)
        field1475 = unwrapped_fields1473[2]
        pretty_relation_id(pp, field1475)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1481 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1481)
        write(pp, flat1481)
        return nothing
    else
        _dollar_dollar = msg
        fields1477 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1478 = fields1477
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1479 = unwrapped_fields1478[1]
        pretty_name(pp, field1479)
        newline(pp)
        field1480 = unwrapped_fields1478[2]
        pretty_epoch(pp, field1480)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1487 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1487)
        write(pp, flat1487)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1708 = _dollar_dollar.name
        else
            _t1708 = nothing
        end
        fields1482 = (_t1708, _dollar_dollar.relation_id,)
        unwrapped_fields1483 = fields1482
        write(pp, "(abort")
        indent_sexp!(pp)
        field1484 = unwrapped_fields1483[1]
        if !isnothing(field1484)
            newline(pp)
            opt_val1485 = field1484
            pretty_name(pp, opt_val1485)
        end
        newline(pp)
        field1486 = unwrapped_fields1483[2]
        pretty_relation_id(pp, field1486)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1492 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1492)
        write(pp, flat1492)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1709 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1709 = nothing
        end
        deconstruct_result1490 = _t1709
        if !isnothing(deconstruct_result1490)
            unwrapped1491 = deconstruct_result1490
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1491)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1710 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1710 = nothing
            end
            deconstruct_result1488 = _t1710
            if !isnothing(deconstruct_result1488)
                unwrapped1489 = deconstruct_result1488
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1489)
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
    flat1503 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1503)
        write(pp, flat1503)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1711 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1711 = nothing
        end
        deconstruct_result1498 = _t1711
        if !isnothing(deconstruct_result1498)
            unwrapped1499 = deconstruct_result1498
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1500 = unwrapped1499[1]
            pretty_export_csv_path(pp, field1500)
            newline(pp)
            field1501 = unwrapped1499[2]
            pretty_export_csv_source(pp, field1501)
            newline(pp)
            field1502 = unwrapped1499[3]
            pretty_csv_config(pp, field1502)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1713 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1712 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1713,)
            else
                _t1712 = nothing
            end
            deconstruct_result1493 = _t1712
            if !isnothing(deconstruct_result1493)
                unwrapped1494 = deconstruct_result1493
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1495 = unwrapped1494[1]
                pretty_export_csv_path(pp, field1495)
                newline(pp)
                field1496 = unwrapped1494[2]
                pretty_export_csv_columns_list(pp, field1496)
                newline(pp)
                field1497 = unwrapped1494[3]
                pretty_config_dict(pp, field1497)
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
    flat1505 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1505)
        write(pp, flat1505)
        return nothing
    else
        fields1504 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1504))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1512 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1512)
        write(pp, flat1512)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1714 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1714 = nothing
        end
        deconstruct_result1508 = _t1714
        if !isnothing(deconstruct_result1508)
            unwrapped1509 = deconstruct_result1508
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1509)
                newline(pp)
                for (i1715, elem1510) in enumerate(unwrapped1509)
                    i1511 = i1715 - 1
                    if (i1511 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1510)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1716 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1716 = nothing
            end
            deconstruct_result1506 = _t1716
            if !isnothing(deconstruct_result1506)
                unwrapped1507 = deconstruct_result1506
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1507)
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
    flat1517 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1517)
        write(pp, flat1517)
        return nothing
    else
        _dollar_dollar = msg
        fields1513 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1514 = fields1513
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1515 = unwrapped_fields1514[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1515))
        newline(pp)
        field1516 = unwrapped_fields1514[2]
        pretty_relation_id(pp, field1516)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1521 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1521)
        write(pp, flat1521)
        return nothing
    else
        fields1518 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1518)
            newline(pp)
            for (i1717, elem1519) in enumerate(fields1518)
                i1520 = i1717 - 1
                if (i1520 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1519)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1534 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1534)
        write(pp, flat1534)
        return nothing
    else
        _dollar_dollar = msg
        _t1718 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1522 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, sort([(k, v) for (k, v) in _dollar_dollar.create_table_properties]), _t1718,)
        unwrapped_fields1523 = fields1522
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1524 = unwrapped_fields1523[1]
        pretty_iceberg_locator(pp, field1524)
        newline(pp)
        field1525 = unwrapped_fields1523[2]
        pretty_iceberg_catalog_config(pp, field1525)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "columns")
        field1526 = unwrapped_fields1523[3]
        if !isempty(field1526)
            newline(pp)
            for (i1719, elem1527) in enumerate(field1526)
                i1528 = i1719 - 1
                if (i1528 > 0)
                    newline(pp)
                end
                pretty_iceberg_export_column(pp, elem1527)
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "create_table_properties")
        field1529 = unwrapped_fields1523[4]
        if !isempty(field1529)
            newline(pp)
            for (i1720, elem1530) in enumerate(field1529)
                i1531 = i1720 - 1
                if (i1531 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1530)
            end
        end
        dedent!(pp)
        write(pp, ")")
        field1532 = unwrapped_fields1523[5]
        if !isnothing(field1532)
            newline(pp)
            opt_val1533 = field1532
            pretty_config_dict(pp, opt_val1533)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_export_column(pp::PrettyPrinter, msg::Proto.ExportIcebergColumn)
    flat1541 = try_flat(pp, msg, pretty_iceberg_export_column)
    if !isnothing(flat1541)
        write(pp, flat1541)
        return nothing
    else
        _dollar_dollar = msg
        fields1535 = (_dollar_dollar.name, _dollar_dollar.column_data, _dollar_dollar.var"#type", _dollar_dollar.nullable,)
        unwrapped_fields1536 = fields1535
        write(pp, "(iceberg_column")
        indent_sexp!(pp)
        newline(pp)
        field1537 = unwrapped_fields1536[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1537))
        newline(pp)
        field1538 = unwrapped_fields1536[2]
        pretty_relation_id(pp, field1538)
        newline(pp)
        field1539 = unwrapped_fields1536[3]
        pretty_type(pp, field1539)
        newline(pp)
        field1540 = unwrapped_fields1536[4]
        pretty_boolean_value(pp, field1540)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1765, _rid) in enumerate(msg.ids)
        _idx = i1765 - 1
        newline(pp)
        write(pp, "(")
        _t1766 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1766)
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
    for (i1767, _elem) in enumerate(msg.keys)
        _idx = i1767 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1768, _elem) in enumerate(msg.values)
        _idx = i1768 - 1
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
    for (i1769, _elem) in enumerate(msg.columns)
        _idx = i1769 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportIcebergColumn) = pretty_iceberg_export_column(pp, x)
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
