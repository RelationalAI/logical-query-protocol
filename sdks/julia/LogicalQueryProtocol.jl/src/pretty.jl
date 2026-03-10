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
    _t1588 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1588
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1589 = Proto.Value(value=OneOf(:int_value, v))
    return _t1589
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1590 = Proto.Value(value=OneOf(:float_value, v))
    return _t1590
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1591 = Proto.Value(value=OneOf(:string_value, v))
    return _t1591
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1592 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1592
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1593 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1593
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1594 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1594,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1595 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1595,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1596 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1596,))
            end
        end
    end
    _t1597 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1597,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1598 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1598,))
    _t1599 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1599,))
    if msg.new_line != ""
        _t1600 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1600,))
    end
    _t1601 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1601,))
    _t1602 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1602,))
    _t1603 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1603,))
    if msg.comment != ""
        _t1604 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1604,))
    end
    for missing_string in msg.missing_strings
        _t1605 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1605,))
    end
    _t1606 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1606,))
    _t1607 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1607,))
    _t1608 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1608,))
    if msg.partition_size_mb != 0
        _t1609 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1609,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1610 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1610,))
    _t1611 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1611,))
    _t1612 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1612,))
    _t1613 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1613,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1614 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1614,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1615 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1615,))
        end
    end
    _t1616 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1616,))
    _t1617 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1617,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1618 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1618,))
    end
    if !isnothing(msg.compression)
        _t1619 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1619,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1620 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1620,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1621 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1621,))
    end
    if !isnothing(msg.syntax_delim)
        _t1622 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1622,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1623 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1623,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1624 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1624,))
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
        _t1625 = nothing
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
    flat719 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat719)
        write(pp, flat719)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1420 = _dollar_dollar.configure
        else
            _t1420 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1421 = _dollar_dollar.sync
        else
            _t1421 = nothing
        end
        fields710 = (_t1420, _t1421, _dollar_dollar.epochs,)
        unwrapped_fields711 = fields710
        write(pp, "(transaction")
        indent_sexp!(pp)
        field712 = unwrapped_fields711[1]
        if !isnothing(field712)
            newline(pp)
            opt_val713 = field712
            pretty_configure(pp, opt_val713)
        end
        field714 = unwrapped_fields711[2]
        if !isnothing(field714)
            newline(pp)
            opt_val715 = field714
            pretty_sync(pp, opt_val715)
        end
        field716 = unwrapped_fields711[3]
        if !isempty(field716)
            newline(pp)
            for (i1422, elem717) in enumerate(field716)
                i718 = i1422 - 1
                if (i718 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem717)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat722 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat722)
        write(pp, flat722)
        return nothing
    else
        _dollar_dollar = msg
        _t1423 = deconstruct_configure(pp, _dollar_dollar)
        fields720 = _t1423
        unwrapped_fields721 = fields720
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields721)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat726 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat726)
        write(pp, flat726)
        return nothing
    else
        fields723 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields723)
            newline(pp)
            for (i1424, elem724) in enumerate(fields723)
                i725 = i1424 - 1
                if (i725 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem724)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat731 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat731)
        write(pp, flat731)
        return nothing
    else
        _dollar_dollar = msg
        fields727 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields728 = fields727
        write(pp, ":")
        field729 = unwrapped_fields728[1]
        write(pp, field729)
        write(pp, " ")
        field730 = unwrapped_fields728[2]
        pretty_raw_value(pp, field730)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat757 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat757)
        write(pp, flat757)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1425 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1425 = nothing
        end
        deconstruct_result755 = _t1425
        if !isnothing(deconstruct_result755)
            unwrapped756 = deconstruct_result755
            pretty_raw_date(pp, unwrapped756)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1426 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1426 = nothing
            end
            deconstruct_result753 = _t1426
            if !isnothing(deconstruct_result753)
                unwrapped754 = deconstruct_result753
                pretty_raw_datetime(pp, unwrapped754)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1427 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1427 = nothing
                end
                deconstruct_result751 = _t1427
                if !isnothing(deconstruct_result751)
                    unwrapped752 = deconstruct_result751
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped752))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1428 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1428 = nothing
                    end
                    deconstruct_result749 = _t1428
                    if !isnothing(deconstruct_result749)
                        unwrapped750 = deconstruct_result749
                        write(pp, (string(Int64(unwrapped750)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1429 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1429 = nothing
                        end
                        deconstruct_result747 = _t1429
                        if !isnothing(deconstruct_result747)
                            unwrapped748 = deconstruct_result747
                            write(pp, string(unwrapped748))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1430 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1430 = nothing
                            end
                            deconstruct_result745 = _t1430
                            if !isnothing(deconstruct_result745)
                                unwrapped746 = deconstruct_result745
                                write(pp, format_float32_literal(unwrapped746))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1431 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1431 = nothing
                                end
                                deconstruct_result743 = _t1431
                                if !isnothing(deconstruct_result743)
                                    unwrapped744 = deconstruct_result743
                                    write(pp, lowercase(string(unwrapped744)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1432 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1432 = nothing
                                    end
                                    deconstruct_result741 = _t1432
                                    if !isnothing(deconstruct_result741)
                                        unwrapped742 = deconstruct_result741
                                        write(pp, (string(Int64(unwrapped742)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1433 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1433 = nothing
                                        end
                                        deconstruct_result739 = _t1433
                                        if !isnothing(deconstruct_result739)
                                            unwrapped740 = deconstruct_result739
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped740))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1434 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1434 = nothing
                                            end
                                            deconstruct_result737 = _t1434
                                            if !isnothing(deconstruct_result737)
                                                unwrapped738 = deconstruct_result737
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped738))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1435 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1435 = nothing
                                                end
                                                deconstruct_result735 = _t1435
                                                if !isnothing(deconstruct_result735)
                                                    unwrapped736 = deconstruct_result735
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped736))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1436 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1436 = nothing
                                                    end
                                                    deconstruct_result733 = _t1436
                                                    if !isnothing(deconstruct_result733)
                                                        unwrapped734 = deconstruct_result733
                                                        pretty_boolean_value(pp, unwrapped734)
                                                    else
                                                        fields732 = msg
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
    flat763 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat763)
        write(pp, flat763)
        return nothing
    else
        _dollar_dollar = msg
        fields758 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields759 = fields758
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field760 = unwrapped_fields759[1]
        write(pp, string(field760))
        newline(pp)
        field761 = unwrapped_fields759[2]
        write(pp, string(field761))
        newline(pp)
        field762 = unwrapped_fields759[3]
        write(pp, string(field762))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat774 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat774)
        write(pp, flat774)
        return nothing
    else
        _dollar_dollar = msg
        fields764 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields765 = fields764
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field766 = unwrapped_fields765[1]
        write(pp, string(field766))
        newline(pp)
        field767 = unwrapped_fields765[2]
        write(pp, string(field767))
        newline(pp)
        field768 = unwrapped_fields765[3]
        write(pp, string(field768))
        newline(pp)
        field769 = unwrapped_fields765[4]
        write(pp, string(field769))
        newline(pp)
        field770 = unwrapped_fields765[5]
        write(pp, string(field770))
        newline(pp)
        field771 = unwrapped_fields765[6]
        write(pp, string(field771))
        field772 = unwrapped_fields765[7]
        if !isnothing(field772)
            newline(pp)
            opt_val773 = field772
            write(pp, string(opt_val773))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1437 = ()
    else
        _t1437 = nothing
    end
    deconstruct_result777 = _t1437
    if !isnothing(deconstruct_result777)
        unwrapped778 = deconstruct_result777
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1438 = ()
        else
            _t1438 = nothing
        end
        deconstruct_result775 = _t1438
        if !isnothing(deconstruct_result775)
            unwrapped776 = deconstruct_result775
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat783 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat783)
        write(pp, flat783)
        return nothing
    else
        _dollar_dollar = msg
        fields779 = _dollar_dollar.fragments
        unwrapped_fields780 = fields779
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields780)
            newline(pp)
            for (i1439, elem781) in enumerate(unwrapped_fields780)
                i782 = i1439 - 1
                if (i782 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem781)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat786 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat786)
        write(pp, flat786)
        return nothing
    else
        _dollar_dollar = msg
        fields784 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields785 = fields784
        write(pp, ":")
        write(pp, unwrapped_fields785)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat793 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat793)
        write(pp, flat793)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1440 = _dollar_dollar.writes
        else
            _t1440 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1441 = _dollar_dollar.reads
        else
            _t1441 = nothing
        end
        fields787 = (_t1440, _t1441,)
        unwrapped_fields788 = fields787
        write(pp, "(epoch")
        indent_sexp!(pp)
        field789 = unwrapped_fields788[1]
        if !isnothing(field789)
            newline(pp)
            opt_val790 = field789
            pretty_epoch_writes(pp, opt_val790)
        end
        field791 = unwrapped_fields788[2]
        if !isnothing(field791)
            newline(pp)
            opt_val792 = field791
            pretty_epoch_reads(pp, opt_val792)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat797 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat797)
        write(pp, flat797)
        return nothing
    else
        fields794 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields794)
            newline(pp)
            for (i1442, elem795) in enumerate(fields794)
                i796 = i1442 - 1
                if (i796 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem795)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat806 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat806)
        write(pp, flat806)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1443 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1443 = nothing
        end
        deconstruct_result804 = _t1443
        if !isnothing(deconstruct_result804)
            unwrapped805 = deconstruct_result804
            pretty_define(pp, unwrapped805)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1444 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1444 = nothing
            end
            deconstruct_result802 = _t1444
            if !isnothing(deconstruct_result802)
                unwrapped803 = deconstruct_result802
                pretty_undefine(pp, unwrapped803)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1445 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1445 = nothing
                end
                deconstruct_result800 = _t1445
                if !isnothing(deconstruct_result800)
                    unwrapped801 = deconstruct_result800
                    pretty_context(pp, unwrapped801)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1446 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1446 = nothing
                    end
                    deconstruct_result798 = _t1446
                    if !isnothing(deconstruct_result798)
                        unwrapped799 = deconstruct_result798
                        pretty_snapshot(pp, unwrapped799)
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
    flat809 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat809)
        write(pp, flat809)
        return nothing
    else
        _dollar_dollar = msg
        fields807 = _dollar_dollar.fragment
        unwrapped_fields808 = fields807
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields808)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat816 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat816)
        write(pp, flat816)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields810 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields811 = fields810
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field812 = unwrapped_fields811[1]
        pretty_new_fragment_id(pp, field812)
        field813 = unwrapped_fields811[2]
        if !isempty(field813)
            newline(pp)
            for (i1447, elem814) in enumerate(field813)
                i815 = i1447 - 1
                if (i815 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem814)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat818 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat818)
        write(pp, flat818)
        return nothing
    else
        fields817 = msg
        pretty_fragment_id(pp, fields817)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat827 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat827)
        write(pp, flat827)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1448 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1448 = nothing
        end
        deconstruct_result825 = _t1448
        if !isnothing(deconstruct_result825)
            unwrapped826 = deconstruct_result825
            pretty_def(pp, unwrapped826)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1449 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1449 = nothing
            end
            deconstruct_result823 = _t1449
            if !isnothing(deconstruct_result823)
                unwrapped824 = deconstruct_result823
                pretty_algorithm(pp, unwrapped824)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1450 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1450 = nothing
                end
                deconstruct_result821 = _t1450
                if !isnothing(deconstruct_result821)
                    unwrapped822 = deconstruct_result821
                    pretty_constraint(pp, unwrapped822)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1451 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1451 = nothing
                    end
                    deconstruct_result819 = _t1451
                    if !isnothing(deconstruct_result819)
                        unwrapped820 = deconstruct_result819
                        pretty_data(pp, unwrapped820)
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
    flat834 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat834)
        write(pp, flat834)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1452 = _dollar_dollar.attrs
        else
            _t1452 = nothing
        end
        fields828 = (_dollar_dollar.name, _dollar_dollar.body, _t1452,)
        unwrapped_fields829 = fields828
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field830 = unwrapped_fields829[1]
        pretty_relation_id(pp, field830)
        newline(pp)
        field831 = unwrapped_fields829[2]
        pretty_abstraction(pp, field831)
        field832 = unwrapped_fields829[3]
        if !isnothing(field832)
            newline(pp)
            opt_val833 = field832
            pretty_attrs(pp, opt_val833)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat839 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat839)
        write(pp, flat839)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1454 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1453 = _t1454
        else
            _t1453 = nothing
        end
        deconstruct_result837 = _t1453
        if !isnothing(deconstruct_result837)
            unwrapped838 = deconstruct_result837
            write(pp, ":")
            write(pp, unwrapped838)
        else
            _dollar_dollar = msg
            _t1455 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result835 = _t1455
            if !isnothing(deconstruct_result835)
                unwrapped836 = deconstruct_result835
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped836))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat844 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat844)
        write(pp, flat844)
        return nothing
    else
        _dollar_dollar = msg
        _t1456 = deconstruct_bindings(pp, _dollar_dollar)
        fields840 = (_t1456, _dollar_dollar.value,)
        unwrapped_fields841 = fields840
        write(pp, "(")
        indent!(pp)
        field842 = unwrapped_fields841[1]
        pretty_bindings(pp, field842)
        newline(pp)
        field843 = unwrapped_fields841[2]
        pretty_formula(pp, field843)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat852 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat852)
        write(pp, flat852)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1457 = _dollar_dollar[2]
        else
            _t1457 = nothing
        end
        fields845 = (_dollar_dollar[1], _t1457,)
        unwrapped_fields846 = fields845
        write(pp, "[")
        indent!(pp)
        field847 = unwrapped_fields846[1]
        for (i1458, elem848) in enumerate(field847)
            i849 = i1458 - 1
            if (i849 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem848)
        end
        field850 = unwrapped_fields846[2]
        if !isnothing(field850)
            newline(pp)
            opt_val851 = field850
            pretty_value_bindings(pp, opt_val851)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat857 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat857)
        write(pp, flat857)
        return nothing
    else
        _dollar_dollar = msg
        fields853 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields854 = fields853
        field855 = unwrapped_fields854[1]
        write(pp, field855)
        write(pp, "::")
        field856 = unwrapped_fields854[2]
        pretty_type(pp, field856)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat886 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat886)
        write(pp, flat886)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1459 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1459 = nothing
        end
        deconstruct_result884 = _t1459
        if !isnothing(deconstruct_result884)
            unwrapped885 = deconstruct_result884
            pretty_unspecified_type(pp, unwrapped885)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1460 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1460 = nothing
            end
            deconstruct_result882 = _t1460
            if !isnothing(deconstruct_result882)
                unwrapped883 = deconstruct_result882
                pretty_string_type(pp, unwrapped883)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1461 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1461 = nothing
                end
                deconstruct_result880 = _t1461
                if !isnothing(deconstruct_result880)
                    unwrapped881 = deconstruct_result880
                    pretty_int_type(pp, unwrapped881)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1462 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1462 = nothing
                    end
                    deconstruct_result878 = _t1462
                    if !isnothing(deconstruct_result878)
                        unwrapped879 = deconstruct_result878
                        pretty_float_type(pp, unwrapped879)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1463 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1463 = nothing
                        end
                        deconstruct_result876 = _t1463
                        if !isnothing(deconstruct_result876)
                            unwrapped877 = deconstruct_result876
                            pretty_uint128_type(pp, unwrapped877)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1464 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1464 = nothing
                            end
                            deconstruct_result874 = _t1464
                            if !isnothing(deconstruct_result874)
                                unwrapped875 = deconstruct_result874
                                pretty_int128_type(pp, unwrapped875)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1465 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1465 = nothing
                                end
                                deconstruct_result872 = _t1465
                                if !isnothing(deconstruct_result872)
                                    unwrapped873 = deconstruct_result872
                                    pretty_date_type(pp, unwrapped873)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1466 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1466 = nothing
                                    end
                                    deconstruct_result870 = _t1466
                                    if !isnothing(deconstruct_result870)
                                        unwrapped871 = deconstruct_result870
                                        pretty_datetime_type(pp, unwrapped871)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1467 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1467 = nothing
                                        end
                                        deconstruct_result868 = _t1467
                                        if !isnothing(deconstruct_result868)
                                            unwrapped869 = deconstruct_result868
                                            pretty_missing_type(pp, unwrapped869)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1468 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1468 = nothing
                                            end
                                            deconstruct_result866 = _t1468
                                            if !isnothing(deconstruct_result866)
                                                unwrapped867 = deconstruct_result866
                                                pretty_decimal_type(pp, unwrapped867)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1469 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1469 = nothing
                                                end
                                                deconstruct_result864 = _t1469
                                                if !isnothing(deconstruct_result864)
                                                    unwrapped865 = deconstruct_result864
                                                    pretty_boolean_type(pp, unwrapped865)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1470 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1470 = nothing
                                                    end
                                                    deconstruct_result862 = _t1470
                                                    if !isnothing(deconstruct_result862)
                                                        unwrapped863 = deconstruct_result862
                                                        pretty_int32_type(pp, unwrapped863)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1471 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1471 = nothing
                                                        end
                                                        deconstruct_result860 = _t1471
                                                        if !isnothing(deconstruct_result860)
                                                            unwrapped861 = deconstruct_result860
                                                            pretty_float32_type(pp, unwrapped861)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1472 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1472 = nothing
                                                            end
                                                            deconstruct_result858 = _t1472
                                                            if !isnothing(deconstruct_result858)
                                                                unwrapped859 = deconstruct_result858
                                                                pretty_uint32_type(pp, unwrapped859)
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
    fields887 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields888 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields889 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields890 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields891 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields892 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields893 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields894 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields895 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat900 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat900)
        write(pp, flat900)
        return nothing
    else
        _dollar_dollar = msg
        fields896 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields897 = fields896
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field898 = unwrapped_fields897[1]
        write(pp, string(field898))
        newline(pp)
        field899 = unwrapped_fields897[2]
        write(pp, string(field899))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields901 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields902 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields903 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields904 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat908 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat908)
        write(pp, flat908)
        return nothing
    else
        fields905 = msg
        write(pp, "|")
        if !isempty(fields905)
            write(pp, " ")
            for (i1473, elem906) in enumerate(fields905)
                i907 = i1473 - 1
                if (i907 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem906)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat935 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat935)
        write(pp, flat935)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1474 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1474 = nothing
        end
        deconstruct_result933 = _t1474
        if !isnothing(deconstruct_result933)
            unwrapped934 = deconstruct_result933
            pretty_true(pp, unwrapped934)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1475 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1475 = nothing
            end
            deconstruct_result931 = _t1475
            if !isnothing(deconstruct_result931)
                unwrapped932 = deconstruct_result931
                pretty_false(pp, unwrapped932)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1476 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1476 = nothing
                end
                deconstruct_result929 = _t1476
                if !isnothing(deconstruct_result929)
                    unwrapped930 = deconstruct_result929
                    pretty_exists(pp, unwrapped930)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1477 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1477 = nothing
                    end
                    deconstruct_result927 = _t1477
                    if !isnothing(deconstruct_result927)
                        unwrapped928 = deconstruct_result927
                        pretty_reduce(pp, unwrapped928)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1478 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1478 = nothing
                        end
                        deconstruct_result925 = _t1478
                        if !isnothing(deconstruct_result925)
                            unwrapped926 = deconstruct_result925
                            pretty_conjunction(pp, unwrapped926)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1479 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1479 = nothing
                            end
                            deconstruct_result923 = _t1479
                            if !isnothing(deconstruct_result923)
                                unwrapped924 = deconstruct_result923
                                pretty_disjunction(pp, unwrapped924)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1480 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1480 = nothing
                                end
                                deconstruct_result921 = _t1480
                                if !isnothing(deconstruct_result921)
                                    unwrapped922 = deconstruct_result921
                                    pretty_not(pp, unwrapped922)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1481 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1481 = nothing
                                    end
                                    deconstruct_result919 = _t1481
                                    if !isnothing(deconstruct_result919)
                                        unwrapped920 = deconstruct_result919
                                        pretty_ffi(pp, unwrapped920)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1482 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1482 = nothing
                                        end
                                        deconstruct_result917 = _t1482
                                        if !isnothing(deconstruct_result917)
                                            unwrapped918 = deconstruct_result917
                                            pretty_atom(pp, unwrapped918)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1483 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1483 = nothing
                                            end
                                            deconstruct_result915 = _t1483
                                            if !isnothing(deconstruct_result915)
                                                unwrapped916 = deconstruct_result915
                                                pretty_pragma(pp, unwrapped916)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1484 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1484 = nothing
                                                end
                                                deconstruct_result913 = _t1484
                                                if !isnothing(deconstruct_result913)
                                                    unwrapped914 = deconstruct_result913
                                                    pretty_primitive(pp, unwrapped914)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1485 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1485 = nothing
                                                    end
                                                    deconstruct_result911 = _t1485
                                                    if !isnothing(deconstruct_result911)
                                                        unwrapped912 = deconstruct_result911
                                                        pretty_rel_atom(pp, unwrapped912)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1486 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1486 = nothing
                                                        end
                                                        deconstruct_result909 = _t1486
                                                        if !isnothing(deconstruct_result909)
                                                            unwrapped910 = deconstruct_result909
                                                            pretty_cast(pp, unwrapped910)
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
    fields936 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields937 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat942 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat942)
        write(pp, flat942)
        return nothing
    else
        _dollar_dollar = msg
        _t1487 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields938 = (_t1487, _dollar_dollar.body.value,)
        unwrapped_fields939 = fields938
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field940 = unwrapped_fields939[1]
        pretty_bindings(pp, field940)
        newline(pp)
        field941 = unwrapped_fields939[2]
        pretty_formula(pp, field941)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat948 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat948)
        write(pp, flat948)
        return nothing
    else
        _dollar_dollar = msg
        fields943 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields944 = fields943
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field945 = unwrapped_fields944[1]
        pretty_abstraction(pp, field945)
        newline(pp)
        field946 = unwrapped_fields944[2]
        pretty_abstraction(pp, field946)
        newline(pp)
        field947 = unwrapped_fields944[3]
        pretty_terms(pp, field947)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat952 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat952)
        write(pp, flat952)
        return nothing
    else
        fields949 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields949)
            newline(pp)
            for (i1488, elem950) in enumerate(fields949)
                i951 = i1488 - 1
                if (i951 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem950)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat957 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat957)
        write(pp, flat957)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1489 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1489 = nothing
        end
        deconstruct_result955 = _t1489
        if !isnothing(deconstruct_result955)
            unwrapped956 = deconstruct_result955
            pretty_var(pp, unwrapped956)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1490 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1490 = nothing
            end
            deconstruct_result953 = _t1490
            if !isnothing(deconstruct_result953)
                unwrapped954 = deconstruct_result953
                pretty_value(pp, unwrapped954)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat960 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat960)
        write(pp, flat960)
        return nothing
    else
        _dollar_dollar = msg
        fields958 = _dollar_dollar.name
        unwrapped_fields959 = fields958
        write(pp, unwrapped_fields959)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat986 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat986)
        write(pp, flat986)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1491 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1491 = nothing
        end
        deconstruct_result984 = _t1491
        if !isnothing(deconstruct_result984)
            unwrapped985 = deconstruct_result984
            pretty_date(pp, unwrapped985)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1492 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1492 = nothing
            end
            deconstruct_result982 = _t1492
            if !isnothing(deconstruct_result982)
                unwrapped983 = deconstruct_result982
                pretty_datetime(pp, unwrapped983)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1493 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1493 = nothing
                end
                deconstruct_result980 = _t1493
                if !isnothing(deconstruct_result980)
                    unwrapped981 = deconstruct_result980
                    write(pp, format_string(pp, unwrapped981))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1494 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1494 = nothing
                    end
                    deconstruct_result978 = _t1494
                    if !isnothing(deconstruct_result978)
                        unwrapped979 = deconstruct_result978
                        write(pp, format_int32(pp, unwrapped979))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1495 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1495 = nothing
                        end
                        deconstruct_result976 = _t1495
                        if !isnothing(deconstruct_result976)
                            unwrapped977 = deconstruct_result976
                            write(pp, format_int(pp, unwrapped977))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1496 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1496 = nothing
                            end
                            deconstruct_result974 = _t1496
                            if !isnothing(deconstruct_result974)
                                unwrapped975 = deconstruct_result974
                                write(pp, format_float32(pp, unwrapped975))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1497 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1497 = nothing
                                end
                                deconstruct_result972 = _t1497
                                if !isnothing(deconstruct_result972)
                                    unwrapped973 = deconstruct_result972
                                    write(pp, format_float(pp, unwrapped973))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1498 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1498 = nothing
                                    end
                                    deconstruct_result970 = _t1498
                                    if !isnothing(deconstruct_result970)
                                        unwrapped971 = deconstruct_result970
                                        write(pp, format_uint32(pp, unwrapped971))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1499 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1499 = nothing
                                        end
                                        deconstruct_result968 = _t1499
                                        if !isnothing(deconstruct_result968)
                                            unwrapped969 = deconstruct_result968
                                            write(pp, format_uint128(pp, unwrapped969))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1500 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1500 = nothing
                                            end
                                            deconstruct_result966 = _t1500
                                            if !isnothing(deconstruct_result966)
                                                unwrapped967 = deconstruct_result966
                                                write(pp, format_int128(pp, unwrapped967))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1501 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1501 = nothing
                                                end
                                                deconstruct_result964 = _t1501
                                                if !isnothing(deconstruct_result964)
                                                    unwrapped965 = deconstruct_result964
                                                    write(pp, format_decimal(pp, unwrapped965))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1502 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1502 = nothing
                                                    end
                                                    deconstruct_result962 = _t1502
                                                    if !isnothing(deconstruct_result962)
                                                        unwrapped963 = deconstruct_result962
                                                        pretty_boolean_value(pp, unwrapped963)
                                                    else
                                                        fields961 = msg
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
    flat992 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat992)
        write(pp, flat992)
        return nothing
    else
        _dollar_dollar = msg
        fields987 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields988 = fields987
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field989 = unwrapped_fields988[1]
        write(pp, format_int(pp, field989))
        newline(pp)
        field990 = unwrapped_fields988[2]
        write(pp, format_int(pp, field990))
        newline(pp)
        field991 = unwrapped_fields988[3]
        write(pp, format_int(pp, field991))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1003 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1003)
        write(pp, flat1003)
        return nothing
    else
        _dollar_dollar = msg
        fields993 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields994 = fields993
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field995 = unwrapped_fields994[1]
        write(pp, format_int(pp, field995))
        newline(pp)
        field996 = unwrapped_fields994[2]
        write(pp, format_int(pp, field996))
        newline(pp)
        field997 = unwrapped_fields994[3]
        write(pp, format_int(pp, field997))
        newline(pp)
        field998 = unwrapped_fields994[4]
        write(pp, format_int(pp, field998))
        newline(pp)
        field999 = unwrapped_fields994[5]
        write(pp, format_int(pp, field999))
        newline(pp)
        field1000 = unwrapped_fields994[6]
        write(pp, format_int(pp, field1000))
        field1001 = unwrapped_fields994[7]
        if !isnothing(field1001)
            newline(pp)
            opt_val1002 = field1001
            write(pp, format_int(pp, opt_val1002))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1008 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1008)
        write(pp, flat1008)
        return nothing
    else
        _dollar_dollar = msg
        fields1004 = _dollar_dollar.args
        unwrapped_fields1005 = fields1004
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1005)
            newline(pp)
            for (i1503, elem1006) in enumerate(unwrapped_fields1005)
                i1007 = i1503 - 1
                if (i1007 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1006)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1013 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1013)
        write(pp, flat1013)
        return nothing
    else
        _dollar_dollar = msg
        fields1009 = _dollar_dollar.args
        unwrapped_fields1010 = fields1009
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1010)
            newline(pp)
            for (i1504, elem1011) in enumerate(unwrapped_fields1010)
                i1012 = i1504 - 1
                if (i1012 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1011)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1016 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1016)
        write(pp, flat1016)
        return nothing
    else
        _dollar_dollar = msg
        fields1014 = _dollar_dollar.arg
        unwrapped_fields1015 = fields1014
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1015)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1022 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1022)
        write(pp, flat1022)
        return nothing
    else
        _dollar_dollar = msg
        fields1017 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1018 = fields1017
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1019 = unwrapped_fields1018[1]
        pretty_name(pp, field1019)
        newline(pp)
        field1020 = unwrapped_fields1018[2]
        pretty_ffi_args(pp, field1020)
        newline(pp)
        field1021 = unwrapped_fields1018[3]
        pretty_terms(pp, field1021)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1024 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1024)
        write(pp, flat1024)
        return nothing
    else
        fields1023 = msg
        write(pp, ":")
        write(pp, fields1023)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1028 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1028)
        write(pp, flat1028)
        return nothing
    else
        fields1025 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1025)
            newline(pp)
            for (i1505, elem1026) in enumerate(fields1025)
                i1027 = i1505 - 1
                if (i1027 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1026)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1035 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1035)
        write(pp, flat1035)
        return nothing
    else
        _dollar_dollar = msg
        fields1029 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1030 = fields1029
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1031 = unwrapped_fields1030[1]
        pretty_relation_id(pp, field1031)
        field1032 = unwrapped_fields1030[2]
        if !isempty(field1032)
            newline(pp)
            for (i1506, elem1033) in enumerate(field1032)
                i1034 = i1506 - 1
                if (i1034 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1033)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1042 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1042)
        write(pp, flat1042)
        return nothing
    else
        _dollar_dollar = msg
        fields1036 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1037 = fields1036
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1038 = unwrapped_fields1037[1]
        pretty_name(pp, field1038)
        field1039 = unwrapped_fields1037[2]
        if !isempty(field1039)
            newline(pp)
            for (i1507, elem1040) in enumerate(field1039)
                i1041 = i1507 - 1
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

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1058 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1058)
        write(pp, flat1058)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1508 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1508 = nothing
        end
        guard_result1057 = _t1508
        if !isnothing(guard_result1057)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1509 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1509 = nothing
            end
            guard_result1056 = _t1509
            if !isnothing(guard_result1056)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1510 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1510 = nothing
                end
                guard_result1055 = _t1510
                if !isnothing(guard_result1055)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1511 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1511 = nothing
                    end
                    guard_result1054 = _t1511
                    if !isnothing(guard_result1054)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1512 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1512 = nothing
                        end
                        guard_result1053 = _t1512
                        if !isnothing(guard_result1053)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1513 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1513 = nothing
                            end
                            guard_result1052 = _t1513
                            if !isnothing(guard_result1052)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1514 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1514 = nothing
                                end
                                guard_result1051 = _t1514
                                if !isnothing(guard_result1051)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1515 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1515 = nothing
                                    end
                                    guard_result1050 = _t1515
                                    if !isnothing(guard_result1050)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1516 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1516 = nothing
                                        end
                                        guard_result1049 = _t1516
                                        if !isnothing(guard_result1049)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1043 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1044 = fields1043
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1045 = unwrapped_fields1044[1]
                                            pretty_name(pp, field1045)
                                            field1046 = unwrapped_fields1044[2]
                                            if !isempty(field1046)
                                                newline(pp)
                                                for (i1517, elem1047) in enumerate(field1046)
                                                    i1048 = i1517 - 1
                                                    if (i1048 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1047)
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
    flat1063 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1063)
        write(pp, flat1063)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1518 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1518 = nothing
        end
        fields1059 = _t1518
        unwrapped_fields1060 = fields1059
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1061 = unwrapped_fields1060[1]
        pretty_term(pp, field1061)
        newline(pp)
        field1062 = unwrapped_fields1060[2]
        pretty_term(pp, field1062)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1068 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1068)
        write(pp, flat1068)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1519 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1519 = nothing
        end
        fields1064 = _t1519
        unwrapped_fields1065 = fields1064
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1066 = unwrapped_fields1065[1]
        pretty_term(pp, field1066)
        newline(pp)
        field1067 = unwrapped_fields1065[2]
        pretty_term(pp, field1067)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1073 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1073)
        write(pp, flat1073)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1520 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1520 = nothing
        end
        fields1069 = _t1520
        unwrapped_fields1070 = fields1069
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1071 = unwrapped_fields1070[1]
        pretty_term(pp, field1071)
        newline(pp)
        field1072 = unwrapped_fields1070[2]
        pretty_term(pp, field1072)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1078 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1078)
        write(pp, flat1078)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1521 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1521 = nothing
        end
        fields1074 = _t1521
        unwrapped_fields1075 = fields1074
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1076 = unwrapped_fields1075[1]
        pretty_term(pp, field1076)
        newline(pp)
        field1077 = unwrapped_fields1075[2]
        pretty_term(pp, field1077)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1083 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1083)
        write(pp, flat1083)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1522 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1522 = nothing
        end
        fields1079 = _t1522
        unwrapped_fields1080 = fields1079
        write(pp, "(>=")
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

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1089 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1089)
        write(pp, flat1089)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1523 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1523 = nothing
        end
        fields1084 = _t1523
        unwrapped_fields1085 = fields1084
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1086 = unwrapped_fields1085[1]
        pretty_term(pp, field1086)
        newline(pp)
        field1087 = unwrapped_fields1085[2]
        pretty_term(pp, field1087)
        newline(pp)
        field1088 = unwrapped_fields1085[3]
        pretty_term(pp, field1088)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1095 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1095)
        write(pp, flat1095)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1524 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1524 = nothing
        end
        fields1090 = _t1524
        unwrapped_fields1091 = fields1090
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1092 = unwrapped_fields1091[1]
        pretty_term(pp, field1092)
        newline(pp)
        field1093 = unwrapped_fields1091[2]
        pretty_term(pp, field1093)
        newline(pp)
        field1094 = unwrapped_fields1091[3]
        pretty_term(pp, field1094)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1101 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1101)
        write(pp, flat1101)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1525 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1525 = nothing
        end
        fields1096 = _t1525
        unwrapped_fields1097 = fields1096
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1098 = unwrapped_fields1097[1]
        pretty_term(pp, field1098)
        newline(pp)
        field1099 = unwrapped_fields1097[2]
        pretty_term(pp, field1099)
        newline(pp)
        field1100 = unwrapped_fields1097[3]
        pretty_term(pp, field1100)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1107 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1107)
        write(pp, flat1107)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1526 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1526 = nothing
        end
        fields1102 = _t1526
        unwrapped_fields1103 = fields1102
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1104 = unwrapped_fields1103[1]
        pretty_term(pp, field1104)
        newline(pp)
        field1105 = unwrapped_fields1103[2]
        pretty_term(pp, field1105)
        newline(pp)
        field1106 = unwrapped_fields1103[3]
        pretty_term(pp, field1106)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1112 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1112)
        write(pp, flat1112)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1527 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1527 = nothing
        end
        deconstruct_result1110 = _t1527
        if !isnothing(deconstruct_result1110)
            unwrapped1111 = deconstruct_result1110
            pretty_specialized_value(pp, unwrapped1111)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1528 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1528 = nothing
            end
            deconstruct_result1108 = _t1528
            if !isnothing(deconstruct_result1108)
                unwrapped1109 = deconstruct_result1108
                pretty_term(pp, unwrapped1109)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1114 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1114)
        write(pp, flat1114)
        return nothing
    else
        fields1113 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1113)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1121 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1121)
        write(pp, flat1121)
        return nothing
    else
        _dollar_dollar = msg
        fields1115 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1116 = fields1115
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1117 = unwrapped_fields1116[1]
        pretty_name(pp, field1117)
        field1118 = unwrapped_fields1116[2]
        if !isempty(field1118)
            newline(pp)
            for (i1529, elem1119) in enumerate(field1118)
                i1120 = i1529 - 1
                if (i1120 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1119)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1126 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1126)
        write(pp, flat1126)
        return nothing
    else
        _dollar_dollar = msg
        fields1122 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1123 = fields1122
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1124 = unwrapped_fields1123[1]
        pretty_term(pp, field1124)
        newline(pp)
        field1125 = unwrapped_fields1123[2]
        pretty_term(pp, field1125)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1130 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1130)
        write(pp, flat1130)
        return nothing
    else
        fields1127 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1127)
            newline(pp)
            for (i1530, elem1128) in enumerate(fields1127)
                i1129 = i1530 - 1
                if (i1129 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1128)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1137 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1137)
        write(pp, flat1137)
        return nothing
    else
        _dollar_dollar = msg
        fields1131 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1132 = fields1131
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1133 = unwrapped_fields1132[1]
        pretty_name(pp, field1133)
        field1134 = unwrapped_fields1132[2]
        if !isempty(field1134)
            newline(pp)
            for (i1531, elem1135) in enumerate(field1134)
                i1136 = i1531 - 1
                if (i1136 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1135)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1144 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1144)
        write(pp, flat1144)
        return nothing
    else
        _dollar_dollar = msg
        fields1138 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1139 = fields1138
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1140 = unwrapped_fields1139[1]
        if !isempty(field1140)
            newline(pp)
            for (i1532, elem1141) in enumerate(field1140)
                i1142 = i1532 - 1
                if (i1142 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1141)
            end
        end
        newline(pp)
        field1143 = unwrapped_fields1139[2]
        pretty_script(pp, field1143)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1149 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1149)
        write(pp, flat1149)
        return nothing
    else
        _dollar_dollar = msg
        fields1145 = _dollar_dollar.constructs
        unwrapped_fields1146 = fields1145
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1146)
            newline(pp)
            for (i1533, elem1147) in enumerate(unwrapped_fields1146)
                i1148 = i1533 - 1
                if (i1148 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1147)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1154 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1154)
        write(pp, flat1154)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1534 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1534 = nothing
        end
        deconstruct_result1152 = _t1534
        if !isnothing(deconstruct_result1152)
            unwrapped1153 = deconstruct_result1152
            pretty_loop(pp, unwrapped1153)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1535 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1535 = nothing
            end
            deconstruct_result1150 = _t1535
            if !isnothing(deconstruct_result1150)
                unwrapped1151 = deconstruct_result1150
                pretty_instruction(pp, unwrapped1151)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1159 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1159)
        write(pp, flat1159)
        return nothing
    else
        _dollar_dollar = msg
        fields1155 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1156 = fields1155
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1157 = unwrapped_fields1156[1]
        pretty_init(pp, field1157)
        newline(pp)
        field1158 = unwrapped_fields1156[2]
        pretty_script(pp, field1158)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1163 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1163)
        write(pp, flat1163)
        return nothing
    else
        fields1160 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1160)
            newline(pp)
            for (i1536, elem1161) in enumerate(fields1160)
                i1162 = i1536 - 1
                if (i1162 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1161)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1174 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1174)
        write(pp, flat1174)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1537 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1537 = nothing
        end
        deconstruct_result1172 = _t1537
        if !isnothing(deconstruct_result1172)
            unwrapped1173 = deconstruct_result1172
            pretty_assign(pp, unwrapped1173)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1538 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1538 = nothing
            end
            deconstruct_result1170 = _t1538
            if !isnothing(deconstruct_result1170)
                unwrapped1171 = deconstruct_result1170
                pretty_upsert(pp, unwrapped1171)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1539 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1539 = nothing
                end
                deconstruct_result1168 = _t1539
                if !isnothing(deconstruct_result1168)
                    unwrapped1169 = deconstruct_result1168
                    pretty_break(pp, unwrapped1169)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1540 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1540 = nothing
                    end
                    deconstruct_result1166 = _t1540
                    if !isnothing(deconstruct_result1166)
                        unwrapped1167 = deconstruct_result1166
                        pretty_monoid_def(pp, unwrapped1167)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1541 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1541 = nothing
                        end
                        deconstruct_result1164 = _t1541
                        if !isnothing(deconstruct_result1164)
                            unwrapped1165 = deconstruct_result1164
                            pretty_monus_def(pp, unwrapped1165)
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
    flat1181 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1181)
        write(pp, flat1181)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1542 = _dollar_dollar.attrs
        else
            _t1542 = nothing
        end
        fields1175 = (_dollar_dollar.name, _dollar_dollar.body, _t1542,)
        unwrapped_fields1176 = fields1175
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1177 = unwrapped_fields1176[1]
        pretty_relation_id(pp, field1177)
        newline(pp)
        field1178 = unwrapped_fields1176[2]
        pretty_abstraction(pp, field1178)
        field1179 = unwrapped_fields1176[3]
        if !isnothing(field1179)
            newline(pp)
            opt_val1180 = field1179
            pretty_attrs(pp, opt_val1180)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1188 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1188)
        write(pp, flat1188)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1543 = _dollar_dollar.attrs
        else
            _t1543 = nothing
        end
        fields1182 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1543,)
        unwrapped_fields1183 = fields1182
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1184 = unwrapped_fields1183[1]
        pretty_relation_id(pp, field1184)
        newline(pp)
        field1185 = unwrapped_fields1183[2]
        pretty_abstraction_with_arity(pp, field1185)
        field1186 = unwrapped_fields1183[3]
        if !isnothing(field1186)
            newline(pp)
            opt_val1187 = field1186
            pretty_attrs(pp, opt_val1187)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1193 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1193)
        write(pp, flat1193)
        return nothing
    else
        _dollar_dollar = msg
        _t1544 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1189 = (_t1544, _dollar_dollar[1].value,)
        unwrapped_fields1190 = fields1189
        write(pp, "(")
        indent!(pp)
        field1191 = unwrapped_fields1190[1]
        pretty_bindings(pp, field1191)
        newline(pp)
        field1192 = unwrapped_fields1190[2]
        pretty_formula(pp, field1192)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1200 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1200)
        write(pp, flat1200)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1545 = _dollar_dollar.attrs
        else
            _t1545 = nothing
        end
        fields1194 = (_dollar_dollar.name, _dollar_dollar.body, _t1545,)
        unwrapped_fields1195 = fields1194
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1196 = unwrapped_fields1195[1]
        pretty_relation_id(pp, field1196)
        newline(pp)
        field1197 = unwrapped_fields1195[2]
        pretty_abstraction(pp, field1197)
        field1198 = unwrapped_fields1195[3]
        if !isnothing(field1198)
            newline(pp)
            opt_val1199 = field1198
            pretty_attrs(pp, opt_val1199)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1208 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1208)
        write(pp, flat1208)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1546 = _dollar_dollar.attrs
        else
            _t1546 = nothing
        end
        fields1201 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1546,)
        unwrapped_fields1202 = fields1201
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1203 = unwrapped_fields1202[1]
        pretty_monoid(pp, field1203)
        newline(pp)
        field1204 = unwrapped_fields1202[2]
        pretty_relation_id(pp, field1204)
        newline(pp)
        field1205 = unwrapped_fields1202[3]
        pretty_abstraction_with_arity(pp, field1205)
        field1206 = unwrapped_fields1202[4]
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

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1217 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1217)
        write(pp, flat1217)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1547 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1547 = nothing
        end
        deconstruct_result1215 = _t1547
        if !isnothing(deconstruct_result1215)
            unwrapped1216 = deconstruct_result1215
            pretty_or_monoid(pp, unwrapped1216)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1548 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1548 = nothing
            end
            deconstruct_result1213 = _t1548
            if !isnothing(deconstruct_result1213)
                unwrapped1214 = deconstruct_result1213
                pretty_min_monoid(pp, unwrapped1214)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1549 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1549 = nothing
                end
                deconstruct_result1211 = _t1549
                if !isnothing(deconstruct_result1211)
                    unwrapped1212 = deconstruct_result1211
                    pretty_max_monoid(pp, unwrapped1212)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1550 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1550 = nothing
                    end
                    deconstruct_result1209 = _t1550
                    if !isnothing(deconstruct_result1209)
                        unwrapped1210 = deconstruct_result1209
                        pretty_sum_monoid(pp, unwrapped1210)
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
    fields1218 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1221 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1221)
        write(pp, flat1221)
        return nothing
    else
        _dollar_dollar = msg
        fields1219 = _dollar_dollar.var"#type"
        unwrapped_fields1220 = fields1219
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1220)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1224 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1224)
        write(pp, flat1224)
        return nothing
    else
        _dollar_dollar = msg
        fields1222 = _dollar_dollar.var"#type"
        unwrapped_fields1223 = fields1222
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1223)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1227 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1227)
        write(pp, flat1227)
        return nothing
    else
        _dollar_dollar = msg
        fields1225 = _dollar_dollar.var"#type"
        unwrapped_fields1226 = fields1225
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1226)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1235 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1235)
        write(pp, flat1235)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1551 = _dollar_dollar.attrs
        else
            _t1551 = nothing
        end
        fields1228 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1551,)
        unwrapped_fields1229 = fields1228
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1230 = unwrapped_fields1229[1]
        pretty_monoid(pp, field1230)
        newline(pp)
        field1231 = unwrapped_fields1229[2]
        pretty_relation_id(pp, field1231)
        newline(pp)
        field1232 = unwrapped_fields1229[3]
        pretty_abstraction_with_arity(pp, field1232)
        field1233 = unwrapped_fields1229[4]
        if !isnothing(field1233)
            newline(pp)
            opt_val1234 = field1233
            pretty_attrs(pp, opt_val1234)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1242 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1242)
        write(pp, flat1242)
        return nothing
    else
        _dollar_dollar = msg
        fields1236 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1237 = fields1236
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1238 = unwrapped_fields1237[1]
        pretty_relation_id(pp, field1238)
        newline(pp)
        field1239 = unwrapped_fields1237[2]
        pretty_abstraction(pp, field1239)
        newline(pp)
        field1240 = unwrapped_fields1237[3]
        pretty_functional_dependency_keys(pp, field1240)
        newline(pp)
        field1241 = unwrapped_fields1237[4]
        pretty_functional_dependency_values(pp, field1241)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1246 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1246)
        write(pp, flat1246)
        return nothing
    else
        fields1243 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1243)
            newline(pp)
            for (i1552, elem1244) in enumerate(fields1243)
                i1245 = i1552 - 1
                if (i1245 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1244)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1250 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1250)
        write(pp, flat1250)
        return nothing
    else
        fields1247 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1247)
            newline(pp)
            for (i1553, elem1248) in enumerate(fields1247)
                i1249 = i1553 - 1
                if (i1249 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1248)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1257 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1257)
        write(pp, flat1257)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1554 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1554 = nothing
        end
        deconstruct_result1255 = _t1554
        if !isnothing(deconstruct_result1255)
            unwrapped1256 = deconstruct_result1255
            pretty_edb(pp, unwrapped1256)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1555 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1555 = nothing
            end
            deconstruct_result1253 = _t1555
            if !isnothing(deconstruct_result1253)
                unwrapped1254 = deconstruct_result1253
                pretty_betree_relation(pp, unwrapped1254)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1556 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1556 = nothing
                end
                deconstruct_result1251 = _t1556
                if !isnothing(deconstruct_result1251)
                    unwrapped1252 = deconstruct_result1251
                    pretty_csv_data(pp, unwrapped1252)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_edb(pp::PrettyPrinter, msg::Proto.EDB)
    flat1263 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1263)
        write(pp, flat1263)
        return nothing
    else
        _dollar_dollar = msg
        fields1258 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1259 = fields1258
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1260 = unwrapped_fields1259[1]
        pretty_relation_id(pp, field1260)
        newline(pp)
        field1261 = unwrapped_fields1259[2]
        pretty_edb_path(pp, field1261)
        newline(pp)
        field1262 = unwrapped_fields1259[3]
        pretty_edb_types(pp, field1262)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1267 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1267)
        write(pp, flat1267)
        return nothing
    else
        fields1264 = msg
        write(pp, "[")
        indent!(pp)
        for (i1557, elem1265) in enumerate(fields1264)
            i1266 = i1557 - 1
            if (i1266 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1265))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1271 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1271)
        write(pp, flat1271)
        return nothing
    else
        fields1268 = msg
        write(pp, "[")
        indent!(pp)
        for (i1558, elem1269) in enumerate(fields1268)
            i1270 = i1558 - 1
            if (i1270 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1269)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1276 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1276)
        write(pp, flat1276)
        return nothing
    else
        _dollar_dollar = msg
        fields1272 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1273 = fields1272
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1274 = unwrapped_fields1273[1]
        pretty_relation_id(pp, field1274)
        newline(pp)
        field1275 = unwrapped_fields1273[2]
        pretty_betree_info(pp, field1275)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1282 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1282)
        write(pp, flat1282)
        return nothing
    else
        _dollar_dollar = msg
        _t1559 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1277 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1559,)
        unwrapped_fields1278 = fields1277
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1279 = unwrapped_fields1278[1]
        pretty_betree_info_key_types(pp, field1279)
        newline(pp)
        field1280 = unwrapped_fields1278[2]
        pretty_betree_info_value_types(pp, field1280)
        newline(pp)
        field1281 = unwrapped_fields1278[3]
        pretty_config_dict(pp, field1281)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1286 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1286)
        write(pp, flat1286)
        return nothing
    else
        fields1283 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1283)
            newline(pp)
            for (i1560, elem1284) in enumerate(fields1283)
                i1285 = i1560 - 1
                if (i1285 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1284)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1290 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1290)
        write(pp, flat1290)
        return nothing
    else
        fields1287 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1287)
            newline(pp)
            for (i1561, elem1288) in enumerate(fields1287)
                i1289 = i1561 - 1
                if (i1289 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1288)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1297 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1297)
        write(pp, flat1297)
        return nothing
    else
        _dollar_dollar = msg
        fields1291 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1292 = fields1291
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1293 = unwrapped_fields1292[1]
        pretty_csvlocator(pp, field1293)
        newline(pp)
        field1294 = unwrapped_fields1292[2]
        pretty_csv_config(pp, field1294)
        newline(pp)
        field1295 = unwrapped_fields1292[3]
        pretty_gnf_columns(pp, field1295)
        newline(pp)
        field1296 = unwrapped_fields1292[4]
        pretty_csv_asof(pp, field1296)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1304 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1304)
        write(pp, flat1304)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1562 = _dollar_dollar.paths
        else
            _t1562 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1563 = String(copy(_dollar_dollar.inline_data))
        else
            _t1563 = nothing
        end
        fields1298 = (_t1562, _t1563,)
        unwrapped_fields1299 = fields1298
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1300 = unwrapped_fields1299[1]
        if !isnothing(field1300)
            newline(pp)
            opt_val1301 = field1300
            pretty_csv_locator_paths(pp, opt_val1301)
        end
        field1302 = unwrapped_fields1299[2]
        if !isnothing(field1302)
            newline(pp)
            opt_val1303 = field1302
            pretty_csv_locator_inline_data(pp, opt_val1303)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1308 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1308)
        write(pp, flat1308)
        return nothing
    else
        fields1305 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1305)
            newline(pp)
            for (i1564, elem1306) in enumerate(fields1305)
                i1307 = i1564 - 1
                if (i1307 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1306))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1310 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1310)
        write(pp, flat1310)
        return nothing
    else
        fields1309 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1309))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1313 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1313)
        write(pp, flat1313)
        return nothing
    else
        _dollar_dollar = msg
        _t1565 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1311 = _t1565
        unwrapped_fields1312 = fields1311
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1312)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1317 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1317)
        write(pp, flat1317)
        return nothing
    else
        fields1314 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1314)
            newline(pp)
            for (i1566, elem1315) in enumerate(fields1314)
                i1316 = i1566 - 1
                if (i1316 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1315)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1326 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1326)
        write(pp, flat1326)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1567 = _dollar_dollar.target_id
        else
            _t1567 = nothing
        end
        fields1318 = (_dollar_dollar.column_path, _t1567, _dollar_dollar.types,)
        unwrapped_fields1319 = fields1318
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1320 = unwrapped_fields1319[1]
        pretty_gnf_column_path(pp, field1320)
        field1321 = unwrapped_fields1319[2]
        if !isnothing(field1321)
            newline(pp)
            opt_val1322 = field1321
            pretty_relation_id(pp, opt_val1322)
        end
        newline(pp)
        write(pp, "[")
        field1323 = unwrapped_fields1319[3]
        for (i1568, elem1324) in enumerate(field1323)
            i1325 = i1568 - 1
            if (i1325 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1324)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1333 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1333)
        write(pp, flat1333)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1569 = _dollar_dollar[1]
        else
            _t1569 = nothing
        end
        deconstruct_result1331 = _t1569
        if !isnothing(deconstruct_result1331)
            unwrapped1332 = deconstruct_result1331
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1332))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1570 = _dollar_dollar
            else
                _t1570 = nothing
            end
            deconstruct_result1327 = _t1570
            if !isnothing(deconstruct_result1327)
                unwrapped1328 = deconstruct_result1327
                write(pp, "[")
                indent!(pp)
                for (i1571, elem1329) in enumerate(unwrapped1328)
                    i1330 = i1571 - 1
                    if (i1330 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1329))
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
    flat1335 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1335)
        write(pp, flat1335)
        return nothing
    else
        fields1334 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1334))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1338 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1338)
        write(pp, flat1338)
        return nothing
    else
        _dollar_dollar = msg
        fields1336 = _dollar_dollar.fragment_id
        unwrapped_fields1337 = fields1336
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1337)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1343 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1343)
        write(pp, flat1343)
        return nothing
    else
        _dollar_dollar = msg
        fields1339 = _dollar_dollar.relations
        unwrapped_fields1340 = fields1339
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1340)
            newline(pp)
            for (i1572, elem1341) in enumerate(unwrapped_fields1340)
                i1342 = i1572 - 1
                if (i1342 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1341)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1348 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1348)
        write(pp, flat1348)
        return nothing
    else
        _dollar_dollar = msg
        fields1344 = _dollar_dollar.mappings
        unwrapped_fields1345 = fields1344
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1345)
            newline(pp)
            for (i1573, elem1346) in enumerate(unwrapped_fields1345)
                i1347 = i1573 - 1
                if (i1347 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1346)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1353 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1353)
        write(pp, flat1353)
        return nothing
    else
        _dollar_dollar = msg
        fields1349 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1350 = fields1349
        field1351 = unwrapped_fields1350[1]
        pretty_edb_path(pp, field1351)
        write(pp, " ")
        field1352 = unwrapped_fields1350[2]
        pretty_relation_id(pp, field1352)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1357 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1357)
        write(pp, flat1357)
        return nothing
    else
        fields1354 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1354)
            newline(pp)
            for (i1574, elem1355) in enumerate(fields1354)
                i1356 = i1574 - 1
                if (i1356 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1355)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1368 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1368)
        write(pp, flat1368)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1575 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1575 = nothing
        end
        deconstruct_result1366 = _t1575
        if !isnothing(deconstruct_result1366)
            unwrapped1367 = deconstruct_result1366
            pretty_demand(pp, unwrapped1367)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1576 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1576 = nothing
            end
            deconstruct_result1364 = _t1576
            if !isnothing(deconstruct_result1364)
                unwrapped1365 = deconstruct_result1364
                pretty_output(pp, unwrapped1365)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1577 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1577 = nothing
                end
                deconstruct_result1362 = _t1577
                if !isnothing(deconstruct_result1362)
                    unwrapped1363 = deconstruct_result1362
                    pretty_what_if(pp, unwrapped1363)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1578 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1578 = nothing
                    end
                    deconstruct_result1360 = _t1578
                    if !isnothing(deconstruct_result1360)
                        unwrapped1361 = deconstruct_result1360
                        pretty_abort(pp, unwrapped1361)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1579 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1579 = nothing
                        end
                        deconstruct_result1358 = _t1579
                        if !isnothing(deconstruct_result1358)
                            unwrapped1359 = deconstruct_result1358
                            pretty_export(pp, unwrapped1359)
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
    flat1371 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1371)
        write(pp, flat1371)
        return nothing
    else
        _dollar_dollar = msg
        fields1369 = _dollar_dollar.relation_id
        unwrapped_fields1370 = fields1369
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1370)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1376 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        _dollar_dollar = msg
        fields1372 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1373 = fields1372
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1374 = unwrapped_fields1373[1]
        pretty_name(pp, field1374)
        newline(pp)
        field1375 = unwrapped_fields1373[2]
        pretty_relation_id(pp, field1375)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1381 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1381)
        write(pp, flat1381)
        return nothing
    else
        _dollar_dollar = msg
        fields1377 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1378 = fields1377
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1379 = unwrapped_fields1378[1]
        pretty_name(pp, field1379)
        newline(pp)
        field1380 = unwrapped_fields1378[2]
        pretty_epoch(pp, field1380)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1387 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1387)
        write(pp, flat1387)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1580 = _dollar_dollar.name
        else
            _t1580 = nothing
        end
        fields1382 = (_t1580, _dollar_dollar.relation_id,)
        unwrapped_fields1383 = fields1382
        write(pp, "(abort")
        indent_sexp!(pp)
        field1384 = unwrapped_fields1383[1]
        if !isnothing(field1384)
            newline(pp)
            opt_val1385 = field1384
            pretty_name(pp, opt_val1385)
        end
        newline(pp)
        field1386 = unwrapped_fields1383[2]
        pretty_relation_id(pp, field1386)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1390 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1390)
        write(pp, flat1390)
        return nothing
    else
        _dollar_dollar = msg
        fields1388 = _get_oneof_field(_dollar_dollar, :csv_config)
        unwrapped_fields1389 = fields1388
        write(pp, "(export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1389)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1401 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1401)
        write(pp, flat1401)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1581 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1581 = nothing
        end
        deconstruct_result1396 = _t1581
        if !isnothing(deconstruct_result1396)
            unwrapped1397 = deconstruct_result1396
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1398 = unwrapped1397[1]
            pretty_export_csv_path(pp, field1398)
            newline(pp)
            field1399 = unwrapped1397[2]
            pretty_export_csv_source(pp, field1399)
            newline(pp)
            field1400 = unwrapped1397[3]
            pretty_csv_config(pp, field1400)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1583 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1582 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1583,)
            else
                _t1582 = nothing
            end
            deconstruct_result1391 = _t1582
            if !isnothing(deconstruct_result1391)
                unwrapped1392 = deconstruct_result1391
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1393 = unwrapped1392[1]
                pretty_export_csv_path(pp, field1393)
                newline(pp)
                field1394 = unwrapped1392[2]
                pretty_export_csv_columns_list(pp, field1394)
                newline(pp)
                field1395 = unwrapped1392[3]
                pretty_config_dict(pp, field1395)
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
    flat1403 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1403)
        write(pp, flat1403)
        return nothing
    else
        fields1402 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1402))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1410 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1410)
        write(pp, flat1410)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1584 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1584 = nothing
        end
        deconstruct_result1406 = _t1584
        if !isnothing(deconstruct_result1406)
            unwrapped1407 = deconstruct_result1406
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1407)
                newline(pp)
                for (i1585, elem1408) in enumerate(unwrapped1407)
                    i1409 = i1585 - 1
                    if (i1409 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1408)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1586 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1586 = nothing
            end
            deconstruct_result1404 = _t1586
            if !isnothing(deconstruct_result1404)
                unwrapped1405 = deconstruct_result1404
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1405)
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
    flat1415 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1415)
        write(pp, flat1415)
        return nothing
    else
        _dollar_dollar = msg
        fields1411 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1412 = fields1411
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1413 = unwrapped_fields1412[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1413))
        newline(pp)
        field1414 = unwrapped_fields1412[2]
        pretty_relation_id(pp, field1414)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1419 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1419)
        write(pp, flat1419)
        return nothing
    else
        fields1416 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1416)
            newline(pp)
            for (i1587, elem1417) in enumerate(fields1416)
                i1418 = i1587 - 1
                if (i1418 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1417)
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
    for (i1626, _rid) in enumerate(msg.ids)
        _idx = i1626 - 1
        newline(pp)
        write(pp, "(")
        _t1627 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1627)
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
    for (i1628, _elem) in enumerate(msg.keys)
        _idx = i1628 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1629, _elem) in enumerate(msg.values)
        _idx = i1629 - 1
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
    for (i1630, _elem) in enumerate(msg.columns)
        _idx = i1630 - 1
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
