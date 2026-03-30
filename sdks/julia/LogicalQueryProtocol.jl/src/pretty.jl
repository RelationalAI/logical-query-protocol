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
    _t1719 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1719
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1720 = Proto.Value(value=OneOf(:int_value, v))
    return _t1720
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1721 = Proto.Value(value=OneOf(:float_value, v))
    return _t1721
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1722 = Proto.Value(value=OneOf(:string_value, v))
    return _t1722
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1723 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1723
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1724 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1724
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1725 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1725,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1726 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1726,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1727 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1727,))
            end
        end
    end
    _t1728 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1728,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1729 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1729,))
    _t1730 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1730,))
    if msg.new_line != ""
        _t1731 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1731,))
    end
    _t1732 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1732,))
    _t1733 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1733,))
    _t1734 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1734,))
    if msg.comment != ""
        _t1735 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1735,))
    end
    for missing_string in msg.missing_strings
        _t1736 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1736,))
    end
    _t1737 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1737,))
    _t1738 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1738,))
    _t1739 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1739,))
    if msg.partition_size_mb != 0
        _t1740 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1740,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1741 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1741,))
    _t1742 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1742,))
    _t1743 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1743,))
    _t1744 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1744,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1745 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1745,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1746 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1746,))
        end
    end
    _t1747 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1747,))
    _t1748 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1748,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1749 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1749,))
    end
    if !isnothing(msg.compression)
        _t1750 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1750,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1751 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1751,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1752 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1752,))
    end
    if !isnothing(msg.syntax_delim)
        _t1753 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1753,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1754 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1754,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1755 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1755,))
    end
    return sort(result)
end

function deconstruct_iceberg_catalog_config_scope_optional(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)::Union{Nothing, String}
    if msg.scope != ""
        return msg.scope
    else
        _t1756 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1757 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1758 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1758,))
    end
    if msg.target_file_size_bytes != 0
        _t1759 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1759,))
    end
    if msg.compression != ""
        _t1760 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1760,))
    end
    if length(result) == 0
        return nothing
    else
        _t1761 = nothing
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
        _t1762 = nothing
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
    flat779 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat779)
        write(pp, flat779)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1540 = _dollar_dollar.configure
        else
            _t1540 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1541 = _dollar_dollar.sync
        else
            _t1541 = nothing
        end
        fields770 = (_t1540, _t1541, _dollar_dollar.epochs,)
        unwrapped_fields771 = fields770
        write(pp, "(transaction")
        indent_sexp!(pp)
        field772 = unwrapped_fields771[1]
        if !isnothing(field772)
            newline(pp)
            opt_val773 = field772
            pretty_configure(pp, opt_val773)
        end
        field774 = unwrapped_fields771[2]
        if !isnothing(field774)
            newline(pp)
            opt_val775 = field774
            pretty_sync(pp, opt_val775)
        end
        field776 = unwrapped_fields771[3]
        if !isempty(field776)
            newline(pp)
            for (i1542, elem777) in enumerate(field776)
                i778 = i1542 - 1
                if (i778 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem777)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat782 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat782)
        write(pp, flat782)
        return nothing
    else
        _dollar_dollar = msg
        _t1543 = deconstruct_configure(pp, _dollar_dollar)
        fields780 = _t1543
        unwrapped_fields781 = fields780
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields781)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat786 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat786)
        write(pp, flat786)
        return nothing
    else
        fields783 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields783)
            newline(pp)
            for (i1544, elem784) in enumerate(fields783)
                i785 = i1544 - 1
                if (i785 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem784)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat791 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat791)
        write(pp, flat791)
        return nothing
    else
        _dollar_dollar = msg
        fields787 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields788 = fields787
        write(pp, ":")
        field789 = unwrapped_fields788[1]
        write(pp, field789)
        write(pp, " ")
        field790 = unwrapped_fields788[2]
        pretty_raw_value(pp, field790)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat817 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat817)
        write(pp, flat817)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1545 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1545 = nothing
        end
        deconstruct_result815 = _t1545
        if !isnothing(deconstruct_result815)
            unwrapped816 = deconstruct_result815
            pretty_raw_date(pp, unwrapped816)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1546 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1546 = nothing
            end
            deconstruct_result813 = _t1546
            if !isnothing(deconstruct_result813)
                unwrapped814 = deconstruct_result813
                pretty_raw_datetime(pp, unwrapped814)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1547 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1547 = nothing
                end
                deconstruct_result811 = _t1547
                if !isnothing(deconstruct_result811)
                    unwrapped812 = deconstruct_result811
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped812))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1548 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1548 = nothing
                    end
                    deconstruct_result809 = _t1548
                    if !isnothing(deconstruct_result809)
                        unwrapped810 = deconstruct_result809
                        write(pp, (string(Int64(unwrapped810)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1549 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1549 = nothing
                        end
                        deconstruct_result807 = _t1549
                        if !isnothing(deconstruct_result807)
                            unwrapped808 = deconstruct_result807
                            write(pp, string(unwrapped808))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1550 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1550 = nothing
                            end
                            deconstruct_result805 = _t1550
                            if !isnothing(deconstruct_result805)
                                unwrapped806 = deconstruct_result805
                                write(pp, format_float32_literal(unwrapped806))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1551 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1551 = nothing
                                end
                                deconstruct_result803 = _t1551
                                if !isnothing(deconstruct_result803)
                                    unwrapped804 = deconstruct_result803
                                    write(pp, lowercase(string(unwrapped804)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1552 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1552 = nothing
                                    end
                                    deconstruct_result801 = _t1552
                                    if !isnothing(deconstruct_result801)
                                        unwrapped802 = deconstruct_result801
                                        write(pp, (string(Int64(unwrapped802)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1553 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1553 = nothing
                                        end
                                        deconstruct_result799 = _t1553
                                        if !isnothing(deconstruct_result799)
                                            unwrapped800 = deconstruct_result799
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped800))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1554 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1554 = nothing
                                            end
                                            deconstruct_result797 = _t1554
                                            if !isnothing(deconstruct_result797)
                                                unwrapped798 = deconstruct_result797
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped798))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1555 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1555 = nothing
                                                end
                                                deconstruct_result795 = _t1555
                                                if !isnothing(deconstruct_result795)
                                                    unwrapped796 = deconstruct_result795
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped796))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1556 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1556 = nothing
                                                    end
                                                    deconstruct_result793 = _t1556
                                                    if !isnothing(deconstruct_result793)
                                                        unwrapped794 = deconstruct_result793
                                                        pretty_boolean_value(pp, unwrapped794)
                                                    else
                                                        fields792 = msg
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
    flat823 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat823)
        write(pp, flat823)
        return nothing
    else
        _dollar_dollar = msg
        fields818 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields819 = fields818
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field820 = unwrapped_fields819[1]
        write(pp, string(field820))
        newline(pp)
        field821 = unwrapped_fields819[2]
        write(pp, string(field821))
        newline(pp)
        field822 = unwrapped_fields819[3]
        write(pp, string(field822))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat834 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat834)
        write(pp, flat834)
        return nothing
    else
        _dollar_dollar = msg
        fields824 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields825 = fields824
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field826 = unwrapped_fields825[1]
        write(pp, string(field826))
        newline(pp)
        field827 = unwrapped_fields825[2]
        write(pp, string(field827))
        newline(pp)
        field828 = unwrapped_fields825[3]
        write(pp, string(field828))
        newline(pp)
        field829 = unwrapped_fields825[4]
        write(pp, string(field829))
        newline(pp)
        field830 = unwrapped_fields825[5]
        write(pp, string(field830))
        newline(pp)
        field831 = unwrapped_fields825[6]
        write(pp, string(field831))
        field832 = unwrapped_fields825[7]
        if !isnothing(field832)
            newline(pp)
            opt_val833 = field832
            write(pp, string(opt_val833))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1557 = ()
    else
        _t1557 = nothing
    end
    deconstruct_result837 = _t1557
    if !isnothing(deconstruct_result837)
        unwrapped838 = deconstruct_result837
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1558 = ()
        else
            _t1558 = nothing
        end
        deconstruct_result835 = _t1558
        if !isnothing(deconstruct_result835)
            unwrapped836 = deconstruct_result835
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat843 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat843)
        write(pp, flat843)
        return nothing
    else
        _dollar_dollar = msg
        fields839 = _dollar_dollar.fragments
        unwrapped_fields840 = fields839
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields840)
            newline(pp)
            for (i1559, elem841) in enumerate(unwrapped_fields840)
                i842 = i1559 - 1
                if (i842 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem841)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat846 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat846)
        write(pp, flat846)
        return nothing
    else
        _dollar_dollar = msg
        fields844 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields845 = fields844
        write(pp, ":")
        write(pp, unwrapped_fields845)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat853 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat853)
        write(pp, flat853)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1560 = _dollar_dollar.writes
        else
            _t1560 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1561 = _dollar_dollar.reads
        else
            _t1561 = nothing
        end
        fields847 = (_t1560, _t1561,)
        unwrapped_fields848 = fields847
        write(pp, "(epoch")
        indent_sexp!(pp)
        field849 = unwrapped_fields848[1]
        if !isnothing(field849)
            newline(pp)
            opt_val850 = field849
            pretty_epoch_writes(pp, opt_val850)
        end
        field851 = unwrapped_fields848[2]
        if !isnothing(field851)
            newline(pp)
            opt_val852 = field851
            pretty_epoch_reads(pp, opt_val852)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat857 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat857)
        write(pp, flat857)
        return nothing
    else
        fields854 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields854)
            newline(pp)
            for (i1562, elem855) in enumerate(fields854)
                i856 = i1562 - 1
                if (i856 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem855)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat866 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat866)
        write(pp, flat866)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1563 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1563 = nothing
        end
        deconstruct_result864 = _t1563
        if !isnothing(deconstruct_result864)
            unwrapped865 = deconstruct_result864
            pretty_define(pp, unwrapped865)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1564 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1564 = nothing
            end
            deconstruct_result862 = _t1564
            if !isnothing(deconstruct_result862)
                unwrapped863 = deconstruct_result862
                pretty_undefine(pp, unwrapped863)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1565 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1565 = nothing
                end
                deconstruct_result860 = _t1565
                if !isnothing(deconstruct_result860)
                    unwrapped861 = deconstruct_result860
                    pretty_context(pp, unwrapped861)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1566 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1566 = nothing
                    end
                    deconstruct_result858 = _t1566
                    if !isnothing(deconstruct_result858)
                        unwrapped859 = deconstruct_result858
                        pretty_snapshot(pp, unwrapped859)
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
    flat869 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat869)
        write(pp, flat869)
        return nothing
    else
        _dollar_dollar = msg
        fields867 = _dollar_dollar.fragment
        unwrapped_fields868 = fields867
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields868)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat876 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat876)
        write(pp, flat876)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields870 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields871 = fields870
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field872 = unwrapped_fields871[1]
        pretty_new_fragment_id(pp, field872)
        field873 = unwrapped_fields871[2]
        if !isempty(field873)
            newline(pp)
            for (i1567, elem874) in enumerate(field873)
                i875 = i1567 - 1
                if (i875 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem874)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat878 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat878)
        write(pp, flat878)
        return nothing
    else
        fields877 = msg
        pretty_fragment_id(pp, fields877)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat887 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat887)
        write(pp, flat887)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1568 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1568 = nothing
        end
        deconstruct_result885 = _t1568
        if !isnothing(deconstruct_result885)
            unwrapped886 = deconstruct_result885
            pretty_def(pp, unwrapped886)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1569 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1569 = nothing
            end
            deconstruct_result883 = _t1569
            if !isnothing(deconstruct_result883)
                unwrapped884 = deconstruct_result883
                pretty_algorithm(pp, unwrapped884)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1570 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1570 = nothing
                end
                deconstruct_result881 = _t1570
                if !isnothing(deconstruct_result881)
                    unwrapped882 = deconstruct_result881
                    pretty_constraint(pp, unwrapped882)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1571 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1571 = nothing
                    end
                    deconstruct_result879 = _t1571
                    if !isnothing(deconstruct_result879)
                        unwrapped880 = deconstruct_result879
                        pretty_data(pp, unwrapped880)
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
    flat894 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat894)
        write(pp, flat894)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1572 = _dollar_dollar.attrs
        else
            _t1572 = nothing
        end
        fields888 = (_dollar_dollar.name, _dollar_dollar.body, _t1572,)
        unwrapped_fields889 = fields888
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field890 = unwrapped_fields889[1]
        pretty_relation_id(pp, field890)
        newline(pp)
        field891 = unwrapped_fields889[2]
        pretty_abstraction(pp, field891)
        field892 = unwrapped_fields889[3]
        if !isnothing(field892)
            newline(pp)
            opt_val893 = field892
            pretty_attrs(pp, opt_val893)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat899 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat899)
        write(pp, flat899)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1574 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1573 = _t1574
        else
            _t1573 = nothing
        end
        deconstruct_result897 = _t1573
        if !isnothing(deconstruct_result897)
            unwrapped898 = deconstruct_result897
            write(pp, ":")
            write(pp, unwrapped898)
        else
            _dollar_dollar = msg
            _t1575 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result895 = _t1575
            if !isnothing(deconstruct_result895)
                unwrapped896 = deconstruct_result895
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped896))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat904 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat904)
        write(pp, flat904)
        return nothing
    else
        _dollar_dollar = msg
        _t1576 = deconstruct_bindings(pp, _dollar_dollar)
        fields900 = (_t1576, _dollar_dollar.value,)
        unwrapped_fields901 = fields900
        write(pp, "(")
        indent!(pp)
        field902 = unwrapped_fields901[1]
        pretty_bindings(pp, field902)
        newline(pp)
        field903 = unwrapped_fields901[2]
        pretty_formula(pp, field903)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat912 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat912)
        write(pp, flat912)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1577 = _dollar_dollar[2]
        else
            _t1577 = nothing
        end
        fields905 = (_dollar_dollar[1], _t1577,)
        unwrapped_fields906 = fields905
        write(pp, "[")
        indent!(pp)
        field907 = unwrapped_fields906[1]
        for (i1578, elem908) in enumerate(field907)
            i909 = i1578 - 1
            if (i909 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem908)
        end
        field910 = unwrapped_fields906[2]
        if !isnothing(field910)
            newline(pp)
            opt_val911 = field910
            pretty_value_bindings(pp, opt_val911)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat917 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat917)
        write(pp, flat917)
        return nothing
    else
        _dollar_dollar = msg
        fields913 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields914 = fields913
        field915 = unwrapped_fields914[1]
        write(pp, field915)
        write(pp, "::")
        field916 = unwrapped_fields914[2]
        pretty_type(pp, field916)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat946 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1579 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1579 = nothing
        end
        deconstruct_result944 = _t1579
        if !isnothing(deconstruct_result944)
            unwrapped945 = deconstruct_result944
            pretty_unspecified_type(pp, unwrapped945)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1580 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1580 = nothing
            end
            deconstruct_result942 = _t1580
            if !isnothing(deconstruct_result942)
                unwrapped943 = deconstruct_result942
                pretty_string_type(pp, unwrapped943)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1581 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1581 = nothing
                end
                deconstruct_result940 = _t1581
                if !isnothing(deconstruct_result940)
                    unwrapped941 = deconstruct_result940
                    pretty_int_type(pp, unwrapped941)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1582 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1582 = nothing
                    end
                    deconstruct_result938 = _t1582
                    if !isnothing(deconstruct_result938)
                        unwrapped939 = deconstruct_result938
                        pretty_float_type(pp, unwrapped939)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1583 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1583 = nothing
                        end
                        deconstruct_result936 = _t1583
                        if !isnothing(deconstruct_result936)
                            unwrapped937 = deconstruct_result936
                            pretty_uint128_type(pp, unwrapped937)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1584 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1584 = nothing
                            end
                            deconstruct_result934 = _t1584
                            if !isnothing(deconstruct_result934)
                                unwrapped935 = deconstruct_result934
                                pretty_int128_type(pp, unwrapped935)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1585 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1585 = nothing
                                end
                                deconstruct_result932 = _t1585
                                if !isnothing(deconstruct_result932)
                                    unwrapped933 = deconstruct_result932
                                    pretty_date_type(pp, unwrapped933)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1586 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1586 = nothing
                                    end
                                    deconstruct_result930 = _t1586
                                    if !isnothing(deconstruct_result930)
                                        unwrapped931 = deconstruct_result930
                                        pretty_datetime_type(pp, unwrapped931)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1587 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1587 = nothing
                                        end
                                        deconstruct_result928 = _t1587
                                        if !isnothing(deconstruct_result928)
                                            unwrapped929 = deconstruct_result928
                                            pretty_missing_type(pp, unwrapped929)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1588 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1588 = nothing
                                            end
                                            deconstruct_result926 = _t1588
                                            if !isnothing(deconstruct_result926)
                                                unwrapped927 = deconstruct_result926
                                                pretty_decimal_type(pp, unwrapped927)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1589 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1589 = nothing
                                                end
                                                deconstruct_result924 = _t1589
                                                if !isnothing(deconstruct_result924)
                                                    unwrapped925 = deconstruct_result924
                                                    pretty_boolean_type(pp, unwrapped925)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1590 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1590 = nothing
                                                    end
                                                    deconstruct_result922 = _t1590
                                                    if !isnothing(deconstruct_result922)
                                                        unwrapped923 = deconstruct_result922
                                                        pretty_int32_type(pp, unwrapped923)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1591 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1591 = nothing
                                                        end
                                                        deconstruct_result920 = _t1591
                                                        if !isnothing(deconstruct_result920)
                                                            unwrapped921 = deconstruct_result920
                                                            pretty_float32_type(pp, unwrapped921)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1592 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1592 = nothing
                                                            end
                                                            deconstruct_result918 = _t1592
                                                            if !isnothing(deconstruct_result918)
                                                                unwrapped919 = deconstruct_result918
                                                                pretty_uint32_type(pp, unwrapped919)
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
    fields947 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields948 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields949 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields950 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields951 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields952 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields953 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields954 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields955 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat960 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat960)
        write(pp, flat960)
        return nothing
    else
        _dollar_dollar = msg
        fields956 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields957 = fields956
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field958 = unwrapped_fields957[1]
        write(pp, string(field958))
        newline(pp)
        field959 = unwrapped_fields957[2]
        write(pp, string(field959))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields961 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields962 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields963 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields964 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat968 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat968)
        write(pp, flat968)
        return nothing
    else
        fields965 = msg
        write(pp, "|")
        if !isempty(fields965)
            write(pp, " ")
            for (i1593, elem966) in enumerate(fields965)
                i967 = i1593 - 1
                if (i967 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem966)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat995 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat995)
        write(pp, flat995)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1594 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1594 = nothing
        end
        deconstruct_result993 = _t1594
        if !isnothing(deconstruct_result993)
            unwrapped994 = deconstruct_result993
            pretty_true(pp, unwrapped994)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1595 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1595 = nothing
            end
            deconstruct_result991 = _t1595
            if !isnothing(deconstruct_result991)
                unwrapped992 = deconstruct_result991
                pretty_false(pp, unwrapped992)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1596 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1596 = nothing
                end
                deconstruct_result989 = _t1596
                if !isnothing(deconstruct_result989)
                    unwrapped990 = deconstruct_result989
                    pretty_exists(pp, unwrapped990)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1597 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1597 = nothing
                    end
                    deconstruct_result987 = _t1597
                    if !isnothing(deconstruct_result987)
                        unwrapped988 = deconstruct_result987
                        pretty_reduce(pp, unwrapped988)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1598 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1598 = nothing
                        end
                        deconstruct_result985 = _t1598
                        if !isnothing(deconstruct_result985)
                            unwrapped986 = deconstruct_result985
                            pretty_conjunction(pp, unwrapped986)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1599 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1599 = nothing
                            end
                            deconstruct_result983 = _t1599
                            if !isnothing(deconstruct_result983)
                                unwrapped984 = deconstruct_result983
                                pretty_disjunction(pp, unwrapped984)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1600 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1600 = nothing
                                end
                                deconstruct_result981 = _t1600
                                if !isnothing(deconstruct_result981)
                                    unwrapped982 = deconstruct_result981
                                    pretty_not(pp, unwrapped982)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1601 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1601 = nothing
                                    end
                                    deconstruct_result979 = _t1601
                                    if !isnothing(deconstruct_result979)
                                        unwrapped980 = deconstruct_result979
                                        pretty_ffi(pp, unwrapped980)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1602 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1602 = nothing
                                        end
                                        deconstruct_result977 = _t1602
                                        if !isnothing(deconstruct_result977)
                                            unwrapped978 = deconstruct_result977
                                            pretty_atom(pp, unwrapped978)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1603 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1603 = nothing
                                            end
                                            deconstruct_result975 = _t1603
                                            if !isnothing(deconstruct_result975)
                                                unwrapped976 = deconstruct_result975
                                                pretty_pragma(pp, unwrapped976)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1604 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1604 = nothing
                                                end
                                                deconstruct_result973 = _t1604
                                                if !isnothing(deconstruct_result973)
                                                    unwrapped974 = deconstruct_result973
                                                    pretty_primitive(pp, unwrapped974)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1605 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1605 = nothing
                                                    end
                                                    deconstruct_result971 = _t1605
                                                    if !isnothing(deconstruct_result971)
                                                        unwrapped972 = deconstruct_result971
                                                        pretty_rel_atom(pp, unwrapped972)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1606 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1606 = nothing
                                                        end
                                                        deconstruct_result969 = _t1606
                                                        if !isnothing(deconstruct_result969)
                                                            unwrapped970 = deconstruct_result969
                                                            pretty_cast(pp, unwrapped970)
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
    fields996 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields997 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1002 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1002)
        write(pp, flat1002)
        return nothing
    else
        _dollar_dollar = msg
        _t1607 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields998 = (_t1607, _dollar_dollar.body.value,)
        unwrapped_fields999 = fields998
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1000 = unwrapped_fields999[1]
        pretty_bindings(pp, field1000)
        newline(pp)
        field1001 = unwrapped_fields999[2]
        pretty_formula(pp, field1001)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1008 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1008)
        write(pp, flat1008)
        return nothing
    else
        _dollar_dollar = msg
        fields1003 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1004 = fields1003
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1005 = unwrapped_fields1004[1]
        pretty_abstraction(pp, field1005)
        newline(pp)
        field1006 = unwrapped_fields1004[2]
        pretty_abstraction(pp, field1006)
        newline(pp)
        field1007 = unwrapped_fields1004[3]
        pretty_terms(pp, field1007)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1012 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1012)
        write(pp, flat1012)
        return nothing
    else
        fields1009 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1009)
            newline(pp)
            for (i1608, elem1010) in enumerate(fields1009)
                i1011 = i1608 - 1
                if (i1011 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1010)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1017 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1017)
        write(pp, flat1017)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1609 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1609 = nothing
        end
        deconstruct_result1015 = _t1609
        if !isnothing(deconstruct_result1015)
            unwrapped1016 = deconstruct_result1015
            pretty_var(pp, unwrapped1016)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1610 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1610 = nothing
            end
            deconstruct_result1013 = _t1610
            if !isnothing(deconstruct_result1013)
                unwrapped1014 = deconstruct_result1013
                pretty_value(pp, unwrapped1014)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1020 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1020)
        write(pp, flat1020)
        return nothing
    else
        _dollar_dollar = msg
        fields1018 = _dollar_dollar.name
        unwrapped_fields1019 = fields1018
        write(pp, unwrapped_fields1019)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1046 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1046)
        write(pp, flat1046)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1611 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1611 = nothing
        end
        deconstruct_result1044 = _t1611
        if !isnothing(deconstruct_result1044)
            unwrapped1045 = deconstruct_result1044
            pretty_date(pp, unwrapped1045)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1612 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1612 = nothing
            end
            deconstruct_result1042 = _t1612
            if !isnothing(deconstruct_result1042)
                unwrapped1043 = deconstruct_result1042
                pretty_datetime(pp, unwrapped1043)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1613 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1613 = nothing
                end
                deconstruct_result1040 = _t1613
                if !isnothing(deconstruct_result1040)
                    unwrapped1041 = deconstruct_result1040
                    write(pp, format_string(pp, unwrapped1041))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1614 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1614 = nothing
                    end
                    deconstruct_result1038 = _t1614
                    if !isnothing(deconstruct_result1038)
                        unwrapped1039 = deconstruct_result1038
                        write(pp, format_int32(pp, unwrapped1039))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1615 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1615 = nothing
                        end
                        deconstruct_result1036 = _t1615
                        if !isnothing(deconstruct_result1036)
                            unwrapped1037 = deconstruct_result1036
                            write(pp, format_int(pp, unwrapped1037))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1616 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1616 = nothing
                            end
                            deconstruct_result1034 = _t1616
                            if !isnothing(deconstruct_result1034)
                                unwrapped1035 = deconstruct_result1034
                                write(pp, format_float32(pp, unwrapped1035))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1617 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1617 = nothing
                                end
                                deconstruct_result1032 = _t1617
                                if !isnothing(deconstruct_result1032)
                                    unwrapped1033 = deconstruct_result1032
                                    write(pp, format_float(pp, unwrapped1033))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1618 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1618 = nothing
                                    end
                                    deconstruct_result1030 = _t1618
                                    if !isnothing(deconstruct_result1030)
                                        unwrapped1031 = deconstruct_result1030
                                        write(pp, format_uint32(pp, unwrapped1031))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1619 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1619 = nothing
                                        end
                                        deconstruct_result1028 = _t1619
                                        if !isnothing(deconstruct_result1028)
                                            unwrapped1029 = deconstruct_result1028
                                            write(pp, format_uint128(pp, unwrapped1029))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1620 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1620 = nothing
                                            end
                                            deconstruct_result1026 = _t1620
                                            if !isnothing(deconstruct_result1026)
                                                unwrapped1027 = deconstruct_result1026
                                                write(pp, format_int128(pp, unwrapped1027))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1621 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1621 = nothing
                                                end
                                                deconstruct_result1024 = _t1621
                                                if !isnothing(deconstruct_result1024)
                                                    unwrapped1025 = deconstruct_result1024
                                                    write(pp, format_decimal(pp, unwrapped1025))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1622 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1622 = nothing
                                                    end
                                                    deconstruct_result1022 = _t1622
                                                    if !isnothing(deconstruct_result1022)
                                                        unwrapped1023 = deconstruct_result1022
                                                        pretty_boolean_value(pp, unwrapped1023)
                                                    else
                                                        fields1021 = msg
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
    flat1052 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1052)
        write(pp, flat1052)
        return nothing
    else
        _dollar_dollar = msg
        fields1047 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1048 = fields1047
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1049 = unwrapped_fields1048[1]
        write(pp, format_int(pp, field1049))
        newline(pp)
        field1050 = unwrapped_fields1048[2]
        write(pp, format_int(pp, field1050))
        newline(pp)
        field1051 = unwrapped_fields1048[3]
        write(pp, format_int(pp, field1051))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1063 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1063)
        write(pp, flat1063)
        return nothing
    else
        _dollar_dollar = msg
        fields1053 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1054 = fields1053
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1055 = unwrapped_fields1054[1]
        write(pp, format_int(pp, field1055))
        newline(pp)
        field1056 = unwrapped_fields1054[2]
        write(pp, format_int(pp, field1056))
        newline(pp)
        field1057 = unwrapped_fields1054[3]
        write(pp, format_int(pp, field1057))
        newline(pp)
        field1058 = unwrapped_fields1054[4]
        write(pp, format_int(pp, field1058))
        newline(pp)
        field1059 = unwrapped_fields1054[5]
        write(pp, format_int(pp, field1059))
        newline(pp)
        field1060 = unwrapped_fields1054[6]
        write(pp, format_int(pp, field1060))
        field1061 = unwrapped_fields1054[7]
        if !isnothing(field1061)
            newline(pp)
            opt_val1062 = field1061
            write(pp, format_int(pp, opt_val1062))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1068 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1068)
        write(pp, flat1068)
        return nothing
    else
        _dollar_dollar = msg
        fields1064 = _dollar_dollar.args
        unwrapped_fields1065 = fields1064
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1065)
            newline(pp)
            for (i1623, elem1066) in enumerate(unwrapped_fields1065)
                i1067 = i1623 - 1
                if (i1067 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1066)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1073 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1073)
        write(pp, flat1073)
        return nothing
    else
        _dollar_dollar = msg
        fields1069 = _dollar_dollar.args
        unwrapped_fields1070 = fields1069
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1070)
            newline(pp)
            for (i1624, elem1071) in enumerate(unwrapped_fields1070)
                i1072 = i1624 - 1
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

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1076 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1076)
        write(pp, flat1076)
        return nothing
    else
        _dollar_dollar = msg
        fields1074 = _dollar_dollar.arg
        unwrapped_fields1075 = fields1074
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1075)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1082 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1082)
        write(pp, flat1082)
        return nothing
    else
        _dollar_dollar = msg
        fields1077 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1078 = fields1077
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1079 = unwrapped_fields1078[1]
        pretty_name(pp, field1079)
        newline(pp)
        field1080 = unwrapped_fields1078[2]
        pretty_ffi_args(pp, field1080)
        newline(pp)
        field1081 = unwrapped_fields1078[3]
        pretty_terms(pp, field1081)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1084 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1084)
        write(pp, flat1084)
        return nothing
    else
        fields1083 = msg
        write(pp, ":")
        write(pp, fields1083)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1088 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1088)
        write(pp, flat1088)
        return nothing
    else
        fields1085 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1085)
            newline(pp)
            for (i1625, elem1086) in enumerate(fields1085)
                i1087 = i1625 - 1
                if (i1087 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1086)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1095 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1095)
        write(pp, flat1095)
        return nothing
    else
        _dollar_dollar = msg
        fields1089 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1090 = fields1089
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1091 = unwrapped_fields1090[1]
        pretty_relation_id(pp, field1091)
        field1092 = unwrapped_fields1090[2]
        if !isempty(field1092)
            newline(pp)
            for (i1626, elem1093) in enumerate(field1092)
                i1094 = i1626 - 1
                if (i1094 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1093)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1102 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1102)
        write(pp, flat1102)
        return nothing
    else
        _dollar_dollar = msg
        fields1096 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1097 = fields1096
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1098 = unwrapped_fields1097[1]
        pretty_name(pp, field1098)
        field1099 = unwrapped_fields1097[2]
        if !isempty(field1099)
            newline(pp)
            for (i1627, elem1100) in enumerate(field1099)
                i1101 = i1627 - 1
                if (i1101 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1100)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1118 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1118)
        write(pp, flat1118)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1628 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1628 = nothing
        end
        guard_result1117 = _t1628
        if !isnothing(guard_result1117)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1629 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1629 = nothing
            end
            guard_result1116 = _t1629
            if !isnothing(guard_result1116)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1630 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1630 = nothing
                end
                guard_result1115 = _t1630
                if !isnothing(guard_result1115)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1631 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1631 = nothing
                    end
                    guard_result1114 = _t1631
                    if !isnothing(guard_result1114)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1632 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1632 = nothing
                        end
                        guard_result1113 = _t1632
                        if !isnothing(guard_result1113)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1633 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1633 = nothing
                            end
                            guard_result1112 = _t1633
                            if !isnothing(guard_result1112)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1634 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1634 = nothing
                                end
                                guard_result1111 = _t1634
                                if !isnothing(guard_result1111)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1635 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1635 = nothing
                                    end
                                    guard_result1110 = _t1635
                                    if !isnothing(guard_result1110)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1636 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1636 = nothing
                                        end
                                        guard_result1109 = _t1636
                                        if !isnothing(guard_result1109)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1103 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1104 = fields1103
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1105 = unwrapped_fields1104[1]
                                            pretty_name(pp, field1105)
                                            field1106 = unwrapped_fields1104[2]
                                            if !isempty(field1106)
                                                newline(pp)
                                                for (i1637, elem1107) in enumerate(field1106)
                                                    i1108 = i1637 - 1
                                                    if (i1108 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1107)
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
    flat1123 = try_flat(pp, msg, pretty_eq)
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
        fields1119 = _t1638
        unwrapped_fields1120 = fields1119
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1121 = unwrapped_fields1120[1]
        pretty_term(pp, field1121)
        newline(pp)
        field1122 = unwrapped_fields1120[2]
        pretty_term(pp, field1122)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1128 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1128)
        write(pp, flat1128)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1639 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1639 = nothing
        end
        fields1124 = _t1639
        unwrapped_fields1125 = fields1124
        write(pp, "(<")
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

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1133 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1133)
        write(pp, flat1133)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1640 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1640 = nothing
        end
        fields1129 = _t1640
        unwrapped_fields1130 = fields1129
        write(pp, "(<=")
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

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1138 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1138)
        write(pp, flat1138)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1641 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1641 = nothing
        end
        fields1134 = _t1641
        unwrapped_fields1135 = fields1134
        write(pp, "(>")
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

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1143 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1143)
        write(pp, flat1143)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1642 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1642 = nothing
        end
        fields1139 = _t1642
        unwrapped_fields1140 = fields1139
        write(pp, "(>=")
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

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1149 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1149)
        write(pp, flat1149)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1643 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1643 = nothing
        end
        fields1144 = _t1643
        unwrapped_fields1145 = fields1144
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1146 = unwrapped_fields1145[1]
        pretty_term(pp, field1146)
        newline(pp)
        field1147 = unwrapped_fields1145[2]
        pretty_term(pp, field1147)
        newline(pp)
        field1148 = unwrapped_fields1145[3]
        pretty_term(pp, field1148)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1155 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1155)
        write(pp, flat1155)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1644 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1644 = nothing
        end
        fields1150 = _t1644
        unwrapped_fields1151 = fields1150
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1152 = unwrapped_fields1151[1]
        pretty_term(pp, field1152)
        newline(pp)
        field1153 = unwrapped_fields1151[2]
        pretty_term(pp, field1153)
        newline(pp)
        field1154 = unwrapped_fields1151[3]
        pretty_term(pp, field1154)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1161 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1161)
        write(pp, flat1161)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1645 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1645 = nothing
        end
        fields1156 = _t1645
        unwrapped_fields1157 = fields1156
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1158 = unwrapped_fields1157[1]
        pretty_term(pp, field1158)
        newline(pp)
        field1159 = unwrapped_fields1157[2]
        pretty_term(pp, field1159)
        newline(pp)
        field1160 = unwrapped_fields1157[3]
        pretty_term(pp, field1160)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1167 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1646 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1646 = nothing
        end
        fields1162 = _t1646
        unwrapped_fields1163 = fields1162
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1164 = unwrapped_fields1163[1]
        pretty_term(pp, field1164)
        newline(pp)
        field1165 = unwrapped_fields1163[2]
        pretty_term(pp, field1165)
        newline(pp)
        field1166 = unwrapped_fields1163[3]
        pretty_term(pp, field1166)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1172 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1172)
        write(pp, flat1172)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1647 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1647 = nothing
        end
        deconstruct_result1170 = _t1647
        if !isnothing(deconstruct_result1170)
            unwrapped1171 = deconstruct_result1170
            pretty_specialized_value(pp, unwrapped1171)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1648 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1648 = nothing
            end
            deconstruct_result1168 = _t1648
            if !isnothing(deconstruct_result1168)
                unwrapped1169 = deconstruct_result1168
                pretty_term(pp, unwrapped1169)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1174 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1174)
        write(pp, flat1174)
        return nothing
    else
        fields1173 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1173)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1181 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1181)
        write(pp, flat1181)
        return nothing
    else
        _dollar_dollar = msg
        fields1175 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1176 = fields1175
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1177 = unwrapped_fields1176[1]
        pretty_name(pp, field1177)
        field1178 = unwrapped_fields1176[2]
        if !isempty(field1178)
            newline(pp)
            for (i1649, elem1179) in enumerate(field1178)
                i1180 = i1649 - 1
                if (i1180 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1179)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1186 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1186)
        write(pp, flat1186)
        return nothing
    else
        _dollar_dollar = msg
        fields1182 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1183 = fields1182
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1184 = unwrapped_fields1183[1]
        pretty_term(pp, field1184)
        newline(pp)
        field1185 = unwrapped_fields1183[2]
        pretty_term(pp, field1185)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1190 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1190)
        write(pp, flat1190)
        return nothing
    else
        fields1187 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1187)
            newline(pp)
            for (i1650, elem1188) in enumerate(fields1187)
                i1189 = i1650 - 1
                if (i1189 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1188)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1197 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1197)
        write(pp, flat1197)
        return nothing
    else
        _dollar_dollar = msg
        fields1191 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1192 = fields1191
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1193 = unwrapped_fields1192[1]
        pretty_name(pp, field1193)
        field1194 = unwrapped_fields1192[2]
        if !isempty(field1194)
            newline(pp)
            for (i1651, elem1195) in enumerate(field1194)
                i1196 = i1651 - 1
                if (i1196 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1195)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1204 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1204)
        write(pp, flat1204)
        return nothing
    else
        _dollar_dollar = msg
        fields1198 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1199 = fields1198
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1200 = unwrapped_fields1199[1]
        if !isempty(field1200)
            newline(pp)
            for (i1652, elem1201) in enumerate(field1200)
                i1202 = i1652 - 1
                if (i1202 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1201)
            end
        end
        newline(pp)
        field1203 = unwrapped_fields1199[2]
        pretty_script(pp, field1203)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1209 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1209)
        write(pp, flat1209)
        return nothing
    else
        _dollar_dollar = msg
        fields1205 = _dollar_dollar.constructs
        unwrapped_fields1206 = fields1205
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1206)
            newline(pp)
            for (i1653, elem1207) in enumerate(unwrapped_fields1206)
                i1208 = i1653 - 1
                if (i1208 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1207)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1214 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1214)
        write(pp, flat1214)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1654 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1654 = nothing
        end
        deconstruct_result1212 = _t1654
        if !isnothing(deconstruct_result1212)
            unwrapped1213 = deconstruct_result1212
            pretty_loop(pp, unwrapped1213)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1655 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1655 = nothing
            end
            deconstruct_result1210 = _t1655
            if !isnothing(deconstruct_result1210)
                unwrapped1211 = deconstruct_result1210
                pretty_instruction(pp, unwrapped1211)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1219 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1219)
        write(pp, flat1219)
        return nothing
    else
        _dollar_dollar = msg
        fields1215 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1216 = fields1215
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1217 = unwrapped_fields1216[1]
        pretty_init(pp, field1217)
        newline(pp)
        field1218 = unwrapped_fields1216[2]
        pretty_script(pp, field1218)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1223 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1223)
        write(pp, flat1223)
        return nothing
    else
        fields1220 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1220)
            newline(pp)
            for (i1656, elem1221) in enumerate(fields1220)
                i1222 = i1656 - 1
                if (i1222 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1221)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1234 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1234)
        write(pp, flat1234)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1657 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1657 = nothing
        end
        deconstruct_result1232 = _t1657
        if !isnothing(deconstruct_result1232)
            unwrapped1233 = deconstruct_result1232
            pretty_assign(pp, unwrapped1233)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1658 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1658 = nothing
            end
            deconstruct_result1230 = _t1658
            if !isnothing(deconstruct_result1230)
                unwrapped1231 = deconstruct_result1230
                pretty_upsert(pp, unwrapped1231)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1659 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1659 = nothing
                end
                deconstruct_result1228 = _t1659
                if !isnothing(deconstruct_result1228)
                    unwrapped1229 = deconstruct_result1228
                    pretty_break(pp, unwrapped1229)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1660 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1660 = nothing
                    end
                    deconstruct_result1226 = _t1660
                    if !isnothing(deconstruct_result1226)
                        unwrapped1227 = deconstruct_result1226
                        pretty_monoid_def(pp, unwrapped1227)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1661 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1661 = nothing
                        end
                        deconstruct_result1224 = _t1661
                        if !isnothing(deconstruct_result1224)
                            unwrapped1225 = deconstruct_result1224
                            pretty_monus_def(pp, unwrapped1225)
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
    flat1241 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1241)
        write(pp, flat1241)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1662 = _dollar_dollar.attrs
        else
            _t1662 = nothing
        end
        fields1235 = (_dollar_dollar.name, _dollar_dollar.body, _t1662,)
        unwrapped_fields1236 = fields1235
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1237 = unwrapped_fields1236[1]
        pretty_relation_id(pp, field1237)
        newline(pp)
        field1238 = unwrapped_fields1236[2]
        pretty_abstraction(pp, field1238)
        field1239 = unwrapped_fields1236[3]
        if !isnothing(field1239)
            newline(pp)
            opt_val1240 = field1239
            pretty_attrs(pp, opt_val1240)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1248 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1248)
        write(pp, flat1248)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1663 = _dollar_dollar.attrs
        else
            _t1663 = nothing
        end
        fields1242 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1663,)
        unwrapped_fields1243 = fields1242
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1244 = unwrapped_fields1243[1]
        pretty_relation_id(pp, field1244)
        newline(pp)
        field1245 = unwrapped_fields1243[2]
        pretty_abstraction_with_arity(pp, field1245)
        field1246 = unwrapped_fields1243[3]
        if !isnothing(field1246)
            newline(pp)
            opt_val1247 = field1246
            pretty_attrs(pp, opt_val1247)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1253 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        _dollar_dollar = msg
        _t1664 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1249 = (_t1664, _dollar_dollar[1].value,)
        unwrapped_fields1250 = fields1249
        write(pp, "(")
        indent!(pp)
        field1251 = unwrapped_fields1250[1]
        pretty_bindings(pp, field1251)
        newline(pp)
        field1252 = unwrapped_fields1250[2]
        pretty_formula(pp, field1252)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1260 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1260)
        write(pp, flat1260)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1665 = _dollar_dollar.attrs
        else
            _t1665 = nothing
        end
        fields1254 = (_dollar_dollar.name, _dollar_dollar.body, _t1665,)
        unwrapped_fields1255 = fields1254
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1256 = unwrapped_fields1255[1]
        pretty_relation_id(pp, field1256)
        newline(pp)
        field1257 = unwrapped_fields1255[2]
        pretty_abstraction(pp, field1257)
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

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1268 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1268)
        write(pp, flat1268)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1666 = _dollar_dollar.attrs
        else
            _t1666 = nothing
        end
        fields1261 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1666,)
        unwrapped_fields1262 = fields1261
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1263 = unwrapped_fields1262[1]
        pretty_monoid(pp, field1263)
        newline(pp)
        field1264 = unwrapped_fields1262[2]
        pretty_relation_id(pp, field1264)
        newline(pp)
        field1265 = unwrapped_fields1262[3]
        pretty_abstraction_with_arity(pp, field1265)
        field1266 = unwrapped_fields1262[4]
        if !isnothing(field1266)
            newline(pp)
            opt_val1267 = field1266
            pretty_attrs(pp, opt_val1267)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1277 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1277)
        write(pp, flat1277)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1667 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1667 = nothing
        end
        deconstruct_result1275 = _t1667
        if !isnothing(deconstruct_result1275)
            unwrapped1276 = deconstruct_result1275
            pretty_or_monoid(pp, unwrapped1276)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1668 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1668 = nothing
            end
            deconstruct_result1273 = _t1668
            if !isnothing(deconstruct_result1273)
                unwrapped1274 = deconstruct_result1273
                pretty_min_monoid(pp, unwrapped1274)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1669 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1669 = nothing
                end
                deconstruct_result1271 = _t1669
                if !isnothing(deconstruct_result1271)
                    unwrapped1272 = deconstruct_result1271
                    pretty_max_monoid(pp, unwrapped1272)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1670 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1670 = nothing
                    end
                    deconstruct_result1269 = _t1670
                    if !isnothing(deconstruct_result1269)
                        unwrapped1270 = deconstruct_result1269
                        pretty_sum_monoid(pp, unwrapped1270)
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
    fields1278 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1281 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1281)
        write(pp, flat1281)
        return nothing
    else
        _dollar_dollar = msg
        fields1279 = _dollar_dollar.var"#type"
        unwrapped_fields1280 = fields1279
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1280)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1284 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1284)
        write(pp, flat1284)
        return nothing
    else
        _dollar_dollar = msg
        fields1282 = _dollar_dollar.var"#type"
        unwrapped_fields1283 = fields1282
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1283)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1287 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1287)
        write(pp, flat1287)
        return nothing
    else
        _dollar_dollar = msg
        fields1285 = _dollar_dollar.var"#type"
        unwrapped_fields1286 = fields1285
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1286)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1295 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1295)
        write(pp, flat1295)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1671 = _dollar_dollar.attrs
        else
            _t1671 = nothing
        end
        fields1288 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1671,)
        unwrapped_fields1289 = fields1288
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1290 = unwrapped_fields1289[1]
        pretty_monoid(pp, field1290)
        newline(pp)
        field1291 = unwrapped_fields1289[2]
        pretty_relation_id(pp, field1291)
        newline(pp)
        field1292 = unwrapped_fields1289[3]
        pretty_abstraction_with_arity(pp, field1292)
        field1293 = unwrapped_fields1289[4]
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

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1302 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1302)
        write(pp, flat1302)
        return nothing
    else
        _dollar_dollar = msg
        fields1296 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1297 = fields1296
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1298 = unwrapped_fields1297[1]
        pretty_relation_id(pp, field1298)
        newline(pp)
        field1299 = unwrapped_fields1297[2]
        pretty_abstraction(pp, field1299)
        newline(pp)
        field1300 = unwrapped_fields1297[3]
        pretty_functional_dependency_keys(pp, field1300)
        newline(pp)
        field1301 = unwrapped_fields1297[4]
        pretty_functional_dependency_values(pp, field1301)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1306 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1306)
        write(pp, flat1306)
        return nothing
    else
        fields1303 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1303)
            newline(pp)
            for (i1672, elem1304) in enumerate(fields1303)
                i1305 = i1672 - 1
                if (i1305 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1304)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1310 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1310)
        write(pp, flat1310)
        return nothing
    else
        fields1307 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1307)
            newline(pp)
            for (i1673, elem1308) in enumerate(fields1307)
                i1309 = i1673 - 1
                if (i1309 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1308)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1319 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1319)
        write(pp, flat1319)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1674 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1674 = nothing
        end
        deconstruct_result1317 = _t1674
        if !isnothing(deconstruct_result1317)
            unwrapped1318 = deconstruct_result1317
            pretty_edb(pp, unwrapped1318)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1675 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1675 = nothing
            end
            deconstruct_result1315 = _t1675
            if !isnothing(deconstruct_result1315)
                unwrapped1316 = deconstruct_result1315
                pretty_betree_relation(pp, unwrapped1316)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1676 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1676 = nothing
                end
                deconstruct_result1313 = _t1676
                if !isnothing(deconstruct_result1313)
                    unwrapped1314 = deconstruct_result1313
                    pretty_csv_data(pp, unwrapped1314)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1677 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1677 = nothing
                    end
                    deconstruct_result1311 = _t1677
                    if !isnothing(deconstruct_result1311)
                        unwrapped1312 = deconstruct_result1311
                        pretty_iceberg_data(pp, unwrapped1312)
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
    flat1325 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1325)
        write(pp, flat1325)
        return nothing
    else
        _dollar_dollar = msg
        fields1320 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1321 = fields1320
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1322 = unwrapped_fields1321[1]
        pretty_relation_id(pp, field1322)
        newline(pp)
        field1323 = unwrapped_fields1321[2]
        pretty_edb_path(pp, field1323)
        newline(pp)
        field1324 = unwrapped_fields1321[3]
        pretty_edb_types(pp, field1324)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1329 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1329)
        write(pp, flat1329)
        return nothing
    else
        fields1326 = msg
        write(pp, "[")
        indent!(pp)
        for (i1678, elem1327) in enumerate(fields1326)
            i1328 = i1678 - 1
            if (i1328 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1327))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1333 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1333)
        write(pp, flat1333)
        return nothing
    else
        fields1330 = msg
        write(pp, "[")
        indent!(pp)
        for (i1679, elem1331) in enumerate(fields1330)
            i1332 = i1679 - 1
            if (i1332 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1331)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1338 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1338)
        write(pp, flat1338)
        return nothing
    else
        _dollar_dollar = msg
        fields1334 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1335 = fields1334
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1336 = unwrapped_fields1335[1]
        pretty_relation_id(pp, field1336)
        newline(pp)
        field1337 = unwrapped_fields1335[2]
        pretty_betree_info(pp, field1337)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1344 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1344)
        write(pp, flat1344)
        return nothing
    else
        _dollar_dollar = msg
        _t1680 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1339 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1680,)
        unwrapped_fields1340 = fields1339
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1341 = unwrapped_fields1340[1]
        pretty_betree_info_key_types(pp, field1341)
        newline(pp)
        field1342 = unwrapped_fields1340[2]
        pretty_betree_info_value_types(pp, field1342)
        newline(pp)
        field1343 = unwrapped_fields1340[3]
        pretty_config_dict(pp, field1343)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1348 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1348)
        write(pp, flat1348)
        return nothing
    else
        fields1345 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1345)
            newline(pp)
            for (i1681, elem1346) in enumerate(fields1345)
                i1347 = i1681 - 1
                if (i1347 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1346)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1352 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1352)
        write(pp, flat1352)
        return nothing
    else
        fields1349 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1349)
            newline(pp)
            for (i1682, elem1350) in enumerate(fields1349)
                i1351 = i1682 - 1
                if (i1351 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1350)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1359 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1359)
        write(pp, flat1359)
        return nothing
    else
        _dollar_dollar = msg
        fields1353 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1354 = fields1353
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1355 = unwrapped_fields1354[1]
        pretty_csvlocator(pp, field1355)
        newline(pp)
        field1356 = unwrapped_fields1354[2]
        pretty_csv_config(pp, field1356)
        newline(pp)
        field1357 = unwrapped_fields1354[3]
        pretty_gnf_columns(pp, field1357)
        newline(pp)
        field1358 = unwrapped_fields1354[4]
        pretty_csv_asof(pp, field1358)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1366 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1366)
        write(pp, flat1366)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1683 = _dollar_dollar.paths
        else
            _t1683 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1684 = String(copy(_dollar_dollar.inline_data))
        else
            _t1684 = nothing
        end
        fields1360 = (_t1683, _t1684,)
        unwrapped_fields1361 = fields1360
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1362 = unwrapped_fields1361[1]
        if !isnothing(field1362)
            newline(pp)
            opt_val1363 = field1362
            pretty_csv_locator_paths(pp, opt_val1363)
        end
        field1364 = unwrapped_fields1361[2]
        if !isnothing(field1364)
            newline(pp)
            opt_val1365 = field1364
            pretty_csv_locator_inline_data(pp, opt_val1365)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1370 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1370)
        write(pp, flat1370)
        return nothing
    else
        fields1367 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1367)
            newline(pp)
            for (i1685, elem1368) in enumerate(fields1367)
                i1369 = i1685 - 1
                if (i1369 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1368))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1372 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1372)
        write(pp, flat1372)
        return nothing
    else
        fields1371 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1371))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1375 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1375)
        write(pp, flat1375)
        return nothing
    else
        _dollar_dollar = msg
        _t1686 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1373 = _t1686
        unwrapped_fields1374 = fields1373
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1374)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1379 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1379)
        write(pp, flat1379)
        return nothing
    else
        fields1376 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1376)
            newline(pp)
            for (i1687, elem1377) in enumerate(fields1376)
                i1378 = i1687 - 1
                if (i1378 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1377)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1388 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1388)
        write(pp, flat1388)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1688 = _dollar_dollar.target_id
        else
            _t1688 = nothing
        end
        fields1380 = (_dollar_dollar.column_path, _t1688, _dollar_dollar.types,)
        unwrapped_fields1381 = fields1380
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1382 = unwrapped_fields1381[1]
        pretty_gnf_column_path(pp, field1382)
        field1383 = unwrapped_fields1381[2]
        if !isnothing(field1383)
            newline(pp)
            opt_val1384 = field1383
            pretty_relation_id(pp, opt_val1384)
        end
        newline(pp)
        write(pp, "[")
        field1385 = unwrapped_fields1381[3]
        for (i1689, elem1386) in enumerate(field1385)
            i1387 = i1689 - 1
            if (i1387 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1386)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1395 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1395)
        write(pp, flat1395)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1690 = _dollar_dollar[1]
        else
            _t1690 = nothing
        end
        deconstruct_result1393 = _t1690
        if !isnothing(deconstruct_result1393)
            unwrapped1394 = deconstruct_result1393
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1394))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1691 = _dollar_dollar
            else
                _t1691 = nothing
            end
            deconstruct_result1389 = _t1691
            if !isnothing(deconstruct_result1389)
                unwrapped1390 = deconstruct_result1389
                write(pp, "[")
                indent!(pp)
                for (i1692, elem1391) in enumerate(unwrapped1390)
                    i1392 = i1692 - 1
                    if (i1392 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1391))
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
    flat1397 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1397)
        write(pp, flat1397)
        return nothing
    else
        fields1396 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1396))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1405 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1405)
        write(pp, flat1405)
        return nothing
    else
        _dollar_dollar = msg
        _t1693 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1398 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1693,)
        unwrapped_fields1399 = fields1398
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1400 = unwrapped_fields1399[1]
        pretty_iceberg_locator(pp, field1400)
        newline(pp)
        field1401 = unwrapped_fields1399[2]
        pretty_iceberg_catalog_config(pp, field1401)
        newline(pp)
        field1402 = unwrapped_fields1399[3]
        pretty_gnf_columns(pp, field1402)
        field1403 = unwrapped_fields1399[4]
        if !isnothing(field1403)
            newline(pp)
            opt_val1404 = field1403
            pretty_iceberg_to_snapshot(pp, opt_val1404)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1413 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1413)
        write(pp, flat1413)
        return nothing
    else
        _dollar_dollar = msg
        fields1406 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1407 = fields1406
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_name")
        newline(pp)
        field1408 = unwrapped_fields1407[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1408))
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "namespace")
        field1409 = unwrapped_fields1407[2]
        if !isempty(field1409)
            newline(pp)
            for (i1694, elem1410) in enumerate(field1409)
                i1411 = i1694 - 1
                if (i1411 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1410))
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "warehouse")
        newline(pp)
        field1412 = unwrapped_fields1407[3]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1412))
        dedent!(pp)
        write(pp, ")")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1425 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1425)
        write(pp, flat1425)
        return nothing
    else
        _dollar_dollar = msg
        _t1695 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1414 = (_dollar_dollar.catalog_uri, _t1695, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1415 = fields1414
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "catalog_uri")
        newline(pp)
        field1416 = unwrapped_fields1415[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1416))
        dedent!(pp)
        write(pp, ")")
        field1417 = unwrapped_fields1415[2]
        if !isnothing(field1417)
            newline(pp)
            opt_val1418 = field1417
            pretty_iceberg_catalog_config_scope(pp, opt_val1418)
        end
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "properties")
        field1419 = unwrapped_fields1415[3]
        if !isempty(field1419)
            newline(pp)
            for (i1696, elem1420) in enumerate(field1419)
                i1421 = i1696 - 1
                if (i1421 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1420)
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "auth_properties")
        field1422 = unwrapped_fields1415[4]
        if !isempty(field1422)
            newline(pp)
            for (i1697, elem1423) in enumerate(field1422)
                i1424 = i1697 - 1
                if (i1424 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1423)
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
    flat1427 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1427)
        write(pp, flat1427)
        return nothing
    else
        fields1426 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1426))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1432 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1432)
        write(pp, flat1432)
        return nothing
    else
        _dollar_dollar = msg
        fields1428 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1429 = fields1428
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1430 = unwrapped_fields1429[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1430))
        newline(pp)
        field1431 = unwrapped_fields1429[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1431))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1434 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1434)
        write(pp, flat1434)
        return nothing
    else
        fields1433 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1433))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1437 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1437)
        write(pp, flat1437)
        return nothing
    else
        _dollar_dollar = msg
        fields1435 = _dollar_dollar.fragment_id
        unwrapped_fields1436 = fields1435
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1436)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1442 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1442)
        write(pp, flat1442)
        return nothing
    else
        _dollar_dollar = msg
        fields1438 = _dollar_dollar.relations
        unwrapped_fields1439 = fields1438
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1439)
            newline(pp)
            for (i1698, elem1440) in enumerate(unwrapped_fields1439)
                i1441 = i1698 - 1
                if (i1441 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1440)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1447 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1447)
        write(pp, flat1447)
        return nothing
    else
        _dollar_dollar = msg
        fields1443 = _dollar_dollar.mappings
        unwrapped_fields1444 = fields1443
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1444)
            newline(pp)
            for (i1699, elem1445) in enumerate(unwrapped_fields1444)
                i1446 = i1699 - 1
                if (i1446 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1445)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1452 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1452)
        write(pp, flat1452)
        return nothing
    else
        _dollar_dollar = msg
        fields1448 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1449 = fields1448
        field1450 = unwrapped_fields1449[1]
        pretty_edb_path(pp, field1450)
        write(pp, " ")
        field1451 = unwrapped_fields1449[2]
        pretty_relation_id(pp, field1451)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1456 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1456)
        write(pp, flat1456)
        return nothing
    else
        fields1453 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1453)
            newline(pp)
            for (i1700, elem1454) in enumerate(fields1453)
                i1455 = i1700 - 1
                if (i1455 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1454)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1467 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1467)
        write(pp, flat1467)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1701 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1701 = nothing
        end
        deconstruct_result1465 = _t1701
        if !isnothing(deconstruct_result1465)
            unwrapped1466 = deconstruct_result1465
            pretty_demand(pp, unwrapped1466)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1702 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1702 = nothing
            end
            deconstruct_result1463 = _t1702
            if !isnothing(deconstruct_result1463)
                unwrapped1464 = deconstruct_result1463
                pretty_output(pp, unwrapped1464)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1703 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1703 = nothing
                end
                deconstruct_result1461 = _t1703
                if !isnothing(deconstruct_result1461)
                    unwrapped1462 = deconstruct_result1461
                    pretty_what_if(pp, unwrapped1462)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1704 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1704 = nothing
                    end
                    deconstruct_result1459 = _t1704
                    if !isnothing(deconstruct_result1459)
                        unwrapped1460 = deconstruct_result1459
                        pretty_abort(pp, unwrapped1460)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1705 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1705 = nothing
                        end
                        deconstruct_result1457 = _t1705
                        if !isnothing(deconstruct_result1457)
                            unwrapped1458 = deconstruct_result1457
                            pretty_export(pp, unwrapped1458)
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
    flat1470 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1470)
        write(pp, flat1470)
        return nothing
    else
        _dollar_dollar = msg
        fields1468 = _dollar_dollar.relation_id
        unwrapped_fields1469 = fields1468
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1469)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1475 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1475)
        write(pp, flat1475)
        return nothing
    else
        _dollar_dollar = msg
        fields1471 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1472 = fields1471
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1473 = unwrapped_fields1472[1]
        pretty_name(pp, field1473)
        newline(pp)
        field1474 = unwrapped_fields1472[2]
        pretty_relation_id(pp, field1474)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1480 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1480)
        write(pp, flat1480)
        return nothing
    else
        _dollar_dollar = msg
        fields1476 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1477 = fields1476
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1478 = unwrapped_fields1477[1]
        pretty_name(pp, field1478)
        newline(pp)
        field1479 = unwrapped_fields1477[2]
        pretty_epoch(pp, field1479)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1486 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1486)
        write(pp, flat1486)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1706 = _dollar_dollar.name
        else
            _t1706 = nothing
        end
        fields1481 = (_t1706, _dollar_dollar.relation_id,)
        unwrapped_fields1482 = fields1481
        write(pp, "(abort")
        indent_sexp!(pp)
        field1483 = unwrapped_fields1482[1]
        if !isnothing(field1483)
            newline(pp)
            opt_val1484 = field1483
            pretty_name(pp, opt_val1484)
        end
        newline(pp)
        field1485 = unwrapped_fields1482[2]
        pretty_relation_id(pp, field1485)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1491 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1491)
        write(pp, flat1491)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1707 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1707 = nothing
        end
        deconstruct_result1489 = _t1707
        if !isnothing(deconstruct_result1489)
            unwrapped1490 = deconstruct_result1489
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1490)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1708 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1708 = nothing
            end
            deconstruct_result1487 = _t1708
            if !isnothing(deconstruct_result1487)
                unwrapped1488 = deconstruct_result1487
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1488)
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
    flat1502 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1502)
        write(pp, flat1502)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1709 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1709 = nothing
        end
        deconstruct_result1497 = _t1709
        if !isnothing(deconstruct_result1497)
            unwrapped1498 = deconstruct_result1497
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1499 = unwrapped1498[1]
            pretty_export_csv_path(pp, field1499)
            newline(pp)
            field1500 = unwrapped1498[2]
            pretty_export_csv_source(pp, field1500)
            newline(pp)
            field1501 = unwrapped1498[3]
            pretty_csv_config(pp, field1501)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1711 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1710 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1711,)
            else
                _t1710 = nothing
            end
            deconstruct_result1492 = _t1710
            if !isnothing(deconstruct_result1492)
                unwrapped1493 = deconstruct_result1492
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1494 = unwrapped1493[1]
                pretty_export_csv_path(pp, field1494)
                newline(pp)
                field1495 = unwrapped1493[2]
                pretty_export_csv_columns_list(pp, field1495)
                newline(pp)
                field1496 = unwrapped1493[3]
                pretty_config_dict(pp, field1496)
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
    flat1504 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1504)
        write(pp, flat1504)
        return nothing
    else
        fields1503 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1503))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1511 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1511)
        write(pp, flat1511)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1712 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1712 = nothing
        end
        deconstruct_result1507 = _t1712
        if !isnothing(deconstruct_result1507)
            unwrapped1508 = deconstruct_result1507
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1508)
                newline(pp)
                for (i1713, elem1509) in enumerate(unwrapped1508)
                    i1510 = i1713 - 1
                    if (i1510 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1509)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1714 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1714 = nothing
            end
            deconstruct_result1505 = _t1714
            if !isnothing(deconstruct_result1505)
                unwrapped1506 = deconstruct_result1505
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1506)
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
    flat1516 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1516)
        write(pp, flat1516)
        return nothing
    else
        _dollar_dollar = msg
        fields1512 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1513 = fields1512
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1514 = unwrapped_fields1513[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1514))
        newline(pp)
        field1515 = unwrapped_fields1513[2]
        pretty_relation_id(pp, field1515)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1520 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1520)
        write(pp, flat1520)
        return nothing
    else
        fields1517 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1517)
            newline(pp)
            for (i1715, elem1518) in enumerate(fields1517)
                i1519 = i1715 - 1
                if (i1519 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1518)
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
        _t1716 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1521 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, _dollar_dollar.columns, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1716,)
        unwrapped_fields1522 = fields1521
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1523 = unwrapped_fields1522[1]
        pretty_iceberg_locator(pp, field1523)
        newline(pp)
        field1524 = unwrapped_fields1522[2]
        pretty_iceberg_catalog_config(pp, field1524)
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_def")
        newline(pp)
        field1525 = unwrapped_fields1522[3]
        pretty_relation_id(pp, field1525)
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "columns")
        field1526 = unwrapped_fields1522[4]
        if !isempty(field1526)
            newline(pp)
            for (i1717, elem1527) in enumerate(field1526)
                i1528 = i1717 - 1
                if (i1528 > 0)
                    newline(pp)
                end
                pretty_export_iceberg_column(pp, elem1527)
            end
        end
        dedent!(pp)
        write(pp, ")")
        newline(pp)
        write(pp, "(")
        newline(pp)
        write(pp, "table_properties")
        field1529 = unwrapped_fields1522[5]
        if !isempty(field1529)
            newline(pp)
            for (i1718, elem1530) in enumerate(field1529)
                i1531 = i1718 - 1
                if (i1531 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1530)
            end
        end
        dedent!(pp)
        write(pp, ")")
        field1532 = unwrapped_fields1522[6]
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

function pretty_export_iceberg_column(pp::PrettyPrinter, msg::Proto.ExportIcebergColumn)
    flat1539 = try_flat(pp, msg, pretty_export_iceberg_column)
    if !isnothing(flat1539)
        write(pp, flat1539)
        return nothing
    else
        _dollar_dollar = msg
        fields1535 = (_dollar_dollar.name, _dollar_dollar.nullable,)
        unwrapped_fields1536 = fields1535
        write(pp, "(iceberg_column")
        indent_sexp!(pp)
        newline(pp)
        field1537 = unwrapped_fields1536[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1537))
        newline(pp)
        field1538 = unwrapped_fields1536[2]
        pretty_boolean_value(pp, field1538)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1763, _rid) in enumerate(msg.ids)
        _idx = i1763 - 1
        newline(pp)
        write(pp, "(")
        _t1764 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1764)
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
    for (i1765, _elem) in enumerate(msg.keys)
        _idx = i1765 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1766, _elem) in enumerate(msg.values)
        _idx = i1766 - 1
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
    for (i1767, _elem) in enumerate(msg.columns)
        _idx = i1767 - 1
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
