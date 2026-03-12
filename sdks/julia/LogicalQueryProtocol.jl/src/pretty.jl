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
    _t1594 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1594
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1595 = Proto.Value(value=OneOf(:int_value, v))
    return _t1595
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1596 = Proto.Value(value=OneOf(:float_value, v))
    return _t1596
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1597 = Proto.Value(value=OneOf(:string_value, v))
    return _t1597
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1598 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1598
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1599 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1599
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1600 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1600,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1601 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1601,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1602 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1602,))
            end
        end
    end
    _t1603 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1603,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1604 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1604,))
    _t1605 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1605,))
    if msg.new_line != ""
        _t1606 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1606,))
    end
    _t1607 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1607,))
    _t1608 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1608,))
    _t1609 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1609,))
    if msg.comment != ""
        _t1610 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1610,))
    end
    for missing_string in msg.missing_strings
        _t1611 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1611,))
    end
    _t1612 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1612,))
    _t1613 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1613,))
    _t1614 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1614,))
    if msg.partition_size_mb != 0
        _t1615 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1615,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1616 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1616,))
    _t1617 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1617,))
    _t1618 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1618,))
    _t1619 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1619,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1620 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1620,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1621 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1621,))
        end
    end
    _t1622 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1622,))
    _t1623 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1623,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1624 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1624,))
    end
    if !isnothing(msg.compression)
        _t1625 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1625,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1626 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1626,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1627 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1627,))
    end
    if !isnothing(msg.syntax_delim)
        _t1628 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1628,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1629 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1629,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1630 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1630,))
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
        _t1631 = nothing
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
    flat725 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat725)
        write(pp, flat725)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1432 = _dollar_dollar.configure
        else
            _t1432 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1433 = _dollar_dollar.sync
        else
            _t1433 = nothing
        end
        fields716 = (_t1432, _t1433, _dollar_dollar.epochs,)
        unwrapped_fields717 = fields716
        write(pp, "(transaction")
        indent_sexp!(pp)
        field718 = unwrapped_fields717[1]
        if !isnothing(field718)
            newline(pp)
            opt_val719 = field718
            pretty_configure(pp, opt_val719)
        end
        field720 = unwrapped_fields717[2]
        if !isnothing(field720)
            newline(pp)
            opt_val721 = field720
            pretty_sync(pp, opt_val721)
        end
        field722 = unwrapped_fields717[3]
        if !isempty(field722)
            newline(pp)
            for (i1434, elem723) in enumerate(field722)
                i724 = i1434 - 1
                if (i724 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem723)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat728 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat728)
        write(pp, flat728)
        return nothing
    else
        _dollar_dollar = msg
        _t1435 = deconstruct_configure(pp, _dollar_dollar)
        fields726 = _t1435
        unwrapped_fields727 = fields726
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields727)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat732 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat732)
        write(pp, flat732)
        return nothing
    else
        fields729 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields729)
            newline(pp)
            for (i1436, elem730) in enumerate(fields729)
                i731 = i1436 - 1
                if (i731 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem730)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat737 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat737)
        write(pp, flat737)
        return nothing
    else
        _dollar_dollar = msg
        fields733 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields734 = fields733
        write(pp, ":")
        field735 = unwrapped_fields734[1]
        write(pp, field735)
        write(pp, " ")
        field736 = unwrapped_fields734[2]
        pretty_value(pp, field736)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat763 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat763)
        write(pp, flat763)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1437 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1437 = nothing
        end
        deconstruct_result761 = _t1437
        if !isnothing(deconstruct_result761)
            unwrapped762 = deconstruct_result761
            pretty_date(pp, unwrapped762)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1438 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1438 = nothing
            end
            deconstruct_result759 = _t1438
            if !isnothing(deconstruct_result759)
                unwrapped760 = deconstruct_result759
                pretty_datetime(pp, unwrapped760)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1439 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1439 = nothing
                end
                deconstruct_result757 = _t1439
                if !isnothing(deconstruct_result757)
                    unwrapped758 = deconstruct_result757
                    write(pp, format_string(pp, unwrapped758))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                        _t1440 = _get_oneof_field(_dollar_dollar, :int_value)
                    else
                        _t1440 = nothing
                    end
                    deconstruct_result755 = _t1440
                    if !isnothing(deconstruct_result755)
                        unwrapped756 = deconstruct_result755
                        write(pp, format_int(pp, unwrapped756))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                            _t1441 = _get_oneof_field(_dollar_dollar, :float_value)
                        else
                            _t1441 = nothing
                        end
                        deconstruct_result753 = _t1441
                        if !isnothing(deconstruct_result753)
                            unwrapped754 = deconstruct_result753
                            write(pp, format_float(pp, unwrapped754))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                _t1442 = _get_oneof_field(_dollar_dollar, :uint128_value)
                            else
                                _t1442 = nothing
                            end
                            deconstruct_result751 = _t1442
                            if !isnothing(deconstruct_result751)
                                unwrapped752 = deconstruct_result751
                                write(pp, format_uint128(pp, unwrapped752))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                    _t1443 = _get_oneof_field(_dollar_dollar, :int128_value)
                                else
                                    _t1443 = nothing
                                end
                                deconstruct_result749 = _t1443
                                if !isnothing(deconstruct_result749)
                                    unwrapped750 = deconstruct_result749
                                    write(pp, format_int128(pp, unwrapped750))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                        _t1444 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                    else
                                        _t1444 = nothing
                                    end
                                    deconstruct_result747 = _t1444
                                    if !isnothing(deconstruct_result747)
                                        unwrapped748 = deconstruct_result747
                                        write(pp, format_decimal(pp, unwrapped748))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                            _t1445 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                        else
                                            _t1445 = nothing
                                        end
                                        deconstruct_result745 = _t1445
                                        if !isnothing(deconstruct_result745)
                                            unwrapped746 = deconstruct_result745
                                            pretty_boolean_value(pp, unwrapped746)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                                                _t1446 = _get_oneof_field(_dollar_dollar, :int32_value)
                                            else
                                                _t1446 = nothing
                                            end
                                            deconstruct_result743 = _t1446
                                            if !isnothing(deconstruct_result743)
                                                unwrapped744 = deconstruct_result743
                                                write(pp, (string(Int64(unwrapped744)) * "i32"))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                                    _t1447 = _get_oneof_field(_dollar_dollar, :float32_value)
                                                else
                                                    _t1447 = nothing
                                                end
                                                deconstruct_result741 = _t1447
                                                if !isnothing(deconstruct_result741)
                                                    unwrapped742 = deconstruct_result741
                                                    write(pp, (lowercase(string(unwrapped742)) * "f32"))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                                        _t1448 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                                    else
                                                        _t1448 = nothing
                                                    end
                                                    deconstruct_result739 = _t1448
                                                    if !isnothing(deconstruct_result739)
                                                        unwrapped740 = deconstruct_result739
                                                        write(pp, (string(Int64(unwrapped740)) * "u32"))
                                                    else
                                                        fields738 = msg
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
    flat769 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat769)
        write(pp, flat769)
        return nothing
    else
        _dollar_dollar = msg
        fields764 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields765 = fields764
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field766 = unwrapped_fields765[1]
        write(pp, format_int(pp, field766))
        newline(pp)
        field767 = unwrapped_fields765[2]
        write(pp, format_int(pp, field767))
        newline(pp)
        field768 = unwrapped_fields765[3]
        write(pp, format_int(pp, field768))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat780 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat780)
        write(pp, flat780)
        return nothing
    else
        _dollar_dollar = msg
        fields770 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields771 = fields770
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field772 = unwrapped_fields771[1]
        write(pp, format_int(pp, field772))
        newline(pp)
        field773 = unwrapped_fields771[2]
        write(pp, format_int(pp, field773))
        newline(pp)
        field774 = unwrapped_fields771[3]
        write(pp, format_int(pp, field774))
        newline(pp)
        field775 = unwrapped_fields771[4]
        write(pp, format_int(pp, field775))
        newline(pp)
        field776 = unwrapped_fields771[5]
        write(pp, format_int(pp, field776))
        newline(pp)
        field777 = unwrapped_fields771[6]
        write(pp, format_int(pp, field777))
        field778 = unwrapped_fields771[7]
        if !isnothing(field778)
            newline(pp)
            opt_val779 = field778
            write(pp, format_int(pp, opt_val779))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1449 = ()
    else
        _t1449 = nothing
    end
    deconstruct_result783 = _t1449
    if !isnothing(deconstruct_result783)
        unwrapped784 = deconstruct_result783
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1450 = ()
        else
            _t1450 = nothing
        end
        deconstruct_result781 = _t1450
        if !isnothing(deconstruct_result781)
            unwrapped782 = deconstruct_result781
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat789 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat789)
        write(pp, flat789)
        return nothing
    else
        _dollar_dollar = msg
        fields785 = _dollar_dollar.fragments
        unwrapped_fields786 = fields785
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields786)
            newline(pp)
            for (i1451, elem787) in enumerate(unwrapped_fields786)
                i788 = i1451 - 1
                if (i788 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem787)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat792 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat792)
        write(pp, flat792)
        return nothing
    else
        _dollar_dollar = msg
        fields790 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields791 = fields790
        write(pp, ":")
        write(pp, unwrapped_fields791)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat799 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat799)
        write(pp, flat799)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1452 = _dollar_dollar.writes
        else
            _t1452 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1453 = _dollar_dollar.reads
        else
            _t1453 = nothing
        end
        fields793 = (_t1452, _t1453,)
        unwrapped_fields794 = fields793
        write(pp, "(epoch")
        indent_sexp!(pp)
        field795 = unwrapped_fields794[1]
        if !isnothing(field795)
            newline(pp)
            opt_val796 = field795
            pretty_epoch_writes(pp, opt_val796)
        end
        field797 = unwrapped_fields794[2]
        if !isnothing(field797)
            newline(pp)
            opt_val798 = field797
            pretty_epoch_reads(pp, opt_val798)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat803 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat803)
        write(pp, flat803)
        return nothing
    else
        fields800 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields800)
            newline(pp)
            for (i1454, elem801) in enumerate(fields800)
                i802 = i1454 - 1
                if (i802 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem801)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat812 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat812)
        write(pp, flat812)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1455 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1455 = nothing
        end
        deconstruct_result810 = _t1455
        if !isnothing(deconstruct_result810)
            unwrapped811 = deconstruct_result810
            pretty_define(pp, unwrapped811)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1456 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1456 = nothing
            end
            deconstruct_result808 = _t1456
            if !isnothing(deconstruct_result808)
                unwrapped809 = deconstruct_result808
                pretty_undefine(pp, unwrapped809)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1457 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1457 = nothing
                end
                deconstruct_result806 = _t1457
                if !isnothing(deconstruct_result806)
                    unwrapped807 = deconstruct_result806
                    pretty_context(pp, unwrapped807)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1458 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1458 = nothing
                    end
                    deconstruct_result804 = _t1458
                    if !isnothing(deconstruct_result804)
                        unwrapped805 = deconstruct_result804
                        pretty_snapshot(pp, unwrapped805)
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
    flat815 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat815)
        write(pp, flat815)
        return nothing
    else
        _dollar_dollar = msg
        fields813 = _dollar_dollar.fragment
        unwrapped_fields814 = fields813
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields814)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat822 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat822)
        write(pp, flat822)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields816 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields817 = fields816
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field818 = unwrapped_fields817[1]
        pretty_new_fragment_id(pp, field818)
        field819 = unwrapped_fields817[2]
        if !isempty(field819)
            newline(pp)
            for (i1459, elem820) in enumerate(field819)
                i821 = i1459 - 1
                if (i821 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem820)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat824 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat824)
        write(pp, flat824)
        return nothing
    else
        fields823 = msg
        pretty_fragment_id(pp, fields823)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat833 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat833)
        write(pp, flat833)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1460 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1460 = nothing
        end
        deconstruct_result831 = _t1460
        if !isnothing(deconstruct_result831)
            unwrapped832 = deconstruct_result831
            pretty_def(pp, unwrapped832)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1461 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1461 = nothing
            end
            deconstruct_result829 = _t1461
            if !isnothing(deconstruct_result829)
                unwrapped830 = deconstruct_result829
                pretty_algorithm(pp, unwrapped830)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1462 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1462 = nothing
                end
                deconstruct_result827 = _t1462
                if !isnothing(deconstruct_result827)
                    unwrapped828 = deconstruct_result827
                    pretty_constraint(pp, unwrapped828)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1463 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1463 = nothing
                    end
                    deconstruct_result825 = _t1463
                    if !isnothing(deconstruct_result825)
                        unwrapped826 = deconstruct_result825
                        pretty_data(pp, unwrapped826)
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
    flat840 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat840)
        write(pp, flat840)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1464 = _dollar_dollar.attrs
        else
            _t1464 = nothing
        end
        fields834 = (_dollar_dollar.name, _dollar_dollar.body, _t1464,)
        unwrapped_fields835 = fields834
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field836 = unwrapped_fields835[1]
        pretty_relation_id(pp, field836)
        newline(pp)
        field837 = unwrapped_fields835[2]
        pretty_abstraction(pp, field837)
        field838 = unwrapped_fields835[3]
        if !isnothing(field838)
            newline(pp)
            opt_val839 = field838
            pretty_attrs(pp, opt_val839)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat845 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat845)
        write(pp, flat845)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1466 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1465 = _t1466
        else
            _t1465 = nothing
        end
        deconstruct_result843 = _t1465
        if !isnothing(deconstruct_result843)
            unwrapped844 = deconstruct_result843
            write(pp, ":")
            write(pp, unwrapped844)
        else
            _dollar_dollar = msg
            _t1467 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result841 = _t1467
            if !isnothing(deconstruct_result841)
                unwrapped842 = deconstruct_result841
                write(pp, format_uint128(pp, unwrapped842))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat850 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat850)
        write(pp, flat850)
        return nothing
    else
        _dollar_dollar = msg
        _t1468 = deconstruct_bindings(pp, _dollar_dollar)
        fields846 = (_t1468, _dollar_dollar.value,)
        unwrapped_fields847 = fields846
        write(pp, "(")
        indent!(pp)
        field848 = unwrapped_fields847[1]
        pretty_bindings(pp, field848)
        newline(pp)
        field849 = unwrapped_fields847[2]
        pretty_formula(pp, field849)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat858 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat858)
        write(pp, flat858)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1469 = _dollar_dollar[2]
        else
            _t1469 = nothing
        end
        fields851 = (_dollar_dollar[1], _t1469,)
        unwrapped_fields852 = fields851
        write(pp, "[")
        indent!(pp)
        field853 = unwrapped_fields852[1]
        for (i1470, elem854) in enumerate(field853)
            i855 = i1470 - 1
            if (i855 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem854)
        end
        field856 = unwrapped_fields852[2]
        if !isnothing(field856)
            newline(pp)
            opt_val857 = field856
            pretty_value_bindings(pp, opt_val857)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat863 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat863)
        write(pp, flat863)
        return nothing
    else
        _dollar_dollar = msg
        fields859 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields860 = fields859
        field861 = unwrapped_fields860[1]
        write(pp, field861)
        write(pp, "::")
        field862 = unwrapped_fields860[2]
        pretty_type(pp, field862)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat892 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat892)
        write(pp, flat892)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1471 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1471 = nothing
        end
        deconstruct_result890 = _t1471
        if !isnothing(deconstruct_result890)
            unwrapped891 = deconstruct_result890
            pretty_unspecified_type(pp, unwrapped891)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1472 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1472 = nothing
            end
            deconstruct_result888 = _t1472
            if !isnothing(deconstruct_result888)
                unwrapped889 = deconstruct_result888
                pretty_string_type(pp, unwrapped889)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1473 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1473 = nothing
                end
                deconstruct_result886 = _t1473
                if !isnothing(deconstruct_result886)
                    unwrapped887 = deconstruct_result886
                    pretty_int_type(pp, unwrapped887)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1474 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1474 = nothing
                    end
                    deconstruct_result884 = _t1474
                    if !isnothing(deconstruct_result884)
                        unwrapped885 = deconstruct_result884
                        pretty_float_type(pp, unwrapped885)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1475 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1475 = nothing
                        end
                        deconstruct_result882 = _t1475
                        if !isnothing(deconstruct_result882)
                            unwrapped883 = deconstruct_result882
                            pretty_uint128_type(pp, unwrapped883)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1476 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1476 = nothing
                            end
                            deconstruct_result880 = _t1476
                            if !isnothing(deconstruct_result880)
                                unwrapped881 = deconstruct_result880
                                pretty_int128_type(pp, unwrapped881)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1477 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1477 = nothing
                                end
                                deconstruct_result878 = _t1477
                                if !isnothing(deconstruct_result878)
                                    unwrapped879 = deconstruct_result878
                                    pretty_date_type(pp, unwrapped879)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1478 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1478 = nothing
                                    end
                                    deconstruct_result876 = _t1478
                                    if !isnothing(deconstruct_result876)
                                        unwrapped877 = deconstruct_result876
                                        pretty_datetime_type(pp, unwrapped877)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1479 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1479 = nothing
                                        end
                                        deconstruct_result874 = _t1479
                                        if !isnothing(deconstruct_result874)
                                            unwrapped875 = deconstruct_result874
                                            pretty_missing_type(pp, unwrapped875)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1480 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1480 = nothing
                                            end
                                            deconstruct_result872 = _t1480
                                            if !isnothing(deconstruct_result872)
                                                unwrapped873 = deconstruct_result872
                                                pretty_decimal_type(pp, unwrapped873)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1481 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1481 = nothing
                                                end
                                                deconstruct_result870 = _t1481
                                                if !isnothing(deconstruct_result870)
                                                    unwrapped871 = deconstruct_result870
                                                    pretty_boolean_type(pp, unwrapped871)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1482 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1482 = nothing
                                                    end
                                                    deconstruct_result868 = _t1482
                                                    if !isnothing(deconstruct_result868)
                                                        unwrapped869 = deconstruct_result868
                                                        pretty_int32_type(pp, unwrapped869)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1483 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1483 = nothing
                                                        end
                                                        deconstruct_result866 = _t1483
                                                        if !isnothing(deconstruct_result866)
                                                            unwrapped867 = deconstruct_result866
                                                            pretty_float32_type(pp, unwrapped867)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1484 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1484 = nothing
                                                            end
                                                            deconstruct_result864 = _t1484
                                                            if !isnothing(deconstruct_result864)
                                                                unwrapped865 = deconstruct_result864
                                                                pretty_uint32_type(pp, unwrapped865)
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
    fields893 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields894 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields895 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields896 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields897 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields898 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields899 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields900 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields901 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat906 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        _dollar_dollar = msg
        fields902 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields903 = fields902
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field904 = unwrapped_fields903[1]
        write(pp, format_int(pp, field904))
        newline(pp)
        field905 = unwrapped_fields903[2]
        write(pp, format_int(pp, field905))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields907 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields908 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields909 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields910 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat914 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat914)
        write(pp, flat914)
        return nothing
    else
        fields911 = msg
        write(pp, "|")
        if !isempty(fields911)
            write(pp, " ")
            for (i1485, elem912) in enumerate(fields911)
                i913 = i1485 - 1
                if (i913 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem912)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat941 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat941)
        write(pp, flat941)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1486 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1486 = nothing
        end
        deconstruct_result939 = _t1486
        if !isnothing(deconstruct_result939)
            unwrapped940 = deconstruct_result939
            pretty_true(pp, unwrapped940)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1487 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1487 = nothing
            end
            deconstruct_result937 = _t1487
            if !isnothing(deconstruct_result937)
                unwrapped938 = deconstruct_result937
                pretty_false(pp, unwrapped938)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1488 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1488 = nothing
                end
                deconstruct_result935 = _t1488
                if !isnothing(deconstruct_result935)
                    unwrapped936 = deconstruct_result935
                    pretty_exists(pp, unwrapped936)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1489 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1489 = nothing
                    end
                    deconstruct_result933 = _t1489
                    if !isnothing(deconstruct_result933)
                        unwrapped934 = deconstruct_result933
                        pretty_reduce(pp, unwrapped934)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1490 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1490 = nothing
                        end
                        deconstruct_result931 = _t1490
                        if !isnothing(deconstruct_result931)
                            unwrapped932 = deconstruct_result931
                            pretty_conjunction(pp, unwrapped932)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1491 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1491 = nothing
                            end
                            deconstruct_result929 = _t1491
                            if !isnothing(deconstruct_result929)
                                unwrapped930 = deconstruct_result929
                                pretty_disjunction(pp, unwrapped930)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1492 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1492 = nothing
                                end
                                deconstruct_result927 = _t1492
                                if !isnothing(deconstruct_result927)
                                    unwrapped928 = deconstruct_result927
                                    pretty_not(pp, unwrapped928)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1493 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1493 = nothing
                                    end
                                    deconstruct_result925 = _t1493
                                    if !isnothing(deconstruct_result925)
                                        unwrapped926 = deconstruct_result925
                                        pretty_ffi(pp, unwrapped926)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1494 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1494 = nothing
                                        end
                                        deconstruct_result923 = _t1494
                                        if !isnothing(deconstruct_result923)
                                            unwrapped924 = deconstruct_result923
                                            pretty_atom(pp, unwrapped924)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1495 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1495 = nothing
                                            end
                                            deconstruct_result921 = _t1495
                                            if !isnothing(deconstruct_result921)
                                                unwrapped922 = deconstruct_result921
                                                pretty_pragma(pp, unwrapped922)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1496 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1496 = nothing
                                                end
                                                deconstruct_result919 = _t1496
                                                if !isnothing(deconstruct_result919)
                                                    unwrapped920 = deconstruct_result919
                                                    pretty_primitive(pp, unwrapped920)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1497 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1497 = nothing
                                                    end
                                                    deconstruct_result917 = _t1497
                                                    if !isnothing(deconstruct_result917)
                                                        unwrapped918 = deconstruct_result917
                                                        pretty_rel_atom(pp, unwrapped918)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1498 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1498 = nothing
                                                        end
                                                        deconstruct_result915 = _t1498
                                                        if !isnothing(deconstruct_result915)
                                                            unwrapped916 = deconstruct_result915
                                                            pretty_cast(pp, unwrapped916)
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
    fields942 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields943 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat948 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat948)
        write(pp, flat948)
        return nothing
    else
        _dollar_dollar = msg
        _t1499 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields944 = (_t1499, _dollar_dollar.body.value,)
        unwrapped_fields945 = fields944
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field946 = unwrapped_fields945[1]
        pretty_bindings(pp, field946)
        newline(pp)
        field947 = unwrapped_fields945[2]
        pretty_formula(pp, field947)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat954 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat954)
        write(pp, flat954)
        return nothing
    else
        _dollar_dollar = msg
        fields949 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields950 = fields949
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field951 = unwrapped_fields950[1]
        pretty_abstraction(pp, field951)
        newline(pp)
        field952 = unwrapped_fields950[2]
        pretty_abstraction(pp, field952)
        newline(pp)
        field953 = unwrapped_fields950[3]
        pretty_terms(pp, field953)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat958 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat958)
        write(pp, flat958)
        return nothing
    else
        fields955 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields955)
            newline(pp)
            for (i1500, elem956) in enumerate(fields955)
                i957 = i1500 - 1
                if (i957 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem956)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat963 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat963)
        write(pp, flat963)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1501 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1501 = nothing
        end
        deconstruct_result961 = _t1501
        if !isnothing(deconstruct_result961)
            unwrapped962 = deconstruct_result961
            pretty_var(pp, unwrapped962)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1502 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1502 = nothing
            end
            deconstruct_result959 = _t1502
            if !isnothing(deconstruct_result959)
                unwrapped960 = deconstruct_result959
                pretty_constant(pp, unwrapped960)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat966 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat966)
        write(pp, flat966)
        return nothing
    else
        _dollar_dollar = msg
        fields964 = _dollar_dollar.name
        unwrapped_fields965 = fields964
        write(pp, unwrapped_fields965)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat968 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat968)
        write(pp, flat968)
        return nothing
    else
        fields967 = msg
        pretty_value(pp, fields967)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat973 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat973)
        write(pp, flat973)
        return nothing
    else
        _dollar_dollar = msg
        fields969 = _dollar_dollar.args
        unwrapped_fields970 = fields969
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields970)
            newline(pp)
            for (i1503, elem971) in enumerate(unwrapped_fields970)
                i972 = i1503 - 1
                if (i972 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem971)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat978 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat978)
        write(pp, flat978)
        return nothing
    else
        _dollar_dollar = msg
        fields974 = _dollar_dollar.args
        unwrapped_fields975 = fields974
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields975)
            newline(pp)
            for (i1504, elem976) in enumerate(unwrapped_fields975)
                i977 = i1504 - 1
                if (i977 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem976)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat981 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat981)
        write(pp, flat981)
        return nothing
    else
        _dollar_dollar = msg
        fields979 = _dollar_dollar.arg
        unwrapped_fields980 = fields979
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields980)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat987 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat987)
        write(pp, flat987)
        return nothing
    else
        _dollar_dollar = msg
        fields982 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields983 = fields982
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field984 = unwrapped_fields983[1]
        pretty_name(pp, field984)
        newline(pp)
        field985 = unwrapped_fields983[2]
        pretty_ffi_args(pp, field985)
        newline(pp)
        field986 = unwrapped_fields983[3]
        pretty_terms(pp, field986)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat989 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat989)
        write(pp, flat989)
        return nothing
    else
        fields988 = msg
        write(pp, ":")
        write(pp, fields988)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat993 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat993)
        write(pp, flat993)
        return nothing
    else
        fields990 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields990)
            newline(pp)
            for (i1505, elem991) in enumerate(fields990)
                i992 = i1505 - 1
                if (i992 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem991)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1000 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1000)
        write(pp, flat1000)
        return nothing
    else
        _dollar_dollar = msg
        fields994 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields995 = fields994
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field996 = unwrapped_fields995[1]
        pretty_relation_id(pp, field996)
        field997 = unwrapped_fields995[2]
        if !isempty(field997)
            newline(pp)
            for (i1506, elem998) in enumerate(field997)
                i999 = i1506 - 1
                if (i999 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem998)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1007 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1007)
        write(pp, flat1007)
        return nothing
    else
        _dollar_dollar = msg
        fields1001 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1002 = fields1001
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1003 = unwrapped_fields1002[1]
        pretty_name(pp, field1003)
        field1004 = unwrapped_fields1002[2]
        if !isempty(field1004)
            newline(pp)
            for (i1507, elem1005) in enumerate(field1004)
                i1006 = i1507 - 1
                if (i1006 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1005)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1023 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1023)
        write(pp, flat1023)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1508 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1508 = nothing
        end
        guard_result1022 = _t1508
        if !isnothing(guard_result1022)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1509 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1509 = nothing
            end
            guard_result1021 = _t1509
            if !isnothing(guard_result1021)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1510 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1510 = nothing
                end
                guard_result1020 = _t1510
                if !isnothing(guard_result1020)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1511 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1511 = nothing
                    end
                    guard_result1019 = _t1511
                    if !isnothing(guard_result1019)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1512 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1512 = nothing
                        end
                        guard_result1018 = _t1512
                        if !isnothing(guard_result1018)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1513 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1513 = nothing
                            end
                            guard_result1017 = _t1513
                            if !isnothing(guard_result1017)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1514 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1514 = nothing
                                end
                                guard_result1016 = _t1514
                                if !isnothing(guard_result1016)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1515 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1515 = nothing
                                    end
                                    guard_result1015 = _t1515
                                    if !isnothing(guard_result1015)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1516 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1516 = nothing
                                        end
                                        guard_result1014 = _t1516
                                        if !isnothing(guard_result1014)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1008 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1009 = fields1008
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1010 = unwrapped_fields1009[1]
                                            pretty_name(pp, field1010)
                                            field1011 = unwrapped_fields1009[2]
                                            if !isempty(field1011)
                                                newline(pp)
                                                for (i1517, elem1012) in enumerate(field1011)
                                                    i1013 = i1517 - 1
                                                    if (i1013 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1012)
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
    flat1028 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1028)
        write(pp, flat1028)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1518 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1518 = nothing
        end
        fields1024 = _t1518
        unwrapped_fields1025 = fields1024
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1026 = unwrapped_fields1025[1]
        pretty_term(pp, field1026)
        newline(pp)
        field1027 = unwrapped_fields1025[2]
        pretty_term(pp, field1027)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1033 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1033)
        write(pp, flat1033)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1519 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1519 = nothing
        end
        fields1029 = _t1519
        unwrapped_fields1030 = fields1029
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1031 = unwrapped_fields1030[1]
        pretty_term(pp, field1031)
        newline(pp)
        field1032 = unwrapped_fields1030[2]
        pretty_term(pp, field1032)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1038 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1038)
        write(pp, flat1038)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1520 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1520 = nothing
        end
        fields1034 = _t1520
        unwrapped_fields1035 = fields1034
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1036 = unwrapped_fields1035[1]
        pretty_term(pp, field1036)
        newline(pp)
        field1037 = unwrapped_fields1035[2]
        pretty_term(pp, field1037)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1043 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1043)
        write(pp, flat1043)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1521 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1521 = nothing
        end
        fields1039 = _t1521
        unwrapped_fields1040 = fields1039
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1041 = unwrapped_fields1040[1]
        pretty_term(pp, field1041)
        newline(pp)
        field1042 = unwrapped_fields1040[2]
        pretty_term(pp, field1042)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1048 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1048)
        write(pp, flat1048)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1522 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1522 = nothing
        end
        fields1044 = _t1522
        unwrapped_fields1045 = fields1044
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1046 = unwrapped_fields1045[1]
        pretty_term(pp, field1046)
        newline(pp)
        field1047 = unwrapped_fields1045[2]
        pretty_term(pp, field1047)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1054 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1054)
        write(pp, flat1054)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1523 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1523 = nothing
        end
        fields1049 = _t1523
        unwrapped_fields1050 = fields1049
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1051 = unwrapped_fields1050[1]
        pretty_term(pp, field1051)
        newline(pp)
        field1052 = unwrapped_fields1050[2]
        pretty_term(pp, field1052)
        newline(pp)
        field1053 = unwrapped_fields1050[3]
        pretty_term(pp, field1053)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1060 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1060)
        write(pp, flat1060)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1524 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1524 = nothing
        end
        fields1055 = _t1524
        unwrapped_fields1056 = fields1055
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1057 = unwrapped_fields1056[1]
        pretty_term(pp, field1057)
        newline(pp)
        field1058 = unwrapped_fields1056[2]
        pretty_term(pp, field1058)
        newline(pp)
        field1059 = unwrapped_fields1056[3]
        pretty_term(pp, field1059)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1066 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1066)
        write(pp, flat1066)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1525 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1525 = nothing
        end
        fields1061 = _t1525
        unwrapped_fields1062 = fields1061
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1063 = unwrapped_fields1062[1]
        pretty_term(pp, field1063)
        newline(pp)
        field1064 = unwrapped_fields1062[2]
        pretty_term(pp, field1064)
        newline(pp)
        field1065 = unwrapped_fields1062[3]
        pretty_term(pp, field1065)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1072 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1072)
        write(pp, flat1072)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1526 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1526 = nothing
        end
        fields1067 = _t1526
        unwrapped_fields1068 = fields1067
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1069 = unwrapped_fields1068[1]
        pretty_term(pp, field1069)
        newline(pp)
        field1070 = unwrapped_fields1068[2]
        pretty_term(pp, field1070)
        newline(pp)
        field1071 = unwrapped_fields1068[3]
        pretty_term(pp, field1071)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1077 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1077)
        write(pp, flat1077)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1527 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1527 = nothing
        end
        deconstruct_result1075 = _t1527
        if !isnothing(deconstruct_result1075)
            unwrapped1076 = deconstruct_result1075
            pretty_specialized_value(pp, unwrapped1076)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1528 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1528 = nothing
            end
            deconstruct_result1073 = _t1528
            if !isnothing(deconstruct_result1073)
                unwrapped1074 = deconstruct_result1073
                pretty_term(pp, unwrapped1074)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1079 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1079)
        write(pp, flat1079)
        return nothing
    else
        fields1078 = msg
        write(pp, "#")
        pretty_value(pp, fields1078)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1086 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1086)
        write(pp, flat1086)
        return nothing
    else
        _dollar_dollar = msg
        fields1080 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1081 = fields1080
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1082 = unwrapped_fields1081[1]
        pretty_name(pp, field1082)
        field1083 = unwrapped_fields1081[2]
        if !isempty(field1083)
            newline(pp)
            for (i1529, elem1084) in enumerate(field1083)
                i1085 = i1529 - 1
                if (i1085 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1084)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1091 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1091)
        write(pp, flat1091)
        return nothing
    else
        _dollar_dollar = msg
        fields1087 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1088 = fields1087
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1089 = unwrapped_fields1088[1]
        pretty_term(pp, field1089)
        newline(pp)
        field1090 = unwrapped_fields1088[2]
        pretty_term(pp, field1090)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1095 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1095)
        write(pp, flat1095)
        return nothing
    else
        fields1092 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1092)
            newline(pp)
            for (i1530, elem1093) in enumerate(fields1092)
                i1094 = i1530 - 1
                if (i1094 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1093)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1102 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1102)
        write(pp, flat1102)
        return nothing
    else
        _dollar_dollar = msg
        fields1096 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1097 = fields1096
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1098 = unwrapped_fields1097[1]
        pretty_name(pp, field1098)
        field1099 = unwrapped_fields1097[2]
        if !isempty(field1099)
            newline(pp)
            for (i1531, elem1100) in enumerate(field1099)
                i1101 = i1531 - 1
                if (i1101 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem1100)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1109 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1109)
        write(pp, flat1109)
        return nothing
    else
        _dollar_dollar = msg
        fields1103 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1104 = fields1103
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1105 = unwrapped_fields1104[1]
        if !isempty(field1105)
            newline(pp)
            for (i1532, elem1106) in enumerate(field1105)
                i1107 = i1532 - 1
                if (i1107 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1106)
            end
        end
        newline(pp)
        field1108 = unwrapped_fields1104[2]
        pretty_script(pp, field1108)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1114 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1114)
        write(pp, flat1114)
        return nothing
    else
        _dollar_dollar = msg
        fields1110 = _dollar_dollar.constructs
        unwrapped_fields1111 = fields1110
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1111)
            newline(pp)
            for (i1533, elem1112) in enumerate(unwrapped_fields1111)
                i1113 = i1533 - 1
                if (i1113 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1112)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1119 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1119)
        write(pp, flat1119)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1534 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1534 = nothing
        end
        deconstruct_result1117 = _t1534
        if !isnothing(deconstruct_result1117)
            unwrapped1118 = deconstruct_result1117
            pretty_loop(pp, unwrapped1118)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1535 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1535 = nothing
            end
            deconstruct_result1115 = _t1535
            if !isnothing(deconstruct_result1115)
                unwrapped1116 = deconstruct_result1115
                pretty_instruction(pp, unwrapped1116)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1124 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1124)
        write(pp, flat1124)
        return nothing
    else
        _dollar_dollar = msg
        fields1120 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1121 = fields1120
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1122 = unwrapped_fields1121[1]
        pretty_init(pp, field1122)
        newline(pp)
        field1123 = unwrapped_fields1121[2]
        pretty_script(pp, field1123)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1128 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1128)
        write(pp, flat1128)
        return nothing
    else
        fields1125 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1125)
            newline(pp)
            for (i1536, elem1126) in enumerate(fields1125)
                i1127 = i1536 - 1
                if (i1127 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1126)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1139 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1139)
        write(pp, flat1139)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1537 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1537 = nothing
        end
        deconstruct_result1137 = _t1537
        if !isnothing(deconstruct_result1137)
            unwrapped1138 = deconstruct_result1137
            pretty_assign(pp, unwrapped1138)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1538 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1538 = nothing
            end
            deconstruct_result1135 = _t1538
            if !isnothing(deconstruct_result1135)
                unwrapped1136 = deconstruct_result1135
                pretty_upsert(pp, unwrapped1136)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1539 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1539 = nothing
                end
                deconstruct_result1133 = _t1539
                if !isnothing(deconstruct_result1133)
                    unwrapped1134 = deconstruct_result1133
                    pretty_break(pp, unwrapped1134)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1540 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1540 = nothing
                    end
                    deconstruct_result1131 = _t1540
                    if !isnothing(deconstruct_result1131)
                        unwrapped1132 = deconstruct_result1131
                        pretty_monoid_def(pp, unwrapped1132)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1541 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1541 = nothing
                        end
                        deconstruct_result1129 = _t1541
                        if !isnothing(deconstruct_result1129)
                            unwrapped1130 = deconstruct_result1129
                            pretty_monus_def(pp, unwrapped1130)
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
    flat1146 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1146)
        write(pp, flat1146)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1542 = _dollar_dollar.attrs
        else
            _t1542 = nothing
        end
        fields1140 = (_dollar_dollar.name, _dollar_dollar.body, _t1542,)
        unwrapped_fields1141 = fields1140
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1142 = unwrapped_fields1141[1]
        pretty_relation_id(pp, field1142)
        newline(pp)
        field1143 = unwrapped_fields1141[2]
        pretty_abstraction(pp, field1143)
        field1144 = unwrapped_fields1141[3]
        if !isnothing(field1144)
            newline(pp)
            opt_val1145 = field1144
            pretty_attrs(pp, opt_val1145)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1153 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1153)
        write(pp, flat1153)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1543 = _dollar_dollar.attrs
        else
            _t1543 = nothing
        end
        fields1147 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1543,)
        unwrapped_fields1148 = fields1147
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1149 = unwrapped_fields1148[1]
        pretty_relation_id(pp, field1149)
        newline(pp)
        field1150 = unwrapped_fields1148[2]
        pretty_abstraction_with_arity(pp, field1150)
        field1151 = unwrapped_fields1148[3]
        if !isnothing(field1151)
            newline(pp)
            opt_val1152 = field1151
            pretty_attrs(pp, opt_val1152)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1158 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1158)
        write(pp, flat1158)
        return nothing
    else
        _dollar_dollar = msg
        _t1544 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1154 = (_t1544, _dollar_dollar[1].value,)
        unwrapped_fields1155 = fields1154
        write(pp, "(")
        indent!(pp)
        field1156 = unwrapped_fields1155[1]
        pretty_bindings(pp, field1156)
        newline(pp)
        field1157 = unwrapped_fields1155[2]
        pretty_formula(pp, field1157)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1165 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1165)
        write(pp, flat1165)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1545 = _dollar_dollar.attrs
        else
            _t1545 = nothing
        end
        fields1159 = (_dollar_dollar.name, _dollar_dollar.body, _t1545,)
        unwrapped_fields1160 = fields1159
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1161 = unwrapped_fields1160[1]
        pretty_relation_id(pp, field1161)
        newline(pp)
        field1162 = unwrapped_fields1160[2]
        pretty_abstraction(pp, field1162)
        field1163 = unwrapped_fields1160[3]
        if !isnothing(field1163)
            newline(pp)
            opt_val1164 = field1163
            pretty_attrs(pp, opt_val1164)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1173 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1173)
        write(pp, flat1173)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1546 = _dollar_dollar.attrs
        else
            _t1546 = nothing
        end
        fields1166 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1546,)
        unwrapped_fields1167 = fields1166
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1168 = unwrapped_fields1167[1]
        pretty_monoid(pp, field1168)
        newline(pp)
        field1169 = unwrapped_fields1167[2]
        pretty_relation_id(pp, field1169)
        newline(pp)
        field1170 = unwrapped_fields1167[3]
        pretty_abstraction_with_arity(pp, field1170)
        field1171 = unwrapped_fields1167[4]
        if !isnothing(field1171)
            newline(pp)
            opt_val1172 = field1171
            pretty_attrs(pp, opt_val1172)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1182 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1182)
        write(pp, flat1182)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1547 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1547 = nothing
        end
        deconstruct_result1180 = _t1547
        if !isnothing(deconstruct_result1180)
            unwrapped1181 = deconstruct_result1180
            pretty_or_monoid(pp, unwrapped1181)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1548 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1548 = nothing
            end
            deconstruct_result1178 = _t1548
            if !isnothing(deconstruct_result1178)
                unwrapped1179 = deconstruct_result1178
                pretty_min_monoid(pp, unwrapped1179)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1549 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1549 = nothing
                end
                deconstruct_result1176 = _t1549
                if !isnothing(deconstruct_result1176)
                    unwrapped1177 = deconstruct_result1176
                    pretty_max_monoid(pp, unwrapped1177)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1550 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1550 = nothing
                    end
                    deconstruct_result1174 = _t1550
                    if !isnothing(deconstruct_result1174)
                        unwrapped1175 = deconstruct_result1174
                        pretty_sum_monoid(pp, unwrapped1175)
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
    fields1183 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1186 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1186)
        write(pp, flat1186)
        return nothing
    else
        _dollar_dollar = msg
        fields1184 = _dollar_dollar.var"#type"
        unwrapped_fields1185 = fields1184
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1185)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1189 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1189)
        write(pp, flat1189)
        return nothing
    else
        _dollar_dollar = msg
        fields1187 = _dollar_dollar.var"#type"
        unwrapped_fields1188 = fields1187
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1188)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1192 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1192)
        write(pp, flat1192)
        return nothing
    else
        _dollar_dollar = msg
        fields1190 = _dollar_dollar.var"#type"
        unwrapped_fields1191 = fields1190
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1191)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1200 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1200)
        write(pp, flat1200)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1551 = _dollar_dollar.attrs
        else
            _t1551 = nothing
        end
        fields1193 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1551,)
        unwrapped_fields1194 = fields1193
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1195 = unwrapped_fields1194[1]
        pretty_monoid(pp, field1195)
        newline(pp)
        field1196 = unwrapped_fields1194[2]
        pretty_relation_id(pp, field1196)
        newline(pp)
        field1197 = unwrapped_fields1194[3]
        pretty_abstraction_with_arity(pp, field1197)
        field1198 = unwrapped_fields1194[4]
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

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1207 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1207)
        write(pp, flat1207)
        return nothing
    else
        _dollar_dollar = msg
        fields1201 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1202 = fields1201
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1203 = unwrapped_fields1202[1]
        pretty_relation_id(pp, field1203)
        newline(pp)
        field1204 = unwrapped_fields1202[2]
        pretty_abstraction(pp, field1204)
        newline(pp)
        field1205 = unwrapped_fields1202[3]
        pretty_functional_dependency_keys(pp, field1205)
        newline(pp)
        field1206 = unwrapped_fields1202[4]
        pretty_functional_dependency_values(pp, field1206)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1211 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1211)
        write(pp, flat1211)
        return nothing
    else
        fields1208 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1208)
            newline(pp)
            for (i1552, elem1209) in enumerate(fields1208)
                i1210 = i1552 - 1
                if (i1210 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1209)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1215 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        fields1212 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1212)
            newline(pp)
            for (i1553, elem1213) in enumerate(fields1212)
                i1214 = i1553 - 1
                if (i1214 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1213)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1224 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1224)
        write(pp, flat1224)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1554 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1554 = nothing
        end
        deconstruct_result1222 = _t1554
        if !isnothing(deconstruct_result1222)
            unwrapped1223 = deconstruct_result1222
            pretty_edb(pp, unwrapped1223)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1555 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1555 = nothing
            end
            deconstruct_result1220 = _t1555
            if !isnothing(deconstruct_result1220)
                unwrapped1221 = deconstruct_result1220
                pretty_betree_relation(pp, unwrapped1221)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1556 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1556 = nothing
                end
                deconstruct_result1218 = _t1556
                if !isnothing(deconstruct_result1218)
                    unwrapped1219 = deconstruct_result1218
                    pretty_csv_data(pp, unwrapped1219)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1557 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1557 = nothing
                    end
                    deconstruct_result1216 = _t1557
                    if !isnothing(deconstruct_result1216)
                        unwrapped1217 = deconstruct_result1216
                        pretty_iceberg_data(pp, unwrapped1217)
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
    flat1230 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1230)
        write(pp, flat1230)
        return nothing
    else
        _dollar_dollar = msg
        fields1225 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1226 = fields1225
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1227 = unwrapped_fields1226[1]
        pretty_relation_id(pp, field1227)
        newline(pp)
        field1228 = unwrapped_fields1226[2]
        pretty_edb_path(pp, field1228)
        newline(pp)
        field1229 = unwrapped_fields1226[3]
        pretty_edb_types(pp, field1229)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1234 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1234)
        write(pp, flat1234)
        return nothing
    else
        fields1231 = msg
        write(pp, "[")
        indent!(pp)
        for (i1558, elem1232) in enumerate(fields1231)
            i1233 = i1558 - 1
            if (i1233 > 0)
                newline(pp)
            end
            write(pp, format_string(pp, elem1232))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1238 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1238)
        write(pp, flat1238)
        return nothing
    else
        fields1235 = msg
        write(pp, "[")
        indent!(pp)
        for (i1559, elem1236) in enumerate(fields1235)
            i1237 = i1559 - 1
            if (i1237 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1236)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1243 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1243)
        write(pp, flat1243)
        return nothing
    else
        _dollar_dollar = msg
        fields1239 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1240 = fields1239
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1241 = unwrapped_fields1240[1]
        pretty_relation_id(pp, field1241)
        newline(pp)
        field1242 = unwrapped_fields1240[2]
        pretty_betree_info(pp, field1242)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1249 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1249)
        write(pp, flat1249)
        return nothing
    else
        _dollar_dollar = msg
        _t1560 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1244 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1560,)
        unwrapped_fields1245 = fields1244
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1246 = unwrapped_fields1245[1]
        pretty_betree_info_key_types(pp, field1246)
        newline(pp)
        field1247 = unwrapped_fields1245[2]
        pretty_betree_info_value_types(pp, field1247)
        newline(pp)
        field1248 = unwrapped_fields1245[3]
        pretty_config_dict(pp, field1248)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1253 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        fields1250 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1250)
            newline(pp)
            for (i1561, elem1251) in enumerate(fields1250)
                i1252 = i1561 - 1
                if (i1252 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1251)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1257 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1257)
        write(pp, flat1257)
        return nothing
    else
        fields1254 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1254)
            newline(pp)
            for (i1562, elem1255) in enumerate(fields1254)
                i1256 = i1562 - 1
                if (i1256 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1255)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1264 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1264)
        write(pp, flat1264)
        return nothing
    else
        _dollar_dollar = msg
        fields1258 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1259 = fields1258
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1260 = unwrapped_fields1259[1]
        pretty_csvlocator(pp, field1260)
        newline(pp)
        field1261 = unwrapped_fields1259[2]
        pretty_csv_config(pp, field1261)
        newline(pp)
        field1262 = unwrapped_fields1259[3]
        pretty_gnf_columns(pp, field1262)
        newline(pp)
        field1263 = unwrapped_fields1259[4]
        pretty_csv_asof(pp, field1263)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1271 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1271)
        write(pp, flat1271)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1563 = _dollar_dollar.paths
        else
            _t1563 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1564 = String(copy(_dollar_dollar.inline_data))
        else
            _t1564 = nothing
        end
        fields1265 = (_t1563, _t1564,)
        unwrapped_fields1266 = fields1265
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1267 = unwrapped_fields1266[1]
        if !isnothing(field1267)
            newline(pp)
            opt_val1268 = field1267
            pretty_csv_locator_paths(pp, opt_val1268)
        end
        field1269 = unwrapped_fields1266[2]
        if !isnothing(field1269)
            newline(pp)
            opt_val1270 = field1269
            pretty_csv_locator_inline_data(pp, opt_val1270)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1275 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1275)
        write(pp, flat1275)
        return nothing
    else
        fields1272 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1272)
            newline(pp)
            for (i1565, elem1273) in enumerate(fields1272)
                i1274 = i1565 - 1
                if (i1274 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1273))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1277 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1277)
        write(pp, flat1277)
        return nothing
    else
        fields1276 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1276))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1280 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1280)
        write(pp, flat1280)
        return nothing
    else
        _dollar_dollar = msg
        _t1566 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1278 = _t1566
        unwrapped_fields1279 = fields1278
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1279)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1284 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1284)
        write(pp, flat1284)
        return nothing
    else
        fields1281 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1281)
            newline(pp)
            for (i1567, elem1282) in enumerate(fields1281)
                i1283 = i1567 - 1
                if (i1283 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1282)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1293 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1293)
        write(pp, flat1293)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1568 = _dollar_dollar.target_id
        else
            _t1568 = nothing
        end
        fields1285 = (_dollar_dollar.column_path, _t1568, _dollar_dollar.types,)
        unwrapped_fields1286 = fields1285
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1287 = unwrapped_fields1286[1]
        pretty_gnf_column_path(pp, field1287)
        field1288 = unwrapped_fields1286[2]
        if !isnothing(field1288)
            newline(pp)
            opt_val1289 = field1288
            pretty_relation_id(pp, opt_val1289)
        end
        newline(pp)
        write(pp, "[")
        field1290 = unwrapped_fields1286[3]
        for (i1569, elem1291) in enumerate(field1290)
            i1292 = i1569 - 1
            if (i1292 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1291)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1300 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1300)
        write(pp, flat1300)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1570 = _dollar_dollar[1]
        else
            _t1570 = nothing
        end
        deconstruct_result1298 = _t1570
        if !isnothing(deconstruct_result1298)
            unwrapped1299 = deconstruct_result1298
            write(pp, format_string(pp, unwrapped1299))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1571 = _dollar_dollar
            else
                _t1571 = nothing
            end
            deconstruct_result1294 = _t1571
            if !isnothing(deconstruct_result1294)
                unwrapped1295 = deconstruct_result1294
                write(pp, "[")
                indent!(pp)
                for (i1572, elem1296) in enumerate(unwrapped1295)
                    i1297 = i1572 - 1
                    if (i1297 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(pp, elem1296))
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
    flat1302 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1302)
        write(pp, flat1302)
        return nothing
    else
        fields1301 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1301))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1310 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1310)
        write(pp, flat1310)
        return nothing
    else
        _dollar_dollar = msg
        fields1303 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.to_snapshot,)
        unwrapped_fields1304 = fields1303
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1305 = unwrapped_fields1304[1]
        pretty_iceberg_locator(pp, field1305)
        newline(pp)
        field1306 = unwrapped_fields1304[2]
        pretty_iceberg_config(pp, field1306)
        newline(pp)
        field1307 = unwrapped_fields1304[3]
        pretty_gnf_columns(pp, field1307)
        field1308 = unwrapped_fields1304[4]
        if !isnothing(field1308)
            newline(pp)
            opt_val1309 = field1308
            pretty_iceberg_to_snapshot(pp, opt_val1309)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1316 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1316)
        write(pp, flat1316)
        return nothing
    else
        _dollar_dollar = msg
        fields1311 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1312 = fields1311
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1313 = unwrapped_fields1312[1]
        write(pp, format_string(pp, field1313))
        newline(pp)
        field1314 = unwrapped_fields1312[2]
        pretty_iceberg_locator_namespace(pp, field1314)
        newline(pp)
        field1315 = unwrapped_fields1312[3]
        write(pp, format_string(pp, field1315))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1320 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1320)
        write(pp, flat1320)
        return nothing
    else
        fields1317 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1317)
            newline(pp)
            for (i1573, elem1318) in enumerate(fields1317)
                i1319 = i1573 - 1
                if (i1319 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1318))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_config(pp::PrettyPrinter, msg::Proto.IcebergConfig)
    flat1330 = try_flat(pp, msg, pretty_iceberg_config)
    if !isnothing(flat1330)
        write(pp, flat1330)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.scope != ""
            _t1574 = _dollar_dollar.scope
        else
            _t1574 = nothing
        end
        if !isempty(sort([(k, v) for (k, v) in _dollar_dollar.properties]))
            _t1575 = sort([(k, v) for (k, v) in _dollar_dollar.properties])
        else
            _t1575 = nothing
        end
        fields1321 = (_dollar_dollar.catalog_uri, _t1574, _t1575, nothing,)
        unwrapped_fields1322 = fields1321
        write(pp, "(iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1323 = unwrapped_fields1322[1]
        write(pp, format_string(pp, field1323))
        field1324 = unwrapped_fields1322[2]
        if !isnothing(field1324)
            newline(pp)
            opt_val1325 = field1324
            pretty_iceberg_config_scope(pp, opt_val1325)
        end
        field1326 = unwrapped_fields1322[3]
        if !isnothing(field1326)
            newline(pp)
            opt_val1327 = field1326
            pretty_iceberg_config_properties(pp, opt_val1327)
        end
        field1328 = unwrapped_fields1322[4]
        if !isnothing(field1328)
            newline(pp)
            opt_val1329 = field1328
            pretty_iceberg_config_credentials(pp, opt_val1329)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_config_scope(pp::PrettyPrinter, msg::String)
    flat1332 = try_flat(pp, msg, pretty_iceberg_config_scope)
    if !isnothing(flat1332)
        write(pp, flat1332)
        return nothing
    else
        fields1331 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1331))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_config_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1336 = try_flat(pp, msg, pretty_iceberg_config_properties)
    if !isnothing(flat1336)
        write(pp, flat1336)
        return nothing
    else
        fields1333 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1333)
            newline(pp)
            for (i1576, elem1334) in enumerate(fields1333)
                i1335 = i1576 - 1
                if (i1335 > 0)
                    newline(pp)
                end
                pretty_iceberg_kv_pair(pp, elem1334)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_kv_pair(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1341 = try_flat(pp, msg, pretty_iceberg_kv_pair)
    if !isnothing(flat1341)
        write(pp, flat1341)
        return nothing
    else
        _dollar_dollar = msg
        fields1337 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1338 = fields1337
        write(pp, "(")
        indent!(pp)
        field1339 = unwrapped_fields1338[1]
        write(pp, format_string(pp, field1339))
        newline(pp)
        field1340 = unwrapped_fields1338[2]
        write(pp, format_string(pp, field1340))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_config_credentials(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1345 = try_flat(pp, msg, pretty_iceberg_config_credentials)
    if !isnothing(flat1345)
        write(pp, flat1345)
        return nothing
    else
        fields1342 = msg
        write(pp, "(credentials")
        indent_sexp!(pp)
        if !isempty(fields1342)
            newline(pp)
            for (i1577, elem1343) in enumerate(fields1342)
                i1344 = i1577 - 1
                if (i1344 > 0)
                    newline(pp)
                end
                pretty_iceberg_kv_pair(pp, elem1343)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1347 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1347)
        write(pp, flat1347)
        return nothing
    else
        fields1346 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1346))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1350 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1350)
        write(pp, flat1350)
        return nothing
    else
        _dollar_dollar = msg
        fields1348 = _dollar_dollar.fragment_id
        unwrapped_fields1349 = fields1348
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1349)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1355 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1355)
        write(pp, flat1355)
        return nothing
    else
        _dollar_dollar = msg
        fields1351 = _dollar_dollar.relations
        unwrapped_fields1352 = fields1351
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1352)
            newline(pp)
            for (i1578, elem1353) in enumerate(unwrapped_fields1352)
                i1354 = i1578 - 1
                if (i1354 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1353)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1360 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1360)
        write(pp, flat1360)
        return nothing
    else
        _dollar_dollar = msg
        fields1356 = _dollar_dollar.mappings
        unwrapped_fields1357 = fields1356
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1357)
            newline(pp)
            for (i1579, elem1358) in enumerate(unwrapped_fields1357)
                i1359 = i1579 - 1
                if (i1359 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1358)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1365 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1365)
        write(pp, flat1365)
        return nothing
    else
        _dollar_dollar = msg
        fields1361 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1362 = fields1361
        field1363 = unwrapped_fields1362[1]
        pretty_edb_path(pp, field1363)
        write(pp, " ")
        field1364 = unwrapped_fields1362[2]
        pretty_relation_id(pp, field1364)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1369 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1369)
        write(pp, flat1369)
        return nothing
    else
        fields1366 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1366)
            newline(pp)
            for (i1580, elem1367) in enumerate(fields1366)
                i1368 = i1580 - 1
                if (i1368 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1367)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1380 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1380)
        write(pp, flat1380)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1581 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1581 = nothing
        end
        deconstruct_result1378 = _t1581
        if !isnothing(deconstruct_result1378)
            unwrapped1379 = deconstruct_result1378
            pretty_demand(pp, unwrapped1379)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1582 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1582 = nothing
            end
            deconstruct_result1376 = _t1582
            if !isnothing(deconstruct_result1376)
                unwrapped1377 = deconstruct_result1376
                pretty_output(pp, unwrapped1377)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1583 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1583 = nothing
                end
                deconstruct_result1374 = _t1583
                if !isnothing(deconstruct_result1374)
                    unwrapped1375 = deconstruct_result1374
                    pretty_what_if(pp, unwrapped1375)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1584 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1584 = nothing
                    end
                    deconstruct_result1372 = _t1584
                    if !isnothing(deconstruct_result1372)
                        unwrapped1373 = deconstruct_result1372
                        pretty_abort(pp, unwrapped1373)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1585 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1585 = nothing
                        end
                        deconstruct_result1370 = _t1585
                        if !isnothing(deconstruct_result1370)
                            unwrapped1371 = deconstruct_result1370
                            pretty_export(pp, unwrapped1371)
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
    flat1383 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1383)
        write(pp, flat1383)
        return nothing
    else
        _dollar_dollar = msg
        fields1381 = _dollar_dollar.relation_id
        unwrapped_fields1382 = fields1381
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1382)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1388 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1388)
        write(pp, flat1388)
        return nothing
    else
        _dollar_dollar = msg
        fields1384 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1385 = fields1384
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1386 = unwrapped_fields1385[1]
        pretty_name(pp, field1386)
        newline(pp)
        field1387 = unwrapped_fields1385[2]
        pretty_relation_id(pp, field1387)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1393 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1393)
        write(pp, flat1393)
        return nothing
    else
        _dollar_dollar = msg
        fields1389 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1390 = fields1389
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1391 = unwrapped_fields1390[1]
        pretty_name(pp, field1391)
        newline(pp)
        field1392 = unwrapped_fields1390[2]
        pretty_epoch(pp, field1392)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1399 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1399)
        write(pp, flat1399)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1586 = _dollar_dollar.name
        else
            _t1586 = nothing
        end
        fields1394 = (_t1586, _dollar_dollar.relation_id,)
        unwrapped_fields1395 = fields1394
        write(pp, "(abort")
        indent_sexp!(pp)
        field1396 = unwrapped_fields1395[1]
        if !isnothing(field1396)
            newline(pp)
            opt_val1397 = field1396
            pretty_name(pp, opt_val1397)
        end
        newline(pp)
        field1398 = unwrapped_fields1395[2]
        pretty_relation_id(pp, field1398)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1402 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1402)
        write(pp, flat1402)
        return nothing
    else
        _dollar_dollar = msg
        fields1400 = _get_oneof_field(_dollar_dollar, :csv_config)
        unwrapped_fields1401 = fields1400
        write(pp, "(export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1401)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1413 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1413)
        write(pp, flat1413)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1587 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1587 = nothing
        end
        deconstruct_result1408 = _t1587
        if !isnothing(deconstruct_result1408)
            unwrapped1409 = deconstruct_result1408
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1410 = unwrapped1409[1]
            pretty_export_csv_path(pp, field1410)
            newline(pp)
            field1411 = unwrapped1409[2]
            pretty_export_csv_source(pp, field1411)
            newline(pp)
            field1412 = unwrapped1409[3]
            pretty_csv_config(pp, field1412)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1589 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1588 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1589,)
            else
                _t1588 = nothing
            end
            deconstruct_result1403 = _t1588
            if !isnothing(deconstruct_result1403)
                unwrapped1404 = deconstruct_result1403
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1405 = unwrapped1404[1]
                pretty_export_csv_path(pp, field1405)
                newline(pp)
                field1406 = unwrapped1404[2]
                pretty_export_csv_columns_list(pp, field1406)
                newline(pp)
                field1407 = unwrapped1404[3]
                pretty_config_dict(pp, field1407)
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
    flat1415 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1415)
        write(pp, flat1415)
        return nothing
    else
        fields1414 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1414))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1422 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1422)
        write(pp, flat1422)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1590 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1590 = nothing
        end
        deconstruct_result1418 = _t1590
        if !isnothing(deconstruct_result1418)
            unwrapped1419 = deconstruct_result1418
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1419)
                newline(pp)
                for (i1591, elem1420) in enumerate(unwrapped1419)
                    i1421 = i1591 - 1
                    if (i1421 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1420)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1592 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1592 = nothing
            end
            deconstruct_result1416 = _t1592
            if !isnothing(deconstruct_result1416)
                unwrapped1417 = deconstruct_result1416
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1417)
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
    flat1427 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1427)
        write(pp, flat1427)
        return nothing
    else
        _dollar_dollar = msg
        fields1423 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1424 = fields1423
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1425 = unwrapped_fields1424[1]
        write(pp, format_string(pp, field1425))
        newline(pp)
        field1426 = unwrapped_fields1424[2]
        pretty_relation_id(pp, field1426)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1431 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1431)
        write(pp, flat1431)
        return nothing
    else
        fields1428 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1428)
            newline(pp)
            for (i1593, elem1429) in enumerate(fields1428)
                i1430 = i1593 - 1
                if (i1430 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1429)
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
    for (i1632, _rid) in enumerate(msg.ids)
        _idx = i1632 - 1
        newline(pp)
        write(pp, "(")
        _t1633 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1633)
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
    for (i1634, _elem) in enumerate(msg.keys)
        _idx = i1634 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1635, _elem) in enumerate(msg.values)
        _idx = i1635 - 1
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
    for (i1636, _elem) in enumerate(msg.columns)
        _idx = i1636 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.IcebergConfig) = pretty_iceberg_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Tuple{String, String}}) = pretty_iceberg_config_properties(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Tuple{String, String}) = pretty_iceberg_kv_pair(pp, x)
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
