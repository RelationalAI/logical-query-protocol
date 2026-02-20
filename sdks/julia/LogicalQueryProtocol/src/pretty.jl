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
    format_int(formatter::ConstantFormatter, pp::PrettyPrinter, v::Integer)::String

Format an integer value as a string.

Override this function for custom ConstantFormatter subtypes to customize integer formatting.
"""
format_int(formatter::DefaultConstantFormatter, pp::PrettyPrinter, v::Integer)::String = string(v)

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
format_int(formatter::ConstantFormatter, pp::PrettyPrinter, v::Integer)::String = format_int(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_float(formatter::ConstantFormatter, pp::PrettyPrinter, v::Float64)::String = format_float(DEFAULT_CONSTANT_FORMATTER, pp, v)
format_string(formatter::ConstantFormatter, pp::PrettyPrinter, s::AbstractString)::String = format_string(DEFAULT_CONSTANT_FORMATTER, pp, s)
format_bool(formatter::ConstantFormatter, pp::PrettyPrinter, v::Bool)::String = format_bool(DEFAULT_CONSTANT_FORMATTER, pp, v)

# Backward compatibility: convenience methods that use pp.constant_formatter
format_decimal(pp::PrettyPrinter, msg::Proto.DecimalValue)::String = format_decimal(pp.constant_formatter, pp, msg)
format_int128(pp::PrettyPrinter, msg::Proto.Int128Value)::String = format_int128(pp.constant_formatter, pp, msg)
format_uint128(pp::PrettyPrinter, msg::Proto.UInt128Value)::String = format_uint128(pp.constant_formatter, pp, msg)
format_int(pp::PrettyPrinter, v::Integer)::String = format_int(pp.constant_formatter, pp, v)
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
    _t1686 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1686
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1687 = Proto.Value(value=OneOf(:int_value, v))
    return _t1687
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1688 = Proto.Value(value=OneOf(:float_value, v))
    return _t1688
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1689 = Proto.Value(value=OneOf(:string_value, v))
    return _t1689
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1690 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1690
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1691 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1691
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1692 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1692,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1693 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1693,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1694 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1694,))
            end
        end
    end
    _t1695 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1695,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1696 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1696,))
    _t1697 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1697,))
    if msg.new_line != ""
        _t1698 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1698,))
    end
    _t1699 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1699,))
    _t1700 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1700,))
    _t1701 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1701,))
    if msg.comment != ""
        _t1702 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1702,))
    end
    for missing_string in msg.missing_strings
        _t1703 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1703,))
    end
    _t1704 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1704,))
    _t1705 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1705,))
    _t1706 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1706,))
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1707 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1707,))
    _t1708 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1708,))
    _t1709 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1709,))
    _t1710 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1710,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1711 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1711,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1712 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1712,))
        end
    end
    _t1713 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1713,))
    _t1714 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1714,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1715 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1715,))
    end
    if !isnothing(msg.compression)
        _t1716 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1716,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1717 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1717,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1718 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1718,))
    end
    if !isnothing(msg.syntax_delim)
        _t1719 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1719,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1720 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1720,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1721 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1721,))
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
        _t1722 = nothing
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
    flat638 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat638)
        write(pp, flat638)
        return nothing
    else
        function _t1258(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("configure"))
                _t1259 = _dollar_dollar.configure
            else
                _t1259 = nothing
            end
            if _has_proto_field(_dollar_dollar, Symbol("sync"))
                _t1260 = _dollar_dollar.sync
            else
                _t1260 = nothing
            end
            return (_t1259, _t1260, _dollar_dollar.epochs,)
        end
        _t1261 = _t1258(msg)
        fields629 = _t1261
        unwrapped_fields630 = fields629
        write(pp, "(")
        write(pp, "transaction")
        indent_sexp!(pp)
        field631 = unwrapped_fields630[1]
        if !isnothing(field631)
            newline(pp)
            opt_val632 = field631
            pretty_configure(pp, opt_val632)
        end
        field633 = unwrapped_fields630[2]
        if !isnothing(field633)
            newline(pp)
            opt_val634 = field633
            pretty_sync(pp, opt_val634)
        end
        field635 = unwrapped_fields630[3]
        if !isempty(field635)
            newline(pp)
            for (i1262, elem636) in enumerate(field635)
                i637 = i1262 - 1
                if (i637 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem636)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat641 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat641)
        write(pp, flat641)
        return nothing
    else
        function _t1263(_dollar_dollar)
            _t1264 = deconstruct_configure(pp, _dollar_dollar)
            return _t1264
        end
        _t1265 = _t1263(msg)
        fields639 = _t1265
        unwrapped_fields640 = fields639
        write(pp, "(")
        write(pp, "configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields640)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat645 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat645)
        write(pp, flat645)
        return nothing
    else
        fields642 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields642)
            newline(pp)
            for (i1266, elem643) in enumerate(fields642)
                i644 = i1266 - 1
                if (i644 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem643)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat650 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat650)
        write(pp, flat650)
        return nothing
    else
        function _t1267(_dollar_dollar)
            return (_dollar_dollar[1], _dollar_dollar[2],)
        end
        _t1268 = _t1267(msg)
        fields646 = _t1268
        unwrapped_fields647 = fields646
        write(pp, ":")
        field648 = unwrapped_fields647[1]
        write(pp, field648)
        write(pp, " ")
        field649 = unwrapped_fields647[2]
        pretty_value(pp, field649)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat670 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat670)
        write(pp, flat670)
        return nothing
    else
        function _t1269(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("date_value"))
                _t1270 = _get_oneof_field(_dollar_dollar, :date_value)
            else
                _t1270 = nothing
            end
            return _t1270
        end
        _t1271 = _t1269(msg)
        deconstruct_result668 = _t1271
        if !isnothing(deconstruct_result668)
            unwrapped669 = deconstruct_result668
            pretty_date(pp, unwrapped669)
        else
            function _t1272(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                    _t1273 = _get_oneof_field(_dollar_dollar, :datetime_value)
                else
                    _t1273 = nothing
                end
                return _t1273
            end
            _t1274 = _t1272(msg)
            deconstruct_result666 = _t1274
            if !isnothing(deconstruct_result666)
                unwrapped667 = deconstruct_result666
                pretty_datetime(pp, unwrapped667)
            else
                function _t1275(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                        _t1276 = _get_oneof_field(_dollar_dollar, :string_value)
                    else
                        _t1276 = nothing
                    end
                    return _t1276
                end
                _t1277 = _t1275(msg)
                deconstruct_result664 = _t1277
                if !isnothing(deconstruct_result664)
                    unwrapped665 = deconstruct_result664
                    write(pp, format_string(pp, unwrapped665))
                else
                    function _t1278(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1279 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1279 = nothing
                        end
                        return _t1279
                    end
                    _t1280 = _t1278(msg)
                    deconstruct_result662 = _t1280
                    if !isnothing(deconstruct_result662)
                        unwrapped663 = deconstruct_result662
                        write(pp, format_int(pp, unwrapped663))
                    else
                        function _t1281(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                _t1282 = _get_oneof_field(_dollar_dollar, :float_value)
                            else
                                _t1282 = nothing
                            end
                            return _t1282
                        end
                        _t1283 = _t1281(msg)
                        deconstruct_result660 = _t1283
                        if !isnothing(deconstruct_result660)
                            unwrapped661 = deconstruct_result660
                            write(pp, format_float(pp, unwrapped661))
                        else
                            function _t1284(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                    _t1285 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                else
                                    _t1285 = nothing
                                end
                                return _t1285
                            end
                            _t1286 = _t1284(msg)
                            deconstruct_result658 = _t1286
                            if !isnothing(deconstruct_result658)
                                unwrapped659 = deconstruct_result658
                                write(pp, format_uint128(pp, unwrapped659))
                            else
                                function _t1287(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                        _t1288 = _get_oneof_field(_dollar_dollar, :int128_value)
                                    else
                                        _t1288 = nothing
                                    end
                                    return _t1288
                                end
                                _t1289 = _t1287(msg)
                                deconstruct_result656 = _t1289
                                if !isnothing(deconstruct_result656)
                                    unwrapped657 = deconstruct_result656
                                    write(pp, format_int128(pp, unwrapped657))
                                else
                                    function _t1290(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                            _t1291 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                        else
                                            _t1291 = nothing
                                        end
                                        return _t1291
                                    end
                                    _t1292 = _t1290(msg)
                                    deconstruct_result654 = _t1292
                                    if !isnothing(deconstruct_result654)
                                        unwrapped655 = deconstruct_result654
                                        write(pp, format_decimal(pp, unwrapped655))
                                    else
                                        function _t1293(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                _t1294 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                            else
                                                _t1294 = nothing
                                            end
                                            return _t1294
                                        end
                                        _t1295 = _t1293(msg)
                                        deconstruct_result652 = _t1295
                                        if !isnothing(deconstruct_result652)
                                            unwrapped653 = deconstruct_result652
                                            pretty_boolean_value(pp, unwrapped653)
                                        else
                                            fields651 = msg
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
    flat676 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat676)
        write(pp, flat676)
        return nothing
    else
        function _t1296(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        end
        _t1297 = _t1296(msg)
        fields671 = _t1297
        unwrapped_fields672 = fields671
        write(pp, "(")
        write(pp, "date")
        indent_sexp!(pp)
        newline(pp)
        field673 = unwrapped_fields672[1]
        write(pp, format_int(pp, field673))
        newline(pp)
        field674 = unwrapped_fields672[2]
        write(pp, format_int(pp, field674))
        newline(pp)
        field675 = unwrapped_fields672[3]
        write(pp, format_int(pp, field675))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat687 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat687)
        write(pp, flat687)
        return nothing
    else
        function _t1298(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        end
        _t1299 = _t1298(msg)
        fields677 = _t1299
        unwrapped_fields678 = fields677
        write(pp, "(")
        write(pp, "datetime")
        indent_sexp!(pp)
        newline(pp)
        field679 = unwrapped_fields678[1]
        write(pp, format_int(pp, field679))
        newline(pp)
        field680 = unwrapped_fields678[2]
        write(pp, format_int(pp, field680))
        newline(pp)
        field681 = unwrapped_fields678[3]
        write(pp, format_int(pp, field681))
        newline(pp)
        field682 = unwrapped_fields678[4]
        write(pp, format_int(pp, field682))
        newline(pp)
        field683 = unwrapped_fields678[5]
        write(pp, format_int(pp, field683))
        newline(pp)
        field684 = unwrapped_fields678[6]
        write(pp, format_int(pp, field684))
        field685 = unwrapped_fields678[7]
        if !isnothing(field685)
            newline(pp)
            opt_val686 = field685
            write(pp, format_int(pp, opt_val686))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    function _t1300(_dollar_dollar)
        if _dollar_dollar
            _t1301 = ()
        else
            _t1301 = nothing
        end
        return _t1301
    end
    _t1302 = _t1300(msg)
    deconstruct_result690 = _t1302
    if !isnothing(deconstruct_result690)
        unwrapped691 = deconstruct_result690
        write(pp, "true")
    else
        function _t1303(_dollar_dollar)
            if !_dollar_dollar
                _t1304 = ()
            else
                _t1304 = nothing
            end
            return _t1304
        end
        _t1305 = _t1303(msg)
        deconstruct_result688 = _t1305
        if !isnothing(deconstruct_result688)
            unwrapped689 = deconstruct_result688
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat696 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat696)
        write(pp, flat696)
        return nothing
    else
        function _t1306(_dollar_dollar)
            return _dollar_dollar.fragments
        end
        _t1307 = _t1306(msg)
        fields692 = _t1307
        unwrapped_fields693 = fields692
        write(pp, "(")
        write(pp, "sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields693)
            newline(pp)
            for (i1308, elem694) in enumerate(unwrapped_fields693)
                i695 = i1308 - 1
                if (i695 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem694)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat699 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat699)
        write(pp, flat699)
        return nothing
    else
        function _t1309(_dollar_dollar)
            return fragment_id_to_string(pp, _dollar_dollar)
        end
        _t1310 = _t1309(msg)
        fields697 = _t1310
        unwrapped_fields698 = fields697
        write(pp, ":")
        write(pp, unwrapped_fields698)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat706 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat706)
        write(pp, flat706)
        return nothing
    else
        function _t1311(_dollar_dollar)
            if !isempty(_dollar_dollar.writes)
                _t1312 = _dollar_dollar.writes
            else
                _t1312 = nothing
            end
            if !isempty(_dollar_dollar.reads)
                _t1313 = _dollar_dollar.reads
            else
                _t1313 = nothing
            end
            return (_t1312, _t1313,)
        end
        _t1314 = _t1311(msg)
        fields700 = _t1314
        unwrapped_fields701 = fields700
        write(pp, "(")
        write(pp, "epoch")
        indent_sexp!(pp)
        field702 = unwrapped_fields701[1]
        if !isnothing(field702)
            newline(pp)
            opt_val703 = field702
            pretty_epoch_writes(pp, opt_val703)
        end
        field704 = unwrapped_fields701[2]
        if !isnothing(field704)
            newline(pp)
            opt_val705 = field704
            pretty_epoch_reads(pp, opt_val705)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat710 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat710)
        write(pp, flat710)
        return nothing
    else
        fields707 = msg
        write(pp, "(")
        write(pp, "writes")
        indent_sexp!(pp)
        if !isempty(fields707)
            newline(pp)
            for (i1315, elem708) in enumerate(fields707)
                i709 = i1315 - 1
                if (i709 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem708)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat719 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat719)
        write(pp, flat719)
        return nothing
    else
        function _t1316(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("define"))
                _t1317 = _get_oneof_field(_dollar_dollar, :define)
            else
                _t1317 = nothing
            end
            return _t1317
        end
        _t1318 = _t1316(msg)
        deconstruct_result717 = _t1318
        if !isnothing(deconstruct_result717)
            unwrapped718 = deconstruct_result717
            pretty_define(pp, unwrapped718)
        else
            function _t1319(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                    _t1320 = _get_oneof_field(_dollar_dollar, :undefine)
                else
                    _t1320 = nothing
                end
                return _t1320
            end
            _t1321 = _t1319(msg)
            deconstruct_result715 = _t1321
            if !isnothing(deconstruct_result715)
                unwrapped716 = deconstruct_result715
                pretty_undefine(pp, unwrapped716)
            else
                function _t1322(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("context"))
                        _t1323 = _get_oneof_field(_dollar_dollar, :context)
                    else
                        _t1323 = nothing
                    end
                    return _t1323
                end
                _t1324 = _t1322(msg)
                deconstruct_result713 = _t1324
                if !isnothing(deconstruct_result713)
                    unwrapped714 = deconstruct_result713
                    pretty_context(pp, unwrapped714)
                else
                    function _t1325(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                            _t1326 = _get_oneof_field(_dollar_dollar, :snapshot)
                        else
                            _t1326 = nothing
                        end
                        return _t1326
                    end
                    _t1327 = _t1325(msg)
                    deconstruct_result711 = _t1327
                    if !isnothing(deconstruct_result711)
                        unwrapped712 = deconstruct_result711
                        pretty_snapshot(pp, unwrapped712)
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
    flat722 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat722)
        write(pp, flat722)
        return nothing
    else
        function _t1328(_dollar_dollar)
            return _dollar_dollar.fragment
        end
        _t1329 = _t1328(msg)
        fields720 = _t1329
        unwrapped_fields721 = fields720
        write(pp, "(")
        write(pp, "define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields721)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat729 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat729)
        write(pp, flat729)
        return nothing
    else
        function _t1330(_dollar_dollar)
            start_pretty_fragment(pp, _dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        end
        _t1331 = _t1330(msg)
        fields723 = _t1331
        unwrapped_fields724 = fields723
        write(pp, "(")
        write(pp, "fragment")
        indent_sexp!(pp)
        newline(pp)
        field725 = unwrapped_fields724[1]
        pretty_new_fragment_id(pp, field725)
        field726 = unwrapped_fields724[2]
        if !isempty(field726)
            newline(pp)
            for (i1332, elem727) in enumerate(field726)
                i728 = i1332 - 1
                if (i728 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem727)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat731 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat731)
        write(pp, flat731)
        return nothing
    else
        fields730 = msg
        pretty_fragment_id(pp, fields730)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat740 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat740)
        write(pp, flat740)
        return nothing
    else
        function _t1333(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("def"))
                _t1334 = _get_oneof_field(_dollar_dollar, :def)
            else
                _t1334 = nothing
            end
            return _t1334
        end
        _t1335 = _t1333(msg)
        deconstruct_result738 = _t1335
        if !isnothing(deconstruct_result738)
            unwrapped739 = deconstruct_result738
            pretty_def(pp, unwrapped739)
        else
            function _t1336(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                    _t1337 = _get_oneof_field(_dollar_dollar, :algorithm)
                else
                    _t1337 = nothing
                end
                return _t1337
            end
            _t1338 = _t1336(msg)
            deconstruct_result736 = _t1338
            if !isnothing(deconstruct_result736)
                unwrapped737 = deconstruct_result736
                pretty_algorithm(pp, unwrapped737)
            else
                function _t1339(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                        _t1340 = _get_oneof_field(_dollar_dollar, :constraint)
                    else
                        _t1340 = nothing
                    end
                    return _t1340
                end
                _t1341 = _t1339(msg)
                deconstruct_result734 = _t1341
                if !isnothing(deconstruct_result734)
                    unwrapped735 = deconstruct_result734
                    pretty_constraint(pp, unwrapped735)
                else
                    function _t1342(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("data"))
                            _t1343 = _get_oneof_field(_dollar_dollar, :data)
                        else
                            _t1343 = nothing
                        end
                        return _t1343
                    end
                    _t1344 = _t1342(msg)
                    deconstruct_result732 = _t1344
                    if !isnothing(deconstruct_result732)
                        unwrapped733 = deconstruct_result732
                        pretty_data(pp, unwrapped733)
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
    flat747 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat747)
        write(pp, flat747)
        return nothing
    else
        function _t1345(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1346 = _dollar_dollar.attrs
            else
                _t1346 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1346,)
        end
        _t1347 = _t1345(msg)
        fields741 = _t1347
        unwrapped_fields742 = fields741
        write(pp, "(")
        write(pp, "def")
        indent_sexp!(pp)
        newline(pp)
        field743 = unwrapped_fields742[1]
        pretty_relation_id(pp, field743)
        newline(pp)
        field744 = unwrapped_fields742[2]
        pretty_abstraction(pp, field744)
        field745 = unwrapped_fields742[3]
        if !isnothing(field745)
            newline(pp)
            opt_val746 = field745
            pretty_attrs(pp, opt_val746)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat752 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat752)
        write(pp, flat752)
        return nothing
    else
        function _t1348(_dollar_dollar)
            if !isnothing(relation_id_to_string(pp, _dollar_dollar))
                _t1350 = deconstruct_relation_id_string(pp, _dollar_dollar)
                _t1349 = _t1350
            else
                _t1349 = nothing
            end
            return _t1349
        end
        _t1351 = _t1348(msg)
        deconstruct_result750 = _t1351
        if !isnothing(deconstruct_result750)
            unwrapped751 = deconstruct_result750
            write(pp, ":")
            write(pp, unwrapped751)
        else
            function _t1352(_dollar_dollar)
                _t1353 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
                return _t1353
            end
            _t1354 = _t1352(msg)
            deconstruct_result748 = _t1354
            if !isnothing(deconstruct_result748)
                unwrapped749 = deconstruct_result748
                write(pp, format_uint128(pp, unwrapped749))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat757 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat757)
        write(pp, flat757)
        return nothing
    else
        function _t1355(_dollar_dollar)
            _t1356 = deconstruct_bindings(pp, _dollar_dollar)
            return (_t1356, _dollar_dollar.value,)
        end
        _t1357 = _t1355(msg)
        fields753 = _t1357
        unwrapped_fields754 = fields753
        write(pp, "(")
        indent!(pp)
        field755 = unwrapped_fields754[1]
        pretty_bindings(pp, field755)
        newline(pp)
        field756 = unwrapped_fields754[2]
        pretty_formula(pp, field756)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat765 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat765)
        write(pp, flat765)
        return nothing
    else
        function _t1358(_dollar_dollar)
            if !isempty(_dollar_dollar[2])
                _t1359 = _dollar_dollar[2]
            else
                _t1359 = nothing
            end
            return (_dollar_dollar[1], _t1359,)
        end
        _t1360 = _t1358(msg)
        fields758 = _t1360
        unwrapped_fields759 = fields758
        write(pp, "[")
        indent!(pp)
        field760 = unwrapped_fields759[1]
        for (i1361, elem761) in enumerate(field760)
            i762 = i1361 - 1
            if (i762 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem761)
        end
        field763 = unwrapped_fields759[2]
        if !isnothing(field763)
            newline(pp)
            opt_val764 = field763
            pretty_value_bindings(pp, opt_val764)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat770 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat770)
        write(pp, flat770)
        return nothing
    else
        function _t1362(_dollar_dollar)
            return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        end
        _t1363 = _t1362(msg)
        fields766 = _t1363
        unwrapped_fields767 = fields766
        field768 = unwrapped_fields767[1]
        write(pp, field768)
        write(pp, "::")
        field769 = unwrapped_fields767[2]
        pretty_type(pp, field769)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat793 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat793)
        write(pp, flat793)
        return nothing
    else
        function _t1364(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
                _t1365 = _get_oneof_field(_dollar_dollar, :unspecified_type)
            else
                _t1365 = nothing
            end
            return _t1365
        end
        _t1366 = _t1364(msg)
        deconstruct_result791 = _t1366
        if !isnothing(deconstruct_result791)
            unwrapped792 = deconstruct_result791
            pretty_unspecified_type(pp, unwrapped792)
        else
            function _t1367(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                    _t1368 = _get_oneof_field(_dollar_dollar, :string_type)
                else
                    _t1368 = nothing
                end
                return _t1368
            end
            _t1369 = _t1367(msg)
            deconstruct_result789 = _t1369
            if !isnothing(deconstruct_result789)
                unwrapped790 = deconstruct_result789
                pretty_string_type(pp, unwrapped790)
            else
                function _t1370(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                        _t1371 = _get_oneof_field(_dollar_dollar, :int_type)
                    else
                        _t1371 = nothing
                    end
                    return _t1371
                end
                _t1372 = _t1370(msg)
                deconstruct_result787 = _t1372
                if !isnothing(deconstruct_result787)
                    unwrapped788 = deconstruct_result787
                    pretty_int_type(pp, unwrapped788)
                else
                    function _t1373(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                            _t1374 = _get_oneof_field(_dollar_dollar, :float_type)
                        else
                            _t1374 = nothing
                        end
                        return _t1374
                    end
                    _t1375 = _t1373(msg)
                    deconstruct_result785 = _t1375
                    if !isnothing(deconstruct_result785)
                        unwrapped786 = deconstruct_result785
                        pretty_float_type(pp, unwrapped786)
                    else
                        function _t1376(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                                _t1377 = _get_oneof_field(_dollar_dollar, :uint128_type)
                            else
                                _t1377 = nothing
                            end
                            return _t1377
                        end
                        _t1378 = _t1376(msg)
                        deconstruct_result783 = _t1378
                        if !isnothing(deconstruct_result783)
                            unwrapped784 = deconstruct_result783
                            pretty_uint128_type(pp, unwrapped784)
                        else
                            function _t1379(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                    _t1380 = _get_oneof_field(_dollar_dollar, :int128_type)
                                else
                                    _t1380 = nothing
                                end
                                return _t1380
                            end
                            _t1381 = _t1379(msg)
                            deconstruct_result781 = _t1381
                            if !isnothing(deconstruct_result781)
                                unwrapped782 = deconstruct_result781
                                pretty_int128_type(pp, unwrapped782)
                            else
                                function _t1382(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                        _t1383 = _get_oneof_field(_dollar_dollar, :date_type)
                                    else
                                        _t1383 = nothing
                                    end
                                    return _t1383
                                end
                                _t1384 = _t1382(msg)
                                deconstruct_result779 = _t1384
                                if !isnothing(deconstruct_result779)
                                    unwrapped780 = deconstruct_result779
                                    pretty_date_type(pp, unwrapped780)
                                else
                                    function _t1385(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                            _t1386 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                        else
                                            _t1386 = nothing
                                        end
                                        return _t1386
                                    end
                                    _t1387 = _t1385(msg)
                                    deconstruct_result777 = _t1387
                                    if !isnothing(deconstruct_result777)
                                        unwrapped778 = deconstruct_result777
                                        pretty_datetime_type(pp, unwrapped778)
                                    else
                                        function _t1388(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                                _t1389 = _get_oneof_field(_dollar_dollar, :missing_type)
                                            else
                                                _t1389 = nothing
                                            end
                                            return _t1389
                                        end
                                        _t1390 = _t1388(msg)
                                        deconstruct_result775 = _t1390
                                        if !isnothing(deconstruct_result775)
                                            unwrapped776 = deconstruct_result775
                                            pretty_missing_type(pp, unwrapped776)
                                        else
                                            function _t1391(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                    _t1392 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                                else
                                                    _t1392 = nothing
                                                end
                                                return _t1392
                                            end
                                            _t1393 = _t1391(msg)
                                            deconstruct_result773 = _t1393
                                            if !isnothing(deconstruct_result773)
                                                unwrapped774 = deconstruct_result773
                                                pretty_decimal_type(pp, unwrapped774)
                                            else
                                                function _t1394(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                        _t1395 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                    else
                                                        _t1395 = nothing
                                                    end
                                                    return _t1395
                                                end
                                                _t1396 = _t1394(msg)
                                                deconstruct_result771 = _t1396
                                                if !isnothing(deconstruct_result771)
                                                    unwrapped772 = deconstruct_result771
                                                    pretty_boolean_type(pp, unwrapped772)
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
    fields794 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields795 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields796 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields797 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields798 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields799 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields800 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields801 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields802 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat807 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat807)
        write(pp, flat807)
        return nothing
    else
        function _t1397(_dollar_dollar)
            return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        end
        _t1398 = _t1397(msg)
        fields803 = _t1398
        unwrapped_fields804 = fields803
        write(pp, "(")
        write(pp, "DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field805 = unwrapped_fields804[1]
        write(pp, format_int(pp, field805))
        newline(pp)
        field806 = unwrapped_fields804[2]
        write(pp, format_int(pp, field806))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields808 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat812 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat812)
        write(pp, flat812)
        return nothing
    else
        fields809 = msg
        write(pp, "|")
        if !isempty(fields809)
            write(pp, " ")
            for (i1399, elem810) in enumerate(fields809)
                i811 = i1399 - 1
                if (i811 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem810)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat839 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat839)
        write(pp, flat839)
        return nothing
    else
        function _t1400(_dollar_dollar)
            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                _t1401 = _get_oneof_field(_dollar_dollar, :conjunction)
            else
                _t1401 = nothing
            end
            return _t1401
        end
        _t1402 = _t1400(msg)
        deconstruct_result837 = _t1402
        if !isnothing(deconstruct_result837)
            unwrapped838 = deconstruct_result837
            pretty_true(pp, unwrapped838)
        else
            function _t1403(_dollar_dollar)
                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                    _t1404 = _get_oneof_field(_dollar_dollar, :disjunction)
                else
                    _t1404 = nothing
                end
                return _t1404
            end
            _t1405 = _t1403(msg)
            deconstruct_result835 = _t1405
            if !isnothing(deconstruct_result835)
                unwrapped836 = deconstruct_result835
                pretty_false(pp, unwrapped836)
            else
                function _t1406(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("exists"))
                        _t1407 = _get_oneof_field(_dollar_dollar, :exists)
                    else
                        _t1407 = nothing
                    end
                    return _t1407
                end
                _t1408 = _t1406(msg)
                deconstruct_result833 = _t1408
                if !isnothing(deconstruct_result833)
                    unwrapped834 = deconstruct_result833
                    pretty_exists(pp, unwrapped834)
                else
                    function _t1409(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                            _t1410 = _get_oneof_field(_dollar_dollar, :reduce)
                        else
                            _t1410 = nothing
                        end
                        return _t1410
                    end
                    _t1411 = _t1409(msg)
                    deconstruct_result831 = _t1411
                    if !isnothing(deconstruct_result831)
                        unwrapped832 = deconstruct_result831
                        pretty_reduce(pp, unwrapped832)
                    else
                        function _t1412(_dollar_dollar)
                            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                                _t1413 = _get_oneof_field(_dollar_dollar, :conjunction)
                            else
                                _t1413 = nothing
                            end
                            return _t1413
                        end
                        _t1414 = _t1412(msg)
                        deconstruct_result829 = _t1414
                        if !isnothing(deconstruct_result829)
                            unwrapped830 = deconstruct_result829
                            pretty_conjunction(pp, unwrapped830)
                        else
                            function _t1415(_dollar_dollar)
                                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                    _t1416 = _get_oneof_field(_dollar_dollar, :disjunction)
                                else
                                    _t1416 = nothing
                                end
                                return _t1416
                            end
                            _t1417 = _t1415(msg)
                            deconstruct_result827 = _t1417
                            if !isnothing(deconstruct_result827)
                                unwrapped828 = deconstruct_result827
                                pretty_disjunction(pp, unwrapped828)
                            else
                                function _t1418(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("not"))
                                        _t1419 = _get_oneof_field(_dollar_dollar, :not)
                                    else
                                        _t1419 = nothing
                                    end
                                    return _t1419
                                end
                                _t1420 = _t1418(msg)
                                deconstruct_result825 = _t1420
                                if !isnothing(deconstruct_result825)
                                    unwrapped826 = deconstruct_result825
                                    pretty_not(pp, unwrapped826)
                                else
                                    function _t1421(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                            _t1422 = _get_oneof_field(_dollar_dollar, :ffi)
                                        else
                                            _t1422 = nothing
                                        end
                                        return _t1422
                                    end
                                    _t1423 = _t1421(msg)
                                    deconstruct_result823 = _t1423
                                    if !isnothing(deconstruct_result823)
                                        unwrapped824 = deconstruct_result823
                                        pretty_ffi(pp, unwrapped824)
                                    else
                                        function _t1424(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                                _t1425 = _get_oneof_field(_dollar_dollar, :atom)
                                            else
                                                _t1425 = nothing
                                            end
                                            return _t1425
                                        end
                                        _t1426 = _t1424(msg)
                                        deconstruct_result821 = _t1426
                                        if !isnothing(deconstruct_result821)
                                            unwrapped822 = deconstruct_result821
                                            pretty_atom(pp, unwrapped822)
                                        else
                                            function _t1427(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                    _t1428 = _get_oneof_field(_dollar_dollar, :pragma)
                                                else
                                                    _t1428 = nothing
                                                end
                                                return _t1428
                                            end
                                            _t1429 = _t1427(msg)
                                            deconstruct_result819 = _t1429
                                            if !isnothing(deconstruct_result819)
                                                unwrapped820 = deconstruct_result819
                                                pretty_pragma(pp, unwrapped820)
                                            else
                                                function _t1430(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                        _t1431 = _get_oneof_field(_dollar_dollar, :primitive)
                                                    else
                                                        _t1431 = nothing
                                                    end
                                                    return _t1431
                                                end
                                                _t1432 = _t1430(msg)
                                                deconstruct_result817 = _t1432
                                                if !isnothing(deconstruct_result817)
                                                    unwrapped818 = deconstruct_result817
                                                    pretty_primitive(pp, unwrapped818)
                                                else
                                                    function _t1433(_dollar_dollar)
                                                        if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                            _t1434 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                        else
                                                            _t1434 = nothing
                                                        end
                                                        return _t1434
                                                    end
                                                    _t1435 = _t1433(msg)
                                                    deconstruct_result815 = _t1435
                                                    if !isnothing(deconstruct_result815)
                                                        unwrapped816 = deconstruct_result815
                                                        pretty_rel_atom(pp, unwrapped816)
                                                    else
                                                        function _t1436(_dollar_dollar)
                                                            if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                                _t1437 = _get_oneof_field(_dollar_dollar, :cast)
                                                            else
                                                                _t1437 = nothing
                                                            end
                                                            return _t1437
                                                        end
                                                        _t1438 = _t1436(msg)
                                                        deconstruct_result813 = _t1438
                                                        if !isnothing(deconstruct_result813)
                                                            unwrapped814 = deconstruct_result813
                                                            pretty_cast(pp, unwrapped814)
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
    fields840 = msg
    write(pp, "(")
    write(pp, "true")
    write(pp, ")")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields841 = msg
    write(pp, "(")
    write(pp, "false")
    write(pp, ")")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat846 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat846)
        write(pp, flat846)
        return nothing
    else
        function _t1439(_dollar_dollar)
            _t1440 = deconstruct_bindings(pp, _dollar_dollar.body)
            return (_t1440, _dollar_dollar.body.value,)
        end
        _t1441 = _t1439(msg)
        fields842 = _t1441
        unwrapped_fields843 = fields842
        write(pp, "(")
        write(pp, "exists")
        indent_sexp!(pp)
        newline(pp)
        field844 = unwrapped_fields843[1]
        pretty_bindings(pp, field844)
        newline(pp)
        field845 = unwrapped_fields843[2]
        pretty_formula(pp, field845)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat852 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat852)
        write(pp, flat852)
        return nothing
    else
        function _t1442(_dollar_dollar)
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        end
        _t1443 = _t1442(msg)
        fields847 = _t1443
        unwrapped_fields848 = fields847
        write(pp, "(")
        write(pp, "reduce")
        indent_sexp!(pp)
        newline(pp)
        field849 = unwrapped_fields848[1]
        pretty_abstraction(pp, field849)
        newline(pp)
        field850 = unwrapped_fields848[2]
        pretty_abstraction(pp, field850)
        newline(pp)
        field851 = unwrapped_fields848[3]
        pretty_terms(pp, field851)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat856 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat856)
        write(pp, flat856)
        return nothing
    else
        fields853 = msg
        write(pp, "(")
        write(pp, "terms")
        indent_sexp!(pp)
        if !isempty(fields853)
            newline(pp)
            for (i1444, elem854) in enumerate(fields853)
                i855 = i1444 - 1
                if (i855 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem854)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat861 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat861)
        write(pp, flat861)
        return nothing
    else
        function _t1445(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("var"))
                _t1446 = _get_oneof_field(_dollar_dollar, :var)
            else
                _t1446 = nothing
            end
            return _t1446
        end
        _t1447 = _t1445(msg)
        deconstruct_result859 = _t1447
        if !isnothing(deconstruct_result859)
            unwrapped860 = deconstruct_result859
            pretty_var(pp, unwrapped860)
        else
            function _t1448(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("constant"))
                    _t1449 = _get_oneof_field(_dollar_dollar, :constant)
                else
                    _t1449 = nothing
                end
                return _t1449
            end
            _t1450 = _t1448(msg)
            deconstruct_result857 = _t1450
            if !isnothing(deconstruct_result857)
                unwrapped858 = deconstruct_result857
                pretty_constant(pp, unwrapped858)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat864 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat864)
        write(pp, flat864)
        return nothing
    else
        function _t1451(_dollar_dollar)
            return _dollar_dollar.name
        end
        _t1452 = _t1451(msg)
        fields862 = _t1452
        unwrapped_fields863 = fields862
        write(pp, unwrapped_fields863)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat866 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat866)
        write(pp, flat866)
        return nothing
    else
        fields865 = msg
        pretty_value(pp, fields865)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat871 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat871)
        write(pp, flat871)
        return nothing
    else
        function _t1453(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1454 = _t1453(msg)
        fields867 = _t1454
        unwrapped_fields868 = fields867
        write(pp, "(")
        write(pp, "and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields868)
            newline(pp)
            for (i1455, elem869) in enumerate(unwrapped_fields868)
                i870 = i1455 - 1
                if (i870 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem869)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat876 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat876)
        write(pp, flat876)
        return nothing
    else
        function _t1456(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1457 = _t1456(msg)
        fields872 = _t1457
        unwrapped_fields873 = fields872
        write(pp, "(")
        write(pp, "or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields873)
            newline(pp)
            for (i1458, elem874) in enumerate(unwrapped_fields873)
                i875 = i1458 - 1
                if (i875 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem874)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat879 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat879)
        write(pp, flat879)
        return nothing
    else
        function _t1459(_dollar_dollar)
            return _dollar_dollar.arg
        end
        _t1460 = _t1459(msg)
        fields877 = _t1460
        unwrapped_fields878 = fields877
        write(pp, "(")
        write(pp, "not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields878)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat885 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat885)
        write(pp, flat885)
        return nothing
    else
        function _t1461(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        end
        _t1462 = _t1461(msg)
        fields880 = _t1462
        unwrapped_fields881 = fields880
        write(pp, "(")
        write(pp, "ffi")
        indent_sexp!(pp)
        newline(pp)
        field882 = unwrapped_fields881[1]
        pretty_name(pp, field882)
        newline(pp)
        field883 = unwrapped_fields881[2]
        pretty_ffi_args(pp, field883)
        newline(pp)
        field884 = unwrapped_fields881[3]
        pretty_terms(pp, field884)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat887 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat887)
        write(pp, flat887)
        return nothing
    else
        fields886 = msg
        write(pp, ":")
        write(pp, fields886)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat891 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat891)
        write(pp, flat891)
        return nothing
    else
        fields888 = msg
        write(pp, "(")
        write(pp, "args")
        indent_sexp!(pp)
        if !isempty(fields888)
            newline(pp)
            for (i1463, elem889) in enumerate(fields888)
                i890 = i1463 - 1
                if (i890 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem889)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat898 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat898)
        write(pp, flat898)
        return nothing
    else
        function _t1464(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1465 = _t1464(msg)
        fields892 = _t1465
        unwrapped_fields893 = fields892
        write(pp, "(")
        write(pp, "atom")
        indent_sexp!(pp)
        newline(pp)
        field894 = unwrapped_fields893[1]
        pretty_relation_id(pp, field894)
        field895 = unwrapped_fields893[2]
        if !isempty(field895)
            newline(pp)
            for (i1466, elem896) in enumerate(field895)
                i897 = i1466 - 1
                if (i897 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem896)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat905 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat905)
        write(pp, flat905)
        return nothing
    else
        function _t1467(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1468 = _t1467(msg)
        fields899 = _t1468
        unwrapped_fields900 = fields899
        write(pp, "(")
        write(pp, "pragma")
        indent_sexp!(pp)
        newline(pp)
        field901 = unwrapped_fields900[1]
        pretty_name(pp, field901)
        field902 = unwrapped_fields900[2]
        if !isempty(field902)
            newline(pp)
            for (i1469, elem903) in enumerate(field902)
                i904 = i1469 - 1
                if (i904 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem903)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat921 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat921)
        write(pp, flat921)
        return nothing
    else
        function _t1470(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1471 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1471 = nothing
            end
            return _t1471
        end
        _t1472 = _t1470(msg)
        guard_result920 = _t1472
        if !isnothing(guard_result920)
            pretty_eq(pp, msg)
        else
            function _t1473(_dollar_dollar)
                if _dollar_dollar.name == "rel_primitive_lt_monotype"
                    _t1474 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1474 = nothing
                end
                return _t1474
            end
            _t1475 = _t1473(msg)
            guard_result919 = _t1475
            if !isnothing(guard_result919)
                pretty_lt(pp, msg)
            else
                function _t1476(_dollar_dollar)
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                        _t1477 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1477 = nothing
                    end
                    return _t1477
                end
                _t1478 = _t1476(msg)
                guard_result918 = _t1478
                if !isnothing(guard_result918)
                    pretty_lt_eq(pp, msg)
                else
                    function _t1479(_dollar_dollar)
                        if _dollar_dollar.name == "rel_primitive_gt_monotype"
                            _t1480 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1480 = nothing
                        end
                        return _t1480
                    end
                    _t1481 = _t1479(msg)
                    guard_result917 = _t1481
                    if !isnothing(guard_result917)
                        pretty_gt(pp, msg)
                    else
                        function _t1482(_dollar_dollar)
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                                _t1483 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                            else
                                _t1483 = nothing
                            end
                            return _t1483
                        end
                        _t1484 = _t1482(msg)
                        guard_result916 = _t1484
                        if !isnothing(guard_result916)
                            pretty_gt_eq(pp, msg)
                        else
                            function _t1485(_dollar_dollar)
                                if _dollar_dollar.name == "rel_primitive_add_monotype"
                                    _t1486 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1486 = nothing
                                end
                                return _t1486
                            end
                            _t1487 = _t1485(msg)
                            guard_result915 = _t1487
                            if !isnothing(guard_result915)
                                pretty_add(pp, msg)
                            else
                                function _t1488(_dollar_dollar)
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                        _t1489 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1489 = nothing
                                    end
                                    return _t1489
                                end
                                _t1490 = _t1488(msg)
                                guard_result914 = _t1490
                                if !isnothing(guard_result914)
                                    pretty_minus(pp, msg)
                                else
                                    function _t1491(_dollar_dollar)
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                            _t1492 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1492 = nothing
                                        end
                                        return _t1492
                                    end
                                    _t1493 = _t1491(msg)
                                    guard_result913 = _t1493
                                    if !isnothing(guard_result913)
                                        pretty_multiply(pp, msg)
                                    else
                                        function _t1494(_dollar_dollar)
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                                _t1495 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                            else
                                                _t1495 = nothing
                                            end
                                            return _t1495
                                        end
                                        _t1496 = _t1494(msg)
                                        guard_result912 = _t1496
                                        if !isnothing(guard_result912)
                                            pretty_divide(pp, msg)
                                        else
                                            function _t1497(_dollar_dollar)
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            end
                                            _t1498 = _t1497(msg)
                                            fields906 = _t1498
                                            unwrapped_fields907 = fields906
                                            write(pp, "(")
                                            write(pp, "primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field908 = unwrapped_fields907[1]
                                            pretty_name(pp, field908)
                                            field909 = unwrapped_fields907[2]
                                            if !isempty(field909)
                                                newline(pp)
                                                for (i1499, elem910) in enumerate(field909)
                                                    i911 = i1499 - 1
                                                    if (i911 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem910)
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
    flat926 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat926)
        write(pp, flat926)
        return nothing
    else
        function _t1500(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1501 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1501 = nothing
            end
            return _t1501
        end
        _t1502 = _t1500(msg)
        fields922 = _t1502
        unwrapped_fields923 = fields922
        write(pp, "(")
        write(pp, "=")
        indent_sexp!(pp)
        newline(pp)
        field924 = unwrapped_fields923[1]
        pretty_term(pp, field924)
        newline(pp)
        field925 = unwrapped_fields923[2]
        pretty_term(pp, field925)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat931 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat931)
        write(pp, flat931)
        return nothing
    else
        function _t1503(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1504 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1504 = nothing
            end
            return _t1504
        end
        _t1505 = _t1503(msg)
        fields927 = _t1505
        unwrapped_fields928 = fields927
        write(pp, "(")
        write(pp, "<")
        indent_sexp!(pp)
        newline(pp)
        field929 = unwrapped_fields928[1]
        pretty_term(pp, field929)
        newline(pp)
        field930 = unwrapped_fields928[2]
        pretty_term(pp, field930)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat936 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat936)
        write(pp, flat936)
        return nothing
    else
        function _t1506(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                _t1507 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1507 = nothing
            end
            return _t1507
        end
        _t1508 = _t1506(msg)
        fields932 = _t1508
        unwrapped_fields933 = fields932
        write(pp, "(")
        write(pp, "<=")
        indent_sexp!(pp)
        newline(pp)
        field934 = unwrapped_fields933[1]
        pretty_term(pp, field934)
        newline(pp)
        field935 = unwrapped_fields933[2]
        pretty_term(pp, field935)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat941 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat941)
        write(pp, flat941)
        return nothing
    else
        function _t1509(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_monotype"
                _t1510 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1510 = nothing
            end
            return _t1510
        end
        _t1511 = _t1509(msg)
        fields937 = _t1511
        unwrapped_fields938 = fields937
        write(pp, "(")
        write(pp, ">")
        indent_sexp!(pp)
        newline(pp)
        field939 = unwrapped_fields938[1]
        pretty_term(pp, field939)
        newline(pp)
        field940 = unwrapped_fields938[2]
        pretty_term(pp, field940)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat946 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        function _t1512(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                _t1513 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1513 = nothing
            end
            return _t1513
        end
        _t1514 = _t1512(msg)
        fields942 = _t1514
        unwrapped_fields943 = fields942
        write(pp, "(")
        write(pp, ">=")
        indent_sexp!(pp)
        newline(pp)
        field944 = unwrapped_fields943[1]
        pretty_term(pp, field944)
        newline(pp)
        field945 = unwrapped_fields943[2]
        pretty_term(pp, field945)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat952 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat952)
        write(pp, flat952)
        return nothing
    else
        function _t1515(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_add_monotype"
                _t1516 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1516 = nothing
            end
            return _t1516
        end
        _t1517 = _t1515(msg)
        fields947 = _t1517
        unwrapped_fields948 = fields947
        write(pp, "(")
        write(pp, "+")
        indent_sexp!(pp)
        newline(pp)
        field949 = unwrapped_fields948[1]
        pretty_term(pp, field949)
        newline(pp)
        field950 = unwrapped_fields948[2]
        pretty_term(pp, field950)
        newline(pp)
        field951 = unwrapped_fields948[3]
        pretty_term(pp, field951)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat958 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat958)
        write(pp, flat958)
        return nothing
    else
        function _t1518(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                _t1519 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1519 = nothing
            end
            return _t1519
        end
        _t1520 = _t1518(msg)
        fields953 = _t1520
        unwrapped_fields954 = fields953
        write(pp, "(")
        write(pp, "-")
        indent_sexp!(pp)
        newline(pp)
        field955 = unwrapped_fields954[1]
        pretty_term(pp, field955)
        newline(pp)
        field956 = unwrapped_fields954[2]
        pretty_term(pp, field956)
        newline(pp)
        field957 = unwrapped_fields954[3]
        pretty_term(pp, field957)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat964 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat964)
        write(pp, flat964)
        return nothing
    else
        function _t1521(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                _t1522 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1522 = nothing
            end
            return _t1522
        end
        _t1523 = _t1521(msg)
        fields959 = _t1523
        unwrapped_fields960 = fields959
        write(pp, "(")
        write(pp, "*")
        indent_sexp!(pp)
        newline(pp)
        field961 = unwrapped_fields960[1]
        pretty_term(pp, field961)
        newline(pp)
        field962 = unwrapped_fields960[2]
        pretty_term(pp, field962)
        newline(pp)
        field963 = unwrapped_fields960[3]
        pretty_term(pp, field963)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat970 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat970)
        write(pp, flat970)
        return nothing
    else
        function _t1524(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                _t1525 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1525 = nothing
            end
            return _t1525
        end
        _t1526 = _t1524(msg)
        fields965 = _t1526
        unwrapped_fields966 = fields965
        write(pp, "(")
        write(pp, "/")
        indent_sexp!(pp)
        newline(pp)
        field967 = unwrapped_fields966[1]
        pretty_term(pp, field967)
        newline(pp)
        field968 = unwrapped_fields966[2]
        pretty_term(pp, field968)
        newline(pp)
        field969 = unwrapped_fields966[3]
        pretty_term(pp, field969)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat975 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat975)
        write(pp, flat975)
        return nothing
    else
        function _t1527(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
                _t1528 = _get_oneof_field(_dollar_dollar, :specialized_value)
            else
                _t1528 = nothing
            end
            return _t1528
        end
        _t1529 = _t1527(msg)
        deconstruct_result973 = _t1529
        if !isnothing(deconstruct_result973)
            unwrapped974 = deconstruct_result973
            pretty_specialized_value(pp, unwrapped974)
        else
            function _t1530(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("term"))
                    _t1531 = _get_oneof_field(_dollar_dollar, :term)
                else
                    _t1531 = nothing
                end
                return _t1531
            end
            _t1532 = _t1530(msg)
            deconstruct_result971 = _t1532
            if !isnothing(deconstruct_result971)
                unwrapped972 = deconstruct_result971
                pretty_term(pp, unwrapped972)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat977 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat977)
        write(pp, flat977)
        return nothing
    else
        fields976 = msg
        write(pp, "#")
        pretty_value(pp, fields976)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat984 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat984)
        write(pp, flat984)
        return nothing
    else
        function _t1533(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1534 = _t1533(msg)
        fields978 = _t1534
        unwrapped_fields979 = fields978
        write(pp, "(")
        write(pp, "relatom")
        indent_sexp!(pp)
        newline(pp)
        field980 = unwrapped_fields979[1]
        pretty_name(pp, field980)
        field981 = unwrapped_fields979[2]
        if !isempty(field981)
            newline(pp)
            for (i1535, elem982) in enumerate(field981)
                i983 = i1535 - 1
                if (i983 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem982)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat989 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat989)
        write(pp, flat989)
        return nothing
    else
        function _t1536(_dollar_dollar)
            return (_dollar_dollar.input, _dollar_dollar.result,)
        end
        _t1537 = _t1536(msg)
        fields985 = _t1537
        unwrapped_fields986 = fields985
        write(pp, "(")
        write(pp, "cast")
        indent_sexp!(pp)
        newline(pp)
        field987 = unwrapped_fields986[1]
        pretty_term(pp, field987)
        newline(pp)
        field988 = unwrapped_fields986[2]
        pretty_term(pp, field988)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat993 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat993)
        write(pp, flat993)
        return nothing
    else
        fields990 = msg
        write(pp, "(")
        write(pp, "attrs")
        indent_sexp!(pp)
        if !isempty(fields990)
            newline(pp)
            for (i1538, elem991) in enumerate(fields990)
                i992 = i1538 - 1
                if (i992 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem991)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1000 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1000)
        write(pp, flat1000)
        return nothing
    else
        function _t1539(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args,)
        end
        _t1540 = _t1539(msg)
        fields994 = _t1540
        unwrapped_fields995 = fields994
        write(pp, "(")
        write(pp, "attribute")
        indent_sexp!(pp)
        newline(pp)
        field996 = unwrapped_fields995[1]
        pretty_name(pp, field996)
        field997 = unwrapped_fields995[2]
        if !isempty(field997)
            newline(pp)
            for (i1541, elem998) in enumerate(field997)
                i999 = i1541 - 1
                if (i999 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem998)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1007 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1007)
        write(pp, flat1007)
        return nothing
    else
        function _t1542(_dollar_dollar)
            return (_dollar_dollar.var"#global", _dollar_dollar.body,)
        end
        _t1543 = _t1542(msg)
        fields1001 = _t1543
        unwrapped_fields1002 = fields1001
        write(pp, "(")
        write(pp, "algorithm")
        indent_sexp!(pp)
        field1003 = unwrapped_fields1002[1]
        if !isempty(field1003)
            newline(pp)
            for (i1544, elem1004) in enumerate(field1003)
                i1005 = i1544 - 1
                if (i1005 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1004)
            end
        end
        newline(pp)
        field1006 = unwrapped_fields1002[2]
        pretty_script(pp, field1006)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1012 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1012)
        write(pp, flat1012)
        return nothing
    else
        function _t1545(_dollar_dollar)
            return _dollar_dollar.constructs
        end
        _t1546 = _t1545(msg)
        fields1008 = _t1546
        unwrapped_fields1009 = fields1008
        write(pp, "(")
        write(pp, "script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1009)
            newline(pp)
            for (i1547, elem1010) in enumerate(unwrapped_fields1009)
                i1011 = i1547 - 1
                if (i1011 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1010)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1017 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1017)
        write(pp, flat1017)
        return nothing
    else
        function _t1548(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("loop"))
                _t1549 = _get_oneof_field(_dollar_dollar, :loop)
            else
                _t1549 = nothing
            end
            return _t1549
        end
        _t1550 = _t1548(msg)
        deconstruct_result1015 = _t1550
        if !isnothing(deconstruct_result1015)
            unwrapped1016 = deconstruct_result1015
            pretty_loop(pp, unwrapped1016)
        else
            function _t1551(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                    _t1552 = _get_oneof_field(_dollar_dollar, :instruction)
                else
                    _t1552 = nothing
                end
                return _t1552
            end
            _t1553 = _t1551(msg)
            deconstruct_result1013 = _t1553
            if !isnothing(deconstruct_result1013)
                unwrapped1014 = deconstruct_result1013
                pretty_instruction(pp, unwrapped1014)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1022 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1022)
        write(pp, flat1022)
        return nothing
    else
        function _t1554(_dollar_dollar)
            return (_dollar_dollar.init, _dollar_dollar.body,)
        end
        _t1555 = _t1554(msg)
        fields1018 = _t1555
        unwrapped_fields1019 = fields1018
        write(pp, "(")
        write(pp, "loop")
        indent_sexp!(pp)
        newline(pp)
        field1020 = unwrapped_fields1019[1]
        pretty_init(pp, field1020)
        newline(pp)
        field1021 = unwrapped_fields1019[2]
        pretty_script(pp, field1021)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1026 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1026)
        write(pp, flat1026)
        return nothing
    else
        fields1023 = msg
        write(pp, "(")
        write(pp, "init")
        indent_sexp!(pp)
        if !isempty(fields1023)
            newline(pp)
            for (i1556, elem1024) in enumerate(fields1023)
                i1025 = i1556 - 1
                if (i1025 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1024)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1037 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1037)
        write(pp, flat1037)
        return nothing
    else
        function _t1557(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("assign"))
                _t1558 = _get_oneof_field(_dollar_dollar, :assign)
            else
                _t1558 = nothing
            end
            return _t1558
        end
        _t1559 = _t1557(msg)
        deconstruct_result1035 = _t1559
        if !isnothing(deconstruct_result1035)
            unwrapped1036 = deconstruct_result1035
            pretty_assign(pp, unwrapped1036)
        else
            function _t1560(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                    _t1561 = _get_oneof_field(_dollar_dollar, :upsert)
                else
                    _t1561 = nothing
                end
                return _t1561
            end
            _t1562 = _t1560(msg)
            deconstruct_result1033 = _t1562
            if !isnothing(deconstruct_result1033)
                unwrapped1034 = deconstruct_result1033
                pretty_upsert(pp, unwrapped1034)
            else
                function _t1563(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("#break"))
                        _t1564 = _get_oneof_field(_dollar_dollar, :var"#break")
                    else
                        _t1564 = nothing
                    end
                    return _t1564
                end
                _t1565 = _t1563(msg)
                deconstruct_result1031 = _t1565
                if !isnothing(deconstruct_result1031)
                    unwrapped1032 = deconstruct_result1031
                    pretty_break(pp, unwrapped1032)
                else
                    function _t1566(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                            _t1567 = _get_oneof_field(_dollar_dollar, :monoid_def)
                        else
                            _t1567 = nothing
                        end
                        return _t1567
                    end
                    _t1568 = _t1566(msg)
                    deconstruct_result1029 = _t1568
                    if !isnothing(deconstruct_result1029)
                        unwrapped1030 = deconstruct_result1029
                        pretty_monoid_def(pp, unwrapped1030)
                    else
                        function _t1569(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                                _t1570 = _get_oneof_field(_dollar_dollar, :monus_def)
                            else
                                _t1570 = nothing
                            end
                            return _t1570
                        end
                        _t1571 = _t1569(msg)
                        deconstruct_result1027 = _t1571
                        if !isnothing(deconstruct_result1027)
                            unwrapped1028 = deconstruct_result1027
                            pretty_monus_def(pp, unwrapped1028)
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
    flat1044 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1044)
        write(pp, flat1044)
        return nothing
    else
        function _t1572(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1573 = _dollar_dollar.attrs
            else
                _t1573 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1573,)
        end
        _t1574 = _t1572(msg)
        fields1038 = _t1574
        unwrapped_fields1039 = fields1038
        write(pp, "(")
        write(pp, "assign")
        indent_sexp!(pp)
        newline(pp)
        field1040 = unwrapped_fields1039[1]
        pretty_relation_id(pp, field1040)
        newline(pp)
        field1041 = unwrapped_fields1039[2]
        pretty_abstraction(pp, field1041)
        field1042 = unwrapped_fields1039[3]
        if !isnothing(field1042)
            newline(pp)
            opt_val1043 = field1042
            pretty_attrs(pp, opt_val1043)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1051 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1051)
        write(pp, flat1051)
        return nothing
    else
        function _t1575(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1576 = _dollar_dollar.attrs
            else
                _t1576 = nothing
            end
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1576,)
        end
        _t1577 = _t1575(msg)
        fields1045 = _t1577
        unwrapped_fields1046 = fields1045
        write(pp, "(")
        write(pp, "upsert")
        indent_sexp!(pp)
        newline(pp)
        field1047 = unwrapped_fields1046[1]
        pretty_relation_id(pp, field1047)
        newline(pp)
        field1048 = unwrapped_fields1046[2]
        pretty_abstraction_with_arity(pp, field1048)
        field1049 = unwrapped_fields1046[3]
        if !isnothing(field1049)
            newline(pp)
            opt_val1050 = field1049
            pretty_attrs(pp, opt_val1050)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1056 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1056)
        write(pp, flat1056)
        return nothing
    else
        function _t1578(_dollar_dollar)
            _t1579 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
            return (_t1579, _dollar_dollar[1].value,)
        end
        _t1580 = _t1578(msg)
        fields1052 = _t1580
        unwrapped_fields1053 = fields1052
        write(pp, "(")
        indent!(pp)
        field1054 = unwrapped_fields1053[1]
        pretty_bindings(pp, field1054)
        newline(pp)
        field1055 = unwrapped_fields1053[2]
        pretty_formula(pp, field1055)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1063 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1063)
        write(pp, flat1063)
        return nothing
    else
        function _t1581(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1582 = _dollar_dollar.attrs
            else
                _t1582 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1582,)
        end
        _t1583 = _t1581(msg)
        fields1057 = _t1583
        unwrapped_fields1058 = fields1057
        write(pp, "(")
        write(pp, "break")
        indent_sexp!(pp)
        newline(pp)
        field1059 = unwrapped_fields1058[1]
        pretty_relation_id(pp, field1059)
        newline(pp)
        field1060 = unwrapped_fields1058[2]
        pretty_abstraction(pp, field1060)
        field1061 = unwrapped_fields1058[3]
        if !isnothing(field1061)
            newline(pp)
            opt_val1062 = field1061
            pretty_attrs(pp, opt_val1062)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1071 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1071)
        write(pp, flat1071)
        return nothing
    else
        function _t1584(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1585 = _dollar_dollar.attrs
            else
                _t1585 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1585,)
        end
        _t1586 = _t1584(msg)
        fields1064 = _t1586
        unwrapped_fields1065 = fields1064
        write(pp, "(")
        write(pp, "monoid")
        indent_sexp!(pp)
        newline(pp)
        field1066 = unwrapped_fields1065[1]
        pretty_monoid(pp, field1066)
        newline(pp)
        field1067 = unwrapped_fields1065[2]
        pretty_relation_id(pp, field1067)
        newline(pp)
        field1068 = unwrapped_fields1065[3]
        pretty_abstraction_with_arity(pp, field1068)
        field1069 = unwrapped_fields1065[4]
        if !isnothing(field1069)
            newline(pp)
            opt_val1070 = field1069
            pretty_attrs(pp, opt_val1070)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1080 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1080)
        write(pp, flat1080)
        return nothing
    else
        function _t1587(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
                _t1588 = _get_oneof_field(_dollar_dollar, :or_monoid)
            else
                _t1588 = nothing
            end
            return _t1588
        end
        _t1589 = _t1587(msg)
        deconstruct_result1078 = _t1589
        if !isnothing(deconstruct_result1078)
            unwrapped1079 = deconstruct_result1078
            pretty_or_monoid(pp, unwrapped1079)
        else
            function _t1590(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                    _t1591 = _get_oneof_field(_dollar_dollar, :min_monoid)
                else
                    _t1591 = nothing
                end
                return _t1591
            end
            _t1592 = _t1590(msg)
            deconstruct_result1076 = _t1592
            if !isnothing(deconstruct_result1076)
                unwrapped1077 = deconstruct_result1076
                pretty_min_monoid(pp, unwrapped1077)
            else
                function _t1593(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                        _t1594 = _get_oneof_field(_dollar_dollar, :max_monoid)
                    else
                        _t1594 = nothing
                    end
                    return _t1594
                end
                _t1595 = _t1593(msg)
                deconstruct_result1074 = _t1595
                if !isnothing(deconstruct_result1074)
                    unwrapped1075 = deconstruct_result1074
                    pretty_max_monoid(pp, unwrapped1075)
                else
                    function _t1596(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                            _t1597 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                        else
                            _t1597 = nothing
                        end
                        return _t1597
                    end
                    _t1598 = _t1596(msg)
                    deconstruct_result1072 = _t1598
                    if !isnothing(deconstruct_result1072)
                        unwrapped1073 = deconstruct_result1072
                        pretty_sum_monoid(pp, unwrapped1073)
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
    fields1081 = msg
    write(pp, "(")
    write(pp, "or")
    write(pp, ")")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1084 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1084)
        write(pp, flat1084)
        return nothing
    else
        function _t1599(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1600 = _t1599(msg)
        fields1082 = _t1600
        unwrapped_fields1083 = fields1082
        write(pp, "(")
        write(pp, "min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1083)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1087 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1087)
        write(pp, flat1087)
        return nothing
    else
        function _t1601(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1602 = _t1601(msg)
        fields1085 = _t1602
        unwrapped_fields1086 = fields1085
        write(pp, "(")
        write(pp, "max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1086)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1090 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1090)
        write(pp, flat1090)
        return nothing
    else
        function _t1603(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1604 = _t1603(msg)
        fields1088 = _t1604
        unwrapped_fields1089 = fields1088
        write(pp, "(")
        write(pp, "sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1089)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1098 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1098)
        write(pp, flat1098)
        return nothing
    else
        function _t1605(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1606 = _dollar_dollar.attrs
            else
                _t1606 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1606,)
        end
        _t1607 = _t1605(msg)
        fields1091 = _t1607
        unwrapped_fields1092 = fields1091
        write(pp, "(")
        write(pp, "monus")
        indent_sexp!(pp)
        newline(pp)
        field1093 = unwrapped_fields1092[1]
        pretty_monoid(pp, field1093)
        newline(pp)
        field1094 = unwrapped_fields1092[2]
        pretty_relation_id(pp, field1094)
        newline(pp)
        field1095 = unwrapped_fields1092[3]
        pretty_abstraction_with_arity(pp, field1095)
        field1096 = unwrapped_fields1092[4]
        if !isnothing(field1096)
            newline(pp)
            opt_val1097 = field1096
            pretty_attrs(pp, opt_val1097)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1105 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1105)
        write(pp, flat1105)
        return nothing
    else
        function _t1608(_dollar_dollar)
            return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        end
        _t1609 = _t1608(msg)
        fields1099 = _t1609
        unwrapped_fields1100 = fields1099
        write(pp, "(")
        write(pp, "functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1101 = unwrapped_fields1100[1]
        pretty_relation_id(pp, field1101)
        newline(pp)
        field1102 = unwrapped_fields1100[2]
        pretty_abstraction(pp, field1102)
        newline(pp)
        field1103 = unwrapped_fields1100[3]
        pretty_functional_dependency_keys(pp, field1103)
        newline(pp)
        field1104 = unwrapped_fields1100[4]
        pretty_functional_dependency_values(pp, field1104)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1109 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1109)
        write(pp, flat1109)
        return nothing
    else
        fields1106 = msg
        write(pp, "(")
        write(pp, "keys")
        indent_sexp!(pp)
        if !isempty(fields1106)
            newline(pp)
            for (i1610, elem1107) in enumerate(fields1106)
                i1108 = i1610 - 1
                if (i1108 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1107)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1113 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1113)
        write(pp, flat1113)
        return nothing
    else
        fields1110 = msg
        write(pp, "(")
        write(pp, "values")
        indent_sexp!(pp)
        if !isempty(fields1110)
            newline(pp)
            for (i1611, elem1111) in enumerate(fields1110)
                i1112 = i1611 - 1
                if (i1112 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1111)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1120 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1120)
        write(pp, flat1120)
        return nothing
    else
        function _t1612(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("rel_edb"))
                _t1613 = _get_oneof_field(_dollar_dollar, :rel_edb)
            else
                _t1613 = nothing
            end
            return _t1613
        end
        _t1614 = _t1612(msg)
        deconstruct_result1118 = _t1614
        if !isnothing(deconstruct_result1118)
            unwrapped1119 = deconstruct_result1118
            pretty_rel_edb(pp, unwrapped1119)
        else
            function _t1615(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                    _t1616 = _get_oneof_field(_dollar_dollar, :betree_relation)
                else
                    _t1616 = nothing
                end
                return _t1616
            end
            _t1617 = _t1615(msg)
            deconstruct_result1116 = _t1617
            if !isnothing(deconstruct_result1116)
                unwrapped1117 = deconstruct_result1116
                pretty_betree_relation(pp, unwrapped1117)
            else
                function _t1618(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                        _t1619 = _get_oneof_field(_dollar_dollar, :csv_data)
                    else
                        _t1619 = nothing
                    end
                    return _t1619
                end
                _t1620 = _t1618(msg)
                deconstruct_result1114 = _t1620
                if !isnothing(deconstruct_result1114)
                    unwrapped1115 = deconstruct_result1114
                    pretty_csv_data(pp, unwrapped1115)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_rel_edb(pp::PrettyPrinter, msg::Proto.RelEDB)
    flat1126 = try_flat(pp, msg, pretty_rel_edb)
    if !isnothing(flat1126)
        write(pp, flat1126)
        return nothing
    else
        function _t1621(_dollar_dollar)
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        end
        _t1622 = _t1621(msg)
        fields1121 = _t1622
        unwrapped_fields1122 = fields1121
        write(pp, "(")
        write(pp, "rel_edb")
        indent_sexp!(pp)
        newline(pp)
        field1123 = unwrapped_fields1122[1]
        pretty_relation_id(pp, field1123)
        newline(pp)
        field1124 = unwrapped_fields1122[2]
        pretty_rel_edb_path(pp, field1124)
        newline(pp)
        field1125 = unwrapped_fields1122[3]
        pretty_rel_edb_types(pp, field1125)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1130 = try_flat(pp, msg, pretty_rel_edb_path)
    if !isnothing(flat1130)
        write(pp, flat1130)
        return nothing
    else
        fields1127 = msg
        write(pp, "[")
        indent!(pp)
        for (i1623, elem1128) in enumerate(fields1127)
            i1129 = i1623 - 1
            if (i1129 > 0)
                newline(pp)
            end
            write(pp, format_string(pp, elem1128))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_rel_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1134 = try_flat(pp, msg, pretty_rel_edb_types)
    if !isnothing(flat1134)
        write(pp, flat1134)
        return nothing
    else
        fields1131 = msg
        write(pp, "[")
        indent!(pp)
        for (i1624, elem1132) in enumerate(fields1131)
            i1133 = i1624 - 1
            if (i1133 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1132)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1139 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1139)
        write(pp, flat1139)
        return nothing
    else
        function _t1625(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        end
        _t1626 = _t1625(msg)
        fields1135 = _t1626
        unwrapped_fields1136 = fields1135
        write(pp, "(")
        write(pp, "betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1137 = unwrapped_fields1136[1]
        pretty_relation_id(pp, field1137)
        newline(pp)
        field1138 = unwrapped_fields1136[2]
        pretty_betree_info(pp, field1138)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1145 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1145)
        write(pp, flat1145)
        return nothing
    else
        function _t1627(_dollar_dollar)
            _t1628 = deconstruct_betree_info_config(pp, _dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1628,)
        end
        _t1629 = _t1627(msg)
        fields1140 = _t1629
        unwrapped_fields1141 = fields1140
        write(pp, "(")
        write(pp, "betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1142 = unwrapped_fields1141[1]
        pretty_betree_info_key_types(pp, field1142)
        newline(pp)
        field1143 = unwrapped_fields1141[2]
        pretty_betree_info_value_types(pp, field1143)
        newline(pp)
        field1144 = unwrapped_fields1141[3]
        pretty_config_dict(pp, field1144)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1149 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1149)
        write(pp, flat1149)
        return nothing
    else
        fields1146 = msg
        write(pp, "(")
        write(pp, "key_types")
        indent_sexp!(pp)
        if !isempty(fields1146)
            newline(pp)
            for (i1630, elem1147) in enumerate(fields1146)
                i1148 = i1630 - 1
                if (i1148 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1147)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1153 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1153)
        write(pp, flat1153)
        return nothing
    else
        fields1150 = msg
        write(pp, "(")
        write(pp, "value_types")
        indent_sexp!(pp)
        if !isempty(fields1150)
            newline(pp)
            for (i1631, elem1151) in enumerate(fields1150)
                i1152 = i1631 - 1
                if (i1152 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1151)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1160 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1160)
        write(pp, flat1160)
        return nothing
    else
        function _t1632(_dollar_dollar)
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        end
        _t1633 = _t1632(msg)
        fields1154 = _t1633
        unwrapped_fields1155 = fields1154
        write(pp, "(")
        write(pp, "csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1156 = unwrapped_fields1155[1]
        pretty_csvlocator(pp, field1156)
        newline(pp)
        field1157 = unwrapped_fields1155[2]
        pretty_csv_config(pp, field1157)
        newline(pp)
        field1158 = unwrapped_fields1155[3]
        pretty_csv_columns(pp, field1158)
        newline(pp)
        field1159 = unwrapped_fields1155[4]
        pretty_csv_asof(pp, field1159)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1167 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        function _t1634(_dollar_dollar)
            if !isempty(_dollar_dollar.paths)
                _t1635 = _dollar_dollar.paths
            else
                _t1635 = nothing
            end
            if String(copy(_dollar_dollar.inline_data)) != ""
                _t1636 = String(copy(_dollar_dollar.inline_data))
            else
                _t1636 = nothing
            end
            return (_t1635, _t1636,)
        end
        _t1637 = _t1634(msg)
        fields1161 = _t1637
        unwrapped_fields1162 = fields1161
        write(pp, "(")
        write(pp, "csv_locator")
        indent_sexp!(pp)
        field1163 = unwrapped_fields1162[1]
        if !isnothing(field1163)
            newline(pp)
            opt_val1164 = field1163
            pretty_csv_locator_paths(pp, opt_val1164)
        end
        field1165 = unwrapped_fields1162[2]
        if !isnothing(field1165)
            newline(pp)
            opt_val1166 = field1165
            pretty_csv_locator_inline_data(pp, opt_val1166)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1171 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1171)
        write(pp, flat1171)
        return nothing
    else
        fields1168 = msg
        write(pp, "(")
        write(pp, "paths")
        indent_sexp!(pp)
        if !isempty(fields1168)
            newline(pp)
            for (i1638, elem1169) in enumerate(fields1168)
                i1170 = i1638 - 1
                if (i1170 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1169))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1173 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1173)
        write(pp, flat1173)
        return nothing
    else
        fields1172 = msg
        write(pp, "(")
        write(pp, "inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1172))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1176 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1176)
        write(pp, flat1176)
        return nothing
    else
        function _t1639(_dollar_dollar)
            _t1640 = deconstruct_csv_config(pp, _dollar_dollar)
            return _t1640
        end
        _t1641 = _t1639(msg)
        fields1174 = _t1641
        unwrapped_fields1175 = fields1174
        write(pp, "(")
        write(pp, "csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1175)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.CSVColumn})
    flat1180 = try_flat(pp, msg, pretty_csv_columns)
    if !isnothing(flat1180)
        write(pp, flat1180)
        return nothing
    else
        fields1177 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1177)
            newline(pp)
            for (i1642, elem1178) in enumerate(fields1177)
                i1179 = i1642 - 1
                if (i1179 > 0)
                    newline(pp)
                end
                pretty_csv_column(pp, elem1178)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_column(pp::PrettyPrinter, msg::Proto.CSVColumn)
    flat1188 = try_flat(pp, msg, pretty_csv_column)
    if !isnothing(flat1188)
        write(pp, flat1188)
        return nothing
    else
        function _t1643(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        end
        _t1644 = _t1643(msg)
        fields1181 = _t1644
        unwrapped_fields1182 = fields1181
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1183 = unwrapped_fields1182[1]
        write(pp, format_string(pp, field1183))
        newline(pp)
        field1184 = unwrapped_fields1182[2]
        pretty_relation_id(pp, field1184)
        newline(pp)
        write(pp, "[")
        field1185 = unwrapped_fields1182[3]
        for (i1645, elem1186) in enumerate(field1185)
            i1187 = i1645 - 1
            if (i1187 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1186)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1190 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1190)
        write(pp, flat1190)
        return nothing
    else
        fields1189 = msg
        write(pp, "(")
        write(pp, "asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1189))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1193 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1193)
        write(pp, flat1193)
        return nothing
    else
        function _t1646(_dollar_dollar)
            return _dollar_dollar.fragment_id
        end
        _t1647 = _t1646(msg)
        fields1191 = _t1647
        unwrapped_fields1192 = fields1191
        write(pp, "(")
        write(pp, "undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1192)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1198 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1198)
        write(pp, flat1198)
        return nothing
    else
        function _t1648(_dollar_dollar)
            return _dollar_dollar.relations
        end
        _t1649 = _t1648(msg)
        fields1194 = _t1649
        unwrapped_fields1195 = fields1194
        write(pp, "(")
        write(pp, "context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1195)
            newline(pp)
            for (i1650, elem1196) in enumerate(unwrapped_fields1195)
                i1197 = i1650 - 1
                if (i1197 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1196)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1203 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1203)
        write(pp, flat1203)
        return nothing
    else
        function _t1651(_dollar_dollar)
            return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        end
        _t1652 = _t1651(msg)
        fields1199 = _t1652
        unwrapped_fields1200 = fields1199
        write(pp, "(")
        write(pp, "snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1201 = unwrapped_fields1200[1]
        pretty_rel_edb_path(pp, field1201)
        newline(pp)
        field1202 = unwrapped_fields1200[2]
        pretty_relation_id(pp, field1202)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1207 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1207)
        write(pp, flat1207)
        return nothing
    else
        fields1204 = msg
        write(pp, "(")
        write(pp, "reads")
        indent_sexp!(pp)
        if !isempty(fields1204)
            newline(pp)
            for (i1653, elem1205) in enumerate(fields1204)
                i1206 = i1653 - 1
                if (i1206 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1205)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1218 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1218)
        write(pp, flat1218)
        return nothing
    else
        function _t1654(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("demand"))
                _t1655 = _get_oneof_field(_dollar_dollar, :demand)
            else
                _t1655 = nothing
            end
            return _t1655
        end
        _t1656 = _t1654(msg)
        deconstruct_result1216 = _t1656
        if !isnothing(deconstruct_result1216)
            unwrapped1217 = deconstruct_result1216
            pretty_demand(pp, unwrapped1217)
        else
            function _t1657(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("output"))
                    _t1658 = _get_oneof_field(_dollar_dollar, :output)
                else
                    _t1658 = nothing
                end
                return _t1658
            end
            _t1659 = _t1657(msg)
            deconstruct_result1214 = _t1659
            if !isnothing(deconstruct_result1214)
                unwrapped1215 = deconstruct_result1214
                pretty_output(pp, unwrapped1215)
            else
                function _t1660(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                        _t1661 = _get_oneof_field(_dollar_dollar, :what_if)
                    else
                        _t1661 = nothing
                    end
                    return _t1661
                end
                _t1662 = _t1660(msg)
                deconstruct_result1212 = _t1662
                if !isnothing(deconstruct_result1212)
                    unwrapped1213 = deconstruct_result1212
                    pretty_what_if(pp, unwrapped1213)
                else
                    function _t1663(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("abort"))
                            _t1664 = _get_oneof_field(_dollar_dollar, :abort)
                        else
                            _t1664 = nothing
                        end
                        return _t1664
                    end
                    _t1665 = _t1663(msg)
                    deconstruct_result1210 = _t1665
                    if !isnothing(deconstruct_result1210)
                        unwrapped1211 = deconstruct_result1210
                        pretty_abort(pp, unwrapped1211)
                    else
                        function _t1666(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("#export"))
                                _t1667 = _get_oneof_field(_dollar_dollar, :var"#export")
                            else
                                _t1667 = nothing
                            end
                            return _t1667
                        end
                        _t1668 = _t1666(msg)
                        deconstruct_result1208 = _t1668
                        if !isnothing(deconstruct_result1208)
                            unwrapped1209 = deconstruct_result1208
                            pretty_export(pp, unwrapped1209)
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
    flat1221 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1221)
        write(pp, flat1221)
        return nothing
    else
        function _t1669(_dollar_dollar)
            return _dollar_dollar.relation_id
        end
        _t1670 = _t1669(msg)
        fields1219 = _t1670
        unwrapped_fields1220 = fields1219
        write(pp, "(")
        write(pp, "demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1220)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1226 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1226)
        write(pp, flat1226)
        return nothing
    else
        function _t1671(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        end
        _t1672 = _t1671(msg)
        fields1222 = _t1672
        unwrapped_fields1223 = fields1222
        write(pp, "(")
        write(pp, "output")
        indent_sexp!(pp)
        newline(pp)
        field1224 = unwrapped_fields1223[1]
        pretty_name(pp, field1224)
        newline(pp)
        field1225 = unwrapped_fields1223[2]
        pretty_relation_id(pp, field1225)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1231 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1231)
        write(pp, flat1231)
        return nothing
    else
        function _t1673(_dollar_dollar)
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        end
        _t1674 = _t1673(msg)
        fields1227 = _t1674
        unwrapped_fields1228 = fields1227
        write(pp, "(")
        write(pp, "what_if")
        indent_sexp!(pp)
        newline(pp)
        field1229 = unwrapped_fields1228[1]
        pretty_name(pp, field1229)
        newline(pp)
        field1230 = unwrapped_fields1228[2]
        pretty_epoch(pp, field1230)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1237 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1237)
        write(pp, flat1237)
        return nothing
    else
        function _t1675(_dollar_dollar)
            if _dollar_dollar.name != "abort"
                _t1676 = _dollar_dollar.name
            else
                _t1676 = nothing
            end
            return (_t1676, _dollar_dollar.relation_id,)
        end
        _t1677 = _t1675(msg)
        fields1232 = _t1677
        unwrapped_fields1233 = fields1232
        write(pp, "(")
        write(pp, "abort")
        indent_sexp!(pp)
        field1234 = unwrapped_fields1233[1]
        if !isnothing(field1234)
            newline(pp)
            opt_val1235 = field1234
            pretty_name(pp, opt_val1235)
        end
        newline(pp)
        field1236 = unwrapped_fields1233[2]
        pretty_relation_id(pp, field1236)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1240 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1240)
        write(pp, flat1240)
        return nothing
    else
        function _t1678(_dollar_dollar)
            return _get_oneof_field(_dollar_dollar, :csv_config)
        end
        _t1679 = _t1678(msg)
        fields1238 = _t1679
        unwrapped_fields1239 = fields1238
        write(pp, "(")
        write(pp, "export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1239)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1246 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1246)
        write(pp, flat1246)
        return nothing
    else
        function _t1680(_dollar_dollar)
            _t1681 = deconstruct_export_csv_config(pp, _dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1681,)
        end
        _t1682 = _t1680(msg)
        fields1241 = _t1682
        unwrapped_fields1242 = fields1241
        write(pp, "(")
        write(pp, "export_csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1243 = unwrapped_fields1242[1]
        pretty_export_csv_path(pp, field1243)
        newline(pp)
        field1244 = unwrapped_fields1242[2]
        pretty_export_csv_columns(pp, field1244)
        newline(pp)
        field1245 = unwrapped_fields1242[3]
        pretty_config_dict(pp, field1245)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1248 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1248)
        write(pp, flat1248)
        return nothing
    else
        fields1247 = msg
        write(pp, "(")
        write(pp, "path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1247))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1252 = try_flat(pp, msg, pretty_export_csv_columns)
    if !isnothing(flat1252)
        write(pp, flat1252)
        return nothing
    else
        fields1249 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1249)
            newline(pp)
            for (i1683, elem1250) in enumerate(fields1249)
                i1251 = i1683 - 1
                if (i1251 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1250)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_column(pp::PrettyPrinter, msg::Proto.ExportCSVColumn)
    flat1257 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1257)
        write(pp, flat1257)
        return nothing
    else
        function _t1684(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        end
        _t1685 = _t1684(msg)
        fields1253 = _t1685
        unwrapped_fields1254 = fields1253
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1255 = unwrapped_fields1254[1]
        write(pp, format_string(pp, field1255))
        newline(pp)
        field1256 = unwrapped_fields1254[2]
        pretty_relation_id(pp, field1256)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1723, _rid) in enumerate(msg.ids)
        _idx = i1723 - 1
        newline(pp)
        write(pp, "(")
        _t1724 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1724)
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
    write(pp, ":keys ")
    write(pp, "(")
    for (i1725, _elem) in enumerate(msg.keys)
        _idx = i1725 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values ")
    write(pp, "(")
    for (i1726, _elem) in enumerate(msg.values)
        _idx = i1726 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    write(pp, ")")
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
_pprint_dispatch(pp::PrettyPrinter, x::Proto.RelEDB) = pretty_rel_edb(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{String}) = pretty_rel_edb_path(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.var"#Type"}) = pretty_rel_edb_types(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeRelation) = pretty_betree_relation(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeInfo) = pretty_betree_info(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVData) = pretty_csv_data(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVLocator) = pretty_csvlocator(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVConfig) = pretty_csv_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.CSVColumn}) = pretty_csv_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.CSVColumn) = pretty_csv_column(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Undefine) = pretty_undefine(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Context) = pretty_context(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Snapshot) = pretty_snapshot(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.Read}) = pretty_epoch_reads(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Read) = pretty_read(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Demand) = pretty_demand(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Output) = pretty_output(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.WhatIf) = pretty_what_if(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Abort) = pretty_abort(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Export) = pretty_export(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportCSVConfig) = pretty_export_csv_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.ExportCSVColumn}) = pretty_export_csv_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportCSVColumn) = pretty_export_csv_column(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DebugInfo) = pretty_debug_info(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeConfig) = pretty_be_tree_config(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.BeTreeLocator) = pretty_be_tree_locator(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.DecimalValue) = pretty_decimal_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.FunctionalDependency) = pretty_functional_dependency(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.Int128Value) = pretty_int128_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.MissingValue) = pretty_missing_value(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.UInt128Value) = pretty_u_int128_value(pp, x)
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
