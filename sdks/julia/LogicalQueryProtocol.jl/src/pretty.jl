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
    _t1482 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1482
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1483 = Proto.Value(value=OneOf(:int_value, v))
    return _t1483
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1484 = Proto.Value(value=OneOf(:float_value, v))
    return _t1484
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1485 = Proto.Value(value=OneOf(:string_value, v))
    return _t1485
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1486 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1486
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1487 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1487
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1488 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1488,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1489 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1489,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1490 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1490,))
            end
        end
    end
    _t1491 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1491,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1492 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1492,))
    _t1493 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1493,))
    if msg.new_line != ""
        _t1494 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1494,))
    end
    _t1495 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1495,))
    _t1496 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1496,))
    _t1497 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1497,))
    if msg.comment != ""
        _t1498 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1498,))
    end
    for missing_string in msg.missing_strings
        _t1499 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1499,))
    end
    _t1500 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1500,))
    _t1501 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1501,))
    _t1502 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1502,))
    if msg.partition_size_mb != 0
        _t1503 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1503,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1504 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1504,))
    _t1505 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1505,))
    _t1506 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1506,))
    _t1507 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1507,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1508 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1508,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1509 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1509,))
        end
    end
    _t1510 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1510,))
    _t1511 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1511,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1512 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1512,))
    end
    if !isnothing(msg.compression)
        _t1513 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1513,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1514 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1514,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1515 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1515,))
    end
    if !isnothing(msg.syntax_delim)
        _t1516 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1516,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1517 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1517,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1518 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1518,))
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
        _t1519 = nothing
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
    flat673 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat673)
        write(pp, flat673)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1328 = _dollar_dollar.configure
        else
            _t1328 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1329 = _dollar_dollar.sync
        else
            _t1329 = nothing
        end
        fields664 = (_t1328, _t1329, _dollar_dollar.epochs,)
        unwrapped_fields665 = fields664
        write(pp, "(transaction")
        indent_sexp!(pp)
        field666 = unwrapped_fields665[1]
        if !isnothing(field666)
            newline(pp)
            opt_val667 = field666
            pretty_configure(pp, opt_val667)
        end
        field668 = unwrapped_fields665[2]
        if !isnothing(field668)
            newline(pp)
            opt_val669 = field668
            pretty_sync(pp, opt_val669)
        end
        field670 = unwrapped_fields665[3]
        if !isempty(field670)
            newline(pp)
            for (i1330, elem671) in enumerate(field670)
                i672 = i1330 - 1
                if (i672 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem671)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat676 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat676)
        write(pp, flat676)
        return nothing
    else
        _dollar_dollar = msg
        _t1331 = deconstruct_configure(pp, _dollar_dollar)
        fields674 = _t1331
        unwrapped_fields675 = fields674
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields675)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat680 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat680)
        write(pp, flat680)
        return nothing
    else
        fields677 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields677)
            newline(pp)
            for (i1332, elem678) in enumerate(fields677)
                i679 = i1332 - 1
                if (i679 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem678)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat685 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat685)
        write(pp, flat685)
        return nothing
    else
        _dollar_dollar = msg
        fields681 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields682 = fields681
        write(pp, ":")
        field683 = unwrapped_fields682[1]
        write(pp, field683)
        write(pp, " ")
        field684 = unwrapped_fields682[2]
        pretty_value(pp, field684)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat709 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat709)
        write(pp, flat709)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1333 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1333 = nothing
        end
        deconstruct_result707 = _t1333
        if !isnothing(deconstruct_result707)
            unwrapped708 = deconstruct_result707
            pretty_date(pp, unwrapped708)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1334 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1334 = nothing
            end
            deconstruct_result705 = _t1334
            if !isnothing(deconstruct_result705)
                unwrapped706 = deconstruct_result705
                pretty_datetime(pp, unwrapped706)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1335 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1335 = nothing
                end
                deconstruct_result703 = _t1335
                if !isnothing(deconstruct_result703)
                    unwrapped704 = deconstruct_result703
                    write(pp, format_string(pp, unwrapped704))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                        _t1336 = _get_oneof_field(_dollar_dollar, :int_value)
                    else
                        _t1336 = nothing
                    end
                    deconstruct_result701 = _t1336
                    if !isnothing(deconstruct_result701)
                        unwrapped702 = deconstruct_result701
                        write(pp, format_int(pp, unwrapped702))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                            _t1337 = _get_oneof_field(_dollar_dollar, :float_value)
                        else
                            _t1337 = nothing
                        end
                        deconstruct_result699 = _t1337
                        if !isnothing(deconstruct_result699)
                            unwrapped700 = deconstruct_result699
                            write(pp, format_float(pp, unwrapped700))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                _t1338 = _get_oneof_field(_dollar_dollar, :uint128_value)
                            else
                                _t1338 = nothing
                            end
                            deconstruct_result697 = _t1338
                            if !isnothing(deconstruct_result697)
                                unwrapped698 = deconstruct_result697
                                write(pp, format_uint128(pp, unwrapped698))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                    _t1339 = _get_oneof_field(_dollar_dollar, :int128_value)
                                else
                                    _t1339 = nothing
                                end
                                deconstruct_result695 = _t1339
                                if !isnothing(deconstruct_result695)
                                    unwrapped696 = deconstruct_result695
                                    write(pp, format_int128(pp, unwrapped696))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                        _t1340 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                    else
                                        _t1340 = nothing
                                    end
                                    deconstruct_result693 = _t1340
                                    if !isnothing(deconstruct_result693)
                                        unwrapped694 = deconstruct_result693
                                        write(pp, format_decimal(pp, unwrapped694))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                            _t1341 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                        else
                                            _t1341 = nothing
                                        end
                                        deconstruct_result691 = _t1341
                                        if !isnothing(deconstruct_result691)
                                            unwrapped692 = deconstruct_result691
                                            pretty_boolean_value(pp, unwrapped692)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                                                _t1342 = _get_oneof_field(_dollar_dollar, :int32_value)
                                            else
                                                _t1342 = nothing
                                            end
                                            deconstruct_result689 = _t1342
                                            if !isnothing(deconstruct_result689)
                                                unwrapped690 = deconstruct_result689
                                                write(pp, (string(Int64(unwrapped690)) * "i32"))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                                    _t1343 = _get_oneof_field(_dollar_dollar, :float32_value)
                                                else
                                                    _t1343 = nothing
                                                end
                                                deconstruct_result687 = _t1343
                                                if !isnothing(deconstruct_result687)
                                                    unwrapped688 = deconstruct_result687
                                                    write(pp, (lowercase(string(Float64(unwrapped688))) * "f32"))
                                                else
                                                    fields686 = msg
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
    flat715 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat715)
        write(pp, flat715)
        return nothing
    else
        _dollar_dollar = msg
        fields710 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields711 = fields710
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field712 = unwrapped_fields711[1]
        write(pp, format_int(pp, field712))
        newline(pp)
        field713 = unwrapped_fields711[2]
        write(pp, format_int(pp, field713))
        newline(pp)
        field714 = unwrapped_fields711[3]
        write(pp, format_int(pp, field714))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat726 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat726)
        write(pp, flat726)
        return nothing
    else
        _dollar_dollar = msg
        fields716 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields717 = fields716
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field718 = unwrapped_fields717[1]
        write(pp, format_int(pp, field718))
        newline(pp)
        field719 = unwrapped_fields717[2]
        write(pp, format_int(pp, field719))
        newline(pp)
        field720 = unwrapped_fields717[3]
        write(pp, format_int(pp, field720))
        newline(pp)
        field721 = unwrapped_fields717[4]
        write(pp, format_int(pp, field721))
        newline(pp)
        field722 = unwrapped_fields717[5]
        write(pp, format_int(pp, field722))
        newline(pp)
        field723 = unwrapped_fields717[6]
        write(pp, format_int(pp, field723))
        field724 = unwrapped_fields717[7]
        if !isnothing(field724)
            newline(pp)
            opt_val725 = field724
            write(pp, format_int(pp, opt_val725))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1344 = ()
    else
        _t1344 = nothing
    end
    deconstruct_result729 = _t1344
    if !isnothing(deconstruct_result729)
        unwrapped730 = deconstruct_result729
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1345 = ()
        else
            _t1345 = nothing
        end
        deconstruct_result727 = _t1345
        if !isnothing(deconstruct_result727)
            unwrapped728 = deconstruct_result727
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat735 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat735)
        write(pp, flat735)
        return nothing
    else
        _dollar_dollar = msg
        fields731 = _dollar_dollar.fragments
        unwrapped_fields732 = fields731
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields732)
            newline(pp)
            for (i1346, elem733) in enumerate(unwrapped_fields732)
                i734 = i1346 - 1
                if (i734 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem733)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat738 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat738)
        write(pp, flat738)
        return nothing
    else
        _dollar_dollar = msg
        fields736 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields737 = fields736
        write(pp, ":")
        write(pp, unwrapped_fields737)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat745 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat745)
        write(pp, flat745)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1347 = _dollar_dollar.writes
        else
            _t1347 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1348 = _dollar_dollar.reads
        else
            _t1348 = nothing
        end
        fields739 = (_t1347, _t1348,)
        unwrapped_fields740 = fields739
        write(pp, "(epoch")
        indent_sexp!(pp)
        field741 = unwrapped_fields740[1]
        if !isnothing(field741)
            newline(pp)
            opt_val742 = field741
            pretty_epoch_writes(pp, opt_val742)
        end
        field743 = unwrapped_fields740[2]
        if !isnothing(field743)
            newline(pp)
            opt_val744 = field743
            pretty_epoch_reads(pp, opt_val744)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat749 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat749)
        write(pp, flat749)
        return nothing
    else
        fields746 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields746)
            newline(pp)
            for (i1349, elem747) in enumerate(fields746)
                i748 = i1349 - 1
                if (i748 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem747)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat758 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat758)
        write(pp, flat758)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1350 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1350 = nothing
        end
        deconstruct_result756 = _t1350
        if !isnothing(deconstruct_result756)
            unwrapped757 = deconstruct_result756
            pretty_define(pp, unwrapped757)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1351 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1351 = nothing
            end
            deconstruct_result754 = _t1351
            if !isnothing(deconstruct_result754)
                unwrapped755 = deconstruct_result754
                pretty_undefine(pp, unwrapped755)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1352 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1352 = nothing
                end
                deconstruct_result752 = _t1352
                if !isnothing(deconstruct_result752)
                    unwrapped753 = deconstruct_result752
                    pretty_context(pp, unwrapped753)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1353 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1353 = nothing
                    end
                    deconstruct_result750 = _t1353
                    if !isnothing(deconstruct_result750)
                        unwrapped751 = deconstruct_result750
                        pretty_snapshot(pp, unwrapped751)
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
    flat761 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat761)
        write(pp, flat761)
        return nothing
    else
        _dollar_dollar = msg
        fields759 = _dollar_dollar.fragment
        unwrapped_fields760 = fields759
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields760)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat768 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat768)
        write(pp, flat768)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields762 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields763 = fields762
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field764 = unwrapped_fields763[1]
        pretty_new_fragment_id(pp, field764)
        field765 = unwrapped_fields763[2]
        if !isempty(field765)
            newline(pp)
            for (i1354, elem766) in enumerate(field765)
                i767 = i1354 - 1
                if (i767 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem766)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat770 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat770)
        write(pp, flat770)
        return nothing
    else
        fields769 = msg
        pretty_fragment_id(pp, fields769)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat779 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat779)
        write(pp, flat779)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1355 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1355 = nothing
        end
        deconstruct_result777 = _t1355
        if !isnothing(deconstruct_result777)
            unwrapped778 = deconstruct_result777
            pretty_def(pp, unwrapped778)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1356 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1356 = nothing
            end
            deconstruct_result775 = _t1356
            if !isnothing(deconstruct_result775)
                unwrapped776 = deconstruct_result775
                pretty_algorithm(pp, unwrapped776)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1357 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1357 = nothing
                end
                deconstruct_result773 = _t1357
                if !isnothing(deconstruct_result773)
                    unwrapped774 = deconstruct_result773
                    pretty_constraint(pp, unwrapped774)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1358 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1358 = nothing
                    end
                    deconstruct_result771 = _t1358
                    if !isnothing(deconstruct_result771)
                        unwrapped772 = deconstruct_result771
                        pretty_data(pp, unwrapped772)
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
    flat786 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat786)
        write(pp, flat786)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1359 = _dollar_dollar.attrs
        else
            _t1359 = nothing
        end
        fields780 = (_dollar_dollar.name, _dollar_dollar.body, _t1359,)
        unwrapped_fields781 = fields780
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field782 = unwrapped_fields781[1]
        pretty_relation_id(pp, field782)
        newline(pp)
        field783 = unwrapped_fields781[2]
        pretty_abstraction(pp, field783)
        field784 = unwrapped_fields781[3]
        if !isnothing(field784)
            newline(pp)
            opt_val785 = field784
            pretty_attrs(pp, opt_val785)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat791 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat791)
        write(pp, flat791)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1361 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1360 = _t1361
        else
            _t1360 = nothing
        end
        deconstruct_result789 = _t1360
        if !isnothing(deconstruct_result789)
            unwrapped790 = deconstruct_result789
            write(pp, ":")
            write(pp, unwrapped790)
        else
            _dollar_dollar = msg
            _t1362 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result787 = _t1362
            if !isnothing(deconstruct_result787)
                unwrapped788 = deconstruct_result787
                write(pp, format_uint128(pp, unwrapped788))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat796 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat796)
        write(pp, flat796)
        return nothing
    else
        _dollar_dollar = msg
        _t1363 = deconstruct_bindings(pp, _dollar_dollar)
        fields792 = (_t1363, _dollar_dollar.value,)
        unwrapped_fields793 = fields792
        write(pp, "(")
        indent!(pp)
        field794 = unwrapped_fields793[1]
        pretty_bindings(pp, field794)
        newline(pp)
        field795 = unwrapped_fields793[2]
        pretty_formula(pp, field795)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat804 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat804)
        write(pp, flat804)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1364 = _dollar_dollar[2]
        else
            _t1364 = nothing
        end
        fields797 = (_dollar_dollar[1], _t1364,)
        unwrapped_fields798 = fields797
        write(pp, "[")
        indent!(pp)
        field799 = unwrapped_fields798[1]
        for (i1365, elem800) in enumerate(field799)
            i801 = i1365 - 1
            if (i801 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem800)
        end
        field802 = unwrapped_fields798[2]
        if !isnothing(field802)
            newline(pp)
            opt_val803 = field802
            pretty_value_bindings(pp, opt_val803)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat809 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat809)
        write(pp, flat809)
        return nothing
    else
        _dollar_dollar = msg
        fields805 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields806 = fields805
        field807 = unwrapped_fields806[1]
        write(pp, field807)
        write(pp, "::")
        field808 = unwrapped_fields806[2]
        pretty_type(pp, field808)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat836 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat836)
        write(pp, flat836)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1366 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1366 = nothing
        end
        deconstruct_result834 = _t1366
        if !isnothing(deconstruct_result834)
            unwrapped835 = deconstruct_result834
            pretty_unspecified_type(pp, unwrapped835)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1367 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1367 = nothing
            end
            deconstruct_result832 = _t1367
            if !isnothing(deconstruct_result832)
                unwrapped833 = deconstruct_result832
                pretty_string_type(pp, unwrapped833)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1368 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1368 = nothing
                end
                deconstruct_result830 = _t1368
                if !isnothing(deconstruct_result830)
                    unwrapped831 = deconstruct_result830
                    pretty_int_type(pp, unwrapped831)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1369 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1369 = nothing
                    end
                    deconstruct_result828 = _t1369
                    if !isnothing(deconstruct_result828)
                        unwrapped829 = deconstruct_result828
                        pretty_float_type(pp, unwrapped829)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1370 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1370 = nothing
                        end
                        deconstruct_result826 = _t1370
                        if !isnothing(deconstruct_result826)
                            unwrapped827 = deconstruct_result826
                            pretty_uint128_type(pp, unwrapped827)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1371 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1371 = nothing
                            end
                            deconstruct_result824 = _t1371
                            if !isnothing(deconstruct_result824)
                                unwrapped825 = deconstruct_result824
                                pretty_int128_type(pp, unwrapped825)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1372 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1372 = nothing
                                end
                                deconstruct_result822 = _t1372
                                if !isnothing(deconstruct_result822)
                                    unwrapped823 = deconstruct_result822
                                    pretty_date_type(pp, unwrapped823)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1373 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1373 = nothing
                                    end
                                    deconstruct_result820 = _t1373
                                    if !isnothing(deconstruct_result820)
                                        unwrapped821 = deconstruct_result820
                                        pretty_datetime_type(pp, unwrapped821)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1374 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1374 = nothing
                                        end
                                        deconstruct_result818 = _t1374
                                        if !isnothing(deconstruct_result818)
                                            unwrapped819 = deconstruct_result818
                                            pretty_missing_type(pp, unwrapped819)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1375 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1375 = nothing
                                            end
                                            deconstruct_result816 = _t1375
                                            if !isnothing(deconstruct_result816)
                                                unwrapped817 = deconstruct_result816
                                                pretty_decimal_type(pp, unwrapped817)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1376 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1376 = nothing
                                                end
                                                deconstruct_result814 = _t1376
                                                if !isnothing(deconstruct_result814)
                                                    unwrapped815 = deconstruct_result814
                                                    pretty_boolean_type(pp, unwrapped815)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1377 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1377 = nothing
                                                    end
                                                    deconstruct_result812 = _t1377
                                                    if !isnothing(deconstruct_result812)
                                                        unwrapped813 = deconstruct_result812
                                                        pretty_int32_type(pp, unwrapped813)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1378 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1378 = nothing
                                                        end
                                                        deconstruct_result810 = _t1378
                                                        if !isnothing(deconstruct_result810)
                                                            unwrapped811 = deconstruct_result810
                                                            pretty_float32_type(pp, unwrapped811)
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
    fields837 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields838 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields839 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields840 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields841 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields842 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields843 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields844 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields845 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat850 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat850)
        write(pp, flat850)
        return nothing
    else
        _dollar_dollar = msg
        fields846 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields847 = fields846
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field848 = unwrapped_fields847[1]
        write(pp, format_int(pp, field848))
        newline(pp)
        field849 = unwrapped_fields847[2]
        write(pp, format_int(pp, field849))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields851 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields852 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields853 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat857 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat857)
        write(pp, flat857)
        return nothing
    else
        fields854 = msg
        write(pp, "|")
        if !isempty(fields854)
            write(pp, " ")
            for (i1379, elem855) in enumerate(fields854)
                i856 = i1379 - 1
                if (i856 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem855)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat884 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat884)
        write(pp, flat884)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1380 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1380 = nothing
        end
        deconstruct_result882 = _t1380
        if !isnothing(deconstruct_result882)
            unwrapped883 = deconstruct_result882
            pretty_true(pp, unwrapped883)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1381 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1381 = nothing
            end
            deconstruct_result880 = _t1381
            if !isnothing(deconstruct_result880)
                unwrapped881 = deconstruct_result880
                pretty_false(pp, unwrapped881)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1382 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1382 = nothing
                end
                deconstruct_result878 = _t1382
                if !isnothing(deconstruct_result878)
                    unwrapped879 = deconstruct_result878
                    pretty_exists(pp, unwrapped879)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1383 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1383 = nothing
                    end
                    deconstruct_result876 = _t1383
                    if !isnothing(deconstruct_result876)
                        unwrapped877 = deconstruct_result876
                        pretty_reduce(pp, unwrapped877)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1384 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1384 = nothing
                        end
                        deconstruct_result874 = _t1384
                        if !isnothing(deconstruct_result874)
                            unwrapped875 = deconstruct_result874
                            pretty_conjunction(pp, unwrapped875)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1385 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1385 = nothing
                            end
                            deconstruct_result872 = _t1385
                            if !isnothing(deconstruct_result872)
                                unwrapped873 = deconstruct_result872
                                pretty_disjunction(pp, unwrapped873)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1386 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1386 = nothing
                                end
                                deconstruct_result870 = _t1386
                                if !isnothing(deconstruct_result870)
                                    unwrapped871 = deconstruct_result870
                                    pretty_not(pp, unwrapped871)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1387 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1387 = nothing
                                    end
                                    deconstruct_result868 = _t1387
                                    if !isnothing(deconstruct_result868)
                                        unwrapped869 = deconstruct_result868
                                        pretty_ffi(pp, unwrapped869)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1388 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1388 = nothing
                                        end
                                        deconstruct_result866 = _t1388
                                        if !isnothing(deconstruct_result866)
                                            unwrapped867 = deconstruct_result866
                                            pretty_atom(pp, unwrapped867)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1389 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1389 = nothing
                                            end
                                            deconstruct_result864 = _t1389
                                            if !isnothing(deconstruct_result864)
                                                unwrapped865 = deconstruct_result864
                                                pretty_pragma(pp, unwrapped865)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1390 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1390 = nothing
                                                end
                                                deconstruct_result862 = _t1390
                                                if !isnothing(deconstruct_result862)
                                                    unwrapped863 = deconstruct_result862
                                                    pretty_primitive(pp, unwrapped863)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1391 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1391 = nothing
                                                    end
                                                    deconstruct_result860 = _t1391
                                                    if !isnothing(deconstruct_result860)
                                                        unwrapped861 = deconstruct_result860
                                                        pretty_rel_atom(pp, unwrapped861)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1392 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1392 = nothing
                                                        end
                                                        deconstruct_result858 = _t1392
                                                        if !isnothing(deconstruct_result858)
                                                            unwrapped859 = deconstruct_result858
                                                            pretty_cast(pp, unwrapped859)
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
    fields885 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields886 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat891 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat891)
        write(pp, flat891)
        return nothing
    else
        _dollar_dollar = msg
        _t1393 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields887 = (_t1393, _dollar_dollar.body.value,)
        unwrapped_fields888 = fields887
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field889 = unwrapped_fields888[1]
        pretty_bindings(pp, field889)
        newline(pp)
        field890 = unwrapped_fields888[2]
        pretty_formula(pp, field890)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat897 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat897)
        write(pp, flat897)
        return nothing
    else
        _dollar_dollar = msg
        fields892 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields893 = fields892
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field894 = unwrapped_fields893[1]
        pretty_abstraction(pp, field894)
        newline(pp)
        field895 = unwrapped_fields893[2]
        pretty_abstraction(pp, field895)
        newline(pp)
        field896 = unwrapped_fields893[3]
        pretty_terms(pp, field896)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat901 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat901)
        write(pp, flat901)
        return nothing
    else
        fields898 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields898)
            newline(pp)
            for (i1394, elem899) in enumerate(fields898)
                i900 = i1394 - 1
                if (i900 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem899)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat906 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat906)
        write(pp, flat906)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1395 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1395 = nothing
        end
        deconstruct_result904 = _t1395
        if !isnothing(deconstruct_result904)
            unwrapped905 = deconstruct_result904
            pretty_var(pp, unwrapped905)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1396 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1396 = nothing
            end
            deconstruct_result902 = _t1396
            if !isnothing(deconstruct_result902)
                unwrapped903 = deconstruct_result902
                pretty_constant(pp, unwrapped903)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat909 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat909)
        write(pp, flat909)
        return nothing
    else
        _dollar_dollar = msg
        fields907 = _dollar_dollar.name
        unwrapped_fields908 = fields907
        write(pp, unwrapped_fields908)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat911 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat911)
        write(pp, flat911)
        return nothing
    else
        fields910 = msg
        pretty_value(pp, fields910)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat916 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat916)
        write(pp, flat916)
        return nothing
    else
        _dollar_dollar = msg
        fields912 = _dollar_dollar.args
        unwrapped_fields913 = fields912
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields913)
            newline(pp)
            for (i1397, elem914) in enumerate(unwrapped_fields913)
                i915 = i1397 - 1
                if (i915 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem914)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat921 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat921)
        write(pp, flat921)
        return nothing
    else
        _dollar_dollar = msg
        fields917 = _dollar_dollar.args
        unwrapped_fields918 = fields917
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields918)
            newline(pp)
            for (i1398, elem919) in enumerate(unwrapped_fields918)
                i920 = i1398 - 1
                if (i920 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem919)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat924 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat924)
        write(pp, flat924)
        return nothing
    else
        _dollar_dollar = msg
        fields922 = _dollar_dollar.arg
        unwrapped_fields923 = fields922
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields923)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat930 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat930)
        write(pp, flat930)
        return nothing
    else
        _dollar_dollar = msg
        fields925 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields926 = fields925
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field927 = unwrapped_fields926[1]
        pretty_name(pp, field927)
        newline(pp)
        field928 = unwrapped_fields926[2]
        pretty_ffi_args(pp, field928)
        newline(pp)
        field929 = unwrapped_fields926[3]
        pretty_terms(pp, field929)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat932 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat932)
        write(pp, flat932)
        return nothing
    else
        fields931 = msg
        write(pp, ":")
        write(pp, fields931)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat936 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat936)
        write(pp, flat936)
        return nothing
    else
        fields933 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields933)
            newline(pp)
            for (i1399, elem934) in enumerate(fields933)
                i935 = i1399 - 1
                if (i935 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem934)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat943 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat943)
        write(pp, flat943)
        return nothing
    else
        _dollar_dollar = msg
        fields937 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields938 = fields937
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field939 = unwrapped_fields938[1]
        pretty_relation_id(pp, field939)
        field940 = unwrapped_fields938[2]
        if !isempty(field940)
            newline(pp)
            for (i1400, elem941) in enumerate(field940)
                i942 = i1400 - 1
                if (i942 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem941)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat950 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat950)
        write(pp, flat950)
        return nothing
    else
        _dollar_dollar = msg
        fields944 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields945 = fields944
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field946 = unwrapped_fields945[1]
        pretty_name(pp, field946)
        field947 = unwrapped_fields945[2]
        if !isempty(field947)
            newline(pp)
            for (i1401, elem948) in enumerate(field947)
                i949 = i1401 - 1
                if (i949 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem948)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat966 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat966)
        write(pp, flat966)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1402 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1402 = nothing
        end
        guard_result965 = _t1402
        if !isnothing(guard_result965)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1403 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1403 = nothing
            end
            guard_result964 = _t1403
            if !isnothing(guard_result964)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1404 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1404 = nothing
                end
                guard_result963 = _t1404
                if !isnothing(guard_result963)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1405 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1405 = nothing
                    end
                    guard_result962 = _t1405
                    if !isnothing(guard_result962)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1406 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1406 = nothing
                        end
                        guard_result961 = _t1406
                        if !isnothing(guard_result961)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1407 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1407 = nothing
                            end
                            guard_result960 = _t1407
                            if !isnothing(guard_result960)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1408 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1408 = nothing
                                end
                                guard_result959 = _t1408
                                if !isnothing(guard_result959)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1409 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1409 = nothing
                                    end
                                    guard_result958 = _t1409
                                    if !isnothing(guard_result958)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1410 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1410 = nothing
                                        end
                                        guard_result957 = _t1410
                                        if !isnothing(guard_result957)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields951 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields952 = fields951
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field953 = unwrapped_fields952[1]
                                            pretty_name(pp, field953)
                                            field954 = unwrapped_fields952[2]
                                            if !isempty(field954)
                                                newline(pp)
                                                for (i1411, elem955) in enumerate(field954)
                                                    i956 = i1411 - 1
                                                    if (i956 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem955)
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
    flat971 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat971)
        write(pp, flat971)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1412 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1412 = nothing
        end
        fields967 = _t1412
        unwrapped_fields968 = fields967
        write(pp, "(=")
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

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat976 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat976)
        write(pp, flat976)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1413 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1413 = nothing
        end
        fields972 = _t1413
        unwrapped_fields973 = fields972
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field974 = unwrapped_fields973[1]
        pretty_term(pp, field974)
        newline(pp)
        field975 = unwrapped_fields973[2]
        pretty_term(pp, field975)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat981 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat981)
        write(pp, flat981)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1414 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1414 = nothing
        end
        fields977 = _t1414
        unwrapped_fields978 = fields977
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field979 = unwrapped_fields978[1]
        pretty_term(pp, field979)
        newline(pp)
        field980 = unwrapped_fields978[2]
        pretty_term(pp, field980)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat986 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat986)
        write(pp, flat986)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1415 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1415 = nothing
        end
        fields982 = _t1415
        unwrapped_fields983 = fields982
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field984 = unwrapped_fields983[1]
        pretty_term(pp, field984)
        newline(pp)
        field985 = unwrapped_fields983[2]
        pretty_term(pp, field985)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat991 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat991)
        write(pp, flat991)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1416 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1416 = nothing
        end
        fields987 = _t1416
        unwrapped_fields988 = fields987
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field989 = unwrapped_fields988[1]
        pretty_term(pp, field989)
        newline(pp)
        field990 = unwrapped_fields988[2]
        pretty_term(pp, field990)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat997 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat997)
        write(pp, flat997)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1417 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1417 = nothing
        end
        fields992 = _t1417
        unwrapped_fields993 = fields992
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field994 = unwrapped_fields993[1]
        pretty_term(pp, field994)
        newline(pp)
        field995 = unwrapped_fields993[2]
        pretty_term(pp, field995)
        newline(pp)
        field996 = unwrapped_fields993[3]
        pretty_term(pp, field996)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1003 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1003)
        write(pp, flat1003)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1418 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1418 = nothing
        end
        fields998 = _t1418
        unwrapped_fields999 = fields998
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1000 = unwrapped_fields999[1]
        pretty_term(pp, field1000)
        newline(pp)
        field1001 = unwrapped_fields999[2]
        pretty_term(pp, field1001)
        newline(pp)
        field1002 = unwrapped_fields999[3]
        pretty_term(pp, field1002)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1009 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1009)
        write(pp, flat1009)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1419 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1419 = nothing
        end
        fields1004 = _t1419
        unwrapped_fields1005 = fields1004
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1006 = unwrapped_fields1005[1]
        pretty_term(pp, field1006)
        newline(pp)
        field1007 = unwrapped_fields1005[2]
        pretty_term(pp, field1007)
        newline(pp)
        field1008 = unwrapped_fields1005[3]
        pretty_term(pp, field1008)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1015 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1015)
        write(pp, flat1015)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1420 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1420 = nothing
        end
        fields1010 = _t1420
        unwrapped_fields1011 = fields1010
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1012 = unwrapped_fields1011[1]
        pretty_term(pp, field1012)
        newline(pp)
        field1013 = unwrapped_fields1011[2]
        pretty_term(pp, field1013)
        newline(pp)
        field1014 = unwrapped_fields1011[3]
        pretty_term(pp, field1014)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1020 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1020)
        write(pp, flat1020)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1421 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1421 = nothing
        end
        deconstruct_result1018 = _t1421
        if !isnothing(deconstruct_result1018)
            unwrapped1019 = deconstruct_result1018
            pretty_specialized_value(pp, unwrapped1019)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1422 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1422 = nothing
            end
            deconstruct_result1016 = _t1422
            if !isnothing(deconstruct_result1016)
                unwrapped1017 = deconstruct_result1016
                pretty_term(pp, unwrapped1017)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1022 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1022)
        write(pp, flat1022)
        return nothing
    else
        fields1021 = msg
        write(pp, "#")
        pretty_value(pp, fields1021)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1029 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1029)
        write(pp, flat1029)
        return nothing
    else
        _dollar_dollar = msg
        fields1023 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1024 = fields1023
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1025 = unwrapped_fields1024[1]
        pretty_name(pp, field1025)
        field1026 = unwrapped_fields1024[2]
        if !isempty(field1026)
            newline(pp)
            for (i1423, elem1027) in enumerate(field1026)
                i1028 = i1423 - 1
                if (i1028 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1027)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1034 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1034)
        write(pp, flat1034)
        return nothing
    else
        _dollar_dollar = msg
        fields1030 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1031 = fields1030
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1032 = unwrapped_fields1031[1]
        pretty_term(pp, field1032)
        newline(pp)
        field1033 = unwrapped_fields1031[2]
        pretty_term(pp, field1033)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1038 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1038)
        write(pp, flat1038)
        return nothing
    else
        fields1035 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1035)
            newline(pp)
            for (i1424, elem1036) in enumerate(fields1035)
                i1037 = i1424 - 1
                if (i1037 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1036)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1045 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1045)
        write(pp, flat1045)
        return nothing
    else
        _dollar_dollar = msg
        fields1039 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1040 = fields1039
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1041 = unwrapped_fields1040[1]
        pretty_name(pp, field1041)
        field1042 = unwrapped_fields1040[2]
        if !isempty(field1042)
            newline(pp)
            for (i1425, elem1043) in enumerate(field1042)
                i1044 = i1425 - 1
                if (i1044 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem1043)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1052 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1052)
        write(pp, flat1052)
        return nothing
    else
        _dollar_dollar = msg
        fields1046 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1047 = fields1046
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1048 = unwrapped_fields1047[1]
        if !isempty(field1048)
            newline(pp)
            for (i1426, elem1049) in enumerate(field1048)
                i1050 = i1426 - 1
                if (i1050 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1049)
            end
        end
        newline(pp)
        field1051 = unwrapped_fields1047[2]
        pretty_script(pp, field1051)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1057 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1057)
        write(pp, flat1057)
        return nothing
    else
        _dollar_dollar = msg
        fields1053 = _dollar_dollar.constructs
        unwrapped_fields1054 = fields1053
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1054)
            newline(pp)
            for (i1427, elem1055) in enumerate(unwrapped_fields1054)
                i1056 = i1427 - 1
                if (i1056 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1055)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1062 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1062)
        write(pp, flat1062)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1428 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1428 = nothing
        end
        deconstruct_result1060 = _t1428
        if !isnothing(deconstruct_result1060)
            unwrapped1061 = deconstruct_result1060
            pretty_loop(pp, unwrapped1061)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1429 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1429 = nothing
            end
            deconstruct_result1058 = _t1429
            if !isnothing(deconstruct_result1058)
                unwrapped1059 = deconstruct_result1058
                pretty_instruction(pp, unwrapped1059)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1067 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1067)
        write(pp, flat1067)
        return nothing
    else
        _dollar_dollar = msg
        fields1063 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1064 = fields1063
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1065 = unwrapped_fields1064[1]
        pretty_init(pp, field1065)
        newline(pp)
        field1066 = unwrapped_fields1064[2]
        pretty_script(pp, field1066)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1071 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1071)
        write(pp, flat1071)
        return nothing
    else
        fields1068 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1068)
            newline(pp)
            for (i1430, elem1069) in enumerate(fields1068)
                i1070 = i1430 - 1
                if (i1070 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1069)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1082 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1082)
        write(pp, flat1082)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1431 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1431 = nothing
        end
        deconstruct_result1080 = _t1431
        if !isnothing(deconstruct_result1080)
            unwrapped1081 = deconstruct_result1080
            pretty_assign(pp, unwrapped1081)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1432 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1432 = nothing
            end
            deconstruct_result1078 = _t1432
            if !isnothing(deconstruct_result1078)
                unwrapped1079 = deconstruct_result1078
                pretty_upsert(pp, unwrapped1079)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1433 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1433 = nothing
                end
                deconstruct_result1076 = _t1433
                if !isnothing(deconstruct_result1076)
                    unwrapped1077 = deconstruct_result1076
                    pretty_break(pp, unwrapped1077)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1434 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1434 = nothing
                    end
                    deconstruct_result1074 = _t1434
                    if !isnothing(deconstruct_result1074)
                        unwrapped1075 = deconstruct_result1074
                        pretty_monoid_def(pp, unwrapped1075)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1435 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1435 = nothing
                        end
                        deconstruct_result1072 = _t1435
                        if !isnothing(deconstruct_result1072)
                            unwrapped1073 = deconstruct_result1072
                            pretty_monus_def(pp, unwrapped1073)
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
    flat1089 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1089)
        write(pp, flat1089)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1436 = _dollar_dollar.attrs
        else
            _t1436 = nothing
        end
        fields1083 = (_dollar_dollar.name, _dollar_dollar.body, _t1436,)
        unwrapped_fields1084 = fields1083
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1085 = unwrapped_fields1084[1]
        pretty_relation_id(pp, field1085)
        newline(pp)
        field1086 = unwrapped_fields1084[2]
        pretty_abstraction(pp, field1086)
        field1087 = unwrapped_fields1084[3]
        if !isnothing(field1087)
            newline(pp)
            opt_val1088 = field1087
            pretty_attrs(pp, opt_val1088)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1096 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1096)
        write(pp, flat1096)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1437 = _dollar_dollar.attrs
        else
            _t1437 = nothing
        end
        fields1090 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1437,)
        unwrapped_fields1091 = fields1090
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1092 = unwrapped_fields1091[1]
        pretty_relation_id(pp, field1092)
        newline(pp)
        field1093 = unwrapped_fields1091[2]
        pretty_abstraction_with_arity(pp, field1093)
        field1094 = unwrapped_fields1091[3]
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

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1101 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1101)
        write(pp, flat1101)
        return nothing
    else
        _dollar_dollar = msg
        _t1438 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1097 = (_t1438, _dollar_dollar[1].value,)
        unwrapped_fields1098 = fields1097
        write(pp, "(")
        indent!(pp)
        field1099 = unwrapped_fields1098[1]
        pretty_bindings(pp, field1099)
        newline(pp)
        field1100 = unwrapped_fields1098[2]
        pretty_formula(pp, field1100)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1108 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1108)
        write(pp, flat1108)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1439 = _dollar_dollar.attrs
        else
            _t1439 = nothing
        end
        fields1102 = (_dollar_dollar.name, _dollar_dollar.body, _t1439,)
        unwrapped_fields1103 = fields1102
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1104 = unwrapped_fields1103[1]
        pretty_relation_id(pp, field1104)
        newline(pp)
        field1105 = unwrapped_fields1103[2]
        pretty_abstraction(pp, field1105)
        field1106 = unwrapped_fields1103[3]
        if !isnothing(field1106)
            newline(pp)
            opt_val1107 = field1106
            pretty_attrs(pp, opt_val1107)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1116 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1116)
        write(pp, flat1116)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1440 = _dollar_dollar.attrs
        else
            _t1440 = nothing
        end
        fields1109 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1440,)
        unwrapped_fields1110 = fields1109
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1111 = unwrapped_fields1110[1]
        pretty_monoid(pp, field1111)
        newline(pp)
        field1112 = unwrapped_fields1110[2]
        pretty_relation_id(pp, field1112)
        newline(pp)
        field1113 = unwrapped_fields1110[3]
        pretty_abstraction_with_arity(pp, field1113)
        field1114 = unwrapped_fields1110[4]
        if !isnothing(field1114)
            newline(pp)
            opt_val1115 = field1114
            pretty_attrs(pp, opt_val1115)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1125 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1125)
        write(pp, flat1125)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1441 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1441 = nothing
        end
        deconstruct_result1123 = _t1441
        if !isnothing(deconstruct_result1123)
            unwrapped1124 = deconstruct_result1123
            pretty_or_monoid(pp, unwrapped1124)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1442 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1442 = nothing
            end
            deconstruct_result1121 = _t1442
            if !isnothing(deconstruct_result1121)
                unwrapped1122 = deconstruct_result1121
                pretty_min_monoid(pp, unwrapped1122)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1443 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1443 = nothing
                end
                deconstruct_result1119 = _t1443
                if !isnothing(deconstruct_result1119)
                    unwrapped1120 = deconstruct_result1119
                    pretty_max_monoid(pp, unwrapped1120)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1444 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1444 = nothing
                    end
                    deconstruct_result1117 = _t1444
                    if !isnothing(deconstruct_result1117)
                        unwrapped1118 = deconstruct_result1117
                        pretty_sum_monoid(pp, unwrapped1118)
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
    fields1126 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1129 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1129)
        write(pp, flat1129)
        return nothing
    else
        _dollar_dollar = msg
        fields1127 = _dollar_dollar.var"#type"
        unwrapped_fields1128 = fields1127
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1128)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1132 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1132)
        write(pp, flat1132)
        return nothing
    else
        _dollar_dollar = msg
        fields1130 = _dollar_dollar.var"#type"
        unwrapped_fields1131 = fields1130
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1131)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1135 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1135)
        write(pp, flat1135)
        return nothing
    else
        _dollar_dollar = msg
        fields1133 = _dollar_dollar.var"#type"
        unwrapped_fields1134 = fields1133
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1134)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1143 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1143)
        write(pp, flat1143)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1445 = _dollar_dollar.attrs
        else
            _t1445 = nothing
        end
        fields1136 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1445,)
        unwrapped_fields1137 = fields1136
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1138 = unwrapped_fields1137[1]
        pretty_monoid(pp, field1138)
        newline(pp)
        field1139 = unwrapped_fields1137[2]
        pretty_relation_id(pp, field1139)
        newline(pp)
        field1140 = unwrapped_fields1137[3]
        pretty_abstraction_with_arity(pp, field1140)
        field1141 = unwrapped_fields1137[4]
        if !isnothing(field1141)
            newline(pp)
            opt_val1142 = field1141
            pretty_attrs(pp, opt_val1142)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1150 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1150)
        write(pp, flat1150)
        return nothing
    else
        _dollar_dollar = msg
        fields1144 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1145 = fields1144
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1146 = unwrapped_fields1145[1]
        pretty_relation_id(pp, field1146)
        newline(pp)
        field1147 = unwrapped_fields1145[2]
        pretty_abstraction(pp, field1147)
        newline(pp)
        field1148 = unwrapped_fields1145[3]
        pretty_functional_dependency_keys(pp, field1148)
        newline(pp)
        field1149 = unwrapped_fields1145[4]
        pretty_functional_dependency_values(pp, field1149)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1154 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1154)
        write(pp, flat1154)
        return nothing
    else
        fields1151 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1151)
            newline(pp)
            for (i1446, elem1152) in enumerate(fields1151)
                i1153 = i1446 - 1
                if (i1153 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1152)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1158 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1158)
        write(pp, flat1158)
        return nothing
    else
        fields1155 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1155)
            newline(pp)
            for (i1447, elem1156) in enumerate(fields1155)
                i1157 = i1447 - 1
                if (i1157 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1156)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1165 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1165)
        write(pp, flat1165)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1448 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1448 = nothing
        end
        deconstruct_result1163 = _t1448
        if !isnothing(deconstruct_result1163)
            unwrapped1164 = deconstruct_result1163
            pretty_edb(pp, unwrapped1164)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1449 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1449 = nothing
            end
            deconstruct_result1161 = _t1449
            if !isnothing(deconstruct_result1161)
                unwrapped1162 = deconstruct_result1161
                pretty_betree_relation(pp, unwrapped1162)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1450 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1450 = nothing
                end
                deconstruct_result1159 = _t1450
                if !isnothing(deconstruct_result1159)
                    unwrapped1160 = deconstruct_result1159
                    pretty_csv_data(pp, unwrapped1160)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_edb(pp::PrettyPrinter, msg::Proto.EDB)
    flat1171 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1171)
        write(pp, flat1171)
        return nothing
    else
        _dollar_dollar = msg
        fields1166 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1167 = fields1166
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1168 = unwrapped_fields1167[1]
        pretty_relation_id(pp, field1168)
        newline(pp)
        field1169 = unwrapped_fields1167[2]
        pretty_edb_path(pp, field1169)
        newline(pp)
        field1170 = unwrapped_fields1167[3]
        pretty_edb_types(pp, field1170)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1175 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1175)
        write(pp, flat1175)
        return nothing
    else
        fields1172 = msg
        write(pp, "[")
        indent!(pp)
        for (i1451, elem1173) in enumerate(fields1172)
            i1174 = i1451 - 1
            if (i1174 > 0)
                newline(pp)
            end
            write(pp, format_string(pp, elem1173))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1179 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1179)
        write(pp, flat1179)
        return nothing
    else
        fields1176 = msg
        write(pp, "[")
        indent!(pp)
        for (i1452, elem1177) in enumerate(fields1176)
            i1178 = i1452 - 1
            if (i1178 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1177)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1184 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1184)
        write(pp, flat1184)
        return nothing
    else
        _dollar_dollar = msg
        fields1180 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1181 = fields1180
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1182 = unwrapped_fields1181[1]
        pretty_relation_id(pp, field1182)
        newline(pp)
        field1183 = unwrapped_fields1181[2]
        pretty_betree_info(pp, field1183)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1190 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1190)
        write(pp, flat1190)
        return nothing
    else
        _dollar_dollar = msg
        _t1453 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1185 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1453,)
        unwrapped_fields1186 = fields1185
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1187 = unwrapped_fields1186[1]
        pretty_betree_info_key_types(pp, field1187)
        newline(pp)
        field1188 = unwrapped_fields1186[2]
        pretty_betree_info_value_types(pp, field1188)
        newline(pp)
        field1189 = unwrapped_fields1186[3]
        pretty_config_dict(pp, field1189)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1194 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1194)
        write(pp, flat1194)
        return nothing
    else
        fields1191 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1191)
            newline(pp)
            for (i1454, elem1192) in enumerate(fields1191)
                i1193 = i1454 - 1
                if (i1193 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1192)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1198 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1198)
        write(pp, flat1198)
        return nothing
    else
        fields1195 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1195)
            newline(pp)
            for (i1455, elem1196) in enumerate(fields1195)
                i1197 = i1455 - 1
                if (i1197 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1196)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1205 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1205)
        write(pp, flat1205)
        return nothing
    else
        _dollar_dollar = msg
        fields1199 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1200 = fields1199
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1201 = unwrapped_fields1200[1]
        pretty_csvlocator(pp, field1201)
        newline(pp)
        field1202 = unwrapped_fields1200[2]
        pretty_csv_config(pp, field1202)
        newline(pp)
        field1203 = unwrapped_fields1200[3]
        pretty_gnf_columns(pp, field1203)
        newline(pp)
        field1204 = unwrapped_fields1200[4]
        pretty_csv_asof(pp, field1204)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1212 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1212)
        write(pp, flat1212)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1456 = _dollar_dollar.paths
        else
            _t1456 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1457 = String(copy(_dollar_dollar.inline_data))
        else
            _t1457 = nothing
        end
        fields1206 = (_t1456, _t1457,)
        unwrapped_fields1207 = fields1206
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1208 = unwrapped_fields1207[1]
        if !isnothing(field1208)
            newline(pp)
            opt_val1209 = field1208
            pretty_csv_locator_paths(pp, opt_val1209)
        end
        field1210 = unwrapped_fields1207[2]
        if !isnothing(field1210)
            newline(pp)
            opt_val1211 = field1210
            pretty_csv_locator_inline_data(pp, opt_val1211)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1216 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1216)
        write(pp, flat1216)
        return nothing
    else
        fields1213 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1213)
            newline(pp)
            for (i1458, elem1214) in enumerate(fields1213)
                i1215 = i1458 - 1
                if (i1215 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1214))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1218 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1218)
        write(pp, flat1218)
        return nothing
    else
        fields1217 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1217))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1221 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1221)
        write(pp, flat1221)
        return nothing
    else
        _dollar_dollar = msg
        _t1459 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1219 = _t1459
        unwrapped_fields1220 = fields1219
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1220)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1225 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1225)
        write(pp, flat1225)
        return nothing
    else
        fields1222 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1222)
            newline(pp)
            for (i1460, elem1223) in enumerate(fields1222)
                i1224 = i1460 - 1
                if (i1224 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1223)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1234 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1234)
        write(pp, flat1234)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1461 = _dollar_dollar.target_id
        else
            _t1461 = nothing
        end
        fields1226 = (_dollar_dollar.column_path, _t1461, _dollar_dollar.types,)
        unwrapped_fields1227 = fields1226
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1228 = unwrapped_fields1227[1]
        pretty_gnf_column_path(pp, field1228)
        field1229 = unwrapped_fields1227[2]
        if !isnothing(field1229)
            newline(pp)
            opt_val1230 = field1229
            pretty_relation_id(pp, opt_val1230)
        end
        newline(pp)
        write(pp, "[")
        field1231 = unwrapped_fields1227[3]
        for (i1462, elem1232) in enumerate(field1231)
            i1233 = i1462 - 1
            if (i1233 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1232)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1241 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1241)
        write(pp, flat1241)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1463 = _dollar_dollar[1]
        else
            _t1463 = nothing
        end
        deconstruct_result1239 = _t1463
        if !isnothing(deconstruct_result1239)
            unwrapped1240 = deconstruct_result1239
            write(pp, format_string(pp, unwrapped1240))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1464 = _dollar_dollar
            else
                _t1464 = nothing
            end
            deconstruct_result1235 = _t1464
            if !isnothing(deconstruct_result1235)
                unwrapped1236 = deconstruct_result1235
                write(pp, "[")
                indent!(pp)
                for (i1465, elem1237) in enumerate(unwrapped1236)
                    i1238 = i1465 - 1
                    if (i1238 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(pp, elem1237))
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
    flat1243 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1243)
        write(pp, flat1243)
        return nothing
    else
        fields1242 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1242))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1246 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1246)
        write(pp, flat1246)
        return nothing
    else
        _dollar_dollar = msg
        fields1244 = _dollar_dollar.fragment_id
        unwrapped_fields1245 = fields1244
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1245)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1251 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1251)
        write(pp, flat1251)
        return nothing
    else
        _dollar_dollar = msg
        fields1247 = _dollar_dollar.relations
        unwrapped_fields1248 = fields1247
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1248)
            newline(pp)
            for (i1466, elem1249) in enumerate(unwrapped_fields1248)
                i1250 = i1466 - 1
                if (i1250 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1249)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1256 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1256)
        write(pp, flat1256)
        return nothing
    else
        _dollar_dollar = msg
        fields1252 = _dollar_dollar.mappings
        unwrapped_fields1253 = fields1252
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1253)
            newline(pp)
            for (i1467, elem1254) in enumerate(unwrapped_fields1253)
                i1255 = i1467 - 1
                if (i1255 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1254)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1261 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1261)
        write(pp, flat1261)
        return nothing
    else
        _dollar_dollar = msg
        fields1257 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1258 = fields1257
        field1259 = unwrapped_fields1258[1]
        pretty_edb_path(pp, field1259)
        write(pp, " ")
        field1260 = unwrapped_fields1258[2]
        pretty_relation_id(pp, field1260)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1265 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1265)
        write(pp, flat1265)
        return nothing
    else
        fields1262 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1262)
            newline(pp)
            for (i1468, elem1263) in enumerate(fields1262)
                i1264 = i1468 - 1
                if (i1264 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1263)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1276 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1276)
        write(pp, flat1276)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1469 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1469 = nothing
        end
        deconstruct_result1274 = _t1469
        if !isnothing(deconstruct_result1274)
            unwrapped1275 = deconstruct_result1274
            pretty_demand(pp, unwrapped1275)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1470 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1470 = nothing
            end
            deconstruct_result1272 = _t1470
            if !isnothing(deconstruct_result1272)
                unwrapped1273 = deconstruct_result1272
                pretty_output(pp, unwrapped1273)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1471 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1471 = nothing
                end
                deconstruct_result1270 = _t1471
                if !isnothing(deconstruct_result1270)
                    unwrapped1271 = deconstruct_result1270
                    pretty_what_if(pp, unwrapped1271)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1472 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1472 = nothing
                    end
                    deconstruct_result1268 = _t1472
                    if !isnothing(deconstruct_result1268)
                        unwrapped1269 = deconstruct_result1268
                        pretty_abort(pp, unwrapped1269)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1473 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1473 = nothing
                        end
                        deconstruct_result1266 = _t1473
                        if !isnothing(deconstruct_result1266)
                            unwrapped1267 = deconstruct_result1266
                            pretty_export(pp, unwrapped1267)
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
    flat1279 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1279)
        write(pp, flat1279)
        return nothing
    else
        _dollar_dollar = msg
        fields1277 = _dollar_dollar.relation_id
        unwrapped_fields1278 = fields1277
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1278)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1284 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1284)
        write(pp, flat1284)
        return nothing
    else
        _dollar_dollar = msg
        fields1280 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1281 = fields1280
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1282 = unwrapped_fields1281[1]
        pretty_name(pp, field1282)
        newline(pp)
        field1283 = unwrapped_fields1281[2]
        pretty_relation_id(pp, field1283)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1289 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1289)
        write(pp, flat1289)
        return nothing
    else
        _dollar_dollar = msg
        fields1285 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1286 = fields1285
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1287 = unwrapped_fields1286[1]
        pretty_name(pp, field1287)
        newline(pp)
        field1288 = unwrapped_fields1286[2]
        pretty_epoch(pp, field1288)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1295 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1295)
        write(pp, flat1295)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1474 = _dollar_dollar.name
        else
            _t1474 = nothing
        end
        fields1290 = (_t1474, _dollar_dollar.relation_id,)
        unwrapped_fields1291 = fields1290
        write(pp, "(abort")
        indent_sexp!(pp)
        field1292 = unwrapped_fields1291[1]
        if !isnothing(field1292)
            newline(pp)
            opt_val1293 = field1292
            pretty_name(pp, opt_val1293)
        end
        newline(pp)
        field1294 = unwrapped_fields1291[2]
        pretty_relation_id(pp, field1294)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1298 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1298)
        write(pp, flat1298)
        return nothing
    else
        _dollar_dollar = msg
        fields1296 = _get_oneof_field(_dollar_dollar, :csv_config)
        unwrapped_fields1297 = fields1296
        write(pp, "(export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1297)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1309 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1309)
        write(pp, flat1309)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1475 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1475 = nothing
        end
        deconstruct_result1304 = _t1475
        if !isnothing(deconstruct_result1304)
            unwrapped1305 = deconstruct_result1304
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1306 = unwrapped1305[1]
            pretty_export_csv_path(pp, field1306)
            newline(pp)
            field1307 = unwrapped1305[2]
            pretty_export_csv_source(pp, field1307)
            newline(pp)
            field1308 = unwrapped1305[3]
            pretty_csv_config(pp, field1308)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1477 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1476 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1477,)
            else
                _t1476 = nothing
            end
            deconstruct_result1299 = _t1476
            if !isnothing(deconstruct_result1299)
                unwrapped1300 = deconstruct_result1299
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1301 = unwrapped1300[1]
                pretty_export_csv_path(pp, field1301)
                newline(pp)
                field1302 = unwrapped1300[2]
                pretty_export_csv_columns_list(pp, field1302)
                newline(pp)
                field1303 = unwrapped1300[3]
                pretty_config_dict(pp, field1303)
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
    flat1311 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1311)
        write(pp, flat1311)
        return nothing
    else
        fields1310 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1310))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1318 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1318)
        write(pp, flat1318)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1478 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1478 = nothing
        end
        deconstruct_result1314 = _t1478
        if !isnothing(deconstruct_result1314)
            unwrapped1315 = deconstruct_result1314
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1315)
                newline(pp)
                for (i1479, elem1316) in enumerate(unwrapped1315)
                    i1317 = i1479 - 1
                    if (i1317 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1316)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1480 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1480 = nothing
            end
            deconstruct_result1312 = _t1480
            if !isnothing(deconstruct_result1312)
                unwrapped1313 = deconstruct_result1312
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1313)
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
    flat1323 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1323)
        write(pp, flat1323)
        return nothing
    else
        _dollar_dollar = msg
        fields1319 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1320 = fields1319
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1321 = unwrapped_fields1320[1]
        write(pp, format_string(pp, field1321))
        newline(pp)
        field1322 = unwrapped_fields1320[2]
        pretty_relation_id(pp, field1322)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1327 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1327)
        write(pp, flat1327)
        return nothing
    else
        fields1324 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1324)
            newline(pp)
            for (i1481, elem1325) in enumerate(fields1324)
                i1326 = i1481 - 1
                if (i1326 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1325)
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
    for (i1520, _rid) in enumerate(msg.ids)
        _idx = i1520 - 1
        newline(pp)
        write(pp, "(")
        _t1521 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1521)
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
    for (i1522, _elem) in enumerate(msg.keys)
        _idx = i1522 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1523, _elem) in enumerate(msg.values)
        _idx = i1523 - 1
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
    for (i1524, _elem) in enumerate(msg.columns)
        _idx = i1524 - 1
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
