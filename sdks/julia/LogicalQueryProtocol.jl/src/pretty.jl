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
format_float32(formatter::DefaultConstantFormatter, pp::PrettyPrinter, v::Float32)::String = lowercase(string(v)) * "f32"

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
format_float32(pp::PrettyPrinter, v::Float32)::String = format_float32(pp.constant_formatter, pp, v)

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
    _t1571 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1571
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1572 = Proto.Value(value=OneOf(:int_value, v))
    return _t1572
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1573 = Proto.Value(value=OneOf(:float_value, v))
    return _t1573
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1574 = Proto.Value(value=OneOf(:string_value, v))
    return _t1574
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1575 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1575
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1576 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1576
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1577 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1577,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1578 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1578,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1579 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1579,))
            end
        end
    end
    _t1580 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1580,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1581 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1581,))
    _t1582 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1582,))
    if msg.new_line != ""
        _t1583 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1583,))
    end
    _t1584 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1584,))
    _t1585 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1585,))
    _t1586 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1586,))
    if msg.comment != ""
        _t1587 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1587,))
    end
    for missing_string in msg.missing_strings
        _t1588 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1588,))
    end
    _t1589 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1589,))
    _t1590 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1590,))
    _t1591 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1591,))
    if msg.partition_size_mb != 0
        _t1592 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1592,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1593 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1593,))
    _t1594 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1594,))
    _t1595 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1595,))
    _t1596 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1596,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1597 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1597,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1598 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1598,))
        end
    end
    _t1599 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1599,))
    _t1600 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1600,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1601 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1601,))
    end
    if !isnothing(msg.compression)
        _t1602 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1602,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1603 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1603,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1604 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1604,))
    end
    if !isnothing(msg.syntax_delim)
        _t1605 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1605,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1606 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1606,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1607 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1607,))
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
        _t1608 = nothing
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
    flat712 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat712)
        write(pp, flat712)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1406 = _dollar_dollar.configure
        else
            _t1406 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1407 = _dollar_dollar.sync
        else
            _t1407 = nothing
        end
        fields703 = (_t1406, _t1407, _dollar_dollar.epochs,)
        unwrapped_fields704 = fields703
        write(pp, "(transaction")
        indent_sexp!(pp)
        field705 = unwrapped_fields704[1]
        if !isnothing(field705)
            newline(pp)
            opt_val706 = field705
            pretty_configure(pp, opt_val706)
        end
        field707 = unwrapped_fields704[2]
        if !isnothing(field707)
            newline(pp)
            opt_val708 = field707
            pretty_sync(pp, opt_val708)
        end
        field709 = unwrapped_fields704[3]
        if !isempty(field709)
            newline(pp)
            for (i1408, elem710) in enumerate(field709)
                i711 = i1408 - 1
                if (i711 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem710)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat715 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat715)
        write(pp, flat715)
        return nothing
    else
        _dollar_dollar = msg
        _t1409 = deconstruct_configure(pp, _dollar_dollar)
        fields713 = _t1409
        unwrapped_fields714 = fields713
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields714)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat719 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat719)
        write(pp, flat719)
        return nothing
    else
        fields716 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields716)
            newline(pp)
            for (i1410, elem717) in enumerate(fields716)
                i718 = i1410 - 1
                if (i718 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem717)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat724 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat724)
        write(pp, flat724)
        return nothing
    else
        _dollar_dollar = msg
        fields720 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields721 = fields720
        write(pp, ":")
        field722 = unwrapped_fields721[1]
        write(pp, field722)
        write(pp, " ")
        field723 = unwrapped_fields721[2]
        pretty_raw_value(pp, field723)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat748 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat748)
        write(pp, flat748)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1411 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1411 = nothing
        end
        deconstruct_result746 = _t1411
        if !isnothing(deconstruct_result746)
            unwrapped747 = deconstruct_result746
            pretty_raw_date(pp, unwrapped747)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1412 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1412 = nothing
            end
            deconstruct_result744 = _t1412
            if !isnothing(deconstruct_result744)
                unwrapped745 = deconstruct_result744
                pretty_raw_datetime(pp, unwrapped745)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1413 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1413 = nothing
                end
                deconstruct_result742 = _t1413
                if !isnothing(deconstruct_result742)
                    unwrapped743 = deconstruct_result742
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped743))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1414 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1414 = nothing
                    end
                    deconstruct_result740 = _t1414
                    if !isnothing(deconstruct_result740)
                        unwrapped741 = deconstruct_result740
                        write(pp, (string(Int64(unwrapped741)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1415 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1415 = nothing
                        end
                        deconstruct_result738 = _t1415
                        if !isnothing(deconstruct_result738)
                            unwrapped739 = deconstruct_result738
                            write(pp, string(unwrapped739))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1416 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1416 = nothing
                            end
                            deconstruct_result736 = _t1416
                            if !isnothing(deconstruct_result736)
                                unwrapped737 = deconstruct_result736
                                write(pp, (lowercase(string(unwrapped737)) * "f32"))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1417 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1417 = nothing
                                end
                                deconstruct_result734 = _t1417
                                if !isnothing(deconstruct_result734)
                                    unwrapped735 = deconstruct_result734
                                    write(pp, lowercase(string(unwrapped735)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                        _t1418 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                    else
                                        _t1418 = nothing
                                    end
                                    deconstruct_result732 = _t1418
                                    if !isnothing(deconstruct_result732)
                                        unwrapped733 = deconstruct_result732
                                        write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped733))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                            _t1419 = _get_oneof_field(_dollar_dollar, :int128_value)
                                        else
                                            _t1419 = nothing
                                        end
                                        deconstruct_result730 = _t1419
                                        if !isnothing(deconstruct_result730)
                                            unwrapped731 = deconstruct_result730
                                            write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped731))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                _t1420 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                            else
                                                _t1420 = nothing
                                            end
                                            deconstruct_result728 = _t1420
                                            if !isnothing(deconstruct_result728)
                                                unwrapped729 = deconstruct_result728
                                                write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped729))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                    _t1421 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                else
                                                    _t1421 = nothing
                                                end
                                                deconstruct_result726 = _t1421
                                                if !isnothing(deconstruct_result726)
                                                    unwrapped727 = deconstruct_result726
                                                    pretty_boolean_value(pp, unwrapped727)
                                                else
                                                    fields725 = msg
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
    return nothing
end

function pretty_raw_date(pp::PrettyPrinter, msg::Proto.DateValue)
    flat754 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat754)
        write(pp, flat754)
        return nothing
    else
        _dollar_dollar = msg
        fields749 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields750 = fields749
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field751 = unwrapped_fields750[1]
        write(pp, string(field751))
        newline(pp)
        field752 = unwrapped_fields750[2]
        write(pp, string(field752))
        newline(pp)
        field753 = unwrapped_fields750[3]
        write(pp, string(field753))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat765 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat765)
        write(pp, flat765)
        return nothing
    else
        _dollar_dollar = msg
        fields755 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields756 = fields755
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field757 = unwrapped_fields756[1]
        write(pp, string(field757))
        newline(pp)
        field758 = unwrapped_fields756[2]
        write(pp, string(field758))
        newline(pp)
        field759 = unwrapped_fields756[3]
        write(pp, string(field759))
        newline(pp)
        field760 = unwrapped_fields756[4]
        write(pp, string(field760))
        newline(pp)
        field761 = unwrapped_fields756[5]
        write(pp, string(field761))
        newline(pp)
        field762 = unwrapped_fields756[6]
        write(pp, string(field762))
        field763 = unwrapped_fields756[7]
        if !isnothing(field763)
            newline(pp)
            opt_val764 = field763
            write(pp, string(opt_val764))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1422 = ()
    else
        _t1422 = nothing
    end
    deconstruct_result768 = _t1422
    if !isnothing(deconstruct_result768)
        unwrapped769 = deconstruct_result768
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1423 = ()
        else
            _t1423 = nothing
        end
        deconstruct_result766 = _t1423
        if !isnothing(deconstruct_result766)
            unwrapped767 = deconstruct_result766
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat774 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat774)
        write(pp, flat774)
        return nothing
    else
        _dollar_dollar = msg
        fields770 = _dollar_dollar.fragments
        unwrapped_fields771 = fields770
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields771)
            newline(pp)
            for (i1424, elem772) in enumerate(unwrapped_fields771)
                i773 = i1424 - 1
                if (i773 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem772)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat777 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat777)
        write(pp, flat777)
        return nothing
    else
        _dollar_dollar = msg
        fields775 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields776 = fields775
        write(pp, ":")
        write(pp, unwrapped_fields776)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat784 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat784)
        write(pp, flat784)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1425 = _dollar_dollar.writes
        else
            _t1425 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1426 = _dollar_dollar.reads
        else
            _t1426 = nothing
        end
        fields778 = (_t1425, _t1426,)
        unwrapped_fields779 = fields778
        write(pp, "(epoch")
        indent_sexp!(pp)
        field780 = unwrapped_fields779[1]
        if !isnothing(field780)
            newline(pp)
            opt_val781 = field780
            pretty_epoch_writes(pp, opt_val781)
        end
        field782 = unwrapped_fields779[2]
        if !isnothing(field782)
            newline(pp)
            opt_val783 = field782
            pretty_epoch_reads(pp, opt_val783)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat788 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat788)
        write(pp, flat788)
        return nothing
    else
        fields785 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields785)
            newline(pp)
            for (i1427, elem786) in enumerate(fields785)
                i787 = i1427 - 1
                if (i787 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem786)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat797 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat797)
        write(pp, flat797)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1428 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1428 = nothing
        end
        deconstruct_result795 = _t1428
        if !isnothing(deconstruct_result795)
            unwrapped796 = deconstruct_result795
            pretty_define(pp, unwrapped796)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1429 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1429 = nothing
            end
            deconstruct_result793 = _t1429
            if !isnothing(deconstruct_result793)
                unwrapped794 = deconstruct_result793
                pretty_undefine(pp, unwrapped794)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1430 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1430 = nothing
                end
                deconstruct_result791 = _t1430
                if !isnothing(deconstruct_result791)
                    unwrapped792 = deconstruct_result791
                    pretty_context(pp, unwrapped792)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1431 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1431 = nothing
                    end
                    deconstruct_result789 = _t1431
                    if !isnothing(deconstruct_result789)
                        unwrapped790 = deconstruct_result789
                        pretty_snapshot(pp, unwrapped790)
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
    flat800 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat800)
        write(pp, flat800)
        return nothing
    else
        _dollar_dollar = msg
        fields798 = _dollar_dollar.fragment
        unwrapped_fields799 = fields798
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields799)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat807 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat807)
        write(pp, flat807)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields801 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields802 = fields801
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field803 = unwrapped_fields802[1]
        pretty_new_fragment_id(pp, field803)
        field804 = unwrapped_fields802[2]
        if !isempty(field804)
            newline(pp)
            for (i1432, elem805) in enumerate(field804)
                i806 = i1432 - 1
                if (i806 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem805)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat809 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat809)
        write(pp, flat809)
        return nothing
    else
        fields808 = msg
        pretty_fragment_id(pp, fields808)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat818 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat818)
        write(pp, flat818)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1433 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1433 = nothing
        end
        deconstruct_result816 = _t1433
        if !isnothing(deconstruct_result816)
            unwrapped817 = deconstruct_result816
            pretty_def(pp, unwrapped817)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1434 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1434 = nothing
            end
            deconstruct_result814 = _t1434
            if !isnothing(deconstruct_result814)
                unwrapped815 = deconstruct_result814
                pretty_algorithm(pp, unwrapped815)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1435 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1435 = nothing
                end
                deconstruct_result812 = _t1435
                if !isnothing(deconstruct_result812)
                    unwrapped813 = deconstruct_result812
                    pretty_constraint(pp, unwrapped813)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1436 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1436 = nothing
                    end
                    deconstruct_result810 = _t1436
                    if !isnothing(deconstruct_result810)
                        unwrapped811 = deconstruct_result810
                        pretty_data(pp, unwrapped811)
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
    flat825 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat825)
        write(pp, flat825)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1437 = _dollar_dollar.attrs
        else
            _t1437 = nothing
        end
        fields819 = (_dollar_dollar.name, _dollar_dollar.body, _t1437,)
        unwrapped_fields820 = fields819
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field821 = unwrapped_fields820[1]
        pretty_relation_id(pp, field821)
        newline(pp)
        field822 = unwrapped_fields820[2]
        pretty_abstraction(pp, field822)
        field823 = unwrapped_fields820[3]
        if !isnothing(field823)
            newline(pp)
            opt_val824 = field823
            pretty_attrs(pp, opt_val824)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat830 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat830)
        write(pp, flat830)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1439 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1438 = _t1439
        else
            _t1438 = nothing
        end
        deconstruct_result828 = _t1438
        if !isnothing(deconstruct_result828)
            unwrapped829 = deconstruct_result828
            write(pp, ":")
            write(pp, unwrapped829)
        else
            _dollar_dollar = msg
            _t1440 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result826 = _t1440
            if !isnothing(deconstruct_result826)
                unwrapped827 = deconstruct_result826
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped827))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat835 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat835)
        write(pp, flat835)
        return nothing
    else
        _dollar_dollar = msg
        _t1441 = deconstruct_bindings(pp, _dollar_dollar)
        fields831 = (_t1441, _dollar_dollar.value,)
        unwrapped_fields832 = fields831
        write(pp, "(")
        indent!(pp)
        field833 = unwrapped_fields832[1]
        pretty_bindings(pp, field833)
        newline(pp)
        field834 = unwrapped_fields832[2]
        pretty_formula(pp, field834)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat843 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat843)
        write(pp, flat843)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1442 = _dollar_dollar[2]
        else
            _t1442 = nothing
        end
        fields836 = (_dollar_dollar[1], _t1442,)
        unwrapped_fields837 = fields836
        write(pp, "[")
        indent!(pp)
        field838 = unwrapped_fields837[1]
        for (i1443, elem839) in enumerate(field838)
            i840 = i1443 - 1
            if (i840 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem839)
        end
        field841 = unwrapped_fields837[2]
        if !isnothing(field841)
            newline(pp)
            opt_val842 = field841
            pretty_value_bindings(pp, opt_val842)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat848 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat848)
        write(pp, flat848)
        return nothing
    else
        _dollar_dollar = msg
        fields844 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields845 = fields844
        field846 = unwrapped_fields845[1]
        write(pp, field846)
        write(pp, "::")
        field847 = unwrapped_fields845[2]
        pretty_type(pp, field847)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat875 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat875)
        write(pp, flat875)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1444 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1444 = nothing
        end
        deconstruct_result873 = _t1444
        if !isnothing(deconstruct_result873)
            unwrapped874 = deconstruct_result873
            pretty_unspecified_type(pp, unwrapped874)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1445 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1445 = nothing
            end
            deconstruct_result871 = _t1445
            if !isnothing(deconstruct_result871)
                unwrapped872 = deconstruct_result871
                pretty_string_type(pp, unwrapped872)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1446 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1446 = nothing
                end
                deconstruct_result869 = _t1446
                if !isnothing(deconstruct_result869)
                    unwrapped870 = deconstruct_result869
                    pretty_int_type(pp, unwrapped870)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1447 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1447 = nothing
                    end
                    deconstruct_result867 = _t1447
                    if !isnothing(deconstruct_result867)
                        unwrapped868 = deconstruct_result867
                        pretty_float_type(pp, unwrapped868)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1448 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1448 = nothing
                        end
                        deconstruct_result865 = _t1448
                        if !isnothing(deconstruct_result865)
                            unwrapped866 = deconstruct_result865
                            pretty_uint128_type(pp, unwrapped866)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1449 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1449 = nothing
                            end
                            deconstruct_result863 = _t1449
                            if !isnothing(deconstruct_result863)
                                unwrapped864 = deconstruct_result863
                                pretty_int128_type(pp, unwrapped864)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1450 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1450 = nothing
                                end
                                deconstruct_result861 = _t1450
                                if !isnothing(deconstruct_result861)
                                    unwrapped862 = deconstruct_result861
                                    pretty_date_type(pp, unwrapped862)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1451 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1451 = nothing
                                    end
                                    deconstruct_result859 = _t1451
                                    if !isnothing(deconstruct_result859)
                                        unwrapped860 = deconstruct_result859
                                        pretty_datetime_type(pp, unwrapped860)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1452 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1452 = nothing
                                        end
                                        deconstruct_result857 = _t1452
                                        if !isnothing(deconstruct_result857)
                                            unwrapped858 = deconstruct_result857
                                            pretty_missing_type(pp, unwrapped858)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1453 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1453 = nothing
                                            end
                                            deconstruct_result855 = _t1453
                                            if !isnothing(deconstruct_result855)
                                                unwrapped856 = deconstruct_result855
                                                pretty_decimal_type(pp, unwrapped856)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1454 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1454 = nothing
                                                end
                                                deconstruct_result853 = _t1454
                                                if !isnothing(deconstruct_result853)
                                                    unwrapped854 = deconstruct_result853
                                                    pretty_boolean_type(pp, unwrapped854)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1455 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1455 = nothing
                                                    end
                                                    deconstruct_result851 = _t1455
                                                    if !isnothing(deconstruct_result851)
                                                        unwrapped852 = deconstruct_result851
                                                        pretty_int32_type(pp, unwrapped852)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1456 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1456 = nothing
                                                        end
                                                        deconstruct_result849 = _t1456
                                                        if !isnothing(deconstruct_result849)
                                                            unwrapped850 = deconstruct_result849
                                                            pretty_float32_type(pp, unwrapped850)
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
    return nothing
end

function pretty_unspecified_type(pp::PrettyPrinter, msg::Proto.UnspecifiedType)
    fields876 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields877 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields878 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields879 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields880 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields881 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields882 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields883 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields884 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat889 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat889)
        write(pp, flat889)
        return nothing
    else
        _dollar_dollar = msg
        fields885 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields886 = fields885
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field887 = unwrapped_fields886[1]
        write(pp, string(field887))
        newline(pp)
        field888 = unwrapped_fields886[2]
        write(pp, string(field888))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields890 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields891 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields892 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat896 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat896)
        write(pp, flat896)
        return nothing
    else
        fields893 = msg
        write(pp, "|")
        if !isempty(fields893)
            write(pp, " ")
            for (i1457, elem894) in enumerate(fields893)
                i895 = i1457 - 1
                if (i895 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem894)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat923 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat923)
        write(pp, flat923)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1458 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1458 = nothing
        end
        deconstruct_result921 = _t1458
        if !isnothing(deconstruct_result921)
            unwrapped922 = deconstruct_result921
            pretty_true(pp, unwrapped922)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1459 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1459 = nothing
            end
            deconstruct_result919 = _t1459
            if !isnothing(deconstruct_result919)
                unwrapped920 = deconstruct_result919
                pretty_false(pp, unwrapped920)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1460 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1460 = nothing
                end
                deconstruct_result917 = _t1460
                if !isnothing(deconstruct_result917)
                    unwrapped918 = deconstruct_result917
                    pretty_exists(pp, unwrapped918)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1461 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1461 = nothing
                    end
                    deconstruct_result915 = _t1461
                    if !isnothing(deconstruct_result915)
                        unwrapped916 = deconstruct_result915
                        pretty_reduce(pp, unwrapped916)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1462 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1462 = nothing
                        end
                        deconstruct_result913 = _t1462
                        if !isnothing(deconstruct_result913)
                            unwrapped914 = deconstruct_result913
                            pretty_conjunction(pp, unwrapped914)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1463 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1463 = nothing
                            end
                            deconstruct_result911 = _t1463
                            if !isnothing(deconstruct_result911)
                                unwrapped912 = deconstruct_result911
                                pretty_disjunction(pp, unwrapped912)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1464 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1464 = nothing
                                end
                                deconstruct_result909 = _t1464
                                if !isnothing(deconstruct_result909)
                                    unwrapped910 = deconstruct_result909
                                    pretty_not(pp, unwrapped910)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1465 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1465 = nothing
                                    end
                                    deconstruct_result907 = _t1465
                                    if !isnothing(deconstruct_result907)
                                        unwrapped908 = deconstruct_result907
                                        pretty_ffi(pp, unwrapped908)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1466 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1466 = nothing
                                        end
                                        deconstruct_result905 = _t1466
                                        if !isnothing(deconstruct_result905)
                                            unwrapped906 = deconstruct_result905
                                            pretty_atom(pp, unwrapped906)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1467 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1467 = nothing
                                            end
                                            deconstruct_result903 = _t1467
                                            if !isnothing(deconstruct_result903)
                                                unwrapped904 = deconstruct_result903
                                                pretty_pragma(pp, unwrapped904)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1468 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1468 = nothing
                                                end
                                                deconstruct_result901 = _t1468
                                                if !isnothing(deconstruct_result901)
                                                    unwrapped902 = deconstruct_result901
                                                    pretty_primitive(pp, unwrapped902)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1469 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1469 = nothing
                                                    end
                                                    deconstruct_result899 = _t1469
                                                    if !isnothing(deconstruct_result899)
                                                        unwrapped900 = deconstruct_result899
                                                        pretty_rel_atom(pp, unwrapped900)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1470 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1470 = nothing
                                                        end
                                                        deconstruct_result897 = _t1470
                                                        if !isnothing(deconstruct_result897)
                                                            unwrapped898 = deconstruct_result897
                                                            pretty_cast(pp, unwrapped898)
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
    fields924 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields925 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat930 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat930)
        write(pp, flat930)
        return nothing
    else
        _dollar_dollar = msg
        _t1471 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields926 = (_t1471, _dollar_dollar.body.value,)
        unwrapped_fields927 = fields926
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field928 = unwrapped_fields927[1]
        pretty_bindings(pp, field928)
        newline(pp)
        field929 = unwrapped_fields927[2]
        pretty_formula(pp, field929)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat936 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat936)
        write(pp, flat936)
        return nothing
    else
        _dollar_dollar = msg
        fields931 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields932 = fields931
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field933 = unwrapped_fields932[1]
        pretty_abstraction(pp, field933)
        newline(pp)
        field934 = unwrapped_fields932[2]
        pretty_abstraction(pp, field934)
        newline(pp)
        field935 = unwrapped_fields932[3]
        pretty_terms(pp, field935)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat940 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat940)
        write(pp, flat940)
        return nothing
    else
        fields937 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields937)
            newline(pp)
            for (i1472, elem938) in enumerate(fields937)
                i939 = i1472 - 1
                if (i939 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem938)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat945 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat945)
        write(pp, flat945)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1473 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1473 = nothing
        end
        deconstruct_result943 = _t1473
        if !isnothing(deconstruct_result943)
            unwrapped944 = deconstruct_result943
            pretty_var(pp, unwrapped944)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1474 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1474 = nothing
            end
            deconstruct_result941 = _t1474
            if !isnothing(deconstruct_result941)
                unwrapped942 = deconstruct_result941
                pretty_value(pp, unwrapped942)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat948 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat948)
        write(pp, flat948)
        return nothing
    else
        _dollar_dollar = msg
        fields946 = _dollar_dollar.name
        unwrapped_fields947 = fields946
        write(pp, unwrapped_fields947)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat972 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat972)
        write(pp, flat972)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1475 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1475 = nothing
        end
        deconstruct_result970 = _t1475
        if !isnothing(deconstruct_result970)
            unwrapped971 = deconstruct_result970
            pretty_date(pp, unwrapped971)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1476 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1476 = nothing
            end
            deconstruct_result968 = _t1476
            if !isnothing(deconstruct_result968)
                unwrapped969 = deconstruct_result968
                pretty_datetime(pp, unwrapped969)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1477 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1477 = nothing
                end
                deconstruct_result966 = _t1477
                if !isnothing(deconstruct_result966)
                    unwrapped967 = deconstruct_result966
                    write(pp, format_string(pp, unwrapped967))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1478 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1478 = nothing
                    end
                    deconstruct_result964 = _t1478
                    if !isnothing(deconstruct_result964)
                        unwrapped965 = deconstruct_result964
                        write(pp, format_int32(pp, unwrapped965))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1479 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1479 = nothing
                        end
                        deconstruct_result962 = _t1479
                        if !isnothing(deconstruct_result962)
                            unwrapped963 = deconstruct_result962
                            write(pp, format_int(pp, unwrapped963))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1480 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1480 = nothing
                            end
                            deconstruct_result960 = _t1480
                            if !isnothing(deconstruct_result960)
                                unwrapped961 = deconstruct_result960
                                write(pp, format_float32(pp, unwrapped961))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1481 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1481 = nothing
                                end
                                deconstruct_result958 = _t1481
                                if !isnothing(deconstruct_result958)
                                    unwrapped959 = deconstruct_result958
                                    write(pp, format_float(pp, unwrapped959))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                        _t1482 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                    else
                                        _t1482 = nothing
                                    end
                                    deconstruct_result956 = _t1482
                                    if !isnothing(deconstruct_result956)
                                        unwrapped957 = deconstruct_result956
                                        write(pp, format_uint128(pp, unwrapped957))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                            _t1483 = _get_oneof_field(_dollar_dollar, :int128_value)
                                        else
                                            _t1483 = nothing
                                        end
                                        deconstruct_result954 = _t1483
                                        if !isnothing(deconstruct_result954)
                                            unwrapped955 = deconstruct_result954
                                            write(pp, format_int128(pp, unwrapped955))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                _t1484 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                            else
                                                _t1484 = nothing
                                            end
                                            deconstruct_result952 = _t1484
                                            if !isnothing(deconstruct_result952)
                                                unwrapped953 = deconstruct_result952
                                                write(pp, format_decimal(pp, unwrapped953))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                    _t1485 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                else
                                                    _t1485 = nothing
                                                end
                                                deconstruct_result950 = _t1485
                                                if !isnothing(deconstruct_result950)
                                                    unwrapped951 = deconstruct_result950
                                                    pretty_boolean_value(pp, unwrapped951)
                                                else
                                                    fields949 = msg
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
    return nothing
end

function pretty_date(pp::PrettyPrinter, msg::Proto.DateValue)
    flat978 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat978)
        write(pp, flat978)
        return nothing
    else
        _dollar_dollar = msg
        fields973 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields974 = fields973
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field975 = unwrapped_fields974[1]
        write(pp, format_int(pp, field975))
        newline(pp)
        field976 = unwrapped_fields974[2]
        write(pp, format_int(pp, field976))
        newline(pp)
        field977 = unwrapped_fields974[3]
        write(pp, format_int(pp, field977))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat989 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat989)
        write(pp, flat989)
        return nothing
    else
        _dollar_dollar = msg
        fields979 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields980 = fields979
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field981 = unwrapped_fields980[1]
        write(pp, format_int(pp, field981))
        newline(pp)
        field982 = unwrapped_fields980[2]
        write(pp, format_int(pp, field982))
        newline(pp)
        field983 = unwrapped_fields980[3]
        write(pp, format_int(pp, field983))
        newline(pp)
        field984 = unwrapped_fields980[4]
        write(pp, format_int(pp, field984))
        newline(pp)
        field985 = unwrapped_fields980[5]
        write(pp, format_int(pp, field985))
        newline(pp)
        field986 = unwrapped_fields980[6]
        write(pp, format_int(pp, field986))
        field987 = unwrapped_fields980[7]
        if !isnothing(field987)
            newline(pp)
            opt_val988 = field987
            write(pp, format_int(pp, opt_val988))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat994 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat994)
        write(pp, flat994)
        return nothing
    else
        _dollar_dollar = msg
        fields990 = _dollar_dollar.args
        unwrapped_fields991 = fields990
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields991)
            newline(pp)
            for (i1486, elem992) in enumerate(unwrapped_fields991)
                i993 = i1486 - 1
                if (i993 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem992)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat999 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat999)
        write(pp, flat999)
        return nothing
    else
        _dollar_dollar = msg
        fields995 = _dollar_dollar.args
        unwrapped_fields996 = fields995
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields996)
            newline(pp)
            for (i1487, elem997) in enumerate(unwrapped_fields996)
                i998 = i1487 - 1
                if (i998 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem997)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1002 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1002)
        write(pp, flat1002)
        return nothing
    else
        _dollar_dollar = msg
        fields1000 = _dollar_dollar.arg
        unwrapped_fields1001 = fields1000
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1001)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1008 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1008)
        write(pp, flat1008)
        return nothing
    else
        _dollar_dollar = msg
        fields1003 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1004 = fields1003
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1005 = unwrapped_fields1004[1]
        pretty_name(pp, field1005)
        newline(pp)
        field1006 = unwrapped_fields1004[2]
        pretty_ffi_args(pp, field1006)
        newline(pp)
        field1007 = unwrapped_fields1004[3]
        pretty_terms(pp, field1007)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1010 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1010)
        write(pp, flat1010)
        return nothing
    else
        fields1009 = msg
        write(pp, ":")
        write(pp, fields1009)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1014 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1014)
        write(pp, flat1014)
        return nothing
    else
        fields1011 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1011)
            newline(pp)
            for (i1488, elem1012) in enumerate(fields1011)
                i1013 = i1488 - 1
                if (i1013 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1012)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1021 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1021)
        write(pp, flat1021)
        return nothing
    else
        _dollar_dollar = msg
        fields1015 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1016 = fields1015
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1017 = unwrapped_fields1016[1]
        pretty_relation_id(pp, field1017)
        field1018 = unwrapped_fields1016[2]
        if !isempty(field1018)
            newline(pp)
            for (i1489, elem1019) in enumerate(field1018)
                i1020 = i1489 - 1
                if (i1020 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1019)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1028 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1028)
        write(pp, flat1028)
        return nothing
    else
        _dollar_dollar = msg
        fields1022 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1023 = fields1022
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1024 = unwrapped_fields1023[1]
        pretty_name(pp, field1024)
        field1025 = unwrapped_fields1023[2]
        if !isempty(field1025)
            newline(pp)
            for (i1490, elem1026) in enumerate(field1025)
                i1027 = i1490 - 1
                if (i1027 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1026)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1044 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1044)
        write(pp, flat1044)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1491 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1491 = nothing
        end
        guard_result1043 = _t1491
        if !isnothing(guard_result1043)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1492 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1492 = nothing
            end
            guard_result1042 = _t1492
            if !isnothing(guard_result1042)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1493 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1493 = nothing
                end
                guard_result1041 = _t1493
                if !isnothing(guard_result1041)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1494 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1494 = nothing
                    end
                    guard_result1040 = _t1494
                    if !isnothing(guard_result1040)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1495 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1495 = nothing
                        end
                        guard_result1039 = _t1495
                        if !isnothing(guard_result1039)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1496 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1496 = nothing
                            end
                            guard_result1038 = _t1496
                            if !isnothing(guard_result1038)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1497 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1497 = nothing
                                end
                                guard_result1037 = _t1497
                                if !isnothing(guard_result1037)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1498 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1498 = nothing
                                    end
                                    guard_result1036 = _t1498
                                    if !isnothing(guard_result1036)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1499 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1499 = nothing
                                        end
                                        guard_result1035 = _t1499
                                        if !isnothing(guard_result1035)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1029 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1030 = fields1029
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1031 = unwrapped_fields1030[1]
                                            pretty_name(pp, field1031)
                                            field1032 = unwrapped_fields1030[2]
                                            if !isempty(field1032)
                                                newline(pp)
                                                for (i1500, elem1033) in enumerate(field1032)
                                                    i1034 = i1500 - 1
                                                    if (i1034 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1033)
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
    flat1049 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1049)
        write(pp, flat1049)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1501 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1501 = nothing
        end
        fields1045 = _t1501
        unwrapped_fields1046 = fields1045
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1047 = unwrapped_fields1046[1]
        pretty_term(pp, field1047)
        newline(pp)
        field1048 = unwrapped_fields1046[2]
        pretty_term(pp, field1048)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1054 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1054)
        write(pp, flat1054)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1502 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1502 = nothing
        end
        fields1050 = _t1502
        unwrapped_fields1051 = fields1050
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1052 = unwrapped_fields1051[1]
        pretty_term(pp, field1052)
        newline(pp)
        field1053 = unwrapped_fields1051[2]
        pretty_term(pp, field1053)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1059 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1059)
        write(pp, flat1059)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1503 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1503 = nothing
        end
        fields1055 = _t1503
        unwrapped_fields1056 = fields1055
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1057 = unwrapped_fields1056[1]
        pretty_term(pp, field1057)
        newline(pp)
        field1058 = unwrapped_fields1056[2]
        pretty_term(pp, field1058)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1064 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1064)
        write(pp, flat1064)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1504 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1504 = nothing
        end
        fields1060 = _t1504
        unwrapped_fields1061 = fields1060
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1062 = unwrapped_fields1061[1]
        pretty_term(pp, field1062)
        newline(pp)
        field1063 = unwrapped_fields1061[2]
        pretty_term(pp, field1063)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1069 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1069)
        write(pp, flat1069)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1505 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1505 = nothing
        end
        fields1065 = _t1505
        unwrapped_fields1066 = fields1065
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1067 = unwrapped_fields1066[1]
        pretty_term(pp, field1067)
        newline(pp)
        field1068 = unwrapped_fields1066[2]
        pretty_term(pp, field1068)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1075 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1075)
        write(pp, flat1075)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1506 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1506 = nothing
        end
        fields1070 = _t1506
        unwrapped_fields1071 = fields1070
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1072 = unwrapped_fields1071[1]
        pretty_term(pp, field1072)
        newline(pp)
        field1073 = unwrapped_fields1071[2]
        pretty_term(pp, field1073)
        newline(pp)
        field1074 = unwrapped_fields1071[3]
        pretty_term(pp, field1074)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1081 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1081)
        write(pp, flat1081)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1507 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1507 = nothing
        end
        fields1076 = _t1507
        unwrapped_fields1077 = fields1076
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1078 = unwrapped_fields1077[1]
        pretty_term(pp, field1078)
        newline(pp)
        field1079 = unwrapped_fields1077[2]
        pretty_term(pp, field1079)
        newline(pp)
        field1080 = unwrapped_fields1077[3]
        pretty_term(pp, field1080)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1087 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1087)
        write(pp, flat1087)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1508 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1508 = nothing
        end
        fields1082 = _t1508
        unwrapped_fields1083 = fields1082
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1084 = unwrapped_fields1083[1]
        pretty_term(pp, field1084)
        newline(pp)
        field1085 = unwrapped_fields1083[2]
        pretty_term(pp, field1085)
        newline(pp)
        field1086 = unwrapped_fields1083[3]
        pretty_term(pp, field1086)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1093 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1093)
        write(pp, flat1093)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1509 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1509 = nothing
        end
        fields1088 = _t1509
        unwrapped_fields1089 = fields1088
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1090 = unwrapped_fields1089[1]
        pretty_term(pp, field1090)
        newline(pp)
        field1091 = unwrapped_fields1089[2]
        pretty_term(pp, field1091)
        newline(pp)
        field1092 = unwrapped_fields1089[3]
        pretty_term(pp, field1092)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1098 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1098)
        write(pp, flat1098)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1510 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1510 = nothing
        end
        deconstruct_result1096 = _t1510
        if !isnothing(deconstruct_result1096)
            unwrapped1097 = deconstruct_result1096
            pretty_specialized_value(pp, unwrapped1097)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1511 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1511 = nothing
            end
            deconstruct_result1094 = _t1511
            if !isnothing(deconstruct_result1094)
                unwrapped1095 = deconstruct_result1094
                pretty_term(pp, unwrapped1095)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1100 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1100)
        write(pp, flat1100)
        return nothing
    else
        fields1099 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1099)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1107 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1107)
        write(pp, flat1107)
        return nothing
    else
        _dollar_dollar = msg
        fields1101 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1102 = fields1101
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1103 = unwrapped_fields1102[1]
        pretty_name(pp, field1103)
        field1104 = unwrapped_fields1102[2]
        if !isempty(field1104)
            newline(pp)
            for (i1512, elem1105) in enumerate(field1104)
                i1106 = i1512 - 1
                if (i1106 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1105)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1112 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1112)
        write(pp, flat1112)
        return nothing
    else
        _dollar_dollar = msg
        fields1108 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1109 = fields1108
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1110 = unwrapped_fields1109[1]
        pretty_term(pp, field1110)
        newline(pp)
        field1111 = unwrapped_fields1109[2]
        pretty_term(pp, field1111)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1116 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1116)
        write(pp, flat1116)
        return nothing
    else
        fields1113 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1113)
            newline(pp)
            for (i1513, elem1114) in enumerate(fields1113)
                i1115 = i1513 - 1
                if (i1115 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1114)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1123 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1123)
        write(pp, flat1123)
        return nothing
    else
        _dollar_dollar = msg
        fields1117 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1118 = fields1117
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1119 = unwrapped_fields1118[1]
        pretty_name(pp, field1119)
        field1120 = unwrapped_fields1118[2]
        if !isempty(field1120)
            newline(pp)
            for (i1514, elem1121) in enumerate(field1120)
                i1122 = i1514 - 1
                if (i1122 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1121)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1130 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1130)
        write(pp, flat1130)
        return nothing
    else
        _dollar_dollar = msg
        fields1124 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1125 = fields1124
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1126 = unwrapped_fields1125[1]
        if !isempty(field1126)
            newline(pp)
            for (i1515, elem1127) in enumerate(field1126)
                i1128 = i1515 - 1
                if (i1128 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1127)
            end
        end
        newline(pp)
        field1129 = unwrapped_fields1125[2]
        pretty_script(pp, field1129)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1135 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1135)
        write(pp, flat1135)
        return nothing
    else
        _dollar_dollar = msg
        fields1131 = _dollar_dollar.constructs
        unwrapped_fields1132 = fields1131
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1132)
            newline(pp)
            for (i1516, elem1133) in enumerate(unwrapped_fields1132)
                i1134 = i1516 - 1
                if (i1134 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1133)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1140 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1140)
        write(pp, flat1140)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1517 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1517 = nothing
        end
        deconstruct_result1138 = _t1517
        if !isnothing(deconstruct_result1138)
            unwrapped1139 = deconstruct_result1138
            pretty_loop(pp, unwrapped1139)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1518 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1518 = nothing
            end
            deconstruct_result1136 = _t1518
            if !isnothing(deconstruct_result1136)
                unwrapped1137 = deconstruct_result1136
                pretty_instruction(pp, unwrapped1137)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1145 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1145)
        write(pp, flat1145)
        return nothing
    else
        _dollar_dollar = msg
        fields1141 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1142 = fields1141
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1143 = unwrapped_fields1142[1]
        pretty_init(pp, field1143)
        newline(pp)
        field1144 = unwrapped_fields1142[2]
        pretty_script(pp, field1144)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1149 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1149)
        write(pp, flat1149)
        return nothing
    else
        fields1146 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1146)
            newline(pp)
            for (i1519, elem1147) in enumerate(fields1146)
                i1148 = i1519 - 1
                if (i1148 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1147)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1160 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1160)
        write(pp, flat1160)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1520 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1520 = nothing
        end
        deconstruct_result1158 = _t1520
        if !isnothing(deconstruct_result1158)
            unwrapped1159 = deconstruct_result1158
            pretty_assign(pp, unwrapped1159)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1521 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1521 = nothing
            end
            deconstruct_result1156 = _t1521
            if !isnothing(deconstruct_result1156)
                unwrapped1157 = deconstruct_result1156
                pretty_upsert(pp, unwrapped1157)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1522 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1522 = nothing
                end
                deconstruct_result1154 = _t1522
                if !isnothing(deconstruct_result1154)
                    unwrapped1155 = deconstruct_result1154
                    pretty_break(pp, unwrapped1155)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1523 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1523 = nothing
                    end
                    deconstruct_result1152 = _t1523
                    if !isnothing(deconstruct_result1152)
                        unwrapped1153 = deconstruct_result1152
                        pretty_monoid_def(pp, unwrapped1153)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1524 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1524 = nothing
                        end
                        deconstruct_result1150 = _t1524
                        if !isnothing(deconstruct_result1150)
                            unwrapped1151 = deconstruct_result1150
                            pretty_monus_def(pp, unwrapped1151)
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
    flat1167 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1525 = _dollar_dollar.attrs
        else
            _t1525 = nothing
        end
        fields1161 = (_dollar_dollar.name, _dollar_dollar.body, _t1525,)
        unwrapped_fields1162 = fields1161
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1163 = unwrapped_fields1162[1]
        pretty_relation_id(pp, field1163)
        newline(pp)
        field1164 = unwrapped_fields1162[2]
        pretty_abstraction(pp, field1164)
        field1165 = unwrapped_fields1162[3]
        if !isnothing(field1165)
            newline(pp)
            opt_val1166 = field1165
            pretty_attrs(pp, opt_val1166)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1174 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1174)
        write(pp, flat1174)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1526 = _dollar_dollar.attrs
        else
            _t1526 = nothing
        end
        fields1168 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1526,)
        unwrapped_fields1169 = fields1168
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1170 = unwrapped_fields1169[1]
        pretty_relation_id(pp, field1170)
        newline(pp)
        field1171 = unwrapped_fields1169[2]
        pretty_abstraction_with_arity(pp, field1171)
        field1172 = unwrapped_fields1169[3]
        if !isnothing(field1172)
            newline(pp)
            opt_val1173 = field1172
            pretty_attrs(pp, opt_val1173)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1179 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        _dollar_dollar = msg
        _t1527 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1175 = (_t1527, _dollar_dollar[1].value,)
        unwrapped_fields1176 = fields1175
        write(pp, "(")
        indent!(pp)
        field1177 = unwrapped_fields1176[1]
        pretty_bindings(pp, field1177)
        newline(pp)
        field1178 = unwrapped_fields1176[2]
        pretty_formula(pp, field1178)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1186 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1186)
        write(pp, flat1186)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1528 = _dollar_dollar.attrs
        else
            _t1528 = nothing
        end
        fields1180 = (_dollar_dollar.name, _dollar_dollar.body, _t1528,)
        unwrapped_fields1181 = fields1180
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1182 = unwrapped_fields1181[1]
        pretty_relation_id(pp, field1182)
        newline(pp)
        field1183 = unwrapped_fields1181[2]
        pretty_abstraction(pp, field1183)
        field1184 = unwrapped_fields1181[3]
        if !isnothing(field1184)
            newline(pp)
            opt_val1185 = field1184
            pretty_attrs(pp, opt_val1185)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1194 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1194)
        write(pp, flat1194)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1529 = _dollar_dollar.attrs
        else
            _t1529 = nothing
        end
        fields1187 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1529,)
        unwrapped_fields1188 = fields1187
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1189 = unwrapped_fields1188[1]
        pretty_monoid(pp, field1189)
        newline(pp)
        field1190 = unwrapped_fields1188[2]
        pretty_relation_id(pp, field1190)
        newline(pp)
        field1191 = unwrapped_fields1188[3]
        pretty_abstraction_with_arity(pp, field1191)
        field1192 = unwrapped_fields1188[4]
        if !isnothing(field1192)
            newline(pp)
            opt_val1193 = field1192
            pretty_attrs(pp, opt_val1193)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1203 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1203)
        write(pp, flat1203)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1530 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1530 = nothing
        end
        deconstruct_result1201 = _t1530
        if !isnothing(deconstruct_result1201)
            unwrapped1202 = deconstruct_result1201
            pretty_or_monoid(pp, unwrapped1202)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1531 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1531 = nothing
            end
            deconstruct_result1199 = _t1531
            if !isnothing(deconstruct_result1199)
                unwrapped1200 = deconstruct_result1199
                pretty_min_monoid(pp, unwrapped1200)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1532 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1532 = nothing
                end
                deconstruct_result1197 = _t1532
                if !isnothing(deconstruct_result1197)
                    unwrapped1198 = deconstruct_result1197
                    pretty_max_monoid(pp, unwrapped1198)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1533 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1533 = nothing
                    end
                    deconstruct_result1195 = _t1533
                    if !isnothing(deconstruct_result1195)
                        unwrapped1196 = deconstruct_result1195
                        pretty_sum_monoid(pp, unwrapped1196)
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
    fields1204 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1207 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1207)
        write(pp, flat1207)
        return nothing
    else
        _dollar_dollar = msg
        fields1205 = _dollar_dollar.var"#type"
        unwrapped_fields1206 = fields1205
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1206)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1210 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1210)
        write(pp, flat1210)
        return nothing
    else
        _dollar_dollar = msg
        fields1208 = _dollar_dollar.var"#type"
        unwrapped_fields1209 = fields1208
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1209)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1213 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1213)
        write(pp, flat1213)
        return nothing
    else
        _dollar_dollar = msg
        fields1211 = _dollar_dollar.var"#type"
        unwrapped_fields1212 = fields1211
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1212)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1221 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1221)
        write(pp, flat1221)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1534 = _dollar_dollar.attrs
        else
            _t1534 = nothing
        end
        fields1214 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1534,)
        unwrapped_fields1215 = fields1214
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1216 = unwrapped_fields1215[1]
        pretty_monoid(pp, field1216)
        newline(pp)
        field1217 = unwrapped_fields1215[2]
        pretty_relation_id(pp, field1217)
        newline(pp)
        field1218 = unwrapped_fields1215[3]
        pretty_abstraction_with_arity(pp, field1218)
        field1219 = unwrapped_fields1215[4]
        if !isnothing(field1219)
            newline(pp)
            opt_val1220 = field1219
            pretty_attrs(pp, opt_val1220)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1228 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1228)
        write(pp, flat1228)
        return nothing
    else
        _dollar_dollar = msg
        fields1222 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1223 = fields1222
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1224 = unwrapped_fields1223[1]
        pretty_relation_id(pp, field1224)
        newline(pp)
        field1225 = unwrapped_fields1223[2]
        pretty_abstraction(pp, field1225)
        newline(pp)
        field1226 = unwrapped_fields1223[3]
        pretty_functional_dependency_keys(pp, field1226)
        newline(pp)
        field1227 = unwrapped_fields1223[4]
        pretty_functional_dependency_values(pp, field1227)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1232 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1232)
        write(pp, flat1232)
        return nothing
    else
        fields1229 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1229)
            newline(pp)
            for (i1535, elem1230) in enumerate(fields1229)
                i1231 = i1535 - 1
                if (i1231 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1230)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1236 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1236)
        write(pp, flat1236)
        return nothing
    else
        fields1233 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1233)
            newline(pp)
            for (i1536, elem1234) in enumerate(fields1233)
                i1235 = i1536 - 1
                if (i1235 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1234)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1243 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1243)
        write(pp, flat1243)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1537 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1537 = nothing
        end
        deconstruct_result1241 = _t1537
        if !isnothing(deconstruct_result1241)
            unwrapped1242 = deconstruct_result1241
            pretty_edb(pp, unwrapped1242)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1538 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1538 = nothing
            end
            deconstruct_result1239 = _t1538
            if !isnothing(deconstruct_result1239)
                unwrapped1240 = deconstruct_result1239
                pretty_betree_relation(pp, unwrapped1240)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1539 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1539 = nothing
                end
                deconstruct_result1237 = _t1539
                if !isnothing(deconstruct_result1237)
                    unwrapped1238 = deconstruct_result1237
                    pretty_csv_data(pp, unwrapped1238)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_edb(pp::PrettyPrinter, msg::Proto.EDB)
    flat1249 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1249)
        write(pp, flat1249)
        return nothing
    else
        _dollar_dollar = msg
        fields1244 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1245 = fields1244
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1246 = unwrapped_fields1245[1]
        pretty_relation_id(pp, field1246)
        newline(pp)
        field1247 = unwrapped_fields1245[2]
        pretty_edb_path(pp, field1247)
        newline(pp)
        field1248 = unwrapped_fields1245[3]
        pretty_edb_types(pp, field1248)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1253 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        fields1250 = msg
        write(pp, "[")
        indent!(pp)
        for (i1540, elem1251) in enumerate(fields1250)
            i1252 = i1540 - 1
            if (i1252 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1251))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1257 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1257)
        write(pp, flat1257)
        return nothing
    else
        fields1254 = msg
        write(pp, "[")
        indent!(pp)
        for (i1541, elem1255) in enumerate(fields1254)
            i1256 = i1541 - 1
            if (i1256 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1255)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1262 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1262)
        write(pp, flat1262)
        return nothing
    else
        _dollar_dollar = msg
        fields1258 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1259 = fields1258
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1260 = unwrapped_fields1259[1]
        pretty_relation_id(pp, field1260)
        newline(pp)
        field1261 = unwrapped_fields1259[2]
        pretty_betree_info(pp, field1261)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1268 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1268)
        write(pp, flat1268)
        return nothing
    else
        _dollar_dollar = msg
        _t1542 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1263 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1542,)
        unwrapped_fields1264 = fields1263
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1265 = unwrapped_fields1264[1]
        pretty_betree_info_key_types(pp, field1265)
        newline(pp)
        field1266 = unwrapped_fields1264[2]
        pretty_betree_info_value_types(pp, field1266)
        newline(pp)
        field1267 = unwrapped_fields1264[3]
        pretty_config_dict(pp, field1267)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1272 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1272)
        write(pp, flat1272)
        return nothing
    else
        fields1269 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1269)
            newline(pp)
            for (i1543, elem1270) in enumerate(fields1269)
                i1271 = i1543 - 1
                if (i1271 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1270)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1276 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1276)
        write(pp, flat1276)
        return nothing
    else
        fields1273 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1273)
            newline(pp)
            for (i1544, elem1274) in enumerate(fields1273)
                i1275 = i1544 - 1
                if (i1275 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1274)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1283 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1283)
        write(pp, flat1283)
        return nothing
    else
        _dollar_dollar = msg
        fields1277 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1278 = fields1277
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1279 = unwrapped_fields1278[1]
        pretty_csvlocator(pp, field1279)
        newline(pp)
        field1280 = unwrapped_fields1278[2]
        pretty_csv_config(pp, field1280)
        newline(pp)
        field1281 = unwrapped_fields1278[3]
        pretty_gnf_columns(pp, field1281)
        newline(pp)
        field1282 = unwrapped_fields1278[4]
        pretty_csv_asof(pp, field1282)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1290 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1290)
        write(pp, flat1290)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1545 = _dollar_dollar.paths
        else
            _t1545 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1546 = String(copy(_dollar_dollar.inline_data))
        else
            _t1546 = nothing
        end
        fields1284 = (_t1545, _t1546,)
        unwrapped_fields1285 = fields1284
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1286 = unwrapped_fields1285[1]
        if !isnothing(field1286)
            newline(pp)
            opt_val1287 = field1286
            pretty_csv_locator_paths(pp, opt_val1287)
        end
        field1288 = unwrapped_fields1285[2]
        if !isnothing(field1288)
            newline(pp)
            opt_val1289 = field1288
            pretty_csv_locator_inline_data(pp, opt_val1289)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1294 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1294)
        write(pp, flat1294)
        return nothing
    else
        fields1291 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1291)
            newline(pp)
            for (i1547, elem1292) in enumerate(fields1291)
                i1293 = i1547 - 1
                if (i1293 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1292))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1296 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1296)
        write(pp, flat1296)
        return nothing
    else
        fields1295 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1295))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1299 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1299)
        write(pp, flat1299)
        return nothing
    else
        _dollar_dollar = msg
        _t1548 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1297 = _t1548
        unwrapped_fields1298 = fields1297
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1298)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1303 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1303)
        write(pp, flat1303)
        return nothing
    else
        fields1300 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1300)
            newline(pp)
            for (i1549, elem1301) in enumerate(fields1300)
                i1302 = i1549 - 1
                if (i1302 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1301)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1312 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1312)
        write(pp, flat1312)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1550 = _dollar_dollar.target_id
        else
            _t1550 = nothing
        end
        fields1304 = (_dollar_dollar.column_path, _t1550, _dollar_dollar.types,)
        unwrapped_fields1305 = fields1304
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1306 = unwrapped_fields1305[1]
        pretty_gnf_column_path(pp, field1306)
        field1307 = unwrapped_fields1305[2]
        if !isnothing(field1307)
            newline(pp)
            opt_val1308 = field1307
            pretty_relation_id(pp, opt_val1308)
        end
        newline(pp)
        write(pp, "[")
        field1309 = unwrapped_fields1305[3]
        for (i1551, elem1310) in enumerate(field1309)
            i1311 = i1551 - 1
            if (i1311 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1310)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1319 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1319)
        write(pp, flat1319)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1552 = _dollar_dollar[1]
        else
            _t1552 = nothing
        end
        deconstruct_result1317 = _t1552
        if !isnothing(deconstruct_result1317)
            unwrapped1318 = deconstruct_result1317
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1318))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1553 = _dollar_dollar
            else
                _t1553 = nothing
            end
            deconstruct_result1313 = _t1553
            if !isnothing(deconstruct_result1313)
                unwrapped1314 = deconstruct_result1313
                write(pp, "[")
                indent!(pp)
                for (i1554, elem1315) in enumerate(unwrapped1314)
                    i1316 = i1554 - 1
                    if (i1316 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1315))
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
    flat1321 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1321)
        write(pp, flat1321)
        return nothing
    else
        fields1320 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1320))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1324 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1324)
        write(pp, flat1324)
        return nothing
    else
        _dollar_dollar = msg
        fields1322 = _dollar_dollar.fragment_id
        unwrapped_fields1323 = fields1322
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1323)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1329 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1329)
        write(pp, flat1329)
        return nothing
    else
        _dollar_dollar = msg
        fields1325 = _dollar_dollar.relations
        unwrapped_fields1326 = fields1325
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1326)
            newline(pp)
            for (i1555, elem1327) in enumerate(unwrapped_fields1326)
                i1328 = i1555 - 1
                if (i1328 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1327)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1334 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1334)
        write(pp, flat1334)
        return nothing
    else
        _dollar_dollar = msg
        fields1330 = _dollar_dollar.mappings
        unwrapped_fields1331 = fields1330
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1331)
            newline(pp)
            for (i1556, elem1332) in enumerate(unwrapped_fields1331)
                i1333 = i1556 - 1
                if (i1333 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1332)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1339 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1339)
        write(pp, flat1339)
        return nothing
    else
        _dollar_dollar = msg
        fields1335 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1336 = fields1335
        field1337 = unwrapped_fields1336[1]
        pretty_edb_path(pp, field1337)
        write(pp, " ")
        field1338 = unwrapped_fields1336[2]
        pretty_relation_id(pp, field1338)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1343 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1343)
        write(pp, flat1343)
        return nothing
    else
        fields1340 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1340)
            newline(pp)
            for (i1557, elem1341) in enumerate(fields1340)
                i1342 = i1557 - 1
                if (i1342 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1341)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1354 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1354)
        write(pp, flat1354)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1558 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1558 = nothing
        end
        deconstruct_result1352 = _t1558
        if !isnothing(deconstruct_result1352)
            unwrapped1353 = deconstruct_result1352
            pretty_demand(pp, unwrapped1353)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1559 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1559 = nothing
            end
            deconstruct_result1350 = _t1559
            if !isnothing(deconstruct_result1350)
                unwrapped1351 = deconstruct_result1350
                pretty_output(pp, unwrapped1351)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1560 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1560 = nothing
                end
                deconstruct_result1348 = _t1560
                if !isnothing(deconstruct_result1348)
                    unwrapped1349 = deconstruct_result1348
                    pretty_what_if(pp, unwrapped1349)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1561 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1561 = nothing
                    end
                    deconstruct_result1346 = _t1561
                    if !isnothing(deconstruct_result1346)
                        unwrapped1347 = deconstruct_result1346
                        pretty_abort(pp, unwrapped1347)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1562 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1562 = nothing
                        end
                        deconstruct_result1344 = _t1562
                        if !isnothing(deconstruct_result1344)
                            unwrapped1345 = deconstruct_result1344
                            pretty_export(pp, unwrapped1345)
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
    flat1357 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1357)
        write(pp, flat1357)
        return nothing
    else
        _dollar_dollar = msg
        fields1355 = _dollar_dollar.relation_id
        unwrapped_fields1356 = fields1355
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1356)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1362 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1362)
        write(pp, flat1362)
        return nothing
    else
        _dollar_dollar = msg
        fields1358 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1359 = fields1358
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1360 = unwrapped_fields1359[1]
        pretty_name(pp, field1360)
        newline(pp)
        field1361 = unwrapped_fields1359[2]
        pretty_relation_id(pp, field1361)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1367 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1367)
        write(pp, flat1367)
        return nothing
    else
        _dollar_dollar = msg
        fields1363 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1364 = fields1363
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1365 = unwrapped_fields1364[1]
        pretty_name(pp, field1365)
        newline(pp)
        field1366 = unwrapped_fields1364[2]
        pretty_epoch(pp, field1366)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1373 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1373)
        write(pp, flat1373)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1563 = _dollar_dollar.name
        else
            _t1563 = nothing
        end
        fields1368 = (_t1563, _dollar_dollar.relation_id,)
        unwrapped_fields1369 = fields1368
        write(pp, "(abort")
        indent_sexp!(pp)
        field1370 = unwrapped_fields1369[1]
        if !isnothing(field1370)
            newline(pp)
            opt_val1371 = field1370
            pretty_name(pp, opt_val1371)
        end
        newline(pp)
        field1372 = unwrapped_fields1369[2]
        pretty_relation_id(pp, field1372)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1376 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        _dollar_dollar = msg
        fields1374 = _get_oneof_field(_dollar_dollar, :csv_config)
        unwrapped_fields1375 = fields1374
        write(pp, "(export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1375)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1387 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1387)
        write(pp, flat1387)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1564 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1564 = nothing
        end
        deconstruct_result1382 = _t1564
        if !isnothing(deconstruct_result1382)
            unwrapped1383 = deconstruct_result1382
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1384 = unwrapped1383[1]
            pretty_export_csv_path(pp, field1384)
            newline(pp)
            field1385 = unwrapped1383[2]
            pretty_export_csv_source(pp, field1385)
            newline(pp)
            field1386 = unwrapped1383[3]
            pretty_csv_config(pp, field1386)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1566 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1565 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1566,)
            else
                _t1565 = nothing
            end
            deconstruct_result1377 = _t1565
            if !isnothing(deconstruct_result1377)
                unwrapped1378 = deconstruct_result1377
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1379 = unwrapped1378[1]
                pretty_export_csv_path(pp, field1379)
                newline(pp)
                field1380 = unwrapped1378[2]
                pretty_export_csv_columns_list(pp, field1380)
                newline(pp)
                field1381 = unwrapped1378[3]
                pretty_config_dict(pp, field1381)
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
    flat1389 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1389)
        write(pp, flat1389)
        return nothing
    else
        fields1388 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1388))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1396 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1396)
        write(pp, flat1396)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1567 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1567 = nothing
        end
        deconstruct_result1392 = _t1567
        if !isnothing(deconstruct_result1392)
            unwrapped1393 = deconstruct_result1392
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1393)
                newline(pp)
                for (i1568, elem1394) in enumerate(unwrapped1393)
                    i1395 = i1568 - 1
                    if (i1395 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1394)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1569 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1569 = nothing
            end
            deconstruct_result1390 = _t1569
            if !isnothing(deconstruct_result1390)
                unwrapped1391 = deconstruct_result1390
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1391)
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
    flat1401 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1401)
        write(pp, flat1401)
        return nothing
    else
        _dollar_dollar = msg
        fields1397 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1398 = fields1397
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1399 = unwrapped_fields1398[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1399))
        newline(pp)
        field1400 = unwrapped_fields1398[2]
        pretty_relation_id(pp, field1400)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1405 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1405)
        write(pp, flat1405)
        return nothing
    else
        fields1402 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1402)
            newline(pp)
            for (i1570, elem1403) in enumerate(fields1402)
                i1404 = i1570 - 1
                if (i1404 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1403)
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
    for (i1609, _rid) in enumerate(msg.ids)
        _idx = i1609 - 1
        newline(pp)
        write(pp, "(")
        _t1610 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1610)
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
    for (i1611, _elem) in enumerate(msg.keys)
        _idx = i1611 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1612, _elem) in enumerate(msg.values)
        _idx = i1612 - 1
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
    for (i1613, _elem) in enumerate(msg.columns)
        _idx = i1613 - 1
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
export format_decimal, format_int128, format_uint128, format_int, format_float, format_string, format_bool, format_int32, format_float32
# Export legacy format functions for backward compatibility
export format_float64, format_string_value
# Export pretty printing API
export pprint, pretty, pretty_debug
export PrettyPrinter
# Export internal helpers for testing
export indent_level, indent!, try_flat

end # module Pretty
