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

# Fallback methods for custom formatters that don't override all types
# These delegate to the default formatter
format_decimal(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.DecimalValue)::String = format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, msg)
format_int128(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.Int128Value)::String = format_int128(DEFAULT_CONSTANT_FORMATTER, pp, msg)
format_uint128(formatter::ConstantFormatter, pp::PrettyPrinter, msg::Proto.UInt128Value)::String = format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, msg)
format_int(formatter::ConstantFormatter, pp::PrettyPrinter, v::Int64)::String = format_int(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_float(formatter::ConstantFormatter, pp::PrettyPrinter, v::Float64)::String = format_float(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_string(formatter::ConstantFormatter, pp::PrettyPrinter, s::AbstractString)::String = format_string(DEFAULT_CONSTANT_FORMATTER, pp, s)
format_bool(formatter::ConstantFormatter, pp::PrettyPrinter, v::Bool)::String = format_bool(DEFAULT_CONSTANT_FORMATTER, pp, v)

# Backward compatibility: convenience methods that use pp.constant_formatter
format_decimal(pp::PrettyPrinter, msg::Proto.DecimalValue)::String = format_decimal(pp.constant_formatter, pp, msg)
format_int128(pp::PrettyPrinter, msg::Proto.Int128Value)::String = format_int128(pp.constant_formatter, pp, msg)
format_uint128(pp::PrettyPrinter, msg::Proto.UInt128Value)::String = format_uint128(pp.constant_formatter, pp, msg)
format_int(pp::PrettyPrinter, v::Int64)::String = format_int(pp.constant_formatter, pp, v)
format_float(pp::PrettyPrinter, v::Float64)::String = format_float(pp.constant_formatter, pp, v)
format_string(pp::PrettyPrinter, s::AbstractString)::String = format_string(pp.constant_formatter, pp, s)
format_bool(pp::PrettyPrinter, v::Bool)::String = format_bool(pp.constant_formatter, pp, v)

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
    _t1458 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1458
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1459 = Proto.Value(value=OneOf(:int_value, v))
    return _t1459
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1460 = Proto.Value(value=OneOf(:float_value, v))
    return _t1460
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1461 = Proto.Value(value=OneOf(:string_value, v))
    return _t1461
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1462 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1462
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1463 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1463
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1464 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1464,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1465 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1465,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1466 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1466,))
            end
        end
    end
    _t1467 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1467,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1468 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1468,))
    _t1469 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1469,))
    if msg.new_line != ""
        _t1470 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1470,))
    end
    _t1471 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1471,))
    _t1472 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1472,))
    _t1473 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1473,))
    if msg.comment != ""
        _t1474 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1474,))
    end
    for missing_string in msg.missing_strings
        _t1475 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1475,))
    end
    _t1476 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1476,))
    _t1477 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1477,))
    _t1478 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1478,))
    if msg.partition_size_mb != 0
        _t1479 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1479,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1480 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1480,))
    _t1481 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1481,))
    _t1482 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1482,))
    _t1483 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1483,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1484 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1484,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1485 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1485,))
        end
    end
    _t1486 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1486,))
    _t1487 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1487,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1488 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1488,))
    end
    if !isnothing(msg.compression)
        _t1489 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1489,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1490 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1490,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1491 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1491,))
    end
    if !isnothing(msg.syntax_delim)
        _t1492 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1492,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1493 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1493,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1494 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1494,))
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
        _t1495 = nothing
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
    flat663 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat663)
        write(pp, flat663)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1308 = _dollar_dollar.configure
        else
            _t1308 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1309 = _dollar_dollar.sync
        else
            _t1309 = nothing
        end
        fields654 = (_t1308, _t1309, _dollar_dollar.epochs,)
        unwrapped_fields655 = fields654
        write(pp, "(transaction")
        indent_sexp!(pp)
        field656 = unwrapped_fields655[1]
        if !isnothing(field656)
            newline(pp)
            opt_val657 = field656
            pretty_configure(pp, opt_val657)
        end
        field658 = unwrapped_fields655[2]
        if !isnothing(field658)
            newline(pp)
            opt_val659 = field658
            pretty_sync(pp, opt_val659)
        end
        field660 = unwrapped_fields655[3]
        if !isempty(field660)
            newline(pp)
            for (i1310, elem661) in enumerate(field660)
                i662 = i1310 - 1
                if (i662 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem661)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat666 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat666)
        write(pp, flat666)
        return nothing
    else
        _dollar_dollar = msg
        _t1311 = deconstruct_configure(pp, _dollar_dollar)
        fields664 = _t1311
        unwrapped_fields665 = fields664
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields665)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat670 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat670)
        write(pp, flat670)
        return nothing
    else
        fields667 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields667)
            newline(pp)
            for (i1312, elem668) in enumerate(fields667)
                i669 = i1312 - 1
                if (i669 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem668)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat675 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat675)
        write(pp, flat675)
        return nothing
    else
        _dollar_dollar = msg
        fields671 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields672 = fields671
        write(pp, ":")
        field673 = unwrapped_fields672[1]
        write(pp, field673)
        write(pp, " ")
        field674 = unwrapped_fields672[2]
        pretty_value(pp, field674)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat695 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat695)
        write(pp, flat695)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1313 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1313 = nothing
        end
        deconstruct_result693 = _t1313
        if !isnothing(deconstruct_result693)
            unwrapped694 = deconstruct_result693
            pretty_date(pp, unwrapped694)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1314 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1314 = nothing
            end
            deconstruct_result691 = _t1314
            if !isnothing(deconstruct_result691)
                unwrapped692 = deconstruct_result691
                pretty_datetime(pp, unwrapped692)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1315 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1315 = nothing
                end
                deconstruct_result689 = _t1315
                if !isnothing(deconstruct_result689)
                    unwrapped690 = deconstruct_result689
                    write(pp, format_string(pp, unwrapped690))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                        _t1316 = _get_oneof_field(_dollar_dollar, :int_value)
                    else
                        _t1316 = nothing
                    end
                    deconstruct_result687 = _t1316
                    if !isnothing(deconstruct_result687)
                        unwrapped688 = deconstruct_result687
                        write(pp, format_int(pp, unwrapped688))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                            _t1317 = _get_oneof_field(_dollar_dollar, :float_value)
                        else
                            _t1317 = nothing
                        end
                        deconstruct_result685 = _t1317
                        if !isnothing(deconstruct_result685)
                            unwrapped686 = deconstruct_result685
                            write(pp, format_float(pp, unwrapped686))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                _t1318 = _get_oneof_field(_dollar_dollar, :uint128_value)
                            else
                                _t1318 = nothing
                            end
                            deconstruct_result683 = _t1318
                            if !isnothing(deconstruct_result683)
                                unwrapped684 = deconstruct_result683
                                write(pp, format_uint128(pp, unwrapped684))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                    _t1319 = _get_oneof_field(_dollar_dollar, :int128_value)
                                else
                                    _t1319 = nothing
                                end
                                deconstruct_result681 = _t1319
                                if !isnothing(deconstruct_result681)
                                    unwrapped682 = deconstruct_result681
                                    write(pp, format_int128(pp, unwrapped682))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                        _t1320 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                    else
                                        _t1320 = nothing
                                    end
                                    deconstruct_result679 = _t1320
                                    if !isnothing(deconstruct_result679)
                                        unwrapped680 = deconstruct_result679
                                        write(pp, format_decimal(pp, unwrapped680))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                            _t1321 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                        else
                                            _t1321 = nothing
                                        end
                                        deconstruct_result677 = _t1321
                                        if !isnothing(deconstruct_result677)
                                            unwrapped678 = deconstruct_result677
                                            pretty_boolean_value(pp, unwrapped678)
                                        else
                                            fields676 = msg
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
    return nothing
end

function pretty_date(pp::PrettyPrinter, msg::Proto.DateValue)
    flat701 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat701)
        write(pp, flat701)
        return nothing
    else
        _dollar_dollar = msg
        fields696 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields697 = fields696
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field698 = unwrapped_fields697[1]
        write(pp, format_int(pp, field698))
        newline(pp)
        field699 = unwrapped_fields697[2]
        write(pp, format_int(pp, field699))
        newline(pp)
        field700 = unwrapped_fields697[3]
        write(pp, format_int(pp, field700))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat712 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat712)
        write(pp, flat712)
        return nothing
    else
        _dollar_dollar = msg
        fields702 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields703 = fields702
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field704 = unwrapped_fields703[1]
        write(pp, format_int(pp, field704))
        newline(pp)
        field705 = unwrapped_fields703[2]
        write(pp, format_int(pp, field705))
        newline(pp)
        field706 = unwrapped_fields703[3]
        write(pp, format_int(pp, field706))
        newline(pp)
        field707 = unwrapped_fields703[4]
        write(pp, format_int(pp, field707))
        newline(pp)
        field708 = unwrapped_fields703[5]
        write(pp, format_int(pp, field708))
        newline(pp)
        field709 = unwrapped_fields703[6]
        write(pp, format_int(pp, field709))
        field710 = unwrapped_fields703[7]
        if !isnothing(field710)
            newline(pp)
            opt_val711 = field710
            write(pp, format_int(pp, opt_val711))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1322 = ()
    else
        _t1322 = nothing
    end
    deconstruct_result715 = _t1322
    if !isnothing(deconstruct_result715)
        unwrapped716 = deconstruct_result715
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1323 = ()
        else
            _t1323 = nothing
        end
        deconstruct_result713 = _t1323
        if !isnothing(deconstruct_result713)
            unwrapped714 = deconstruct_result713
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat721 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat721)
        write(pp, flat721)
        return nothing
    else
        _dollar_dollar = msg
        fields717 = _dollar_dollar.fragments
        unwrapped_fields718 = fields717
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields718)
            newline(pp)
            for (i1324, elem719) in enumerate(unwrapped_fields718)
                i720 = i1324 - 1
                if (i720 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem719)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat724 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat724)
        write(pp, flat724)
        return nothing
    else
        _dollar_dollar = msg
        fields722 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields723 = fields722
        write(pp, ":")
        write(pp, unwrapped_fields723)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat731 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat731)
        write(pp, flat731)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1325 = _dollar_dollar.writes
        else
            _t1325 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1326 = _dollar_dollar.reads
        else
            _t1326 = nothing
        end
        fields725 = (_t1325, _t1326,)
        unwrapped_fields726 = fields725
        write(pp, "(epoch")
        indent_sexp!(pp)
        field727 = unwrapped_fields726[1]
        if !isnothing(field727)
            newline(pp)
            opt_val728 = field727
            pretty_epoch_writes(pp, opt_val728)
        end
        field729 = unwrapped_fields726[2]
        if !isnothing(field729)
            newline(pp)
            opt_val730 = field729
            pretty_epoch_reads(pp, opt_val730)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat735 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat735)
        write(pp, flat735)
        return nothing
    else
        fields732 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields732)
            newline(pp)
            for (i1327, elem733) in enumerate(fields732)
                i734 = i1327 - 1
                if (i734 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem733)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat744 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat744)
        write(pp, flat744)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1328 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1328 = nothing
        end
        deconstruct_result742 = _t1328
        if !isnothing(deconstruct_result742)
            unwrapped743 = deconstruct_result742
            pretty_define(pp, unwrapped743)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1329 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1329 = nothing
            end
            deconstruct_result740 = _t1329
            if !isnothing(deconstruct_result740)
                unwrapped741 = deconstruct_result740
                pretty_undefine(pp, unwrapped741)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1330 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1330 = nothing
                end
                deconstruct_result738 = _t1330
                if !isnothing(deconstruct_result738)
                    unwrapped739 = deconstruct_result738
                    pretty_context(pp, unwrapped739)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1331 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1331 = nothing
                    end
                    deconstruct_result736 = _t1331
                    if !isnothing(deconstruct_result736)
                        unwrapped737 = deconstruct_result736
                        pretty_snapshot(pp, unwrapped737)
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
    flat747 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat747)
        write(pp, flat747)
        return nothing
    else
        _dollar_dollar = msg
        fields745 = _dollar_dollar.fragment
        unwrapped_fields746 = fields745
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields746)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat754 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat754)
        write(pp, flat754)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields748 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields749 = fields748
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field750 = unwrapped_fields749[1]
        pretty_new_fragment_id(pp, field750)
        field751 = unwrapped_fields749[2]
        if !isempty(field751)
            newline(pp)
            for (i1332, elem752) in enumerate(field751)
                i753 = i1332 - 1
                if (i753 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem752)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat756 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat756)
        write(pp, flat756)
        return nothing
    else
        fields755 = msg
        pretty_fragment_id(pp, fields755)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat765 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat765)
        write(pp, flat765)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1333 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1333 = nothing
        end
        deconstruct_result763 = _t1333
        if !isnothing(deconstruct_result763)
            unwrapped764 = deconstruct_result763
            pretty_def(pp, unwrapped764)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1334 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1334 = nothing
            end
            deconstruct_result761 = _t1334
            if !isnothing(deconstruct_result761)
                unwrapped762 = deconstruct_result761
                pretty_algorithm(pp, unwrapped762)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1335 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1335 = nothing
                end
                deconstruct_result759 = _t1335
                if !isnothing(deconstruct_result759)
                    unwrapped760 = deconstruct_result759
                    pretty_constraint(pp, unwrapped760)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1336 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1336 = nothing
                    end
                    deconstruct_result757 = _t1336
                    if !isnothing(deconstruct_result757)
                        unwrapped758 = deconstruct_result757
                        pretty_data(pp, unwrapped758)
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
    flat772 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat772)
        write(pp, flat772)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1337 = _dollar_dollar.attrs
        else
            _t1337 = nothing
        end
        fields766 = (_dollar_dollar.name, _dollar_dollar.body, _t1337,)
        unwrapped_fields767 = fields766
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field768 = unwrapped_fields767[1]
        pretty_relation_id(pp, field768)
        newline(pp)
        field769 = unwrapped_fields767[2]
        pretty_abstraction(pp, field769)
        field770 = unwrapped_fields767[3]
        if !isnothing(field770)
            newline(pp)
            opt_val771 = field770
            pretty_attrs(pp, opt_val771)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat777 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat777)
        write(pp, flat777)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1339 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1338 = _t1339
        else
            _t1338 = nothing
        end
        deconstruct_result775 = _t1338
        if !isnothing(deconstruct_result775)
            unwrapped776 = deconstruct_result775
            write(pp, ":")
            write(pp, unwrapped776)
        else
            _dollar_dollar = msg
            _t1340 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result773 = _t1340
            if !isnothing(deconstruct_result773)
                unwrapped774 = deconstruct_result773
                write(pp, format_uint128(pp, unwrapped774))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat782 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat782)
        write(pp, flat782)
        return nothing
    else
        _dollar_dollar = msg
        _t1341 = deconstruct_bindings(pp, _dollar_dollar)
        fields778 = (_t1341, _dollar_dollar.value,)
        unwrapped_fields779 = fields778
        write(pp, "(")
        indent!(pp)
        field780 = unwrapped_fields779[1]
        pretty_bindings(pp, field780)
        newline(pp)
        field781 = unwrapped_fields779[2]
        pretty_formula(pp, field781)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat790 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat790)
        write(pp, flat790)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1342 = _dollar_dollar[2]
        else
            _t1342 = nothing
        end
        fields783 = (_dollar_dollar[1], _t1342,)
        unwrapped_fields784 = fields783
        write(pp, "[")
        indent!(pp)
        field785 = unwrapped_fields784[1]
        for (i1343, elem786) in enumerate(field785)
            i787 = i1343 - 1
            if (i787 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem786)
        end
        field788 = unwrapped_fields784[2]
        if !isnothing(field788)
            newline(pp)
            opt_val789 = field788
            pretty_value_bindings(pp, opt_val789)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat795 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat795)
        write(pp, flat795)
        return nothing
    else
        _dollar_dollar = msg
        fields791 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields792 = fields791
        field793 = unwrapped_fields792[1]
        write(pp, field793)
        write(pp, "::")
        field794 = unwrapped_fields792[2]
        pretty_type(pp, field794)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat818 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat818)
        write(pp, flat818)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1344 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1344 = nothing
        end
        deconstruct_result816 = _t1344
        if !isnothing(deconstruct_result816)
            unwrapped817 = deconstruct_result816
            pretty_unspecified_type(pp, unwrapped817)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1345 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1345 = nothing
            end
            deconstruct_result814 = _t1345
            if !isnothing(deconstruct_result814)
                unwrapped815 = deconstruct_result814
                pretty_string_type(pp, unwrapped815)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1346 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1346 = nothing
                end
                deconstruct_result812 = _t1346
                if !isnothing(deconstruct_result812)
                    unwrapped813 = deconstruct_result812
                    pretty_int_type(pp, unwrapped813)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1347 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1347 = nothing
                    end
                    deconstruct_result810 = _t1347
                    if !isnothing(deconstruct_result810)
                        unwrapped811 = deconstruct_result810
                        pretty_float_type(pp, unwrapped811)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1348 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1348 = nothing
                        end
                        deconstruct_result808 = _t1348
                        if !isnothing(deconstruct_result808)
                            unwrapped809 = deconstruct_result808
                            pretty_uint128_type(pp, unwrapped809)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1349 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1349 = nothing
                            end
                            deconstruct_result806 = _t1349
                            if !isnothing(deconstruct_result806)
                                unwrapped807 = deconstruct_result806
                                pretty_int128_type(pp, unwrapped807)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1350 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1350 = nothing
                                end
                                deconstruct_result804 = _t1350
                                if !isnothing(deconstruct_result804)
                                    unwrapped805 = deconstruct_result804
                                    pretty_date_type(pp, unwrapped805)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1351 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1351 = nothing
                                    end
                                    deconstruct_result802 = _t1351
                                    if !isnothing(deconstruct_result802)
                                        unwrapped803 = deconstruct_result802
                                        pretty_datetime_type(pp, unwrapped803)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1352 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1352 = nothing
                                        end
                                        deconstruct_result800 = _t1352
                                        if !isnothing(deconstruct_result800)
                                            unwrapped801 = deconstruct_result800
                                            pretty_missing_type(pp, unwrapped801)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1353 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1353 = nothing
                                            end
                                            deconstruct_result798 = _t1353
                                            if !isnothing(deconstruct_result798)
                                                unwrapped799 = deconstruct_result798
                                                pretty_decimal_type(pp, unwrapped799)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1354 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1354 = nothing
                                                end
                                                deconstruct_result796 = _t1354
                                                if !isnothing(deconstruct_result796)
                                                    unwrapped797 = deconstruct_result796
                                                    pretty_boolean_type(pp, unwrapped797)
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
    return nothing
end

function pretty_unspecified_type(pp::PrettyPrinter, msg::Proto.UnspecifiedType)
    fields819 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields820 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields821 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields822 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields823 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields824 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields825 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields826 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields827 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat832 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat832)
        write(pp, flat832)
        return nothing
    else
        _dollar_dollar = msg
        fields828 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields829 = fields828
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field830 = unwrapped_fields829[1]
        write(pp, format_int(pp, field830))
        newline(pp)
        field831 = unwrapped_fields829[2]
        write(pp, format_int(pp, field831))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields833 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat837 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat837)
        write(pp, flat837)
        return nothing
    else
        fields834 = msg
        write(pp, "|")
        if !isempty(fields834)
            write(pp, " ")
            for (i1355, elem835) in enumerate(fields834)
                i836 = i1355 - 1
                if (i836 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem835)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat864 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat864)
        write(pp, flat864)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1356 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1356 = nothing
        end
        deconstruct_result862 = _t1356
        if !isnothing(deconstruct_result862)
            unwrapped863 = deconstruct_result862
            pretty_true(pp, unwrapped863)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1357 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1357 = nothing
            end
            deconstruct_result860 = _t1357
            if !isnothing(deconstruct_result860)
                unwrapped861 = deconstruct_result860
                pretty_false(pp, unwrapped861)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1358 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1358 = nothing
                end
                deconstruct_result858 = _t1358
                if !isnothing(deconstruct_result858)
                    unwrapped859 = deconstruct_result858
                    pretty_exists(pp, unwrapped859)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1359 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1359 = nothing
                    end
                    deconstruct_result856 = _t1359
                    if !isnothing(deconstruct_result856)
                        unwrapped857 = deconstruct_result856
                        pretty_reduce(pp, unwrapped857)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1360 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1360 = nothing
                        end
                        deconstruct_result854 = _t1360
                        if !isnothing(deconstruct_result854)
                            unwrapped855 = deconstruct_result854
                            pretty_conjunction(pp, unwrapped855)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1361 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1361 = nothing
                            end
                            deconstruct_result852 = _t1361
                            if !isnothing(deconstruct_result852)
                                unwrapped853 = deconstruct_result852
                                pretty_disjunction(pp, unwrapped853)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1362 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1362 = nothing
                                end
                                deconstruct_result850 = _t1362
                                if !isnothing(deconstruct_result850)
                                    unwrapped851 = deconstruct_result850
                                    pretty_not(pp, unwrapped851)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1363 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1363 = nothing
                                    end
                                    deconstruct_result848 = _t1363
                                    if !isnothing(deconstruct_result848)
                                        unwrapped849 = deconstruct_result848
                                        pretty_ffi(pp, unwrapped849)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1364 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1364 = nothing
                                        end
                                        deconstruct_result846 = _t1364
                                        if !isnothing(deconstruct_result846)
                                            unwrapped847 = deconstruct_result846
                                            pretty_atom(pp, unwrapped847)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1365 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1365 = nothing
                                            end
                                            deconstruct_result844 = _t1365
                                            if !isnothing(deconstruct_result844)
                                                unwrapped845 = deconstruct_result844
                                                pretty_pragma(pp, unwrapped845)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1366 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1366 = nothing
                                                end
                                                deconstruct_result842 = _t1366
                                                if !isnothing(deconstruct_result842)
                                                    unwrapped843 = deconstruct_result842
                                                    pretty_primitive(pp, unwrapped843)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1367 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1367 = nothing
                                                    end
                                                    deconstruct_result840 = _t1367
                                                    if !isnothing(deconstruct_result840)
                                                        unwrapped841 = deconstruct_result840
                                                        pretty_rel_atom(pp, unwrapped841)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1368 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1368 = nothing
                                                        end
                                                        deconstruct_result838 = _t1368
                                                        if !isnothing(deconstruct_result838)
                                                            unwrapped839 = deconstruct_result838
                                                            pretty_cast(pp, unwrapped839)
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
    fields865 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields866 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat871 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat871)
        write(pp, flat871)
        return nothing
    else
        _dollar_dollar = msg
        _t1369 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields867 = (_t1369, _dollar_dollar.body.value,)
        unwrapped_fields868 = fields867
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field869 = unwrapped_fields868[1]
        pretty_bindings(pp, field869)
        newline(pp)
        field870 = unwrapped_fields868[2]
        pretty_formula(pp, field870)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat877 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat877)
        write(pp, flat877)
        return nothing
    else
        _dollar_dollar = msg
        fields872 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields873 = fields872
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field874 = unwrapped_fields873[1]
        pretty_abstraction(pp, field874)
        newline(pp)
        field875 = unwrapped_fields873[2]
        pretty_abstraction(pp, field875)
        newline(pp)
        field876 = unwrapped_fields873[3]
        pretty_terms(pp, field876)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat881 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat881)
        write(pp, flat881)
        return nothing
    else
        fields878 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields878)
            newline(pp)
            for (i1370, elem879) in enumerate(fields878)
                i880 = i1370 - 1
                if (i880 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem879)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat886 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat886)
        write(pp, flat886)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1371 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1371 = nothing
        end
        deconstruct_result884 = _t1371
        if !isnothing(deconstruct_result884)
            unwrapped885 = deconstruct_result884
            pretty_var(pp, unwrapped885)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1372 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1372 = nothing
            end
            deconstruct_result882 = _t1372
            if !isnothing(deconstruct_result882)
                unwrapped883 = deconstruct_result882
                pretty_constant(pp, unwrapped883)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat889 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat889)
        write(pp, flat889)
        return nothing
    else
        _dollar_dollar = msg
        fields887 = _dollar_dollar.name
        unwrapped_fields888 = fields887
        write(pp, unwrapped_fields888)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat891 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat891)
        write(pp, flat891)
        return nothing
    else
        fields890 = msg
        pretty_value(pp, fields890)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat896 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat896)
        write(pp, flat896)
        return nothing
    else
        _dollar_dollar = msg
        fields892 = _dollar_dollar.args
        unwrapped_fields893 = fields892
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields893)
            newline(pp)
            for (i1373, elem894) in enumerate(unwrapped_fields893)
                i895 = i1373 - 1
                if (i895 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem894)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat901 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat901)
        write(pp, flat901)
        return nothing
    else
        _dollar_dollar = msg
        fields897 = _dollar_dollar.args
        unwrapped_fields898 = fields897
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields898)
            newline(pp)
            for (i1374, elem899) in enumerate(unwrapped_fields898)
                i900 = i1374 - 1
                if (i900 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem899)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat904 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat904)
        write(pp, flat904)
        return nothing
    else
        _dollar_dollar = msg
        fields902 = _dollar_dollar.arg
        unwrapped_fields903 = fields902
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields903)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat910 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat910)
        write(pp, flat910)
        return nothing
    else
        _dollar_dollar = msg
        fields905 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields906 = fields905
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field907 = unwrapped_fields906[1]
        pretty_name(pp, field907)
        newline(pp)
        field908 = unwrapped_fields906[2]
        pretty_ffi_args(pp, field908)
        newline(pp)
        field909 = unwrapped_fields906[3]
        pretty_terms(pp, field909)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat912 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat912)
        write(pp, flat912)
        return nothing
    else
        fields911 = msg
        write(pp, ":")
        write(pp, fields911)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat916 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat916)
        write(pp, flat916)
        return nothing
    else
        fields913 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields913)
            newline(pp)
            for (i1375, elem914) in enumerate(fields913)
                i915 = i1375 - 1
                if (i915 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem914)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat923 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat923)
        write(pp, flat923)
        return nothing
    else
        _dollar_dollar = msg
        fields917 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields918 = fields917
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field919 = unwrapped_fields918[1]
        pretty_relation_id(pp, field919)
        field920 = unwrapped_fields918[2]
        if !isempty(field920)
            newline(pp)
            for (i1376, elem921) in enumerate(field920)
                i922 = i1376 - 1
                if (i922 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem921)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat930 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat930)
        write(pp, flat930)
        return nothing
    else
        _dollar_dollar = msg
        fields924 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields925 = fields924
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field926 = unwrapped_fields925[1]
        pretty_name(pp, field926)
        field927 = unwrapped_fields925[2]
        if !isempty(field927)
            newline(pp)
            for (i1377, elem928) in enumerate(field927)
                i929 = i1377 - 1
                if (i929 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem928)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat946 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1378 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1378 = nothing
        end
        guard_result945 = _t1378
        if !isnothing(guard_result945)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1379 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1379 = nothing
            end
            guard_result944 = _t1379
            if !isnothing(guard_result944)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1380 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1380 = nothing
                end
                guard_result943 = _t1380
                if !isnothing(guard_result943)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1381 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1381 = nothing
                    end
                    guard_result942 = _t1381
                    if !isnothing(guard_result942)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1382 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1382 = nothing
                        end
                        guard_result941 = _t1382
                        if !isnothing(guard_result941)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1383 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1383 = nothing
                            end
                            guard_result940 = _t1383
                            if !isnothing(guard_result940)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1384 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1384 = nothing
                                end
                                guard_result939 = _t1384
                                if !isnothing(guard_result939)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1385 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1385 = nothing
                                    end
                                    guard_result938 = _t1385
                                    if !isnothing(guard_result938)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1386 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1386 = nothing
                                        end
                                        guard_result937 = _t1386
                                        if !isnothing(guard_result937)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields931 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields932 = fields931
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field933 = unwrapped_fields932[1]
                                            pretty_name(pp, field933)
                                            field934 = unwrapped_fields932[2]
                                            if !isempty(field934)
                                                newline(pp)
                                                for (i1387, elem935) in enumerate(field934)
                                                    i936 = i1387 - 1
                                                    if (i936 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem935)
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
    flat951 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat951)
        write(pp, flat951)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1388 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1388 = nothing
        end
        fields947 = _t1388
        unwrapped_fields948 = fields947
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field949 = unwrapped_fields948[1]
        pretty_term(pp, field949)
        newline(pp)
        field950 = unwrapped_fields948[2]
        pretty_term(pp, field950)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat956 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat956)
        write(pp, flat956)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1389 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1389 = nothing
        end
        fields952 = _t1389
        unwrapped_fields953 = fields952
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field954 = unwrapped_fields953[1]
        pretty_term(pp, field954)
        newline(pp)
        field955 = unwrapped_fields953[2]
        pretty_term(pp, field955)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat961 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat961)
        write(pp, flat961)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1390 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1390 = nothing
        end
        fields957 = _t1390
        unwrapped_fields958 = fields957
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field959 = unwrapped_fields958[1]
        pretty_term(pp, field959)
        newline(pp)
        field960 = unwrapped_fields958[2]
        pretty_term(pp, field960)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat966 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat966)
        write(pp, flat966)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1391 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1391 = nothing
        end
        fields962 = _t1391
        unwrapped_fields963 = fields962
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field964 = unwrapped_fields963[1]
        pretty_term(pp, field964)
        newline(pp)
        field965 = unwrapped_fields963[2]
        pretty_term(pp, field965)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat971 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat971)
        write(pp, flat971)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1392 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1392 = nothing
        end
        fields967 = _t1392
        unwrapped_fields968 = fields967
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field969 = unwrapped_fields968[1]
        pretty_term(pp, field969)
        newline(pp)
        field970 = unwrapped_fields968[2]
        pretty_term(pp, field970)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat977 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat977)
        write(pp, flat977)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1393 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1393 = nothing
        end
        fields972 = _t1393
        unwrapped_fields973 = fields972
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field974 = unwrapped_fields973[1]
        pretty_term(pp, field974)
        newline(pp)
        field975 = unwrapped_fields973[2]
        pretty_term(pp, field975)
        newline(pp)
        field976 = unwrapped_fields973[3]
        pretty_term(pp, field976)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat983 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat983)
        write(pp, flat983)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1394 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1394 = nothing
        end
        fields978 = _t1394
        unwrapped_fields979 = fields978
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field980 = unwrapped_fields979[1]
        pretty_term(pp, field980)
        newline(pp)
        field981 = unwrapped_fields979[2]
        pretty_term(pp, field981)
        newline(pp)
        field982 = unwrapped_fields979[3]
        pretty_term(pp, field982)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat989 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat989)
        write(pp, flat989)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1395 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1395 = nothing
        end
        fields984 = _t1395
        unwrapped_fields985 = fields984
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field986 = unwrapped_fields985[1]
        pretty_term(pp, field986)
        newline(pp)
        field987 = unwrapped_fields985[2]
        pretty_term(pp, field987)
        newline(pp)
        field988 = unwrapped_fields985[3]
        pretty_term(pp, field988)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat995 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat995)
        write(pp, flat995)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1396 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1396 = nothing
        end
        fields990 = _t1396
        unwrapped_fields991 = fields990
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field992 = unwrapped_fields991[1]
        pretty_term(pp, field992)
        newline(pp)
        field993 = unwrapped_fields991[2]
        pretty_term(pp, field993)
        newline(pp)
        field994 = unwrapped_fields991[3]
        pretty_term(pp, field994)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1000 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1000)
        write(pp, flat1000)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1397 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1397 = nothing
        end
        deconstruct_result998 = _t1397
        if !isnothing(deconstruct_result998)
            unwrapped999 = deconstruct_result998
            pretty_specialized_value(pp, unwrapped999)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1398 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1398 = nothing
            end
            deconstruct_result996 = _t1398
            if !isnothing(deconstruct_result996)
                unwrapped997 = deconstruct_result996
                pretty_term(pp, unwrapped997)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1002 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1002)
        write(pp, flat1002)
        return nothing
    else
        fields1001 = msg
        write(pp, "#")
        pretty_value(pp, fields1001)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1009 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1009)
        write(pp, flat1009)
        return nothing
    else
        _dollar_dollar = msg
        fields1003 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1004 = fields1003
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1005 = unwrapped_fields1004[1]
        pretty_name(pp, field1005)
        field1006 = unwrapped_fields1004[2]
        if !isempty(field1006)
            newline(pp)
            for (i1399, elem1007) in enumerate(field1006)
                i1008 = i1399 - 1
                if (i1008 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1007)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1014 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1014)
        write(pp, flat1014)
        return nothing
    else
        _dollar_dollar = msg
        fields1010 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1011 = fields1010
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1012 = unwrapped_fields1011[1]
        pretty_term(pp, field1012)
        newline(pp)
        field1013 = unwrapped_fields1011[2]
        pretty_term(pp, field1013)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1018 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1018)
        write(pp, flat1018)
        return nothing
    else
        fields1015 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1015)
            newline(pp)
            for (i1400, elem1016) in enumerate(fields1015)
                i1017 = i1400 - 1
                if (i1017 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1016)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1025 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1025)
        write(pp, flat1025)
        return nothing
    else
        _dollar_dollar = msg
        fields1019 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1020 = fields1019
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1021 = unwrapped_fields1020[1]
        pretty_name(pp, field1021)
        field1022 = unwrapped_fields1020[2]
        if !isempty(field1022)
            newline(pp)
            for (i1401, elem1023) in enumerate(field1022)
                i1024 = i1401 - 1
                if (i1024 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem1023)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1032 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1032)
        write(pp, flat1032)
        return nothing
    else
        _dollar_dollar = msg
        fields1026 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1027 = fields1026
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1028 = unwrapped_fields1027[1]
        if !isempty(field1028)
            newline(pp)
            for (i1402, elem1029) in enumerate(field1028)
                i1030 = i1402 - 1
                if (i1030 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1029)
            end
        end
        newline(pp)
        field1031 = unwrapped_fields1027[2]
        pretty_script(pp, field1031)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1037 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1037)
        write(pp, flat1037)
        return nothing
    else
        _dollar_dollar = msg
        fields1033 = _dollar_dollar.constructs
        unwrapped_fields1034 = fields1033
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1034)
            newline(pp)
            for (i1403, elem1035) in enumerate(unwrapped_fields1034)
                i1036 = i1403 - 1
                if (i1036 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1035)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1042 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1042)
        write(pp, flat1042)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1404 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1404 = nothing
        end
        deconstruct_result1040 = _t1404
        if !isnothing(deconstruct_result1040)
            unwrapped1041 = deconstruct_result1040
            pretty_loop(pp, unwrapped1041)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1405 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1405 = nothing
            end
            deconstruct_result1038 = _t1405
            if !isnothing(deconstruct_result1038)
                unwrapped1039 = deconstruct_result1038
                pretty_instruction(pp, unwrapped1039)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1047 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1047)
        write(pp, flat1047)
        return nothing
    else
        _dollar_dollar = msg
        fields1043 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1044 = fields1043
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1045 = unwrapped_fields1044[1]
        pretty_init(pp, field1045)
        newline(pp)
        field1046 = unwrapped_fields1044[2]
        pretty_script(pp, field1046)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1051 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1051)
        write(pp, flat1051)
        return nothing
    else
        fields1048 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1048)
            newline(pp)
            for (i1406, elem1049) in enumerate(fields1048)
                i1050 = i1406 - 1
                if (i1050 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1049)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1062 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1062)
        write(pp, flat1062)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1407 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1407 = nothing
        end
        deconstruct_result1060 = _t1407
        if !isnothing(deconstruct_result1060)
            unwrapped1061 = deconstruct_result1060
            pretty_assign(pp, unwrapped1061)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1408 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1408 = nothing
            end
            deconstruct_result1058 = _t1408
            if !isnothing(deconstruct_result1058)
                unwrapped1059 = deconstruct_result1058
                pretty_upsert(pp, unwrapped1059)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1409 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1409 = nothing
                end
                deconstruct_result1056 = _t1409
                if !isnothing(deconstruct_result1056)
                    unwrapped1057 = deconstruct_result1056
                    pretty_break(pp, unwrapped1057)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1410 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1410 = nothing
                    end
                    deconstruct_result1054 = _t1410
                    if !isnothing(deconstruct_result1054)
                        unwrapped1055 = deconstruct_result1054
                        pretty_monoid_def(pp, unwrapped1055)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1411 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1411 = nothing
                        end
                        deconstruct_result1052 = _t1411
                        if !isnothing(deconstruct_result1052)
                            unwrapped1053 = deconstruct_result1052
                            pretty_monus_def(pp, unwrapped1053)
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
    flat1069 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1069)
        write(pp, flat1069)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1412 = _dollar_dollar.attrs
        else
            _t1412 = nothing
        end
        fields1063 = (_dollar_dollar.name, _dollar_dollar.body, _t1412,)
        unwrapped_fields1064 = fields1063
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1065 = unwrapped_fields1064[1]
        pretty_relation_id(pp, field1065)
        newline(pp)
        field1066 = unwrapped_fields1064[2]
        pretty_abstraction(pp, field1066)
        field1067 = unwrapped_fields1064[3]
        if !isnothing(field1067)
            newline(pp)
            opt_val1068 = field1067
            pretty_attrs(pp, opt_val1068)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1076 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1076)
        write(pp, flat1076)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1413 = _dollar_dollar.attrs
        else
            _t1413 = nothing
        end
        fields1070 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1413,)
        unwrapped_fields1071 = fields1070
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1072 = unwrapped_fields1071[1]
        pretty_relation_id(pp, field1072)
        newline(pp)
        field1073 = unwrapped_fields1071[2]
        pretty_abstraction_with_arity(pp, field1073)
        field1074 = unwrapped_fields1071[3]
        if !isnothing(field1074)
            newline(pp)
            opt_val1075 = field1074
            pretty_attrs(pp, opt_val1075)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1081 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1081)
        write(pp, flat1081)
        return nothing
    else
        _dollar_dollar = msg
        _t1414 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1077 = (_t1414, _dollar_dollar[1].value,)
        unwrapped_fields1078 = fields1077
        write(pp, "(")
        indent!(pp)
        field1079 = unwrapped_fields1078[1]
        pretty_bindings(pp, field1079)
        newline(pp)
        field1080 = unwrapped_fields1078[2]
        pretty_formula(pp, field1080)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1088 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1088)
        write(pp, flat1088)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1415 = _dollar_dollar.attrs
        else
            _t1415 = nothing
        end
        fields1082 = (_dollar_dollar.name, _dollar_dollar.body, _t1415,)
        unwrapped_fields1083 = fields1082
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1084 = unwrapped_fields1083[1]
        pretty_relation_id(pp, field1084)
        newline(pp)
        field1085 = unwrapped_fields1083[2]
        pretty_abstraction(pp, field1085)
        field1086 = unwrapped_fields1083[3]
        if !isnothing(field1086)
            newline(pp)
            opt_val1087 = field1086
            pretty_attrs(pp, opt_val1087)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1096 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1416 = _dollar_dollar.attrs
        else
            _t1416 = nothing
        end
        fields1089 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1416,)
        unwrapped_fields1090 = fields1089
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1091 = unwrapped_fields1090[1]
        pretty_monoid(pp, field1091)
        newline(pp)
        field1092 = unwrapped_fields1090[2]
        pretty_relation_id(pp, field1092)
        newline(pp)
        field1093 = unwrapped_fields1090[3]
        pretty_abstraction_with_arity(pp, field1093)
        field1094 = unwrapped_fields1090[4]
        if !isnothing(field1094)
            newline(pp)
            opt_val1095 = field1094
            pretty_attrs(pp, opt_val1095)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1105 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1105)
        write(pp, flat1105)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1417 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1417 = nothing
        end
        deconstruct_result1103 = _t1417
        if !isnothing(deconstruct_result1103)
            unwrapped1104 = deconstruct_result1103
            pretty_or_monoid(pp, unwrapped1104)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1418 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1418 = nothing
            end
            deconstruct_result1101 = _t1418
            if !isnothing(deconstruct_result1101)
                unwrapped1102 = deconstruct_result1101
                pretty_min_monoid(pp, unwrapped1102)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1419 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1419 = nothing
                end
                deconstruct_result1099 = _t1419
                if !isnothing(deconstruct_result1099)
                    unwrapped1100 = deconstruct_result1099
                    pretty_max_monoid(pp, unwrapped1100)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1420 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1420 = nothing
                    end
                    deconstruct_result1097 = _t1420
                    if !isnothing(deconstruct_result1097)
                        unwrapped1098 = deconstruct_result1097
                        pretty_sum_monoid(pp, unwrapped1098)
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
    fields1106 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1109 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1109)
        write(pp, flat1109)
        return nothing
    else
        _dollar_dollar = msg
        fields1107 = _dollar_dollar.var"#type"
        unwrapped_fields1108 = fields1107
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1108)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1112 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1112)
        write(pp, flat1112)
        return nothing
    else
        _dollar_dollar = msg
        fields1110 = _dollar_dollar.var"#type"
        unwrapped_fields1111 = fields1110
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1111)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1115 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1115)
        write(pp, flat1115)
        return nothing
    else
        _dollar_dollar = msg
        fields1113 = _dollar_dollar.var"#type"
        unwrapped_fields1114 = fields1113
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1114)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1123 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1123)
        write(pp, flat1123)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1421 = _dollar_dollar.attrs
        else
            _t1421 = nothing
        end
        fields1116 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1421,)
        unwrapped_fields1117 = fields1116
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1118 = unwrapped_fields1117[1]
        pretty_monoid(pp, field1118)
        newline(pp)
        field1119 = unwrapped_fields1117[2]
        pretty_relation_id(pp, field1119)
        newline(pp)
        field1120 = unwrapped_fields1117[3]
        pretty_abstraction_with_arity(pp, field1120)
        field1121 = unwrapped_fields1117[4]
        if !isnothing(field1121)
            newline(pp)
            opt_val1122 = field1121
            pretty_attrs(pp, opt_val1122)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1130 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1130)
        write(pp, flat1130)
        return nothing
    else
        _dollar_dollar = msg
        fields1124 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1125 = fields1124
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1126 = unwrapped_fields1125[1]
        pretty_relation_id(pp, field1126)
        newline(pp)
        field1127 = unwrapped_fields1125[2]
        pretty_abstraction(pp, field1127)
        newline(pp)
        field1128 = unwrapped_fields1125[3]
        pretty_functional_dependency_keys(pp, field1128)
        newline(pp)
        field1129 = unwrapped_fields1125[4]
        pretty_functional_dependency_values(pp, field1129)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1134 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1134)
        write(pp, flat1134)
        return nothing
    else
        fields1131 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1131)
            newline(pp)
            for (i1422, elem1132) in enumerate(fields1131)
                i1133 = i1422 - 1
                if (i1133 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1132)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1138 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1138)
        write(pp, flat1138)
        return nothing
    else
        fields1135 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1135)
            newline(pp)
            for (i1423, elem1136) in enumerate(fields1135)
                i1137 = i1423 - 1
                if (i1137 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1136)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1145 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1145)
        write(pp, flat1145)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1424 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1424 = nothing
        end
        deconstruct_result1143 = _t1424
        if !isnothing(deconstruct_result1143)
            unwrapped1144 = deconstruct_result1143
            pretty_edb(pp, unwrapped1144)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1425 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1425 = nothing
            end
            deconstruct_result1141 = _t1425
            if !isnothing(deconstruct_result1141)
                unwrapped1142 = deconstruct_result1141
                pretty_betree_relation(pp, unwrapped1142)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1426 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1426 = nothing
                end
                deconstruct_result1139 = _t1426
                if !isnothing(deconstruct_result1139)
                    unwrapped1140 = deconstruct_result1139
                    pretty_csv_data(pp, unwrapped1140)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_edb(pp::PrettyPrinter, msg::Proto.EDB)
    flat1151 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1151)
        write(pp, flat1151)
        return nothing
    else
        _dollar_dollar = msg
        fields1146 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1147 = fields1146
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1148 = unwrapped_fields1147[1]
        pretty_relation_id(pp, field1148)
        newline(pp)
        field1149 = unwrapped_fields1147[2]
        pretty_edb_path(pp, field1149)
        newline(pp)
        field1150 = unwrapped_fields1147[3]
        pretty_edb_types(pp, field1150)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1155 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1155)
        write(pp, flat1155)
        return nothing
    else
        fields1152 = msg
        write(pp, "[")
        indent!(pp)
        for (i1427, elem1153) in enumerate(fields1152)
            i1154 = i1427 - 1
            if (i1154 > 0)
                newline(pp)
            end
            write(pp, format_string(pp, elem1153))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1159 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1159)
        write(pp, flat1159)
        return nothing
    else
        fields1156 = msg
        write(pp, "[")
        indent!(pp)
        for (i1428, elem1157) in enumerate(fields1156)
            i1158 = i1428 - 1
            if (i1158 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1157)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1164 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1164)
        write(pp, flat1164)
        return nothing
    else
        _dollar_dollar = msg
        fields1160 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1161 = fields1160
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1162 = unwrapped_fields1161[1]
        pretty_relation_id(pp, field1162)
        newline(pp)
        field1163 = unwrapped_fields1161[2]
        pretty_betree_info(pp, field1163)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1170 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1170)
        write(pp, flat1170)
        return nothing
    else
        _dollar_dollar = msg
        _t1429 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1165 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1429,)
        unwrapped_fields1166 = fields1165
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1167 = unwrapped_fields1166[1]
        pretty_betree_info_key_types(pp, field1167)
        newline(pp)
        field1168 = unwrapped_fields1166[2]
        pretty_betree_info_value_types(pp, field1168)
        newline(pp)
        field1169 = unwrapped_fields1166[3]
        pretty_config_dict(pp, field1169)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1174 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1174)
        write(pp, flat1174)
        return nothing
    else
        fields1171 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1171)
            newline(pp)
            for (i1430, elem1172) in enumerate(fields1171)
                i1173 = i1430 - 1
                if (i1173 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1172)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1178 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1178)
        write(pp, flat1178)
        return nothing
    else
        fields1175 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1175)
            newline(pp)
            for (i1431, elem1176) in enumerate(fields1175)
                i1177 = i1431 - 1
                if (i1177 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1176)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1185 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1185)
        write(pp, flat1185)
        return nothing
    else
        _dollar_dollar = msg
        fields1179 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1180 = fields1179
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1181 = unwrapped_fields1180[1]
        pretty_csvlocator(pp, field1181)
        newline(pp)
        field1182 = unwrapped_fields1180[2]
        pretty_csv_config(pp, field1182)
        newline(pp)
        field1183 = unwrapped_fields1180[3]
        pretty_gnf_columns(pp, field1183)
        newline(pp)
        field1184 = unwrapped_fields1180[4]
        pretty_csv_asof(pp, field1184)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1192 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1192)
        write(pp, flat1192)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1432 = _dollar_dollar.paths
        else
            _t1432 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1433 = String(copy(_dollar_dollar.inline_data))
        else
            _t1433 = nothing
        end
        fields1186 = (_t1432, _t1433,)
        unwrapped_fields1187 = fields1186
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1188 = unwrapped_fields1187[1]
        if !isnothing(field1188)
            newline(pp)
            opt_val1189 = field1188
            pretty_csv_locator_paths(pp, opt_val1189)
        end
        field1190 = unwrapped_fields1187[2]
        if !isnothing(field1190)
            newline(pp)
            opt_val1191 = field1190
            pretty_csv_locator_inline_data(pp, opt_val1191)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1196 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1196)
        write(pp, flat1196)
        return nothing
    else
        fields1193 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1193)
            newline(pp)
            for (i1434, elem1194) in enumerate(fields1193)
                i1195 = i1434 - 1
                if (i1195 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1194))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1198 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1198)
        write(pp, flat1198)
        return nothing
    else
        fields1197 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1197))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1201 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1201)
        write(pp, flat1201)
        return nothing
    else
        _dollar_dollar = msg
        _t1435 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1199 = _t1435
        unwrapped_fields1200 = fields1199
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1200)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1205 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1205)
        write(pp, flat1205)
        return nothing
    else
        fields1202 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1202)
            newline(pp)
            for (i1436, elem1203) in enumerate(fields1202)
                i1204 = i1436 - 1
                if (i1204 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1203)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1214 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1214)
        write(pp, flat1214)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1437 = _dollar_dollar.target_id
        else
            _t1437 = nothing
        end
        fields1206 = (_dollar_dollar.column_path, _t1437, _dollar_dollar.types,)
        unwrapped_fields1207 = fields1206
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1208 = unwrapped_fields1207[1]
        pretty_gnf_column_path(pp, field1208)
        field1209 = unwrapped_fields1207[2]
        if !isnothing(field1209)
            newline(pp)
            opt_val1210 = field1209
            pretty_relation_id(pp, opt_val1210)
        end
        newline(pp)
        write(pp, "[")
        field1211 = unwrapped_fields1207[3]
        for (i1438, elem1212) in enumerate(field1211)
            i1213 = i1438 - 1
            if (i1213 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1212)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1221 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1221)
        write(pp, flat1221)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1439 = _dollar_dollar[1]
        else
            _t1439 = nothing
        end
        deconstruct_result1219 = _t1439
        if !isnothing(deconstruct_result1219)
            unwrapped1220 = deconstruct_result1219
            write(pp, format_string(pp, unwrapped1220))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1440 = _dollar_dollar
            else
                _t1440 = nothing
            end
            deconstruct_result1215 = _t1440
            if !isnothing(deconstruct_result1215)
                unwrapped1216 = deconstruct_result1215
                write(pp, "[")
                indent!(pp)
                for (i1441, elem1217) in enumerate(unwrapped1216)
                    i1218 = i1441 - 1
                    if (i1218 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(pp, elem1217))
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
    flat1223 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1223)
        write(pp, flat1223)
        return nothing
    else
        fields1222 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1222))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1226 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1226)
        write(pp, flat1226)
        return nothing
    else
        _dollar_dollar = msg
        fields1224 = _dollar_dollar.fragment_id
        unwrapped_fields1225 = fields1224
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1225)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1231 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1231)
        write(pp, flat1231)
        return nothing
    else
        _dollar_dollar = msg
        fields1227 = _dollar_dollar.relations
        unwrapped_fields1228 = fields1227
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1228)
            newline(pp)
            for (i1442, elem1229) in enumerate(unwrapped_fields1228)
                i1230 = i1442 - 1
                if (i1230 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1229)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1236 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1236)
        write(pp, flat1236)
        return nothing
    else
        _dollar_dollar = msg
        fields1232 = _dollar_dollar.mappings
        unwrapped_fields1233 = fields1232
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1233)
            newline(pp)
            for (i1443, elem1234) in enumerate(unwrapped_fields1233)
                i1235 = i1443 - 1
                if (i1235 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1234)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1241 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1241)
        write(pp, flat1241)
        return nothing
    else
        _dollar_dollar = msg
        fields1237 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1238 = fields1237
        field1239 = unwrapped_fields1238[1]
        pretty_edb_path(pp, field1239)
        write(pp, " ")
        field1240 = unwrapped_fields1238[2]
        pretty_relation_id(pp, field1240)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1245 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1245)
        write(pp, flat1245)
        return nothing
    else
        fields1242 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1242)
            newline(pp)
            for (i1444, elem1243) in enumerate(fields1242)
                i1244 = i1444 - 1
                if (i1244 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1243)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1256 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1256)
        write(pp, flat1256)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1445 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1445 = nothing
        end
        deconstruct_result1254 = _t1445
        if !isnothing(deconstruct_result1254)
            unwrapped1255 = deconstruct_result1254
            pretty_demand(pp, unwrapped1255)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1446 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1446 = nothing
            end
            deconstruct_result1252 = _t1446
            if !isnothing(deconstruct_result1252)
                unwrapped1253 = deconstruct_result1252
                pretty_output(pp, unwrapped1253)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1447 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1447 = nothing
                end
                deconstruct_result1250 = _t1447
                if !isnothing(deconstruct_result1250)
                    unwrapped1251 = deconstruct_result1250
                    pretty_what_if(pp, unwrapped1251)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1448 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1448 = nothing
                    end
                    deconstruct_result1248 = _t1448
                    if !isnothing(deconstruct_result1248)
                        unwrapped1249 = deconstruct_result1248
                        pretty_abort(pp, unwrapped1249)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1449 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1449 = nothing
                        end
                        deconstruct_result1246 = _t1449
                        if !isnothing(deconstruct_result1246)
                            unwrapped1247 = deconstruct_result1246
                            pretty_export(pp, unwrapped1247)
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
    flat1259 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1259)
        write(pp, flat1259)
        return nothing
    else
        _dollar_dollar = msg
        fields1257 = _dollar_dollar.relation_id
        unwrapped_fields1258 = fields1257
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1258)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1264 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1264)
        write(pp, flat1264)
        return nothing
    else
        _dollar_dollar = msg
        fields1260 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1261 = fields1260
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1262 = unwrapped_fields1261[1]
        pretty_name(pp, field1262)
        newline(pp)
        field1263 = unwrapped_fields1261[2]
        pretty_relation_id(pp, field1263)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1269 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1269)
        write(pp, flat1269)
        return nothing
    else
        _dollar_dollar = msg
        fields1265 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1266 = fields1265
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1267 = unwrapped_fields1266[1]
        pretty_name(pp, field1267)
        newline(pp)
        field1268 = unwrapped_fields1266[2]
        pretty_epoch(pp, field1268)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1275 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1275)
        write(pp, flat1275)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1450 = _dollar_dollar.name
        else
            _t1450 = nothing
        end
        fields1270 = (_t1450, _dollar_dollar.relation_id,)
        unwrapped_fields1271 = fields1270
        write(pp, "(abort")
        indent_sexp!(pp)
        field1272 = unwrapped_fields1271[1]
        if !isnothing(field1272)
            newline(pp)
            opt_val1273 = field1272
            pretty_name(pp, opt_val1273)
        end
        newline(pp)
        field1274 = unwrapped_fields1271[2]
        pretty_relation_id(pp, field1274)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1278 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1278)
        write(pp, flat1278)
        return nothing
    else
        _dollar_dollar = msg
        fields1276 = _get_oneof_field(_dollar_dollar, :csv_config)
        unwrapped_fields1277 = fields1276
        write(pp, "(export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1277)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1289 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1289)
        write(pp, flat1289)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1451 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1451 = nothing
        end
        deconstruct_result1284 = _t1451
        if !isnothing(deconstruct_result1284)
            unwrapped1285 = deconstruct_result1284
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1286 = unwrapped1285[1]
            pretty_export_csv_path(pp, field1286)
            newline(pp)
            field1287 = unwrapped1285[2]
            pretty_export_csv_source(pp, field1287)
            newline(pp)
            field1288 = unwrapped1285[3]
            pretty_csv_config(pp, field1288)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1453 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1452 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1453,)
            else
                _t1452 = nothing
            end
            deconstruct_result1279 = _t1452
            if !isnothing(deconstruct_result1279)
                unwrapped1280 = deconstruct_result1279
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1281 = unwrapped1280[1]
                pretty_export_csv_path(pp, field1281)
                newline(pp)
                field1282 = unwrapped1280[2]
                pretty_export_csv_columns_list(pp, field1282)
                newline(pp)
                field1283 = unwrapped1280[3]
                pretty_config_dict(pp, field1283)
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
    flat1291 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1291)
        write(pp, flat1291)
        return nothing
    else
        fields1290 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1290))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1298 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1298)
        write(pp, flat1298)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1454 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1454 = nothing
        end
        deconstruct_result1294 = _t1454
        if !isnothing(deconstruct_result1294)
            unwrapped1295 = deconstruct_result1294
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1295)
                newline(pp)
                for (i1455, elem1296) in enumerate(unwrapped1295)
                    i1297 = i1455 - 1
                    if (i1297 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1296)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1456 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1456 = nothing
            end
            deconstruct_result1292 = _t1456
            if !isnothing(deconstruct_result1292)
                unwrapped1293 = deconstruct_result1292
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1293)
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
    flat1303 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1303)
        write(pp, flat1303)
        return nothing
    else
        _dollar_dollar = msg
        fields1299 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1300 = fields1299
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1301 = unwrapped_fields1300[1]
        write(pp, format_string(pp, field1301))
        newline(pp)
        field1302 = unwrapped_fields1300[2]
        pretty_relation_id(pp, field1302)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1307 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1307)
        write(pp, flat1307)
        return nothing
    else
        fields1304 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1304)
            newline(pp)
            for (i1457, elem1305) in enumerate(fields1304)
                i1306 = i1457 - 1
                if (i1306 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1305)
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
    for (i1496, _rid) in enumerate(msg.ids)
        _idx = i1496 - 1
        newline(pp)
        write(pp, "(")
        _t1497 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1497)
        write(pp, " ")
        write(pp, format_string(pp, msg.orig_names[_idx + 1]))
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
    write(pp, format_float(pp, msg.epsilon))
    newline(pp)
    write(pp, ":max_pivots ")
    write(pp, format_int(pp, msg.max_pivots))
    newline(pp)
    write(pp, ":max_deltas ")
    write(pp, format_int(pp, msg.max_deltas))
    newline(pp)
    write(pp, ":max_leaf ")
    write(pp, format_int(pp, msg.max_leaf))
    write(pp, ")")
    dedent!(pp)
    return nothing
end

function pretty_be_tree_locator(pp::PrettyPrinter, msg::Proto.BeTreeLocator)
    write(pp, "(be_tree_locator")
    indent_sexp!(pp)
    newline(pp)
    write(pp, ":element_count ")
    write(pp, format_int(pp, msg.element_count))
    newline(pp)
    write(pp, ":tree_height ")
    write(pp, format_int(pp, msg.tree_height))
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
    for (i1498, _elem) in enumerate(msg.keys)
        _idx = i1498 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1499, _elem) in enumerate(msg.values)
        _idx = i1499 - 1
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
    for (i1500, _elem) in enumerate(msg.columns)
        _idx = i1500 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DateValue) = pretty_date(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DateTimeValue) = pretty_datetime(pp, x)
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
export format_decimal, format_int128, format_uint128, format_int, format_float, format_string, format_bool
# Export legacy format functions for backward compatibility
export format_float64, format_string_value
# Export pretty printing API
export pprint, pretty, pretty_debug
export PrettyPrinter
# Export internal helpers for testing
export indent_level, indent!, try_flat

end # module Pretty
