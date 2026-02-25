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
    _t1723 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1723
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1724 = Proto.Value(value=OneOf(:int_value, v))
    return _t1724
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1725 = Proto.Value(value=OneOf(:float_value, v))
    return _t1725
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1726 = Proto.Value(value=OneOf(:string_value, v))
    return _t1726
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1727 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1727
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1728 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1728
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1729 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1729,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1730 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1730,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1731 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1731,))
            end
        end
    end
    _t1732 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1732,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1733 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1733,))
    _t1734 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1734,))
    if msg.new_line != ""
        _t1735 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1735,))
    end
    _t1736 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1736,))
    _t1737 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1737,))
    _t1738 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1738,))
    if msg.comment != ""
        _t1739 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1739,))
    end
    for missing_string in msg.missing_strings
        _t1740 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1740,))
    end
    _t1741 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1741,))
    _t1742 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1742,))
    _t1743 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1743,))
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1744 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1744,))
    _t1745 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1745,))
    _t1746 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1746,))
    _t1747 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1747,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1748 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1748,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1749 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1749,))
        end
    end
    _t1750 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1750,))
    _t1751 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1751,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1752 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1752,))
    end
    if !isnothing(msg.compression)
        _t1753 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1753,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1754 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1754,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1755 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1755,))
    end
    if !isnothing(msg.syntax_delim)
        _t1756 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1756,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1757 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1757,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1758 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1758,))
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
        _t1759 = nothing
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
    flat651 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat651)
        write(pp, flat651)
        return nothing
    else
        function _t1284(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("configure"))
                _t1285 = _dollar_dollar.configure
            else
                _t1285 = nothing
            end
            if _has_proto_field(_dollar_dollar, Symbol("sync"))
                _t1286 = _dollar_dollar.sync
            else
                _t1286 = nothing
            end
            return (_t1285, _t1286, _dollar_dollar.epochs,)
        end
        _t1287 = _t1284(msg)
        fields642 = _t1287
        unwrapped_fields643 = fields642
        write(pp, "(")
        write(pp, "transaction")
        indent_sexp!(pp)
        field644 = unwrapped_fields643[1]
        if !isnothing(field644)
            newline(pp)
            opt_val645 = field644
            pretty_configure(pp, opt_val645)
        end
        field646 = unwrapped_fields643[2]
        if !isnothing(field646)
            newline(pp)
            opt_val647 = field646
            pretty_sync(pp, opt_val647)
        end
        field648 = unwrapped_fields643[3]
        if !isempty(field648)
            newline(pp)
            for (i1288, elem649) in enumerate(field648)
                i650 = i1288 - 1
                if (i650 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem649)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat654 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat654)
        write(pp, flat654)
        return nothing
    else
        function _t1289(_dollar_dollar)
            _t1290 = deconstruct_configure(pp, _dollar_dollar)
            return _t1290
        end
        _t1291 = _t1289(msg)
        fields652 = _t1291
        unwrapped_fields653 = fields652
        write(pp, "(")
        write(pp, "configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields653)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat658 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat658)
        write(pp, flat658)
        return nothing
    else
        fields655 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields655)
            newline(pp)
            for (i1292, elem656) in enumerate(fields655)
                i657 = i1292 - 1
                if (i657 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem656)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat663 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat663)
        write(pp, flat663)
        return nothing
    else
        function _t1293(_dollar_dollar)
            return (_dollar_dollar[1], _dollar_dollar[2],)
        end
        _t1294 = _t1293(msg)
        fields659 = _t1294
        unwrapped_fields660 = fields659
        write(pp, ":")
        field661 = unwrapped_fields660[1]
        write(pp, field661)
        write(pp, " ")
        field662 = unwrapped_fields660[2]
        pretty_value(pp, field662)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat683 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat683)
        write(pp, flat683)
        return nothing
    else
        function _t1295(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("date_value"))
                _t1296 = _get_oneof_field(_dollar_dollar, :date_value)
            else
                _t1296 = nothing
            end
            return _t1296
        end
        _t1297 = _t1295(msg)
        deconstruct_result681 = _t1297
        if !isnothing(deconstruct_result681)
            unwrapped682 = deconstruct_result681
            pretty_date(pp, unwrapped682)
        else
            function _t1298(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                    _t1299 = _get_oneof_field(_dollar_dollar, :datetime_value)
                else
                    _t1299 = nothing
                end
                return _t1299
            end
            _t1300 = _t1298(msg)
            deconstruct_result679 = _t1300
            if !isnothing(deconstruct_result679)
                unwrapped680 = deconstruct_result679
                pretty_datetime(pp, unwrapped680)
            else
                function _t1301(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                        _t1302 = _get_oneof_field(_dollar_dollar, :string_value)
                    else
                        _t1302 = nothing
                    end
                    return _t1302
                end
                _t1303 = _t1301(msg)
                deconstruct_result677 = _t1303
                if !isnothing(deconstruct_result677)
                    unwrapped678 = deconstruct_result677
                    write(pp, format_string(pp, unwrapped678))
                else
                    function _t1304(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1305 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1305 = nothing
                        end
                        return _t1305
                    end
                    _t1306 = _t1304(msg)
                    deconstruct_result675 = _t1306
                    if !isnothing(deconstruct_result675)
                        unwrapped676 = deconstruct_result675
                        write(pp, format_int(pp, unwrapped676))
                    else
                        function _t1307(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                _t1308 = _get_oneof_field(_dollar_dollar, :float_value)
                            else
                                _t1308 = nothing
                            end
                            return _t1308
                        end
                        _t1309 = _t1307(msg)
                        deconstruct_result673 = _t1309
                        if !isnothing(deconstruct_result673)
                            unwrapped674 = deconstruct_result673
                            write(pp, format_float(pp, unwrapped674))
                        else
                            function _t1310(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                    _t1311 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                else
                                    _t1311 = nothing
                                end
                                return _t1311
                            end
                            _t1312 = _t1310(msg)
                            deconstruct_result671 = _t1312
                            if !isnothing(deconstruct_result671)
                                unwrapped672 = deconstruct_result671
                                write(pp, format_uint128(pp, unwrapped672))
                            else
                                function _t1313(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                        _t1314 = _get_oneof_field(_dollar_dollar, :int128_value)
                                    else
                                        _t1314 = nothing
                                    end
                                    return _t1314
                                end
                                _t1315 = _t1313(msg)
                                deconstruct_result669 = _t1315
                                if !isnothing(deconstruct_result669)
                                    unwrapped670 = deconstruct_result669
                                    write(pp, format_int128(pp, unwrapped670))
                                else
                                    function _t1316(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                            _t1317 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                        else
                                            _t1317 = nothing
                                        end
                                        return _t1317
                                    end
                                    _t1318 = _t1316(msg)
                                    deconstruct_result667 = _t1318
                                    if !isnothing(deconstruct_result667)
                                        unwrapped668 = deconstruct_result667
                                        write(pp, format_decimal(pp, unwrapped668))
                                    else
                                        function _t1319(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                _t1320 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                            else
                                                _t1320 = nothing
                                            end
                                            return _t1320
                                        end
                                        _t1321 = _t1319(msg)
                                        deconstruct_result665 = _t1321
                                        if !isnothing(deconstruct_result665)
                                            unwrapped666 = deconstruct_result665
                                            pretty_boolean_value(pp, unwrapped666)
                                        else
                                            fields664 = msg
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
    flat689 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat689)
        write(pp, flat689)
        return nothing
    else
        function _t1322(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        end
        _t1323 = _t1322(msg)
        fields684 = _t1323
        unwrapped_fields685 = fields684
        write(pp, "(")
        write(pp, "date")
        indent_sexp!(pp)
        newline(pp)
        field686 = unwrapped_fields685[1]
        write(pp, format_int(pp, field686))
        newline(pp)
        field687 = unwrapped_fields685[2]
        write(pp, format_int(pp, field687))
        newline(pp)
        field688 = unwrapped_fields685[3]
        write(pp, format_int(pp, field688))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat700 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat700)
        write(pp, flat700)
        return nothing
    else
        function _t1324(_dollar_dollar)
            return (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        end
        _t1325 = _t1324(msg)
        fields690 = _t1325
        unwrapped_fields691 = fields690
        write(pp, "(")
        write(pp, "datetime")
        indent_sexp!(pp)
        newline(pp)
        field692 = unwrapped_fields691[1]
        write(pp, format_int(pp, field692))
        newline(pp)
        field693 = unwrapped_fields691[2]
        write(pp, format_int(pp, field693))
        newline(pp)
        field694 = unwrapped_fields691[3]
        write(pp, format_int(pp, field694))
        newline(pp)
        field695 = unwrapped_fields691[4]
        write(pp, format_int(pp, field695))
        newline(pp)
        field696 = unwrapped_fields691[5]
        write(pp, format_int(pp, field696))
        newline(pp)
        field697 = unwrapped_fields691[6]
        write(pp, format_int(pp, field697))
        field698 = unwrapped_fields691[7]
        if !isnothing(field698)
            newline(pp)
            opt_val699 = field698
            write(pp, format_int(pp, opt_val699))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    function _t1326(_dollar_dollar)
        if _dollar_dollar
            _t1327 = ()
        else
            _t1327 = nothing
        end
        return _t1327
    end
    _t1328 = _t1326(msg)
    deconstruct_result703 = _t1328
    if !isnothing(deconstruct_result703)
        unwrapped704 = deconstruct_result703
        write(pp, "true")
    else
        function _t1329(_dollar_dollar)
            if !_dollar_dollar
                _t1330 = ()
            else
                _t1330 = nothing
            end
            return _t1330
        end
        _t1331 = _t1329(msg)
        deconstruct_result701 = _t1331
        if !isnothing(deconstruct_result701)
            unwrapped702 = deconstruct_result701
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat709 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat709)
        write(pp, flat709)
        return nothing
    else
        function _t1332(_dollar_dollar)
            return _dollar_dollar.fragments
        end
        _t1333 = _t1332(msg)
        fields705 = _t1333
        unwrapped_fields706 = fields705
        write(pp, "(")
        write(pp, "sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields706)
            newline(pp)
            for (i1334, elem707) in enumerate(unwrapped_fields706)
                i708 = i1334 - 1
                if (i708 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem707)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat712 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat712)
        write(pp, flat712)
        return nothing
    else
        function _t1335(_dollar_dollar)
            return fragment_id_to_string(pp, _dollar_dollar)
        end
        _t1336 = _t1335(msg)
        fields710 = _t1336
        unwrapped_fields711 = fields710
        write(pp, ":")
        write(pp, unwrapped_fields711)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat719 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat719)
        write(pp, flat719)
        return nothing
    else
        function _t1337(_dollar_dollar)
            if !isempty(_dollar_dollar.writes)
                _t1338 = _dollar_dollar.writes
            else
                _t1338 = nothing
            end
            if !isempty(_dollar_dollar.reads)
                _t1339 = _dollar_dollar.reads
            else
                _t1339 = nothing
            end
            return (_t1338, _t1339,)
        end
        _t1340 = _t1337(msg)
        fields713 = _t1340
        unwrapped_fields714 = fields713
        write(pp, "(")
        write(pp, "epoch")
        indent_sexp!(pp)
        field715 = unwrapped_fields714[1]
        if !isnothing(field715)
            newline(pp)
            opt_val716 = field715
            pretty_epoch_writes(pp, opt_val716)
        end
        field717 = unwrapped_fields714[2]
        if !isnothing(field717)
            newline(pp)
            opt_val718 = field717
            pretty_epoch_reads(pp, opt_val718)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat723 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat723)
        write(pp, flat723)
        return nothing
    else
        fields720 = msg
        write(pp, "(")
        write(pp, "writes")
        indent_sexp!(pp)
        if !isempty(fields720)
            newline(pp)
            for (i1341, elem721) in enumerate(fields720)
                i722 = i1341 - 1
                if (i722 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem721)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat732 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat732)
        write(pp, flat732)
        return nothing
    else
        function _t1342(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("define"))
                _t1343 = _get_oneof_field(_dollar_dollar, :define)
            else
                _t1343 = nothing
            end
            return _t1343
        end
        _t1344 = _t1342(msg)
        deconstruct_result730 = _t1344
        if !isnothing(deconstruct_result730)
            unwrapped731 = deconstruct_result730
            pretty_define(pp, unwrapped731)
        else
            function _t1345(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                    _t1346 = _get_oneof_field(_dollar_dollar, :undefine)
                else
                    _t1346 = nothing
                end
                return _t1346
            end
            _t1347 = _t1345(msg)
            deconstruct_result728 = _t1347
            if !isnothing(deconstruct_result728)
                unwrapped729 = deconstruct_result728
                pretty_undefine(pp, unwrapped729)
            else
                function _t1348(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("context"))
                        _t1349 = _get_oneof_field(_dollar_dollar, :context)
                    else
                        _t1349 = nothing
                    end
                    return _t1349
                end
                _t1350 = _t1348(msg)
                deconstruct_result726 = _t1350
                if !isnothing(deconstruct_result726)
                    unwrapped727 = deconstruct_result726
                    pretty_context(pp, unwrapped727)
                else
                    function _t1351(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                            _t1352 = _get_oneof_field(_dollar_dollar, :snapshot)
                        else
                            _t1352 = nothing
                        end
                        return _t1352
                    end
                    _t1353 = _t1351(msg)
                    deconstruct_result724 = _t1353
                    if !isnothing(deconstruct_result724)
                        unwrapped725 = deconstruct_result724
                        pretty_snapshot(pp, unwrapped725)
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
    flat735 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat735)
        write(pp, flat735)
        return nothing
    else
        function _t1354(_dollar_dollar)
            return _dollar_dollar.fragment
        end
        _t1355 = _t1354(msg)
        fields733 = _t1355
        unwrapped_fields734 = fields733
        write(pp, "(")
        write(pp, "define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields734)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat742 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat742)
        write(pp, flat742)
        return nothing
    else
        function _t1356(_dollar_dollar)
            start_pretty_fragment(pp, _dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        end
        _t1357 = _t1356(msg)
        fields736 = _t1357
        unwrapped_fields737 = fields736
        write(pp, "(")
        write(pp, "fragment")
        indent_sexp!(pp)
        newline(pp)
        field738 = unwrapped_fields737[1]
        pretty_new_fragment_id(pp, field738)
        field739 = unwrapped_fields737[2]
        if !isempty(field739)
            newline(pp)
            for (i1358, elem740) in enumerate(field739)
                i741 = i1358 - 1
                if (i741 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem740)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat744 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat744)
        write(pp, flat744)
        return nothing
    else
        fields743 = msg
        pretty_fragment_id(pp, fields743)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat753 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat753)
        write(pp, flat753)
        return nothing
    else
        function _t1359(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("def"))
                _t1360 = _get_oneof_field(_dollar_dollar, :def)
            else
                _t1360 = nothing
            end
            return _t1360
        end
        _t1361 = _t1359(msg)
        deconstruct_result751 = _t1361
        if !isnothing(deconstruct_result751)
            unwrapped752 = deconstruct_result751
            pretty_def(pp, unwrapped752)
        else
            function _t1362(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                    _t1363 = _get_oneof_field(_dollar_dollar, :algorithm)
                else
                    _t1363 = nothing
                end
                return _t1363
            end
            _t1364 = _t1362(msg)
            deconstruct_result749 = _t1364
            if !isnothing(deconstruct_result749)
                unwrapped750 = deconstruct_result749
                pretty_algorithm(pp, unwrapped750)
            else
                function _t1365(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                        _t1366 = _get_oneof_field(_dollar_dollar, :constraint)
                    else
                        _t1366 = nothing
                    end
                    return _t1366
                end
                _t1367 = _t1365(msg)
                deconstruct_result747 = _t1367
                if !isnothing(deconstruct_result747)
                    unwrapped748 = deconstruct_result747
                    pretty_constraint(pp, unwrapped748)
                else
                    function _t1368(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("data"))
                            _t1369 = _get_oneof_field(_dollar_dollar, :data)
                        else
                            _t1369 = nothing
                        end
                        return _t1369
                    end
                    _t1370 = _t1368(msg)
                    deconstruct_result745 = _t1370
                    if !isnothing(deconstruct_result745)
                        unwrapped746 = deconstruct_result745
                        pretty_data(pp, unwrapped746)
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
    flat760 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat760)
        write(pp, flat760)
        return nothing
    else
        function _t1371(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1372 = _dollar_dollar.attrs
            else
                _t1372 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1372,)
        end
        _t1373 = _t1371(msg)
        fields754 = _t1373
        unwrapped_fields755 = fields754
        write(pp, "(")
        write(pp, "def")
        indent_sexp!(pp)
        newline(pp)
        field756 = unwrapped_fields755[1]
        pretty_relation_id(pp, field756)
        newline(pp)
        field757 = unwrapped_fields755[2]
        pretty_abstraction(pp, field757)
        field758 = unwrapped_fields755[3]
        if !isnothing(field758)
            newline(pp)
            opt_val759 = field758
            pretty_attrs(pp, opt_val759)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat765 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat765)
        write(pp, flat765)
        return nothing
    else
        function _t1374(_dollar_dollar)
            if !isnothing(relation_id_to_string(pp, _dollar_dollar))
                _t1376 = deconstruct_relation_id_string(pp, _dollar_dollar)
                _t1375 = _t1376
            else
                _t1375 = nothing
            end
            return _t1375
        end
        _t1377 = _t1374(msg)
        deconstruct_result763 = _t1377
        if !isnothing(deconstruct_result763)
            unwrapped764 = deconstruct_result763
            write(pp, ":")
            write(pp, unwrapped764)
        else
            function _t1378(_dollar_dollar)
                _t1379 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
                return _t1379
            end
            _t1380 = _t1378(msg)
            deconstruct_result761 = _t1380
            if !isnothing(deconstruct_result761)
                unwrapped762 = deconstruct_result761
                write(pp, format_uint128(pp, unwrapped762))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat770 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat770)
        write(pp, flat770)
        return nothing
    else
        function _t1381(_dollar_dollar)
            _t1382 = deconstruct_bindings(pp, _dollar_dollar)
            return (_t1382, _dollar_dollar.value,)
        end
        _t1383 = _t1381(msg)
        fields766 = _t1383
        unwrapped_fields767 = fields766
        write(pp, "(")
        indent!(pp)
        field768 = unwrapped_fields767[1]
        pretty_bindings(pp, field768)
        newline(pp)
        field769 = unwrapped_fields767[2]
        pretty_formula(pp, field769)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat778 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat778)
        write(pp, flat778)
        return nothing
    else
        function _t1384(_dollar_dollar)
            if !isempty(_dollar_dollar[2])
                _t1385 = _dollar_dollar[2]
            else
                _t1385 = nothing
            end
            return (_dollar_dollar[1], _t1385,)
        end
        _t1386 = _t1384(msg)
        fields771 = _t1386
        unwrapped_fields772 = fields771
        write(pp, "[")
        indent!(pp)
        field773 = unwrapped_fields772[1]
        for (i1387, elem774) in enumerate(field773)
            i775 = i1387 - 1
            if (i775 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem774)
        end
        field776 = unwrapped_fields772[2]
        if !isnothing(field776)
            newline(pp)
            opt_val777 = field776
            pretty_value_bindings(pp, opt_val777)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat783 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat783)
        write(pp, flat783)
        return nothing
    else
        function _t1388(_dollar_dollar)
            return (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        end
        _t1389 = _t1388(msg)
        fields779 = _t1389
        unwrapped_fields780 = fields779
        field781 = unwrapped_fields780[1]
        write(pp, field781)
        write(pp, "::")
        field782 = unwrapped_fields780[2]
        pretty_type(pp, field782)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat806 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat806)
        write(pp, flat806)
        return nothing
    else
        function _t1390(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
                _t1391 = _get_oneof_field(_dollar_dollar, :unspecified_type)
            else
                _t1391 = nothing
            end
            return _t1391
        end
        _t1392 = _t1390(msg)
        deconstruct_result804 = _t1392
        if !isnothing(deconstruct_result804)
            unwrapped805 = deconstruct_result804
            pretty_unspecified_type(pp, unwrapped805)
        else
            function _t1393(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                    _t1394 = _get_oneof_field(_dollar_dollar, :string_type)
                else
                    _t1394 = nothing
                end
                return _t1394
            end
            _t1395 = _t1393(msg)
            deconstruct_result802 = _t1395
            if !isnothing(deconstruct_result802)
                unwrapped803 = deconstruct_result802
                pretty_string_type(pp, unwrapped803)
            else
                function _t1396(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                        _t1397 = _get_oneof_field(_dollar_dollar, :int_type)
                    else
                        _t1397 = nothing
                    end
                    return _t1397
                end
                _t1398 = _t1396(msg)
                deconstruct_result800 = _t1398
                if !isnothing(deconstruct_result800)
                    unwrapped801 = deconstruct_result800
                    pretty_int_type(pp, unwrapped801)
                else
                    function _t1399(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                            _t1400 = _get_oneof_field(_dollar_dollar, :float_type)
                        else
                            _t1400 = nothing
                        end
                        return _t1400
                    end
                    _t1401 = _t1399(msg)
                    deconstruct_result798 = _t1401
                    if !isnothing(deconstruct_result798)
                        unwrapped799 = deconstruct_result798
                        pretty_float_type(pp, unwrapped799)
                    else
                        function _t1402(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                                _t1403 = _get_oneof_field(_dollar_dollar, :uint128_type)
                            else
                                _t1403 = nothing
                            end
                            return _t1403
                        end
                        _t1404 = _t1402(msg)
                        deconstruct_result796 = _t1404
                        if !isnothing(deconstruct_result796)
                            unwrapped797 = deconstruct_result796
                            pretty_uint128_type(pp, unwrapped797)
                        else
                            function _t1405(_dollar_dollar)
                                if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                    _t1406 = _get_oneof_field(_dollar_dollar, :int128_type)
                                else
                                    _t1406 = nothing
                                end
                                return _t1406
                            end
                            _t1407 = _t1405(msg)
                            deconstruct_result794 = _t1407
                            if !isnothing(deconstruct_result794)
                                unwrapped795 = deconstruct_result794
                                pretty_int128_type(pp, unwrapped795)
                            else
                                function _t1408(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                        _t1409 = _get_oneof_field(_dollar_dollar, :date_type)
                                    else
                                        _t1409 = nothing
                                    end
                                    return _t1409
                                end
                                _t1410 = _t1408(msg)
                                deconstruct_result792 = _t1410
                                if !isnothing(deconstruct_result792)
                                    unwrapped793 = deconstruct_result792
                                    pretty_date_type(pp, unwrapped793)
                                else
                                    function _t1411(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                            _t1412 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                        else
                                            _t1412 = nothing
                                        end
                                        return _t1412
                                    end
                                    _t1413 = _t1411(msg)
                                    deconstruct_result790 = _t1413
                                    if !isnothing(deconstruct_result790)
                                        unwrapped791 = deconstruct_result790
                                        pretty_datetime_type(pp, unwrapped791)
                                    else
                                        function _t1414(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                                _t1415 = _get_oneof_field(_dollar_dollar, :missing_type)
                                            else
                                                _t1415 = nothing
                                            end
                                            return _t1415
                                        end
                                        _t1416 = _t1414(msg)
                                        deconstruct_result788 = _t1416
                                        if !isnothing(deconstruct_result788)
                                            unwrapped789 = deconstruct_result788
                                            pretty_missing_type(pp, unwrapped789)
                                        else
                                            function _t1417(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                    _t1418 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                                else
                                                    _t1418 = nothing
                                                end
                                                return _t1418
                                            end
                                            _t1419 = _t1417(msg)
                                            deconstruct_result786 = _t1419
                                            if !isnothing(deconstruct_result786)
                                                unwrapped787 = deconstruct_result786
                                                pretty_decimal_type(pp, unwrapped787)
                                            else
                                                function _t1420(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                        _t1421 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                    else
                                                        _t1421 = nothing
                                                    end
                                                    return _t1421
                                                end
                                                _t1422 = _t1420(msg)
                                                deconstruct_result784 = _t1422
                                                if !isnothing(deconstruct_result784)
                                                    unwrapped785 = deconstruct_result784
                                                    pretty_boolean_type(pp, unwrapped785)
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
    fields807 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields808 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields809 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields810 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields811 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields812 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields813 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields814 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields815 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat820 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat820)
        write(pp, flat820)
        return nothing
    else
        function _t1423(_dollar_dollar)
            return (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        end
        _t1424 = _t1423(msg)
        fields816 = _t1424
        unwrapped_fields817 = fields816
        write(pp, "(")
        write(pp, "DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field818 = unwrapped_fields817[1]
        write(pp, format_int(pp, field818))
        newline(pp)
        field819 = unwrapped_fields817[2]
        write(pp, format_int(pp, field819))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields821 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat825 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat825)
        write(pp, flat825)
        return nothing
    else
        fields822 = msg
        write(pp, "|")
        if !isempty(fields822)
            write(pp, " ")
            for (i1425, elem823) in enumerate(fields822)
                i824 = i1425 - 1
                if (i824 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem823)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat852 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat852)
        write(pp, flat852)
        return nothing
    else
        function _t1426(_dollar_dollar)
            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                _t1427 = _get_oneof_field(_dollar_dollar, :conjunction)
            else
                _t1427 = nothing
            end
            return _t1427
        end
        _t1428 = _t1426(msg)
        deconstruct_result850 = _t1428
        if !isnothing(deconstruct_result850)
            unwrapped851 = deconstruct_result850
            pretty_true(pp, unwrapped851)
        else
            function _t1429(_dollar_dollar)
                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                    _t1430 = _get_oneof_field(_dollar_dollar, :disjunction)
                else
                    _t1430 = nothing
                end
                return _t1430
            end
            _t1431 = _t1429(msg)
            deconstruct_result848 = _t1431
            if !isnothing(deconstruct_result848)
                unwrapped849 = deconstruct_result848
                pretty_false(pp, unwrapped849)
            else
                function _t1432(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("exists"))
                        _t1433 = _get_oneof_field(_dollar_dollar, :exists)
                    else
                        _t1433 = nothing
                    end
                    return _t1433
                end
                _t1434 = _t1432(msg)
                deconstruct_result846 = _t1434
                if !isnothing(deconstruct_result846)
                    unwrapped847 = deconstruct_result846
                    pretty_exists(pp, unwrapped847)
                else
                    function _t1435(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                            _t1436 = _get_oneof_field(_dollar_dollar, :reduce)
                        else
                            _t1436 = nothing
                        end
                        return _t1436
                    end
                    _t1437 = _t1435(msg)
                    deconstruct_result844 = _t1437
                    if !isnothing(deconstruct_result844)
                        unwrapped845 = deconstruct_result844
                        pretty_reduce(pp, unwrapped845)
                    else
                        function _t1438(_dollar_dollar)
                            if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                                _t1439 = _get_oneof_field(_dollar_dollar, :conjunction)
                            else
                                _t1439 = nothing
                            end
                            return _t1439
                        end
                        _t1440 = _t1438(msg)
                        deconstruct_result842 = _t1440
                        if !isnothing(deconstruct_result842)
                            unwrapped843 = deconstruct_result842
                            pretty_conjunction(pp, unwrapped843)
                        else
                            function _t1441(_dollar_dollar)
                                if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                    _t1442 = _get_oneof_field(_dollar_dollar, :disjunction)
                                else
                                    _t1442 = nothing
                                end
                                return _t1442
                            end
                            _t1443 = _t1441(msg)
                            deconstruct_result840 = _t1443
                            if !isnothing(deconstruct_result840)
                                unwrapped841 = deconstruct_result840
                                pretty_disjunction(pp, unwrapped841)
                            else
                                function _t1444(_dollar_dollar)
                                    if _has_proto_field(_dollar_dollar, Symbol("not"))
                                        _t1445 = _get_oneof_field(_dollar_dollar, :not)
                                    else
                                        _t1445 = nothing
                                    end
                                    return _t1445
                                end
                                _t1446 = _t1444(msg)
                                deconstruct_result838 = _t1446
                                if !isnothing(deconstruct_result838)
                                    unwrapped839 = deconstruct_result838
                                    pretty_not(pp, unwrapped839)
                                else
                                    function _t1447(_dollar_dollar)
                                        if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                            _t1448 = _get_oneof_field(_dollar_dollar, :ffi)
                                        else
                                            _t1448 = nothing
                                        end
                                        return _t1448
                                    end
                                    _t1449 = _t1447(msg)
                                    deconstruct_result836 = _t1449
                                    if !isnothing(deconstruct_result836)
                                        unwrapped837 = deconstruct_result836
                                        pretty_ffi(pp, unwrapped837)
                                    else
                                        function _t1450(_dollar_dollar)
                                            if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                                _t1451 = _get_oneof_field(_dollar_dollar, :atom)
                                            else
                                                _t1451 = nothing
                                            end
                                            return _t1451
                                        end
                                        _t1452 = _t1450(msg)
                                        deconstruct_result834 = _t1452
                                        if !isnothing(deconstruct_result834)
                                            unwrapped835 = deconstruct_result834
                                            pretty_atom(pp, unwrapped835)
                                        else
                                            function _t1453(_dollar_dollar)
                                                if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                    _t1454 = _get_oneof_field(_dollar_dollar, :pragma)
                                                else
                                                    _t1454 = nothing
                                                end
                                                return _t1454
                                            end
                                            _t1455 = _t1453(msg)
                                            deconstruct_result832 = _t1455
                                            if !isnothing(deconstruct_result832)
                                                unwrapped833 = deconstruct_result832
                                                pretty_pragma(pp, unwrapped833)
                                            else
                                                function _t1456(_dollar_dollar)
                                                    if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                        _t1457 = _get_oneof_field(_dollar_dollar, :primitive)
                                                    else
                                                        _t1457 = nothing
                                                    end
                                                    return _t1457
                                                end
                                                _t1458 = _t1456(msg)
                                                deconstruct_result830 = _t1458
                                                if !isnothing(deconstruct_result830)
                                                    unwrapped831 = deconstruct_result830
                                                    pretty_primitive(pp, unwrapped831)
                                                else
                                                    function _t1459(_dollar_dollar)
                                                        if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                            _t1460 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                        else
                                                            _t1460 = nothing
                                                        end
                                                        return _t1460
                                                    end
                                                    _t1461 = _t1459(msg)
                                                    deconstruct_result828 = _t1461
                                                    if !isnothing(deconstruct_result828)
                                                        unwrapped829 = deconstruct_result828
                                                        pretty_rel_atom(pp, unwrapped829)
                                                    else
                                                        function _t1462(_dollar_dollar)
                                                            if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                                _t1463 = _get_oneof_field(_dollar_dollar, :cast)
                                                            else
                                                                _t1463 = nothing
                                                            end
                                                            return _t1463
                                                        end
                                                        _t1464 = _t1462(msg)
                                                        deconstruct_result826 = _t1464
                                                        if !isnothing(deconstruct_result826)
                                                            unwrapped827 = deconstruct_result826
                                                            pretty_cast(pp, unwrapped827)
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
    fields853 = msg
    write(pp, "(")
    write(pp, "true")
    write(pp, ")")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields854 = msg
    write(pp, "(")
    write(pp, "false")
    write(pp, ")")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat859 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat859)
        write(pp, flat859)
        return nothing
    else
        function _t1465(_dollar_dollar)
            _t1466 = deconstruct_bindings(pp, _dollar_dollar.body)
            return (_t1466, _dollar_dollar.body.value,)
        end
        _t1467 = _t1465(msg)
        fields855 = _t1467
        unwrapped_fields856 = fields855
        write(pp, "(")
        write(pp, "exists")
        indent_sexp!(pp)
        newline(pp)
        field857 = unwrapped_fields856[1]
        pretty_bindings(pp, field857)
        newline(pp)
        field858 = unwrapped_fields856[2]
        pretty_formula(pp, field858)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat865 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat865)
        write(pp, flat865)
        return nothing
    else
        function _t1468(_dollar_dollar)
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        end
        _t1469 = _t1468(msg)
        fields860 = _t1469
        unwrapped_fields861 = fields860
        write(pp, "(")
        write(pp, "reduce")
        indent_sexp!(pp)
        newline(pp)
        field862 = unwrapped_fields861[1]
        pretty_abstraction(pp, field862)
        newline(pp)
        field863 = unwrapped_fields861[2]
        pretty_abstraction(pp, field863)
        newline(pp)
        field864 = unwrapped_fields861[3]
        pretty_terms(pp, field864)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat869 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat869)
        write(pp, flat869)
        return nothing
    else
        fields866 = msg
        write(pp, "(")
        write(pp, "terms")
        indent_sexp!(pp)
        if !isempty(fields866)
            newline(pp)
            for (i1470, elem867) in enumerate(fields866)
                i868 = i1470 - 1
                if (i868 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem867)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat874 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat874)
        write(pp, flat874)
        return nothing
    else
        function _t1471(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("var"))
                _t1472 = _get_oneof_field(_dollar_dollar, :var)
            else
                _t1472 = nothing
            end
            return _t1472
        end
        _t1473 = _t1471(msg)
        deconstruct_result872 = _t1473
        if !isnothing(deconstruct_result872)
            unwrapped873 = deconstruct_result872
            pretty_var(pp, unwrapped873)
        else
            function _t1474(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("constant"))
                    _t1475 = _get_oneof_field(_dollar_dollar, :constant)
                else
                    _t1475 = nothing
                end
                return _t1475
            end
            _t1476 = _t1474(msg)
            deconstruct_result870 = _t1476
            if !isnothing(deconstruct_result870)
                unwrapped871 = deconstruct_result870
                pretty_constant(pp, unwrapped871)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat877 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat877)
        write(pp, flat877)
        return nothing
    else
        function _t1477(_dollar_dollar)
            return _dollar_dollar.name
        end
        _t1478 = _t1477(msg)
        fields875 = _t1478
        unwrapped_fields876 = fields875
        write(pp, unwrapped_fields876)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat879 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat879)
        write(pp, flat879)
        return nothing
    else
        fields878 = msg
        pretty_value(pp, fields878)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat884 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat884)
        write(pp, flat884)
        return nothing
    else
        function _t1479(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1480 = _t1479(msg)
        fields880 = _t1480
        unwrapped_fields881 = fields880
        write(pp, "(")
        write(pp, "and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields881)
            newline(pp)
            for (i1481, elem882) in enumerate(unwrapped_fields881)
                i883 = i1481 - 1
                if (i883 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem882)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat889 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat889)
        write(pp, flat889)
        return nothing
    else
        function _t1482(_dollar_dollar)
            return _dollar_dollar.args
        end
        _t1483 = _t1482(msg)
        fields885 = _t1483
        unwrapped_fields886 = fields885
        write(pp, "(")
        write(pp, "or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields886)
            newline(pp)
            for (i1484, elem887) in enumerate(unwrapped_fields886)
                i888 = i1484 - 1
                if (i888 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem887)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat892 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat892)
        write(pp, flat892)
        return nothing
    else
        function _t1485(_dollar_dollar)
            return _dollar_dollar.arg
        end
        _t1486 = _t1485(msg)
        fields890 = _t1486
        unwrapped_fields891 = fields890
        write(pp, "(")
        write(pp, "not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields891)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat898 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat898)
        write(pp, flat898)
        return nothing
    else
        function _t1487(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        end
        _t1488 = _t1487(msg)
        fields893 = _t1488
        unwrapped_fields894 = fields893
        write(pp, "(")
        write(pp, "ffi")
        indent_sexp!(pp)
        newline(pp)
        field895 = unwrapped_fields894[1]
        pretty_name(pp, field895)
        newline(pp)
        field896 = unwrapped_fields894[2]
        pretty_ffi_args(pp, field896)
        newline(pp)
        field897 = unwrapped_fields894[3]
        pretty_terms(pp, field897)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat900 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat900)
        write(pp, flat900)
        return nothing
    else
        fields899 = msg
        write(pp, ":")
        write(pp, fields899)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat904 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat904)
        write(pp, flat904)
        return nothing
    else
        fields901 = msg
        write(pp, "(")
        write(pp, "args")
        indent_sexp!(pp)
        if !isempty(fields901)
            newline(pp)
            for (i1489, elem902) in enumerate(fields901)
                i903 = i1489 - 1
                if (i903 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem902)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat911 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat911)
        write(pp, flat911)
        return nothing
    else
        function _t1490(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1491 = _t1490(msg)
        fields905 = _t1491
        unwrapped_fields906 = fields905
        write(pp, "(")
        write(pp, "atom")
        indent_sexp!(pp)
        newline(pp)
        field907 = unwrapped_fields906[1]
        pretty_relation_id(pp, field907)
        field908 = unwrapped_fields906[2]
        if !isempty(field908)
            newline(pp)
            for (i1492, elem909) in enumerate(field908)
                i910 = i1492 - 1
                if (i910 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem909)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat918 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat918)
        write(pp, flat918)
        return nothing
    else
        function _t1493(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1494 = _t1493(msg)
        fields912 = _t1494
        unwrapped_fields913 = fields912
        write(pp, "(")
        write(pp, "pragma")
        indent_sexp!(pp)
        newline(pp)
        field914 = unwrapped_fields913[1]
        pretty_name(pp, field914)
        field915 = unwrapped_fields913[2]
        if !isempty(field915)
            newline(pp)
            for (i1495, elem916) in enumerate(field915)
                i917 = i1495 - 1
                if (i917 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem916)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat934 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat934)
        write(pp, flat934)
        return nothing
    else
        function _t1496(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1497 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1497 = nothing
            end
            return _t1497
        end
        _t1498 = _t1496(msg)
        guard_result933 = _t1498
        if !isnothing(guard_result933)
            pretty_eq(pp, msg)
        else
            function _t1499(_dollar_dollar)
                if _dollar_dollar.name == "rel_primitive_lt_monotype"
                    _t1500 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1500 = nothing
                end
                return _t1500
            end
            _t1501 = _t1499(msg)
            guard_result932 = _t1501
            if !isnothing(guard_result932)
                pretty_lt(pp, msg)
            else
                function _t1502(_dollar_dollar)
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                        _t1503 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1503 = nothing
                    end
                    return _t1503
                end
                _t1504 = _t1502(msg)
                guard_result931 = _t1504
                if !isnothing(guard_result931)
                    pretty_lt_eq(pp, msg)
                else
                    function _t1505(_dollar_dollar)
                        if _dollar_dollar.name == "rel_primitive_gt_monotype"
                            _t1506 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1506 = nothing
                        end
                        return _t1506
                    end
                    _t1507 = _t1505(msg)
                    guard_result930 = _t1507
                    if !isnothing(guard_result930)
                        pretty_gt(pp, msg)
                    else
                        function _t1508(_dollar_dollar)
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                                _t1509 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                            else
                                _t1509 = nothing
                            end
                            return _t1509
                        end
                        _t1510 = _t1508(msg)
                        guard_result929 = _t1510
                        if !isnothing(guard_result929)
                            pretty_gt_eq(pp, msg)
                        else
                            function _t1511(_dollar_dollar)
                                if _dollar_dollar.name == "rel_primitive_add_monotype"
                                    _t1512 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1512 = nothing
                                end
                                return _t1512
                            end
                            _t1513 = _t1511(msg)
                            guard_result928 = _t1513
                            if !isnothing(guard_result928)
                                pretty_add(pp, msg)
                            else
                                function _t1514(_dollar_dollar)
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                        _t1515 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1515 = nothing
                                    end
                                    return _t1515
                                end
                                _t1516 = _t1514(msg)
                                guard_result927 = _t1516
                                if !isnothing(guard_result927)
                                    pretty_minus(pp, msg)
                                else
                                    function _t1517(_dollar_dollar)
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                            _t1518 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1518 = nothing
                                        end
                                        return _t1518
                                    end
                                    _t1519 = _t1517(msg)
                                    guard_result926 = _t1519
                                    if !isnothing(guard_result926)
                                        pretty_multiply(pp, msg)
                                    else
                                        function _t1520(_dollar_dollar)
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                                _t1521 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                            else
                                                _t1521 = nothing
                                            end
                                            return _t1521
                                        end
                                        _t1522 = _t1520(msg)
                                        guard_result925 = _t1522
                                        if !isnothing(guard_result925)
                                            pretty_divide(pp, msg)
                                        else
                                            function _t1523(_dollar_dollar)
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            end
                                            _t1524 = _t1523(msg)
                                            fields919 = _t1524
                                            unwrapped_fields920 = fields919
                                            write(pp, "(")
                                            write(pp, "primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field921 = unwrapped_fields920[1]
                                            pretty_name(pp, field921)
                                            field922 = unwrapped_fields920[2]
                                            if !isempty(field922)
                                                newline(pp)
                                                for (i1525, elem923) in enumerate(field922)
                                                    i924 = i1525 - 1
                                                    if (i924 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem923)
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
    flat939 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat939)
        write(pp, flat939)
        return nothing
    else
        function _t1526(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_eq"
                _t1527 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1527 = nothing
            end
            return _t1527
        end
        _t1528 = _t1526(msg)
        fields935 = _t1528
        unwrapped_fields936 = fields935
        write(pp, "(")
        write(pp, "=")
        indent_sexp!(pp)
        newline(pp)
        field937 = unwrapped_fields936[1]
        pretty_term(pp, field937)
        newline(pp)
        field938 = unwrapped_fields936[2]
        pretty_term(pp, field938)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat944 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat944)
        write(pp, flat944)
        return nothing
    else
        function _t1529(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1530 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1530 = nothing
            end
            return _t1530
        end
        _t1531 = _t1529(msg)
        fields940 = _t1531
        unwrapped_fields941 = fields940
        write(pp, "(")
        write(pp, "<")
        indent_sexp!(pp)
        newline(pp)
        field942 = unwrapped_fields941[1]
        pretty_term(pp, field942)
        newline(pp)
        field943 = unwrapped_fields941[2]
        pretty_term(pp, field943)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat949 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat949)
        write(pp, flat949)
        return nothing
    else
        function _t1532(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                _t1533 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1533 = nothing
            end
            return _t1533
        end
        _t1534 = _t1532(msg)
        fields945 = _t1534
        unwrapped_fields946 = fields945
        write(pp, "(")
        write(pp, "<=")
        indent_sexp!(pp)
        newline(pp)
        field947 = unwrapped_fields946[1]
        pretty_term(pp, field947)
        newline(pp)
        field948 = unwrapped_fields946[2]
        pretty_term(pp, field948)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat954 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat954)
        write(pp, flat954)
        return nothing
    else
        function _t1535(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_monotype"
                _t1536 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1536 = nothing
            end
            return _t1536
        end
        _t1537 = _t1535(msg)
        fields950 = _t1537
        unwrapped_fields951 = fields950
        write(pp, "(")
        write(pp, ">")
        indent_sexp!(pp)
        newline(pp)
        field952 = unwrapped_fields951[1]
        pretty_term(pp, field952)
        newline(pp)
        field953 = unwrapped_fields951[2]
        pretty_term(pp, field953)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat959 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat959)
        write(pp, flat959)
        return nothing
    else
        function _t1538(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                _t1539 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1539 = nothing
            end
            return _t1539
        end
        _t1540 = _t1538(msg)
        fields955 = _t1540
        unwrapped_fields956 = fields955
        write(pp, "(")
        write(pp, ">=")
        indent_sexp!(pp)
        newline(pp)
        field957 = unwrapped_fields956[1]
        pretty_term(pp, field957)
        newline(pp)
        field958 = unwrapped_fields956[2]
        pretty_term(pp, field958)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat965 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat965)
        write(pp, flat965)
        return nothing
    else
        function _t1541(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_add_monotype"
                _t1542 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1542 = nothing
            end
            return _t1542
        end
        _t1543 = _t1541(msg)
        fields960 = _t1543
        unwrapped_fields961 = fields960
        write(pp, "(")
        write(pp, "+")
        indent_sexp!(pp)
        newline(pp)
        field962 = unwrapped_fields961[1]
        pretty_term(pp, field962)
        newline(pp)
        field963 = unwrapped_fields961[2]
        pretty_term(pp, field963)
        newline(pp)
        field964 = unwrapped_fields961[3]
        pretty_term(pp, field964)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat971 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat971)
        write(pp, flat971)
        return nothing
    else
        function _t1544(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                _t1545 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1545 = nothing
            end
            return _t1545
        end
        _t1546 = _t1544(msg)
        fields966 = _t1546
        unwrapped_fields967 = fields966
        write(pp, "(")
        write(pp, "-")
        indent_sexp!(pp)
        newline(pp)
        field968 = unwrapped_fields967[1]
        pretty_term(pp, field968)
        newline(pp)
        field969 = unwrapped_fields967[2]
        pretty_term(pp, field969)
        newline(pp)
        field970 = unwrapped_fields967[3]
        pretty_term(pp, field970)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat977 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat977)
        write(pp, flat977)
        return nothing
    else
        function _t1547(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                _t1548 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1548 = nothing
            end
            return _t1548
        end
        _t1549 = _t1547(msg)
        fields972 = _t1549
        unwrapped_fields973 = fields972
        write(pp, "(")
        write(pp, "*")
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

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat983 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat983)
        write(pp, flat983)
        return nothing
    else
        function _t1550(_dollar_dollar)
            if _dollar_dollar.name == "rel_primitive_divide_monotype"
                _t1551 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
            else
                _t1551 = nothing
            end
            return _t1551
        end
        _t1552 = _t1550(msg)
        fields978 = _t1552
        unwrapped_fields979 = fields978
        write(pp, "(")
        write(pp, "/")
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

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat988 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat988)
        write(pp, flat988)
        return nothing
    else
        function _t1553(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
                _t1554 = _get_oneof_field(_dollar_dollar, :specialized_value)
            else
                _t1554 = nothing
            end
            return _t1554
        end
        _t1555 = _t1553(msg)
        deconstruct_result986 = _t1555
        if !isnothing(deconstruct_result986)
            unwrapped987 = deconstruct_result986
            pretty_specialized_value(pp, unwrapped987)
        else
            function _t1556(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("term"))
                    _t1557 = _get_oneof_field(_dollar_dollar, :term)
                else
                    _t1557 = nothing
                end
                return _t1557
            end
            _t1558 = _t1556(msg)
            deconstruct_result984 = _t1558
            if !isnothing(deconstruct_result984)
                unwrapped985 = deconstruct_result984
                pretty_term(pp, unwrapped985)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat990 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat990)
        write(pp, flat990)
        return nothing
    else
        fields989 = msg
        write(pp, "#")
        pretty_value(pp, fields989)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat997 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat997)
        write(pp, flat997)
        return nothing
    else
        function _t1559(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        end
        _t1560 = _t1559(msg)
        fields991 = _t1560
        unwrapped_fields992 = fields991
        write(pp, "(")
        write(pp, "relatom")
        indent_sexp!(pp)
        newline(pp)
        field993 = unwrapped_fields992[1]
        pretty_name(pp, field993)
        field994 = unwrapped_fields992[2]
        if !isempty(field994)
            newline(pp)
            for (i1561, elem995) in enumerate(field994)
                i996 = i1561 - 1
                if (i996 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem995)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1002 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1002)
        write(pp, flat1002)
        return nothing
    else
        function _t1562(_dollar_dollar)
            return (_dollar_dollar.input, _dollar_dollar.result,)
        end
        _t1563 = _t1562(msg)
        fields998 = _t1563
        unwrapped_fields999 = fields998
        write(pp, "(")
        write(pp, "cast")
        indent_sexp!(pp)
        newline(pp)
        field1000 = unwrapped_fields999[1]
        pretty_term(pp, field1000)
        newline(pp)
        field1001 = unwrapped_fields999[2]
        pretty_term(pp, field1001)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1006 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1006)
        write(pp, flat1006)
        return nothing
    else
        fields1003 = msg
        write(pp, "(")
        write(pp, "attrs")
        indent_sexp!(pp)
        if !isempty(fields1003)
            newline(pp)
            for (i1564, elem1004) in enumerate(fields1003)
                i1005 = i1564 - 1
                if (i1005 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1004)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1013 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1013)
        write(pp, flat1013)
        return nothing
    else
        function _t1565(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.args,)
        end
        _t1566 = _t1565(msg)
        fields1007 = _t1566
        unwrapped_fields1008 = fields1007
        write(pp, "(")
        write(pp, "attribute")
        indent_sexp!(pp)
        newline(pp)
        field1009 = unwrapped_fields1008[1]
        pretty_name(pp, field1009)
        field1010 = unwrapped_fields1008[2]
        if !isempty(field1010)
            newline(pp)
            for (i1567, elem1011) in enumerate(field1010)
                i1012 = i1567 - 1
                if (i1012 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem1011)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1020 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1020)
        write(pp, flat1020)
        return nothing
    else
        function _t1568(_dollar_dollar)
            return (_dollar_dollar.var"#global", _dollar_dollar.body,)
        end
        _t1569 = _t1568(msg)
        fields1014 = _t1569
        unwrapped_fields1015 = fields1014
        write(pp, "(")
        write(pp, "algorithm")
        indent_sexp!(pp)
        field1016 = unwrapped_fields1015[1]
        if !isempty(field1016)
            newline(pp)
            for (i1570, elem1017) in enumerate(field1016)
                i1018 = i1570 - 1
                if (i1018 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1017)
            end
        end
        newline(pp)
        field1019 = unwrapped_fields1015[2]
        pretty_script(pp, field1019)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1025 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1025)
        write(pp, flat1025)
        return nothing
    else
        function _t1571(_dollar_dollar)
            return _dollar_dollar.constructs
        end
        _t1572 = _t1571(msg)
        fields1021 = _t1572
        unwrapped_fields1022 = fields1021
        write(pp, "(")
        write(pp, "script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1022)
            newline(pp)
            for (i1573, elem1023) in enumerate(unwrapped_fields1022)
                i1024 = i1573 - 1
                if (i1024 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1023)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1030 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1030)
        write(pp, flat1030)
        return nothing
    else
        function _t1574(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("loop"))
                _t1575 = _get_oneof_field(_dollar_dollar, :loop)
            else
                _t1575 = nothing
            end
            return _t1575
        end
        _t1576 = _t1574(msg)
        deconstruct_result1028 = _t1576
        if !isnothing(deconstruct_result1028)
            unwrapped1029 = deconstruct_result1028
            pretty_loop(pp, unwrapped1029)
        else
            function _t1577(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                    _t1578 = _get_oneof_field(_dollar_dollar, :instruction)
                else
                    _t1578 = nothing
                end
                return _t1578
            end
            _t1579 = _t1577(msg)
            deconstruct_result1026 = _t1579
            if !isnothing(deconstruct_result1026)
                unwrapped1027 = deconstruct_result1026
                pretty_instruction(pp, unwrapped1027)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1035 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1035)
        write(pp, flat1035)
        return nothing
    else
        function _t1580(_dollar_dollar)
            return (_dollar_dollar.init, _dollar_dollar.body,)
        end
        _t1581 = _t1580(msg)
        fields1031 = _t1581
        unwrapped_fields1032 = fields1031
        write(pp, "(")
        write(pp, "loop")
        indent_sexp!(pp)
        newline(pp)
        field1033 = unwrapped_fields1032[1]
        pretty_init(pp, field1033)
        newline(pp)
        field1034 = unwrapped_fields1032[2]
        pretty_script(pp, field1034)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1039 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1039)
        write(pp, flat1039)
        return nothing
    else
        fields1036 = msg
        write(pp, "(")
        write(pp, "init")
        indent_sexp!(pp)
        if !isempty(fields1036)
            newline(pp)
            for (i1582, elem1037) in enumerate(fields1036)
                i1038 = i1582 - 1
                if (i1038 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1037)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1050 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1050)
        write(pp, flat1050)
        return nothing
    else
        function _t1583(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("assign"))
                _t1584 = _get_oneof_field(_dollar_dollar, :assign)
            else
                _t1584 = nothing
            end
            return _t1584
        end
        _t1585 = _t1583(msg)
        deconstruct_result1048 = _t1585
        if !isnothing(deconstruct_result1048)
            unwrapped1049 = deconstruct_result1048
            pretty_assign(pp, unwrapped1049)
        else
            function _t1586(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                    _t1587 = _get_oneof_field(_dollar_dollar, :upsert)
                else
                    _t1587 = nothing
                end
                return _t1587
            end
            _t1588 = _t1586(msg)
            deconstruct_result1046 = _t1588
            if !isnothing(deconstruct_result1046)
                unwrapped1047 = deconstruct_result1046
                pretty_upsert(pp, unwrapped1047)
            else
                function _t1589(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("#break"))
                        _t1590 = _get_oneof_field(_dollar_dollar, :var"#break")
                    else
                        _t1590 = nothing
                    end
                    return _t1590
                end
                _t1591 = _t1589(msg)
                deconstruct_result1044 = _t1591
                if !isnothing(deconstruct_result1044)
                    unwrapped1045 = deconstruct_result1044
                    pretty_break(pp, unwrapped1045)
                else
                    function _t1592(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                            _t1593 = _get_oneof_field(_dollar_dollar, :monoid_def)
                        else
                            _t1593 = nothing
                        end
                        return _t1593
                    end
                    _t1594 = _t1592(msg)
                    deconstruct_result1042 = _t1594
                    if !isnothing(deconstruct_result1042)
                        unwrapped1043 = deconstruct_result1042
                        pretty_monoid_def(pp, unwrapped1043)
                    else
                        function _t1595(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                                _t1596 = _get_oneof_field(_dollar_dollar, :monus_def)
                            else
                                _t1596 = nothing
                            end
                            return _t1596
                        end
                        _t1597 = _t1595(msg)
                        deconstruct_result1040 = _t1597
                        if !isnothing(deconstruct_result1040)
                            unwrapped1041 = deconstruct_result1040
                            pretty_monus_def(pp, unwrapped1041)
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
    flat1057 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1057)
        write(pp, flat1057)
        return nothing
    else
        function _t1598(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1599 = _dollar_dollar.attrs
            else
                _t1599 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1599,)
        end
        _t1600 = _t1598(msg)
        fields1051 = _t1600
        unwrapped_fields1052 = fields1051
        write(pp, "(")
        write(pp, "assign")
        indent_sexp!(pp)
        newline(pp)
        field1053 = unwrapped_fields1052[1]
        pretty_relation_id(pp, field1053)
        newline(pp)
        field1054 = unwrapped_fields1052[2]
        pretty_abstraction(pp, field1054)
        field1055 = unwrapped_fields1052[3]
        if !isnothing(field1055)
            newline(pp)
            opt_val1056 = field1055
            pretty_attrs(pp, opt_val1056)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1064 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1064)
        write(pp, flat1064)
        return nothing
    else
        function _t1601(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1602 = _dollar_dollar.attrs
            else
                _t1602 = nothing
            end
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1602,)
        end
        _t1603 = _t1601(msg)
        fields1058 = _t1603
        unwrapped_fields1059 = fields1058
        write(pp, "(")
        write(pp, "upsert")
        indent_sexp!(pp)
        newline(pp)
        field1060 = unwrapped_fields1059[1]
        pretty_relation_id(pp, field1060)
        newline(pp)
        field1061 = unwrapped_fields1059[2]
        pretty_abstraction_with_arity(pp, field1061)
        field1062 = unwrapped_fields1059[3]
        if !isnothing(field1062)
            newline(pp)
            opt_val1063 = field1062
            pretty_attrs(pp, opt_val1063)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1069 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1069)
        write(pp, flat1069)
        return nothing
    else
        function _t1604(_dollar_dollar)
            _t1605 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
            return (_t1605, _dollar_dollar[1].value,)
        end
        _t1606 = _t1604(msg)
        fields1065 = _t1606
        unwrapped_fields1066 = fields1065
        write(pp, "(")
        indent!(pp)
        field1067 = unwrapped_fields1066[1]
        pretty_bindings(pp, field1067)
        newline(pp)
        field1068 = unwrapped_fields1066[2]
        pretty_formula(pp, field1068)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1076 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1076)
        write(pp, flat1076)
        return nothing
    else
        function _t1607(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1608 = _dollar_dollar.attrs
            else
                _t1608 = nothing
            end
            return (_dollar_dollar.name, _dollar_dollar.body, _t1608,)
        end
        _t1609 = _t1607(msg)
        fields1070 = _t1609
        unwrapped_fields1071 = fields1070
        write(pp, "(")
        write(pp, "break")
        indent_sexp!(pp)
        newline(pp)
        field1072 = unwrapped_fields1071[1]
        pretty_relation_id(pp, field1072)
        newline(pp)
        field1073 = unwrapped_fields1071[2]
        pretty_abstraction(pp, field1073)
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

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1084 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1084)
        write(pp, flat1084)
        return nothing
    else
        function _t1610(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1611 = _dollar_dollar.attrs
            else
                _t1611 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1611,)
        end
        _t1612 = _t1610(msg)
        fields1077 = _t1612
        unwrapped_fields1078 = fields1077
        write(pp, "(")
        write(pp, "monoid")
        indent_sexp!(pp)
        newline(pp)
        field1079 = unwrapped_fields1078[1]
        pretty_monoid(pp, field1079)
        newline(pp)
        field1080 = unwrapped_fields1078[2]
        pretty_relation_id(pp, field1080)
        newline(pp)
        field1081 = unwrapped_fields1078[3]
        pretty_abstraction_with_arity(pp, field1081)
        field1082 = unwrapped_fields1078[4]
        if !isnothing(field1082)
            newline(pp)
            opt_val1083 = field1082
            pretty_attrs(pp, opt_val1083)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1093 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1093)
        write(pp, flat1093)
        return nothing
    else
        function _t1613(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
                _t1614 = _get_oneof_field(_dollar_dollar, :or_monoid)
            else
                _t1614 = nothing
            end
            return _t1614
        end
        _t1615 = _t1613(msg)
        deconstruct_result1091 = _t1615
        if !isnothing(deconstruct_result1091)
            unwrapped1092 = deconstruct_result1091
            pretty_or_monoid(pp, unwrapped1092)
        else
            function _t1616(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                    _t1617 = _get_oneof_field(_dollar_dollar, :min_monoid)
                else
                    _t1617 = nothing
                end
                return _t1617
            end
            _t1618 = _t1616(msg)
            deconstruct_result1089 = _t1618
            if !isnothing(deconstruct_result1089)
                unwrapped1090 = deconstruct_result1089
                pretty_min_monoid(pp, unwrapped1090)
            else
                function _t1619(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                        _t1620 = _get_oneof_field(_dollar_dollar, :max_monoid)
                    else
                        _t1620 = nothing
                    end
                    return _t1620
                end
                _t1621 = _t1619(msg)
                deconstruct_result1087 = _t1621
                if !isnothing(deconstruct_result1087)
                    unwrapped1088 = deconstruct_result1087
                    pretty_max_monoid(pp, unwrapped1088)
                else
                    function _t1622(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                            _t1623 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                        else
                            _t1623 = nothing
                        end
                        return _t1623
                    end
                    _t1624 = _t1622(msg)
                    deconstruct_result1085 = _t1624
                    if !isnothing(deconstruct_result1085)
                        unwrapped1086 = deconstruct_result1085
                        pretty_sum_monoid(pp, unwrapped1086)
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
    fields1094 = msg
    write(pp, "(")
    write(pp, "or")
    write(pp, ")")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1097 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1097)
        write(pp, flat1097)
        return nothing
    else
        function _t1625(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1626 = _t1625(msg)
        fields1095 = _t1626
        unwrapped_fields1096 = fields1095
        write(pp, "(")
        write(pp, "min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1096)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1100 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1100)
        write(pp, flat1100)
        return nothing
    else
        function _t1627(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1628 = _t1627(msg)
        fields1098 = _t1628
        unwrapped_fields1099 = fields1098
        write(pp, "(")
        write(pp, "max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1099)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1103 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1103)
        write(pp, flat1103)
        return nothing
    else
        function _t1629(_dollar_dollar)
            return _dollar_dollar.var"#type"
        end
        _t1630 = _t1629(msg)
        fields1101 = _t1630
        unwrapped_fields1102 = fields1101
        write(pp, "(")
        write(pp, "sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1102)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1111 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1111)
        write(pp, flat1111)
        return nothing
    else
        function _t1631(_dollar_dollar)
            if !isempty(_dollar_dollar.attrs)
                _t1632 = _dollar_dollar.attrs
            else
                _t1632 = nothing
            end
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1632,)
        end
        _t1633 = _t1631(msg)
        fields1104 = _t1633
        unwrapped_fields1105 = fields1104
        write(pp, "(")
        write(pp, "monus")
        indent_sexp!(pp)
        newline(pp)
        field1106 = unwrapped_fields1105[1]
        pretty_monoid(pp, field1106)
        newline(pp)
        field1107 = unwrapped_fields1105[2]
        pretty_relation_id(pp, field1107)
        newline(pp)
        field1108 = unwrapped_fields1105[3]
        pretty_abstraction_with_arity(pp, field1108)
        field1109 = unwrapped_fields1105[4]
        if !isnothing(field1109)
            newline(pp)
            opt_val1110 = field1109
            pretty_attrs(pp, opt_val1110)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1118 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1118)
        write(pp, flat1118)
        return nothing
    else
        function _t1634(_dollar_dollar)
            return (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        end
        _t1635 = _t1634(msg)
        fields1112 = _t1635
        unwrapped_fields1113 = fields1112
        write(pp, "(")
        write(pp, "functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1114 = unwrapped_fields1113[1]
        pretty_relation_id(pp, field1114)
        newline(pp)
        field1115 = unwrapped_fields1113[2]
        pretty_abstraction(pp, field1115)
        newline(pp)
        field1116 = unwrapped_fields1113[3]
        pretty_functional_dependency_keys(pp, field1116)
        newline(pp)
        field1117 = unwrapped_fields1113[4]
        pretty_functional_dependency_values(pp, field1117)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1122 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1122)
        write(pp, flat1122)
        return nothing
    else
        fields1119 = msg
        write(pp, "(")
        write(pp, "keys")
        indent_sexp!(pp)
        if !isempty(fields1119)
            newline(pp)
            for (i1636, elem1120) in enumerate(fields1119)
                i1121 = i1636 - 1
                if (i1121 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1120)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1126 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1126)
        write(pp, flat1126)
        return nothing
    else
        fields1123 = msg
        write(pp, "(")
        write(pp, "values")
        indent_sexp!(pp)
        if !isempty(fields1123)
            newline(pp)
            for (i1637, elem1124) in enumerate(fields1123)
                i1125 = i1637 - 1
                if (i1125 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1124)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1133 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1133)
        write(pp, flat1133)
        return nothing
    else
        function _t1638(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("edb"))
                _t1639 = _get_oneof_field(_dollar_dollar, :edb)
            else
                _t1639 = nothing
            end
            return _t1639
        end
        _t1640 = _t1638(msg)
        deconstruct_result1131 = _t1640
        if !isnothing(deconstruct_result1131)
            unwrapped1132 = deconstruct_result1131
            pretty_edb(pp, unwrapped1132)
        else
            function _t1641(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                    _t1642 = _get_oneof_field(_dollar_dollar, :betree_relation)
                else
                    _t1642 = nothing
                end
                return _t1642
            end
            _t1643 = _t1641(msg)
            deconstruct_result1129 = _t1643
            if !isnothing(deconstruct_result1129)
                unwrapped1130 = deconstruct_result1129
                pretty_betree_relation(pp, unwrapped1130)
            else
                function _t1644(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                        _t1645 = _get_oneof_field(_dollar_dollar, :csv_data)
                    else
                        _t1645 = nothing
                    end
                    return _t1645
                end
                _t1646 = _t1644(msg)
                deconstruct_result1127 = _t1646
                if !isnothing(deconstruct_result1127)
                    unwrapped1128 = deconstruct_result1127
                    pretty_csv_data(pp, unwrapped1128)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_edb(pp::PrettyPrinter, msg::Proto.EDB)
    flat1139 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1139)
        write(pp, flat1139)
        return nothing
    else
        function _t1647(_dollar_dollar)
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        end
        _t1648 = _t1647(msg)
        fields1134 = _t1648
        unwrapped_fields1135 = fields1134
        write(pp, "(")
        write(pp, "edb")
        indent_sexp!(pp)
        newline(pp)
        field1136 = unwrapped_fields1135[1]
        pretty_relation_id(pp, field1136)
        newline(pp)
        field1137 = unwrapped_fields1135[2]
        pretty_edb_path(pp, field1137)
        newline(pp)
        field1138 = unwrapped_fields1135[3]
        pretty_edb_types(pp, field1138)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1143 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1143)
        write(pp, flat1143)
        return nothing
    else
        fields1140 = msg
        write(pp, "[")
        indent!(pp)
        for (i1649, elem1141) in enumerate(fields1140)
            i1142 = i1649 - 1
            if (i1142 > 0)
                newline(pp)
            end
            write(pp, format_string(pp, elem1141))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1147 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1147)
        write(pp, flat1147)
        return nothing
    else
        fields1144 = msg
        write(pp, "[")
        indent!(pp)
        for (i1650, elem1145) in enumerate(fields1144)
            i1146 = i1650 - 1
            if (i1146 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1145)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1152 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1152)
        write(pp, flat1152)
        return nothing
    else
        function _t1651(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        end
        _t1652 = _t1651(msg)
        fields1148 = _t1652
        unwrapped_fields1149 = fields1148
        write(pp, "(")
        write(pp, "betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1150 = unwrapped_fields1149[1]
        pretty_relation_id(pp, field1150)
        newline(pp)
        field1151 = unwrapped_fields1149[2]
        pretty_betree_info(pp, field1151)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1158 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1158)
        write(pp, flat1158)
        return nothing
    else
        function _t1653(_dollar_dollar)
            _t1654 = deconstruct_betree_info_config(pp, _dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1654,)
        end
        _t1655 = _t1653(msg)
        fields1153 = _t1655
        unwrapped_fields1154 = fields1153
        write(pp, "(")
        write(pp, "betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1155 = unwrapped_fields1154[1]
        pretty_betree_info_key_types(pp, field1155)
        newline(pp)
        field1156 = unwrapped_fields1154[2]
        pretty_betree_info_value_types(pp, field1156)
        newline(pp)
        field1157 = unwrapped_fields1154[3]
        pretty_config_dict(pp, field1157)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1162 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1162)
        write(pp, flat1162)
        return nothing
    else
        fields1159 = msg
        write(pp, "(")
        write(pp, "key_types")
        indent_sexp!(pp)
        if !isempty(fields1159)
            newline(pp)
            for (i1656, elem1160) in enumerate(fields1159)
                i1161 = i1656 - 1
                if (i1161 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1160)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1166 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1166)
        write(pp, flat1166)
        return nothing
    else
        fields1163 = msg
        write(pp, "(")
        write(pp, "value_types")
        indent_sexp!(pp)
        if !isempty(fields1163)
            newline(pp)
            for (i1657, elem1164) in enumerate(fields1163)
                i1165 = i1657 - 1
                if (i1165 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1164)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1173 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1173)
        write(pp, flat1173)
        return nothing
    else
        function _t1658(_dollar_dollar)
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        end
        _t1659 = _t1658(msg)
        fields1167 = _t1659
        unwrapped_fields1168 = fields1167
        write(pp, "(")
        write(pp, "csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1169 = unwrapped_fields1168[1]
        pretty_csvlocator(pp, field1169)
        newline(pp)
        field1170 = unwrapped_fields1168[2]
        pretty_csv_config(pp, field1170)
        newline(pp)
        field1171 = unwrapped_fields1168[3]
        pretty_gnf_columns(pp, field1171)
        newline(pp)
        field1172 = unwrapped_fields1168[4]
        pretty_csv_asof(pp, field1172)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1180 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1180)
        write(pp, flat1180)
        return nothing
    else
        function _t1660(_dollar_dollar)
            if !isempty(_dollar_dollar.paths)
                _t1661 = _dollar_dollar.paths
            else
                _t1661 = nothing
            end
            if String(copy(_dollar_dollar.inline_data)) != ""
                _t1662 = String(copy(_dollar_dollar.inline_data))
            else
                _t1662 = nothing
            end
            return (_t1661, _t1662,)
        end
        _t1663 = _t1660(msg)
        fields1174 = _t1663
        unwrapped_fields1175 = fields1174
        write(pp, "(")
        write(pp, "csv_locator")
        indent_sexp!(pp)
        field1176 = unwrapped_fields1175[1]
        if !isnothing(field1176)
            newline(pp)
            opt_val1177 = field1176
            pretty_csv_locator_paths(pp, opt_val1177)
        end
        field1178 = unwrapped_fields1175[2]
        if !isnothing(field1178)
            newline(pp)
            opt_val1179 = field1178
            pretty_csv_locator_inline_data(pp, opt_val1179)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1184 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1184)
        write(pp, flat1184)
        return nothing
    else
        fields1181 = msg
        write(pp, "(")
        write(pp, "paths")
        indent_sexp!(pp)
        if !isempty(fields1181)
            newline(pp)
            for (i1664, elem1182) in enumerate(fields1181)
                i1183 = i1664 - 1
                if (i1183 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1182))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1186 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1186)
        write(pp, flat1186)
        return nothing
    else
        fields1185 = msg
        write(pp, "(")
        write(pp, "inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1185))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1189 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1189)
        write(pp, flat1189)
        return nothing
    else
        function _t1665(_dollar_dollar)
            _t1666 = deconstruct_csv_config(pp, _dollar_dollar)
            return _t1666
        end
        _t1667 = _t1665(msg)
        fields1187 = _t1667
        unwrapped_fields1188 = fields1187
        write(pp, "(")
        write(pp, "csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1188)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1193 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1193)
        write(pp, flat1193)
        return nothing
    else
        fields1190 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1190)
            newline(pp)
            for (i1668, elem1191) in enumerate(fields1190)
                i1192 = i1668 - 1
                if (i1192 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1191)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1202 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1202)
        write(pp, flat1202)
        return nothing
    else
        function _t1669(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("target_id"))
                _t1670 = _dollar_dollar.target_id
            else
                _t1670 = nothing
            end
            return (_dollar_dollar.column_path, _t1670, _dollar_dollar.types,)
        end
        _t1671 = _t1669(msg)
        fields1194 = _t1671
        unwrapped_fields1195 = fields1194
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1196 = unwrapped_fields1195[1]
        pretty_gnf_column_path(pp, field1196)
        field1197 = unwrapped_fields1195[2]
        if !isnothing(field1197)
            newline(pp)
            opt_val1198 = field1197
            pretty_relation_id(pp, opt_val1198)
        end
        newline(pp)
        write(pp, "[")
        field1199 = unwrapped_fields1195[3]
        for (i1672, elem1200) in enumerate(field1199)
            i1201 = i1672 - 1
            if (i1201 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1200)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1209 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1209)
        write(pp, flat1209)
        return nothing
    else
        function _t1673(_dollar_dollar)
            if length(_dollar_dollar) == 1
                _t1674 = _dollar_dollar[1]
            else
                _t1674 = nothing
            end
            return _t1674
        end
        _t1675 = _t1673(msg)
        deconstruct_result1207 = _t1675
        if !isnothing(deconstruct_result1207)
            unwrapped1208 = deconstruct_result1207
            write(pp, format_string(pp, unwrapped1208))
        else
            function _t1676(_dollar_dollar)
                if length(_dollar_dollar) != 1
                    _t1677 = _dollar_dollar
                else
                    _t1677 = nothing
                end
                return _t1677
            end
            _t1678 = _t1676(msg)
            deconstruct_result1203 = _t1678
            if !isnothing(deconstruct_result1203)
                unwrapped1204 = deconstruct_result1203
                write(pp, "[")
                indent!(pp)
                for (i1679, elem1205) in enumerate(unwrapped1204)
                    i1206 = i1679 - 1
                    if (i1206 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(pp, elem1205))
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
    flat1211 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1211)
        write(pp, flat1211)
        return nothing
    else
        fields1210 = msg
        write(pp, "(")
        write(pp, "asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1210))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1214 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1214)
        write(pp, flat1214)
        return nothing
    else
        function _t1680(_dollar_dollar)
            return _dollar_dollar.fragment_id
        end
        _t1681 = _t1680(msg)
        fields1212 = _t1681
        unwrapped_fields1213 = fields1212
        write(pp, "(")
        write(pp, "undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1213)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1219 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1219)
        write(pp, flat1219)
        return nothing
    else
        function _t1682(_dollar_dollar)
            return _dollar_dollar.relations
        end
        _t1683 = _t1682(msg)
        fields1215 = _t1683
        unwrapped_fields1216 = fields1215
        write(pp, "(")
        write(pp, "context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1216)
            newline(pp)
            for (i1684, elem1217) in enumerate(unwrapped_fields1216)
                i1218 = i1684 - 1
                if (i1218 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1217)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1224 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1224)
        write(pp, flat1224)
        return nothing
    else
        function _t1685(_dollar_dollar)
            return _dollar_dollar.mappings
        end
        _t1686 = _t1685(msg)
        fields1220 = _t1686
        unwrapped_fields1221 = fields1220
        write(pp, "(")
        write(pp, "snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1221)
            newline(pp)
            for (i1687, elem1222) in enumerate(unwrapped_fields1221)
                i1223 = i1687 - 1
                if (i1223 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1222)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1229 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1229)
        write(pp, flat1229)
        return nothing
    else
        function _t1688(_dollar_dollar)
            return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        end
        _t1689 = _t1688(msg)
        fields1225 = _t1689
        unwrapped_fields1226 = fields1225
        field1227 = unwrapped_fields1226[1]
        pretty_edb_path(pp, field1227)
        write(pp, " ")
        field1228 = unwrapped_fields1226[2]
        pretty_relation_id(pp, field1228)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1233 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1233)
        write(pp, flat1233)
        return nothing
    else
        fields1230 = msg
        write(pp, "(")
        write(pp, "reads")
        indent_sexp!(pp)
        if !isempty(fields1230)
            newline(pp)
            for (i1690, elem1231) in enumerate(fields1230)
                i1232 = i1690 - 1
                if (i1232 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1231)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1244 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1244)
        write(pp, flat1244)
        return nothing
    else
        function _t1691(_dollar_dollar)
            if _has_proto_field(_dollar_dollar, Symbol("demand"))
                _t1692 = _get_oneof_field(_dollar_dollar, :demand)
            else
                _t1692 = nothing
            end
            return _t1692
        end
        _t1693 = _t1691(msg)
        deconstruct_result1242 = _t1693
        if !isnothing(deconstruct_result1242)
            unwrapped1243 = deconstruct_result1242
            pretty_demand(pp, unwrapped1243)
        else
            function _t1694(_dollar_dollar)
                if _has_proto_field(_dollar_dollar, Symbol("output"))
                    _t1695 = _get_oneof_field(_dollar_dollar, :output)
                else
                    _t1695 = nothing
                end
                return _t1695
            end
            _t1696 = _t1694(msg)
            deconstruct_result1240 = _t1696
            if !isnothing(deconstruct_result1240)
                unwrapped1241 = deconstruct_result1240
                pretty_output(pp, unwrapped1241)
            else
                function _t1697(_dollar_dollar)
                    if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                        _t1698 = _get_oneof_field(_dollar_dollar, :what_if)
                    else
                        _t1698 = nothing
                    end
                    return _t1698
                end
                _t1699 = _t1697(msg)
                deconstruct_result1238 = _t1699
                if !isnothing(deconstruct_result1238)
                    unwrapped1239 = deconstruct_result1238
                    pretty_what_if(pp, unwrapped1239)
                else
                    function _t1700(_dollar_dollar)
                        if _has_proto_field(_dollar_dollar, Symbol("abort"))
                            _t1701 = _get_oneof_field(_dollar_dollar, :abort)
                        else
                            _t1701 = nothing
                        end
                        return _t1701
                    end
                    _t1702 = _t1700(msg)
                    deconstruct_result1236 = _t1702
                    if !isnothing(deconstruct_result1236)
                        unwrapped1237 = deconstruct_result1236
                        pretty_abort(pp, unwrapped1237)
                    else
                        function _t1703(_dollar_dollar)
                            if _has_proto_field(_dollar_dollar, Symbol("#export"))
                                _t1704 = _get_oneof_field(_dollar_dollar, :var"#export")
                            else
                                _t1704 = nothing
                            end
                            return _t1704
                        end
                        _t1705 = _t1703(msg)
                        deconstruct_result1234 = _t1705
                        if !isnothing(deconstruct_result1234)
                            unwrapped1235 = deconstruct_result1234
                            pretty_export(pp, unwrapped1235)
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
    flat1247 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1247)
        write(pp, flat1247)
        return nothing
    else
        function _t1706(_dollar_dollar)
            return _dollar_dollar.relation_id
        end
        _t1707 = _t1706(msg)
        fields1245 = _t1707
        unwrapped_fields1246 = fields1245
        write(pp, "(")
        write(pp, "demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1246)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1252 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1252)
        write(pp, flat1252)
        return nothing
    else
        function _t1708(_dollar_dollar)
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        end
        _t1709 = _t1708(msg)
        fields1248 = _t1709
        unwrapped_fields1249 = fields1248
        write(pp, "(")
        write(pp, "output")
        indent_sexp!(pp)
        newline(pp)
        field1250 = unwrapped_fields1249[1]
        pretty_name(pp, field1250)
        newline(pp)
        field1251 = unwrapped_fields1249[2]
        pretty_relation_id(pp, field1251)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1257 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1257)
        write(pp, flat1257)
        return nothing
    else
        function _t1710(_dollar_dollar)
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        end
        _t1711 = _t1710(msg)
        fields1253 = _t1711
        unwrapped_fields1254 = fields1253
        write(pp, "(")
        write(pp, "what_if")
        indent_sexp!(pp)
        newline(pp)
        field1255 = unwrapped_fields1254[1]
        pretty_name(pp, field1255)
        newline(pp)
        field1256 = unwrapped_fields1254[2]
        pretty_epoch(pp, field1256)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1263 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1263)
        write(pp, flat1263)
        return nothing
    else
        function _t1712(_dollar_dollar)
            if _dollar_dollar.name != "abort"
                _t1713 = _dollar_dollar.name
            else
                _t1713 = nothing
            end
            return (_t1713, _dollar_dollar.relation_id,)
        end
        _t1714 = _t1712(msg)
        fields1258 = _t1714
        unwrapped_fields1259 = fields1258
        write(pp, "(")
        write(pp, "abort")
        indent_sexp!(pp)
        field1260 = unwrapped_fields1259[1]
        if !isnothing(field1260)
            newline(pp)
            opt_val1261 = field1260
            pretty_name(pp, opt_val1261)
        end
        newline(pp)
        field1262 = unwrapped_fields1259[2]
        pretty_relation_id(pp, field1262)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1266 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1266)
        write(pp, flat1266)
        return nothing
    else
        function _t1715(_dollar_dollar)
            return _get_oneof_field(_dollar_dollar, :csv_config)
        end
        _t1716 = _t1715(msg)
        fields1264 = _t1716
        unwrapped_fields1265 = fields1264
        write(pp, "(")
        write(pp, "export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1265)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1272 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1272)
        write(pp, flat1272)
        return nothing
    else
        function _t1717(_dollar_dollar)
            _t1718 = deconstruct_export_csv_config(pp, _dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1718,)
        end
        _t1719 = _t1717(msg)
        fields1267 = _t1719
        unwrapped_fields1268 = fields1267
        write(pp, "(")
        write(pp, "export_csv_config")
        indent_sexp!(pp)
        newline(pp)
        field1269 = unwrapped_fields1268[1]
        pretty_export_csv_path(pp, field1269)
        newline(pp)
        field1270 = unwrapped_fields1268[2]
        pretty_export_csv_columns(pp, field1270)
        newline(pp)
        field1271 = unwrapped_fields1268[3]
        pretty_config_dict(pp, field1271)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_path(pp::PrettyPrinter, msg::String)
    flat1274 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1274)
        write(pp, flat1274)
        return nothing
    else
        fields1273 = msg
        write(pp, "(")
        write(pp, "path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1273))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1278 = try_flat(pp, msg, pretty_export_csv_columns)
    if !isnothing(flat1278)
        write(pp, flat1278)
        return nothing
    else
        fields1275 = msg
        write(pp, "(")
        write(pp, "columns")
        indent_sexp!(pp)
        if !isempty(fields1275)
            newline(pp)
            for (i1720, elem1276) in enumerate(fields1275)
                i1277 = i1720 - 1
                if (i1277 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1276)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_column(pp::PrettyPrinter, msg::Proto.ExportCSVColumn)
    flat1283 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1283)
        write(pp, flat1283)
        return nothing
    else
        function _t1721(_dollar_dollar)
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        end
        _t1722 = _t1721(msg)
        fields1279 = _t1722
        unwrapped_fields1280 = fields1279
        write(pp, "(")
        write(pp, "column")
        indent_sexp!(pp)
        newline(pp)
        field1281 = unwrapped_fields1280[1]
        write(pp, format_string(pp, field1281))
        newline(pp)
        field1282 = unwrapped_fields1280[2]
        pretty_relation_id(pp, field1282)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end


# --- Auto-generated printers for uncovered proto types ---

function pretty_debug_info(pp::PrettyPrinter, msg::Proto.DebugInfo)
    write(pp, "(debug_info")
    indent_sexp!(pp)
    for (i1760, _rid) in enumerate(msg.ids)
        _idx = i1760 - 1
        newline(pp)
        write(pp, "(")
        _t1761 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1761)
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
    for (i1762, _elem) in enumerate(msg.keys)
        _idx = i1762 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values ")
    write(pp, "(")
    for (i1763, _elem) in enumerate(msg.values)
        _idx = i1763 - 1
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
