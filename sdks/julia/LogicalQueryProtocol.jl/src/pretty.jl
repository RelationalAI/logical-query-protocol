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
    _t1732 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1732
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1733 = Proto.Value(value=OneOf(:int_value, v))
    return _t1733
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1734 = Proto.Value(value=OneOf(:float_value, v))
    return _t1734
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1735 = Proto.Value(value=OneOf(:string_value, v))
    return _t1735
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1736 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1736
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1737 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1737
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1738 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1738,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1739 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1739,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1740 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1740,))
            end
        end
    end
    _t1741 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1741,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1742 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1742,))
    _t1743 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1743,))
    if msg.new_line != ""
        _t1744 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1744,))
    end
    _t1745 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1745,))
    _t1746 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1746,))
    _t1747 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1747,))
    if msg.comment != ""
        _t1748 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1748,))
    end
    for missing_string in msg.missing_strings
        _t1749 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1749,))
    end
    _t1750 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1750,))
    _t1751 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1751,))
    _t1752 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1752,))
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1753 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1753,))
    _t1754 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1754,))
    _t1755 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1755,))
    _t1756 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1756,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1757 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1757,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1758 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1758,))
        end
    end
    _t1759 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1759,))
    _t1760 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1760,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1761 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1761,))
    end
    if !isnothing(msg.compression)
        _t1762 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1762,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1763 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1763,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1764 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1764,))
    end
    if !isnothing(msg.syntax_delim)
        _t1765 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1765,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1766 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1766,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1767 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1767,))
    end
    return sort(result)
end

function deconstruct_csv_column_tail(pp::PrettyPrinter, col::Proto.CSVColumn)::Union{Nothing, Tuple{Union{Nothing, Proto.RelationId}, Vector{Proto.var"#Type"}}}
    if (_has_proto_field(col, Symbol("target_id")) || !isempty(col.types))
        return (col.target_id, col.types,)
    else
        _t1768 = nothing
    end
    return nothing
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
        _t1769 = nothing
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
    flat654 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat654)
        write(pp, flat654)
        return nothing
    else
        function _t1290(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("configure"))
                _t1291 = _dollar_dollar.configure
            else
                _t1291 = nothing
            end
            if _has_proto_field(_dollar_dollar, Symbol("sync"))
                _t1292 = _dollar_dollar.sync
            else
                _t1292 = nothing
            end
            return (_t1291, _t1292, _dollar_dollar.epochs,)
        end
        _t1293 = _t1290(msg)
        fields645 = _t1293
        unwrapped_fields646 = fields645
        write(pp, "(")
        write(pp, "transaction")
        indent_sexp!(pp)
        field647 = unwrapped_fields646[1]
        if !isnothing(field647)
            newline(pp)
            opt_val648 = field647
            pretty_configure(pp, opt_val648)
        end
        field649 = unwrapped_fields646[2]
        if !isnothing(field649)
            newline(pp)
            opt_val650 = field649
            pretty_sync(pp, opt_val650)
        end
        field651 = unwrapped_fields646[3]
        if !isempty(field651)
            newline(pp)
            for (i1294, elem652) in enumerate(field651)
                i653 = i1294 - 1
                if (i653 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem652)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat657 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat657)
        write(pp, flat657)
        return nothing
    else
        function _t1295(_dollar_dollar)
            _t1296 = deconstruct_configure(pp, _dollar_dollar)
            return _t1296
        end
        _t1297 = _t1295(msg)
        fields655 = _t1297
        unwrapped_fields656 = fields655
        write(pp, "(")
        write(pp, "configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields656)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat661 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat661)
        write(pp, flat661)
        return nothing
    else
        fields658 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields658)
            newline(pp)
            for (i1298, elem659) in enumerate(fields658)
                i660 = i1298 - 1
                if (i660 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem659)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat666 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat666)
        write(pp, flat666)
        return nothing
    else
        function _t1299(_dollar_dollar)
            return (_dollar_dollar[1], _dollar_dollar[2],)
        end
        _t1300 = _t1299(msg)
        fields662 = _t1300
        unwrapped_fields663 = fields662
        write(pp, ":")
        field664 = unwrapped_fields663[1]
        write(pp, field664)
        write(pp, " ")
        field665 = unwrapped_fields663[2]
        pretty_value(pp, field665)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat686 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat686)
        write(pp, flat686)
        return nothing
    else
        function _t1301(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("date_value"))
                _t1302 = _get_oneof_field(_dollar_dollar, :date_value)
            else
                _t1302 = nothing
            end
            return _t1302
        end
        _t1303 = _t1301(msg)
        deconstruct_result684 = _t1303
        if !isnothing(deconstruct_result684)
            unwrapped685 = deconstruct_result684
            pretty_date(pp, unwrapped685)
        else
            function _t1304(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                    _t1305 = _get_oneof_field(_dollar_dollar, :datetime_value)
                else
                    _t1305 = nothing
                end
                return _t1305
            end
            _t1306 = _t1304(msg)
            deconstruct_result682 = _t1306
            if !isnothing(deconstruct_result682)
                unwrapped683 = deconstruct_result682
                pretty_datetime(pp, unwrapped683)
            else
                function _t1307(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                        _t1308 = _get_oneof_field(_dollar_dollar, :string_value)
                    else
                        _t1308 = nothing
                    end
                    return _t1308
                end
                _t1309 = _t1307(msg)
                deconstruct_result680 = _t1309
                if !isnothing(deconstruct_result680)
                    unwrapped681 = deconstruct_result680
                    write(pp, format_string(pp, unwrapped681))
                else
                    function _t1310(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1311 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1311 = nothing
                        end
                        return _t1311
                    end
                    _t1312 = _t1310(msg)
                    deconstruct_result678 = _t1312
                    if !isnothing(deconstruct_result678)
                        unwrapped679 = deconstruct_result678
                        write(pp, format_int(pp, unwrapped679))
                    else
                        function _t1313(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                _t1314 = _get_oneof_field(_dollar_dollar, :float_value)
                            else
                                _t1314 = nothing
                            end
                            return _t1314
                        end
                        _t1315 = _t1313(msg)
                        deconstruct_result676 = _t1315
                        if !isnothing(deconstruct_result676)
                            unwrapped677 = deconstruct_result676
                            write(pp, format_float(pp, unwrapped677))
                        else
                            function _t1316(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                    _t1317 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                else
                                    _t1317 = nothing
                                end
                                return _t1317
                            end
                            _t1318 = _t1316(msg)
                            deconstruct_result674 = _t1318
                            if !isnothing(deconstruct_result674)
                                unwrapped675 = deconstruct_result674
                                write(pp, format_uint128(pp, unwrapped675))
                            else
                                function _t1319(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                        _t1320 = _get_oneof_field(_dollar_dollar, :int128_value)
                                    else
                                        _t1320 = nothing
                                    end
                                    return _t1320
                                end
                                _t1321 = _t1319(msg)
                                deconstruct_result672 = _t1321
                                if !isnothing(deconstruct_result672)
                                    unwrapped673 = deconstruct_result672
                                    write(pp, format_int128(pp, unwrapped673))
                                else
                                    function _t1322(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                            _t1323 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                        else
                                            _t1323 = nothing
                                        end
                                        return _t1323
                                    end
                                    _t1324 = _t1322(msg)
                                    deconstruct_result670 = _t1324
                                    if !isnothing(deconstruct_result670)
                                        unwrapped671 = deconstruct_result670
                                        write(pp, format_decimal(pp, unwrapped671))
                                    else
                                        function _t1325(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                _t1326 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                            else
                                                _t1326 = nothing
                                            end
                                            return _t1326
                                        end
                                        _t1327 = _t1325(msg)
                                        deconstruct_result668 = _t1327
                                        if !isnothing(deconstruct_result668)
                                            unwrapped669 = deconstruct_result668
                                            pretty_boolean_value(pp, unwrapped669)
                                        else
                                            fields667 = msg
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
    flat692 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat692)
        write(pp, flat692)
        return nothing
    else
        function _t1328(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        end
        _t1329 = _t1328(msg)
        fields687 = _t1329
        unwrapped_fields688 = fields687
        write(pp, "(")
        write(pp, "date")
        indent_sexp!(pp)
        newline(pp)
        field689 = unwrapped_fields688[1]
        write(pp, format_int(pp, field689))
        newline(pp)
        field690 = unwrapped_fields688[2]
        write(pp, format_int(pp, field690))
        newline(pp)
        field691 = unwrapped_fields688[3]
        write(pp, format_int(pp, field691))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat703 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat703)
        write(pp, flat703)
        return nothing
    else
        function _t1330(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        end
        _t1331 = _t1330(msg)
        fields693 = _t1331
        unwrapped_fields694 = fields693
        write(pp, "(")
        write(pp, "datetime")
        indent_sexp!(pp)
        newline(pp)
        field695 = unwrapped_fields694[1]
        write(pp, format_int(pp, field695))
        newline(pp)
        field696 = unwrapped_fields694[2]
        write(pp, format_int(pp, field696))
        newline(pp)
        field697 = unwrapped_fields694[3]
        write(pp, format_int(pp, field697))
        newline(pp)
        field698 = unwrapped_fields694[4]
        write(pp, format_int(pp, field698))
        newline(pp)
        field699 = unwrapped_fields694[5]
        write(pp, format_int(pp, field699))
        newline(pp)
        field700 = unwrapped_fields694[6]
        write(pp, format_int(pp, field700))
        field701 = unwrapped_fields694[7]
        if !isnothing(field701)
            newline(pp)
            opt_val702 = field701
            write(pp, format_int(pp, opt_val702))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    function _t1332(_dollar_dollar)
        if _dollar_dollar
            _t1333 = ()
        else
            _t1333 = nothing
        end
        return _t1333
    end
    _t1334 = _t1332(msg)
    deconstruct_result706 = _t1334
    if !isnothing(deconstruct_result706)
        unwrapped707 = deconstruct_result706
        write(pp, "true")
    else
        function _t1335(_dollar_dollar)
            if !_dollar_dollar
                _t1336 = ()
            else
                _t1336 = nothing
            end
            return _t1336
        end
        _t1337 = _t1335(msg)
        deconstruct_result704 = _t1337
        if !isnothing(deconstruct_result704)
            unwrapped705 = deconstruct_result704
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat712 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat712)
        write(pp, flat712)
        return nothing
    else
        function _t1338(_dollar_dollar)
            return _dollar_dollar.fragments
        end
        _t1339 = _t1338(msg)
        fields708 = _t1339
        unwrapped_fields709 = fields708
        write(pp, "(")
        write(pp, "sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields709)
            newline(pp)
            for (i1340, elem710) in enumerate(unwrapped_fields709)
                i711 = i1340 - 1
                if (i711 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem710)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat715 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat715)
        write(pp, flat715)
        return nothing
    else
        function _t1341(_dollar_dollar)
            return fragment_id_to_string(pp, _dollar_dollar)
        end
        _t1342 = _t1341(msg)
        fields713 = _t1342
        unwrapped_fields714 = fields713
        write(pp, ":")
        write(pp, unwrapped_fields714)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat722 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat722)
        write(pp, flat722)
        return nothing
    else
        function _t1343(_dollar_dollar)
            if !isempty(_dollar_dollar.writes)
                _t1344 = _dollar_dollar.writes
            else
                _t1344 = nothing
            end
            if !isempty(_dollar_dollar.reads)
                _t1345 = _dollar_dollar.reads
            else
                _t1345 = nothing
            end
            return (_t1344, _t1345,)
        end
        _t1346 = _t1343(msg)
        fields716 = _t1346
        unwrapped_fields717 = fields716
        write(pp, "(")
        write(pp, "epoch")
        indent_sexp!(pp)
        field718 = unwrapped_fields717[1]
        if !isnothing(field718)
            newline(pp)
            opt_val719 = field718
            pretty_epoch_writes(pp, opt_val719)
        end
        field720 = unwrapped_fields717[2]
        if !isnothing(field720)
            newline(pp)
            opt_val721 = field720
            pretty_epoch_reads(pp, opt_val721)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat726 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat726)
        write(pp, flat726)
        return nothing
    else
        fields723 = msg
        write(pp, "(")
        write(pp, "writes")
        indent_sexp!(pp)
        if !isempty(fields723)
            newline(pp)
            for (i1347, elem724) in enumerate(fields723)
                i725 = i1347 - 1
                if (i725 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem724)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat735 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat735)
        write(pp, flat735)
        return nothing
    else
        function _t1348(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("define"))
                _t1349 = _get_oneof_field(_dollar_dollar, :define)
            else
                _t1349 = nothing
            end
            return _t1349
        end
        _t1350 = _t1348(msg)
        deconstruct_result733 = _t1350
        if !isnothing(deconstruct_result733)
            unwrapped734 = deconstruct_result733
            pretty_define(pp, unwrapped734)
        else
            function _t1351(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                    _t1352 = _get_oneof_field(_dollar_dollar, :undefine)
                else
                    _t1352 = nothing
                end
                return _t1352
            end
            _t1353 = _t1351(msg)
            deconstruct_result731 = _t1353
            if !isnothing(deconstruct_result731)
                unwrapped732 = deconstruct_result731
                pretty_undefine(pp, unwrapped732)
            else
                function _t1354(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("context"))
                        _t1355 = _get_oneof_field(_dollar_dollar, :context)
                    else
                        _t1355 = nothing
                    end
                    return _t1355
                end
                _t1356 = _t1354(msg)
                deconstruct_result729 = _t1356
                if !isnothing(deconstruct_result729)
                    unwrapped730 = deconstruct_result729
                    pretty_context(pp, unwrapped730)
                else
                    function _t1357(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                            _t1358 = _get_oneof_field(_dollar_dollar, :snapshot)
                        else
                            _t1358 = nothing
                        end
                        return _t1358
                    end
                    _t1359 = _t1357(msg)
                    deconstruct_result727 = _t1359
                    if !isnothing(deconstruct_result727)
                        unwrapped728 = deconstruct_result727
                        pretty_snapshot(pp, unwrapped728)
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
    flat738 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat738)
        write(pp, flat738)
        return nothing
    else
        function _t1360(_dollar_dollar)
            return _dollar_dollar.fragment
        end
        _t1361 = _t1360(msg)
        fields736 = _t1361
        unwrapped_fields737 = fields736
        write(pp, "(")
        write(pp, "define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields737)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat745 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat745)
        write(pp, flat745)
        return nothing
    else
        function _t1362(_dollar_dollar)
            start_pretty_fragment(pp, _dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        end
        _t1363 = _t1362(msg)
        fields739 = _t1363
        unwrapped_fields740 = fields739
        write(pp, "(")
        write(pp, "fragment")
        indent_sexp!(pp)
        newline(pp)
        field741 = unwrapped_fields740[1]
        pretty_new_fragment_id(pp, field741)
        field742 = unwrapped_fields740[2]
        if !isempty(field742)
            newline(pp)
            for (i1364, elem743) in enumerate(field742)
                i744 = i1364 - 1
                if (i744 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem743)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat747 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat747)
        write(pp, flat747)
        return nothing
    else
        fields746 = msg
        pretty_fragment_id(pp, fields746)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat756 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat756)
        write(pp, flat756)
        return nothing
    else
        function _t1365(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("def"))
                _t1366 = _get_oneof_field(_dollar_dollar, :def)
            else
                _t1366 = nothing
            end
            return _t1366
        end
        _t1367 = _t1365(msg)
        deconstruct_result754 = _t1367
        if !isnothing(deconstruct_result754)
            unwrapped755 = deconstruct_result754
            pretty_def(pp, unwrapped755)
        else
            function _t1368(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                    _t1369 = _get_oneof_field(_dollar_dollar, :algorithm)
                else
                    _t1369 = nothing
                end
                return _t1369
            end
            _t1370 = _t1368(msg)
            deconstruct_result752 = _t1370
            if !isnothing(deconstruct_result752)
                unwrapped753 = deconstruct_result752
                pretty_algorithm(pp, unwrapped753)
            else
                function _t1371(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                        _t1372 = _get_oneof_field(_dollar_dollar, :constraint)
                    else
                        _t1372 = nothing
                    end
                    return _t1372
                end
                _t1373 = _t1371(msg)
                deconstruct_result750 = _t1373
                if !isnothing(deconstruct_result750)
                    unwrapped751 = deconstruct_result750
                    pretty_constraint(pp, unwrapped751)
                else
                    function _t1374(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("data"))
                            _t1375 = _get_oneof_field(_dollar_dollar, :data)
                        else
                            _t1375 = nothing
                        end
                        return _t1375
                    end
                    _t1376 = _t1374(msg)
                    deconstruct_result748 = _t1376
                    if !isnothing(deconstruct_result748)
                        unwrapped749 = deconstruct_result748
                        pretty_data(pp, unwrapped749)
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
    flat763 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat763)
        write(pp, flat763)
        return nothing
    else
        function _t1377(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1378 = _dollar_dollar.attrs
            else
                _t1378 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1378,)
        end
        _t1379 = _t1377(msg)
        fields757 = _t1379
        unwrapped_fields758 = fields757
        write(pp, "(")
        write(pp, "def")
        indent_sexp!(pp)
        newline(pp)
        field759 = unwrapped_fields758[1]
        pretty_relation_id(pp, field759)
        newline(pp)
        field760 = unwrapped_fields758[2]
        pretty_abstraction(pp, field760)
        field761 = unwrapped_fields758[3]
        if !isnothing(field761)
            newline(pp)
            opt_val762 = field761
            pretty_attrs(pp, opt_val762)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat768 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat768)
        write(pp, flat768)
        return nothing
    else
        function _t1380(_dollar_dollar)
            if !isnothing(relation_id_to_string(pp, _dollar_dollar))
                _t1382 = deconstruct_relation_id_string(pp, _dollar_dollar)
                _t1381 = _t1382
            else
                _t1381 = nothing
            end
            return _t1381
        end
        _t1383 = _t1380(msg)
        deconstruct_result766 = _t1383
        if !isnothing(deconstruct_result766)
            unwrapped767 = deconstruct_result766
            write(pp, ":")
            write(pp, unwrapped767)
        else
            function _t1384(_dollar_dollar)
                _t1385 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
                return _t1385
            end
            _t1386 = _t1384(msg)
            deconstruct_result764 = _t1386
            if !isnothing(deconstruct_result764)
                unwrapped765 = deconstruct_result764
                write(pp, format_uint128(pp, unwrapped765))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat773 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat773)
        write(pp, flat773)
        return nothing
    else
        function _t1387(_dollar_dollar)
            _t1388 = deconstruct_bindings(pp, _dollar_dollar)
            return (_t1388, _dollar_dollar.value,)
        end
        _t1389 = _t1387(msg)
        fields769 = _t1389
        unwrapped_fields770 = fields769
        write(pp, "(")
        indent!(pp)
        field771 = unwrapped_fields770[1]
        pretty_bindings(pp, field771)
        newline(pp)
        field772 = unwrapped_fields770[2]
        pretty_formula(pp, field772)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat781 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat781)
        write(pp, flat781)
        return nothing
    else
        function _t1390(_dollar_dollar)
            if !isempty(_dollar_dollar[2])
                _t1391 = _dollar_dollar[2]
            else
                _t1391 = nothing
            end
            return (_dollar_dollar[1], _t1391,)
        end
        _t1392 = _t1390(msg)
        fields774 = _t1392
        unwrapped_fields775 = fields774
        write(pp, "[")
        indent!(pp)
        field776 = unwrapped_fields775[1]
        for (i1393, elem777) in enumerate(field776)
            i778 = i1393 - 1
            if (i778 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem777)
        end
        field779 = unwrapped_fields775[2]
        if !isnothing(field779)
            newline(pp)
            opt_val780 = field779
            pretty_value_bindings(pp, opt_val780)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat786 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat786)
        write(pp, flat786)
        return nothing
    else
        function _t1394(_dollar_dollar)
            return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        end
        _t1395 = _t1394(msg)
        fields782 = _t1395
        unwrapped_fields783 = fields782
        field784 = unwrapped_fields783[1]
        write(pp, field784)
        write(pp, "::")
        field785 = unwrapped_fields783[2]
        pretty_type(pp, field785)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat809 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat809)
        write(pp, flat809)
        return nothing
    else
        function _t1396(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
                _t1397 = _get_oneof_field(_dollar_dollar, :unspecified_type)
            else
                _t1397 = nothing
            end
            return _t1397
        end
        _t1398 = _t1396(msg)
        deconstruct_result807 = _t1398
        if !isnothing(deconstruct_result807)
            unwrapped808 = deconstruct_result807
            pretty_unspecified_type(pp, unwrapped808)
        else
            function _t1399(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                    _t1400 = _get_oneof_field(_dollar_dollar, :string_type)
                else
                    _t1400 = nothing
                end
                return _t1400
            end
            _t1401 = _t1399(msg)
            deconstruct_result805 = _t1401
            if !isnothing(deconstruct_result805)
                unwrapped806 = deconstruct_result805
                pretty_string_type(pp, unwrapped806)
            else
                function _t1402(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                        _t1403 = _get_oneof_field(_dollar_dollar, :int_type)
                    else
                        _t1403 = nothing
                    end
                    return _t1403
                end
                _t1404 = _t1402(msg)
                deconstruct_result803 = _t1404
                if !isnothing(deconstruct_result803)
                    unwrapped804 = deconstruct_result803
                    pretty_int_type(pp, unwrapped804)
                else
                    function _t1405(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                            _t1406 = _get_oneof_field(_dollar_dollar, :float_type)
                        else
                            _t1406 = nothing
                        end
                        return _t1406
                    end
                    _t1407 = _t1405(msg)
                    deconstruct_result801 = _t1407
                    if !isnothing(deconstruct_result801)
                        unwrapped802 = deconstruct_result801
                        pretty_float_type(pp, unwrapped802)
                    else
                        function _t1408(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                                _t1409 = _get_oneof_field(_dollar_dollar, :uint128_type)
                            else
                                _t1409 = nothing
                            end
                            return _t1409
                        end
                        _t1410 = _t1408(msg)
                        deconstruct_result799 = _t1410
                        if !isnothing(deconstruct_result799)
                            unwrapped800 = deconstruct_result799
                            pretty_uint128_type(pp, unwrapped800)
                        else
                            function _t1411(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                    _t1412 = _get_oneof_field(_dollar_dollar, :int128_type)
                                else
                                    _t1412 = nothing
                                end
                                return _t1412
                            end
                            _t1413 = _t1411(msg)
                            deconstruct_result797 = _t1413
                            if !isnothing(deconstruct_result797)
                                unwrapped798 = deconstruct_result797
                                pretty_int128_type(pp, unwrapped798)
                            else
                                function _t1414(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                        _t1415 = _get_oneof_field(_dollar_dollar, :date_type)
                                    else
                                        _t1415 = nothing
                                    end
                                    return _t1415
                                end
                                _t1416 = _t1414(msg)
                                deconstruct_result795 = _t1416
                                if !isnothing(deconstruct_result795)
                                    unwrapped796 = deconstruct_result795
                                    pretty_date_type(pp, unwrapped796)
                                else
                                    function _t1417(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                            _t1418 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                        else
                                            _t1418 = nothing
                                        end
                                        return _t1418
                                    end
                                    _t1419 = _t1417(msg)
                                    deconstruct_result793 = _t1419
                                    if !isnothing(deconstruct_result793)
                                        unwrapped794 = deconstruct_result793
                                        pretty_datetime_type(pp, unwrapped794)
                                    else
                                        function _t1420(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                                _t1421 = _get_oneof_field(_dollar_dollar, :missing_type)
                                            else
                                                _t1421 = nothing
                                            end
                                            return _t1421
                                        end
                                        _t1422 = _t1420(msg)
                                        deconstruct_result791 = _t1422
                                        if !isnothing(deconstruct_result791)
                                            unwrapped792 = deconstruct_result791
                                            pretty_missing_type(pp, unwrapped792)
                                        else
                                            function _t1423(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                    _t1424 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                                else
                                                    _t1424 = nothing
                                                end
                                                return _t1424
                                            end
                                            _t1425 = _t1423(msg)
                                            deconstruct_result789 = _t1425
                                            if !isnothing(deconstruct_result789)
                                                unwrapped790 = deconstruct_result789
                                                pretty_decimal_type(pp, unwrapped790)
                                            else
                                                function _t1426(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                        _t1427 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                    else
                                                        _t1427 = nothing
                                                    end
                                                    return _t1427
                                                end
                                                _t1428 = _t1426(msg)
                                                deconstruct_result787 = _t1428
                                                if !isnothing(deconstruct_result787)
                                                    unwrapped788 = deconstruct_result787
                                                    pretty_boolean_type(pp, unwrapped788)
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
    fields810 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields811 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields812 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields813 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields814 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields815 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields816 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields817 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields818 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat823 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat823)
        write(pp, flat823)
        return nothing
    else
        function _t1429(_dollar_dollar)
            return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        end
        _t1430 = _t1429(msg)
        fields819 = _t1430
        unwrapped_fields820 = fields819
        write(pp, "(")
        write(pp, "DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field821 = unwrapped_fields820[1]
        write(pp, format_int(pp, field821))
        newline(pp)
        field822 = unwrapped_fields820[2]
        write(pp, format_int(pp, field822))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields824 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat828 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat828)
        write(pp, flat828)
        return nothing
    else
        fields825 = msg
        write(pp, "|")
        if !isempty(fields825)
            write(pp, " ")
            for (i1431, elem826) in enumerate(fields825)
                i827 = i1431 - 1
                if (i827 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem826)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat855 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat855)
        write(pp, flat855)
        return nothing
    else
        function _t1432(_dollar_dollar)
            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                _t1433 = _get_oneof_field(_dollar_dollar, :conjunction)
            else
                _t1433 = nothing
            end
            return _t1433
        end
        _t1434 = _t1432(msg)
        deconstruct_result853 = _t1434
        if !isnothing(deconstruct_result853)
            unwrapped854 = deconstruct_result853
            pretty_true(pp, unwrapped854)
        else
            function _t1435(_dollar_dollar)
                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                    _t1436 = _get_oneof_field(_dollar_dollar, :disjunction)
                else
                    _t1436 = nothing
                end
                return _t1436
            end
            _t1437 = _t1435(msg)
            deconstruct_result851 = _t1437
            if !isnothing(deconstruct_result851)
                unwrapped852 = deconstruct_result851
                pretty_false(pp, unwrapped852)
            else
                function _t1438(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("exists"))
                        _t1439 = _get_oneof_field(_dollar_dollar, :exists)
                    else
                        _t1439 = nothing
                    end
                    return _t1439
                end
                _t1440 = _t1438(msg)
                deconstruct_result849 = _t1440
                if !isnothing(deconstruct_result849)
                    unwrapped850 = deconstruct_result849
                    pretty_exists(pp, unwrapped850)
                else
                    function _t1441(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                            _t1442 = _get_oneof_field(_dollar_dollar, :reduce)
                        else
                            _t1442 = nothing
                        end
                        return _t1442
                    end
                    _t1443 = _t1441(msg)
                    deconstruct_result847 = _t1443
                    if !isnothing(deconstruct_result847)
                        unwrapped848 = deconstruct_result847
                        pretty_reduce(pp, unwrapped848)
                    else
                        function _t1444(_dollar_dollar)
                            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                                _t1445 = _get_oneof_field(_dollar_dollar, :conjunction)
                            else
                                _t1445 = nothing
                            end
                            return _t1445
                        end
                        _t1446 = _t1444(msg)
                        deconstruct_result845 = _t1446
                        if !isnothing(deconstruct_result845)
                            unwrapped846 = deconstruct_result845
                            pretty_conjunction(pp, unwrapped846)
                        else
                            function _t1447(_dollar_dollar)
                                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                    _t1448 = _get_oneof_field(_dollar_dollar, :disjunction)
                                else
                                    _t1448 = nothing
                                end
                                return _t1448
                            end
                            _t1449 = _t1447(msg)
                            deconstruct_result843 = _t1449
                            if !isnothing(deconstruct_result843)
                                unwrapped844 = deconstruct_result843
                                pretty_disjunction(pp, unwrapped844)
                            else
                                function _t1450(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("not"))
                                        _t1451 = _get_oneof_field(_dollar_dollar, :not)
                                    else
                                        _t1451 = nothing
                                    end
                                    return _t1451
                                end
                                _t1452 = _t1450(msg)
                                deconstruct_result841 = _t1452
                                if !isnothing(deconstruct_result841)
                                    unwrapped842 = deconstruct_result841
                                    pretty_not(pp, unwrapped842)
                                else
                                    function _t1453(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                            _t1454 = _get_oneof_field(_dollar_dollar, :ffi)
                                        else
                                            _t1454 = nothing
                                        end
                                        return _t1454
                                    end
                                    _t1455 = _t1453(msg)
                                    deconstruct_result839 = _t1455
                                    if !isnothing(deconstruct_result839)
                                        unwrapped840 = deconstruct_result839
                                        pretty_ffi(pp, unwrapped840)
                                    else
                                        function _t1456(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                                _t1457 = _get_oneof_field(_dollar_dollar, :atom)
                                            else
                                                _t1457 = nothing
                                            end
                                            return _t1457
                                        end
                                        _t1458 = _t1456(msg)
                                        deconstruct_result837 = _t1458
                                        if !isnothing(deconstruct_result837)
                                            unwrapped838 = deconstruct_result837
                                            pretty_atom(pp, unwrapped838)
                                        else
                                            function _t1459(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                    _t1460 = _get_oneof_field(_dollar_dollar, :pragma)
                                                else
                                                    _t1460 = nothing
                                                end
                                                return _t1460
                                            end
                                            _t1461 = _t1459(msg)
                                            deconstruct_result835 = _t1461
                                            if !isnothing(deconstruct_result835)
                                                unwrapped836 = deconstruct_result835
                                                pretty_pragma(pp, unwrapped836)
                                            else
                                                function _t1462(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                        _t1463 = _get_oneof_field(_dollar_dollar, :primitive)
                                                    else
                                                        _t1463 = nothing
                                                    end
                                                    return _t1463
                                                end
                                                _t1464 = _t1462(msg)
                                                deconstruct_result833 = _t1464
                                                if !isnothing(deconstruct_result833)
                                                    unwrapped834 = deconstruct_result833
                                                    pretty_primitive(pp, unwrapped834)
                                                else
                                                    function _t1465(_dollar_dollar)
                                                        if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                            _t1466 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                        else
                                                            _t1466 = nothing
                                                        end
                                                        return _t1466
                                                    end
                                                    _t1467 = _t1465(msg)
                                                    deconstruct_result831 = _t1467
                                                    if !isnothing(deconstruct_result831)
                                                        unwrapped832 = deconstruct_result831
                                                        pretty_rel_atom(pp, unwrapped832)
                                                    else
                                                        function _t1468(_dollar_dollar)
                                                            if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                                _t1469 = _get_oneof_field(_dollar_dollar, :cast)
                                                            else
                                                                _t1469 = nothing
                                                            end
                                                            return _t1469
                                                        end
                                                        _t1470 = _t1468(msg)
                                                        deconstruct_result829 = _t1470
                                                        if !isnothing(deconstruct_result829)
                                                            unwrapped830 = deconstruct_result829
                                                            pretty_cast(pp, unwrapped830)
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
    fields856 = msg
    write(pp, "(")
    write(pp, "true")
    write(pp, ")")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields857 = msg
    write(pp, "(")
    write(pp, "false")
    write(pp, ")")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat862 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat862)
        write(pp, flat862)
        return nothing
    else
        function _t1471(_dollar_dollar)
            _t1472 = deconstruct_bindings(pp, _dollar_dollar.body)
            return (_t1472, _dollar_dollar.body.value,)
        end
        _t1473 = _t1471(msg)
        fields858 = _t1473
        unwrapped_fields859 = fields858
        write(pp, "(")
        write(pp, "exists")
        indent_sexp!(pp)
        newline(pp)
        field860 = unwrapped_fields859[1]
        pretty_bindings(pp, field860)
        newline(pp)
        field861 = unwrapped_fields859[2]
        pretty_formula(pp, field861)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat868 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat868)
        write(pp, flat868)
        return nothing
    else
        function _t1474(_dollar_dollar)
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        end
        _t1475 = _t1474(msg)
        fields863 = _t1475
        unwrapped_fields864 = fields863
        write(pp, "(")
        write(pp, "reduce")
        indent_sexp!(pp)
        newline(pp)
        field865 = unwrapped_fields864[1]
        pretty_abstraction(pp, field865)
        newline(pp)
        field866 = unwrapped_fields864[2]
        pretty_abstraction(pp, field866)
        newline(pp)
        field867 = unwrapped_fields864[3]
        pretty_terms(pp, field867)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat872 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat872)
        write(pp, flat872)
        return nothing
    else
        fields869 = msg
        write(pp, "(")
        write(pp, "terms")
        indent_sexp!(pp)
        if !isempty(fields869)
            newline(pp)
            for (i1476, elem870) in enumerate(fields869)
                i871 = i1476 - 1
                if (i871 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem870)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat877 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat877)
        write(pp, flat877)
        return nothing
    else
        function _t1477(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("var"))
                _t1478 = _get_oneof_field(_dollar_dollar, :var)
            else
                _t1478 = nothing
            end
            return _t1478
        end
        _t1479 = _t1477(msg)
        deconstruct_result875 = _t1479
        if !isnothing(deconstruct_result875)
            unwrapped876 = deconstruct_result875
            pretty_var(pp, unwrapped876)
        else
            function _t1480(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("constant"))
                    _t1481 = _get_oneof_field(_dollar_dollar, :constant)
                else
                    _t1481 = nothing
                end
                return _t1481
            end
            _t1482 = _t1480(msg)
            deconstruct_result873 = _t1482
            if !isnothing(deconstruct_result873)
                unwrapped874 = deconstruct_result873
                pretty_constant(pp, unwrapped874)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat880 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat880)
        write(pp, flat880)
        return nothing
    else
        function _t1483(_dollar_dollar)
            return _dollar_dollar.name
        end
        _t1484 = _t1483(msg)
        fields878 = _t1484
        unwrapped_fields879 = fields878
        write(pp, unwrapped_fields879)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat882 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat882)
        write(pp, flat882)
        return nothing
    else
        fields881 = msg
        pretty_value(pp, fields881)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat887 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat887)
        write(pp, flat887)
        return nothing
    else
        function _t1485(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1486 = _t1485(msg)
        fields883 = _t1486
        unwrapped_fields884 = fields883
        write(pp, "(")
        write(pp, "and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields884)
            newline(pp)
            for (i1487, elem885) in enumerate(unwrapped_fields884)
                i886 = i1487 - 1
                if (i886 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem885)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat892 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat892)
        write(pp, flat892)
        return nothing
    else
        function _t1488(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1489 = _t1488(msg)
        fields888 = _t1489
        unwrapped_fields889 = fields888
        write(pp, "(")
        write(pp, "or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields889)
            newline(pp)
            for (i1490, elem890) in enumerate(unwrapped_fields889)
                i891 = i1490 - 1
                if (i891 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem890)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat895 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat895)
        write(pp, flat895)
        return nothing
    else
        function _t1491(_dollar_dollar)
            return _dollar_dollar.arg
        end
        _t1492 = _t1491(msg)
        fields893 = _t1492
        unwrapped_fields894 = fields893
        write(pp, "(")
        write(pp, "not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields894)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat901 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat901)
        write(pp, flat901)
        return nothing
    else
        function _t1493(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        end
        _t1494 = _t1493(msg)
        fields896 = _t1494
        unwrapped_fields897 = fields896
        write(pp, "(")
        write(pp, "ffi")
        indent_sexp!(pp)
        newline(pp)
        field898 = unwrapped_fields897[1]
        pretty_name(pp, field898)
        newline(pp)
        field899 = unwrapped_fields897[2]
        pretty_ffi_args(pp, field899)
        newline(pp)
        field900 = unwrapped_fields897[3]
        pretty_terms(pp, field900)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat903 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat903)
        write(pp, flat903)
        return nothing
    else
        fields902 = msg
        write(pp, ":")
        write(pp, fields902)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat907 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat907)
        write(pp, flat907)
        return nothing
    else
        fields904 = msg
        write(pp, "(")
        write(pp, "args")
        indent_sexp!(pp)
        if !isempty(fields904)
            newline(pp)
            for (i1495, elem905) in enumerate(fields904)
                i906 = i1495 - 1
                if (i906 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem905)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat914 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat914)
        write(pp, flat914)
        return nothing
    else
        function _t1496(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1497 = _t1496(msg)
        fields908 = _t1497
        unwrapped_fields909 = fields908
        write(pp, "(")
        write(pp, "atom")
        indent_sexp!(pp)
        newline(pp)
        field910 = unwrapped_fields909[1]
        pretty_relation_id(pp, field910)
        field911 = unwrapped_fields909[2]
        if !isempty(field911)
            newline(pp)
            for (i1498, elem912) in enumerate(field911)
                i913 = i1498 - 1
                if (i913 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem912)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat921 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat921)
        write(pp, flat921)
        return nothing
    else
        function _t1499(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1500 = _t1499(msg)
        fields915 = _t1500
        unwrapped_fields916 = fields915
        write(pp, "(")
        write(pp, "pragma")
        indent_sexp!(pp)
        newline(pp)
        field917 = unwrapped_fields916[1]
        pretty_name(pp, field917)
        field918 = unwrapped_fields916[2]
        if !isempty(field918)
            newline(pp)
            for (i1501, elem919) in enumerate(field918)
                i920 = i1501 - 1
                if (i920 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem919)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat937 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat937)
        write(pp, flat937)
        return nothing
    else
        function _t1502(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1503 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1503 = nothing
            end
            return _t1503
        end
        _t1504 = _t1502(msg)
        guard_result936 = _t1504
        if !isnothing(guard_result936)
            pretty_eq(pp, msg)
        else
            function _t1505(_dollar_dollar)
                if _dollar_dollar.name == "rel_primitive_lt_monotype"
                    _t1506 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1506 = nothing
                end
                return _t1506
            end
            _t1507 = _t1505(msg)
            guard_result935 = _t1507
            if !isnothing(guard_result935)
                pretty_lt(pp, msg)
            else
                function _t1508(_dollar_dollar)
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                        _t1509 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1509 = nothing
                    end
                    return _t1509
                end
                _t1510 = _t1508(msg)
                guard_result934 = _t1510
                if !isnothing(guard_result934)
                    pretty_lt_eq(pp, msg)
                else
                    function _t1511(_dollar_dollar)
                        if _dollar_dollar.name == "rel_primitive_gt_monotype"
                            _t1512 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1512 = nothing
                        end
                        return _t1512
                    end
                    _t1513 = _t1511(msg)
                    guard_result933 = _t1513
                    if !isnothing(guard_result933)
                        pretty_gt(pp, msg)
                    else
                        function _t1514(_dollar_dollar)
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                                _t1515 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                            else
                                _t1515 = nothing
                            end
                            return _t1515
                        end
                        _t1516 = _t1514(msg)
                        guard_result932 = _t1516
                        if !isnothing(guard_result932)
                            pretty_gt_eq(pp, msg)
                        else
                            function _t1517(_dollar_dollar)
                                if _dollar_dollar.name == "rel_primitive_add_monotype"
                                    _t1518 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1518 = nothing
                                end
                                return _t1518
                            end
                            _t1519 = _t1517(msg)
                            guard_result931 = _t1519
                            if !isnothing(guard_result931)
                                pretty_add(pp, msg)
                            else
                                function _t1520(_dollar_dollar)
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                        _t1521 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1521 = nothing
                                    end
                                    return _t1521
                                end
                                _t1522 = _t1520(msg)
                                guard_result930 = _t1522
                                if !isnothing(guard_result930)
                                    pretty_minus(pp, msg)
                                else
                                    function _t1523(_dollar_dollar)
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                            _t1524 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1524 = nothing
                                        end
                                        return _t1524
                                    end
                                    _t1525 = _t1523(msg)
                                    guard_result929 = _t1525
                                    if !isnothing(guard_result929)
                                        pretty_multiply(pp, msg)
                                    else
                                        function _t1526(_dollar_dollar)
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                                _t1527 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                            else
                                                _t1527 = nothing
                                            end
                                            return _t1527
                                        end
                                        _t1528 = _t1526(msg)
                                        guard_result928 = _t1528
                                        if !isnothing(guard_result928)
                                            pretty_divide(pp, msg)
                                        else
                                            function _t1529(_dollar_dollar)
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            end
                                            _t1530 = _t1529(msg)
                                            fields922 = _t1530
                                            unwrapped_fields923 = fields922
                                            write(pp, "(")
                                            write(pp, "primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field924 = unwrapped_fields923[1]
                                            pretty_name(pp, field924)
                                            field925 = unwrapped_fields923[2]
                                            if !isempty(field925)
                                                newline(pp)
                                                for (i1531, elem926) in enumerate(field925)
                                                    i927 = i1531 - 1
                                                    if (i927 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem926)
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
    flat942 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat942)
        write(pp, flat942)
        return nothing
    else
        function _t1532(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1533 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1533 = nothing
            end
            return _t1533
        end
        _t1534 = _t1532(msg)
        fields938 = _t1534
        unwrapped_fields939 = fields938
        write(pp, "(")
        write(pp, "=")
        indent_sexp!(pp)
        newline(pp)
        field940 = unwrapped_fields939[1]
        pretty_term(pp, field940)
        newline(pp)
        field941 = unwrapped_fields939[2]
        pretty_term(pp, field941)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat947 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat947)
        write(pp, flat947)
        return nothing
    else
        function _t1535(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1536 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1536 = nothing
            end
            return _t1536
        end
        _t1537 = _t1535(msg)
        fields943 = _t1537
        unwrapped_fields944 = fields943
        write(pp, "(")
        write(pp, "<")
        indent_sexp!(pp)
        newline(pp)
        field945 = unwrapped_fields944[1]
        pretty_term(pp, field945)
        newline(pp)
        field946 = unwrapped_fields944[2]
        pretty_term(pp, field946)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat952 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat952)
        write(pp, flat952)
        return nothing
    else
        function _t1538(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                _t1539 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1539 = nothing
            end
            return _t1539
        end
        _t1540 = _t1538(msg)
        fields948 = _t1540
        unwrapped_fields949 = fields948
        write(pp, "(")
        write(pp, "<=")
        indent_sexp!(pp)
        newline(pp)
        field950 = unwrapped_fields949[1]
        pretty_term(pp, field950)
        newline(pp)
        field951 = unwrapped_fields949[2]
        pretty_term(pp, field951)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat957 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat957)
        write(pp, flat957)
        return nothing
    else
        function _t1541(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_monotype"
                _t1542 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1542 = nothing
            end
            return _t1542
        end
        _t1543 = _t1541(msg)
        fields953 = _t1543
        unwrapped_fields954 = fields953
        write(pp, "(")
        write(pp, ">")
        indent_sexp!(pp)
        newline(pp)
        field955 = unwrapped_fields954[1]
        pretty_term(pp, field955)
        newline(pp)
        field956 = unwrapped_fields954[2]
        pretty_term(pp, field956)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat962 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat962)
        write(pp, flat962)
        return nothing
    else
        function _t1544(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                _t1545 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1545 = nothing
            end
            return _t1545
        end
        _t1546 = _t1544(msg)
        fields958 = _t1546
        unwrapped_fields959 = fields958
        write(pp, "(")
        write(pp, ">=")
        indent_sexp!(pp)
        newline(pp)
        field960 = unwrapped_fields959[1]
        pretty_term(pp, field960)
        newline(pp)
        field961 = unwrapped_fields959[2]
        pretty_term(pp, field961)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat968 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat968)
        write(pp, flat968)
        return nothing
    else
        function _t1547(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_add_monotype"
                _t1548 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1548 = nothing
            end
            return _t1548
        end
        _t1549 = _t1547(msg)
        fields963 = _t1549
        unwrapped_fields964 = fields963
        write(pp, "(")
        write(pp, "+")
        indent_sexp!(pp)
        newline(pp)
        field965 = unwrapped_fields964[1]
        pretty_term(pp, field965)
        newline(pp)
        field966 = unwrapped_fields964[2]
        pretty_term(pp, field966)
        newline(pp)
        field967 = unwrapped_fields964[3]
        pretty_term(pp, field967)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat974 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat974)
        write(pp, flat974)
        return nothing
    else
        function _t1550(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                _t1551 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1551 = nothing
            end
            return _t1551
        end
        _t1552 = _t1550(msg)
        fields969 = _t1552
        unwrapped_fields970 = fields969
        write(pp, "(")
        write(pp, "-")
        indent_sexp!(pp)
        newline(pp)
        field971 = unwrapped_fields970[1]
        pretty_term(pp, field971)
        newline(pp)
        field972 = unwrapped_fields970[2]
        pretty_term(pp, field972)
        newline(pp)
        field973 = unwrapped_fields970[3]
        pretty_term(pp, field973)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat980 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat980)
        write(pp, flat980)
        return nothing
    else
        function _t1553(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                _t1554 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1554 = nothing
            end
            return _t1554
        end
        _t1555 = _t1553(msg)
        fields975 = _t1555
        unwrapped_fields976 = fields975
        write(pp, "(")
        write(pp, "*")
        indent_sexp!(pp)
        newline(pp)
        field977 = unwrapped_fields976[1]
        pretty_term(pp, field977)
        newline(pp)
        field978 = unwrapped_fields976[2]
        pretty_term(pp, field978)
        newline(pp)
        field979 = unwrapped_fields976[3]
        pretty_term(pp, field979)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat986 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat986)
        write(pp, flat986)
        return nothing
    else
        function _t1556(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                _t1557 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1557 = nothing
            end
            return _t1557
        end
        _t1558 = _t1556(msg)
        fields981 = _t1558
        unwrapped_fields982 = fields981
        write(pp, "(")
        write(pp, "/")
        indent_sexp!(pp)
        newline(pp)
        field983 = unwrapped_fields982[1]
        pretty_term(pp, field983)
        newline(pp)
        field984 = unwrapped_fields982[2]
        pretty_term(pp, field984)
        newline(pp)
        field985 = unwrapped_fields982[3]
        pretty_term(pp, field985)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat991 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat991)
        write(pp, flat991)
        return nothing
    else
        function _t1559(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
                _t1560 = _get_oneof_field(_dollar_dollar, :specialized_value)
            else
                _t1560 = nothing
            end
            return _t1560
        end
        _t1561 = _t1559(msg)
        deconstruct_result989 = _t1561
        if !isnothing(deconstruct_result989)
            unwrapped990 = deconstruct_result989
            pretty_specialized_value(pp, unwrapped990)
        else
            function _t1562(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("term"))
                    _t1563 = _get_oneof_field(_dollar_dollar, :term)
                else
                    _t1563 = nothing
                end
                return _t1563
            end
            _t1564 = _t1562(msg)
            deconstruct_result987 = _t1564
            if !isnothing(deconstruct_result987)
                unwrapped988 = deconstruct_result987
                pretty_term(pp, unwrapped988)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat993 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat993)
        write(pp, flat993)
        return nothing
    else
        fields992 = msg
        write(pp, "#")
        pretty_value(pp, fields992)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1000 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1000)
        write(pp, flat1000)
        return nothing
    else
        function _t1565(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1566 = _t1565(msg)
        fields994 = _t1566
        unwrapped_fields995 = fields994
        write(pp, "(")
        write(pp, "relatom")
        indent_sexp!(pp)
        newline(pp)
        field996 = unwrapped_fields995[1]
        pretty_name(pp, field996)
        field997 = unwrapped_fields995[2]
        if !isempty(field997)
            newline(pp)
            for (i1567, elem998) in enumerate(field997)
                i999 = i1567 - 1
                if (i999 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem998)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1005 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1005)
        write(pp, flat1005)
        return nothing
    else
        function _t1568(_dollar_dollar)
            return (_dollar_dollar.input, _dollar_dollar.result,)
        end
        _t1569 = _t1568(msg)
        fields1001 = _t1569
        unwrapped_fields1002 = fields1001
        write(pp, "(")
        write(pp, "cast")
        indent_sexp!(pp)
        newline(pp)
        field1003 = unwrapped_fields1002[1]
        pretty_term(pp, field1003)
        newline(pp)
        field1004 = unwrapped_fields1002[2]
        pretty_term(pp, field1004)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1009 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1009)
        write(pp, flat1009)
        return nothing
    else
        fields1006 = msg
        write(pp, "(")
        write(pp, "attrs")
        indent_sexp!(pp)
        if !isempty(fields1006)
            newline(pp)
            for (i1570, elem1007) in enumerate(fields1006)
                i1008 = i1570 - 1
                if (i1008 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1007)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1016 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1016)
        write(pp, flat1016)
        return nothing
    else
        function _t1571(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args,)
        end
        _t1572 = _t1571(msg)
        fields1010 = _t1572
        unwrapped_fields1011 = fields1010
        write(pp, "(")
        write(pp, "attribute")
        indent_sexp!(pp)
        newline(pp)
        field1012 = unwrapped_fields1011[1]
        pretty_name(pp, field1012)
        field1013 = unwrapped_fields1011[2]
        if !isempty(field1013)
            newline(pp)
            for (i1573, elem1014) in enumerate(field1013)
                i1015 = i1573 - 1
                if (i1015 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem1014)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1023 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1023)
        write(pp, flat1023)
        return nothing
    else
        function _t1574(_dollar_dollar)
            return (_dollar_dollar.var"#global", _dollar_dollar.body,)
        end
        _t1575 = _t1574(msg)
        fields1017 = _t1575
        unwrapped_fields1018 = fields1017
        write(pp, "(")
        write(pp, "algorithm")
        indent_sexp!(pp)
        field1019 = unwrapped_fields1018[1]
        if !isempty(field1019)
            newline(pp)
            for (i1576, elem1020) in enumerate(field1019)
                i1021 = i1576 - 1
                if (i1021 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1020)
            end
        end
        newline(pp)
        field1022 = unwrapped_fields1018[2]
        pretty_script(pp, field1022)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1028 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1028)
        write(pp, flat1028)
        return nothing
    else
        function _t1577(_dollar_dollar)
            return _dollar_dollar.constructs
        end
        _t1578 = _t1577(msg)
        fields1024 = _t1578
        unwrapped_fields1025 = fields1024
        write(pp, "(")
        write(pp, "script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1025)
            newline(pp)
            for (i1579, elem1026) in enumerate(unwrapped_fields1025)
                i1027 = i1579 - 1
                if (i1027 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1026)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1033 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1033)
        write(pp, flat1033)
        return nothing
    else
        function _t1580(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("loop"))
                _t1581 = _get_oneof_field(_dollar_dollar, :loop)
            else
                _t1581 = nothing
            end
            return _t1581
        end
        _t1582 = _t1580(msg)
        deconstruct_result1031 = _t1582
        if !isnothing(deconstruct_result1031)
            unwrapped1032 = deconstruct_result1031
            pretty_loop(pp, unwrapped1032)
        else
            function _t1583(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                    _t1584 = _get_oneof_field(_dollar_dollar, :instruction)
                else
                    _t1584 = nothing
                end
                return _t1584
            end
            _t1585 = _t1583(msg)
            deconstruct_result1029 = _t1585
            if !isnothing(deconstruct_result1029)
                unwrapped1030 = deconstruct_result1029
                pretty_instruction(pp, unwrapped1030)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1038 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1038)
        write(pp, flat1038)
        return nothing
    else
        function _t1586(_dollar_dollar)
            return (_dollar_dollar.init, _dollar_dollar.body,)
        end
        _t1587 = _t1586(msg)
        fields1034 = _t1587
        unwrapped_fields1035 = fields1034
        write(pp, "(")
        write(pp, "loop")
        indent_sexp!(pp)
        newline(pp)
        field1036 = unwrapped_fields1035[1]
        pretty_init(pp, field1036)
        newline(pp)
        field1037 = unwrapped_fields1035[2]
        pretty_script(pp, field1037)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1042 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1042)
        write(pp, flat1042)
        return nothing
    else
        fields1039 = msg
        write(pp, "(")
        write(pp, "init")
        indent_sexp!(pp)
        if !isempty(fields1039)
            newline(pp)
            for (i1588, elem1040) in enumerate(fields1039)
                i1041 = i1588 - 1
                if (i1041 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1040)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1053 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1053)
        write(pp, flat1053)
        return nothing
    else
        function _t1589(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("assign"))
                _t1590 = _get_oneof_field(_dollar_dollar, :assign)
            else
                _t1590 = nothing
            end
            return _t1590
        end
        _t1591 = _t1589(msg)
        deconstruct_result1051 = _t1591
        if !isnothing(deconstruct_result1051)
            unwrapped1052 = deconstruct_result1051
            pretty_assign(pp, unwrapped1052)
        else
            function _t1592(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                    _t1593 = _get_oneof_field(_dollar_dollar, :upsert)
                else
                    _t1593 = nothing
                end
                return _t1593
            end
            _t1594 = _t1592(msg)
            deconstruct_result1049 = _t1594
            if !isnothing(deconstruct_result1049)
                unwrapped1050 = deconstruct_result1049
                pretty_upsert(pp, unwrapped1050)
            else
                function _t1595(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("#break"))
                        _t1596 = _get_oneof_field(_dollar_dollar, :var"#break")
                    else
                        _t1596 = nothing
                    end
                    return _t1596
                end
                _t1597 = _t1595(msg)
                deconstruct_result1047 = _t1597
                if !isnothing(deconstruct_result1047)
                    unwrapped1048 = deconstruct_result1047
                    pretty_break(pp, unwrapped1048)
                else
                    function _t1598(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                            _t1599 = _get_oneof_field(_dollar_dollar, :monoid_def)
                        else
                            _t1599 = nothing
                        end
                        return _t1599
                    end
                    _t1600 = _t1598(msg)
                    deconstruct_result1045 = _t1600
                    if !isnothing(deconstruct_result1045)
                        unwrapped1046 = deconstruct_result1045
                        pretty_monoid_def(pp, unwrapped1046)
                    else
                        function _t1601(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                                _t1602 = _get_oneof_field(_dollar_dollar, :monus_def)
                            else
                                _t1602 = nothing
                            end
                            return _t1602
                        end
                        _t1603 = _t1601(msg)
                        deconstruct_result1043 = _t1603
                        if !isnothing(deconstruct_result1043)
                            unwrapped1044 = deconstruct_result1043
                            pretty_monus_def(pp, unwrapped1044)
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
    flat1060 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1060)
        write(pp, flat1060)
        return nothing
    else
        function _t1604(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1605 = _dollar_dollar.attrs
            else
                _t1605 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1605,)
        end
        _t1606 = _t1604(msg)
        fields1054 = _t1606
        unwrapped_fields1055 = fields1054
        write(pp, "(")
        write(pp, "assign")
        indent_sexp!(pp)
        newline(pp)
        field1056 = unwrapped_fields1055[1]
        pretty_relation_id(pp, field1056)
        newline(pp)
        field1057 = unwrapped_fields1055[2]
        pretty_abstraction(pp, field1057)
        field1058 = unwrapped_fields1055[3]
        if !isnothing(field1058)
            newline(pp)
            opt_val1059 = field1058
            pretty_attrs(pp, opt_val1059)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1067 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1067)
        write(pp, flat1067)
        return nothing
    else
        function _t1607(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1608 = _dollar_dollar.attrs
            else
                _t1608 = nothing
            end
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1608,)
        end
        _t1609 = _t1607(msg)
        fields1061 = _t1609
        unwrapped_fields1062 = fields1061
        write(pp, "(")
        write(pp, "upsert")
        indent_sexp!(pp)
        newline(pp)
        field1063 = unwrapped_fields1062[1]
        pretty_relation_id(pp, field1063)
        newline(pp)
        field1064 = unwrapped_fields1062[2]
        pretty_abstraction_with_arity(pp, field1064)
        field1065 = unwrapped_fields1062[3]
        if !isnothing(field1065)
            newline(pp)
            opt_val1066 = field1065
            pretty_attrs(pp, opt_val1066)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1072 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1072)
        write(pp, flat1072)
        return nothing
    else
        function _t1610(_dollar_dollar)
            _t1611 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
            return (_t1611, _dollar_dollar[1].value,)
        end
        _t1612 = _t1610(msg)
        fields1068 = _t1612
        unwrapped_fields1069 = fields1068
        write(pp, "(")
        indent!(pp)
        field1070 = unwrapped_fields1069[1]
        pretty_bindings(pp, field1070)
        newline(pp)
        field1071 = unwrapped_fields1069[2]
        pretty_formula(pp, field1071)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1079 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1079)
        write(pp, flat1079)
        return nothing
    else
        function _t1613(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1614 = _dollar_dollar.attrs
            else
                _t1614 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1614,)
        end
        _t1615 = _t1613(msg)
        fields1073 = _t1615
        unwrapped_fields1074 = fields1073
        write(pp, "(")
        write(pp, "break")
        indent_sexp!(pp)
        newline(pp)
        field1075 = unwrapped_fields1074[1]
        pretty_relation_id(pp, field1075)
        newline(pp)
        field1076 = unwrapped_fields1074[2]
        pretty_abstraction(pp, field1076)
        field1077 = unwrapped_fields1074[3]
        if !isnothing(field1077)
            newline(pp)
            opt_val1078 = field1077
            pretty_attrs(pp, opt_val1078)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1087 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1087)
        write(pp, flat1087)
        return nothing
    else
        function _t1616(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1617 = _dollar_dollar.attrs
            else
                _t1617 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1617,)
        end
        _t1618 = _t1616(msg)
        fields1080 = _t1618
        unwrapped_fields1081 = fields1080
        write(pp, "(")
        write(pp, "monoid")
        indent_sexp!(pp)
        newline(pp)
        field1082 = unwrapped_fields1081[1]
        pretty_monoid(pp, field1082)
        newline(pp)
        field1083 = unwrapped_fields1081[2]
        pretty_relation_id(pp, field1083)
        newline(pp)
        field1084 = unwrapped_fields1081[3]
        pretty_abstraction_with_arity(pp, field1084)
        field1085 = unwrapped_fields1081[4]
        if !isnothing(field1085)
            newline(pp)
            opt_val1086 = field1085
            pretty_attrs(pp, opt_val1086)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1096 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        function _t1619(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
                _t1620 = _get_oneof_field(_dollar_dollar, :or_monoid)
            else
                _t1620 = nothing
            end
            return _t1620
        end
        _t1621 = _t1619(msg)
        deconstruct_result1094 = _t1621
        if !isnothing(deconstruct_result1094)
            unwrapped1095 = deconstruct_result1094
            pretty_or_monoid(pp, unwrapped1095)
        else
            function _t1622(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                    _t1623 = _get_oneof_field(_dollar_dollar, :min_monoid)
                else
                    _t1623 = nothing
                end
                return _t1623
            end
            _t1624 = _t1622(msg)
            deconstruct_result1092 = _t1624
            if !isnothing(deconstruct_result1092)
                unwrapped1093 = deconstruct_result1092
                pretty_min_monoid(pp, unwrapped1093)
            else
                function _t1625(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                        _t1626 = _get_oneof_field(_dollar_dollar, :max_monoid)
                    else
                        _t1626 = nothing
                    end
                    return _t1626
                end
                _t1627 = _t1625(msg)
                deconstruct_result1090 = _t1627
                if !isnothing(deconstruct_result1090)
                    unwrapped1091 = deconstruct_result1090
                    pretty_max_monoid(pp, unwrapped1091)
                else
                    function _t1628(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                            _t1629 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                        else
                            _t1629 = nothing
                        end
                        return _t1629
                    end
                    _t1630 = _t1628(msg)
                    deconstruct_result1088 = _t1630
                    if !isnothing(deconstruct_result1088)
                        unwrapped1089 = deconstruct_result1088
                        pretty_sum_monoid(pp, unwrapped1089)
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
    fields1097 = msg
    write(pp, "(")
    write(pp, "or")
    write(pp, ")")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1100 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1100)
        write(pp, flat1100)
        return nothing
    else
        function _t1631(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1632 = _t1631(msg)
        fields1098 = _t1632
        unwrapped_fields1099 = fields1098
        write(pp, "(")
        write(pp, "min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1099)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1103 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1103)
        write(pp, flat1103)
        return nothing
    else
        function _t1633(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1634 = _t1633(msg)
        fields1101 = _t1634
        unwrapped_fields1102 = fields1101
        write(pp, "(")
        write(pp, "max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1102)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1106 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1106)
        write(pp, flat1106)
        return nothing
    else
        function _t1635(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1636 = _t1635(msg)
        fields1104 = _t1636
        unwrapped_fields1105 = fields1104
        write(pp, "(")
        write(pp, "sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1105)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1114 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1114)
        write(pp, flat1114)
        return nothing
    else
        function _t1637(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1638 = _dollar_dollar.attrs
            else
                _t1638 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1638,)
        end
        _t1639 = _t1637(msg)
        fields1107 = _t1639
        unwrapped_fields1108 = fields1107
        write(pp, "(")
        write(pp, "monus")
        indent_sexp!(pp)
        newline(pp)
        field1109 = unwrapped_fields1108[1]
        pretty_monoid(pp, field1109)
        newline(pp)
        field1110 = unwrapped_fields1108[2]
        pretty_relation_id(pp, field1110)
        newline(pp)
        field1111 = unwrapped_fields1108[3]
        pretty_abstraction_with_arity(pp, field1111)
        field1112 = unwrapped_fields1108[4]
        if !isnothing(field1112)
            newline(pp)
            opt_val1113 = field1112
            pretty_attrs(pp, opt_val1113)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1121 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1121)
        write(pp, flat1121)
        return nothing
    else
        function _t1640(_dollar_dollar)
            return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        end
        _t1641 = _t1640(msg)
        fields1115 = _t1641
        unwrapped_fields1116 = fields1115
        write(pp, "(")
        write(pp, "functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1117 = unwrapped_fields1116[1]
        pretty_relation_id(pp, field1117)
        newline(pp)
        field1118 = unwrapped_fields1116[2]
        pretty_abstraction(pp, field1118)
        newline(pp)
        field1119 = unwrapped_fields1116[3]
        pretty_functional_dependency_keys(pp, field1119)
        newline(pp)
        field1120 = unwrapped_fields1116[4]
        pretty_functional_dependency_values(pp, field1120)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1125 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1125)
        write(pp, flat1125)
        return nothing
    else
        fields1122 = msg
        write(pp, "(")
        write(pp, "keys")
        indent_sexp!(pp)
        if !isempty(fields1122)
            newline(pp)
            for (i1642, elem1123) in enumerate(fields1122)
                i1124 = i1642 - 1
                if (i1124 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1123)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1129 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1129)
        write(pp, flat1129)
        return nothing
    else
        fields1126 = msg
        write(pp, "(")
        write(pp, "values")
        indent_sexp!(pp)
        if !isempty(fields1126)
            newline(pp)
            for (i1643, elem1127) in enumerate(fields1126)
                i1128 = i1643 - 1
                if (i1128 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1127)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1136 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1136)
        write(pp, flat1136)
        return nothing
    else
        function _t1644(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("rel_edb"))
                _t1645 = _get_oneof_field(_dollar_dollar, :rel_edb)
            else
                _t1645 = nothing
            end
            return _t1645
        end
        _t1646 = _t1644(msg)
        deconstruct_result1134 = _t1646
        if !isnothing(deconstruct_result1134)
            unwrapped1135 = deconstruct_result1134
            pretty_rel_edb(pp, unwrapped1135)
        else
            function _t1647(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                    _t1648 = _get_oneof_field(_dollar_dollar, :betree_relation)
                else
                    _t1648 = nothing
                end
                return _t1648
            end
            _t1649 = _t1647(msg)
            deconstruct_result1132 = _t1649
            if !isnothing(deconstruct_result1132)
                unwrapped1133 = deconstruct_result1132
                pretty_betree_relation(pp, unwrapped1133)
            else
                function _t1650(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                        _t1651 = _get_oneof_field(_dollar_dollar, :csv_data)
                    else
                        _t1651 = nothing
                    end
                    return _t1651
                end
                _t1652 = _t1650(msg)
                deconstruct_result1130 = _t1652
                if !isnothing(deconstruct_result1130)
                    unwrapped1131 = deconstruct_result1130
                    pretty_csv_data(pp, unwrapped1131)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_rel_edb(pp::PrettyPrinter, msg::Proto.RelEDB)
    flat1142 = try_flat(pp, msg, pretty_rel_edb)
    if !isnothing(flat1142)
        write(pp, flat1142)
        return nothing
    else
        function _t1653(_dollar_dollar)
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        end
        _t1654 = _t1653(msg)
        fields1137 = _t1654
        unwrapped_fields1138 = fields1137
        write(pp, "(")
        write(pp, "rel_edb")
        indent_sexp!(pp)
        newline(pp)
        field1139 = unwrapped_fields1138[1]
        pretty_relation_id(pp, field1139)
        newline(pp)
        field1140 = unwrapped_fields1138[2]
        pretty_rel_edb_path(pp, field1140)
        newline(pp)
        field1141 = unwrapped_fields1138[3]
        pretty_rel_edb_types(pp, field1141)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1146 = try_flat(pp, msg, pretty_rel_edb_path)
    if !isnothing(flat1146)
        write(pp, flat1146)
        return nothing
    else
        fields1143 = msg
        write(pp, "[")
        indent!(pp)
        for (i1655, elem1144) in enumerate(fields1143)
            i1145 = i1655 - 1
            if (i1145 > 0)
                newline(pp)
            end
            write(pp, format_string(pp, elem1144))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_rel_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1150 = try_flat(pp, msg, pretty_rel_edb_types)
    if !isnothing(flat1150)
        write(pp, flat1150)
        return nothing
    else
        fields1147 = msg
        write(pp, "[")
        indent!(pp)
        for (i1656, elem1148) in enumerate(fields1147)
            i1149 = i1656 - 1
            if (i1149 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1148)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1155 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1155)
        write(pp, flat1155)
        return nothing
    else
        function _t1657(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        end
        _t1658 = _t1657(msg)
        fields1151 = _t1658
        unwrapped_fields1152 = fields1151
        write(pp, "(")
        write(pp, "betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1153 = unwrapped_fields1152[1]
        pretty_relation_id(pp, field1153)
        newline(pp)
        field1154 = unwrapped_fields1152[2]
        pretty_betree_info(pp, field1154)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1161 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1161)
        write(pp, flat1161)
        return nothing
    else
        function _t1659(_dollar_dollar)
            _t1660 = deconstruct_betree_info_config(pp, _dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1660,)
        end
        _t1661 = _t1659(msg)
        fields1156 = _t1661
        unwrapped_fields1157 = fields1156
        write(pp, "(")
        write(pp, "betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1158 = unwrapped_fields1157[1]
        pretty_betree_info_key_types(pp, field1158)
        newline(pp)
        field1159 = unwrapped_fields1157[2]
        pretty_betree_info_value_types(pp, field1159)
        newline(pp)
        field1160 = unwrapped_fields1157[3]
        pretty_config_dict(pp, field1160)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1165 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1165)
        write(pp, flat1165)
        return nothing
    else
        fields1162 = msg
        write(pp, "(")
        write(pp, "key_types")
        indent_sexp!(pp)
        if !isempty(fields1162)
            newline(pp)
            for (i1662, elem1163) in enumerate(fields1162)
                i1164 = i1662 - 1
                if (i1164 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1163)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1169 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1169)
        write(pp, flat1169)
        return nothing
    else
        fields1166 = msg
        write(pp, "(")
        write(pp, "value_types")
        indent_sexp!(pp)
        if !isempty(fields1166)
            newline(pp)
            for (i1663, elem1167) in enumerate(fields1166)
                i1168 = i1663 - 1
                if (i1168 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1167)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1176 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1176)
        write(pp, flat1176)
        return nothing
    else
        function _t1664(_dollar_dollar)
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        end
        _t1665 = _t1664(msg)
        fields1170 = _t1665
        unwrapped_fields1171 = fields1170
        write(pp, "(")
        write(pp, "csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1172 = unwrapped_fields1171[1]
        pretty_csvlocator(pp, field1172)
        newline(pp)
        field1173 = unwrapped_fields1171[2]
        pretty_csv_config(pp, field1173)
        newline(pp)
        field1174 = unwrapped_fields1171[3]
        pretty_csv_columns(pp, field1174)
        newline(pp)
        field1175 = unwrapped_fields1171[4]
        pretty_csv_asof(pp, field1175)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1183 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1183)
        write(pp, flat1183)
        return nothing
    else
        function _t1666(_dollar_dollar)
            if !isempty(_dollar_dollar.paths)
                _t1667 = _dollar_dollar.paths
            else
                _t1667 = nothing
            end
            if String(copy(_dollar_dollar.inline_data)) != ""
                _t1668 = String(copy(_dollar_dollar.inline_data))
            else
                _t1668 = nothing
            end
            return (_t1667, _t1668,)
        end
        _t1669 = _t1666(msg)
        fields1177 = _t1669
        unwrapped_fields1178 = fields1177
        write(pp, "(")
        write(pp, "csv_locator")
        indent_sexp!(pp)
        field1179 = unwrapped_fields1178[1]
        if !isnothing(field1179)
            newline(pp)
            opt_val1180 = field1179
            pretty_csv_locator_paths(pp, opt_val1180)
        end
        field1181 = unwrapped_fields1178[2]
        if !isnothing(field1181)
            newline(pp)
            opt_val1182 = field1181
            pretty_csv_locator_inline_data(pp, opt_val1182)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1187 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1187)
        write(pp, flat1187)
        return nothing
    else
        fields1184 = msg
        write(pp, "(")
        write(pp, "paths")
        indent_sexp!(pp)
        if !isempty(fields1184)
            newline(pp)
            for (i1670, elem1185) in enumerate(fields1184)
                i1186 = i1670 - 1
                if (i1186 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1185))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1189 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1189)
        write(pp, flat1189)
        return nothing
    else
        fields1188 = msg
        write(pp, "(")
        write(pp, "inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1188))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1192 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1192)
        write(pp, flat1192)
        return nothing
    else
        function _t1671(_dollar_dollar)
            _t1672 = deconstruct_csv_config(pp, _dollar_dollar)
            return _t1672
        end
        _t1673 = _t1671(msg)
        fields1190 = _t1673
        unwrapped_fields1191 = fields1190
        write(pp, "(")
        write(pp, "csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1191)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.CSVColumn})
    flat1196 = try_flat(pp, msg, pretty_csv_columns)
    if !isnothing(flat1196)
        write(pp, flat1196)
        return nothing
    else
        fields1193 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1193)
            newline(pp)
            for (i1674, elem1194) in enumerate(fields1193)
                i1195 = i1674 - 1
                if (i1195 > 0)
                    newline(pp)
                end
                pretty_csv_column(pp, elem1194)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_column(pp::PrettyPrinter, msg::Proto.CSVColumn)
    flat1202 = try_flat(pp, msg, pretty_csv_column)
    if !isnothing(flat1202)
        write(pp, flat1202)
        return nothing
    else
        function _t1675(_dollar_dollar)
            _t1676 = deconstruct_csv_column_tail(pp, _dollar_dollar)
            return (_dollar_dollar.column_path, _t1676,)
        end
        _t1677 = _t1675(msg)
        fields1197 = _t1677
        unwrapped_fields1198 = fields1197
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1199 = unwrapped_fields1198[1]
        pretty_csv_column_path(pp, field1199)
        field1200 = unwrapped_fields1198[2]
        if !isnothing(field1200)
            newline(pp)
            opt_val1201 = field1200
            pretty_csv_column_tail(pp, opt_val1201)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1209 = try_flat(pp, msg, pretty_csv_column_path)
    if !isnothing(flat1209)
        write(pp, flat1209)
        return nothing
    else
        function _t1678(_dollar_dollar)
            if length(_dollar_dollar) == 1
                _t1679 = _dollar_dollar[1]
            else
                _t1679 = nothing
            end
            return _t1679
        end
        _t1680 = _t1678(msg)
        deconstruct_result1207 = _t1680
        if !isnothing(deconstruct_result1207)
            unwrapped1208 = deconstruct_result1207
            write(pp, format_string(pp, unwrapped1208))
        else
            function _t1681(_dollar_dollar)
                if length(_dollar_dollar) != 1
                    _t1682 = _dollar_dollar
                else
                    _t1682 = nothing
                end
                return _t1682
            end
            _t1683 = _t1681(msg)
            deconstruct_result1203 = _t1683
            if !isnothing(deconstruct_result1203)
                unwrapped1204 = deconstruct_result1203
                write(pp, "[")
                indent!(pp)
                for (i1684, elem1205) in enumerate(unwrapped1204)
                    i1206 = i1684 - 1
                    if (i1206 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(pp, elem1205))
                end
                dedent!(pp)
                write(pp, "]")
            else
                throw(ParseError("No matching rule for csv_column_path"))
            end
        end
    end
    return nothing
end

function pretty_csv_column_tail(pp::PrettyPrinter, msg::Tuple{Union{Nothing, Proto.RelationId}, Vector{Proto.var"#Type"}})
    flat1220 = try_flat(pp, msg, pretty_csv_column_tail)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        function _t1685(_dollar_dollar)
            if !isnothing(_dollar_dollar[1])
                _t1686 = (_dollar_dollar[1], _dollar_dollar[2],)
            else
                _t1686 = nothing
            end
            return _t1686
        end
        _t1687 = _t1685(msg)
        deconstruct_result1214 = _t1687
        if !isnothing(deconstruct_result1214)
            unwrapped1215 = deconstruct_result1214
            field1216 = unwrapped1215[1]
            pretty_relation_id(pp, field1216)
            write(pp, " ")
            write(pp, "[")
            field1217 = unwrapped1215[2]
            for (i1688, elem1218) in enumerate(field1217)
                i1219 = i1688 - 1
                if (i1219 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1218)
            end
            write(pp, "]")
        else
            function _t1689(_dollar_dollar)
                return _dollar_dollar[2]
            end
            _t1690 = _t1689(msg)
            fields1210 = _t1690
            unwrapped_fields1211 = fields1210
            write(pp, "[")
            indent!(pp)
            for (i1691, elem1212) in enumerate(unwrapped_fields1211)
                i1213 = i1691 - 1
                if (i1213 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1212)
            end
            dedent!(pp)
            write(pp, "]")
        end
    end
    return nothing
end

function pretty_csv_asof(pp::PrettyPrinter, msg::String)
    flat1222 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1222)
        write(pp, flat1222)
        return nothing
    else
        fields1221 = msg
        write(pp, "(")
        write(pp, "asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1221))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1225 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1225)
        write(pp, flat1225)
        return nothing
    else
        function _t1692(_dollar_dollar)
            return _dollar_dollar.fragment_id
        end
        _t1693 = _t1692(msg)
        fields1223 = _t1693
        unwrapped_fields1224 = fields1223
        write(pp, "(")
        write(pp, "undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1224)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1230 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1230)
        write(pp, flat1230)
        return nothing
    else
        function _t1694(_dollar_dollar)
            return _dollar_dollar.relations
        end
        _t1695 = _t1694(msg)
        fields1226 = _t1695
        unwrapped_fields1227 = fields1226
        write(pp, "(")
        write(pp, "context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1227)
            newline(pp)
            for (i1696, elem1228) in enumerate(unwrapped_fields1227)
                i1229 = i1696 - 1
                if (i1229 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1228)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1235 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1235)
        write(pp, flat1235)
        return nothing
    else
        function _t1697(_dollar_dollar)
            return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        end
        _t1698 = _t1697(msg)
        fields1231 = _t1698
        unwrapped_fields1232 = fields1231
        write(pp, "(")
        write(pp, "snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1233 = unwrapped_fields1232[1]
        pretty_rel_edb_path(pp, field1233)
        newline(pp)
        field1234 = unwrapped_fields1232[2]
        pretty_relation_id(pp, field1234)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1239 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1239)
        write(pp, flat1239)
        return nothing
    else
        fields1236 = msg
        write(pp, "(")
        write(pp, "reads")
        indent_sexp!(pp)
        if !isempty(fields1236)
            newline(pp)
            for (i1699, elem1237) in enumerate(fields1236)
                i1238 = i1699 - 1
                if (i1238 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1237)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1250 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1250)
        write(pp, flat1250)
        return nothing
    else
        function _t1700(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("demand"))
                _t1701 = _get_oneof_field(_dollar_dollar, :demand)
            else
                _t1701 = nothing
            end
            return _t1701
        end
        _t1702 = _t1700(msg)
        deconstruct_result1248 = _t1702
        if !isnothing(deconstruct_result1248)
            unwrapped1249 = deconstruct_result1248
            pretty_demand(pp, unwrapped1249)
        else
            function _t1703(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("output"))
                    _t1704 = _get_oneof_field(_dollar_dollar, :output)
                else
                    _t1704 = nothing
                end
                return _t1704
            end
            _t1705 = _t1703(msg)
            deconstruct_result1246 = _t1705
            if !isnothing(deconstruct_result1246)
                unwrapped1247 = deconstruct_result1246
                pretty_output(pp, unwrapped1247)
            else
                function _t1706(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                        _t1707 = _get_oneof_field(_dollar_dollar, :what_if)
                    else
                        _t1707 = nothing
                    end
                    return _t1707
                end
                _t1708 = _t1706(msg)
                deconstruct_result1244 = _t1708
                if !isnothing(deconstruct_result1244)
                    unwrapped1245 = deconstruct_result1244
                    pretty_what_if(pp, unwrapped1245)
                else
                    function _t1709(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("abort"))
                            _t1710 = _get_oneof_field(_dollar_dollar, :abort)
                        else
                            _t1710 = nothing
                        end
                        return _t1710
                    end
                    _t1711 = _t1709(msg)
                    deconstruct_result1242 = _t1711
                    if !isnothing(deconstruct_result1242)
                        unwrapped1243 = deconstruct_result1242
                        pretty_abort(pp, unwrapped1243)
                    else
                        function _t1712(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("#export"))
                                _t1713 = _get_oneof_field(_dollar_dollar, :var"#export")
                            else
                                _t1713 = nothing
                            end
                            return _t1713
                        end
                        _t1714 = _t1712(msg)
                        deconstruct_result1240 = _t1714
                        if !isnothing(deconstruct_result1240)
                            unwrapped1241 = deconstruct_result1240
                            pretty_export(pp, unwrapped1241)
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
    flat1253 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        function _t1715(_dollar_dollar)
            return _dollar_dollar.relation_id
        end
        _t1716 = _t1715(msg)
        fields1251 = _t1716
        unwrapped_fields1252 = fields1251
        write(pp, "(")
        write(pp, "demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1252)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1258 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1258)
        write(pp, flat1258)
        return nothing
    else
        function _t1717(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        end
        _t1718 = _t1717(msg)
        fields1254 = _t1718
        unwrapped_fields1255 = fields1254
        write(pp, "(")
        write(pp, "output")
        indent_sexp!(pp)
        newline(pp)
        field1256 = unwrapped_fields1255[1]
        pretty_name(pp, field1256)
        newline(pp)
        field1257 = unwrapped_fields1255[2]
        pretty_relation_id(pp, field1257)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1263 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1263)
        write(pp, flat1263)
        return nothing
    else
        function _t1719(_dollar_dollar)
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        end
        _t1720 = _t1719(msg)
        fields1259 = _t1720
        unwrapped_fields1260 = fields1259
        write(pp, "(")
        write(pp, "what_if")
        indent_sexp!(pp)
        newline(pp)
        field1261 = unwrapped_fields1260[1]
        pretty_name(pp, field1261)
        newline(pp)
        field1262 = unwrapped_fields1260[2]
        pretty_epoch(pp, field1262)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1269 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1269)
        write(pp, flat1269)
        return nothing
    else
        function _t1721(_dollar_dollar)
            if _dollar_dollar.name != "abort"
                _t1722 = _dollar_dollar.name
            else
                _t1722 = nothing
            end
            return (_t1722, _dollar_dollar.relation_id,)
        end
        _t1723 = _t1721(msg)
        fields1264 = _t1723
        unwrapped_fields1265 = fields1264
        write(pp, "(")
        write(pp, "abort")
        indent_sexp!(pp)
        field1266 = unwrapped_fields1265[1]
        if !isnothing(field1266)
            newline(pp)
            opt_val1267 = field1266
            pretty_name(pp, opt_val1267)
        end
        newline(pp)
        field1268 = unwrapped_fields1265[2]
        pretty_relation_id(pp, field1268)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1272 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1272)
        write(pp, flat1272)
        return nothing
    else
        function _t1724(_dollar_dollar)
            return _get_oneof_field(_dollar_dollar, :csv_config)
        end
        _t1725 = _t1724(msg)
        fields1270 = _t1725
        unwrapped_fields1271 = fields1270
        write(pp, "(")
        write(pp, "export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1271)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1278 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1278)
        write(pp, flat1278)
        return nothing
    else
        function _t1726(_dollar_dollar)
            _t1727 = deconstruct_export_csv_config(pp, _dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1727,)
        end
        _t1728 = _t1726(msg)
        fields1273 = _t1728
        unwrapped_fields1274 = fields1273
        write(pp, "(")
        write(pp, "export_csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1275 = unwrapped_fields1274[1]
        pretty_export_csv_path(pp, field1275)
        newline(pp)
        field1276 = unwrapped_fields1274[2]
        pretty_export_csv_columns(pp, field1276)
        newline(pp)
        field1277 = unwrapped_fields1274[3]
        pretty_config_dict(pp, field1277)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1280 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1280)
        write(pp, flat1280)
        return nothing
    else
        fields1279 = msg
        write(pp, "(")
        write(pp, "path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1279))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1284 = try_flat(pp, msg, pretty_export_csv_columns)
    if !isnothing(flat1284)
        write(pp, flat1284)
        return nothing
    else
        fields1281 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1281)
            newline(pp)
            for (i1729, elem1282) in enumerate(fields1281)
                i1283 = i1729 - 1
                if (i1283 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1282)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_column(pp::PrettyPrinter, msg::Proto.ExportCSVColumn)
    flat1289 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1289)
        write(pp, flat1289)
        return nothing
    else
        function _t1730(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        end
        _t1731 = _t1730(msg)
        fields1285 = _t1731
        unwrapped_fields1286 = fields1285
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1287 = unwrapped_fields1286[1]
        write(pp, format_string(pp, field1287))
        newline(pp)
        field1288 = unwrapped_fields1286[2]
        pretty_relation_id(pp, field1288)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1770, _rid) in enumerate(msg.ids)
        _idx = i1770 - 1
        newline(pp)
        write(pp, "(")
        _t1771 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1771)
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
    for (i1772, _elem) in enumerate(msg.keys)
        _idx = i1772 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values ")
    write(pp, "(")
    for (i1773, _elem) in enumerate(msg.values)
        _idx = i1773 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Tuple{Union{Nothing, Proto.RelationId}, Vector{Proto.var"#Type"}}) = pretty_csv_column_tail(pp, x)
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
